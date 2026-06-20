import Foundation
import SwiftUI

/// The four primary destinations in the Liquid Glass tab bar.
enum WarmthTab: Hashable {
    case home, capture, connections, settings
}

/// Root composition object. Owns all services and is injected into the environment
/// so every feature reads the same instances. Dependencies are passed in so previews
/// and tests can supply mocks.
@MainActor
@Observable
final class AppModel {
    let auth: any AuthProviding
    let speech: any SpeechServicing
    let signalClient: any SignalSending
    let crmClient: any CRMProviding
    let socialGraph: any SocialGraphProcessing
    let sessionLog: SessionCaptureLog
    let settings: SettingsStore
    /// Apple Watch companion bridge. Self-contained; wired to capture below.
    let watch: WatchSessionService

    var selectedTab: WarmthTab = .home
    var dashboard: CRMDashboardSummary?
    var roster: CRMRoster?
    var communityMembers: [CRMCommunityMember] = []
    var calendarEvents: [CRMDetectedEvent] = []
    var icpProfile: [CRMICPRow] = []
    var homeError: String?
    var routedCommunityUserIDs: Set<String> = []
    /// Shown after a roster match from a live "hi {name}" greeting.
    var attendeeMatch: AttendeeMatchResult?
    private var matchAttemptedThisCapture = false
    private var didApplyLaunchTab = false
    /// Tunable for tests — production polls the backend while ingest finishes.
    var captureRefreshAttempts = 4
    var captureRefreshDelaySeconds = 1.2

    var recentlyMet: [CRMRosterMetRow] {
        roster?.met ?? []
    }

    var isAtEventToday: Bool {
        settings.isAtEventToday(calendarEvents: calendarEvents)
    }

    init(
        auth: any AuthProviding,
        speech: any SpeechServicing,
        signalClient: any SignalSending,
        crmClient: any CRMProviding,
        socialGraph: any SocialGraphProcessing,
        sessionLog: SessionCaptureLog = SessionCaptureLog(),
        settings: SettingsStore = SettingsStore(),
        watch: WatchSessionService = WatchSessionService()
    ) {
        self.auth = auth
        self.speech = speech
        self.signalClient = signalClient
        self.crmClient = crmClient
        self.socialGraph = socialGraph
        self.sessionLog = sessionLog
        self.settings = settings
        self.watch = watch
        applyBackendURL(settings.baseURL)

        watch.onStartRequested = { [weak self] in self?.startCaptureFromWatch() }
        watch.onStopRequested = { [weak self] in self?.stopCaptureFromWatch() }
        syncWatchState()
        Task {
            await refreshRosterWatchlist()
            await refreshHome()
        }
    }

    func applyLaunchTabIfNeeded() {
        guard !didApplyLaunchTab else { return }
        didApplyLaunchTab = true
        selectedTab = isAtEventToday ? .capture : .home
    }

    func dismissAttendeeMatch() {
        attendeeMatch = nil
    }

    func prepareNewCapture() {
        matchAttemptedThisCapture = false
        attendeeMatch = nil
    }

    /// Hydrate the on-device name watchlist from the backend roster.
    func refreshRosterWatchlist() async {
        let names = await signalClient.fetchRosterFirstNames()
        guard !names.isEmpty else { return }
        WatchlistProvider.shared.update(names: names)
    }

    /// Detect "hi {name}" in the live transcript and match against the event roster.
    func tryMatchAttendee(from transcript: String) async {
        guard !matchAttemptedThisCapture else { return }
        guard let name = Self.extractGreetingName(from: transcript) else { return }
        matchAttemptedThisCapture = true
        guard let result = await signalClient.matchAttendee(
            name: name,
            company: nil,
            transcript: transcript
        ), result.matched else { return }
        attendeeMatch = result
        WarmthHaptics.success()
    }

    private static func extractGreetingName(from transcript: String) -> String? {
        let lowered = transcript.lowercased()
        let patterns = [
            #"\bhi\s+([a-z][a-z'-]{1,24})\b"#,
            #"\bhey\s+([a-z][a-z'-]{1,24})\b"#,
            #"\bnice to meet you[,\s]+([a-z][a-z'-]{1,24})\b"#,
        ]
        for pattern in patterns {
            guard let regex = try? NSRegularExpression(pattern: pattern),
                  let match = regex.firstMatch(in: lowered, range: NSRange(lowered.startIndex..., in: lowered)),
                  match.numberOfRanges > 1,
                  let range = Range(match.range(at: 1), in: lowered) else { continue }
            let name = String(lowered[range]).capitalized
            if name.count >= 2 { return name }
        }
        return nil
    }

    /// Keep upload + CRM read clients pointed at the same backend host.
    func applyBackendURL(_ url: URL) {
        signalClient.updateBaseURL(url)
        crmClient.updateBaseURL(url)
    }

    func refreshConnections() async {
        await crmClient.refreshConnections()
        rebuildRoutedCommunityIDs()
    }

    func refreshHome() async {
        homeError = nil
        do {
            dashboard = try await crmClient.fetchDashboard()
            roster = try await crmClient.fetchRoster()
            communityMembers = try await crmClient.fetchCommunityMembers()
            calendarEvents = try await crmClient.fetchEvents()
            await crmClient.refreshConnections()
            rebuildRoutedCommunityIDs()
            applyLaunchTabIfNeeded()
        } catch {
            homeError = error.localizedDescription
        }
    }

    func refreshICPProfile() async {
        do {
            icpProfile = try await crmClient.fetchICPProfile()
        } catch {
            homeError = error.localizedDescription
        }
    }

    private func rebuildRoutedCommunityIDs() {
        var ids = Set<String>()
        for row in roster?.met ?? [] {
            guard let meet = row.meetResult else { continue }
            guard meet.routedTo?.contains("community") == true else { continue }
            for candidate in meet.matchedCandidates {
                if let userId = candidate.userId { ids.insert(userId) }
            }
        }
        routedCommunityUserIDs = ids
    }

    /// Poll the backend after capture — ingest runs async server-side (HTTP 202).
    func refreshConnectionsAfterCapture() async {
        for attempt in 0..<captureRefreshAttempts {
            if attempt > 0, captureRefreshDelaySeconds > 0 {
                try? await Task.sleep(for: .seconds(captureRefreshDelaySeconds))
            }
            await refreshConnections()
            await refreshHome()
        }
    }

    // MARK: - Watch bridge

    func syncWatchState() {
        let last = crmClient.connections.first ?? sessionLog.people.first.map { person in
            CRMConnection(
                id: person.id.uuidString,
                name: person.name,
                title: person.role,
                companyName: person.org,
                interests: person.interests,
                icpScore: person.icpScore,
                predictedWarmth: person.icpScore
            )
        }
        watch.updateState(
            isRecording: speech.phase == .recording,
            elapsed: speech.elapsed,
            lastPersonName: last?.name,
            lastPersonOrg: last?.org
        )
    }

    func startCaptureFromWatch() {
        matchAttemptedThisCapture = false
        Task { @MainActor in
            guard await speech.requestPermissions(), speech.hasMicrophoneAccess else {
                syncWatchState()
                return
            }
            await speech.startRecording()
            syncWatchState()
        }
    }

    func stopCaptureFromWatch() {
        let transcript = speech.transcript.trimmingCharacters(in: .whitespacesAndNewlines)
        speech.stopAndReset()
        if !transcript.isEmpty {
            Task { await capturePerson(from: transcript) }
        }
        syncWatchState()
    }

    var isOnboarded: Bool { settings.didCompleteOnboarding }

    func completeOnboarding() {
        settings.didCompleteOnboarding = true
    }

    /// Capture a person extracted from a transcript: log it + upload a signal.
    func capturePerson(from transcript: String) async {
        matchAttemptedThisCapture = false
        guard let node = socialGraph.process(transcript: transcript) else { return }
        let recorded = sessionLog.record(node)
        let token = await auth.idToken()
        let user = auth.signalUser(idToken: token)
        let signal = recorded.makeSignal(user: user, sessionId: sessionLog.sessionId)
        signalClient.send(signal)
        await refreshConnectionsAfterCapture()
        syncWatchState()
    }

    // MARK: - Previews / wiring

    static var preview: AppModel {
        let model = AppModel(
            auth: MockAuthService.signedInPreview,
            speech: MockSpeechService(),
            signalClient: MockSignalClient(),
            crmClient: MockCRMClient(),
            socialGraph: MockSocialGraph(),
            sessionLog: .preview
        )
        model.dashboard = .preview
        model.communityMembers = CRMCommunityMember.previewList
        return model
    }
}

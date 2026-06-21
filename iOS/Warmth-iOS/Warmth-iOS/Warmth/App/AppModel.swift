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
    let watch: WatchSessionService
    let eventListening: EventListeningEngine

    var selectedTab: WarmthTab = .home
    var dashboard: CRMDashboardSummary?
    var roster: CRMRoster?
    var communityMembers: [CRMCommunityMember] = []
    var calendarEvents: [CRMDetectedEvent] = []
    var icpProfile: [CRMICPRow] = []
    var homeError: String?
    var routedCommunityUserIDs: Set<String> = []
    var attendeeMatch: AttendeeMatchResult?
    /// Person name supplied by Siri ("I'm meeting Sarah").
    var pendingCapturePersonName: String?
    var isPassiveFloorListeningActive = false
    var passiveFloorTranscript = ""

    /// Mirrored auth state so SwiftUI observes sign-in/out through `AppModel`
    /// (the concrete auth service is stored behind `any AuthProviding`).
    private(set) var authState: AuthState = .unknown

    private var matchAttemptedThisCapture = false
    private var didApplyLaunchTab = false
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
        watch: WatchSessionService = WatchSessionService(),
        eventListening: EventListeningEngine = EventListeningEngine()
    ) {
        self.auth = auth
        self.speech = speech
        self.signalClient = signalClient
        self.crmClient = crmClient
        self.socialGraph = socialGraph
        self.sessionLog = sessionLog
        self.settings = settings
        self.watch = watch
        self.eventListening = eventListening
        applyBackendURL(settings.baseURL)

        eventListening.onCaptureComplete = { [weak self] transcript, _ in
            await self?.capturePerson(from: transcript)
        }
        eventListening.onStateChange = { [weak self] state in
            self?.isPassiveFloorListeningActive = state != .idle
        }
        eventListening.onLiveTranscriptChange = { [weak self] text in
            self?.passiveFloorTranscript = text
        }

        watch.onStartRequested = { [weak self] in
            Task { @MainActor in await self?.startCapture(source: .watch) }
        }
        watch.onStopRequested = { [weak self] in
            Task { @MainActor in await self?.stopCapture(source: .watch) }
        }
        syncWatchState()
        authState = auth.state
        Task {
            await refreshRosterWatchlist()
        }
    }

    func applyLaunchTabIfNeeded() {
        guard !didApplyLaunchTab else { return }
        didApplyLaunchTab = true
        selectedTab = isAtEventToday ? .capture : .home
    }

    func restoreAuth() async {
        await auth.restore()
        syncAuthState()
    }

    func signInWithGoogle() async throws {
        try await auth.signInWithGoogle()
        syncAuthState()
        await refreshHome()
    }

    func signOut() {
        auth.signOut()
        syncAuthState()
    }

    private func syncAuthState() {
        authState = auth.state
    }

    func dismissAttendeeMatch() {
        attendeeMatch = nil
    }

    func prepareNewCapture() {
        matchAttemptedThisCapture = false
        attendeeMatch = nil
        pendingCapturePersonName = nil
    }

    func refreshRosterWatchlist() async {
        let names = await signalClient.fetchRosterFirstNames()
        guard !names.isEmpty else { return }
        WatchlistProvider.shared.update(names: names)
        eventListening.watchlist = names
    }

    func tryMatchAttendee(from transcript: String) async {
        guard !matchAttemptedThisCapture else { return }
        guard let name = Self.extractGreetingName(from: transcript) else { return }
        await matchAttendee(named: name, transcript: transcript)
    }

    func matchAttendee(named name: String, transcript: String? = nil) async {
        guard !matchAttemptedThisCapture else { return }
        matchAttemptedThisCapture = true
        guard let result = await signalClient.matchAttendee(
            name: name,
            company: nil,
            transcript: transcript
        ), result.matched else { return }
        // Surface the connection as a push-style banner rather than an in-app card.
        MatchNotifier.shared.notifyMatch(result)
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
            if authState.isSignedIn {
                do {
                    try await crmClient.bootstrapUserProfileIfNeeded()
                } catch {
                    homeError = "Could not sync your profile: \(error.localizedDescription)"
                }
            }
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

    func refreshConnectionsAfterCapture() async {
        for attempt in 0..<captureRefreshAttempts {
            if attempt > 0, captureRefreshDelaySeconds > 0 {
                try? await Task.sleep(for: .seconds(captureRefreshDelaySeconds))
            }
            await refreshConnections()
            await refreshHome()
        }
    }

    // MARK: - Unified capture router

    func startCapture(source: CaptureSource, personName: String? = nil) async {
        let method = source.activationMethod
        switch method {
        case .siri:
            guard settings.capturePreferences.isEnabled(.siri)
                || settings.capturePreferences.isEnabled(.actionButton) else { return }
        default:
            guard settings.capturePreferences.isEnabled(method) else { return }
        }
        guard isOnboarded else { return }

        prepareNewCapture()
        if let personName, !personName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            let trimmed = personName.trimmingCharacters(in: .whitespacesAndNewlines)
            pendingCapturePersonName = trimmed
            await matchAttendee(named: trimmed)
        }

        selectedTab = .capture
        await stopPassiveFloorListening()

        guard await speech.requestPermissions(), speech.hasMicrophoneAccess else {
            syncWatchState()
            return
        }
        await speech.startRecording()
        syncWatchState()
    }

    func stopCapture(source: CaptureSource) async {
        guard speech.phase == .recording else { return }

        let transcript = speech.transcript.trimmingCharacters(in: .whitespacesAndNewlines)
        speech.stopAndReset()
        pendingCapturePersonName = nil
        if !transcript.isEmpty {
            await capturePerson(from: transcript)
        }
        syncWatchState()
        await resumePassiveFloorListeningIfNeeded()
    }

    func startCaptureFromWatch() {
        Task { await startCapture(source: .watch) }
    }

    func stopCaptureFromWatch() {
        Task { await stopCapture(source: .watch) }
    }

    func startManualCapture() async {
        await startCapture(source: .manual)
    }

    func stopManualCapture() async {
        await stopCapture(source: .manual)
    }

    // MARK: - Passive floor listening

    func startPassiveFloorListeningIfNeeded() async {
        guard settings.capturePreferences.isEnabled(.passiveFloorListening) else { return }
        guard speech.phase == .idle else { return }
        guard eventListening.state == .idle else { return }

        eventListening.watchlist = WatchlistProvider.shared.names
        await eventListening.start()
    }

    func stopPassiveFloorListening() async {
        guard eventListening.state != .idle else { return }
        eventListening.stop()
    }

    func resumePassiveFloorListeningIfNeeded() async {
        guard speech.phase == .idle else { return }
        await startPassiveFloorListeningIfNeeded()
    }

    func handleScenePhase(_ phase: ScenePhase) async {
        switch phase {
        case .active:
            await startPassiveFloorListeningIfNeeded()
        case .background, .inactive:
            await stopPassiveFloorListening()
        @unknown default:
            break
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
            lastPersonName: pendingCapturePersonName ?? last?.name,
            lastPersonOrg: last?.org
        )
    }

    var isOnboarded: Bool { settings.didCompleteOnboarding }

    func completeOnboarding() {
        settings.didCompleteOnboarding = true
    }

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

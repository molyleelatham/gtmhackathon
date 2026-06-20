import Foundation
import SwiftUI

/// The three primary destinations in the Liquid Glass tab bar.
enum WarmthTab: Hashable {
    case capture, connections, settings
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

    var selectedTab: WarmthTab = .capture
    /// Shown after a roster match from a live "hi {name}" greeting.
    var attendeeMatch: AttendeeMatchResult?
    private var matchAttemptedThisCapture = false
    /// Tunable for tests — production polls the backend while ingest finishes.
    var captureRefreshAttempts = 4
    var captureRefreshDelaySeconds = 1.2

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
            await refreshConnections()
        }
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

    /// Keep upload + CRM read clients pointed at the same backend host.
    func applyBackendURL(_ url: URL) {
        signalClient.updateBaseURL(url)
        crmClient.updateBaseURL(url)
    }

    func refreshConnections() async {
        await crmClient.refreshConnections()
    }

    /// Poll the backend after capture — ingest runs async server-side (HTTP 202).
    func refreshConnectionsAfterCapture() async {
        for attempt in 0..<captureRefreshAttempts {
            if attempt > 0, captureRefreshDelaySeconds > 0 {
                try? await Task.sleep(for: .seconds(captureRefreshDelaySeconds))
            }
            await refreshConnections()
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
        AppModel(
            auth: MockAuthService.signedInPreview,
            speech: MockSpeechService(),
            signalClient: MockSignalClient(),
            crmClient: MockCRMClient(),
            socialGraph: MockSocialGraph(),
            sessionLog: .preview
        )
    }
}

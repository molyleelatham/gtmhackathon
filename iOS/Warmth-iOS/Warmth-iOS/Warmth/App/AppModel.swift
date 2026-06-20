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
    let socialGraph: any SocialGraphProcessing
    let sessionLog: SessionCaptureLog
    let settings: SettingsStore
    /// Apple Watch companion bridge. Self-contained; wired to capture below.
    let watch: WatchSessionService

    var selectedTab: WarmthTab = .capture

    init(
        auth: any AuthProviding,
        speech: any SpeechServicing,
        signalClient: any SignalSending,
        socialGraph: any SocialGraphProcessing,
        sessionLog: SessionCaptureLog = SessionCaptureLog(),
        settings: SettingsStore = SettingsStore(),
        watch: WatchSessionService = WatchSessionService()
    ) {
        self.auth = auth
        self.speech = speech
        self.signalClient = signalClient
        self.socialGraph = socialGraph
        self.sessionLog = sessionLog
        self.settings = settings
        self.watch = watch
        signalClient.updateBaseURL(settings.baseURL)

        // The single iOS ↔ watch hook: wrist intents drive capture, and every
        // capture-state change is mirrored back to the watch + complication.
        watch.onStartRequested = { [weak self] in self?.startCaptureFromWatch() }
        watch.onStopRequested = { [weak self] in self?.stopCaptureFromWatch() }
        syncWatchState()
    }

    // MARK: - Watch bridge

    /// Mirror the current capture state to the watch app + complication.
    func syncWatchState() {
        let last = sessionLog.people.first
        watch.updateState(
            isRecording: speech.phase == .recording,
            elapsed: speech.elapsed,
            lastPersonName: last?.name,
            lastPersonOrg: last?.org
        )
    }

    /// Wrist → phone: begin recording.
    func startCaptureFromWatch() {
        Task {
            await speech.startRecording()
            syncWatchState()
        }
    }

    /// Wrist → phone: stop and commit the captured person (mirrors CaptureView's Stop).
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
        guard let node = socialGraph.process(transcript: transcript) else { return }
        let recorded = sessionLog.record(node)
        let token = await auth.idToken()
        let user = auth.signalUser(idToken: token)
        let signal = recorded.makeSignal(user: user, sessionId: sessionLog.sessionId)
        signalClient.send(signal)
        syncWatchState()
    }

    // MARK: - Previews / wiring

    /// Fully-mocked model for SwiftUI previews.
    static var preview: AppModel {
        AppModel(
            auth: MockAuthService.signedInPreview,
            speech: MockSpeechService(),
            signalClient: MockSignalClient(),
            socialGraph: MockSocialGraph(),
            sessionLog: .preview
        )
    }
}

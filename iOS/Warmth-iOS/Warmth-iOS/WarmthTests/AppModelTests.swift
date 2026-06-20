import XCTest
@testable import Warmth

@MainActor
final class AppModelTests: XCTestCase {
    private var auth: MockAuthService!
    private var speech: MockSpeechService!
    private var signalClient: MockSignalClient!
    private var crmClient: MockCRMClient!
    private var sessionLog: SessionCaptureLog!
    private var settings: SettingsStore!
    private var model: AppModel!

    private var suiteName: String!
    private var defaults: UserDefaults!

    override func setUp() {
        super.setUp()
        suiteName = "WarmthTests.\(UUID().uuidString)"
        defaults = UserDefaults(suiteName: suiteName)!

        auth = MockAuthService.signedInPreview
        speech = MockSpeechService()
        signalClient = MockSignalClient()
        crmClient = MockCRMClient()
        sessionLog = SessionCaptureLog(sessionId: "test-session")
        settings = SettingsStore(defaults: defaults)

        model = AppModel(
            auth: auth,
            speech: speech,
            signalClient: signalClient,
            crmClient: crmClient,
            socialGraph: MockSocialGraph(),
            sessionLog: sessionLog,
            settings: settings
        )
        model.captureRefreshAttempts = 1
        model.captureRefreshDelaySeconds = 0
    }

    override func tearDown() {
        defaults.removePersistentDomain(forName: suiteName)
        defaults = nil
        suiteName = nil
        super.tearDown()
    }

    func testIsOnboardedReflectsSettings() {
        XCTAssertFalse(model.isOnboarded)
        model.completeOnboarding()
        XCTAssertTrue(model.isOnboarded)
        XCTAssertTrue(settings.didCompleteOnboarding)
    }

    func testCapturePersonRecordsAndSendsSignal() async {
        let transcript = "Hey, I'm Maya from NorthWind Labs."

        await model.capturePerson(from: transcript)

        XCTAssertEqual(sessionLog.people.count, 1)
        XCTAssertEqual(sessionLog.people.first?.name, "Maya Chen")
        XCTAssertEqual(signalClient.sent.count, 1)
        XCTAssertEqual(signalClient.sent.first?.sessionId, "test-session")
        XCTAssertEqual(signalClient.sent.first?.user.uid, "mock-uid-001")
    }

    func testCapturePersonSkipsWhenGraphReturnsNil() async {
        let emptyGraph = EmptySocialGraph()
        let localModel = AppModel(
            auth: auth,
            speech: speech,
            signalClient: signalClient,
            crmClient: crmClient,
            socialGraph: emptyGraph,
            sessionLog: sessionLog,
            settings: settings
        )

        await localModel.capturePerson(from: "   ")

        XCTAssertTrue(sessionLog.people.isEmpty)
        XCTAssertTrue(signalClient.sent.isEmpty)
    }

    func testStopCaptureFromWatchCapturesNonEmptyTranscript() async {
        speech.transcript = "Nice to meet you — I'm Diego from Helio Robotics."
        speech.phase = .recording

        model.stopCaptureFromWatch()

        // capturePerson runs in a detached Task; give it a moment to finish.
        try? await Task.sleep(for: .milliseconds(50))

        XCTAssertEqual(speech.phase, .idle)
        XCTAssertEqual(sessionLog.people.count, 1)
        XCTAssertEqual(signalClient.sent.count, 1)
    }

    func testStopCaptureFromWatchIgnoresEmptyTranscript() async {
        speech.transcript = "   "
        speech.phase = .recording

        model.stopCaptureFromWatch()
        try? await Task.sleep(for: .milliseconds(50))

        XCTAssertEqual(speech.phase, .idle)
        XCTAssertTrue(sessionLog.people.isEmpty)
        XCTAssertTrue(signalClient.sent.isEmpty)
    }

    func testStartCaptureFromWatchStartsRecording() async {
        model.startCaptureFromWatch()
        try? await Task.sleep(for: .milliseconds(50))

        XCTAssertEqual(speech.phase, .recording)
    }

    func testSyncWatchStateUsesLatestCapturedPerson() async {
        await model.capturePerson(from: "Maya from NorthWind Labs")
        model.syncWatchState()
        // WatchSessionService has no readable last-person surface; verify no crash
        // and that recording state mirrors speech phase.
        XCTAssertFalse(model.watch.isRecording)
    }

    func testBackendURLPropagatesToUploadAndCRMClients() {
        settings.baseURLString = "https://custom.backend.test"
        let updated = AppModel(
            auth: auth,
            speech: speech,
            signalClient: signalClient,
            crmClient: crmClient,
            socialGraph: MockSocialGraph(),
            sessionLog: sessionLog,
            settings: settings
        )
        XCTAssertEqual(updated.signalClient.baseURL.absoluteString, "https://custom.backend.test")
        XCTAssertEqual(updated.crmClient.baseURL.absoluteString, "https://custom.backend.test")
    }
}

/// Returns nil for every transcript — used to exercise the early-exit path in `capturePerson`.
private struct EmptySocialGraph: SocialGraphProcessing {
    func process(transcript: String) -> PersonNode? { nil }
}

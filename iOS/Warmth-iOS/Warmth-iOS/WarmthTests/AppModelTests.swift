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
        settings.didCompleteOnboarding = true

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
        settings.didCompleteOnboarding = false
        let fresh = AppModel(
            auth: auth,
            speech: speech,
            signalClient: signalClient,
            crmClient: crmClient,
            socialGraph: MockSocialGraph(),
            sessionLog: sessionLog,
            settings: settings
        )
        XCTAssertFalse(fresh.isOnboarded)
        fresh.completeOnboarding()
        XCTAssertTrue(fresh.isOnboarded)
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

        await model.stopCapture(source: .watch)

        XCTAssertEqual(speech.phase, .idle)
        XCTAssertEqual(sessionLog.people.count, 1)
        XCTAssertEqual(signalClient.sent.count, 1)
    }

    func testStopCaptureFromWatchIgnoresEmptyTranscript() async {
        speech.transcript = "   "
        speech.phase = .recording

        await model.stopCapture(source: .watch)
        XCTAssertEqual(speech.phase, .idle)
        XCTAssertTrue(sessionLog.people.isEmpty)
        XCTAssertTrue(signalClient.sent.isEmpty)
    }

    func testStartCaptureFromWatchStartsRecording() async {
        await model.startCapture(source: .watch)
        XCTAssertEqual(speech.phase, .recording)
        XCTAssertEqual(model.selectedTab, .capture)
    }

    func testStartCaptureRespectsDisabledWatchPref() async {
        settings.capturePreferences.setEnabled(.watch, enabled: false)
        await model.startCapture(source: .watch)
        XCTAssertEqual(speech.phase, .idle)
    }

    func testStartCaptureSetsPendingPersonNameFromSiri() async {
        await model.startCapture(source: .siri, personName: "Sarah")
        XCTAssertEqual(model.pendingCapturePersonName, "Sarah")
        XCTAssertEqual(speech.phase, .recording)
    }

    func testStartCaptureRespectsDisabledManualPref() async {
        settings.capturePreferences.setEnabled(.manual, enabled: false)
        await model.startCapture(source: .manual)
        XCTAssertEqual(speech.phase, .idle)
    }

    func testSyncWatchStateUsesLatestCapturedPerson() async {
        await model.capturePerson(from: "Maya from NorthWind Labs")
        model.syncWatchState()
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

    func testLaunchTabUsesEventMode() {
        settings.eventModeEnabled = true
        model.applyLaunchTabIfNeeded()
        XCTAssertEqual(model.selectedTab, .capture)
    }

    func testLaunchTabDefaultsToHome() {
        settings.eventModeEnabled = false
        model.applyLaunchTabIfNeeded()
        XCTAssertEqual(model.selectedTab, .home)
    }

    func testRefreshHomeLoadsDashboardAndRoster() async {
        await model.refreshHome()
        XCTAssertNotNil(model.dashboard)
        XCTAssertNotNil(model.roster)
        XCTAssertFalse(model.communityMembers.isEmpty)
        XCTAssertNil(model.homeError)
    }

    func testRefreshHomeRecordsErrorFromCRMClient() async {
        let failing = FailingCRMClient()
        let localModel = AppModel(
            auth: auth,
            speech: speech,
            signalClient: signalClient,
            crmClient: failing,
            socialGraph: MockSocialGraph(),
            sessionLog: sessionLog,
            settings: settings
        )
        await localModel.refreshHome()
        XCTAssertNotNil(localModel.homeError)
    }

    func testRefreshICPProfileLoadsRows() async {
        await model.refreshICPProfile()
        XCTAssertFalse(model.icpProfile.isEmpty)
    }
}

@MainActor
private final class FailingCRMClient: CRMProviding {
    var baseURL: URL = URL(string: "http://localhost:8000")!
    var connections: [CRMConnection] = []
    var fetchState: CRMFetchState = .idle

    func updateBaseURL(_ url: URL) { baseURL = url }
    func refreshConnections() async { fetchState = .failed("offline") }
    func connectionDetail(id: String) async throws -> CRMConnectionDetail { throw CRMClientError.httpStatus(500) }
    func fetchDashboard() async throws -> CRMDashboardSummary { throw CRMClientError.httpStatus(500) }
    func fetchRoster() async throws -> CRMRoster { throw CRMClientError.httpStatus(500) }
    func fetchCommunityMembers() async throws -> [CRMCommunityMember] { throw CRMClientError.httpStatus(500) }
    func fetchEvents() async throws -> [CRMDetectedEvent] { throw CRMClientError.httpStatus(500) }
    func fetchICPProfile() async throws -> [CRMICPRow] { throw CRMClientError.httpStatus(500) }
    func sendFollowup(connectionId: String) async throws -> CRMFollowUpDraft { throw CRMClientError.httpStatus(500) }
    func bootstrapUserProfileIfNeeded() async throws {}
}

private struct EmptySocialGraph: SocialGraphProcessing {
    func process(transcript: String) -> PersonNode? { nil }
}

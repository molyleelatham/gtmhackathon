import XCTest
@testable import Warmth

@MainActor
final class MockAuthServiceTests: XCTestCase {
    func testContinueAsGuestSignsInGuestUser() {
        let auth = MockAuthService()
        auth.continueAsGuest()

        XCTAssertTrue(auth.state.isSignedIn)
        XCTAssertEqual(auth.state.user?.id, "guest")
        XCTAssertEqual(auth.state.user?.displayName, "Guest")
    }

    func testSignOutClearsSession() {
        let auth = MockAuthService.signedInPreview
        auth.signOut()
        XCTAssertEqual(auth.state, .signedOut)
    }

    func testSignInWithGoogleUpdatesState() async throws {
        let auth = MockAuthService()
        try await auth.signInWithGoogle()

        XCTAssertTrue(auth.state.isSignedIn)
        XCTAssertEqual(auth.state.user?.id, "mock-uid-001")
        XCTAssertEqual(auth.state.user?.email, "demo@warmth.app")
    }

    func testIdTokenReturnsMockValue() async {
        let auth = MockAuthService.signedInPreview
        let token = await auth.idToken()
        XCTAssertEqual(token, "mock-id-token")
    }

    func testSignalUserUsesSignedInUid() async {
        let auth = MockAuthService.signedInPreview
        let user = auth.signalUser(idToken: "abc-token")
        XCTAssertEqual(user.uid, "mock-uid-001")
        XCTAssertEqual(user.idToken, "abc-token")
    }

    func testSignalUserFallsBackToAnonymousWhenSignedOut() async {
        let auth = MockAuthService()
        let user = auth.signalUser(idToken: "")
        XCTAssertEqual(user.uid, "anonymous")
    }
}

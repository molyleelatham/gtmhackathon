import XCTest
@testable import Warmth

@MainActor
final class FirebaseAuthServiceTests: XCTestCase {
    func testApplyAuthorizationAddsBearerToken() async {
        let auth = MockAuthService.signedInPreview
        var request = URLRequest(url: URL(string: "https://api.test")!)
        await auth.applyAuthorization(to: &request)
        XCTAssertEqual(request.value(forHTTPHeaderField: "Authorization"), "Bearer mock-id-token")
    }

    func testApplyAuthorizationSkipsWhenTokenEmpty() async {
        let auth = MockAuthService(state: .signedOut)
        var request = URLRequest(url: URL(string: "https://api.test")!)
        await auth.applyAuthorization(to: &request)
        XCTAssertNil(request.value(forHTTPHeaderField: "Authorization"))
    }

    func testSignalUserUsesSignedInUid() async {
        let auth = MockAuthService.signedInPreview
        let user = auth.signalUser(idToken: "token-123")
        XCTAssertEqual(user.uid, "mock-uid-001")
        XCTAssertEqual(user.idToken, "token-123")
    }

    func testAuthErrorDescriptions() {
        XCTAssertNotNil(AuthError.cancelled.errorDescription)
        XCTAssertNotNil(AuthError.missingClientID.errorDescription)
        XCTAssertNotNil(AuthError.providerUnavailable.errorDescription)
        XCTAssertNotNil(AuthError.underlying("boom").errorDescription)
    }
}

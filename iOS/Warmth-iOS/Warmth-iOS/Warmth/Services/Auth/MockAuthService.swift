import Foundation

/// In-memory auth for previews and tests.
@MainActor
@Observable
final class MockAuthService: AuthProviding {
    var state: AuthState

    init(state: AuthState = .signedOut) {
        self.state = state
    }

    func restore() async {}

    func signInWithGoogle() async throws {
        try? await Task.sleep(for: .milliseconds(400))
        state = .signedIn(WarmthUser(
            id: "mock-uid-001",
            displayName: "Demo Founder",
            email: "demo@warmth.app",
            photoURL: nil
        ))
    }

    func signOut() { state = .signedOut }

    func idToken() async -> String { "mock-id-token" }

    static var signedInPreview: MockAuthService {
        MockAuthService(state: .signedIn(WarmthUser(
            id: "mock-uid-001", displayName: "Demo Founder", email: "demo@warmth.app", photoURL: nil
        )))
    }
}

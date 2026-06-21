import Foundation

/// Minimal signed-in user surface the app needs (independent of Firebase types).
struct WarmthUser: Identifiable, Sendable, Equatable {
    let id: String          // Firebase uid
    let displayName: String?
    let email: String?
    let photoURL: URL?
}

enum AuthState: Equatable, Sendable {
    case unknown
    case signedOut
    case signedIn(WarmthUser)

    var user: WarmthUser? {
        if case let .signedIn(user) = self { return user }
        return nil
    }

    var isSignedIn: Bool { user != nil }
}

enum AuthError: LocalizedError {
    case providerUnavailable
    case cancelled
    case missingClientID
    case underlying(String)

    var errorDescription: String? {
        switch self {
        case .providerUnavailable: return "Google sign-in isn't available on this device."
        case .cancelled: return "Sign-in was cancelled."
        case .missingClientID:
            return "Google sign-in isn't configured yet. Enable the Google provider in Firebase and add the client ID."
        case .underlying(let message): return message
        }
    }
}

/// Auth abstraction so previews/tests can inject a mock and the app keeps building
/// even if Firebase/GoogleSignIn fail to configure.
@MainActor
protocol AuthProviding: AnyObject {
    var state: AuthState { get }
    func restore() async
    func signInWithGoogle() async throws
    func signOut()
    /// Fetch a fresh ID token for the signal payload (empty string if unavailable).
    func idToken() async -> String
}

extension AuthProviding {
    /// Convenience: build the `CapturedSignal.User` for the current session.
    func signalUser(idToken: String) -> CapturedSignal.User {
        CapturedSignal.User(uid: state.user?.id ?? "anonymous", idToken: idToken)
    }
}

import Foundation
import UIKit
import FirebaseCore
import FirebaseAuth
import GoogleSignIn

/// Production auth: Google sign-in via GoogleSignIn → Firebase Auth credential.
/// Degrades gracefully when the Google provider / client ID isn't configured yet
/// (the bundled GoogleService-Info.plist currently lacks CLIENT_ID) by surfacing
/// `AuthError.missingClientID`; onboarding then offers "continue as guest".
@MainActor
@Observable
final class FirebaseAuthService: AuthProviding {
    private enum Keys {
        static let guestSession = "warmth.guestSessionActive"
    }

    private let defaults: UserDefaults
    private(set) var state: AuthState = .unknown

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    func restore() async {
        if let user = Auth.auth().currentUser {
            defaults.set(false, forKey: Keys.guestSession)
            state = .signedIn(map(user))
        } else if defaults.bool(forKey: Keys.guestSession) {
            state = .signedIn(WarmthUser(id: "guest", displayName: "Guest", email: nil, photoURL: nil))
        } else {
            state = .signedOut
        }
    }

    func signInWithGoogle() async throws {
        guard let clientID = FirebaseApp.app()?.options.clientID, !clientID.isEmpty else {
            throw AuthError.missingClientID
        }
        GIDSignIn.sharedInstance.configuration = GIDConfiguration(clientID: clientID)

        guard let presenter = Self.topViewController() else {
            throw AuthError.providerUnavailable
        }

        do {
            let result = try await GIDSignIn.sharedInstance.signIn(withPresenting: presenter)
            guard let idToken = result.user.idToken?.tokenString else {
                throw AuthError.providerUnavailable
            }
            let credential = GoogleAuthProvider.credential(
                withIDToken: idToken,
                accessToken: result.user.accessToken.tokenString
            )
            let authResult = try await Auth.auth().signIn(with: credential)
            defaults.set(false, forKey: Keys.guestSession)
            state = .signedIn(map(authResult.user))
        } catch let error as NSError {
            if error.code == GIDSignInError.canceled.rawValue { throw AuthError.cancelled }
            throw AuthError.underlying(error.localizedDescription)
        }
    }

    func continueAsGuest() {
        defaults.set(true, forKey: Keys.guestSession)
        state = .signedIn(WarmthUser(id: "guest", displayName: "Guest", email: nil, photoURL: nil))
    }

    func signOut() {
        defaults.set(false, forKey: Keys.guestSession)
        try? Auth.auth().signOut()
        GIDSignIn.sharedInstance.signOut()
        state = .signedOut
    }

    func idToken() async -> String {
        guard let user = Auth.auth().currentUser else { return "" }
        return (try? await user.getIDToken()) ?? ""
    }

    // MARK: - Helpers

    private func map(_ user: FirebaseAuth.User) -> WarmthUser {
        WarmthUser(id: user.uid, displayName: user.displayName, email: user.email, photoURL: user.photoURL)
    }

    /// Find a reasonable presenter for the Google sign-in sheet.
    static func topViewController() -> UIViewController? {
        let scene = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first(where: { $0.activationState == .foregroundActive }) ?? UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first
        var top = scene?.windows.first(where: { $0.isKeyWindow })?.rootViewController
            ?? scene?.windows.first?.rootViewController
        while let presented = top?.presentedViewController { top = presented }
        return top
    }
}

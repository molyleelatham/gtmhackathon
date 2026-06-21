import Foundation
import UIKit
import FirebaseCore
import FirebaseAuth
import GoogleSignIn

/// Production auth: Google sign-in via GoogleSignIn → Firebase Auth credential.
@MainActor
@Observable
final class FirebaseAuthService: AuthProviding {
    private enum Keys {
        static let legacyGuestSession = "warmth.guestSessionActive"
    }

    private let defaults: UserDefaults
    private(set) var state: AuthState = .unknown

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    func restore() async {
        defaults.removeObject(forKey: Keys.legacyGuestSession)
        if let user = Auth.auth().currentUser {
            state = .signedIn(map(user))
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
            defaults.removeObject(forKey: Keys.legacyGuestSession)
            state = .signedIn(map(authResult.user))
        } catch let error as NSError {
            if error.code == GIDSignInError.canceled.rawValue { throw AuthError.cancelled }
            throw AuthError.underlying(error.localizedDescription)
        }
    }

    func signOut() {
        defaults.removeObject(forKey: Keys.legacyGuestSession)
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

    /// Walks tab bars, navigation stacks, and presented controllers to find the
    /// topmost presenter — required for Google Sign-In from nested SwiftUI tabs.
    static func topViewController(base: UIViewController? = nil) -> UIViewController? {
        let root = base ?? {
            let scene = UIApplication.shared.connectedScenes
                .compactMap { $0 as? UIWindowScene }
                .first(where: { $0.activationState == .foregroundActive })
                ?? UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first
            return scene?.windows.first(where: { $0.isKeyWindow })?.rootViewController
                ?? scene?.windows.first?.rootViewController
        }()

        guard let root else { return nil }
        if let navigation = root as? UINavigationController {
            return topViewController(base: navigation.visibleViewController)
        }
        if let tabBar = root as? UITabBarController {
            return topViewController(base: tabBar.selectedViewController)
        }
        if let presented = root.presentedViewController {
            return topViewController(base: presented)
        }
        return root
    }
}

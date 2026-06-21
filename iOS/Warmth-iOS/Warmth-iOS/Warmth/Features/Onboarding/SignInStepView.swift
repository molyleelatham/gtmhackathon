import SwiftUI

/// Shared Google sign-in control for onboarding and Settings.
struct GoogleSignInButton: View {
    @Environment(AppModel.self) private var model
    var fill: Bool = true
    var showsInlineError = true
    var onSuccess: (() -> Void)?
    var onCancelled: (() -> Void)?
    var onFailure: ((String?) -> Void)?

    @State private var isSigningIn = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            if showsInlineError, let errorMessage {
                Text(errorMessage)
                    .warmthText(.Warmth.footnote, color: WarmthColor.emberRed)
                    .fixedSize(horizontal: false, vertical: true)
            }

            EmberButton(
                title: isSigningIn ? "Signing in…" : "Sign in with Google",
                systemImage: "g.circle.fill",
                fill: fill
            ) {
                signIn()
            }
            .disabled(isSigningIn)
            .opacity(isSigningIn ? 0.7 : 1)
        }
    }

    private func signIn() {
        isSigningIn = true
        errorMessage = nil
        Task {
            defer { isSigningIn = false }
            do {
                try await model.signInWithGoogle()
                WarmthHaptics.success()
                onSuccess?()
            } catch AuthError.cancelled {
                onCancelled?()
            } catch let error as AuthError {
                handle(message: error.errorDescription)
            } catch {
                handle(message: error.localizedDescription)
            }
        }
    }

    private func handle(message: String?) {
        WarmthHaptics.warning()
        let resolved = message ?? "Something went wrong signing in. Try again."
        if showsInlineError {
            errorMessage = resolved
        }
        onFailure?(resolved)
    }
}

/// Step 2 — Google sign-in required before entering the app.
struct SignInStepView: View {
    @Environment(AppModel.self) private var model
    let advance: () -> Void

    @State private var errorMessage: String?
    @State private var didAdvance = false

    var body: some View {
        VStack(spacing: 24) {
            VStack(spacing: 12) {
                Image(systemName: "person.crop.circle.badge.checkmark")
                    .font(.system(size: 44, weight: .semibold))
                    .foregroundStyle(WarmthColor.emberGradient)

                Text("Sign in")
                    .warmthText(.Warmth.largeTitle)

                Text("Warmth syncs your connections securely so your network is always with you.")
                    .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                    .multilineTextAlignment(.center)
            }

            if let errorMessage {
                GlassCard {
                    VStack(alignment: .leading, spacing: 6) {
                        Label("Heads up", systemImage: "exclamationmark.bubble.fill")
                            .warmthText(.Warmth.subheadline, color: WarmthColor.emberRed)
                        Text(errorMessage)
                            .warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)
                    }
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
            }

            GoogleSignInButton(
                showsInlineError: false,
                onSuccess: advanceIfNeeded,
                onFailure: { message in
                    errorMessage = message ?? "Something went wrong signing in. Try again."
                }
            )
        }
        .animation(WarmthMotion.gentle, value: errorMessage)
        .onChange(of: model.authState.isSignedIn) { _, isSignedIn in
            if isSignedIn { advanceIfNeeded() }
        }
        .onAppear {
            if model.authState.isSignedIn { advanceIfNeeded() }
        }
    }

    private func advanceIfNeeded() {
        guard !didAdvance else { return }
        didAdvance = true
        advance()
    }
}

#Preview {
    ZStack {
        MeshGradientBackground()
        SignInStepView(advance: {})
            .padding()
    }
    .environment(AppModel.preview)
}

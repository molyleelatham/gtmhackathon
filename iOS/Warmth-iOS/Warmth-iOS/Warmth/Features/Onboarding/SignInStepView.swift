import SwiftUI

/// Step 2 — Google sign-in with a graceful "continue as guest" fallback so the
/// demo never dead-ends on console configuration.
struct SignInStepView: View {
    @Environment(AppModel.self) private var model
    let advance: () -> Void

    @State private var isSigningIn = false
    @State private var errorMessage: String?
    @State private var showGuestFallback = false

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

            VStack(spacing: 12) {
                EmberButton(title: isSigningIn ? "Signing in…" : "Sign in with Google",
                            systemImage: "g.circle.fill") {
                    signIn()
                }
                .disabled(isSigningIn)
                .opacity(isSigningIn ? 0.7 : 1)

                if showGuestFallback {
                    EmberButton(title: "Continue as guest", systemImage: "arrow.right", fill: false) {
                        model.auth.continueAsGuest()
                        advance()
                    }
                    .transition(.opacity)
                }
            }
        }
        .animation(WarmthMotion.gentle, value: errorMessage)
        .animation(WarmthMotion.gentle, value: showGuestFallback)
        .onChange(of: model.auth.state.isSignedIn) { _, isSignedIn in
            if isSignedIn { advance() }
        }
        .onAppear {
            if model.auth.state.isSignedIn { advance() }
        }
    }

    private func signIn() {
        isSigningIn = true
        errorMessage = nil
        Task {
            defer { isSigningIn = false }
            do {
                try await model.auth.signInWithGoogle()
                // Auto-advance is handled by the `onChange` observer once state flips.
            } catch let error as AuthError {
                handle(message: error.errorDescription)
            } catch {
                handle(message: error.localizedDescription)
            }
        }
    }

    private func handle(message: String?) {
        WarmthHaptics.warning()
        errorMessage = message ?? "Something went wrong signing in. You can continue as a guest for now."
        showGuestFallback = true
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

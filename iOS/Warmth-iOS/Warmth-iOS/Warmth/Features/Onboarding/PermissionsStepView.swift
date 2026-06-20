import SwiftUI

/// Step 3 — request microphone + on-device speech access and explain the wake phrase.
struct PermissionsStepView: View {
    @Environment(AppModel.self) private var model
    let advance: () -> Void

    @State private var isRequesting = false
    @State private var granted = false

    var body: some View {
        VStack(spacing: 24) {
            VStack(spacing: 12) {
                Image(systemName: "waveform.badge.mic")
                    .font(.system(size: 44, weight: .semibold))
                    .foregroundStyle(WarmthColor.emberGradient)

                Text("Listen for intros")
                    .warmthText(.Warmth.largeTitle)
                    .multilineTextAlignment(.center)

                Text("Warmth uses your microphone and on-device speech recognition to capture introductions. Audio never leaves your phone.")
                    .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                    .multilineTextAlignment(.center)
            }

            GlassCard {
                HStack(spacing: 12) {
                    Image(systemName: "quote.opening")
                        .font(.Warmth.title2)
                        .foregroundStyle(WarmthColor.emberOrange)
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Your wake phrase")
                            .warmthText(.Warmth.caption, color: WarmthColor.inkSecondary)
                        Text("“\(WakeWord.phrase)”")
                            .warmthText(.Warmth.headline)
                    }
                    Spacer(minLength: 0)
                }
            }

            statusNote

            EmberButton(title: granted ? "Continue" : (isRequesting ? "Requesting…" : "Allow microphone & speech"),
                        systemImage: granted ? "arrow.right" : "mic.fill") {
                if granted {
                    advance()
                } else {
                    requestPermissions()
                }
            }
            .disabled(isRequesting)
            .opacity(isRequesting ? 0.7 : 1)
        }
        .animation(WarmthMotion.gentle, value: granted)
        .animation(WarmthMotion.gentle, value: model.speech.permissionError)
    }

    @ViewBuilder
    private var statusNote: some View {
        if let error = model.speech.permissionError {
            Label(error, systemImage: "exclamationmark.triangle.fill")
                .warmthText(.Warmth.footnote, color: WarmthColor.emberRed)
                .multilineTextAlignment(.center)
                .transition(.opacity)
        } else if granted {
            Label("Microphone & speech enabled", systemImage: "checkmark.seal.fill")
                .warmthText(.Warmth.footnote, color: WarmthColor.emberOrange)
                .transition(.opacity)
        }
    }

    private func requestPermissions() {
        isRequesting = true
        Task {
            let ok = await model.speech.requestPermissions()
            isRequesting = false
            granted = ok
            if ok {
                WarmthHaptics.success()
                advance()
            } else {
                WarmthHaptics.warning()
            }
        }
    }
}

#Preview {
    ZStack {
        MeshGradientBackground()
        PermissionsStepView(advance: {})
            .padding()
    }
    .environment(AppModel.preview)
}

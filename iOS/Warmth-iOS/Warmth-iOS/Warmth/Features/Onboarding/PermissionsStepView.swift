import SwiftUI
import UIKit

/// Step 3 — request microphone + on-device speech access and explain the wake phrase.
struct PermissionsStepView: View {
    @Environment(AppModel.self) private var model
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.openURL) private var openURL
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

            EmberButton(title: primaryTitle,
                        systemImage: granted ? "arrow.right" : "mic.fill") {
                if granted {
                    advance()
                } else if model.speech.permissionsDenied {
                    openSettings()
                } else {
                    requestPermissions()
                }
            }
            .disabled(isRequesting)
            .opacity(isRequesting ? 0.7 : 1)
        }
        .animation(WarmthMotion.gentle, value: granted)
        .animation(WarmthMotion.gentle, value: model.speech.permissionError)
        .animation(WarmthMotion.gentle, value: model.speech.permissionsDenied)
        .onChange(of: scenePhase) { _, phase in
            guard phase == .active, !isRequesting else { return }
            syncGrantedState()
        }
        .onAppear {
            syncGrantedState()
        }
    }

    private var primaryTitle: String {
        if granted { return "Continue" }
        if isRequesting { return "Requesting…" }
        if model.speech.permissionsDenied { return "Open Settings" }
        return "Allow microphone & speech"
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

    /// Re-read OS permission flags without prompting or advancing.
    private func syncGrantedState() {
        granted = model.speech.checkPermissions()
    }

    private func requestPermissions() {
        guard !isRequesting else { return }
        isRequesting = true
        Task { @MainActor in
            defer { isRequesting = false }
            let ok = await model.speech.requestPermissions()
            granted = ok
            if ok {
                WarmthHaptics.success()
            } else {
                WarmthHaptics.warning()
            }
        }
    }

    private func openSettings() {
        guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
        openURL(url)
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

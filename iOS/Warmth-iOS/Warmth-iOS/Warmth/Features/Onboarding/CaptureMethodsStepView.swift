import SwiftUI

/// Reusable toggles for capture activation methods (onboarding + settings).
struct CaptureMethodsPicker: View {
    @Binding var preferences: CaptureActivationPreferences
    var showsSetupHints: Bool = false

    var body: some View {
        VStack(spacing: 10) {
            ForEach(CaptureActivationMethod.allCases) { method in
                methodRow(method)
            }

            if showsSetupHints {
                setupHints
            }
        }
    }

    private func methodRow(_ method: CaptureActivationMethod) -> some View {
        Toggle(isOn: binding(for: method)) {
            HStack(spacing: 12) {
                Image(systemName: method.systemImage)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundStyle(WarmthColor.emberOrange)
                    .frame(width: 28)
                VStack(alignment: .leading, spacing: 2) {
                    Text(method.title)
                        .warmthText(.Warmth.body)
                    Text(method.subtitle)
                        .warmthText(.Warmth.caption, color: WarmthColor.inkSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .tint(WarmthColor.emberRed)
    }

    private var setupHints: some View {
        VStack(alignment: .leading, spacing: 8) {
            if preferences.isEnabled(.siri) {
                Text("Tip: After setup, try “Hey Siri, I'm meeting Sarah with Warmth”.")
                    .warmthText(.Warmth.caption, color: WarmthColor.inkSecondary)
            }
            if preferences.isEnabled(.actionButton) {
                Text("Action Button: Settings → Action Button → Shortcut → Start Warmth Capture.")
                    .warmthText(.Warmth.caption, color: WarmthColor.inkSecondary)
            }
            if preferences.isEnabled(.passiveFloorListening) {
                Text("Floor listening uses 30s auto-capture windows when a contact name is heard.")
                    .warmthText(.Warmth.caption, color: WarmthColor.inkSecondary)
            }
        }
        .padding(.top, 4)
    }

    private func binding(for method: CaptureActivationMethod) -> Binding<Bool> {
        Binding(
            get: { preferences.isEnabled(method) },
            set: { enabled in
                preferences.setEnabled(method, enabled: enabled)
            }
        )
    }
}

/// Onboarding step — choose how capture starts.
struct CaptureMethodsStepView: View {
    @Environment(AppModel.self) private var model
    let advance: () -> Void

    var body: some View {
        VStack(spacing: 24) {
            VStack(spacing: 12) {
                Image(systemName: "hand.tap.fill")
                    .font(.system(size: 44, weight: .semibold))
                    .foregroundStyle(WarmthColor.emberGradient)

                Text("How do you want to capture?")
                    .warmthText(.Warmth.largeTitle)
                    .multilineTextAlignment(.center)

                Text("Pick every way you'd like to start recording. You can change these anytime in Settings.")
                    .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                    .multilineTextAlignment(.center)
            }

            GlassCard {
                CaptureMethodsPicker(
                    preferences: Binding(
                        get: { model.settings.capturePreferences },
                        set: { model.settings.capturePreferences = $0 }
                    )
                )
            }

            EmberButton(title: "Continue", systemImage: "arrow.right", action: advance)
        }
    }
}

#Preview {
    ZStack {
        MeshGradientBackground()
        CaptureMethodsStepView(advance: {})
            .padding()
    }
    .environment(AppModel.preview)
}

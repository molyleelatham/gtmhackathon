import SwiftUI

/// Step 6 — celebratory finish. Tapping "Start capturing" completes onboarding.
struct FinishStepView: View {
    @Environment(AppModel.self) private var model
    let finish: () -> Void

    @State private var pulse = false

    var body: some View {
        VStack(spacing: 28) {
            ZStack {
                Circle()
                    .fill(WarmthColor.emberGlow)
                    .frame(width: 200, height: 200)
                    .scaleEffect(pulse ? 1.1 : 0.9)
                    .blur(radius: 6)

                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 96, weight: .bold))
                    .foregroundStyle(WarmthColor.emberGradient)
                    .shadow(color: WarmthColor.emberOrange.opacity(0.5), radius: 24)
            }
            .frame(height: 210)

            VStack(spacing: 12) {
                Text(greeting)
                    .warmthText(.Warmth.largeTitle)
                    .multilineTextAlignment(.center)

                Text(finishCopy)
                    .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                    .multilineTextAlignment(.center)
            }

            EmberButton(title: "Start capturing", systemImage: "waveform", action: finish)
                .padding(.top, 8)
        }
        .onAppear {
            withAnimation(WarmthMotion.breathe) { pulse = true }
        }
    }

    private var greeting: String {
        if let name = model.authState.user?.displayName, !name.isEmpty {
            return "You're all set, \(name)."
        }
        return "You're all set."
    }

    private var finishCopy: String {
        let prefs = model.settings.capturePreferences
        var hints: [String] = []
        if prefs.isEnabled(.siri) {
            hints.append("“Hey Siri, I'm meeting someone with Warmth”")
        }
        if prefs.isEnabled(.watch) {
            hints.append("tap your watch")
        }
        if prefs.isEnabled(.manual) {
            hints.append("tap the ember orb")
        }
        guard !hints.isEmpty else {
            return "Open Capture when you're ready to record an introduction."
        }
        if hints.count == 1 {
            return "Try \(hints[0]) when you meet someone new."
        }
        let last = hints.removeLast()
        return "Try \(hints.joined(separator: ", ")), or \(last) when you meet someone new."
    }
}

#Preview {
    ZStack {
        MeshGradientBackground()
        FinishStepView(finish: {})
            .padding()
    }
    .environment(AppModel.preview)
}

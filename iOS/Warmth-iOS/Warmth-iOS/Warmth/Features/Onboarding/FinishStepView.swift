import SwiftUI

/// Step 5 — celebratory finish. Tapping "Start capturing" completes onboarding.
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

                Text("Just say “\(WakeWord.phrase)” and Warmth will remember every introduction for you.")
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
        if let name = model.auth.state.user?.displayName, !name.isEmpty {
            return "You're all set, \(name)."
        }
        return "You're all set."
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

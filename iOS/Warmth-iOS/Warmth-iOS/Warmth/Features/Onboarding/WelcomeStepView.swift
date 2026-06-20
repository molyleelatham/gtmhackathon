import SwiftUI

/// Step 1 — brand reveal with a glowing ember hero and the "Get started" CTA.
struct WelcomeStepView: View {
    let advance: () -> Void

    @State private var glow = false

    var body: some View {
        VStack(spacing: 28) {
            emberHero

            VStack(spacing: 12) {
                Text("Warmth")
                    .warmthText(.Warmth.hero)
                    .overlay(WarmthColor.emberGradient.mask(
                        Text("Warmth").font(.Warmth.hero)
                    ))

                Text("Never forget a conversation.")
                    .warmthText(.Warmth.title2, color: WarmthColor.inkSecondary)
                    .multilineTextAlignment(.center)
            }

            EmberButton(title: "Get started", systemImage: "sparkles", action: advance)
                .padding(.top, 8)
        }
        .onAppear {
            withAnimation(WarmthMotion.breathe) { glow = true }
        }
    }

    private var emberHero: some View {
        ZStack {
            Circle()
                .fill(WarmthColor.emberGlow)
                .frame(width: 220, height: 220)
                .scaleEffect(glow ? 1.08 : 0.92)
                .blur(radius: 8)

            Circle()
                .fill(WarmthColor.emberGradient)
                .frame(width: 116, height: 116)
                .shadow(color: WarmthColor.emberOrange.opacity(0.6), radius: 30)
                .scaleEffect(glow ? 1.04 : 0.96)

            Image(systemName: "flame.fill")
                .font(.system(size: 52, weight: .bold))
                .foregroundStyle(WarmthColor.warmWhite)
        }
        .frame(height: 240)
    }
}

#Preview {
    ZStack {
        MeshGradientBackground()
        WelcomeStepView(advance: {})
            .padding()
    }
    .environment(AppModel.preview)
}

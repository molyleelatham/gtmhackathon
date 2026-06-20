import SwiftUI

/// Animated warm mesh gradient that slowly drifts ember tones across a warm-white
/// canvas. Used as the ambient backdrop on every primary screen.
struct MeshGradientBackground: View {
    /// When true the mesh animates faster and glows brighter (used while recording).
    var intensity: Double = 1.0
    var animated: Bool = true

    @State private var phase: CGFloat = 0

    private var points: [SIMD2<Float>] {
        let drift = Float(sin(phase)) * 0.08
        let drift2 = Float(cos(phase)) * 0.08
        return [
            [0.0, 0.0], [0.5, 0.0], [1.0, 0.0],
            [0.0, 0.5], [0.5 + drift, 0.5 + drift2], [1.0, 0.5],
            [0.0, 1.0], [0.5, 1.0], [1.0, 1.0]
        ]
    }

    private var colors: [Color] {
        let a = WarmthColor.amber.opacity(0.55 * intensity)
        let o = WarmthColor.emberOrange.opacity(0.6 * intensity)
        let r = WarmthColor.emberRed.opacity(0.5 * intensity)
        return [
            WarmthColor.warmWhite, a, WarmthColor.warmWhite,
            o, r, a,
            WarmthColor.warmWhite, o, WarmthColor.warmWhite
        ]
    }

    var body: some View {
        MeshGradient(width: 3, height: 3, points: points, colors: colors)
            .overlay(WarmthColor.warmWhite.opacity(0.48))
            .ignoresSafeArea()
            .onAppear {
                guard animated else { return }
                withAnimation(.easeInOut(duration: 7).repeatForever(autoreverses: true)) {
                    phase = .pi * 2
                }
            }
    }
}

#Preview {
    MeshGradientBackground(intensity: 1.2)
}

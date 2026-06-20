import SwiftUI

/// Compact "ember" palette for watchOS — a glanceable subset of the phone brand.
/// Colors are sRGB so previews and device render identically.
enum WatchTheme {
    /// #FF2D1A — hottest ember red. Primary accent.
    static let emberRed = Color(red: 1.0, green: 0x2D / 255, blue: 0x1A / 255)
    /// #FF5A2C — orange-red mid tone.
    static let emberOrange = Color(red: 1.0, green: 0x5A / 255, blue: 0x2C / 255)
    /// #FF9A3D — amber, the coolest ember.
    static let amber = Color(red: 1.0, green: 0x9A / 255, blue: 0x3D / 255)

    /// #FBF8F5 — warm white. Used sparingly for primary text on the dark watch face.
    static let warmWhite = Color(red: 0xFB / 255, green: 0xF8 / 255, blue: 0xF5 / 255)
    /// #0B0B0C — near-black ink. The watch canvas is dark for OLED + glance contrast.
    static let ink = Color(red: 0x0B / 255, green: 0x0B / 255, blue: 0x0C / 255)
    /// Muted warm white for secondary copy on the dark canvas.
    static let textSecondary = warmWhite.opacity(0.6)

    /// Signature ember gradient (hot → amber).
    static let emberGradient = LinearGradient(
        colors: [emberRed, emberOrange, amber],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    /// Radial glow behind the record orb / key accents.
    static func emberGlow(radius: CGFloat) -> RadialGradient {
        RadialGradient(
            colors: [emberOrange.opacity(0.85), emberRed.opacity(0.0)],
            center: .center,
            startRadius: 2,
            endRadius: radius
        )
    }

    /// The dark, slightly warm background used across the watch app.
    static let canvas = LinearGradient(
        colors: [Color(red: 0x14 / 255, green: 0x0A / 255, blue: 0x08 / 255), ink],
        startPoint: .top,
        endPoint: .bottom
    )
}

/// Space Grotesk type ramp for the watch. `.custom` degrades gracefully to the
/// system font if the bundled faces are not registered yet, so screens never break.
extension Font {
    enum WatchType {
        static func grotesk(_ weight: SpaceGroteskFace, size: CGFloat) -> Font {
            .custom(weight.fontName, size: size)
        }

        static let timer = grotesk(.bold, size: 34)
        static let hero = grotesk(.bold, size: 26)
        static let title = grotesk(.semiBold, size: 18)
        static let body = grotesk(.medium, size: 15)
        static let caption = grotesk(.medium, size: 12)
        static let label = grotesk(.semiBold, size: 13)
    }
}

/// Maps semantic weights to the bundled Space Grotesk PostScript names.
enum SpaceGroteskFace {
    case regular, medium, semiBold, bold

    var fontName: String {
        switch self {
        case .regular: return "SpaceGrotesk-Regular"
        case .medium: return "SpaceGrotesk-Medium"
        case .semiBold: return "SpaceGrotesk-SemiBold"
        case .bold: return "SpaceGrotesk-Bold"
        }
    }
}

/// A glowing, pulsing ember orb — the heartbeat of the "recording" state.
/// Purely decorative; size is driven by the caller's frame.
struct PulsingEmberIndicator: View {
    /// When false the orb sits calm (used for idle / "armed" affordances).
    var isActive: Bool = true
    var diameter: CGFloat = 64

    @State private var pulse = false

    var body: some View {
        ZStack {
            Circle()
                .fill(WatchTheme.emberGlow(radius: diameter))
                .frame(width: diameter * 2, height: diameter * 2)
                .opacity(isActive ? (pulse ? 0.9 : 0.4) : 0.25)

            Circle()
                .fill(WatchTheme.emberGradient)
                .frame(width: diameter, height: diameter)
                .scaleEffect(isActive ? (pulse ? 1.08 : 0.92) : 1.0)
                .shadow(color: WatchTheme.emberRed.opacity(0.7), radius: pulse ? 12 : 6)

            Image(systemName: "waveform")
                .font(.system(size: diameter * 0.34, weight: .bold))
                .foregroundStyle(WatchTheme.warmWhite)
        }
        .onAppear {
            guard isActive else { return }
            withAnimation(.easeInOut(duration: 0.9).repeatForever(autoreverses: true)) {
                pulse = true
            }
        }
    }
}

#Preview("Ember indicator") {
    ZStack {
        WatchTheme.canvas.ignoresSafeArea()
        PulsingEmberIndicator(isActive: true, diameter: 64)
    }
}

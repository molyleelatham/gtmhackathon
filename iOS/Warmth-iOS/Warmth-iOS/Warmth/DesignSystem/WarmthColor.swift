import SwiftUI

/// Warmth's "ember" palette: vibrant red → orange on warm white, with black ink text.
/// All colors are defined in sRGB so they render identically across previews and device.
enum WarmthColor {
    /// #FF2D1A — the hottest ember red. Primary brand accent.
    static let emberRed = Color(red: 1.0, green: 0x2D / 255, blue: 0x1A / 255)
    /// #FF5A2C — orange-red mid tone.
    static let emberOrange = Color(red: 1.0, green: 0x5A / 255, blue: 0x2C / 255)
    /// #FF9A3D — amber, the coolest ember.
    static let amber = Color(red: 1.0, green: 0x9A / 255, blue: 0x3D / 255)

    /// #FBF8F5 — warm white canvas.
    static let warmWhite = Color(red: 0xFB / 255, green: 0xF8 / 255, blue: 0xF5 / 255)
    /// #0B0B0C — near-black ink for all text.
    static let ink = Color(red: 0x0B / 255, green: 0x0B / 255, blue: 0x0C / 255)
    /// Muted ink for secondary copy.
    static let inkSecondary = Color(red: 0x0B / 255, green: 0x0B / 255, blue: 0x0C / 255).opacity(0.55)

    /// The signature ember gradient (hot → amber).
    static let emberGradient = LinearGradient(
        colors: [emberRed, emberOrange, amber],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    /// Radial glow used behind the record orb and key accents.
    static let emberGlow = RadialGradient(
        colors: [emberOrange.opacity(0.9), emberRed.opacity(0.0)],
        center: .center,
        startRadius: 4,
        endRadius: 160
    )
}

/// Warmth "bands" classify a connection by how strong / fresh the lead is.
/// Backed by the ICP keyword score so the UI can color-code people consistently.
enum WarmthBand: String, CaseIterable, Sendable {
    case hot = "Hot"
    case warm = "Warm"
    case cool = "Cool"

    /// Map an ICP keyword score (0–100) onto a band.
    init(score: Int) {
        switch score {
        case 70...: self = .hot
        case 40..<70: self = .warm
        default: self = .cool
        }
    }

    var tint: Color {
        switch self {
        case .hot: return WarmthColor.emberRed
        case .warm: return WarmthColor.emberOrange
        case .cool: return WarmthColor.amber
        }
    }

    var label: String { rawValue }
}

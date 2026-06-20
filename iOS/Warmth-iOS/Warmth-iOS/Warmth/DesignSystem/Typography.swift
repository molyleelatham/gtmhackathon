import SwiftUI

/// Space Grotesk type ramp. Falls back gracefully to the system font if the
/// custom faces fail to register (e.g. in a stripped preview environment).
extension Font {
    enum Warmth {
        static func custom(_ weight: SpaceGroteskWeight, size: CGFloat) -> Font {
            .custom(weight.fontName, size: size)
        }

        // Display / hero
        static let hero = custom(.bold, size: 44)
        static let largeTitle = custom(.bold, size: 34)
        static let title = custom(.semiBold, size: 26)
        static let title2 = custom(.semiBold, size: 21)
        static let headline = custom(.medium, size: 17)
        static let body = custom(.regular, size: 17)
        static let callout = custom(.regular, size: 15)
        static let subheadline = custom(.medium, size: 14)
        static let footnote = custom(.regular, size: 13)
        static let caption = custom(.medium, size: 12)
        static let mono = custom(.medium, size: 15)
    }
}

/// Maps semantic weights to the bundled Space Grotesk PostScript names.
enum SpaceGroteskWeight {
    case light, regular, medium, semiBold, bold

    var fontName: String {
        switch self {
        case .light: return "SpaceGrotesk-Light"
        case .regular: return "SpaceGrotesk-Regular"
        case .medium: return "SpaceGrotesk-Medium"
        case .semiBold: return "SpaceGrotesk-SemiBold"
        case .bold: return "SpaceGrotesk-Bold"
        }
    }
}

extension View {
    /// Applies a Warmth font plus the ink foreground in one call.
    func warmthText(_ font: Font, color: Color = WarmthColor.ink) -> some View {
        self.font(font).foregroundStyle(color)
    }
}

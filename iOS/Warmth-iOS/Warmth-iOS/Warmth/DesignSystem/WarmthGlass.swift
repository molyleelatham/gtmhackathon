import SwiftUI

/// Shared Liquid Glass presets tuned for Warmth's light, warm surfaces.
enum WarmthGlassStyle {
    /// Standard card / panel glass with a warm white tint.
    static var card: Glass { .regular.tint(WarmthColor.glassTint) }
    /// Interactive controls that respond to touch.
    static var interactive: Glass { card.interactive() }
}

extension View {
    /// Applies Warmth's warm-tinted Liquid Glass with an optional light surface fill.
    func warmthGlass(_ style: Glass = WarmthGlassStyle.card, in shape: some InsettableShape, fillSurface: Bool = true) -> some View {
        modifier(WarmthGlassModifier(style: style, shape: shape, fillSurface: fillSurface))
    }
}

private struct WarmthGlassModifier<S: InsettableShape>: ViewModifier {
    let style: Glass
    let shape: S
    var fillSurface: Bool

    func body(content: Content) -> some View {
        content
            .background {
                if fillSurface {
                    shape.fill(WarmthColor.surfaceWarm.opacity(0.84))
                }
            }
            .glassEffect(style, in: shape)
    }
}

/// A rounded Liquid Glass surface used as the base for cards and sheets.
struct GlassCard<Content: View>: View {
    var cornerRadius: CGFloat = 24
    var padding: CGFloat = 18
    @ViewBuilder var content: Content

    private var cardShape: RoundedRectangle {
        RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
    }

    var body: some View {
        content
            .padding(padding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .warmthGlass(WarmthGlassStyle.card, in: cardShape)
            .overlay(cardShape.strokeBorder(WarmthColor.surfaceBorder.opacity(0.7), lineWidth: 0.5))
    }
}

/// Primary Warmth button: ember gradient fill, glass-clipped, with a press spring.
struct EmberButton: View {
    let title: String
    var systemImage: String?
    var fill: Bool = true
    let action: () -> Void

    @State private var pressed = false

    var body: some View {
        Button(action: {
            WarmthHaptics.impact(.light)
            action()
        }) {
            HStack(spacing: 8) {
                if let systemImage {
                    Image(systemName: systemImage)
                }
                Text(title)
            }
            .font(.Warmth.headline)
            .foregroundStyle(fill ? WarmthColor.warmWhite : WarmthColor.ink)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background {
                if fill {
                    Capsule().fill(WarmthColor.emberGradient)
                }
            }
            .clipShape(Capsule())
            .warmthGlass(WarmthGlassStyle.interactive, in: Capsule(), fillSurface: fill)
            .scaleEffect(pressed ? 0.97 : 1)
        }
        .buttonStyle(.plain)
        .animation(WarmthMotion.snappy, value: pressed)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in pressed = true }
                .onEnded { _ in pressed = false }
        )
    }
}

/// Small pill used for interest / topic chips.
struct InterestChip: View {
    let text: String
    var tint: Color = WarmthColor.emberOrange

    var body: some View {
        Text(text)
            .font(.Warmth.caption)
            .foregroundStyle(WarmthColor.ink)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(tint.opacity(0.18), in: .capsule)
            .overlay(Capsule().strokeBorder(tint.opacity(0.4), lineWidth: 0.5))
    }
}

/// Colored dot + label communicating a connection's warmth band.
struct WarmthBadge: View {
    let band: WarmthBand
    let score: Int

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(band.tint)
                .frame(width: 8, height: 8)
                .shadow(color: band.tint.opacity(0.7), radius: 4)
            Text("\(band.label) · \(score)")
                .font(.Warmth.caption)
                .foregroundStyle(WarmthColor.ink)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .warmthGlass(WarmthGlassStyle.card, in: Capsule())
    }
}

#Preview {
    ZStack {
        MeshGradientBackground()
        VStack(spacing: 20) {
            GlassCard {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Maya Chen").font(.Warmth.title2)
                    Text("NorthWind Labs").font(.Warmth.callout).foregroundStyle(WarmthColor.inkSecondary)
                    HStack { InterestChip(text: "RevOps"); InterestChip(text: "attribution") }
                }
            }
            WarmthBadge(band: .hot, score: 82)
            EmberButton(title: "Continue", systemImage: "arrow.right") {}
            EmberButton(title: "Skip", fill: false) {}
        }
        .padding()
    }
}

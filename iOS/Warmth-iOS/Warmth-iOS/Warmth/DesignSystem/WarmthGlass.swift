import SwiftUI

/// A rounded Liquid Glass surface used as the base for cards and sheets.
struct GlassCard<Content: View>: View {
    var cornerRadius: CGFloat = 24
    var padding: CGFloat = 18
    @ViewBuilder var content: Content

    var body: some View {
        content
            .padding(padding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .glassEffect(.regular, in: .rect(cornerRadius: cornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .strokeBorder(WarmthColor.warmWhite.opacity(0.4), lineWidth: 0.5)
            )
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
            .glassEffect(.regular.interactive(), in: .capsule)
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
            .background(tint.opacity(0.16), in: .capsule)
            .overlay(Capsule().strokeBorder(tint.opacity(0.35), lineWidth: 0.5))
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
        .glassEffect(.regular, in: .capsule)
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

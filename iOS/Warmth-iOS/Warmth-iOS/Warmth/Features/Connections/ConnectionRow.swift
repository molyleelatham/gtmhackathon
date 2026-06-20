import SwiftUI

/// A single glass-styled connection row in the Connections list.
struct ConnectionRow: View {
    let connection: CRMConnection

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 14) {
                    AvatarBadge(initials: connection.initials, size: 48)

                    VStack(alignment: .leading, spacing: 3) {
                        Text(connection.name)
                            .warmthText(.Warmth.headline)
                            .lineLimit(1)

                        if let subtitle {
                            Text(subtitle)
                                .warmthText(.Warmth.subheadline, color: WarmthColor.inkSecondary)
                                .lineLimit(1)
                        }
                    }

                    Spacer(minLength: 8)

                    WarmthBadge(band: connection.band, score: connection.predictedWarmth)
                }

                if !connection.interests.isEmpty {
                    WarmthFlowLayout(spacing: 8, lineSpacing: 8) {
                        ForEach(connection.interests.prefix(3), id: \.self) { interest in
                            InterestChip(text: interest, tint: connection.band.tint)
                        }
                    }
                }
            }
        }
    }

    private var subtitle: String? {
        switch (connection.org, connection.role) {
        case let (org?, role?): return "\(org) · \(role)"
        case let (org?, nil): return org
        case let (nil, role?): return role
        default: return nil
        }
    }
}

/// Circular avatar filled with the ember gradient, showing a person's initials.
struct AvatarBadge: View {
    let initials: String
    var size: CGFloat = 48
    var glow: Bool = false

    var body: some View {
        Circle()
            .fill(WarmthColor.emberGradient)
            .frame(width: size, height: size)
            .overlay(
                Text(initials)
                    .font(.Warmth.custom(.semiBold, size: size * 0.38))
                    .foregroundStyle(WarmthColor.warmWhite)
            )
            .overlay(Circle().strokeBorder(WarmthColor.warmWhite.opacity(0.5), lineWidth: 0.5))
            .shadow(color: glow ? WarmthColor.emberOrange.opacity(0.6) : .clear,
                    radius: glow ? 18 : 0)
    }
}

#Preview {
    ZStack {
        MeshGradientBackground()
        VStack(spacing: 14) {
            ForEach(CRMConnection.previewList) { connection in
                ConnectionRow(connection: connection)
            }
        }
        .padding()
    }
}

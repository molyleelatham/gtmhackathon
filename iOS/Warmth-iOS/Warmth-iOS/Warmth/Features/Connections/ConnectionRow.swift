import SwiftUI

/// A single glass-styled person row in the Connections list: ember avatar, name,
/// org · role, warmth badge, and a few interest chips.
struct ConnectionRow: View {
    let person: PersonNode

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 14) {
                    AvatarBadge(initials: person.initials, size: 48)

                    VStack(alignment: .leading, spacing: 3) {
                        Text(person.name)
                            .warmthText(.Warmth.headline)
                            .lineLimit(1)

                        if let subtitle {
                            Text(subtitle)
                                .warmthText(.Warmth.subheadline, color: WarmthColor.inkSecondary)
                                .lineLimit(1)
                        }
                    }

                    Spacer(minLength: 8)

                    WarmthBadge(band: person.band, score: person.icpScore)
                }

                if !person.interests.isEmpty {
                    HStack(spacing: 8) {
                        ForEach(person.interests.prefix(3), id: \.self) { interest in
                            InterestChip(text: interest, tint: person.band.tint)
                        }
                    }
                }
            }
        }
    }

    private var subtitle: String? {
        switch (person.org, person.role) {
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
            ForEach(PersonNode.mockData.prefix(3)) { person in
                ConnectionRow(person: person)
            }
        }
        .padding()
    }
}

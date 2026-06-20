import SwiftUI

/// Horizontal strip of the people captured this session, pinned near the bottom of
/// the Capture screen. Falls back to seeded `PersonNode.mockData` so the demo never
/// looks empty before the first capture lands.
struct RecentConnectionsStrip: View {
    let people: [PersonNode]

    private var displayed: [PersonNode] {
        people.isEmpty ? PersonNode.mockData : people
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Recently met")
                .font(.Warmth.subheadline)
                .foregroundStyle(WarmthColor.inkSecondary)
                .padding(.horizontal, 20)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 14) {
                    ForEach(displayed) { person in
                        RecentConnectionCard(person: person)
                    }
                }
                .padding(.horizontal, 20)
            }
        }
    }
}

/// A single avatar tile within the recent-connections strip.
private struct RecentConnectionCard: View {
    let person: PersonNode

    var body: some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .fill(WarmthColor.emberGradient)
                    .frame(width: 56, height: 56)
                    .overlay(Circle().strokeBorder(WarmthColor.warmWhite.opacity(0.4), lineWidth: 1))
                    .shadow(color: person.band.tint.opacity(0.5), radius: 8, y: 4)
                Text(person.initials)
                    .font(.Warmth.headline)
                    .foregroundStyle(WarmthColor.warmWhite)
            }

            Text(person.name)
                .font(.Warmth.caption)
                .foregroundStyle(WarmthColor.ink)
                .lineLimit(1)

            WarmthBadge(band: person.band, score: person.icpScore)
        }
        .frame(width: 92)
        .padding(.vertical, 14)
        .padding(.horizontal, 6)
        .glassEffect(.regular, in: .rect(cornerRadius: 20))
    }
}

#Preview("Populated") {
    ZStack {
        MeshGradientBackground()
        RecentConnectionsStrip(people: PersonNode.mockData)
    }
}

#Preview("Fallback (empty)") {
    ZStack {
        MeshGradientBackground()
        RecentConnectionsStrip(people: [])
    }
}

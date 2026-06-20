import SwiftUI

/// Horizontal strip of the warmest recent connections from the backend CRM.
struct RecentConnectionsStrip: View {
    let connections: [CRMConnection]

    private var displayed: [CRMConnection] {
        Array(connections.prefix(6))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Recently met")
                .font(.Warmth.subheadline)
                .foregroundStyle(WarmthColor.inkSecondary)
                .padding(.horizontal, 20)

            if displayed.isEmpty {
                Text("Capture someone to see them here and on the web dashboard.")
                    .font(.Warmth.footnote)
                    .foregroundStyle(WarmthColor.inkSecondary)
                    .padding(.horizontal, 20)
            } else {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 14) {
                        ForEach(displayed) { connection in
                            RecentConnectionCard(connection: connection)
                        }
                    }
                    .padding(.horizontal, 20)
                }
            }
        }
    }
}

private struct RecentConnectionCard: View {
    let connection: CRMConnection

    var body: some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .fill(WarmthColor.emberGradient)
                    .frame(width: 56, height: 56)
                    .overlay(Circle().strokeBorder(WarmthColor.warmWhite.opacity(0.4), lineWidth: 1))
                    .shadow(color: connection.band.tint.opacity(0.5), radius: 8, y: 4)
                Text(connection.initials)
                    .font(.Warmth.headline)
                    .foregroundStyle(WarmthColor.warmWhite)
            }

            Text(connection.name)
                .font(.Warmth.caption)
                .foregroundStyle(WarmthColor.ink)
                .lineLimit(1)

            WarmthBadge(band: connection.band, score: connection.predictedWarmth)
        }
        .frame(width: 92)
        .padding(.vertical, 14)
        .padding(.horizontal, 6)
        .warmthGlass(WarmthGlassStyle.card, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
    }
}

#Preview("Populated") {
    ZStack {
        MeshGradientBackground()
        RecentConnectionsStrip(connections: CRMConnection.previewList)
    }
}

#Preview("Empty") {
    ZStack {
        MeshGradientBackground()
        RecentConnectionsStrip(connections: [])
    }
}

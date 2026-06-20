import SwiftUI

/// Full profile for one captured person: hero header, interests, relations, an
/// ICP gauge, and the raw transcript excerpt — all over the ambient mesh.
struct ConnectionDetailView: View {
    let person: PersonNode

    var body: some View {
        ZStack {
            MeshGradientBackground()

            ScrollView {
                VStack(spacing: 18) {
                    header

                    if !person.interests.isEmpty {
                        section("Interests") {
                            WarmthFlowLayout(spacing: 8, lineSpacing: 8) {
                                ForEach(person.interests, id: \.self) { interest in
                                    InterestChip(text: interest, tint: person.band.tint)
                                }
                            }
                        }
                    }

                    if !person.relations.isEmpty {
                        section("Relations") {
                            VStack(alignment: .leading, spacing: 10) {
                                ForEach(person.relations, id: \.self) { relation in
                                    RelationLine(relation: relation, tint: person.band.tint)
                                }
                            }
                        }
                    }

                    section("ICP score") {
                        ICPGauge(score: person.icpScore, band: person.band)
                    }

                    if !person.transcriptExcerpt.isEmpty {
                        section("Transcript") {
                            Text(person.transcriptExcerpt)
                                .warmthText(.Warmth.body, color: WarmthColor.inkSecondary)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 40)
            }
            .scrollContentBackground(.hidden)
        }
        .navigationTitle(person.name)
        .navigationBarTitleDisplayMode(.inline)
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: 14) {
            AvatarBadge(initials: person.initials, size: 96, glow: true)
                .padding(.top, 8)

            VStack(spacing: 6) {
                Text(person.name)
                    .warmthText(.Warmth.largeTitle)
                    .multilineTextAlignment(.center)

                if let subtitle {
                    Text(subtitle)
                        .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                        .multilineTextAlignment(.center)
                }
            }

            WarmthBadge(band: person.band, score: person.icpScore)
        }
        .frame(maxWidth: .infinity)
        .padding(.bottom, 4)
    }

    private var subtitle: String? {
        switch (person.org, person.role) {
        case let (org?, role?): return "\(org) · \(role)"
        case let (org?, nil): return org
        case let (nil, role?): return role
        default: return nil
        }
    }

    @ViewBuilder
    private func section<Content: View>(_ title: String,
                                        @ViewBuilder content: () -> Content) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                Text(title.uppercased())
                    .font(.Warmth.caption)
                    .tracking(1.2)
                    .foregroundStyle(WarmthColor.inkSecondary)
                content()
            }
        }
    }
}

/// A single subject · predicate · object relation, with the predicate humanized.
private struct RelationLine: View {
    let relation: CapturedSignal.Relation
    let tint: Color

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Circle()
                .fill(tint)
                .frame(width: 6, height: 6)
            (
                Text(relation.subject).foregroundStyle(WarmthColor.ink)
                + Text("  \(humanized)  ").foregroundStyle(WarmthColor.inkSecondary)
                + Text(relation.object).foregroundStyle(WarmthColor.ink)
            )
            .font(.Warmth.callout)
            .fixedSize(horizontal: false, vertical: true)
        }
    }

    private var humanized: String {
        relation.predicate.replacingOccurrences(of: "_", with: " ")
    }
}

/// Horizontal 0–100 gauge tinted by the warmth band.
private struct ICPGauge: View {
    let score: Int
    let band: WarmthBand

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(band.label)
                    .warmthText(.Warmth.headline, color: band.tint)
                Spacer()
                Text("\(score) / 100")
                    .warmthText(.Warmth.subheadline, color: WarmthColor.inkSecondary)
            }

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(WarmthColor.surfaceMuted)
                    Capsule()
                        .fill(WarmthColor.emberGradient)
                        .frame(width: max(8, geo.size.width * fraction))
                        .shadow(color: band.tint.opacity(0.5), radius: 6)
                }
            }
            .frame(height: 12)
        }
    }

    private var fraction: CGFloat {
        CGFloat(min(100, max(0, score))) / 100
    }
}

/// Lightweight wrapping layout for chip rows (no external dependency).
struct WarmthFlowLayout: Layout {
    var spacing: CGFloat = 8
    var lineSpacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let maxWidth = proposal.width ?? .infinity
        var rowWidth: CGFloat = 0
        var rowHeight: CGFloat = 0
        var totalHeight: CGFloat = 0
        var totalWidth: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if rowWidth + size.width > maxWidth, rowWidth > 0 {
                totalHeight += rowHeight + lineSpacing
                totalWidth = max(totalWidth, rowWidth - spacing)
                rowWidth = 0
                rowHeight = 0
            }
            rowWidth += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
        totalHeight += rowHeight
        totalWidth = max(totalWidth, rowWidth - spacing)
        return CGSize(width: min(totalWidth, maxWidth), height: totalHeight)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var x = bounds.minX
        var y = bounds.minY
        var rowHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x + size.width > bounds.maxX, x > bounds.minX {
                x = bounds.minX
                y += rowHeight + lineSpacing
                rowHeight = 0
            }
            subview.place(at: CGPoint(x: x, y: y), anchor: .topLeading,
                          proposal: ProposedViewSize(size))
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
    }
}

#Preview {
    NavigationStack {
        ConnectionDetailView(person: PersonNode.preview)
    }
    .environment(AppModel.preview)
}

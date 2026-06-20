import SwiftUI

/// Full profile for one CRM connection — fetches warmth + draft from the backend
/// so iOS stays in sync with the web dashboard detail page.
struct ConnectionDetailView: View {
    @Environment(AppModel.self) private var model
    let connection: CRMConnection

    @State private var detail: CRMConnectionDetail?
    @State private var loadError: String?

    private var display: CRMConnection { detail?.connection ?? connection }
    private var warmth: CRMWarmthScore? { detail?.warmth }
    private var draftBody: String? {
        detail?.gmailDraft?["body"] ?? display.draftBody
    }
    private var draftSubject: String? {
        detail?.gmailDraft?["subject"] ?? display.draftSubject
    }

    var body: some View {
        ZStack {
            MeshGradientBackground()

            ScrollView {
                VStack(spacing: 18) {
                    header

                    if !display.interests.isEmpty {
                        section("Interest knowledge graph") {
                            KnowledgeGraphMiniView(
                                personName: display.name,
                                interests: display.interests,
                                values: []
                            )
                            .frame(height: 240)
                        }

                        section("Interests") {
                            WarmthFlowLayout(spacing: 8, lineSpacing: 8) {
                                ForEach(display.interests, id: \.self) { interest in
                                    InterestChip(text: interest, tint: display.band.tint)
                                }
                            }
                        }
                    }

                    section("Warmth score") {
                        ICPGauge(
                            score: warmthScore,
                            band: WarmthBand(score: warmthScore)
                        )
                        if let warmth {
                            HStack {
                                Text("ICP fit")
                                    .warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)
                                Spacer()
                                Text("\(warmth.icpScore)")
                                    .warmthText(.Warmth.footnote)
                            }
                        }
                    }

                    if let draftSubject, let draftBody {
                        section("Outreach draft") {
                            VStack(alignment: .leading, spacing: 8) {
                                Text(draftSubject)
                                    .warmthText(.Warmth.headline)
                                Text(draftBody)
                                    .warmthText(.Warmth.body, color: WarmthColor.inkSecondary)
                                    .fixedSize(horizontal: false, vertical: true)
                            }
                        }
                    }

                    if let loadError {
                        Text(loadError)
                            .warmthText(.Warmth.footnote, color: WarmthColor.emberRed)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 40)
            }
            .scrollContentBackground(.hidden)
        }
        .navigationTitle(display.name)
        .navigationBarTitleDisplayMode(.inline)
        .task(id: connection.id) {
            await loadDetail()
        }
        .refreshable { await loadDetail() }
    }

    private var warmthScore: Int {
        if let actual = warmth?.actualScore {
            return Int(actual.rounded())
        }
        if let predicted = warmth?.predictedScore {
            return Int(predicted.rounded())
        }
        return display.predictedWarmth
    }

    @MainActor
    private func loadDetail() async {
        loadError = nil
        do {
            detail = try await model.crmClient.connectionDetail(id: connection.id)
        } catch {
            loadError = error.localizedDescription
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: 14) {
            AvatarBadge(initials: display.initials, size: 96, glow: true)
                .padding(.top, 8)

            VStack(spacing: 6) {
                Text(display.name)
                    .warmthText(.Warmth.largeTitle)
                    .multilineTextAlignment(.center)

                if let subtitle {
                    Text(subtitle)
                        .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                        .multilineTextAlignment(.center)
                }
            }

            WarmthBadge(band: display.band, score: warmthScore)
        }
        .frame(maxWidth: .infinity)
        .padding(.bottom, 4)
    }

    private var subtitle: String? {
        switch (display.org, display.role) {
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
        ConnectionDetailView(connection: .preview)
    }
    .environment(AppModel.preview)
}

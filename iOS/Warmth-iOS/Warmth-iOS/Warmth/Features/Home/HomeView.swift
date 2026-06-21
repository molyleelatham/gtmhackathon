import SwiftUI

/// iOS mini-dashboard — stats, hot leads, recently met, community lite, sync status.
struct HomeView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        NavigationStack {
            ZStack {
                MeshGradientBackground()

                ScrollView {
                    VStack(spacing: 18) {
                        if let error = model.homeError {
                            HomeInlineError(message: error) {
                                Task { await model.refreshHome() }
                            }
                        }

                        if let dashboard = model.dashboard {
                            statsSection(dashboard)
                            if !dashboard.topLeads.isEmpty {
                                hotLeadsSection(dashboard.topLeads)
                            }
                        }

                        if let match = model.attendeeMatch, match.matched {
                            attendeeMatchSection(match)
                        }

                        recentlyMetSection
                        communitySection
                        syncSection
                    }
                    .padding(.horizontal, 18)
                    .padding(.top, 8)
                    .padding(.bottom, 32)
                }
                .scrollIndicators(.hidden)
                .refreshable { await model.refreshHome() }
            }
            .navigationTitle("Home")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    EventModeToolbarToggle()
                }
            }
            .task { await model.refreshHome() }
        }
        .tint(WarmthColor.emberRed)
    }

    @ViewBuilder
    private func statsSection(_ dashboard: CRMDashboardSummary) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 14) {
                HomeSectionHeader(title: "Overview", systemImage: "chart.bar.fill")
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                    StatTile(label: "Connections", value: "\(dashboard.connections)")
                    StatTile(label: "Hot leads", value: "\(dashboard.hotLeads)")
                    StatTile(label: "Events", value: "\(dashboard.events)")
                    StatTile(label: "In CRM", value: "\(dashboard.leadsInCRM)")
                }
            }
        }
    }

    @ViewBuilder
    private func hotLeadsSection(_ leads: [CRMConnection]) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                HomeSectionHeader(title: "Hot leads", systemImage: "flame.fill")
                ForEach(leads.prefix(5)) { lead in
                    NavigationLink {
                        ConnectionDetailView(connection: lead)
                    } label: {
                        ConnectionRow(connection: lead)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    @ViewBuilder
    private func attendeeMatchSection(_ match: AttendeeMatchResult) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 8) {
                HomeSectionHeader(title: "Attendee match", systemImage: "person.crop.circle.badge.checkmark")
                Text(match.message)
                    .warmthText(.Warmth.body)
            }
        }
    }

    @ViewBuilder
    private var recentlyMetSection: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                HomeSectionHeader(title: "Recently met", systemImage: "clock.fill")
                if model.recentlyMet.isEmpty {
                    Text("Capture conversations on the floor — they'll show up here.")
                        .warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)
                } else {
                    ForEach(model.recentlyMet.prefix(6)) { row in
                        NavigationLink {
                            ConnectionDetailView(connection: row.connection)
                        } label: {
                            ConnectionRow(connection: row.connection)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var communitySection: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                HomeSectionHeader(title: "Community", systemImage: "person.3.fill")
                if model.communityMembers.isEmpty {
                    Text("Community members load from the backend roster.")
                        .warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)
                } else {
                    ForEach(model.communityMembers) { member in
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(member.name)
                                    .warmthText(.Warmth.body)
                                if !member.interests.isEmpty {
                                    Text(member.interests.prefix(3).joined(separator: " · "))
                                        .warmthText(.Warmth.caption, color: WarmthColor.inkSecondary)
                                        .lineLimit(1)
                                }
                            }
                            Spacer(minLength: 0)
                            if model.routedCommunityUserIDs.contains(member.userId) {
                                Text("Routed")
                                    .font(.Warmth.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(WarmthColor.amber.opacity(0.25), in: Capsule())
                                    .foregroundStyle(WarmthColor.emberOrange)
                            }
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var syncSection: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 10) {
                HomeSectionHeader(title: "Sync", systemImage: "arrow.triangle.2.circlepath")
                HStack(spacing: 8) {
                    Circle()
                        .fill(crmTint)
                        .frame(width: 8, height: 8)
                    Text(crmStatusText)
                        .warmthText(.Warmth.footnote)
                }
                signalDeliveryLine
            }
        }
    }

    private var signalDeliveryLine: some View {
        let state = model.signalClient.deliveryState
        let text: String = switch state {
        case .idle: "Signals idle"
        case .sending: "Sending signal…"
        case .delivered: "Last signal delivered"
        case .queued(let count): "Queued — \(count) waiting"
        case .failed(let message): "Signal failed — \(message)"
        }
        return HStack(spacing: 8) {
            Circle().fill(WarmthColor.amber).frame(width: 8, height: 8)
            Text(text).warmthText(.Warmth.footnote)
        }
    }

    private var crmStatusText: String {
        switch model.crmClient.fetchState {
        case .idle: return "CRM idle"
        case .loading: return "Refreshing CRM…"
        case .loaded: return "\(model.crmClient.connections.count) connections synced"
        case .failed(let message): return "CRM error — \(message)"
        }
    }

    private var crmTint: Color {
        switch model.crmClient.fetchState {
        case .loaded: return WarmthColor.emberOrange
        case .failed: return WarmthColor.emberRed
        case .loading: return WarmthColor.amber
        case .idle: return WarmthColor.inkSecondary
        }
    }
}

private struct EventModeToolbarToggle: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        @Bindable var settings = model.settings

        Toggle(isOn: $settings.eventModeEnabled) {
            Text("Event")
                .font(.Warmth.caption.weight(.semibold))
                .foregroundStyle(WarmthColor.ink)
        }
        .tint(WarmthColor.emberRed)
        .onChange(of: settings.eventModeEnabled) { _, enabled in
            if enabled { WarmthHaptics.success() }
        }
        .accessibilityLabel("Event mode")
        .accessibilityHint("Opens Capture when you relaunch the app.")
    }
}

private struct HomeSectionHeader: View {
    let title: String
    let systemImage: String

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: systemImage)
                .font(.system(size: 14, weight: .semibold))
                .foregroundStyle(WarmthColor.warmWhite)
                .frame(width: 30, height: 30)
                .background(WarmthColor.emberGradient, in: .rect(cornerRadius: 9, style: .continuous))
            Text(title)
                .warmthText(.Warmth.subheadline, color: WarmthColor.inkSecondary)
                .textCase(.uppercase)
                .kerning(0.6)
            Spacer(minLength: 0)
        }
    }
}

private struct StatTile: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(value)
                .font(.Warmth.title)
                .foregroundStyle(WarmthColor.ink)
            Text(label)
                .warmthText(.Warmth.caption, color: WarmthColor.inkSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(WarmthColor.surfaceMuted, in: .rect(cornerRadius: 12, style: .continuous))
    }
}

private struct HomeInlineError: View {
    let message: String
    let retry: () -> Void

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 8) {
                Text(message)
                    .warmthText(.Warmth.footnote, color: WarmthColor.emberRed)
                Button("Retry", action: retry)
                    .font(.Warmth.footnote)
                    .foregroundStyle(WarmthColor.emberRed)
            }
        }
    }
}

#Preview {
    HomeView()
        .environment(AppModel.preview)
}

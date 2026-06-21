import SwiftUI

/// The Connections tab: live CRM rows from the backend (`GET /api/v1/connections`),
/// sorted warmest-first and searchable — the same data the web dashboard lists.
struct ConnectionsView: View {
    @Environment(AppModel.self) private var model
    @State private var query = ""

    var body: some View {
        NavigationStack {
            ZStack {
                MeshGradientBackground()

                Group {
                    switch model.crmClient.fetchState {
                    case .loading where model.crmClient.connections.isEmpty:
                        ProgressView("Loading connections…")
                            .tint(WarmthColor.emberRed)
                    case .failed(let message) where model.crmClient.connections.isEmpty:
                        CRMErrorState(message: message) {
                            Task { await model.refreshConnections() }
                        }
                    default:
                        connectionsContent
                    }
                }
            }
            .navigationTitle("Connections")
            .accessibilityIdentifier("connections_screen")
            .navigationDestination(for: CRMConnection.self) { connection in
                ConnectionDetailView(connection: connection)
            }
            .searchable(text: $query, prompt: "Search name, org, interest")
            .refreshable { await model.refreshConnections() }
            .task { await model.refreshConnections() }
        }
        .tint(WarmthColor.emberRed)
    }

    @ViewBuilder
    private var connectionsContent: some View {
        if filtered.isEmpty {
            EmptyConnectionsState(hasQuery: !trimmedQuery.isEmpty)
        } else {
            ScrollView {
                LazyVStack(spacing: 14) {
                    if case .failed(let message) = model.crmClient.fetchState {
                        CRMInlineError(message: message)
                    }

                    ForEach(filtered) { connection in
                        NavigationLink(value: connection) {
                            ConnectionRow(connection: connection)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.top, 8)
                .padding(.bottom, 32)
            }
            .scrollContentBackground(.hidden)
        }
    }

    private var trimmedQuery: String {
        query.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var filtered: [CRMConnection] {
        let q = trimmedQuery.lowercased()
        guard !q.isEmpty else { return model.crmClient.connections }
        return model.crmClient.connections.filter { connection in
            if connection.name.lowercased().contains(q) { return true }
            if let org = connection.org, org.lowercased().contains(q) { return true }
            return connection.interests.contains { $0.lowercased().contains(q) }
        }
    }
}

private struct CRMInlineError: View {
    let message: String

    var body: some View {
        Text(message)
            .font(.Warmth.footnote)
            .foregroundStyle(WarmthColor.emberRed)
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .warmthGlass(WarmthGlassStyle.card, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

private struct CRMErrorState: View {
    let message: String
    let retry: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "wifi.exclamationmark")
                .font(.system(size: 44, weight: .light))
                .foregroundStyle(WarmthColor.emberOrange)

            Text("Couldn't reach backend")
                .warmthText(.Warmth.title2)

            Text(message)
                .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                .multilineTextAlignment(.center)

            Button(action: retry) {
                Text("Try again")
                    .font(.Warmth.headline)
                    .foregroundStyle(WarmthColor.emberRed)
            }
            .buttonStyle(.plain)
        }
        .padding(32)
        .frame(maxWidth: 360)
    }
}

/// Tasteful empty state for both "no captures yet" and "no search results".
private struct EmptyConnectionsState: View {
    let hasQuery: Bool

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: hasQuery ? "magnifyingglass" : "person.2.slash")
                .font(.system(size: 44, weight: .light))
                .foregroundStyle(WarmthColor.emberOrange)
                .shadow(color: WarmthColor.emberOrange.opacity(0.5), radius: 12)

            Text(hasQuery ? "No matches" : "No connections yet")
                .warmthText(.Warmth.title2)

            Text(hasQuery
                 ? "Try a different name, org, or interest."
                 : "People you capture on iPhone appear here and on the web dashboard.")
                .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                .multilineTextAlignment(.center)
        }
        .padding(32)
        .frame(maxWidth: 360)
    }
}

#Preview {
    ConnectionsView()
        .environment(AppModel.preview)
}

import SwiftUI

/// The Connections tab: every person captured this session, merged with seeded
/// demo data, sorted warmest-first and searchable. Tapping a row opens the detail.
struct ConnectionsView: View {
    @Environment(AppModel.self) private var model
    @State private var query = ""

    var body: some View {
        NavigationStack {
            ZStack {
                MeshGradientBackground()

                Group {
                    if filtered.isEmpty {
                        EmptyConnectionsState(hasQuery: !trimmedQuery.isEmpty)
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 14) {
                                ForEach(filtered) { person in
                                    NavigationLink(value: person) {
                                        ConnectionRow(person: person)
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
            }
            .navigationTitle("Connections")
            .navigationDestination(for: PersonNode.self) { person in
                ConnectionDetailView(person: person)
            }
            .searchable(text: $query, prompt: "Search name, org, interest")
        }
        .tint(WarmthColor.emberRed)
    }

    // MARK: - Data

    /// Session captures merged with mock data, de-duplicated by case-insensitive
    /// name (session entries win), sorted by ICP score descending.
    private var merged: [PersonNode] {
        var seenNames = Set<String>()
        var result: [PersonNode] = []

        for person in model.sessionLog.people + PersonNode.mockData {
            let key = person.name.lowercased()
            guard !seenNames.contains(key) else { continue }
            seenNames.insert(key)
            result.append(person)
        }

        return result.sorted { $0.icpScore > $1.icpScore }
    }

    private var trimmedQuery: String {
        query.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var filtered: [PersonNode] {
        let q = trimmedQuery.lowercased()
        guard !q.isEmpty else { return merged }
        return merged.filter { person in
            if person.name.lowercased().contains(q) { return true }
            if let org = person.org, org.lowercased().contains(q) { return true }
            return person.interests.contains { $0.lowercased().contains(q) }
        }
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
                 : "People you capture will warm up here.")
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

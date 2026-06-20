import Foundation

/// Supplies the names the wake-word detector listens for. Seeded with ICP first
/// names; in production this is hydrated from the user's Zero CRM contacts
/// (e.g. via `GET /api/contacts`) and refreshed before each event.
final class WatchlistProvider: ObservableObject {
    static let shared = WatchlistProvider()

    @Published private(set) var names: [String]

    private init(names: [String] = WatchlistProvider.seed) {
        self.names = names
    }

    /// Replace the watchlist (e.g. after syncing contacts from the backend).
    func update(names: [String]) {
        self.names = Array(Set(names)).sorted()
    }

    private static let seed = [
        "Anna", "James", "Sarah", "Michael", "Priya", "David",
    ]
}

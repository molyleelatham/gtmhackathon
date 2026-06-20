import Foundation

/// A tiny, Codable snapshot of the capture state shared between the watch app
/// and its WidgetKit complication via an App Group container.
///
/// The watch app writes a fresh snapshot whenever the phone's recording state
/// changes; the complication's `TimelineProvider` reads it to render live status.
/// Everything degrades gracefully: if the App Group is not configured the store
/// silently falls back to `UserDefaults.standard` (the complication then simply
/// shows idle branding instead of live status).
struct WatchSharedState: Codable, Equatable, Sendable {
    var isRecording: Bool
    /// Absolute moment recording began, used to drive a self-updating timer in
    /// the complication. `nil` while idle.
    var recordingStartedAt: Date?
    var lastPersonName: String?
    var lastPersonOrg: String?

    static let idle = WatchSharedState(
        isRecording: false,
        recordingStartedAt: nil,
        lastPersonName: nil,
        lastPersonOrg: nil
    )

    /// A representative snapshot for previews and widget placeholders.
    static let sample = WatchSharedState(
        isRecording: true,
        recordingStartedAt: Date().addingTimeInterval(-128),
        lastPersonName: "Maya Chen",
        lastPersonOrg: "Sequoia"
    )
}

/// Reads/writes the shared `WatchSharedState`. Single source of truth for both
/// the watch app and the complication.
enum WatchSharedStore {
    /// Keep in sync with the App Group declared in the watch + widget entitlements.
    /// See `WATCH_INTEGRATION.md`.
    static let appGroupID = "group.com.warmth.gtmhackathon"
    private static let key = "watch.capture.state.v1"

    private static var defaults: UserDefaults {
        UserDefaults(suiteName: appGroupID) ?? .standard
    }

    static func load() -> WatchSharedState {
        guard
            let data = defaults.data(forKey: key),
            let state = try? JSONDecoder().decode(WatchSharedState.self, from: data)
        else { return .idle }
        return state
    }

    static func save(_ state: WatchSharedState) {
        guard let data = try? JSONEncoder().encode(state) else { return }
        defaults.set(data, forKey: key)
    }
}

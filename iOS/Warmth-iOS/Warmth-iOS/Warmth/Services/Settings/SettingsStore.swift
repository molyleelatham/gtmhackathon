import Foundation

/// UserDefaults-backed app settings. The backend base URL is user-configurable.
@MainActor
@Observable
final class SettingsStore {
    // Friend's FastAPI backend (apps/api) reachable from the phone over the shared
    // hotspot/Wi-Fi. ATS permits this via NSAllowsLocalNetworking. Override in Settings
    // if the Mac's LAN IP changes (run `ipconfig getifaddr en0`) or once deployed.
    static let defaultBaseURL = "http://172.20.10.9:8000"

    private enum Keys {
        static let baseURL = "warmth.backendBaseURL"
        static let onboarded = "warmth.didCompleteOnboarding"
        static let calendarConnected = "warmth.calendarConnected"
    }

    private let defaults: UserDefaults

    var baseURLString: String {
        didSet { defaults.set(baseURLString, forKey: Keys.baseURL) }
    }

    var didCompleteOnboarding: Bool {
        didSet { defaults.set(didCompleteOnboarding, forKey: Keys.onboarded) }
    }

    var calendarConnected: Bool {
        didSet { defaults.set(calendarConnected, forKey: Keys.calendarConnected) }
    }

    /// Loopback/placeholder hosts that never resolve from a physical device — if a
    /// prior build persisted one of these, upgrade it to the current default so the
    /// phone reaches the live backend without a manual Settings edit.
    private static let staleBaseURLs: Set<String> = [
        "",
        "http://127.0.0.1:8010",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://localhost:8010",
        "https://api.warmth.example.com",
    ]

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        let stored = defaults.string(forKey: Keys.baseURL)
        if let stored, !Self.staleBaseURLs.contains(stored) {
            self.baseURLString = stored
        } else {
            self.baseURLString = Self.defaultBaseURL
            defaults.set(Self.defaultBaseURL, forKey: Keys.baseURL)
        }
        self.didCompleteOnboarding = defaults.bool(forKey: Keys.onboarded)
        self.calendarConnected = defaults.bool(forKey: Keys.calendarConnected)
    }

    /// Validated URL, falling back to the default if the user typed something invalid.
    var baseURL: URL {
        URL(string: baseURLString) ?? URL(string: Self.defaultBaseURL)!
    }
}

import Foundation

/// UserDefaults-backed app settings. The backend base URL is user-configurable.
@MainActor
@Observable
final class SettingsStore {
    static let defaultBaseURL = "https://api.warmth.example.com"

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

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        self.baseURLString = defaults.string(forKey: Keys.baseURL) ?? Self.defaultBaseURL
        self.didCompleteOnboarding = defaults.bool(forKey: Keys.onboarded)
        self.calendarConnected = defaults.bool(forKey: Keys.calendarConnected)
    }

    /// Validated URL, falling back to the default if the user typed something invalid.
    var baseURL: URL {
        URL(string: baseURLString) ?? URL(string: Self.defaultBaseURL)!
    }
}

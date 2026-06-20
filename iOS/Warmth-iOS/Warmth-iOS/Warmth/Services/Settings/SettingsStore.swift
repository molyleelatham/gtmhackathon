import Foundation

/// UserDefaults-backed app settings. The backend base URL is user-configurable.
@MainActor
@Observable
final class SettingsStore {
    static let defaultBaseURL = BackendConfiguration.defaultBaseURL

    private enum Keys {
        static let baseURL = "warmth.backendBaseURL"
        static let onboarded = "warmth.didCompleteOnboarding"
        static let calendarConnected = "warmth.calendarConnected"
        static let eventModeEnabled = "warmth.eventModeEnabled"
        static let eventModeDisabledOverride = "warmth.eventModeDisabledOverride"
        static let capturePreferences = "warmth.capturePreferences"
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

    /// Manual Event mode — treat the user as on the event floor (Capture tab).
    var eventModeEnabled: Bool {
        didSet { defaults.set(eventModeEnabled, forKey: Keys.eventModeEnabled) }
    }

    /// Force Home even when calendar says an event is active today.
    var eventModeDisabledOverride: Bool {
        didSet { defaults.set(eventModeDisabledOverride, forKey: Keys.eventModeDisabledOverride) }
    }

    /// Which capture activation methods the user has enabled.
    var capturePreferences: CaptureActivationPreferences {
        didSet { persistCapturePreferences() }
    }

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        let stored = defaults.string(forKey: Keys.baseURL)
        let resolved = BackendConfiguration.normalizedBaseURLString(stored ?? Self.defaultBaseURL)
        self.baseURLString = resolved
        self.didCompleteOnboarding = defaults.bool(forKey: Keys.onboarded)
        self.calendarConnected = defaults.bool(forKey: Keys.calendarConnected)
        self.eventModeEnabled = defaults.bool(forKey: Keys.eventModeEnabled)
        self.eventModeDisabledOverride = defaults.bool(forKey: Keys.eventModeDisabledOverride)
        self.capturePreferences = Self.loadCapturePreferences(from: defaults)
        if stored != resolved {
            defaults.set(resolved, forKey: Keys.baseURL)
        }
    }

    private static func loadCapturePreferences(from defaults: UserDefaults) -> CaptureActivationPreferences {
        guard let data = defaults.data(forKey: Keys.capturePreferences),
              let decoded = try? JSONDecoder().decode(CaptureActivationPreferences.self, from: data) else {
            return .default
        }
        return decoded
    }

    private func persistCapturePreferences() {
        guard let data = try? JSONEncoder().encode(capturePreferences) else { return }
        defaults.set(data, forKey: Keys.capturePreferences)
    }

    /// Validated URL, falling back to the default if the user typed something invalid.
    var baseURL: URL {
        URL(string: baseURLString) ?? URL(string: Self.defaultBaseURL)!
    }
}

extension SettingsStore {
    /// Whether the user should land on Capture (calendar window or manual Event mode).
    func isAtEventToday(calendarEvents: [CRMDetectedEvent]) -> Bool {
        if eventModeDisabledOverride { return false }
        if eventModeEnabled { return true }
        return Self.calendarMatchToday(in: calendarEvents)
    }

    static func calendarMatchToday(in events: [CRMDetectedEvent]) -> Bool {
        let today = Calendar.current.startOfDay(for: Date())
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let fallback = ISO8601DateFormatter()

        for event in events {
            guard let startRaw = event.startDate, let endRaw = event.endDate else { continue }
            let start = formatter.date(from: startRaw) ?? fallback.date(from: startRaw)
            let end = formatter.date(from: endRaw) ?? fallback.date(from: endRaw)
            guard let start, let end else { continue }
            let startDay = Calendar.current.startOfDay(for: start)
            let endDay = Calendar.current.startOfDay(for: end)
            if startDay <= today && today <= endDay { return true }
        }
        return false
    }
}

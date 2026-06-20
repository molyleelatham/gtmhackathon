import Foundation

/// How the user can start a capture session or passive floor listening.
enum CaptureActivationMethod: String, CaseIterable, Codable, Sendable, Identifiable {
    case siri
    case actionButton
    case watch
    case manual
    case passiveFloorListening

    var id: String { rawValue }

    var title: String {
        switch self {
        case .siri: return "Siri"
        case .actionButton: return "Action Button"
        case .watch: return "Apple Watch"
        case .manual: return "In-app button"
        case .passiveFloorListening: return "Floor listening"
        }
    }

    var subtitle: String {
        switch self {
        case .siri:
            return "“Hey Siri, I'm meeting Sarah with Warmth”"
        case .actionButton:
            return "Assign Warmth in Settings → Action Button (iPhone 15 Pro+)"
        case .watch:
            return "Tap the watch to start and stop recording"
        case .manual:
            return "Tap the ember orb on the Capture tab"
        case .passiveFloorListening:
            return "Listen for contact names at events (30s auto-capture)"
        }
    }

    var systemImage: String {
        switch self {
        case .siri: return "mic.badge.plus"
        case .actionButton: return "button.programmable"
        case .watch: return "applewatch"
        case .manual: return "circle.circle"
        case .passiveFloorListening: return "ear"
        }
    }
}

/// UserDefaults-backed capture activation preferences.
struct CaptureActivationPreferences: Codable, Equatable, Sendable {
    var enabledMethods: Set<CaptureActivationMethod>

    static let `default` = CaptureActivationPreferences(
        enabledMethods: [.siri, .actionButton, .watch, .manual]
    )

    func isEnabled(_ method: CaptureActivationMethod) -> Bool {
        enabledMethods.contains(method)
    }

    mutating func setEnabled(_ method: CaptureActivationMethod, enabled: Bool) {
        if enabled {
            enabledMethods.insert(method)
        } else {
            enabledMethods.remove(method)
        }
    }
}

/// External capture trigger sources routed through `AppModel`.
enum CaptureSource: Equatable, Sendable {
    case siri
    case actionButton
    case watch
    case manual

    var activationMethod: CaptureActivationMethod {
        switch self {
        case .siri: return .siri
        case .actionButton: return .actionButton
        case .watch: return .watch
        case .manual: return .manual
        }
    }
}

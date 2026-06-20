import Foundation

/// Holds the live `AppModel` so App Intents can reach capture APIs outside SwiftUI.
@MainActor
enum AppModelRegistry {
    private(set) static weak var current: AppModel?

    static func register(_ model: AppModel) {
        current = model
    }
}

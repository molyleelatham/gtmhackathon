import SwiftUI
import UIKit

/// Shared spring + easing curves so motion feels consistent across Warmth.
enum WarmthMotion {
    static let snappy = Animation.spring(response: 0.35, dampingFraction: 0.78)
    static let gentle = Animation.spring(response: 0.6, dampingFraction: 0.85)
    static let bouncy = Animation.spring(response: 0.45, dampingFraction: 0.6)
    /// Slow continuous breathing used by the idle record orb.
    static let breathe = Animation.easeInOut(duration: 2.4).repeatForever(autoreverses: true)
}

/// Thin wrapper over UIKit feedback generators. `@MainActor` because the
/// generators must be touched on the main thread.
@MainActor
enum WarmthHaptics {
    static func impact(_ style: UIImpactFeedbackGenerator.FeedbackStyle = .medium) {
        let generator = UIImpactFeedbackGenerator(style: style)
        generator.impactOccurred()
    }

    static func success() {
        UINotificationFeedbackGenerator().notificationOccurred(.success)
    }

    static func warning() {
        UINotificationFeedbackGenerator().notificationOccurred(.warning)
    }

    static func selection() {
        UISelectionFeedbackGenerator().selectionChanged()
    }

    /// Distinct double-tap pattern fired the moment the wake word is detected.
    static func wakeWord() {
        impact(.rigid)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
            impact(.light)
        }
    }
}

import Foundation
import UserNotifications

/// Surfaces a confirmed live "hi {name}" roster match as a push-style local
/// notification banner — shown even while Warmth is foregrounded mid-capture.
@MainActor
final class MatchNotifier: NSObject {
    static let shared = MatchNotifier()

    private let center = UNUserNotificationCenter.current()

    private override init() {
        super.init()
        center.delegate = self
    }

    /// Ask once for permission to show banners. Safe to call repeatedly.
    func requestAuthorization() {
        center.requestAuthorization(options: [.alert, .sound, .badge]) { _, _ in }
    }

    /// Fire a banner for a confirmed roster match.
    func notifyMatch(_ match: AttendeeMatchResult) {
        let content = UNMutableNotificationContent()
        content.title = "Attendee matched"
        content.body = match.message
        if let title = match.connection?.title, let company = match.connection?.companyName {
            content.subtitle = "\(title) · \(company)"
        }
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: "warmth.match.\(UUID().uuidString)",
            content: content,
            trigger: nil
        )
        center.add(request)
    }
}

extension MatchNotifier: UNUserNotificationCenterDelegate {
    /// Present the banner in the foreground, since the user is actively capturing.
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .sound, .list])
    }
}

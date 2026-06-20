import AppIntents
import Foundation

/// Start recording a meeting. Optional person name pre-seeds roster matching.
struct StartMeetingCaptureIntent: AppIntent {
    static var title: LocalizedStringResource { "Start Warmth Capture" }
    static var description: IntentDescription { IntentDescription("Opens Warmth and starts recording your conversation.") }
    static var openAppWhenRun: Bool { true }

    @Parameter(title: "Person")
    var personName: String?

    init() {}

    init(personName: String?) {
        self.personName = personName
    }

    @MainActor
    func perform() async throws -> some IntentResult {
        guard let model = AppModelRegistry.current else {
            return .result()
        }
        await model.startCapture(source: .siri, personName: personName)
        return .result()
    }
}

/// Stop an in-progress Warmth recording and save the intro.
struct StopCaptureIntent: AppIntent {
    static var title: LocalizedStringResource { "Stop Warmth Recording" }
    static var description: IntentDescription { IntentDescription("Stops recording and saves the captured introduction.") }
    static var openAppWhenRun: Bool { true }

    @MainActor
    func perform() async throws -> some IntentResult {
        guard let model = AppModelRegistry.current else {
            return .result()
        }
        await model.stopCapture(source: .siri)
        return .result()
    }
}

/// Registers Siri phrases and Action Button shortcuts for Warmth capture.
struct WarmthShortcutsProvider: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: StartMeetingCaptureIntent(),
            phrases: [
                "Start capture in \(.applicationName)",
                "Record my intro with \(.applicationName)",
                "I'm meeting someone with \(.applicationName)",
            ],
            shortTitle: "Start Capture",
            systemImageName: "waveform"
        )
        AppShortcut(
            intent: StopCaptureIntent(),
            phrases: [
                "Stop recording in \(.applicationName)",
                "Stop \(.applicationName) recording",
            ],
            shortTitle: "Stop Recording",
            systemImageName: "stop.circle"
        )
    }
}

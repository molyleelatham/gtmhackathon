import Foundation
import AVFoundation

/// Centralized AVAudioSession configuration shared by the listening pipeline
/// and manual recording.
@MainActor
final class AudioSessionManager {
    static let shared = AudioSessionManager()

    private let session = AVAudioSession.sharedInstance()

    private init() {}

    /// Configure the session for continuous mic capture (wake word + recognition).
    func configureForRecording() throws {
        try session.setCategory(
            .playAndRecord,
            mode: .measurement,
            options: [.defaultToSpeaker, .allowBluetoothHFP, .duckOthers]
        )
        try session.setActive(true, options: .notifyOthersOnDeactivation)
    }

    func deactivate() {
        try? session.setActive(false, options: .notifyOthersOnDeactivation)
    }
}

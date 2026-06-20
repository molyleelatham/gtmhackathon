import Foundation
import SpeechWakeWord   // SPM: https://github.com/soniqo/speech-swift

/// Thin wrapper around the Soniqo wake-word detector. Keywords are built
/// dynamically from the user's contact / ICP names so the phone reacts to
/// "hey anna", "hey sarah", or a bare first name.
final class WakeWordEngine: ObservableObject {
    private var detector: WakeWordDetector?
    private var session: WakeWordSession?

    /// Maps a matched keyword phrase back to the original contact name.
    private(set) var phraseToName: [String: String] = [:]

    @Published private(set) var isConfigured = false

    func configure(names: [String]) async throws {
        var keywords: [KeywordSpec] = []
        var mapping: [String: String] = [:]

        for name in names {
            let lower = name.lowercased()
            let hey = "hey \(lower)"
            keywords.append(KeywordSpec(phrase: hey, acThreshold: 0.15, boost: 0.6))
            keywords.append(KeywordSpec(phrase: lower, acThreshold: 0.20, boost: 0.4))
            mapping[hey] = name
            mapping[lower] = name
        }

        detector = try await WakeWordDetector.fromPretrained(keywords: keywords)
        session = try detector?.createSession()
        phraseToName = mapping

        await MainActor.run { self.isConfigured = true }
    }

    /// Push 16 kHz mono Float32 audio and get back any detections.
    func push(audio: [Float]) -> [WakeWordDetection] {
        (try? session?.pushAudio(audio)) ?? []
    }

    /// Reset the streaming session (e.g. after a capture window) so stale audio
    /// state doesn't cause an immediate re-trigger.
    func resetSession() {
        session = try? detector?.createSession()
    }
}

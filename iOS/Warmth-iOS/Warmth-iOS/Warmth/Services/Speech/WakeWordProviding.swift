import Foundation

/// The wake phrase Warmth listens for.
enum WakeWord {
    static let phrase = "hey it's nice to meet you"
}

/// Abstraction over an on-device wake-word detector. The real implementation would
/// wrap Soniqo's `SpeechWakeWord` (`WakeWordDetector` / `WakeWordSession`); a stub
/// keeps the app building and demoable when that package isn't linked.
protocol WakeWordProviding: AnyObject, Sendable {
    var registeredPhrase: String { get }
    /// Prepare the detector (may download / load models). No-op for the stub.
    func prepare() async throws
    /// Push a chunk of Float32 mono @16kHz audio; returns true if the wake word fired.
    func process(_ samples: [Float]) -> Bool
    func reset()
}

/// Safe default: never auto-fires from audio (callers can also trigger detection
/// manually). Keeps Capture fully functional without the heavy MLX/CoreML package.
final class StubWakeWordProvider: WakeWordProviding, @unchecked Sendable {
    let registeredPhrase = WakeWord.phrase
    func prepare() async throws {}
    func process(_ samples: [Float]) -> Bool { false }
    func reset() {}
}

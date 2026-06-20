import Foundation

/// High-level capture phases that drive the hero Capture UI.
enum CapturePhase: Equatable, Sendable {
    case idle           // not listening
    case listening      // mic on, waiting for the wake word
    case recording      // wake word fired (or manual start); transcribing
}

enum SpeechAuthorization: Sendable {
    case notDetermined, denied, authorized, restricted
}

/// Abstraction over the speech pipeline (AVAudioEngine + wake word + SFSpeechRecognizer)
/// so the Capture UI can be driven by a mock in previews and tests.
@MainActor
protocol SpeechServicing: AnyObject {
    var phase: CapturePhase { get }
    var transcript: String { get }
    /// Normalized 0...1 audio level for the waveform/orb.
    var audioLevel: Double { get }
    var elapsed: TimeInterval { get }
    var permissionError: String? { get }

    func requestPermissions() async -> Bool
    /// Begin listening for the wake word.
    func startListening() async
    /// Begin recording immediately (manual start / wake-word fired).
    func startRecording() async
    func stopAndReset()
    /// Callback fired the moment the wake word is detected.
    var onWakeWordDetected: (() -> Void)? { get set }
}

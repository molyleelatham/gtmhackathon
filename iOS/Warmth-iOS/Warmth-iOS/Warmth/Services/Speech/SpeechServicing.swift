import Foundation

/// High-level capture phases that drive the hero Capture UI.
enum CapturePhase: Equatable, Sendable {
    case idle
    case recording
}

enum SpeechAuthorization: Sendable {
    case notDetermined, denied, authorized, restricted
}

/// Abstraction over the speech pipeline (AVAudioEngine + SFSpeechRecognizer)
/// so the Capture UI can be driven by a mock in previews and tests.
@MainActor
protocol SpeechServicing: AnyObject {
    var phase: CapturePhase { get }
    var transcript: String { get }
    /// Normalized 0...1 audio level for the waveform/orb.
    var audioLevel: Double { get }
    var elapsed: TimeInterval { get }
    var permissionError: String? { get }
    /// True when mic/speech access was previously denied, so iOS will no longer
    /// show the system prompt and the user must change it in Settings.
    var permissionsDenied: Bool { get }
    /// Synchronous mic check — call before touching AVAudioEngine.
    var hasMicrophoneAccess: Bool { get }

    func requestPermissions() async -> Bool
    /// Read current permission status without showing a system prompt.
    func checkPermissions() -> Bool
    /// Begin recording and live transcription immediately.
    func startRecording() async
    func stopAndReset()
}

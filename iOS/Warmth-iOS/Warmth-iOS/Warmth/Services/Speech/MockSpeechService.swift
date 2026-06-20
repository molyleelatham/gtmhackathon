import Foundation

/// Scripted speech service for previews/tests: animates level + a canned transcript.
@MainActor
@Observable
final class MockSpeechService: SpeechServicing {
    var phase: CapturePhase
    var transcript: String
    var audioLevel: Double = 0.3
    var elapsed: TimeInterval = 0
    var permissionError: String?
    var onWakeWordDetected: (() -> Void)?

    private var ticker: Task<Void, Never>?

    init(phase: CapturePhase = .idle, transcript: String = "") {
        self.phase = phase
        self.transcript = transcript
    }

    func requestPermissions() async -> Bool { true }

    func startListening() async { phase = .listening; animate() }

    func startRecording() async {
        phase = .recording
        transcript = "Hey, it's nice to meet you — I'm Maya, I lead RevOps at NorthWind Labs."
        animate()
    }

    func stopAndReset() {
        ticker?.cancel()
        phase = .idle
        audioLevel = 0
        elapsed = 0
    }

    private func animate() {
        ticker?.cancel()
        ticker = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .milliseconds(120))
                guard let self else { return }
                self.audioLevel = Double.random(in: 0.2...0.9)
                if self.phase == .recording { self.elapsed += 0.12 }
            }
        }
    }

    static var recordingPreview: MockSpeechService {
        MockSpeechService(phase: .recording, transcript: "Hey, it's nice to meet you — I'm Maya from NorthWind Labs, we work on attribution and RevOps.")
    }
}

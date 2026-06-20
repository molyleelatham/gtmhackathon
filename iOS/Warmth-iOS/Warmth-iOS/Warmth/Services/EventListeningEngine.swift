import Foundation
import AVFoundation
import Combine
import SpeechWakeWord

/// Orchestrates passive event-listening:
///   mic (16 kHz) → contact-name wake word → 30s capture window → callback
@MainActor
final class EventListeningEngine: ObservableObject {
    enum State: Equatable {
        case idle
        case listening
        case capturing(name: String?)
    }

    @Published private(set) var state: State = .idle
    @Published private(set) var liveTranscript = ""

    private let mic = MicrophoneStream()
    private let wakeWord = WakeWordEngine()
    private let capture = CaptureWindow()

    /// Names the wake word should listen for (contacts + ICP first names).
    var watchlist: [String] = WatchlistProvider.shared.names

    /// Called when a 30s capture window finishes with a non-empty transcript.
    var onCaptureComplete: ((String, String?) async -> Void)?
    var onStateChange: ((State) -> Void)?
    var onLiveTranscriptChange: ((String) -> Void)?

    private func publishState(_ newState: State) {
        state = newState
        onStateChange?(newState)
    }

    private func publishTranscript(_ text: String) {
        liveTranscript = text
        onLiveTranscriptChange?(text)
    }

    private var isCapturing: Bool {
        if case .capturing = state { return true }
        return false
    }

    // MARK: - Lifecycle

    func start() async {
        guard state == .idle else { return }

        do {
            try AudioSessionManager.shared.configureForRecording()
            await capture.prepareLanguageModel()
            try await wakeWord.configure(names: watchlist)

            capture.onPartialTranscript = { [weak self] text in
                Task { @MainActor in self?.publishTranscript(text) }
            }

            mic.onFrame = { [weak self] raw, frame16k in
                guard let self else { return }
                Task { @MainActor in self.handleFrame(raw: raw, frame16k: frame16k) }
            }

            try mic.start()
            publishState(.listening)
        } catch {
            print("EventListeningEngine: failed to start: \(error)")
            publishState(.idle)
        }
    }

    func stop() {
        mic.stop()
        capture.end()
        publishState(.idle)
        publishTranscript("")
    }

    // MARK: - Audio routing

    private func handleFrame(raw: AVAudioPCMBuffer, frame16k: [Float]) {
        switch state {
        case .listening:
            let detections = wakeWord.push(audio: frame16k)
            if let first = detections.first {
                openCaptureWindow(for: matchedName(from: first))
            }
        case .capturing:
            capture.appendBuffer(raw)
        case .idle:
            break
        }
    }

    private func matchedName(from detection: KeywordDetection) -> String? {
        let phrase = detection.phrase.lowercased()
        return wakeWord.phraseToName[phrase]
    }

    // MARK: - Capture window

    private func openCaptureWindow(for name: String?) {
        publishState(.capturing(name: name))
        publishTranscript("")
        WarmthHaptics.wakeWord()

        capture.begin(duration: 30) { [weak self] transcript in
            Task { @MainActor in self?.finishCapture(transcript: transcript, focusName: name) }
        }
    }

    private func finishCapture(transcript: String, focusName: String?) {
        wakeWord.resetSession()

        let trimmed = transcript.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmed.isEmpty, let onCaptureComplete {
            Task { await onCaptureComplete(trimmed, focusName) }
        }

        publishState(mic.isRunning ? .listening : .idle)
        publishTranscript("")
    }
}

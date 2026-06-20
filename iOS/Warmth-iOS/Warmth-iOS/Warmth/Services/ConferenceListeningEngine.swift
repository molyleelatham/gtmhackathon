import Foundation
import AVFoundation
import Speech
import Combine

/// Orchestrates the passive conference-listening pipeline:
///
///   mic (16 kHz) → wake word → 30s capture window → social graph → Signal
///                → watch haptic + POST /api/signals
@MainActor
final class ConferenceListeningEngine: ObservableObject {
    static let shared = ConferenceListeningEngine()

    enum State: Equatable {
        case idle
        case listening          // waiting for a wake word
        case capturing(name: String?)   // inside a 30s window
    }

    @Published private(set) var state: State = .idle
    @Published private(set) var liveTranscript = ""
    @Published private(set) var lastSignal: Signal?

    private let mic = MicrophoneStream()
    private let wakeWord = WakeWordEngine()
    private let capture = CaptureWindow()
    private let graph = SocialGraphEngine()
    private let api = SignalAPIClient.shared
    private let watch = WatchConnectivityService.shared

    /// Names the wake word should listen for (contacts + ICP first names).
    var watchlist: [String] = WatchlistProvider.shared.names

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
                self?.liveTranscript = text
            }

            mic.onFrame = { [weak self] raw, frame16k in
                guard let self else { return }
                Task { @MainActor in self.handleFrame(raw: raw, frame16k: frame16k) }
            }

            try mic.start()
            state = .listening
            print("ConferenceListeningEngine: listening for \(watchlist.count) names")
        } catch {
            print("ConferenceListeningEngine: failed to start: \(error)")
            state = .idle
        }
    }

    func stop() {
        mic.stop()
        capture.end()
        state = .idle
        liveTranscript = ""
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

    /// Best-effort mapping of a detection back to a contact name via the
    /// phrase→name table built in `WakeWordEngine.configure`.
    private func matchedName(from detection: WakeWordDetection) -> String? {
        let phrase = (detection.keyword as String?)?.lowercased() ?? ""
        return wakeWord.phraseToName[phrase]
    }

    // MARK: - Capture window

    private func openCaptureWindow(for name: String?) {
        state = .capturing(name: name)
        liveTranscript = ""

        // Light haptic to confirm the wake word fired.
        watch.notifyWakeWord(name: name)

        capture.begin(duration: 30) { [weak self] transcript in
            Task { @MainActor in self?.finishCapture(transcript: transcript, focusName: name) }
        }
    }

    private func finishCapture(transcript: String, focusName: String?) {
        // Reset wake-word state so trailing audio doesn't immediately re-trigger.
        wakeWord.resetSession()

        if let signal = graph.ingest(transcript: transcript, focusName: focusName) {
            lastSignal = signal
            handle(signal: signal)
        }

        state = mic.isRunning ? .listening : .idle
        liveTranscript = ""
    }

    private func handle(signal: Signal) {
        // Fire-and-forget: the phone is intentionally "dumb". The backend owns
        // authoritative scoring (TGN/GCN, centrality, warm-intro paths) and the
        // CRM (≥70) / Faxxing + Lightfern (≥80) thresholds. We send EVERY signal.
        Task { await api.send(signal) }

        // Instant on-device hint while the backend processes asynchronously.
        // The authoritative lead confirmation arrives later via the dashboard /
        // push channel, not from this POST.
        if signal.isPreScoreHint {
            watch.notifyLeadDetected(name: signal.person.name, score: signal.score)
        }
    }
}

import Foundation
@preconcurrency import AVFoundation
import Speech

/// Real capture pipeline: AVAudioEngine (16 kHz mono tap) → wake-word provider
/// (gates activation) → on-device SFSpeechRecognizer (live transcription).
///
/// All published state is mutated on the main actor; the audio tap hops back to the
/// main actor to update levels/transcript. Third-party wake-word detection is injected
/// via `WakeWordProviding` so a resolution failure can't break capture.
@MainActor
@Observable
final class SpeechService: SpeechServicing {
    private(set) var phase: CapturePhase = .idle
    private(set) var transcript: String = ""
    private(set) var audioLevel: Double = 0
    private(set) var elapsed: TimeInterval = 0
    var permissionError: String?
    private(set) var permissionsDenied = false
    var onWakeWordDetected: (() -> Void)?

    private let wakeWord: any WakeWordProviding
    private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))

    private let engine = AVAudioEngine()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private var converter: AVAudioConverter?
    private let targetFormat = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: 16_000, channels: 1, interleaved: false)

    private var timerTask: Task<Void, Never>?
    private var startDate: Date?
    private var tapInstalled = false
    private var isTransitioning = false

    init(wakeWord: any WakeWordProviding = StubWakeWordProvider()) {
        self.wakeWord = wakeWord
    }

    // MARK: - Permissions

    /// Requests microphone + speech access. Only shows the system prompt when the
    /// status is still undetermined; if a permission was previously denied, iOS will
    /// not re-prompt, so we surface `permissionsDenied` to route the user to Settings.
    func checkPermissions() -> Bool {
        let micOK = AVAudioApplication.shared.recordPermission == .granted
        let speechOK = SFSpeechRecognizer.authorizationStatus() == .authorized
        updatePermissionState(micOK: micOK, speechOK: speechOK)
        return micOK && speechOK
    }

    func requestPermissions() async -> Bool {
        // Microphone first — it's the access we actually can't proceed without.
        let micStatus = AVAudioApplication.shared.recordPermission
        switch micStatus {
        case .granted:
            break
        case .undetermined:
            _ = await withCheckedContinuation { continuation in
                AVAudioApplication.requestRecordPermission { continuation.resume(returning: $0) }
            }
        default:
            break
        }

        let speechStatus = SFSpeechRecognizer.authorizationStatus()
        switch speechStatus {
        case .authorized:
            break
        case .notDetermined:
            _ = await withCheckedContinuation { continuation in
                SFSpeechRecognizer.requestAuthorization { continuation.resume(returning: $0 == .authorized) }
            }
        default:
            break
        }

        // Re-read after any prompts — a first-time denial becomes `.denied` immediately.
        let micOK = AVAudioApplication.shared.recordPermission == .granted
        let speechOK = SFSpeechRecognizer.authorizationStatus() == .authorized
        updatePermissionState(micOK: micOK, speechOK: speechOK)
        return micOK && speechOK
    }

    private func updatePermissionState(micOK: Bool, speechOK: Bool) {
        let micStatus = AVAudioApplication.shared.recordPermission
        let speechStatus = SFSpeechRecognizer.authorizationStatus()

        // "Denied" means the OS will no longer prompt — the only fix is Settings.
        permissionsDenied = micStatus == .denied
            || speechStatus == .denied
            || speechStatus == .restricted

        if !micOK {
            permissionError = permissionsDenied
                ? "Microphone access is turned off. Enable it for Warmth in Settings."
                : "Microphone permission is required."
        } else if !speechOK {
            permissionError = permissionsDenied
                ? "Speech recognition is turned off. Enable it for Warmth in Settings."
                : "Speech recognition permission is required."
        } else {
            permissionError = nil
        }
    }

    // MARK: - Lifecycle

    func startListening() async {
        guard phase == .idle, !isTransitioning else { return }
        guard checkPermissions() else { return }

        isTransitioning = true
        defer { isTransitioning = false }

        try? await wakeWord.prepare()
        do {
            try beginAudio(transcribing: false)
            phase = .listening
        } catch {
            resetAfterAudioFailure(error.localizedDescription)
        }
    }

    func startRecording() async {
        guard phase != .recording, !isTransitioning else { return }
        guard checkPermissions() else { return }

        isTransitioning = true
        defer { isTransitioning = false }

        if phase == .idle { try? await wakeWord.prepare() }
        do {
            if !engine.isRunning {
                try beginAudio(transcribing: true)
            } else if !beginTranscription() {
                throw SpeechCaptureError.recognizerUnavailable
            }
            phase = .recording
            startDate = Date()
            startTimer()
        } catch {
            resetAfterAudioFailure(error.localizedDescription)
        }
    }

    func stopAndReset() {
        timerTask?.cancel(); timerTask = nil
        recognitionTask?.cancel(); recognitionTask = nil
        request?.endAudio(); request = nil
        teardownEngine()
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        wakeWord.reset()
        phase = .idle
        transcript = ""
        audioLevel = 0
        elapsed = 0
        startDate = nil
    }

    // MARK: - Audio

    private enum SpeechCaptureError: LocalizedError {
        case permissionsMissing
        case microphoneUnavailable
        case recognizerUnavailable
        case audioEngineFailed(String)

        var errorDescription: String? {
            switch self {
            case .permissionsMissing:
                return "Microphone and speech recognition permissions are required."
            case .microphoneUnavailable:
                return "The microphone is unavailable. Check permissions in Settings and try again."
            case .recognizerUnavailable:
                return "Speech recognition is unavailable on this device. Check language settings and try again."
            case .audioEngineFailed(let detail):
                return detail
            }
        }
    }

    /// Tear down audio, reset visible capture state, and surface a user-facing error.
    private func resetAfterAudioFailure(_ message: String) {
        timerTask?.cancel()
        timerTask = nil
        recognitionTask?.cancel()
        recognitionTask = nil
        request?.endAudio()
        request = nil
        teardownEngine()
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        wakeWord.reset()
        phase = .idle
        transcript = ""
        audioLevel = 0
        elapsed = 0
        startDate = nil
        permissionError = message
    }

    private func teardownEngine() {
        if tapInstalled {
            engine.inputNode.removeTap(onBus: 0)
            tapInstalled = false
        }
        if engine.isRunning { engine.stop() }
        engine.reset()
        converter = nil
    }

    private func beginAudio(transcribing: Bool) throws {
        guard checkPermissions() else { throw SpeechCaptureError.permissionsMissing }

        teardownEngine()

        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playAndRecord, mode: .measurement, options: [.duckOthers, .defaultToSpeaker])
        try session.setActive(true, options: .notifyOthersOnDeactivation)

        engine.prepare()
        let input = engine.inputNode
        let inputFormat = input.outputFormat(forBus: 0)
        guard inputFormat.sampleRate > 0, inputFormat.channelCount > 0 else {
            throw SpeechCaptureError.microphoneUnavailable
        }
        guard let targetFormat else {
            throw SpeechCaptureError.audioEngineFailed("Audio format is not supported on this device.")
        }
        guard let converter = AVAudioConverter(from: inputFormat, to: targetFormat) else {
            throw SpeechCaptureError.audioEngineFailed("Could not configure the microphone.")
        }
        self.converter = converter

        let wakeWord = self.wakeWord
        let audioConverter = converter
        input.installTap(onBus: 0, bufferSize: 1024, format: inputFormat) { [weak self] buffer, _ in
            let level = Self.rms(of: buffer)
            Task { @MainActor in
                self?.audioLevel = level
                self?.request?.append(buffer)
            }
            if let converted = Self.convert(buffer, converter: audioConverter, targetFormat: targetFormat),
               wakeWord.process(converted) {
                Task { @MainActor in self?.handleWakeWordFired() }
            }
        }
        tapInstalled = true

        try engine.start()
        if transcribing, !beginTranscription() {
            throw SpeechCaptureError.recognizerUnavailable
        }
    }

    @discardableResult
    private func beginTranscription() -> Bool {
        guard let recognizer, recognizer.isAvailable else { return false }
        recognitionTask?.cancel()
        recognitionTask = nil
        request?.endAudio()
        request = nil
        transcript = ""
        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        if recognizer.supportsOnDeviceRecognition { request.requiresOnDeviceRecognition = true }
        self.request = request
        recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self else { return }
            if let result {
                Task { @MainActor in self.transcript = result.bestTranscription.formattedString }
            }
            if let error {
                Task { @MainActor in
                    // Keep capture alive; surface a hint if transcription stops unexpectedly.
                    if self.phase == .recording, self.transcript.isEmpty {
                        self.permissionError = error.localizedDescription
                    }
                }
            }
        }
        return true
    }

    private func handleWakeWordFired() {
        guard phase == .listening else { return }
        WarmthHaptics.wakeWord()
        onWakeWordDetected?()
        Task { await startRecording() }
    }

    nonisolated private static func convert(
        _ buffer: AVAudioPCMBuffer,
        converter: AVAudioConverter?,
        targetFormat: AVAudioFormat?
    ) -> [Float]? {
        guard let targetFormat, let converter else { return nil }
        guard buffer.format.sampleRate > 0 else { return nil }
        let ratio = targetFormat.sampleRate / buffer.format.sampleRate
        let capacity = AVAudioFrameCount(Double(buffer.frameLength) * ratio + 64)
        guard let out = AVAudioPCMBuffer(pcmFormat: targetFormat, frameCapacity: capacity) else { return nil }
        var fed = false
        var err: NSError?
        converter.convert(to: out, error: &err) { _, status in
            if fed { status.pointee = .noDataNow; return nil }
            fed = true
            status.pointee = .haveData
            return buffer
        }
        guard err == nil, let channel = out.floatChannelData?[0] else { return nil }
        return Array(UnsafeBufferPointer(start: channel, count: Int(out.frameLength)))
    }

    nonisolated private static func rms(of buffer: AVAudioPCMBuffer) -> Double {
        guard let channel = buffer.floatChannelData?[0] else { return 0 }
        let count = Int(buffer.frameLength)
        guard count > 0 else { return 0 }
        var sum: Float = 0
        for i in 0..<count { sum += channel[i] * channel[i] }
        let rms = sqrt(sum / Float(count))
        // Map to a pleasant 0...1 visual range.
        return Double(min(max(rms * 12, 0), 1))
    }

    private func startTimer() {
        timerTask?.cancel()
        timerTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .milliseconds(100))
                guard let self, let start = self.startDate else { continue }
                self.elapsed = Date().timeIntervalSince(start)
            }
        }
    }
}

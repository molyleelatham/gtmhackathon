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

    var hasMicrophoneAccess: Bool { MicrophoneAccess.isGranted }

    private let wakeWord: any WakeWordProviding
    private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private let pipeline = SpeechAudioPipeline()

    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let targetFormat = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: 16_000, channels: 1, interleaved: false)

    private var timerTask: Task<Void, Never>?
    private var startDate: Date?
    private var isTransitioning = false

    init(wakeWord: any WakeWordProviding = StubWakeWordProvider()) {
        self.wakeWord = wakeWord
    }

    // MARK: - Permissions

    func checkPermissions() -> Bool {
        let micOK = MicrophoneAccess.isGranted
        let speechOK = SFSpeechRecognizer.authorizationStatus() == .authorized
        updatePermissionState(micOK: micOK, speechOK: speechOK)
        return micOK && speechOK
    }

    func requestPermissions() async -> Bool {
        if !MicrophoneAccess.isGranted, MicrophoneAccess.status == .undetermined {
            _ = await MicrophoneAccess.request()
        }

        let speechStatus = SFSpeechRecognizer.authorizationStatus()
        if speechStatus == .notDetermined {
            _ = await withCheckedContinuation { continuation in
                SFSpeechRecognizer.requestAuthorization { status in
                    Task { @MainActor in
                        continuation.resume(returning: status == .authorized)
                    }
                }
            }
        }

        let micOK = MicrophoneAccess.isGranted
        let speechOK = SFSpeechRecognizer.authorizationStatus() == .authorized
        updatePermissionState(micOK: micOK, speechOK: speechOK)
        return micOK && speechOK
    }

    private func updatePermissionState(micOK: Bool, speechOK: Bool) {
        permissionsDenied = MicrophoneAccess.isDenied
            || SFSpeechRecognizer.authorizationStatus() == .denied
            || SFSpeechRecognizer.authorizationStatus() == .restricted

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
        guard hasMicrophoneAccess, checkPermissions() else { return }

        isTransitioning = true
        defer { isTransitioning = false }

        try? await wakeWord.prepare()
        do {
            try beginAudio(transcribing: false)
            // Mirror the web dashboard: transcribe passively so a "hi {name}" greeting
            // matches the roster immediately, without first saying the wake phrase.
            // Best-effort — if on-device recognition is unavailable we still listen for
            // the wake word.
            _ = beginTranscription()
            phase = .listening
        } catch {
            resetAfterAudioFailure(error.localizedDescription)
        }
    }

    func startRecording() async {
        guard phase != .recording, !isTransitioning else { return }
        guard hasMicrophoneAccess, checkPermissions() else { return }

        isTransitioning = true
        defer { isTransitioning = false }

        if phase == .idle { try? await wakeWord.prepare() }
        do {
            if !pipeline.isRunning {
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
        pipeline.stop()
        deactivateAudioSession()
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

    private func resetAfterAudioFailure(_ message: String) {
        timerTask?.cancel()
        timerTask = nil
        recognitionTask?.cancel()
        recognitionTask = nil
        request?.endAudio()
        request = nil
        pipeline.stop()
        deactivateAudioSession()
        wakeWord.reset()
        phase = .idle
        transcript = ""
        audioLevel = 0
        elapsed = 0
        startDate = nil
        permissionError = message
    }

    private func deactivateAudioSession() {
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }

    private func beginAudio(transcribing: Bool) throws {
        guard hasMicrophoneAccess, checkPermissions() else {
            throw SpeechCaptureError.permissionsMissing
        }

        let wakeWord = self.wakeWord
        let targetFormat = self.targetFormat

        try pipeline.start(
            wakeWord: wakeWord,
            targetFormat: targetFormat,
            onLevel: { [weak self] level in
                Task { @MainActor in self?.audioLevel = level }
            },
            onBuffer: { [weak self] buffer in
                Task { @MainActor in self?.request?.append(buffer) }
            },
            onWakeWord: { [weak self] in
                Task { @MainActor in self?.handleWakeWordFired() }
            }
        )

        if transcribing, !beginTranscription() {
            pipeline.stop()
            deactivateAudioSession()
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
                    if self.phase == .recording, self.transcript.isEmpty {
                        self.permissionError = error.localizedDescription
                    }
                }
            }
        }
        return true
    }

    private func handleWakeWordFired() {
        guard phase == .listening, !isTransitioning else { return }
        WarmthHaptics.wakeWord()
        onWakeWordDetected?()
        Task { await startRecording() }
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

// MARK: - Microphone permission helpers

private enum MicrophoneAccess {
    enum Status { case undetermined, granted, denied }

    static var status: Status {
        switch AVAudioApplication.shared.recordPermission {
        case .granted: return .granted
        case .denied: return .denied
        case .undetermined: return .undetermined
        @unknown default: return .undetermined
        }
    }

    static var isGranted: Bool { status == .granted }
    static var isDenied: Bool { status == .denied }

    static func request() async -> Bool {
        guard status == .undetermined else { return isGranted }
        return await withCheckedContinuation { continuation in
            AVAudioApplication.requestRecordPermission { granted in
                Task { @MainActor in
                    continuation.resume(returning: granted)
                }
            }
        }
    }
}

// MARK: - Off-main-actor audio pipeline

/// Owns AVAudioEngine lifecycle on a dedicated queue. `installTap` must not run on
/// `@MainActor` — the realtime tap thread mismatch crashes on physical devices.
final class SpeechAudioPipeline: @unchecked Sendable {
    private let queue = DispatchQueue(label: "com.warmth.audio-pipeline", qos: .userInitiated)
    private var engine: AVAudioEngine?
    private var tapInstalled = false

    private(set) var isRunning = false

    enum PipelineError: LocalizedError {
        case microphoneUnavailable
        case unsupportedFormat
        case converterFailed
        case engineStartFailed(String)

        var errorDescription: String? {
            switch self {
            case .microphoneUnavailable:
                return "The microphone is unavailable. Check permissions in Settings and try again."
            case .unsupportedFormat:
                return "Audio format is not supported on this device."
            case .converterFailed:
                return "Could not configure the microphone."
            case .engineStartFailed(let detail):
                return detail
            }
        }
    }

    func start(
        wakeWord: any WakeWordProviding,
        targetFormat: AVAudioFormat?,
        onLevel: @escaping @Sendable (Double) -> Void,
        onBuffer: @escaping @Sendable (AVAudioPCMBuffer) -> Void,
        onWakeWord: @escaping @Sendable () -> Void
    ) throws {
        var thrown: Error?
        queue.sync {
            do {
                try self.startLocked(
                    wakeWord: wakeWord,
                    targetFormat: targetFormat,
                    onLevel: onLevel,
                    onBuffer: onBuffer,
                    onWakeWord: onWakeWord
                )
            } catch {
                thrown = error
                self.stopLocked()
            }
        }
        if let thrown { throw thrown }
    }

    func stop() {
        queue.sync { stopLocked() }
    }

    private func startLocked(
        wakeWord: any WakeWordProviding,
        targetFormat: AVAudioFormat?,
        onLevel: @escaping @Sendable (Double) -> Void,
        onBuffer: @escaping @Sendable (AVAudioPCMBuffer) -> Void,
        onWakeWord: @escaping @Sendable () -> Void
    ) throws {
        stopLocked()

        guard MicrophoneAccess.isGranted else {
            throw PipelineError.microphoneUnavailable
        }

        let session = AVAudioSession.sharedInstance()
        try session.setCategory(
            .playAndRecord,
            mode: .measurement,
            options: [.duckOthers, .defaultToSpeaker, .allowBluetoothHFP]
        )
        try session.setActive(true, options: .notifyOthersOnDeactivation)

        // The hardware input route must exist before we touch `inputNode`, otherwise
        // AVAudioEngine asserts ("inputNode != nullptr || outputNode != nullptr").
        guard session.isInputAvailable else {
            throw PipelineError.microphoneUnavailable
        }

        let engine = AVAudioEngine()
        self.engine = engine

        // Access `inputNode` (which lazily instantiates the IO unit) and install the
        // tap BEFORE calling `prepare()`/`start()`. Calling `prepare()` on a brand-new
        // engine that has no IO node attached is what crashed on device.
        let input = engine.inputNode
        guard let inputFormat = Self.resolveInputFormat(for: input) else {
            throw PipelineError.microphoneUnavailable
        }
        guard let targetFormat else {
            throw PipelineError.unsupportedFormat
        }
        guard let converter = AVAudioConverter(from: inputFormat, to: targetFormat) else {
            throw PipelineError.converterFailed
        }

        let audioConverter = converter
        input.installTap(onBus: 0, bufferSize: 1024, format: inputFormat) { buffer, _ in
            onLevel(Self.rms(of: buffer))
            onBuffer(buffer)
            if let converted = Self.convert(buffer, converter: audioConverter, targetFormat: targetFormat),
               wakeWord.process(converted) {
                onWakeWord()
            }
        }
        tapInstalled = true

        engine.prepare()
        do {
            try engine.start()
        } catch {
            throw PipelineError.engineStartFailed(error.localizedDescription)
        }
        isRunning = true
    }

    private func stopLocked() {
        isRunning = false
        guard let engine else { return }

        if tapInstalled {
            engine.inputNode.removeTap(onBus: 0)
            tapInstalled = false
        }
        if engine.isRunning {
            engine.stop()
        }
        self.engine = nil
    }

    private static func resolveInputFormat(for input: AVAudioInputNode) -> AVAudioFormat? {
        func valid(_ format: AVAudioFormat) -> Bool {
            format.sampleRate > 0 && format.channelCount > 0
        }
        let first = input.outputFormat(forBus: 0)
        if valid(first) { return first }
        Thread.sleep(forTimeInterval: 0.05)
        let retry = input.outputFormat(forBus: 0)
        return valid(retry) ? retry : nil
    }

    /// Reference box so the converter input block captures a `let` instead of a
    /// mutable `var` (which Swift 6 flags in concurrently-executing code).
    private final class FeedState { var fed = false }

    private static func convert(
        _ buffer: AVAudioPCMBuffer,
        converter: AVAudioConverter,
        targetFormat: AVAudioFormat
    ) -> [Float]? {
        guard buffer.format.sampleRate > 0 else { return nil }
        let ratio = targetFormat.sampleRate / buffer.format.sampleRate
        let capacity = AVAudioFrameCount(Double(buffer.frameLength) * ratio + 64)
        guard let out = AVAudioPCMBuffer(pcmFormat: targetFormat, frameCapacity: capacity) else { return nil }
        let state = FeedState()
        var err: NSError?
        converter.convert(to: out, error: &err) { _, status in
            if state.fed { status.pointee = .noDataNow; return nil }
            state.fed = true
            status.pointee = .haveData
            return buffer
        }
        guard err == nil, let channel = out.floatChannelData?[0] else { return nil }
        return Array(UnsafeBufferPointer(start: channel, count: Int(out.frameLength)))
    }

    private static func rms(of buffer: AVAudioPCMBuffer) -> Double {
        guard let channel = buffer.floatChannelData?[0] else { return 0 }
        let count = Int(buffer.frameLength)
        guard count > 0 else { return 0 }
        var sum: Float = 0
        for i in 0..<count { sum += channel[i] * channel[i] }
        let rms = sqrt(sum / Float(count))
        return Double(min(max(rms * 12, 0), 1))
    }
}

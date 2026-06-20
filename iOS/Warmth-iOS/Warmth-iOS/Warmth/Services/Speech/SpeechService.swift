import Foundation
import AVFoundation
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

    init(wakeWord: any WakeWordProviding = StubWakeWordProvider()) {
        self.wakeWord = wakeWord
    }

    // MARK: - Permissions

    func requestPermissions() async -> Bool {
        let speechOK = await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status == .authorized)
            }
        }
        let micOK = await withCheckedContinuation { continuation in
            AVAudioApplication.requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
        if !speechOK { permissionError = "Speech recognition permission is required." }
        else if !micOK { permissionError = "Microphone permission is required." }
        else { permissionError = nil }
        return speechOK && micOK
    }

    // MARK: - Lifecycle

    func startListening() async {
        guard phase == .idle else { return }
        try? await wakeWord.prepare()
        do {
            try beginAudio(transcribing: false)
            phase = .listening
        } catch {
            permissionError = error.localizedDescription
        }
    }

    func startRecording() async {
        if phase == .idle { try? await wakeWord.prepare() }
        do {
            if !engine.isRunning { try beginAudio(transcribing: true) }
            else { beginTranscription() }
            phase = .recording
            startDate = Date()
            startTimer()
        } catch {
            permissionError = error.localizedDescription
        }
    }

    func stopAndReset() {
        timerTask?.cancel(); timerTask = nil
        recognitionTask?.cancel(); recognitionTask = nil
        request?.endAudio(); request = nil
        if engine.isRunning {
            engine.inputNode.removeTap(onBus: 0)
            engine.stop()
        }
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        wakeWord.reset()
        phase = .idle
        audioLevel = 0
        elapsed = 0
        startDate = nil
    }

    // MARK: - Audio

    private func beginAudio(transcribing: Bool) throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playAndRecord, mode: .measurement, options: [.duckOthers, .defaultToSpeaker])
        try session.setActive(true, options: .notifyOthersOnDeactivation)

        let input = engine.inputNode
        let inputFormat = input.outputFormat(forBus: 0)
        if let targetFormat { converter = AVAudioConverter(from: inputFormat, to: targetFormat) }

        let wakeWord = self.wakeWord
        let audioConverter = converter
        let format = targetFormat
        input.removeTap(onBus: 0)
        input.installTap(onBus: 0, bufferSize: 1024, format: inputFormat) { [weak self] buffer, _ in
            let level = Self.rms(of: buffer)
            Task { @MainActor in
                self?.audioLevel = level
                self?.request?.append(buffer)
            }
            if let converted = Self.convert(buffer, converter: audioConverter, targetFormat: format),
               wakeWord.process(converted) {
                Task { @MainActor in self?.handleWakeWordFired() }
            }
        }

        engine.prepare()
        try engine.start()
        if transcribing { beginTranscription() }
    }

    private func beginTranscription() {
        guard let recognizer, recognizer.isAvailable else { return }
        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        if recognizer.supportsOnDeviceRecognition { request.requiresOnDeviceRecognition = true }
        self.request = request
        recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self else { return }
            if let result {
                Task { @MainActor in self.transcript = result.bestTranscription.formattedString }
            }
            if error != nil { /* keep capture alive; transcript stays as-is */ }
        }
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

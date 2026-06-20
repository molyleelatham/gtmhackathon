import Foundation
import Speech
import AVFoundation
import UIKit

/// Listens for hardcoded trigger phrases (e.g. "hey its nice to meet you") using on-device speech recognition.
@MainActor
final class PhraseTriggerEngine: NSObject, ObservableObject {
    static let shared = PhraseTriggerEngine()

    @Published private(set) var isListening = false

    private let triggerPhrases = ["hey its nice to meet you", "its nice to meet you"]
    private let triggerCooldown: TimeInterval = 3

    private var speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()

    private var lastTriggerDate: Date?
    private var shouldBeListening = false

    private override init() {
        super.init()
        speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    }

    func startListening() {
        shouldBeListening = true
        guard SFSpeechRecognizer.authorizationStatus() == .authorized else { return }
        guard !isListening else { return }
        beginRecognition()
    }

    func stopListening() {
        shouldBeListening = false
        tearDownRecognition()
    }

    // MARK: - Recognition

    private func beginRecognition() {
        guard let speechRecognizer, speechRecognizer.isAvailable else { return }

        tearDownRecognition()

        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        if speechRecognizer.supportsOnDeviceRecognition {
            request.requiresOnDeviceRecognition = true
        }

        recognitionRequest = request

        recognitionTask = speechRecognizer.recognitionTask(with: request) { [weak self] result, error in
            Task { @MainActor in
                guard let self else { return }

                if let result {
                    self.checkForTrigger(in: result.bestTranscription.formattedString)
                }

                if error != nil || (result?.isFinal ?? false) {
                    self.restartIfNeeded()
                }
            }
        }

        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)

        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.recognitionRequest?.append(buffer)
        }

        do {
            try audioEngine.start()
            isListening = true
        } catch {
            print("PhraseTriggerEngine: failed to start audio engine: \(error)")
            tearDownRecognition()
        }
    }

    private func restartIfNeeded() {
        tearDownRecognition()
        if shouldBeListening {
            beginRecognition()
        }
    }

    private func tearDownRecognition() {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()
        recognitionRequest = nil
        recognitionTask = nil
        isListening = false
    }

    // MARK: - Trigger matching

    private func checkForTrigger(in transcript: String) {
        let normalized = normalize(transcript)
        guard triggerPhrases.contains(where: { normalized.contains($0) }) else { return }

        if let lastTriggerDate, Date().timeIntervalSince(lastTriggerDate) < triggerCooldown {
            return
        }
        lastTriggerDate = Date()

        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.prepare()
        generator.impactOccurred()

        RecordingEngine.shared.startRecording()
    }

    private func normalize(_ text: String) -> String {
        var result = text.lowercased()
        result = result.replacingOccurrences(of: "'", with: "")
        result = result.replacingOccurrences(of: "’", with: "")

        let allowed = CharacterSet.alphanumerics.union(.whitespaces)
        result = String(result.unicodeScalars.filter { allowed.contains($0) })

        return result
            .split(whereSeparator: \.isWhitespace)
            .joined(separator: " ")
    }
}

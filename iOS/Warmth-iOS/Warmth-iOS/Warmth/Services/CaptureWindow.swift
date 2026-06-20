import Foundation
import Speech
import AVFoundation

/// A bounded (default 30s) on-device transcription session opened after a wake
/// word fires. Recognition is biased toward ICP vocabulary via a custom
/// language model so domain terms ("RevOps", "Series B") transcribe reliably.
@MainActor
final class CaptureWindow {
    private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?
    private var timer: Timer?

    private let vocabulary: ICPVocabulary
    private var customModelURL: URL?

    /// Emitted as the transcript grows (for live UI).
    var onPartialTranscript: ((String) -> Void)?

    private(set) var isCapturing = false

    init(vocabulary: ICPVocabulary = .default) {
        self.vocabulary = vocabulary
    }

    /// Prepare the ICP custom language model once. Safe to call repeatedly.
    func prepareLanguageModel() async {
        guard customModelURL == nil else { return }
        do {
            let url = FileManager.default.temporaryDirectory
                .appendingPathComponent("warmth-icp.bin")
            let data = SFCustomLanguageModelData(
                locale: Locale(identifier: "en_US"),
                identifier: "ai.warmth.icp",
                version: "1.0"
            ) {
                for phrase in vocabulary.biasPhrases {
                    SFCustomLanguageModelData.PhraseCount(phrase: phrase, count: 10)
                }
            }
            try await data.export(to: url)
            customModelURL = url
        } catch {
            print("CaptureWindow: custom LM prep failed (continuing without): \(error)")
        }
    }

    /// Open a capture window. `appendBuffer` should be called with mic buffers
    /// while `isCapturing` is true. `completion` returns the final transcript.
    func begin(duration: TimeInterval = 30, completion: @escaping (String) -> Void) {
        guard !isCapturing, let recognizer, recognizer.isAvailable else {
            completion("")
            return
        }

        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        if recognizer.supportsOnDeviceRecognition {
            request.requiresOnDeviceRecognition = true
        }
        if let customModelURL {
            request.customizedLanguageModel =
                SFSpeechLanguageModel.Configuration(languageModel: customModelURL)
        }
        self.request = request
        isCapturing = true

        var latest = ""
        task = recognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self else { return }
            if let result {
                latest = result.bestTranscription.formattedString
                self.onPartialTranscript?(latest)
            }
            if error != nil || (result?.isFinal ?? false) {
                self.finish(with: latest, completion: completion)
            }
        }

        timer = Timer.scheduledTimer(withTimeInterval: duration, repeats: false) { [weak self] _ in
            Task { @MainActor in self?.end() }
        }
    }

    /// Feed a microphone buffer into the active recognition request.
    func appendBuffer(_ buffer: AVAudioPCMBuffer) {
        guard isCapturing else { return }
        request?.append(buffer)
    }

    /// Stop early; recognition flushes and calls the completion handler.
    func end() {
        guard isCapturing else { return }
        request?.endAudio()
    }

    private var completionFired = false
    private func finish(with transcript: String, completion: @escaping (String) -> Void) {
        guard isCapturing, !completionFired else { return }
        completionFired = true

        timer?.invalidate()
        timer = nil
        task?.cancel()
        task = nil
        request = nil
        isCapturing = false

        let final = transcript
        completionFired = false
        completion(final)
    }
}

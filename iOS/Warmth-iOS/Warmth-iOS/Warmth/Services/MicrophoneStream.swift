import Foundation
import AVFoundation

/// Owns the single shared `AVAudioEngine` input tap and fans audio out to both
/// the wake-word detector (as 16 kHz mono `[Float]`) and the capture-window
/// speech recognizer (as the original `AVAudioPCMBuffer`).
final class MicrophoneStream {
    /// Called for every input buffer. `frame16k` is downsampled mono Float32 at
    /// 16 kHz; `raw` is the untouched input buffer (fed to SFSpeech as-is).
    var onFrame: ((_ raw: AVAudioPCMBuffer, _ frame16k: [Float]) -> Void)?

    private let engine = AVAudioEngine()
    private var converter: AVAudioConverter?
    private let targetFormat = AVAudioFormat(
        commonFormat: .pcmFormatFloat32,
        sampleRate: 16_000,
        channels: 1,
        interleaved: false
    )!

    private(set) var isRunning = false

    func start() throws {
        guard !isRunning else { return }

        let input = engine.inputNode
        let inputFormat = input.outputFormat(forBus: 0)
        converter = AVAudioConverter(from: inputFormat, to: targetFormat)

        input.installTap(onBus: 0, bufferSize: 1024, format: inputFormat) { [weak self] buffer, _ in
            guard let self else { return }
            let frame = self.downsample(buffer) ?? []
            self.onFrame?(buffer, frame)
        }

        engine.prepare()
        try engine.start()
        isRunning = true
    }

    func stop() {
        guard isRunning else { return }
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        isRunning = false
    }

    // MARK: - Conversion

    private func downsample(_ buffer: AVAudioPCMBuffer) -> [Float]? {
        guard let converter else { return nil }

        let ratio = targetFormat.sampleRate / buffer.format.sampleRate
        let capacity = AVAudioFrameCount(Double(buffer.frameLength) * ratio) + 1
        guard let out = AVAudioPCMBuffer(pcmFormat: targetFormat, frameCapacity: capacity) else {
            return nil
        }

        var fed = false
        var error: NSError?
        converter.convert(to: out, error: &error) { _, status in
            if fed {
                status.pointee = .noDataNow
                return nil
            }
            fed = true
            status.pointee = .haveData
            return buffer
        }

        if error != nil { return nil }
        guard let channel = out.floatChannelData?[0] else { return nil }
        return Array(UnsafeBufferPointer(start: channel, count: Int(out.frameLength)))
    }
}

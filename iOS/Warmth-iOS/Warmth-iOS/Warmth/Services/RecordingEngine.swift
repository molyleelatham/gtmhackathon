import Foundation
import AVFoundation
import Combine

class RecordingEngine: NSObject, ObservableObject {
    static let shared = RecordingEngine()
    
    @Published var isRecording = false
    @Published var currentTranscript = ""
    @Published var recordingDuration: TimeInterval = 0
    
    private var audioRecorder: AVAudioRecorder?
    private var deepgramClient: DeepgramClient?
    private var recordingTimer: Timer?
    private var recordingStartTime: Date?
    
    private let audioSessionManager = AudioSessionManager.shared
    
    private override init() {
        super.init()
        deepgramClient = DeepgramClient()
    }
    
    func startRecording() {
        guard !isRecording else { return }
        
        do {
            try audioSessionManager.configureForRecording()
            
            let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            let recordingURL = documentsPath.appendingPathComponent("recording_\(Date().timeIntervalSince1970).m4a")
            
            let settings: [String: Any] = [
                AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                AVSampleRateKey: 16000.0,
                AVNumberOfChannelsKey: 1,
                AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
            ]
            
            audioRecorder = try AVAudioRecorder(url: recordingURL, settings: settings)
            audioRecorder?.delegate = self
            audioRecorder?.record()
            
            deepgramClient?.startStreaming { [weak self] transcript in
                DispatchQueue.main.async {
                    self?.currentTranscript = transcript
                }
            }
            
            recordingStartTime = Date()
            recordingTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
                self?.updateRecordingDuration()
            }
            
            isRecording = true
            print("Recording started")
            
        } catch {
            print("Failed to start recording: \(error)")
        }
    }
    
    func stopRecording() {
        guard isRecording else { return }
        
        audioRecorder?.stop()
        audioRecorder = nil
        
        deepgramClient?.stopStreaming()
        
        recordingTimer?.invalidate()
        recordingTimer = nil
        
        isRecording = false
        recordingDuration = 0
        recordingStartTime = nil
        
        print("Recording stopped")
    }
    
    private func updateRecordingDuration() {
        guard let startTime = recordingStartTime else { return }
        recordingDuration = Date().timeIntervalSince(startTime)
    }
}

extension RecordingEngine: AVAudioRecorderDelegate {
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        if successfully {
            print("Recording finished successfully")
        } else {
            print("Recording finished with errors")
        }
    }
}

class DeepgramClient {
    private var webSocketTask: URLSessionWebSocketTask?
    
    func startStreaming(transcriptHandler: @escaping (String) -> Void) {
        // Deepgram WebSocket streaming implementation
        print("Starting Deepgram streaming...")
    }
    
    func stopStreaming() {
        webSocketTask?.cancel()
        print("Stopped Deepgram streaming")
    }
}
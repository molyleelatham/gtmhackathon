import Foundation
import AVFoundation
import Porcupine

class WakeWordEngine: NSObject {
    static let shared = WakeWordEngine()
    
    private var porcupineManager: PvPorcupineManager?
    private var isListening = false
    private let wakeWordCallback: () -> Void
    
    private override init() {
        self.wakeWordCallback = { [weak self] in
            self?.handleWakeWordDetection()
        }
        super.init()
    }
    
    func startListening() throws {
        guard !isListening else { return }
        
        let keywordPath = Bundle.main.path(forResource: "hey_anna", ofType: "ppn")
        guard let keywordPath = keywordPath else {
            throw WakeWordError.keywordFileNotFound
        }
        
        let accessKey = Bundle.main.object(forInfoDictionaryKey: "PorcupineAccessKey") as? String ?? ""
        guard !accessKey.isEmpty else {
            throw WakeWordError.accessKeyNotFound
        }
        
        porcupineManager = PvPorcupineManager(
            accessKey: accessKey,
            keywordPaths: [keywordPath],
            sensitivities: [0.5],
            onDetection: { [weak self] _ in
                self?.handleWakeWordDetection()
            }
        )
        
        try porcupineManager?.start()
        isListening = true
    }
    
    private func handleWakeWordDetection() {
        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.impactOccurred()
        wakeWordCallback()
    }
}

enum WakeWordError: Error {
    case keywordFileNotFound
    case accessKeyNotFound
}
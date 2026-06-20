import Foundation
import WatchConnectivity

class WatchConnectivityService: NSObject, ObservableObject {
    static let shared = WatchConnectivityService()
    
    @Published var isRecording = false
    @Published var watchConnected = false
    
    private let session: WCSession
    private let recordingEngine = RecordingEngine.shared
    
    private override init() {
        self.session = WCSession.default
        super.init()
        
        if WCSession.isSupported() {
            session.delegate = self
            session.activate()
        }
    }
    
    private func sendRecordingStateToWatch() {
        let message: [String: Any] = [
            "action": "recordingStateChanged",
            "isRecording": isRecording,
            "timestamp": Date().timeIntervalSince1970
        ]
        
        if session.isReachable {
            session.sendMessage(message, replyHandler: nil)
        } else {
            session.transferUserInfo(message)
        }
    }

    // MARK: - Lead notifications

    /// Light confirmation buzz when a wake word fires and a capture window opens.
    func notifyWakeWord(name: String?) {
        send([
            "action": "wakeWord",
            "name": name ?? "",
            "timestamp": Date().timeIntervalSince1970
        ])
    }

    /// Strong notification when a qualified lead is detected mid-conversation.
    func notifyLeadDetected(name: String, score: Double) {
        send([
            "action": "leadDetected",
            "name": name,
            "score": score,
            "timestamp": Date().timeIntervalSince1970
        ])
    }

    private func send(_ message: [String: Any]) {
        if session.isReachable {
            session.sendMessage(message, replyHandler: nil, errorHandler: nil)
        } else {
            session.transferUserInfo(message)
        }
    }
}

extension WatchConnectivityService: WCSessionDelegate {
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        DispatchQueue.main.async {
            self.watchConnected = activationState == .activated
            if self.watchConnected {
                self.sendRecordingStateToWatch()
            }
        }
    }
    
    func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        DispatchQueue.main.async {
            if let action = message["action"] as? String, action == "toggleRecording" {
                if self.isRecording {
                    self.recordingEngine.stopRecording()
                } else {
                    self.recordingEngine.startRecording()
                }
                self.isRecording.toggle()
                self.sendRecordingStateToWatch()
            }
        }
    }
}
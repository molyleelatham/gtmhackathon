import Foundation
import WatchConnectivity

class WatchConnectivityService: NSObject, ObservableObject {
    static let shared = WatchConnectivityService()
    
    @Published var isRecording = false
    
    private let session: WCSession
    
    private override init() {
        self.session = WCSession.default
        super.init()
        
        if WCSession.isSupported() {
            session.delegate = self
            session.activate()
        }
    }
    
    func toggleRecording() {
        let message: [String: Any] = [
            "action": "toggleRecording",
            "timestamp": Date().timeIntervalSince1970
        ]
        
        if session.isReachable {
            session.sendMessage(message, replyHandler: { [weak self] response in
                DispatchQueue.main.async {
                    if let isRecording = response["isRecording"] as? Bool {
                        self?.isRecording = isRecording
                    }
                }
            }, errorHandler: nil)
        }
    }
}

extension WatchConnectivityService: WCSessionDelegate {
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        DispatchQueue.main.async {
            if activationState == .activated {
                self.requestStatus()
            }
        }
    }
    
    func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        DispatchQueue.main.async {
            if let isRecording = applicationContext["isRecording"] as? Bool {
                self.isRecording = isRecording
            }
        }
    }
    
    private func requestStatus() {
        let message: [String: Any] = ["action": "requestStatus", "timestamp": Date().timeIntervalSince1970]
        session.sendMessage(message, replyHandler: { [weak self] response in
            DispatchQueue.main.async {
                if let isRecording = response["isRecording"] as? Bool {
                    self?.isRecording = isRecording
                }
            }
        }, errorHandler: nil)
    }
}
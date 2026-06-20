import Foundation
import WatchConnectivity
import WatchKit

class WatchConnectivityService: NSObject, ObservableObject {
    static let shared = WatchConnectivityService()

    @Published var isRecording = false
    /// Most recently detected lead, surfaced on the watch.
    @Published var lastLeadName: String?
    @Published var lastLeadScore: Double = 0

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

    func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        DispatchQueue.main.async { self.handle(message) }
    }

    func session(_ session: WCSession, didReceiveUserInfo userInfo: [String: Any] = [:]) {
        DispatchQueue.main.async { self.handle(userInfo) }
    }

    private func handle(_ message: [String: Any]) {
        guard let action = message["action"] as? String else { return }
        switch action {
        case "leadDetected":
            lastLeadName = message["name"] as? String
            lastLeadScore = message["score"] as? Double ?? 0
            WKInterfaceDevice.current().play(.notification)
        case "wakeWord":
            WKInterfaceDevice.current().play(.click)
        case "recordingStateChanged":
            if let isRecording = message["isRecording"] as? Bool {
                self.isRecording = isRecording
            }
        default:
            break
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
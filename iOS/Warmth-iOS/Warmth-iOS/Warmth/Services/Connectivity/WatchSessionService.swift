import Foundation
import Observation
import WatchConnectivity

/// Phone-side WatchConnectivity bridge for the Warmth Apple Watch companion.
///
/// This type is intentionally **self-contained**: it has no dependency on the
/// app's capture/speech stack. The app wires it up with two closures and one
/// push method, so it can be dropped in without touching capture internals.
///
/// ## How to integrate (single hook)
/// Create one instance high in the app (e.g. on your `AppModel`) and connect it:
/// ```swift
/// let watch = WatchSessionService()
/// watch.onStartRequested = { speech.startCapture() }   // wrist → phone
/// watch.onStopRequested  = { speech.stopCapture() }    // wrist → phone
/// // Whenever capture state changes on the phone, mirror it to the watch:
/// watch.updateState(isRecording: speech.isRecording,
///                   elapsed: speech.elapsed,
///                   lastPersonName: speech.lastPerson?.name,
///                   lastPersonOrg: speech.lastPerson?.company)
/// ```
/// The capture service may be named `SpeechService`, `CaptureViewModel`, etc. —
/// only the four values above are needed.
///
/// ## Protocol
/// - Watch → phone (`sendMessage` / `applicationContext`):
///   `["action": "toggleRecording" | "startRecording" | "stopRecording"]`
/// - Phone → watch (`updateApplicationContext`, plus `sendMessage` when reachable):
///   `["action": "recordingStateChanged", "isRecording": Bool, "elapsed": TimeInterval,
///     "lastPersonName": String?, "lastPersonOrg": String?]`
@MainActor
@Observable
final class WatchSessionService: NSObject {
    /// Mirror of the phone's capture state (kept in sync by the app via `updateState`).
    private(set) var isRecording = false
    /// True once a paired watch is reachable for live `sendMessage`.
    private(set) var isWatchReachable = false
    private(set) var isActivated = false

    /// Called when the wrist asks to begin capture. Wire to your capture service.
    var onStartRequested: () -> Void = {}
    /// Called when the wrist asks to end capture. Wire to your capture service.
    var onStopRequested: () -> Void = {}

    private let session: WCSession
    private var lastElapsed: TimeInterval = 0
    private var lastPersonName: String?
    private var lastPersonOrg: String?

    init(session: WCSession = .default) {
        self.session = session
        super.init()
        guard WCSession.isSupported() else { return }
        session.delegate = self
        session.activate()
    }

    // MARK: - Phone → watch

    /// Push the latest capture state to the watch. Call this whenever recording
    /// starts/stops or a new person/org is detected.
    func updateState(isRecording: Bool,
                     elapsed: TimeInterval,
                     lastPersonName: String?,
                     lastPersonOrg: String?) {
        self.isRecording = isRecording
        self.lastElapsed = elapsed
        self.lastPersonName = lastPersonName
        self.lastPersonOrg = lastPersonOrg
        pushState()
    }

    private func payload() -> [String: Any] {
        var p: [String: Any] = [
            "action": "recordingStateChanged",
            "isRecording": isRecording,
            "elapsed": lastElapsed
        ]
        if let lastPersonName { p["lastPersonName"] = lastPersonName }
        if let lastPersonOrg { p["lastPersonOrg"] = lastPersonOrg }
        return p
    }

    private func pushState() {
        guard session.activationState == .activated else { return }
        let p = payload()
        // Latest-state sync survives the watch being asleep.
        try? session.updateApplicationContext(p)
        // Immediate delivery when the watch is in the foreground.
        if session.isReachable {
            session.sendMessage(p, replyHandler: nil, errorHandler: { _ in })
        }
    }

    // MARK: - Intent handling

    private func handle(action: String) {
        switch action {
        case "startRecording":
            onStartRequested()
        case "stopRecording":
            onStopRequested()
        case "toggleRecording":
            (isRecording ? onStopRequested : onStartRequested)()
        default:
            break
        }
    }
}

// MARK: - WCSessionDelegate

extension WatchSessionService: WCSessionDelegate {
    nonisolated func session(_ session: WCSession,
                             activationDidCompleteWith activationState: WCSessionActivationState,
                             error: Error?) {
        let reachable = session.isReachable
        Task { @MainActor in
            self.isActivated = (activationState == .activated)
            self.isWatchReachable = reachable
            // Send current state so a freshly-launched watch is immediately correct.
            self.pushState()
        }
    }

    nonisolated func sessionReachabilityDidChange(_ session: WCSession) {
        let reachable = session.isReachable
        Task { @MainActor in self.isWatchReachable = reachable }
    }

    nonisolated func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        guard let action = message["action"] as? String else { return }
        Task { @MainActor in self.handle(action: action) }
    }

    nonisolated func session(_ session: WCSession,
                             didReceiveMessage message: [String: Any],
                             replyHandler: @escaping ([String: Any]) -> Void) {
        // Ack synchronously (the closure is non-Sendable, so we don't carry it onto
        // the main actor). Authoritative state follows via `updateApplicationContext`
        // once the app reacts and calls `updateState(...)`.
        replyHandler(["ack": true])
        guard let action = message["action"] as? String else { return }
        Task { @MainActor in self.handle(action: action) }
    }

    nonisolated func session(_ session: WCSession,
                             didReceiveApplicationContext applicationContext: [String: Any]) {
        guard let action = applicationContext["action"] as? String else { return }
        Task { @MainActor in self.handle(action: action) }
    }

    // Required on iOS so the session can re-activate after switching watches.
    nonisolated func sessionDidBecomeInactive(_ session: WCSession) {}

    nonisolated func sessionDidDeactivate(_ session: WCSession) {
        session.activate()
    }
}

#if DEBUG
/// Lightweight stand-in for previews/tests — never touches `WCSession`.
@MainActor
@Observable
final class MockWatchSessionService {
    private(set) var isRecording: Bool
    private(set) var isWatchReachable: Bool
    var onStartRequested: () -> Void = {}
    var onStopRequested: () -> Void = {}

    init(isRecording: Bool = false, isWatchReachable: Bool = true) {
        self.isRecording = isRecording
        self.isWatchReachable = isWatchReachable
    }

    func updateState(isRecording: Bool, elapsed: TimeInterval,
                     lastPersonName: String?, lastPersonOrg: String?) {
        self.isRecording = isRecording
    }
}
#endif

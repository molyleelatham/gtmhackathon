import Foundation
import Observation
import WatchConnectivity
import WidgetKit

/// Watch-side WatchConnectivity client.
///
/// Reflects the phone's capture state and lets the wrist drive start/stop. It is
/// the single source of truth for the watch UI and also mirrors state into the
/// App Group so the complication can show live status.
///
/// Protocol (see also `WatchSessionService` on the phone):
/// - Watch → phone `sendMessage`: `["action": "toggleRecording" | "startRecording" | "stopRecording"]`
/// - Phone → watch `updateApplicationContext` / `sendMessage`:
///   `["action": "recordingStateChanged", "isRecording": Bool, "elapsed": TimeInterval,
///     "lastPersonName": String?, "lastPersonOrg": String?]`
@MainActor
@Observable
final class WatchConnectivityService: NSObject {
    /// Whether the phone is currently capturing.
    private(set) var isRecording = false
    /// Absolute moment recording began — drives a self-updating SwiftUI timer.
    private(set) var recordingStartedAt: Date?
    private(set) var lastPersonName: String?
    private(set) var lastPersonOrg: String?
    /// True once the phone counterpart is reachable for live `sendMessage`.
    private(set) var isPhoneReachable = false
    /// True once `WCSession` has finished activating.
    private(set) var isActivated = false

    private let session: WCSession

    init(session: WCSession = .default) {
        self.session = session
        super.init()
        guard WCSession.isSupported() else { return }
        session.delegate = self
        session.activate()
        // Seed UI from any context the phone pushed while we were asleep.
        applyContext(session.receivedApplicationContext)
    }

    // MARK: - Wrist → phone intents

    /// Toggle capture. Sends a live message when reachable, otherwise records the
    /// intent via application context so the phone picks it up on next launch.
    func toggleRecording() {
        send(action: isRecording ? "stopRecording" : "startRecording")
    }

    func requestStart() { send(action: "startRecording") }
    func requestStop() { send(action: "stopRecording") }

    private func send(action: String) {
        guard WCSession.isSupported(), session.activationState == .activated else { return }
        let payload: [String: Any] = ["action": action, "ts": Date().timeIntervalSince1970]

        if session.isReachable {
            session.sendMessage(payload, replyHandler: { [weak self] reply in
                guard let recording = reply["isRecording"] as? Bool else { return }
                let elapsed = reply["elapsed"] as? TimeInterval ?? 0
                let name = reply["lastPersonName"] as? String
                let org = reply["lastPersonOrg"] as? String
                Task { @MainActor in
                    self?.applyState(isRecording: recording, elapsed: elapsed,
                                     lastPersonName: name, lastPersonOrg: org)
                }
            }, errorHandler: { _ in })
        } else {
            // Best-effort: stash the desired action; phone reconciles on activation.
            do {
                try session.updateApplicationContext(payload)
            } catch {
                // Phone unreachable or WC not ready — intent is dropped safely.
            }
        }
    }

    // MARK: - State application (main actor)

    private func applyState(isRecording: Bool, elapsed: TimeInterval,
                            lastPersonName: String?, lastPersonOrg: String?) {
        self.isRecording = isRecording
        if isRecording {
            // Anchor the start so `Text(_, style: .timer)` ticks correctly.
            self.recordingStartedAt = Date().addingTimeInterval(-max(0, elapsed))
        } else {
            self.recordingStartedAt = nil
        }
        self.lastPersonName = lastPersonName
        self.lastPersonOrg = lastPersonOrg
        mirrorToComplication()
    }

    private func applyContext(_ context: [String: Any]) {
        guard !context.isEmpty else { return }
        guard (context["action"] as? String) == "recordingStateChanged" ||
                context["isRecording"] != nil else { return }
        let recording = context["isRecording"] as? Bool ?? false
        let elapsed = context["elapsed"] as? TimeInterval ?? 0
        let name = context["lastPersonName"] as? String
        let org = context["lastPersonOrg"] as? String
        applyState(isRecording: recording, elapsed: elapsed,
                   lastPersonName: name, lastPersonOrg: org)
    }

    private func mirrorToComplication() {
        WatchSharedStore.save(
            WatchSharedState(
                isRecording: isRecording,
                recordingStartedAt: recordingStartedAt,
                lastPersonName: lastPersonName,
                lastPersonOrg: lastPersonOrg
            )
        )
        WidgetCenter.shared.reloadAllTimelines()
    }
}

// MARK: - WCSessionDelegate

extension WatchConnectivityService: WCSessionDelegate {
    nonisolated func session(_ session: WCSession,
                             activationDidCompleteWith activationState: WCSessionActivationState,
                             error: Error?) {
        let reachable = session.isReachable
        Task { @MainActor in
            self.isActivated = (activationState == .activated)
            self.isPhoneReachable = reachable
        }
    }

    nonisolated func sessionReachabilityDidChange(_ session: WCSession) {
        let reachable = session.isReachable
        Task { @MainActor in self.isPhoneReachable = reachable }
    }

    nonisolated func session(_ session: WCSession,
                             didReceiveApplicationContext applicationContext: [String: Any]) {
        let snapshot = Self.snapshot(from: applicationContext)
        Task { @MainActor in self.applyState(isRecording: snapshot.0, elapsed: snapshot.1,
                                             lastPersonName: snapshot.2, lastPersonOrg: snapshot.3) }
    }

    nonisolated func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        let snapshot = Self.snapshot(from: message)
        Task { @MainActor in self.applyState(isRecording: snapshot.0, elapsed: snapshot.1,
                                             lastPersonName: snapshot.2, lastPersonOrg: snapshot.3) }
    }

    /// Extracts Sendable primitives from a non-Sendable payload off the main actor.
    nonisolated private static func snapshot(
        from payload: [String: Any]
    ) -> (Bool, TimeInterval, String?, String?) {
        (
            payload["isRecording"] as? Bool ?? false,
            payload["elapsed"] as? TimeInterval ?? 0,
            payload["lastPersonName"] as? String,
            payload["lastPersonOrg"] as? String
        )
    }
}

#if DEBUG
extension WatchConnectivityService {
    /// Seeds an instance with deterministic state for `#Preview`s.
    @MainActor
    static func preview(isRecording: Bool,
                        elapsed: TimeInterval = 0,
                        name: String? = nil,
                        org: String? = nil,
                        reachable: Bool = true) -> WatchConnectivityService {
        let service = WatchConnectivityService()
        service.isPhoneReachable = reachable
        service.isActivated = true
        service.applyState(isRecording: isRecording, elapsed: elapsed,
                           lastPersonName: name, lastPersonOrg: org)
        return service
    }
}
#endif

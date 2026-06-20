import Foundation

/// Outcome of an attempt, surfaced for lightweight diagnostics in Settings.
enum SignalDeliveryState: Sendable, Equatable {
    case idle
    case sending
    case delivered
    case queued(Int)   // number of signals waiting in the retry queue
    case failed(String)
}

/// Fire-and-forget uploader for `CapturedSignal`s with a retry queue. Abstracted so
/// the app can run against a mock and so a base-URL change doesn't ripple through UI.
@MainActor
protocol SignalSending: AnyObject {
    var deliveryState: SignalDeliveryState { get }
    var baseURL: URL { get }
    func updateBaseURL(_ url: URL)
    /// Enqueue + attempt delivery without blocking the caller.
    func send(_ signal: CapturedSignal)
    /// Retry anything still queued (e.g. when connectivity returns).
    func flushQueue() async
}

/// No-op uploader for previews/tests.
@MainActor
@Observable
final class MockSignalClient: SignalSending {
    var deliveryState: SignalDeliveryState = .idle
    private(set) var sent: [CapturedSignal] = []
    var baseURL: URL = URL(string: "https://api.warmth.example.com")!

    func updateBaseURL(_ url: URL) { baseURL = url }
    func send(_ signal: CapturedSignal) { sent.append(signal); deliveryState = .delivered }
    func flushQueue() async {}
}

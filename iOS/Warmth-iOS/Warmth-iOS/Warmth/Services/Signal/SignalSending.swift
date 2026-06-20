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
    /// Match a live "hi {name}" greeting to a known event attendee.
    func matchAttendee(name: String, company: String?, transcript: String?) async -> AttendeeMatchResult?
    /// First names from the backend roster for wake-word watchlist hydration.
    func fetchRosterFirstNames() async -> [String]
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
    func matchAttendee(name: String, company: String?, transcript: String?) async -> AttendeeMatchResult? {
        AttendeeMatchResult(
            matched: true,
            name: name,
            message: "You're now connected with \(name).",
            score: 0.92,
            matchedOn: ["first_name"],
            connection: MatchedConnection(
                id: "preview",
                name: name,
                title: "VP Sales",
                companyName: company ?? "Acme",
                predictedWarmth: 82,
                icpScore: 88
            ),
            interests: ["RevOps", "AI GTM", "Pipeline"],
            knowledgeGraph: [KnowledgeGraphSnapshot(topicWeights: ["pipeline": 0.8, "ai": 0.6], values: ["speed"])]
        )
    }
    func fetchRosterFirstNames() async -> [String] { ["Anna", "James", "Sarah"] }
}

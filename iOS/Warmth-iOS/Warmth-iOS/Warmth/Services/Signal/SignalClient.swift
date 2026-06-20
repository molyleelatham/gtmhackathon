import Foundation

/// Fire-and-forget uploader: POSTs `CapturedSignal`s to `{baseURL}/api/signals`.
/// Failures (flaky Wi-Fi, unreachable placeholder host) are appended to an in-memory
/// retry queue and resent on the next `flushQueue()` — never blocking capture.
@MainActor
@Observable
final class SignalClient: SignalSending {
    private(set) var deliveryState: SignalDeliveryState = .idle
    private(set) var baseURL: URL

    private let session: URLSession
    private let encoder = CapturedSignal.makeEncoder()
    /// Signals awaiting retry.
    private var queue: [CapturedSignal] = []
    private let maxQueue = 100

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    func updateBaseURL(_ url: URL) { baseURL = url }

    func send(_ signal: CapturedSignal) {
        deliveryState = .sending
        Task { await attempt(signal) }
    }

    func flushQueue() async {
        guard !queue.isEmpty else { return }
        let pending = queue
        queue.removeAll()
        for signal in pending { await attempt(signal) }
    }

    // MARK: - Internals

    private var endpoint: URL { baseURL.appendingPathComponent("api/signals") }

    private func attempt(_ signal: CapturedSignal) async {
        guard let body = try? encoder.encode(signal) else {
            deliveryState = .failed("Could not encode signal")
            return
        }
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = body
        request.timeoutInterval = 10

        do {
            let (_, response) = try await session.data(for: request)
            if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
                enqueue(signal, reason: "HTTP \(http.statusCode)")
            } else {
                deliveryState = queue.isEmpty ? .delivered : .queued(queue.count)
            }
        } catch {
            enqueue(signal, reason: error.localizedDescription)
        }
    }

    private func enqueue(_ signal: CapturedSignal, reason: String) {
        if queue.count >= maxQueue { queue.removeFirst() }
        queue.append(signal)
        deliveryState = .queued(queue.count)
    }

    var queuedCount: Int { queue.count }
}

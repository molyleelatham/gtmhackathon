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
    private weak var auth: (any AuthProviding)?
    /// Signals awaiting retry.
    private var queue: [CapturedSignal] = []
    private let maxQueue = 100

    init(baseURL: URL, session: URLSession = .shared, auth: (any AuthProviding)? = nil) {
        self.baseURL = baseURL
        self.session = session
        self.auth = auth
    }

    func bindAuth(_ auth: any AuthProviding) {
        self.auth = auth
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
        await auth?.applyAuthorization(to: &request)

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

    // MARK: - Attendee match + roster

    func matchAttendee(name: String, company: String? = nil, transcript: String? = nil) async -> AttendeeMatchResult? {
        let endpoint = baseURL.appendingPathComponent("api/v1/match/attendee")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 8

        var payload: [String: String] = ["name": name]
        if let company { payload["company"] = company }
        if let transcript { payload["transcript"] = transcript }

        guard let body = try? JSONSerialization.data(withJSONObject: payload) else { return nil }

        request.httpBody = body
        await auth?.applyAuthorization(to: &request)
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { return nil }
            let decoder = JSONDecoder()
            decoder.keyDecodingStrategy = .convertFromSnakeCase
            return try decoder.decode(AttendeeMatchResult.self, from: data)
        } catch {
            return nil
        }
    }

    func fetchRosterFirstNames() async -> [String] {
        let endpoint = baseURL.appendingPathComponent("api/v1/connections")
        var request = URLRequest(url: endpoint)
        request.timeoutInterval = 8
        await auth?.applyAuthorization(to: &request)
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { return [] }
            let decoder = JSONDecoder()
            decoder.keyDecodingStrategy = .convertFromSnakeCase
            let rows = try decoder.decode([RosterConnectionRow].self, from: data)
            return rows.compactMap { $0.name?.split(separator: " ").first.map(String.init) }
        } catch {
            return []
        }
    }
}

// MARK: - Attendee match models

struct AttendeeMatchResult: Codable, Equatable {
    let matched: Bool
    let name: String?
    let message: String
    let score: Double?
    let matchedOn: [String]?
    let connection: MatchedConnection?
    let interests: [String]?
    let knowledgeGraph: [KnowledgeGraphSnapshot]?
}

struct MatchedConnection: Codable, Equatable {
    let id: String?
    let name: String?
    let title: String?
    let companyName: String?
    let predictedWarmth: Double?
    let icpScore: Double?
}

struct KnowledgeGraphSnapshot: Codable, Equatable {
    let topicWeights: [String: Double]?
    let values: [String]?
}

private struct RosterConnectionRow: Codable {
    let name: String?
}

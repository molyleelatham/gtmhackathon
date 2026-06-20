import Foundation

enum CRMFetchState: Equatable, Sendable {
    case idle
    case loading
    case loaded
    case failed(String)
}

/// Read-only CRM client — mirrors the web dashboard's `api.ts` calls against
/// `/api/v1/*` on the same FastAPI backend the iOS signal uploader uses.
@MainActor
protocol CRMProviding: AnyObject {
    var baseURL: URL { get }
    var connections: [CRMConnection] { get }
    var fetchState: CRMFetchState { get }
    func updateBaseURL(_ url: URL)
    func refreshConnections() async
    func connectionDetail(id: String) async throws -> CRMConnectionDetail
    func fetchDashboard() async throws -> CRMDashboardSummary
    func fetchRoster() async throws -> CRMRoster
    func fetchCommunityMembers() async throws -> [CRMCommunityMember]
    func fetchEvents() async throws -> [CRMDetectedEvent]
    func fetchICPProfile() async throws -> [CRMICPRow]
    func sendFollowup(connectionId: String) async throws -> CRMFollowUpDraft
}

@MainActor
@Observable
final class WarmthAPIClient: CRMProviding {
    private(set) var baseURL: URL
    private(set) var connections: [CRMConnection] = []
    private(set) var fetchState: CRMFetchState = .idle

    private let session: URLSession
    private let decoder: JSONDecoder

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
        self.decoder = JSONDecoder()
    }

    func updateBaseURL(_ url: URL) {
        baseURL = url
    }

    func refreshConnections() async {
        fetchState = .loading
        do {
            let items = try await listConnections()
            connections = items.sorted { $0.predictedWarmth > $1.predictedWarmth }
            fetchState = .loaded
        } catch {
            fetchState = .failed(error.localizedDescription)
        }
    }

    func connectionDetail(id: String) async throws -> CRMConnectionDetail {
        let url = baseURL.appendingPathComponent("api/v1/connections/\(id)")
        let (data, response) = try await session.data(from: url)
        try validate(response)
        return try parseDetail(data)
    }

    func fetchDashboard() async throws -> CRMDashboardSummary {
        let url = baseURL.appendingPathComponent("api/v1/dashboard")
        let (data, response) = try await session.data(from: url)
        try validate(response)
        return try decoder.decode(CRMDashboardSummary.self, from: data)
    }

    func fetchRoster() async throws -> CRMRoster {
        let url = baseURL.appendingPathComponent("api/v1/dashboard/roster")
        let (data, response) = try await session.data(from: url)
        try validate(response)
        return try parseRoster(data)
    }

    func fetchCommunityMembers() async throws -> [CRMCommunityMember] {
        let url = baseURL.appendingPathComponent("api/v1/community/members")
        let (data, response) = try await session.data(from: url)
        try validate(response)
        return try decoder.decode([CRMCommunityMember].self, from: data)
    }

    func fetchEvents() async throws -> [CRMDetectedEvent] {
        let url = baseURL.appendingPathComponent("api/v1/events")
        let (data, response) = try await session.data(from: url)
        try validate(response)
        return try decoder.decode([CRMDetectedEvent].self, from: data)
    }

    func fetchICPProfile() async throws -> [CRMICPRow] {
        let url = baseURL.appendingPathComponent("api/v1/icp")
        let (data, response) = try await session.data(from: url)
        try validate(response)
        return try decoder.decode([CRMICPRow].self, from: data)
    }

    func sendFollowup(connectionId: String) async throws -> CRMFollowUpDraft {
        var request = URLRequest(url: baseURL.appendingPathComponent("api/v1/connections/\(connectionId)/followup"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = Data("{}".utf8)
        let (data, response) = try await session.data(for: request)
        try validate(response)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
        let subject = json["subject"] as? String ?? "Follow-up"
        let body = json["body"] as? String ?? ""
        return CRMFollowUpDraft(subject: subject, body: body)
    }

    // MARK: - Internals

    private func listConnections() async throws -> [CRMConnection] {
        let url = baseURL.appendingPathComponent("api/v1/connections")
        var request = URLRequest(url: url)
        request.timeoutInterval = 15
        let (data, response) = try await session.data(for: request)
        try validate(response)
        return try decoder.decode([CRMConnection].self, from: data)
    }

    private func validate(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else {
            throw CRMClientError.invalidResponse
        }
        guard (200..<300).contains(http.statusCode) else {
            throw CRMClientError.httpStatus(http.statusCode)
        }
    }

    private func parseDetail(_ data: Data) throws -> CRMConnectionDetail {
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
        if json["error"] != nil {
            throw CRMClientError.notFound
        }

        let connectionData = try JSONSerialization.data(withJSONObject: json["connection"] ?? [:])
        let connection = try decoder.decode(CRMConnection.self, from: connectionData)

        var warmth: CRMWarmthScore?
        if let warmthObject = json["warmth"], !(warmthObject is NSNull) {
            let warmthData = try JSONSerialization.data(withJSONObject: warmthObject)
            warmth = try decoder.decode(CRMWarmthScore.self, from: warmthData)
        }

        var draft: [String: String]?
        if let draftObject = json["gmail_draft"] as? [String: Any] {
            draft = draftObject.compactMapValues { value in
                if let string = value as? String { return string }
                if let number = value as? NSNumber { return number.stringValue }
                return nil
            }
        }

        var meetResult: CRMMeetResult?
        if let meetObject = json["meet_result"], !(meetObject is NSNull) {
            let meetData = try JSONSerialization.data(withJSONObject: meetObject)
            meetResult = try decoder.decode(CRMMeetResult.self, from: meetData)
        }

        return CRMConnectionDetail(connection: connection, warmth: warmth, gmailDraft: draft, meetResult: meetResult)
    }

    private func parseRoster(_ data: Data) throws -> CRMRoster {
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
        var event: CRMDetectedEvent?
        if let eventObject = json["event"], !(eventObject is NSNull) {
            let eventData = try JSONSerialization.data(withJSONObject: eventObject)
            event = try decoder.decode(CRMDetectedEvent.self, from: eventData)
        }
        let attendeesData = try JSONSerialization.data(withJSONObject: json["attendees"] ?? [])
        let attendees = try decoder.decode([CRMConnection].self, from: attendeesData)
        let metRows = (json["met"] as? [[String: Any]] ?? []).compactMap { row -> CRMRosterMetRow? in
            guard let connObject = row["connection"] else { return nil }
            let connData = try? JSONSerialization.data(withJSONObject: connObject)
            guard let connData, let connection = try? decoder.decode(CRMConnection.self, from: connData) else { return nil }
            var meet: CRMMeetResult?
            if let meetObject = row["meet_result"] {
                let meetData = try? JSONSerialization.data(withJSONObject: meetObject)
                if let meetData { meet = try? decoder.decode(CRMMeetResult.self, from: meetData) }
            }
            return CRMRosterMetRow(connection: connection, meetResult: meet)
        }
        return CRMRoster(event: event, attendees: attendees, met: metRows)
    }
}

enum CRMClientError: LocalizedError {
    case invalidResponse
    case httpStatus(Int)
    case notFound

    var errorDescription: String? {
        switch self {
        case .invalidResponse: return "Unexpected server response."
        case .httpStatus(let code): return "Server returned HTTP \(code)."
        case .notFound: return "Connection not found."
        }
    }
}

@MainActor
@Observable
final class MockCRMClient: CRMProviding {
    var baseURL: URL = URL(string: "http://localhost:8000")!
    var connections: [CRMConnection] = CRMConnection.previewList
    var fetchState: CRMFetchState = .loaded

    func updateBaseURL(_ url: URL) { baseURL = url }

    func refreshConnections() async {
        fetchState = .loaded
    }

    func connectionDetail(id: String) async throws -> CRMConnectionDetail {
        guard let connection = connections.first(where: { $0.id == id }) ?? connections.first else {
            throw CRMClientError.notFound
        }
        return CRMConnectionDetail(
            connection: connection,
            warmth: nil,
            gmailDraft: nil,
            meetResult: CRMMeetResult(
                signalId: "mock",
                routedTo: "founder_community",
                narrative: "Strong founder fit — routed to community.",
                recordedAt: ISO8601DateFormatter().string(from: Date()),
                interests: connection.interests,
                matchedCandidates: [CRMMatchCandidate(userId: "u1", name: "Alex Rivera", interests: ["RevOps"])],
                knowledgeGraph: []
            )
        )
    }

    func fetchDashboard() async throws -> CRMDashboardSummary { .preview }

    func fetchRoster() async throws -> CRMRoster {
        CRMRoster(
            event: CRMDetectedEvent(id: "event_demo", name: "GTM Hackathon", startDate: nil, endDate: nil, location: "London"),
            attendees: connections,
            met: connections.prefix(2).map { CRMRosterMetRow(connection: $0, meetResult: nil) }
        )
    }

    func fetchCommunityMembers() async throws -> [CRMCommunityMember] { CRMCommunityMember.previewList }

    func fetchEvents() async throws -> [CRMDetectedEvent] {
        [CRMDetectedEvent(id: "event_demo", name: "GTM Hackathon", startDate: nil, endDate: nil, location: "London")]
    }

    func fetchICPProfile() async throws -> [CRMICPRow] {
        [
            CRMICPRow(label: "Company size", value: "50–500 employees"),
            CRMICPRow(label: "Industries", value: "B2B SaaS, Fintech"),
        ]
    }

    func sendFollowup(connectionId: String) async throws -> CRMFollowUpDraft {
        CRMFollowUpDraft(subject: "Great meeting you", body: "Thanks for the conversation at the event.")
    }
}

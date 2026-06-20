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

        return CRMConnectionDetail(connection: connection, warmth: warmth, gmailDraft: draft)
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
        return CRMConnectionDetail(connection: connection, warmth: nil, gmailDraft: nil)
    }
}

import XCTest
@testable import Warmth

final class CRMConnectionTests: XCTestCase {
    func testDecodesBackendConnectionJSON() throws {
        let json = """
        {
          "id": "premeet_123",
          "event_id": "event_demo_saastr",
          "name": "Maya Chen",
          "title": "VP RevOps",
          "company_name": "NorthWind Labs",
          "interests": ["RevOps", "pipeline"],
          "icp_score": 88.0,
          "predicted_warmth": 81.5,
          "status": "scored",
          "source": "calendar"
        }
        """.data(using: .utf8)!

        let connection = try JSONDecoder().decode(CRMConnection.self, from: json)

        XCTAssertEqual(connection.id, "premeet_123")
        XCTAssertEqual(connection.name, "Maya Chen")
        XCTAssertEqual(connection.org, "NorthWind Labs")
        XCTAssertEqual(connection.icpScore, 88)
        XCTAssertEqual(connection.predictedWarmth, 82)
        XCTAssertEqual(connection.band, .hot)
    }
}

@MainActor
final class WarmthAPIClientTests: XCTestCase {
    func testListConnectionsUsesBackendPath() async throws {
        MockURLProtocol.requestHandler = { request in
            XCTAssertEqual(request.url?.path, "/api/v1/connections")
            let payload = """
            [{"id":"premeet_1","event_id":"e1","name":"Sam","company_name":"Glide","interests":[],"icp_score":70,"predicted_warmth":72}]
            """
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, Data(payload.utf8))
        }

        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [MockURLProtocol.self]
        let session = URLSession(configuration: config)
        let client = WarmthAPIClient(baseURL: URL(string: "https://api.test")!, session: session)

        await client.refreshConnections()

        XCTAssertEqual(client.connections.count, 1)
        XCTAssertEqual(client.connections.first?.name, "Sam")
        XCTAssertEqual(client.fetchState, .loaded)
    }

    func testSendFollowupUsesPostEndpoint() async throws {
        MockURLProtocol.requestHandler = { request in
            XCTAssertEqual(request.httpMethod, "POST")
            XCTAssertTrue(request.url?.path.contains("/followup") == true)
            let payload = #"{"subject":"Hello","body":"Thanks for meeting."}"#
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, Data(payload.utf8))
        }

        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [MockURLProtocol.self]
        let client = WarmthAPIClient(baseURL: URL(string: "https://api.test")!, session: URLSession(configuration: config))
        let draft = try await client.sendFollowup(connectionId: "conn_1")
        XCTAssertEqual(draft.subject, "Hello")
    }
}

private final class MockURLProtocol: URLProtocol {
    nonisolated(unsafe) static var requestHandler: ((URLRequest) throws -> (HTTPURLResponse, Data))?

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        guard let handler = Self.requestHandler else {
            client?.urlProtocol(self, didFailWithError: URLError(.badURL))
            return
        }
        do {
            let (response, data) = try handler(request)
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        } catch {
            client?.urlProtocol(self, didFailWithError: error)
        }
    }

    override func stopLoading() {}
}

import XCTest
@testable import Warmth

@MainActor
final class WarmthAPIClientTests: XCTestCase {
    private var session: URLSession!
    private var client: WarmthAPIClient!
    private let baseURL = URL(string: "https://api.test.warmth")!

    override func setUp() {
        super.setUp()
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [MockURLProtocol.self]
        session = URLSession(configuration: config)
        let auth = MockAuthService.signedInPreview
        client = WarmthAPIClient(baseURL: baseURL, session: session, auth: auth)
        MockURLProtocol.reset()
    }

    override func tearDown() {
        MockURLProtocol.reset()
        session.invalidateAndCancel()
        session = nil
        client = nil
        super.tearDown()
    }

    func testFetchDashboardDecodesSummary() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertTrue(request.url?.path.hasSuffix("/api/v1/dashboard") == true)
            XCTAssertEqual(request.value(forHTTPHeaderField: "Authorization"), "Bearer mock-id-token")
            let body = """
            {"events":2,"connections":5,"hot_leads":1,"leads_in_crm":0,"upcoming_events":[],"top_leads":[]}
            """.data(using: .utf8)!
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, body)
        }

        let summary = try await client.fetchDashboard()
        XCTAssertEqual(summary.events, 2)
        XCTAssertEqual(summary.connections, 5)
    }

    func testFetchRosterDecodesAttendees() async throws {
        MockURLProtocol.handler = { request in
            let body = """
            {"event":null,"attendees":[{"id":"c1","event_id":"e1","name":"Maya","icp_score":80,"predicted_warmth":75,"intent_score":60,"interests":["RevOps"],"status":"scored"}],"met":[],"signals":[]}
            """.data(using: .utf8)!
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, body)
        }

        let roster = try await client.fetchRoster()
        XCTAssertEqual(roster.attendees.count, 1)
        XCTAssertEqual(roster.attendees.first?.name, "Maya")
    }

    func testFetchCommunityMembers() async throws {
        MockURLProtocol.handler = { request in
            let body = #"[{"user_id":"u1","name":"Amir","interests":["GTM"]}]"#.data(using: .utf8)!
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, body)
        }

        let members = try await client.fetchCommunityMembers()
        XCTAssertEqual(members.first?.name, "Amir")
    }

    func testFetchEvents() async throws {
        MockURLProtocol.handler = { request in
            let body = #"[{"id":"e1","name":"Hackathon","event_type":"event","stage":"before_meet"}]"#.data(using: .utf8)!
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, body)
        }

        let events = try await client.fetchEvents()
        XCTAssertEqual(events.first?.name, "Hackathon")
    }

    func testFetchICPProfile() async throws {
        MockURLProtocol.handler = { request in
            let body = #"[{"label":"Keywords","value":"RevOps"}]"#.data(using: .utf8)!
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, body)
        }

        let rows = try await client.fetchICPProfile()
        XCTAssertEqual(rows.first?.label, "Keywords")
    }

    func testConnectionDetail() async throws {
        MockURLProtocol.handler = { request in
            let body = """
            {"connection":{"id":"c1","event_id":"e1","name":"Alex","icp_score":70,"predicted_warmth":65,"intent_score":50,"interests":[],"status":"scored"},"warmth":null,"meet_result":null}
            """.data(using: .utf8)!
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, body)
        }

        let detail = try await client.connectionDetail(id: "c1")
        XCTAssertEqual(detail.connection.name, "Alex")
    }

    func testSendFollowup() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.httpMethod, "POST")
            let body = #"{"subject":"Thanks","body":"Great chat"}"#.data(using: .utf8)!
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, body)
        }

        let draft = try await client.sendFollowup(connectionId: "c1")
        XCTAssertEqual(draft.subject, "Thanks")
    }

    func testBootstrapUserProfile() async throws {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.httpMethod, "POST")
            let body = #"{"uid":"mock-uid-001","email":"demo@warmth.app"}"#.data(using: .utf8)!
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, body)
        }

        try await client.bootstrapUserProfileIfNeeded()
    }

    func testRefreshConnectionsUpdatesState() async {
        MockURLProtocol.handler = { request in
            let body = """
            [{"id":"c1","event_id":"e1","name":"Lead","icp_score":80,"predicted_warmth":90,"intent_score":70,"interests":[],"status":"scored"}]
            """.data(using: .utf8)!
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, body)
        }

        await client.refreshConnections()
        XCTAssertEqual(client.fetchState, .loaded)
        XCTAssertEqual(client.connections.count, 1)
    }
}

import XCTest
@testable import Warmth

@MainActor
final class SignalClientTests: XCTestCase {
    private var session: URLSession!
    private var client: SignalClient!
    private let baseURL = URL(string: "https://api.test.warmth")!

    override func setUp() {
        super.setUp()
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [MockURLProtocol.self]
        session = URLSession(configuration: config)
        client = SignalClient(baseURL: baseURL, session: session)
        MockURLProtocol.reset()
    }

    override func tearDown() {
        MockURLProtocol.reset()
        session.invalidateAndCancel()
        session = nil
        client = nil
        super.tearDown()
    }

    private func sampleSignal() -> CapturedSignal {
        CapturedSignal(
            user: .init(uid: "uid", idToken: "token"),
            sessionId: "session",
            capturedAt: Date(timeIntervalSince1970: 1_700_000_000),
            person: .init(name: "Maya Chen", org: "NorthWind Labs", role: nil),
            relations: [],
            interests: ["RevOps"],
            icpKeywordScore: 72,
            transcriptExcerpt: "Hello",
            device: .current
        )
    }

    func testSuccessfulDeliverySetsDeliveredState() async {
        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.httpMethod, "POST")
            XCTAssertEqual(request.url?.absoluteString, "https://api.test.warmth/api/signals")
            XCTAssertEqual(request.value(forHTTPHeaderField: "Content-Type"), "application/json")
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: 200,
                httpVersion: nil,
                headerFields: nil
            )!
            return (response, Data())
        }

        client.send(sampleSignal())
        try? await Task.sleep(for: .milliseconds(100))

        XCTAssertEqual(client.deliveryState, .delivered)
        XCTAssertEqual(client.queuedCount, 0)
    }

    func testHTTPErrorEnqueuesForRetry() async {
        MockURLProtocol.handler = { request in
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: 503,
                httpVersion: nil,
                headerFields: nil
            )!
            return (response, Data())
        }

        client.send(sampleSignal())
        try? await Task.sleep(for: .milliseconds(100))

        if case .queued(let count) = client.deliveryState {
            XCTAssertEqual(count, 1)
        } else {
            XCTFail("Expected queued state, got \(client.deliveryState)")
        }
        XCTAssertEqual(client.queuedCount, 1)
    }

    func testNetworkErrorEnqueuesForRetry() async {
        MockURLProtocol.handler = { _ in
            throw URLError(.notConnectedToInternet)
        }

        client.send(sampleSignal())
        try? await Task.sleep(for: .milliseconds(100))

        if case .queued(let count) = client.deliveryState {
            XCTAssertEqual(count, 1)
        } else {
            XCTFail("Expected queued state, got \(client.deliveryState)")
        }
    }

    func testFlushQueueRetriesPendingSignals() async {
        var attemptCount = 0
        MockURLProtocol.handler = { request in
            attemptCount += 1
            let status = attemptCount == 1 ? 500 : 200
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: status,
                httpVersion: nil,
                headerFields: nil
            )!
            return (response, Data())
        }

        client.send(sampleSignal())
        try? await Task.sleep(for: .milliseconds(100))
        XCTAssertEqual(client.queuedCount, 1)

        await client.flushQueue()
        try? await Task.sleep(for: .milliseconds(100))

        XCTAssertEqual(client.deliveryState, .delivered)
        XCTAssertEqual(client.queuedCount, 0)
        XCTAssertEqual(attemptCount, 2)
    }

    func testUpdateBaseURLChangesEndpoint() async {
        let newBase = URL(string: "https://new.host.test")!
        client.updateBaseURL(newBase)

        MockURLProtocol.handler = { request in
            XCTAssertEqual(request.url?.host, "new.host.test")
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: 201,
                httpVersion: nil,
                headerFields: nil
            )!
            return (response, Data())
        }

        client.send(sampleSignal())
        try? await Task.sleep(for: .milliseconds(100))

        XCTAssertEqual(client.deliveryState, .delivered)
    }
}

// MARK: - URLProtocol stub

private final class MockURLProtocol: URLProtocol {
    nonisolated(unsafe) static var handler: ((URLRequest) throws -> (HTTPURLResponse, Data))?

    static func reset() {
        handler = nil
    }

    override class func canInit(with request: URLRequest) -> Bool { true }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        guard let handler = Self.handler else {
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

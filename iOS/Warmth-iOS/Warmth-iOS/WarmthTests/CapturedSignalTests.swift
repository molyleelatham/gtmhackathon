import XCTest
@testable import Warmth

final class CapturedSignalTests: XCTestCase {
    private func sampleSignal() -> CapturedSignal {
        CapturedSignal(
            user: .init(uid: "firebase-uid", idToken: "token-123"),
            sessionId: "session-abc",
            capturedAt: Date(timeIntervalSince1970: 1_700_000_000),
            person: .init(name: "Maya Chen", org: "NorthWind Labs", role: nil),
            relations: [.init(subject: "Maya", predicate: "works_at", object: "NorthWind Labs")],
            interests: ["RevOps", "attribution"],
            icpKeywordScore: 72,
            transcriptExcerpt: "It's nice to meet you…",
            device: .current
        )
    }

    func testEncodesSnakeCaseKeys() throws {
        let data = try CapturedSignal.makeEncoder().encode(sampleSignal())
        let json = String(decoding: data, as: UTF8.self)
        XCTAssertTrue(json.contains("\"session_id\""))
        XCTAssertTrue(json.contains("\"captured_at\""))
        XCTAssertTrue(json.contains("\"icp_keyword_score\""))
        XCTAssertTrue(json.contains("\"id_token\""))
        XCTAssertTrue(json.contains("\"transcript_excerpt\""))
    }

    func testEncodesISO8601Date() throws {
        let data = try CapturedSignal.makeEncoder().encode(sampleSignal())
        let json = String(decoding: data, as: UTF8.self)
        // 1_700_000_000 → 2023-11-14T22:13:20Z
        XCTAssertTrue(json.contains("2023-11-14T22:13:20Z"), "Expected ISO8601 captured_at, got: \(json)")
    }

    func testRoundTripDecoding() throws {
        let encoder = CapturedSignal.makeEncoder()
        let data = try encoder.encode(sampleSignal())
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let decoded = try decoder.decode(CapturedSignal.self, from: data)
        XCTAssertEqual(decoded.person.name, "Maya Chen")
        XCTAssertEqual(decoded.icpKeywordScore, 72)
        XCTAssertEqual(decoded.relations.first?.predicate, "works_at")
        XCTAssertEqual(decoded.user.uid, "firebase-uid")
    }

    @MainActor
    func testPersonNodeMakesSignal() {
        let node = PersonNode.preview
        let signal = node.makeSignal(user: .init(uid: "u", idToken: "t"), sessionId: "s")
        XCTAssertEqual(signal.person.name, node.name)
        XCTAssertEqual(signal.icpKeywordScore, node.icpScore)
        XCTAssertEqual(signal.sessionId, "s")
    }
}

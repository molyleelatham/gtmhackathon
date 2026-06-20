import XCTest
@testable import Warmth

final class PersonNodeTests: XCTestCase {
    func testInitialsFromFullName() {
        let node = PersonNode(name: "Maya Chen")
        XCTAssertEqual(node.initials, "MC")
    }

    func testInitialsFromSingleName() {
        let node = PersonNode(name: "Diego")
        XCTAssertEqual(node.initials, "D")
    }

    func testInitialsUsesAtMostTwoWords() {
        let node = PersonNode(name: "Priya Nair Singh")
        XCTAssertEqual(node.initials, "PN")
    }

    func testBandReflectsICPScore() {
        XCTAssertEqual(PersonNode(name: "Hot Lead", icpScore: 85).band, .hot)
        XCTAssertEqual(PersonNode(name: "Warm Lead", icpScore: 55).band, .warm)
        XCTAssertEqual(PersonNode(name: "Cool Lead", icpScore: 15).band, .cool)
    }

    func testWarmthBandBoundaryScores() {
        XCTAssertEqual(WarmthBand(score: 70), .hot)
        XCTAssertEqual(WarmthBand(score: 69), .warm)
        XCTAssertEqual(WarmthBand(score: 40), .warm)
        XCTAssertEqual(WarmthBand(score: 39), .cool)
    }

    func testMakeSignalMapsAllFields() {
        let capturedAt = Date(timeIntervalSince1970: 1_700_000_000)
        let node = PersonNode(
            name: "Aisha Khan",
            org: "Vertex Capital",
            role: "Partner",
            interests: ["SaaS metrics"],
            relations: [.init(subject: "Aisha", predicate: "invests_at", object: "Vertex Capital")],
            icpScore: 91,
            transcriptExcerpt: "Partner at Vertex Capital.",
            capturedAt: capturedAt
        )

        let signal = node.makeSignal(
            user: .init(uid: "uid-1", idToken: "token-abc"),
            sessionId: "session-xyz"
        )

        XCTAssertEqual(signal.person.name, "Aisha Khan")
        XCTAssertEqual(signal.person.org, "Vertex Capital")
        XCTAssertEqual(signal.person.role, "Partner")
        XCTAssertEqual(signal.interests, ["SaaS metrics"])
        XCTAssertEqual(signal.icpKeywordScore, 91)
        XCTAssertEqual(signal.sessionId, "session-xyz")
        XCTAssertEqual(signal.user.uid, "uid-1")
        XCTAssertEqual(signal.capturedAt, capturedAt)
    }
}

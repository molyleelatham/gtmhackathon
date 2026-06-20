import XCTest
@testable import Warmth

@MainActor
final class SessionCaptureLogTests: XCTestCase {
    func testRecordInsertsMostRecentFirst() {
        let log = SessionCaptureLog(sessionId: "sess-1")
        let first = PersonNode(name: "Alice")
        let second = PersonNode(name: "Bob")

        log.record(first)
        log.record(second)

        XCTAssertEqual(log.people.map(\.name), ["Bob", "Alice"])
    }

    func testRecordMergesSameNameCaseInsensitively() {
        let log = SessionCaptureLog()
        let original = PersonNode(
            name: "Maya Chen",
            org: "NorthWind Labs",
            interests: ["RevOps"],
            icpScore: 50,
            transcriptExcerpt: "First mention"
        )
        let update = PersonNode(
            name: "maya chen",
            org: "Helio Robotics",
            role: "VP RevOps",
            interests: ["attribution"],
            relations: [.init(subject: "Maya", predicate: "works_at", object: "Helio Robotics")],
            icpScore: 80,
            transcriptExcerpt: "Second mention"
        )

        log.record(original)
        let merged = log.record(update)

        XCTAssertEqual(log.people.count, 1)
        XCTAssertEqual(merged.name, "Maya Chen")
        XCTAssertEqual(merged.org, "Helio Robotics")
        XCTAssertEqual(merged.role, "VP RevOps")
        XCTAssertEqual(Set(merged.interests), Set(["RevOps", "attribution"]))
        XCTAssertEqual(merged.icpScore, 80)
        XCTAssertEqual(merged.transcriptExcerpt, "Second mention")
        XCTAssertTrue(merged.relations.contains { $0.predicate == "works_at" })
    }

    func testRecordPreservesExistingOrgWhenUpdateHasNone() {
        let log = SessionCaptureLog()
        log.record(PersonNode(name: "Diego Alvarez", org: "Helio Robotics"))
        let merged = log.record(PersonNode(name: "Diego Alvarez", org: nil, interests: ["robotics"]))

        XCTAssertEqual(merged.org, "Helio Robotics")
        XCTAssertEqual(merged.interests, ["robotics"])
    }

    func testUpdateReplacesNodeById() {
        let log = SessionCaptureLog()
        var node = PersonNode(name: "Priya Nair", org: "Lumen Health", icpScore: 40)
        log.record(node)
        node.icpScore = 95
        node.org = "Vertex Capital"

        log.update(node)

        XCTAssertEqual(log.people.first?.id, node.id)
        XCTAssertEqual(log.people.first?.icpScore, 95)
        XCTAssertEqual(log.people.first?.org, "Vertex Capital")
    }

    func testClearRemovesAllPeople() {
        let log = SessionCaptureLog()
        log.record(PersonNode(name: "Tomás Becker"))
        log.clear()
        XCTAssertTrue(log.people.isEmpty)
    }

    func testSessionIdIsStable() {
        let log = SessionCaptureLog(sessionId: "fixed-session")
        XCTAssertEqual(log.sessionId, "fixed-session")
    }
}

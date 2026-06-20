import XCTest
@testable import Warmth

final class SocialGraphEngineExtendedTests: XCTestCase {
    let engine = SocialGraphEngine()

    func testRoleExtractionFindsTitle() {
        let role = engine.role(in: "I'm the VP RevOps at NorthWind Labs.")
        XCTAssertNotNil(role)
        XCTAssertTrue(role?.lowercased().contains("vp") ?? false)
    }

    func testEntitiesExtractsPersonalNames() {
        let names = engine.entities(in: "Hey, I'm Maya Chen and I work at NorthWind Labs.", tag: .personalName)
        XCTAssertFalse(names.isEmpty)
        XCTAssertTrue(names.contains { $0.contains("Maya") })
    }

    func testInterestsAreSortedAndDeduped() {
        let text = "RevOps attribution RevOps pipeline analytics"
        let interests = engine.interests(in: text)
        XCTAssertEqual(interests, interests.sorted())
        XCTAssertEqual(Set(interests).count, interests.count)
    }

    func testCustomICPKeywordsDriveScoring() {
        let custom = SocialGraphEngine(icpKeywords: ["unicorn", "rocket"])
        let score = custom.icpScore(transcript: "We build rocket ships for unicorn founders.", interests: [])
        XCTAssertGreaterThan(score, 0)
    }

    func testProcessIncludesTranscriptExcerpt() {
        let longTranscript = String(repeating: "word ", count: 80)
        let transcript = "Hey, I'm Maya Chen from NorthWind Labs. " + longTranscript
        let node = engine.process(transcript: transcript)
        XCTAssertNotNil(node)
        XCTAssertLessThan(node!.transcriptExcerpt.count, transcript.count)
        XCTAssertTrue(node!.transcriptExcerpt.hasSuffix("…") || node!.transcriptExcerpt.count <= 220)
    }

    func testRelationExtractionInterestedIn() {
        let relations = engine.relations(
            in: "Maya is interested in attribution tooling.",
            names: ["Maya Chen"],
            orgs: []
        )
        XCTAssertTrue(relations.contains { $0.predicate == "interested_in" })
    }
}

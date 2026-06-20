import XCTest
@testable import Warmth

final class SocialGraphEngineTests: XCTestCase {
    let engine = SocialGraphEngine()

    func testEmptyTranscriptYieldsNil() {
        XCTAssertNil(engine.process(transcript: "   "))
    }

    func testExtractsPersonAndOrg() {
        let node = engine.process(
            transcript: "Hey, I'm Maya Chen and I work at NorthWind Labs on RevOps and attribution."
        )
        XCTAssertNotNil(node)
        XCTAssertTrue(node?.name.contains("Maya") ?? false, "Expected the person name to include Maya")
    }

    func testInterestsDetectsICPKeywords() {
        let interests = engine.interests(in: "We focus on RevOps, attribution and pipeline analytics.")
        XCTAssertTrue(interests.contains("RevOps"))
        XCTAssertTrue(interests.contains("attribution"))
        XCTAssertTrue(interests.contains("pipeline"))
    }

    func testICPScoreIncreasesWithKeywordDensity() {
        let low = engine.icpScore(transcript: "Nice weather we are having today.", interests: [])
        let high = engine.icpScore(
            transcript: "RevOps attribution pipeline SaaS metrics growth automation",
            interests: []
        )
        XCTAssertEqual(low, 0)
        XCTAssertGreaterThan(high, low)
        XCTAssertLessThanOrEqual(high, 100)
        XCTAssertGreaterThanOrEqual(high, 0)
    }

    func testICPScoreClampedTo100() {
        let score = engine.icpScore(
            transcript: String(repeating: "revops attribution pipeline gtm saas metrics fundraising investing ", count: 5),
            interests: []
        )
        XCTAssertLessThanOrEqual(score, 100)
    }

    func testRelationExtractionWorksAt() {
        let relations = engine.relations(
            in: "Maya works at NorthWind Labs.",
            names: ["Maya Chen"],
            orgs: ["NorthWind Labs"]
        )
        XCTAssertTrue(relations.contains { $0.predicate == "works_at" })
        XCTAssertEqual(relations.first(where: { $0.predicate == "works_at" })?.subject, "Maya")
    }

    func testRelationExtractionFounded() {
        let relations = engine.relations(
            in: "Diego founded Helio Robotics last year.",
            names: ["Diego Alvarez"],
            orgs: ["Helio Robotics"]
        )
        XCTAssertTrue(relations.contains { $0.predicate == "founded" })
    }

    func testWarmthBandMapping() {
        XCTAssertEqual(WarmthBand(score: 90), .hot)
        XCTAssertEqual(WarmthBand(score: 50), .warm)
        XCTAssertEqual(WarmthBand(score: 10), .cool)
    }
}

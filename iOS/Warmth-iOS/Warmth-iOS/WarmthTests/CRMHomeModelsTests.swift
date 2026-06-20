import XCTest
@testable import Warmth

final class CRMHomeModelsTests: XCTestCase {
    func testDecodesMeetResultWithRouting() throws {
        let json = """
        {
          "signal_id": "sig_1",
          "routed_to": "founder_community",
          "narrative": "Strong founder-community fit.",
          "matched_candidates": [
            {"user_id": "u1", "name": "Alex", "interests": ["RevOps"]}
          ],
          "interests": ["AI", "GTM"],
          "knowledge_graph": []
        }
        """.data(using: .utf8)!

        let meet = try JSONDecoder().decode(CRMMeetResult.self, from: json)
        XCTAssertEqual(meet.routedTo, "founder_community")
        XCTAssertEqual(meet.matchedCandidates.count, 1)
        XCTAssertEqual(meet.matchedCandidates.first?.userId, "u1")
    }

    func testDecodesDashboardSummary() throws {
        let json = """
        {
          "user_id": "demo-user",
          "events": 1,
          "connections": 3,
          "hot_leads": 2,
          "leads_in_crm": 1,
          "top_leads": []
        }
        """.data(using: .utf8)!

        let summary = try JSONDecoder().decode(CRMDashboardSummary.self, from: json)
        XCTAssertEqual(summary.connections, 3)
        XCTAssertEqual(summary.hotLeads, 2)
    }
}

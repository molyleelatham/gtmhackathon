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

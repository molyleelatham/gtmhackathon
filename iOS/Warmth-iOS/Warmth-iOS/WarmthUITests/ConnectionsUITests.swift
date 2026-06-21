import XCTest

final class ConnectionsUITests: XCTestCase {
    override func setUp() {
        continueAfterFailure = false
    }

    func testConnectionsListLoads() {
        let app = XCUIApplication()
        app.launchArguments.append("--uitesting")
        app.launch()

        app.tabBars.buttons["Connections"].tap()
        XCTAssertTrue(app.otherElements["connections_screen"].waitForExistence(timeout: 10))
    }
}

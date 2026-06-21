import XCTest

final class HomeUITests: XCTestCase {
    override func setUp() {
        continueAfterFailure = false
    }

    func testHomeDashboardLoads() {
        let app = XCUIApplication()
        app.launchArguments.append("--uitesting")
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))
        XCTAssertTrue(app.tabBars.buttons["Home"].waitForExistence(timeout: 15))
        XCTAssertTrue(app.otherElements["home_screen"].waitForExistence(timeout: 10))
    }
}

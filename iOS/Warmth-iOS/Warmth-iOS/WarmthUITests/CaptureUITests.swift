import XCTest

final class CaptureUITests: XCTestCase {
    override func setUp() {
        continueAfterFailure = false
    }

    func testCaptureTabShowsRecordOrb() {
        let app = XCUIApplication()
        app.launchArguments.append("--uitesting")
        app.launch()

        app.tabBars.buttons["Capture"].tap()
        XCTAssertTrue(app.otherElements["capture_record_orb"].waitForExistence(timeout: 10))
    }
}

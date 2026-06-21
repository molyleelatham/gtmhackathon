import XCTest

final class OnboardingUITests: XCTestCase {
    override func setUp() {
        continueAfterFailure = false
    }

    func testSignedInUITestUserSkipsOnboarding() {
        let app = XCUIApplication()
        app.launchArguments.append("--uitesting")
        app.launch()

        XCTAssertTrue(app.tabBars.buttons["Home"].waitForExistence(timeout: 15))
        XCTAssertFalse(app.buttons["onboarding_google_sign_in"].exists)
    }
}

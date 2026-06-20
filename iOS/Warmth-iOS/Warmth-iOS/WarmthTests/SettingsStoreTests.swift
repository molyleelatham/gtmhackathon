import XCTest
@testable import Warmth

@MainActor
final class SettingsStoreTests: XCTestCase {
    private var suiteName: String!
    private var defaults: UserDefaults!

    override func setUp() {
        super.setUp()
        suiteName = "WarmthTests.\(UUID().uuidString)"
        defaults = UserDefaults(suiteName: suiteName)!
    }

    override func tearDown() {
        defaults.removePersistentDomain(forName: suiteName)
        defaults = nil
        suiteName = nil
        super.tearDown()
    }

    func testDefaultsWhenKeysMissing() {
        let store = SettingsStore(defaults: defaults)
        XCTAssertEqual(store.baseURLString, SettingsStore.defaultBaseURL)
        XCTAssertFalse(store.didCompleteOnboarding)
        XCTAssertFalse(store.calendarConnected)
    }

    func testLoadsPersistedValues() {
        defaults.set("https://staging.warmth.test", forKey: "warmth.backendBaseURL")
        defaults.set(true, forKey: "warmth.didCompleteOnboarding")
        defaults.set(true, forKey: "warmth.calendarConnected")

        let store = SettingsStore(defaults: defaults)

        XCTAssertEqual(store.baseURLString, "https://staging.warmth.test")
        XCTAssertTrue(store.didCompleteOnboarding)
        XCTAssertTrue(store.calendarConnected)
    }

    func testPersistsChanges() {
        let store = SettingsStore(defaults: defaults)
        store.baseURLString = "https://prod.warmth.test"
        store.didCompleteOnboarding = true
        store.calendarConnected = true

        let reloaded = SettingsStore(defaults: defaults)
        XCTAssertEqual(reloaded.baseURLString, "https://prod.warmth.test")
        XCTAssertTrue(reloaded.didCompleteOnboarding)
        XCTAssertTrue(reloaded.calendarConnected)
    }

    func testBaseURLFallsBackForInvalidString() {
        let store = SettingsStore(defaults: defaults)
        store.baseURLString = "not a valid url :::"
        XCTAssertEqual(store.baseURL.absoluteString, SettingsStore.defaultBaseURL)
    }

    func testBaseURLUsesValidString() throws {
        let store = SettingsStore(defaults: defaults)
        store.baseURLString = "https://api.example.com/v1"
        XCTAssertEqual(store.baseURL.absoluteString, "https://api.example.com/v1")
    }

    func testEventModePersists() {
        let store = SettingsStore(defaults: defaults)
        store.eventModeEnabled = true
        store.eventModeDisabledOverride = true
        let reloaded = SettingsStore(defaults: defaults)
        XCTAssertTrue(reloaded.eventModeEnabled)
        XCTAssertTrue(reloaded.eventModeDisabledOverride)
    }

    func testCalendarMatchToday() {
        let formatter = ISO8601DateFormatter()
        let today = Date()
        let start = formatter.string(from: today)
        let end = formatter.string(from: today)
        let events = [CRMDetectedEvent(id: "e1", name: "Demo", startDate: start, endDate: end, location: nil)]
        XCTAssertTrue(SettingsStore.calendarMatchToday(in: events))
        XCTAssertTrue(SettingsStore(defaults: defaults).isAtEventToday(calendarEvents: events))
    }
}

import SwiftUI

@main
struct WarmthWatchApp: App {
    @WKExtensionDelegate(adaptor: WarmthWatchDelegate.self)
    var delegate
    
    var body: some Scene {
        WindowGroup {
            RecordingStateView()
        }
    }
}
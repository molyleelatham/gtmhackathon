import SwiftUI
import AVFoundation

@main
struct WarmthApp: App {
    @StateObject private var recordingEngine = RecordingEngine.shared
    @StateObject private var watchConnectivityService = WatchConnectivityService.shared
    
    init() {
        setupApp()
    }
    
    var body: some Scene {
        WindowGroup {
            MainTabView()
                .environmentObject(recordingEngine)
                .environmentObject(watchConnectivityService)
                .onAppear {
                    requestPermissions()
                }
        }
        .backgroundTask(.appRefresh("recordingSync")) {
            await syncRecordings()
        }
    }
    
    private func setupApp() {
        _ = AudioSessionManager.shared
        _ = CoreDataManager.shared
    }
    
    private func requestPermissions() {
        AVAudioSession.sharedInstance().requestRecordPermission { granted in
            if granted {
                print("Microphone permission granted")
            } else {
                print("Microphone permission denied")
            }
        }
    }
    
    private func syncRecordings() async {
        await CloudKitSyncService.shared.syncAll()
    }
}
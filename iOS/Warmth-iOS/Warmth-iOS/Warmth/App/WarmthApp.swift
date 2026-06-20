import SwiftUI
import AVFoundation
import Speech

@main
struct WarmthApp: App {
    @Environment(\.scenePhase) private var scenePhase

    @StateObject private var recordingEngine = RecordingEngine.shared
    @StateObject private var watchConnectivityService = WatchConnectivityService.shared
    @StateObject private var phraseTriggerEngine = PhraseTriggerEngine.shared
    
    init() {
        setupApp()
    }
    
    var body: some Scene {
        WindowGroup {
            MainTabView()
                .environmentObject(recordingEngine)
                .environmentObject(watchConnectivityService)
                .environmentObject(phraseTriggerEngine)
                .onAppear {
                    requestPermissions()
                }
                .onChange(of: scenePhase) { _, newPhase in
                    switch newPhase {
                    case .active:
                        phraseTriggerEngine.startListening()
                    case .inactive, .background:
                        phraseTriggerEngine.stopListening()
                    @unknown default:
                        break
                    }
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

        SFSpeechRecognizer.requestAuthorization { status in
            Task { @MainActor in
                switch status {
                case .authorized:
                    print("Speech recognition permission granted")
                    phraseTriggerEngine.startListening()
                case .denied, .restricted:
                    print("Speech recognition permission denied")
                case .notDetermined:
                    break
                @unknown default:
                    break
                }
            }
        }
    }
    
    private func syncRecordings() async {
        await CloudKitSyncService.shared.syncAll()
    }
}
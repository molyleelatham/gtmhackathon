import SwiftUI
import AVFoundation
import Speech

@main
struct WarmthApp: App {
    @Environment(\.scenePhase) private var scenePhase

    @StateObject private var listeningEngine = ConferenceListeningEngine.shared
    @StateObject private var watchConnectivityService = WatchConnectivityService.shared

    var body: some Scene {
        WindowGroup {
            ListeningView()
                .environmentObject(listeningEngine)
                .environmentObject(watchConnectivityService)
                .onAppear { requestPermissions() }
                .onChange(of: scenePhase) { _, newPhase in
                    switch newPhase {
                    case .active:
                        Task { await listeningEngine.start() }
                    case .inactive, .background:
                        listeningEngine.stop()
                    @unknown default:
                        break
                    }
                }
        }
    }

    private func requestPermissions() {
        AVAudioSession.sharedInstance().requestRecordPermission { granted in
            print(granted ? "Microphone permission granted" : "Microphone permission denied")
        }

        SFSpeechRecognizer.requestAuthorization { status in
            Task { @MainActor in
                switch status {
                case .authorized:
                    await listeningEngine.start()
                case .denied, .restricted:
                    print("Speech recognition permission denied")
                default:
                    break
                }
            }
        }
    }
}

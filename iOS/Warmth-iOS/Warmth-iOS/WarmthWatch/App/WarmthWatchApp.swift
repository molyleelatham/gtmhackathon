import SwiftUI

@main
struct WarmthWatchApp: App {
    @State private var connectivity = WatchConnectivityService()

    var body: some Scene {
        WindowGroup {
            RootWatchView(service: connectivity)
        }
    }
}

/// Switches between the branded idle/start screen and the live recording hero,
/// driven entirely by the phone's mirrored capture state.
struct RootWatchView: View {
    let service: WatchConnectivityService

    var body: some View {
        NavigationStack {
            Group {
                if service.isRecording {
                    RecordingStateView(service: service)
                } else {
                    StartView(service: service)
                }
            }
            .animation(.snappy(duration: 0.3), value: service.isRecording)
        }
    }
}

#Preview("Root — idle") {
    RootWatchView(service: .preview(isRecording: false))
}

#Preview("Root — recording") {
    RootWatchView(service: .preview(isRecording: true, elapsed: 64, name: "Dev Patel", org: "Linear"))
}

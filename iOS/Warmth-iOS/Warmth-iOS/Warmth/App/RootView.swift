import SwiftUI

/// Root shell: shows onboarding until complete, then the Liquid Glass tab bar
/// (Capture · Connections · Settings).
struct RootView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        Group {
            if model.isOnboarded && model.auth.state.isSignedIn {
                MainTabView()
            } else {
                OnboardingFlow()
            }
        }
        .animation(WarmthMotion.gentle, value: model.isOnboarded)
        .animation(WarmthMotion.gentle, value: model.auth.state)
        .task { await model.auth.restore() }
    }
}

/// The three-tab Liquid Glass shell.
struct MainTabView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        @Bindable var model = model
        TabView(selection: $model.selectedTab) {
            Tab("Capture", systemImage: "waveform", value: WarmthTab.capture) {
                CaptureView()
            }
            Tab("Connections", systemImage: "person.2.fill", value: WarmthTab.connections) {
                ConnectionsView()
            }
            Tab("Settings", systemImage: "gearshape.fill", value: WarmthTab.settings) {
                SettingsView()
            }
        }
        .tint(WarmthColor.emberRed)
        .onChange(of: model.speech.phase) { _, _ in
            model.syncWatchState()
        }
    }
}

#Preview {
    RootView()
        .environment({
            let m = AppModel.preview
            m.settings.didCompleteOnboarding = true
            return m
        }())
}

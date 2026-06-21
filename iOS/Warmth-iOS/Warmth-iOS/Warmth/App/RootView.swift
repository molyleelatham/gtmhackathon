import SwiftUI

/// Root shell: shows onboarding until complete, then the Liquid Glass tab bar
/// (Home · Capture · Connections · Settings).
struct RootView: View {
    @Environment(AppModel.self) private var model
    @State private var authReady = false

    var body: some View {
        Group {
            if !authReady {
                ZStack {
                    MeshGradientBackground()
                    ProgressView()
                        .tint(WarmthColor.emberRed)
                }
            } else if model.isOnboarded && model.authState.isSignedIn {
                MainTabView()
            } else if model.isOnboarded {
                ReturningSignInView()
            } else {
                OnboardingFlow()
            }
        }
        .animation(WarmthMotion.gentle, value: model.isOnboarded)
        .animation(WarmthMotion.gentle, value: model.authState)
        .task {
            await model.restoreAuth()
            authReady = true
            if model.authState.isSignedIn {
                await model.refreshHome()
            }
        }
    }
}

/// Four-tab Liquid Glass shell.
struct MainTabView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        @Bindable var model = model
        TabView(selection: $model.selectedTab) {
            Tab("Home", systemImage: "house.fill", value: WarmthTab.home) {
                HomeView()
            }
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
        .onChange(of: model.selectedTab) { _, tab in
            if tab == .connections {
                Task { await model.refreshConnections() }
            }
            if tab == .home {
                Task { await model.refreshHome() }
            }
        }
        .onChange(of: model.speech.phase) { _, _ in
            model.syncWatchState()
        }
        .onChange(of: Int(model.speech.elapsed)) { _, _ in
            if model.speech.phase == .recording { model.syncWatchState() }
        }
    }
}

private struct ReturningSignInView: View {
    var body: some View {
        ZStack {
            MeshGradientBackground(intensity: 1.05)
            SignInStepView(advance: {})
                .frame(maxWidth: 480)
                .padding(.horizontal, 28)
                .padding(.vertical, 24)
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

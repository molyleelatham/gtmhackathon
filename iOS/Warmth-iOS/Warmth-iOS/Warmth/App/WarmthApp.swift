import SwiftUI
import FirebaseCore
import GoogleSignIn

@main
struct WarmthApp: App {
    @State private var model: AppModel

    init() {
        FirebaseApp.configure()
        let settings = SettingsStore()
        let appModel = AppModel(
            auth: FirebaseAuthService(),
            speech: SpeechService(),
            signalClient: SignalClient(baseURL: settings.baseURL),
            socialGraph: SocialGraphEngine(),
            settings: settings
        )
        _model = State(initialValue: appModel)
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(model)
                .tint(WarmthColor.emberRed)
                .onOpenURL { url in
                    GIDSignIn.sharedInstance.handle(url)
                }
        }
    }
}

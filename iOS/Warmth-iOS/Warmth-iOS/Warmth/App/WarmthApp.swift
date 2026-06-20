import SwiftUI
import FirebaseCore
import GoogleSignIn

@main
struct WarmthApp: App {
    @State private var model: AppModel

    init() {
        FirebaseApp.configure()
        let auth = FirebaseAuthService()
        let settings = SettingsStore()
        let signalClient = SignalClient(baseURL: settings.baseURL, auth: auth)
        let crmClient = WarmthAPIClient(baseURL: settings.baseURL, auth: auth)
        let appModel = AppModel(
            auth: auth,
            speech: SpeechService(),
            signalClient: signalClient,
            crmClient: crmClient,
            socialGraph: SocialGraphEngine(),
            settings: settings
        )
        _model = State(initialValue: appModel)
        AppModelRegistry.register(appModel)
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

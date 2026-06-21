import SwiftUI
import FirebaseCore
import GoogleSignIn

@main
struct WarmthApp: App {
    @State private var model: AppModel

    init() {
        let isUITesting = ProcessInfo.processInfo.arguments.contains("--uitesting")

        if !isUITesting {
            FirebaseApp.configure()
        }

        let auth: any AuthProviding = isUITesting
            ? MockAuthService.signedInPreview
            : FirebaseAuthService()
        let settings = SettingsStore()
        if isUITesting {
            settings.didCompleteOnboarding = true
        }

        let speech: any SpeechServicing = isUITesting ? MockSpeechService() : SpeechService()
        let signalClient = SignalClient(baseURL: settings.baseURL, auth: auth)
        let crmClient: any CRMProviding = isUITesting ? MockCRMClient() : WarmthAPIClient(baseURL: settings.baseURL, auth: auth)

        let appModel = AppModel(
            auth: auth,
            speech: speech,
            signalClient: signalClient,
            crmClient: crmClient,
            socialGraph: isUITesting ? MockSocialGraph() : SocialGraphEngine(),
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

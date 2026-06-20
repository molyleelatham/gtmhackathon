import SwiftUI

/// Branded idle screen: a calm ember mark and one large primary action that
/// starts capture on the phone from the wrist.
struct StartView: View {
    let service: WatchConnectivityService

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                PulsingEmberIndicator(isActive: false, diameter: 48)
                    .frame(height: 64)
                    .padding(.top, 8)

                VStack(spacing: 2) {
                    Text("Warmth")
                        .font(.WatchType.hero)
                        .foregroundStyle(WatchTheme.warmWhite)
                    Text("Capture every connection")
                        .font(.WatchType.caption)
                        .foregroundStyle(WatchTheme.textSecondary)
                        .multilineTextAlignment(.center)
                }

                Button(action: { service.requestStart() }) {
                    Label("Start capturing", systemImage: "waveform")
                        .font(.WatchType.label)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .tint(WatchTheme.emberRed)
                .controlSize(.large)

                if !service.isPhoneReachable {
                    PhoneUnreachableHint()
                }
            }
            .padding(.horizontal, 4)
            .padding(.bottom, 8)
        }
        .containerBackground(WatchTheme.canvas, for: .navigation)
        .navigationTitle("Warmth")
        .navigationBarTitleDisplayMode(.inline)
    }
}

/// Subtle, non-blocking hint shown when the phone isn't currently reachable.
/// The intent is still queued via application context, so this is informational.
struct PhoneUnreachableHint: View {
    var body: some View {
        Label("Phone not reachable", systemImage: "iphone.slash")
            .font(.WatchType.caption)
            .foregroundStyle(WatchTheme.textSecondary)
            .padding(.top, 2)
    }
}

#Preview("Idle — reachable") {
    NavigationStack {
        StartView(service: .preview(isRecording: false, reachable: true))
    }
}

#Preview("Idle — phone asleep") {
    NavigationStack {
        StartView(service: .preview(isRecording: false, reachable: false))
    }
}

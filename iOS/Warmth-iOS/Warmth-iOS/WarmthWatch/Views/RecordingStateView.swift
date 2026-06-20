import SwiftUI

/// The live capture hero shown while the phone is recording: pulsing ember orb,
/// a self-updating elapsed timer, the last detected person/org, and a big Stop.
struct RecordingStateView: View {
    let service: WatchConnectivityService

    var body: some View {
        ScrollView {
            VStack(spacing: 14) {
                PulsingEmberIndicator(isActive: true, diameter: 56)
                    .frame(height: 72)
                    .padding(.top, 4)

                timer

                lastPerson

                stopButton
            }
            .padding(.horizontal, 4)
            .padding(.bottom, 8)
        }
        .containerBackground(WatchTheme.canvas, for: .navigation)
        .navigationTitle("Warmth")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var timer: some View {
        VStack(spacing: 2) {
            if let start = service.recordingStartedAt {
                Text(start, style: .timer)
                    .font(.WatchType.timer)
                    .monospacedDigit()
                    .foregroundStyle(WatchTheme.warmWhite)
            } else {
                Text("00:00")
                    .font(.WatchType.timer)
                    .foregroundStyle(WatchTheme.warmWhite)
            }
            Label("Capturing", systemImage: "dot.radiowaves.left.and.right")
                .font(.WatchType.caption)
                .foregroundStyle(WatchTheme.amber)
                .labelStyle(.titleAndIcon)
        }
    }

    @ViewBuilder
    private var lastPerson: some View {
        if let name = service.lastPersonName, !name.isEmpty {
            VStack(spacing: 2) {
                Text(name)
                    .font(.WatchType.title)
                    .foregroundStyle(WatchTheme.warmWhite)
                    .lineLimit(1)
                if let org = service.lastPersonOrg, !org.isEmpty {
                    Text(org)
                        .font(.WatchType.body)
                        .foregroundStyle(WatchTheme.textSecondary)
                        .lineLimit(1)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(WatchTheme.warmWhite.opacity(0.08))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .strokeBorder(WatchTheme.emberOrange.opacity(0.35), lineWidth: 1)
            )
        } else {
            Text("Listening for names…")
                .font(.WatchType.caption)
                .foregroundStyle(WatchTheme.textSecondary)
                .padding(.vertical, 6)
        }
    }

    private var stopButton: some View {
        VStack(spacing: 6) {
            Button(action: { service.requestStop() }) {
                Label("Stop", systemImage: "stop.fill")
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
    }
}

#Preview("Recording — with person") {
    NavigationStack {
        RecordingStateView(
            service: .preview(isRecording: true, elapsed: 128, name: "Maya Chen", org: "Sequoia")
        )
    }
}

#Preview("Recording — no person yet") {
    NavigationStack {
        RecordingStateView(service: .preview(isRecording: true, elapsed: 12))
    }
}

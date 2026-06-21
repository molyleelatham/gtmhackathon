import SwiftUI

/// The hero of the Capture screen: a large ember-gradient orb wrapped in a warm
/// radial glow. Its inner content + motion reflect the current `CapturePhase`:
///
/// - `.idle`      — gently breathes, shows a mic glyph + "Tap to record".
/// - `.recording` — morphs into a live `WaveformView` driven by `audioLevel`.
struct RecordOrb: View {
    let phase: CapturePhase
    var audioLevel: Double = 0
    let onTap: () -> Void

    private let diameter: CGFloat = 240

    @State private var breathing = false

    var body: some View {
        ZStack {
            WarmthColor.emberGlow
                .frame(width: diameter * 1.7, height: diameter * 1.7)
                .scaleEffect(phase == .recording ? 1.15 : 1)
                .opacity(phase == .idle ? 0.7 : 1)
                .blur(radius: 8)

            Circle()
                .fill(WarmthColor.emberGradient)
                .frame(width: diameter, height: diameter)
                .overlay(
                    Circle().strokeBorder(WarmthColor.warmWhite.opacity(0.35), lineWidth: 1)
                )
                .overlay { orbContent }
                .warmthGlass(WarmthGlassStyle.interactive, in: Circle(), fillSurface: false)
                .shadow(color: WarmthColor.emberRed.opacity(0.35), radius: 30, y: 12)
                .scaleEffect(orbScale)
                .animation(WarmthMotion.breathe, value: breathing)
                .animation(WarmthMotion.bouncy, value: phase)
        }
        .frame(width: diameter * 1.7, height: diameter * 1.7)
        .contentShape(.circle)
        .onTapGesture(perform: onTap)
        .onAppear { breathing = true }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(accessibilityLabel)
        .accessibilityIdentifier("capture_record_orb")
        .accessibilityAddTraits(.isButton)
    }

    @ViewBuilder
    private var orbContent: some View {
        switch phase {
        case .idle:
            VStack(spacing: 12) {
                Image(systemName: "mic.fill")
                    .font(.system(size: 52, weight: .semibold))
                    .foregroundStyle(WarmthColor.warmWhite)
                Text("Tap to\nrecord")
                    .multilineTextAlignment(.center)
                    .font(.Warmth.headline)
                    .foregroundStyle(WarmthColor.warmWhite)
            }
        case .recording:
            WaveformView(level: audioLevel)
                .frame(width: diameter * 0.62, height: diameter * 0.42)
                .transition(.scale.combined(with: .opacity))
        }
    }

    private var orbScale: CGFloat {
        switch phase {
        case .idle:
            return breathing ? 1.04 : 0.96
        case .recording:
            return 1.0 + CGFloat(max(0, min(1, audioLevel))) * 0.06
        }
    }

    private var accessibilityLabel: String {
        switch phase {
        case .idle: return "Record orb. Tap to start recording."
        case .recording: return "Recording in progress. Tap to stop."
        }
    }
}

#Preview("Idle") {
    ZStack {
        MeshGradientBackground()
        RecordOrb(phase: .idle) {}
    }
}

#Preview("Recording") {
    ZStack {
        MeshGradientBackground(intensity: 1.4)
        RecordOrb(phase: .recording, audioLevel: 0.6) {}
    }
}

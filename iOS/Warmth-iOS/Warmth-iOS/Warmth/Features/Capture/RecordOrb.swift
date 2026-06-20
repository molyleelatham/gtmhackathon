import SwiftUI

/// The hero of the Capture screen: a large ember-gradient orb wrapped in a warm
/// radial glow. Its inner content + motion reflect the current `CapturePhase`:
///
/// - `.idle`      — gently breathes, shows a mic glyph + "Tap to start listening".
/// - `.listening` — emits pulsing rings while it waits for the wake word.
/// - `.recording` — morphs into a live `WaveformView` driven by `audioLevel`.
struct RecordOrb: View {
    let phase: CapturePhase
    var audioLevel: Double = 0
    let onTap: () -> Void

    private let diameter: CGFloat = 240

    @State private var breathing = false
    @State private var pulse = false

    var body: some View {
        ZStack {
            // Ambient glow that intensifies while recording.
            WarmthColor.emberGlow
                .frame(width: diameter * 1.7, height: diameter * 1.7)
                .scaleEffect(phase == .recording ? 1.15 : 1)
                .opacity(phase == .idle ? 0.7 : 1)
                .blur(radius: 8)

            // Listening pulse rings.
            if phase == .listening {
                ForEach(0..<2, id: \.self) { ring in
                    Circle()
                        .strokeBorder(WarmthColor.emberOrange.opacity(0.5), lineWidth: 2)
                        .frame(width: diameter, height: diameter)
                        .scaleEffect(pulse ? 1.35 : 1)
                        .opacity(pulse ? 0 : 0.8)
                        .animation(
                            .easeOut(duration: 1.8)
                                .repeatForever(autoreverses: false)
                                .delay(Double(ring) * 0.9),
                            value: pulse
                        )
                }
            }

            // The orb itself.
            Circle()
                .fill(WarmthColor.emberGradient)
                .frame(width: diameter, height: diameter)
                .overlay(
                    Circle().strokeBorder(WarmthColor.warmWhite.opacity(0.35), lineWidth: 1)
                )
                .overlay { orbContent }
                .glassEffect(.regular.interactive(), in: .circle)
                .shadow(color: WarmthColor.emberRed.opacity(0.35), radius: 30, y: 12)
                .scaleEffect(orbScale)
                .animation(WarmthMotion.breathe, value: breathing)
                .animation(WarmthMotion.bouncy, value: phase)
        }
        .frame(width: diameter * 1.7, height: diameter * 1.7)
        .contentShape(.circle)
        .onTapGesture(perform: onTap)
        .onAppear {
            breathing = true
            pulse = true
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(accessibilityLabel)
        .accessibilityAddTraits(.isButton)
    }

    // MARK: - Inner content

    @ViewBuilder
    private var orbContent: some View {
        switch phase {
        case .idle:
            VStack(spacing: 12) {
                Image(systemName: "mic.fill")
                    .font(.system(size: 52, weight: .semibold))
                    .foregroundStyle(WarmthColor.warmWhite)
                Text("Tap to start\nlistening")
                    .multilineTextAlignment(.center)
                    .font(.Warmth.headline)
                    .foregroundStyle(WarmthColor.warmWhite)
            }
        case .listening:
            VStack(spacing: 12) {
                Image(systemName: "ear.fill")
                    .font(.system(size: 46, weight: .semibold))
                    .foregroundStyle(WarmthColor.warmWhite)
                Text("Listening")
                    .font(.Warmth.title2)
                    .foregroundStyle(WarmthColor.warmWhite)
            }
        case .recording:
            WaveformView(level: audioLevel)
                .frame(width: diameter * 0.62, height: diameter * 0.42)
                .transition(.scale.combined(with: .opacity))
        }
    }

    // MARK: - Motion

    private var orbScale: CGFloat {
        switch phase {
        case .idle:
            return breathing ? 1.04 : 0.96
        case .listening:
            return 1.0
        case .recording:
            // Subtle live "thump" with the audio level.
            return 1.0 + CGFloat(max(0, min(1, audioLevel))) * 0.06
        }
    }

    private var accessibilityLabel: String {
        switch phase {
        case .idle: return "Record orb. Tap to start listening."
        case .listening: return "Listening for the wake word. Tap to start recording."
        case .recording: return "Recording in progress."
        }
    }
}

#Preview("Idle") {
    ZStack {
        MeshGradientBackground()
        RecordOrb(phase: .idle) {}
    }
}

#Preview("Listening") {
    ZStack {
        MeshGradientBackground()
        RecordOrb(phase: .listening) {}
    }
}

#Preview("Recording") {
    ZStack {
        MeshGradientBackground(intensity: 1.4)
        RecordOrb(phase: .recording, audioLevel: 0.6) {}
    }
}

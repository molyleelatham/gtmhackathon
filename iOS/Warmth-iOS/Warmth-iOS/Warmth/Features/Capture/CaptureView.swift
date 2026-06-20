import SwiftUI

/// The hero Capture screen. A breathing ember orb anchors the experience: tap to
/// listen for the wake word, then record a conversation. While recording, the orb
/// becomes a live waveform, the backdrop heats up, a live transcript streams into a
/// glass card, and a prominent Stop control commits the captured person.
struct CaptureView: View {
    @Environment(AppModel.self) private var model
    @State private var isStartingCapture = false

    var body: some View {
        let phase = model.speech.phase

        ZStack {
            MeshGradientBackground(intensity: phase == .recording ? 1.6 : 1.0)
                .animation(WarmthMotion.gentle, value: phase)

            VStack(spacing: 0) {
                header

                if let error = model.speech.permissionError {
                    permissionBanner(error)
                }

                Spacer(minLength: 8)

                // Timer + hero orb.
                VStack(spacing: 18) {
                    if phase == .recording {
                        Text(formattedElapsed)
                            .font(.Warmth.largeTitle)
                            .monospacedDigit()
                            .foregroundStyle(WarmthColor.ink)
                            .transition(.scale.combined(with: .opacity))
                    }

                    RecordOrb(phase: phase, audioLevel: model.speech.audioLevel) {
                        handleOrbTap()
                    }

                    caption
                }

                Spacer(minLength: 8)

                // Phase-specific controls / transcript.
                Group {
                    switch phase {
                    case .idle:
                        EmptyView()
                    case .listening:
                        listeningControls
                    case .recording:
                        recordingControls
                    }
                }
                .padding(.horizontal, 20)

                Spacer(minLength: 16)

                RecentConnectionsStrip(people: model.sessionLog.people)
                    .padding(.bottom, 8)
            }
            .padding(.top, 8)
            .animation(WarmthMotion.snappy, value: phase)
        }
        .task {
            // Light extra flourish; the service already fires its own haptic.
            model.speech.onWakeWordDetected = { WarmthHaptics.success() }
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: 2) {
            Text("Warmth")
                .font(.Warmth.title)
                .foregroundStyle(WarmthColor.ink)
            Text("Capture every connection")
                .font(.Warmth.footnote)
                .foregroundStyle(WarmthColor.inkSecondary)
        }
        .padding(.top, 4)
    }

    private func permissionBanner(_ message: String) -> some View {
        HStack(spacing: 10) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(WarmthColor.emberRed)
            Text(message)
                .font(.Warmth.footnote)
                .foregroundStyle(WarmthColor.ink)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .warmthGlass(WarmthGlassStyle.card, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .padding(.horizontal, 20)
        .padding(.top, 10)
        .transition(.move(edge: .top).combined(with: .opacity))
    }

    // MARK: - Caption under the orb

    @ViewBuilder
    private var caption: some View {
        switch model.speech.phase {
        case .idle:
            Text("Tap the orb to begin")
                .font(.Warmth.callout)
                .foregroundStyle(WarmthColor.inkSecondary)
        case .listening:
            VStack(spacing: 4) {
                Text("Listening for")
                    .font(.Warmth.callout)
                    .foregroundStyle(WarmthColor.inkSecondary)
                Text("\u{201C}\(WakeWord.phrase)\u{201D}")
                    .font(.Warmth.headline)
                    .foregroundStyle(WarmthColor.emberRed)
                    .multilineTextAlignment(.center)
            }
        case .recording:
            Text("Recording — speak naturally")
                .font(.Warmth.callout)
                .foregroundStyle(WarmthColor.inkSecondary)
        }
    }

    // MARK: - Listening controls

    private var listeningControls: some View {
        VStack(spacing: 12) {
            EmberButton(title: "Start recording now", systemImage: "record.circle") {
                _ = beginCaptureIfAllowed { await model.speech.startRecording() }
            }
            EmberButton(title: "Cancel", fill: false) {
                model.speech.stopAndReset()
                model.syncWatchState()
            }
        }
    }

    // MARK: - Recording controls

    private var recordingControls: some View {
        VStack(spacing: 16) {
            transcriptCard

            Button(action: handleStop) {
                HStack(spacing: 10) {
                    Image(systemName: "stop.fill")
                    Text("Stop & save")
                }
                .font(.Warmth.title2)
                .foregroundStyle(WarmthColor.warmWhite)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 20)
                .background(Capsule().fill(WarmthColor.emberGradient))
                .warmthGlass(WarmthGlassStyle.interactive, in: Capsule(), fillSurface: false)
                .shadow(color: WarmthColor.emberRed.opacity(0.4), radius: 16, y: 8)
            }
            .buttonStyle(.plain)
        }
    }

    private var transcriptCard: some View {
        GlassCard {
            ScrollViewReader { proxy in
                ScrollView {
                    let transcript = model.speech.transcript
                    Text(transcript.isEmpty ? "Listening…" : transcript)
                        .font(.Warmth.body)
                        .foregroundStyle(transcript.isEmpty ? WarmthColor.inkSecondary : WarmthColor.ink)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .id("transcriptEnd")
                }
                .frame(height: 120)
                .onChange(of: model.speech.transcript) {
                    withAnimation(WarmthMotion.gentle) {
                        proxy.scrollTo("transcriptEnd", anchor: .bottom)
                    }
                }
            }
        }
    }

    // MARK: - Interaction

    private func handleOrbTap() {
        guard !isStartingCapture else { return }

        switch model.speech.phase {
        case .idle:
            _ = beginCaptureIfAllowed { await model.speech.startListening() }
        case .listening:
            _ = beginCaptureIfAllowed { await model.speech.startRecording() }
        case .recording:
            handleStop()
        }
    }

    /// Returns false when capture must not proceed (denied permissions or in-flight start).
    @discardableResult
    private func beginCaptureIfAllowed(start: @escaping () async -> Void) -> Bool {
        if model.speech.permissionsDenied {
            _ = model.speech.checkPermissions()
            WarmthHaptics.warning()
            return false
        }
        isStartingCapture = true
        Task {
            defer { isStartingCapture = false }
            guard await model.speech.requestPermissions() else { return }
            guard model.speech.hasMicrophoneAccess else { return }
            await start()
            model.syncWatchState()
        }
        return true
    }

    private func handleStop() {
        let transcript = model.speech.transcript.trimmingCharacters(in: .whitespacesAndNewlines)
        model.speech.stopAndReset()
        model.syncWatchState()
        WarmthHaptics.success()
        if !transcript.isEmpty {
            Task { await model.capturePerson(from: transcript) }
        }
    }

    // MARK: - Formatting

    private var formattedElapsed: String {
        let total = Int(model.speech.elapsed)
        let minutes = total / 60
        let seconds = total % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }
}

#Preview {
    CaptureView()
        .environment(AppModel.preview)
}

#Preview("Recording") {
    CaptureView()
        .environment({
            let m = AppModel.preview
            Task { await m.speech.startRecording() }
            return m
        }())
}

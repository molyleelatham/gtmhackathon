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

                RecentConnectionsStrip(connections: model.crmClient.connections)
                    .padding(.bottom, 8)
            }
            .padding(.top, 8)
            .animation(WarmthMotion.snappy, value: phase)

            if let match = model.attendeeMatch, match.matched {
                AttendeeConnectedOverlay(match: match) {
                    model.dismissAttendeeMatch()
                }
                .transition(.scale.combined(with: .opacity))
            }
        }
        .task {
            // Light extra flourish; the service already fires its own haptic.
            model.speech.onWakeWordDetected = {
                WarmthHaptics.success()
                model.prepareNewCapture()
            }
        }
        .onChange(of: model.speech.transcript) { _, transcript in
            // Fire during passive listening too, so "hi {name}" pops the match card
            // without requiring the wake phrase first (mirrors the web dashboard).
            let phase = model.speech.phase
            guard phase == .listening || phase == .recording, !transcript.isEmpty else { return }
            Task { await model.tryMatchAttendee(from: transcript) }
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
            passiveTranscriptHint
            EmberButton(title: "Start recording now", systemImage: "record.circle") {
                _ = beginCaptureIfAllowed { await model.speech.startRecording() }
            }
            EmberButton(title: "Cancel", fill: false) {
                model.speech.stopAndReset()
                model.syncWatchState()
            }
        }
    }

    /// Compact live transcript shown while passively listening — surfaces that we're
    /// hearing the room and matching greetings, mirroring the web "Live transcript" card.
    private var passiveTranscriptHint: some View {
        let transcript = model.speech.transcript.trimmingCharacters(in: .whitespacesAndNewlines)
        return GlassCard {
            VStack(alignment: .leading, spacing: 4) {
                Text("Live transcript")
                    .font(.Warmth.caption)
                    .foregroundStyle(WarmthColor.inkSecondary)
                    .textCase(.uppercase)
                Text(transcript.isEmpty ? "Listening… try \u{201C}Hi Molly\u{201D}" : transcript)
                    .font(.Warmth.footnote)
                    .foregroundStyle(transcript.isEmpty ? WarmthColor.inkSecondary : WarmthColor.ink)
                    .lineLimit(2)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .animation(WarmthMotion.gentle, value: transcript)
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
            model.prepareNewCapture()
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
        Task { @MainActor in
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

// MARK: - Attendee connected overlay

/// Glass modal shown when a live "hi {name}" matches someone on the event roster.
struct AttendeeConnectedOverlay: View {
    let match: AttendeeMatchResult
    let onDismiss: () -> Void

    private var displayName: String {
        match.connection?.name ?? match.name ?? "Attendee"
    }

    var body: some View {
        ZStack {
            Color.black.opacity(0.38)
                .ignoresSafeArea()
                .onTapGesture(perform: onDismiss)

            VStack(spacing: 16) {
                HStack(alignment: .top, spacing: 14) {
                    AvatarBadge(initials: initials(for: displayName), size: 64, glow: true)
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Attendee matched")
                            .font(.Warmth.caption)
                            .foregroundStyle(WarmthColor.emberRed)
                            .textCase(.uppercase)
                        Text(match.message)
                            .font(.Warmth.title2)
                            .foregroundStyle(WarmthColor.ink)
                            .fixedSize(horizontal: false, vertical: true)
                        if let title = match.connection?.title, let company = match.connection?.companyName {
                            Text("\(title) · \(company)")
                                .font(.Warmth.footnote)
                                .foregroundStyle(WarmthColor.inkSecondary)
                        }
                        if let score = match.score {
                            Text("Match confidence \(Int(score * 100))%")
                                .font(.Warmth.caption)
                                .foregroundStyle(WarmthColor.inkSecondary)
                        }
                    }
                    Spacer(minLength: 0)
                    Button(action: onDismiss) {
                        Image(systemName: "xmark")
                            .font(.Warmth.footnote.weight(.semibold))
                            .foregroundStyle(WarmthColor.inkSecondary)
                    }
                    .buttonStyle(.plain)
                }

                if let interests = match.interests, !interests.isEmpty {
                    KnowledgeGraphMiniView(
                        personName: displayName,
                        interests: interests,
                        topicWeights: match.knowledgeGraph?.first?.topicWeights,
                        values: match.knowledgeGraph?.first?.values ?? []
                    )
                    .frame(height: 220)

                    WarmthFlowLayout(spacing: 8, lineSpacing: 8) {
                        ForEach(interests, id: \.self) { interest in
                            InterestChip(text: interest, tint: WarmthColor.emberRed)
                        }
                    }
                }

                Button(action: onDismiss) {
                    Text("Keep capturing")
                        .font(.Warmth.headline)
                        .foregroundStyle(WarmthColor.warmWhite)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                        .background(Capsule().fill(WarmthColor.emberGradient))
                }
                .buttonStyle(.plain)
            }
            .padding(22)
            .warmthGlass(WarmthGlassStyle.card, in: RoundedRectangle(cornerRadius: 28, style: .continuous))
            .padding(.horizontal, 24)
        }
    }

    private func initials(for name: String) -> String {
        name.split(separator: " ").prefix(2).compactMap(\.first).map(String.init).joined()
    }
}

/// Radial interest graph — person at center, topics/interests on the ring.
struct KnowledgeGraphMiniView: View {
    let personName: String
    var interests: [String] = []
    var topicWeights: [String: Double]?
    var values: [String] = []

    private struct OrbitNode: Identifiable {
        let id: String
        let label: String
        let kind: Kind
        enum Kind { case topic, interest, value }
    }

    private var nodes: [OrbitNode] {
        var out: [OrbitNode] = []
        if let topicWeights {
            for (label, _) in topicWeights.sorted(by: { $0.value > $1.value }).prefix(6) {
                out.append(.init(id: "t-\(label)", label: label, kind: .topic))
            }
        }
        for label in interests.prefix(8) where !out.contains(where: { $0.label.lowercased() == label.lowercased() }) {
            out.append(.init(id: "i-\(label)", label: label, kind: .interest))
        }
        for label in values.prefix(4) {
            out.append(.init(id: "v-\(label)", label: label, kind: .value))
        }
        return out
    }

    var body: some View {
        GeometryReader { geo in
            let layout = OrbitLayout(size: geo.size, nodes: nodes)
            ZStack {
                ForEach(layout.placements) { placement in
                    OrbitNodeView(placement: placement, layout: layout)
                }

                Circle()
                    .fill(WarmthColor.emberRed.opacity(0.18))
                    .frame(width: 56, height: 56)
                    .position(layout.center)
                Text(personName.split(separator: " ").first.map(String.init) ?? personName)
                    .font(.Warmth.caption.weight(.bold))
                    .foregroundStyle(WarmthColor.ink)
                    .position(layout.center)
            }
        }
    }

    private struct OrbitLayout {
        let center: CGPoint
        let radius: CGFloat
        let placements: [OrbitPlacement]

        init(size: CGSize, nodes: [OrbitNode]) {
            let side = min(size.width, size.height)
            let centerPoint = CGPoint(x: size.width / 2, y: size.height / 2)
            let orbitRadius = side * 0.34
            let computed = nodes.enumerated().map { index, node in
                let angle = (Double(index) / Double(max(nodes.count, 1))) * (.pi * 2) - .pi / 2
                let point = CGPoint(
                    x: centerPoint.x + CGFloat(cos(angle)) * orbitRadius,
                    y: centerPoint.y + CGFloat(sin(angle)) * orbitRadius
                )
                return OrbitPlacement(node: node, point: point)
            }
            center = centerPoint
            radius = orbitRadius
            placements = computed
        }
    }

    private struct OrbitPlacement: Identifiable {
        let node: OrbitNode
        let point: CGPoint
        var id: String { node.id }
    }

    private struct OrbitNodeView: View {
        let placement: OrbitPlacement
        let layout: OrbitLayout

        var body: some View {
            let node = placement.node
            let point = placement.point
            ZStack {
                Path { path in
                    path.move(to: layout.center)
                    path.addLine(to: point)
                }
                .stroke(nodeColor(node.kind).opacity(0.45), lineWidth: 1.5)

                Circle()
                    .fill(nodeColor(node.kind))
                    .frame(width: node.kind == .topic ? 16 : 12, height: node.kind == .topic ? 16 : 12)
                    .position(point)

                Text(shortLabel(node.label))
                    .font(.Warmth.caption)
                    .foregroundStyle(WarmthColor.inkSecondary)
                    .position(x: point.x, y: point.y + 16)
            }
        }

        private func nodeColor(_ kind: OrbitNode.Kind) -> Color {
            switch kind {
            case .topic: WarmthColor.emberRed.opacity(0.85)
            case .interest: WarmthColor.amber.opacity(0.85)
            case .value: WarmthColor.emberRed.opacity(0.55)
            }
        }

        private func shortLabel(_ label: String) -> String {
            label.count > 14 ? String(label.prefix(13)) + "…" : label
        }
    }
}

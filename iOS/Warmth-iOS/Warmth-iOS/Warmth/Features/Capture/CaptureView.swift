import SwiftUI

/// The hero Capture screen. Tap the ember orb to record; optional passive floor
/// listening runs when enabled in Settings.
struct CaptureView: View {
    @Environment(AppModel.self) private var model
    @Environment(\.scenePhase) private var scenePhase
    @State private var isStartingCapture = false

    var body: some View {
        let phase = model.speech.phase

        ZStack {
            MeshGradientBackground(intensity: phase == .recording ? 1.6 : 1.0)
                .animation(WarmthMotion.gentle, value: phase)

            VStack(spacing: 0) {
                header

                if model.isPassiveFloorListeningActive {
                    passiveFloorBanner
                }

                if let error = model.speech.permissionError {
                    permissionBanner(error)
                }

                Spacer(minLength: 8)

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

                if phase == .recording {
                    recordingControls
                        .padding(.horizontal, 20)
                }

                Spacer(minLength: 16)
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
        .onChange(of: scenePhase) { _, phase in
            Task { await model.handleScenePhase(phase) }
        }
        .task {
            MatchNotifier.shared.requestAuthorization()
            model.speech.onWakeWordDetected = {
                WarmthHaptics.success()
                model.prepareNewCapture()
            }
            await model.handleScenePhase(scenePhase)
        }
        .onChange(of: model.speech.transcript) { _, transcript in
            guard model.speech.phase == .recording, !transcript.isEmpty else { return }
            Task { await model.tryMatchAttendee(from: transcript) }
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: 2) {
            Text("Warmth")
                .font(.Warmth.title)
                .foregroundStyle(WarmthColor.ink)
            if let name = model.pendingCapturePersonName, model.speech.phase == .recording {
                Text("Meeting \(name)")
                    .font(.Warmth.footnote)
                    .foregroundStyle(WarmthColor.emberRed)
            } else {
                Text("Capture every connection")
                    .font(.Warmth.footnote)
                    .foregroundStyle(WarmthColor.inkSecondary)
            }
        }
        .padding(.top, 4)
    }

    private var passiveFloorBanner: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 6) {
                Label("Floor listening", systemImage: "ear")
                    .font(.Warmth.caption.weight(.semibold))
                    .foregroundStyle(WarmthColor.emberOrange)
                Text("Say a contact name — Warmth opens a 30s capture window.")
                    .font(.Warmth.footnote)
                    .foregroundStyle(WarmthColor.inkSecondary)
                let transcript = model.passiveFloorTranscript.trimmingCharacters(in: .whitespacesAndNewlines)
                if !transcript.isEmpty {
                    Text(transcript)
                        .font(.Warmth.footnote)
                        .foregroundStyle(WarmthColor.ink)
                        .lineLimit(2)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.horizontal, 20)
        .padding(.top, 8)
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

    @ViewBuilder
    private var caption: some View {
        switch model.speech.phase {
        case .idle:
            if model.settings.capturePreferences.isEnabled(.manual) {
                Text("Tap the orb to record")
                    .font(.Warmth.callout)
                    .foregroundStyle(WarmthColor.inkSecondary)
            } else {
                Text("Use Siri, your watch, or Action Button to start")
                    .font(.Warmth.callout)
                    .foregroundStyle(WarmthColor.inkSecondary)
                    .multilineTextAlignment(.center)
            }
        case .recording:
            Text("Recording — speak naturally")
                .font(.Warmth.callout)
                .foregroundStyle(WarmthColor.inkSecondary)
        }
    }

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

    private func handleOrbTap() {
        guard model.settings.capturePreferences.isEnabled(.manual) else {
            WarmthHaptics.warning()
            return
        }
        guard !isStartingCapture else { return }

        switch model.speech.phase {
        case .idle:
            model.prepareNewCapture()
            isStartingCapture = true
            Task { @MainActor in
                defer { isStartingCapture = false }
                await model.startManualCapture()
            }
        case .recording:
            Task { await model.stopManualCapture() }
            WarmthHaptics.success()
        }
    }

    private func handleStop() {
        Task {
            await model.stopManualCapture()
            WarmthHaptics.success()
        }
    }

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

import SwiftUI

/// Settings tab: scrollable Liquid Glass cards over the ambient mesh gradient.
struct SettingsView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        NavigationStack {
            ZStack {
                MeshGradientBackground()

                ScrollView {
                    VStack(spacing: 18) {
                        AccountSection()
                        EventModeSection()
                        BackendSection()
                        ICPProfileSection()
                        CaptureMethodsSection()
                        PermissionsSection()
                        CalendarSection()
                        SettingsFooter()
                            .padding(.top, 4)
                    }
                    .padding(.horizontal, 18)
                    .padding(.top, 8)
                    .padding(.bottom, 32)
                }
                .scrollIndicators(.hidden)
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.large)
        }
        .tint(WarmthColor.emberRed)
    }
}

// MARK: - Section scaffolding

/// Small ember-tinted header used at the top of each settings card.
private struct SectionHeader: View {
    let title: String
    let systemImage: String

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: systemImage)
                .font(.system(size: 14, weight: .semibold))
                .foregroundStyle(WarmthColor.warmWhite)
                .frame(width: 30, height: 30)
                .background(WarmthColor.emberGradient, in: .rect(cornerRadius: 9, style: .continuous))
            Text(title)
                .warmthText(.Warmth.subheadline, color: WarmthColor.inkSecondary)
                .textCase(.uppercase)
                .kerning(0.6)
            Spacer(minLength: 0)
        }
    }
}

// MARK: - 1. Account

private struct AccountSection: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 16) {
                SectionHeader(title: "Account", systemImage: "person.fill")

                if let user = model.auth.state.user {
                    HStack(spacing: 14) {
                        AvatarView(user: user)
                        VStack(alignment: .leading, spacing: 3) {
                            Text(user.displayName ?? "Warmth member")
                                .warmthText(.Warmth.title2)
                            if let email = user.email {
                                Text(email)
                                    .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                            }
                        }
                        Spacer(minLength: 0)
                    }

                    EmberButton(title: "Sign out", systemImage: "rectangle.portrait.and.arrow.right", fill: false) {
                        WarmthHaptics.selection()
                        model.auth.signOut()
                    }
                } else {
                    Text("You're not signed in.")
                        .warmthText(.Warmth.body, color: WarmthColor.inkSecondary)
                }
            }
        }
    }
}

/// Circular avatar with an initials fallback when no photo (or it fails to load).
private struct AvatarView: View {
    let user: WarmthUser

    private var initials: String {
        let source = user.displayName?.isEmpty == false ? user.displayName! : (user.email ?? "?")
        let parts = source
            .split(whereSeparator: { $0 == " " || $0 == "@" || $0 == "." })
            .prefix(2)
        let letters = parts.compactMap { $0.first }.map { String($0).uppercased() }
        return letters.isEmpty ? "?" : letters.joined()
    }

    private var fallback: some View {
        ZStack {
            Circle().fill(WarmthColor.emberGradient)
            Text(initials)
                .font(.Warmth.headline)
                .foregroundStyle(WarmthColor.warmWhite)
        }
    }

    var body: some View {
        Group {
            if let url = user.photoURL {
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .success(let image):
                        image.resizable().scaledToFill()
                    case .failure:
                        fallback
                    case .empty:
                        ZStack { fallback.opacity(0.5); ProgressView().tint(WarmthColor.warmWhite) }
                    @unknown default:
                        fallback
                    }
                }
            } else {
                fallback
            }
        }
        .frame(width: 54, height: 54)
        .clipShape(Circle())
        .overlay(Circle().strokeBorder(WarmthColor.warmWhite.opacity(0.5), lineWidth: 0.5))
        .shadow(color: WarmthColor.emberOrange.opacity(0.3), radius: 8)
    }
}

// MARK: - 2. Event mode

private struct EventModeSection: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        @Bindable var settings = model.settings

        GlassCard {
            VStack(alignment: .leading, spacing: 14) {
                SectionHeader(title: "Event mode", systemImage: "calendar.badge.clock")

                Toggle(isOn: $settings.eventModeEnabled) {
                    Text("I'm at an event")
                        .warmthText(.Warmth.body)
                }
                .tint(WarmthColor.emberRed)
                .onChange(of: settings.eventModeEnabled) { _, enabled in
                    if enabled {
                        WarmthHaptics.success()
                        model.selectedTab = .capture
                    }
                }

                Toggle(isOn: $settings.eventModeDisabledOverride) {
                    Text("Stay on Home even during calendar events")
                        .warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)
                }
                .tint(WarmthColor.emberRed)

                Text("Warmth checks your calendar and opens Capture when an event is active today. Enable floor listening below for contact-name detection at events.")
                    .warmthText(.Warmth.caption, color: WarmthColor.inkSecondary)
            }
        }
    }
}

// MARK: - 3. Backend

private struct BackendSection: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        @Bindable var settings = model.settings

        GlassCard {
            VStack(alignment: .leading, spacing: 14) {
                SectionHeader(title: "Backend", systemImage: "server.rack")

                Text("Where captured signals are uploaded. Defaults to the hosted Warmth API (same as the web dashboard).")
                    .warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)

                TextField("Base URL", text: $settings.baseURLString)
                    .font(.Warmth.mono)
                    .foregroundStyle(WarmthColor.ink)
                    .keyboardType(.URL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled(true)
                    .submitLabel(.done)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 12)
                    .background(WarmthColor.surfaceMuted, in: .rect(cornerRadius: 12, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .strokeBorder(WarmthColor.surfaceBorder.opacity(0.8), lineWidth: 0.5)
                    )
                    .onSubmit { applyURL() }
                    .onChange(of: settings.baseURLString) { _, _ in applyURL() }

                DeliveryStatusLine(state: model.signalClient.deliveryState)

                Button {
                    WarmthHaptics.selection()
                    settings.baseURLString = SettingsStore.defaultBaseURL
                    applyURL()
                } label: {
                    Label("Reset to default", systemImage: "arrow.counterclockwise")
                        .font(.Warmth.footnote)
                        .foregroundStyle(WarmthColor.emberRed)
                }
                .buttonStyle(.plain)
            }
        }
    }

    private func applyURL() {
        model.applyBackendURL(model.settings.baseURL)
    }
}

/// Maps `SignalDeliveryState` onto friendly text + an ember-aware color.
private struct DeliveryStatusLine: View {
    let state: SignalDeliveryState

    private var text: String {
        switch state {
        case .idle: return "Idle — nothing sent yet"
        case .sending: return "Sending…"
        case .delivered: return "Delivered"
        case .queued(let count): return "Queued — \(count) waiting to retry"
        case .failed(let message): return "Failed — \(message)"
        }
    }

    private var tint: Color {
        switch state {
        case .idle: return WarmthColor.inkSecondary
        case .sending: return WarmthColor.amber
        case .delivered: return WarmthColor.emberOrange
        case .queued: return WarmthColor.amber
        case .failed: return WarmthColor.emberRed
        }
    }

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(tint)
                .frame(width: 8, height: 8)
                .shadow(color: tint.opacity(0.7), radius: 4)
            Text(text)
                .warmthText(.Warmth.footnote, color: WarmthColor.ink)
                .lineLimit(2)
            Spacer(minLength: 0)
        }
        .padding(.vertical, 4)
    }
}

// MARK: - 4. ICP profile

private struct ICPProfileSection: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeader(title: "ICP profile", systemImage: "target")

                if model.icpProfile.isEmpty {
                    Text("Read-only ICP criteria from the backend.")
                        .warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)
                    EmberButton(title: "Load ICP", systemImage: "arrow.clockwise", fill: false) {
                        Task { await model.refreshICPProfile() }
                    }
                } else {
                    ForEach(model.icpProfile) { row in
                        HStack(alignment: .top) {
                            Text(row.label)
                                .warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)
                                .frame(width: 110, alignment: .leading)
                            Text(row.value)
                                .warmthText(.Warmth.body)
                            Spacer(minLength: 0)
                        }
                    }
                }
            }
        }
        .task { await model.refreshICPProfile() }
    }
}

// MARK: - Capture methods

private struct CaptureMethodsSection: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        @Bindable var settings = model.settings

        GlassCard {
            VStack(alignment: .leading, spacing: 14) {
                SectionHeader(title: "Capture methods", systemImage: "hand.tap.fill")

                CaptureMethodsPicker(
                    preferences: $settings.capturePreferences,
                    showsSetupHints: true
                )
            }
        }
    }
}

// MARK: - Permissions

private struct PermissionsSection: View {
    @Environment(AppModel.self) private var model

    @State private var granted = false
    @State private var checked = false
    @State private var checking = false

    private var statusText: String {
        if checking { return "Checking…" }
        if !checked { return "Not checked yet" }
        if granted { return "Granted" }
        return model.speech.permissionError ?? "Denied — enable mic & speech in Settings"
    }

    private var statusTint: Color {
        if checking { return WarmthColor.amber }
        if !checked { return WarmthColor.inkSecondary }
        return granted ? WarmthColor.emberOrange : WarmthColor.emberRed
    }

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 14) {
                SectionHeader(title: "Permissions", systemImage: "mic.fill")

                HStack(spacing: 8) {
                    Image(systemName: "mic")
                    Text("Microphone & Speech")
                        .warmthText(.Warmth.body)
                    Spacer(minLength: 0)
                    HStack(spacing: 6) {
                        Circle()
                            .fill(statusTint)
                            .frame(width: 8, height: 8)
                            .shadow(color: statusTint.opacity(0.7), radius: 4)
                        Text(statusText)
                            .warmthText(.Warmth.footnote, color: WarmthColor.ink)
                            .lineLimit(2)
                            .multilineTextAlignment(.trailing)
                    }
                }
                .foregroundStyle(WarmthColor.ink)

                EmberButton(title: "Check permissions", systemImage: "checkmark.shield", fill: false) {
                    checking = true
                    granted = model.speech.checkPermissions()
                    checked = true
                    checking = false
                    if granted { WarmthHaptics.success() } else { WarmthHaptics.warning() }
                }
            }
        }
    }
}

// MARK: - 5. Calendar

private struct CalendarSection: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        @Bindable var settings = model.settings

        GlassCard {
            VStack(alignment: .leading, spacing: 14) {
                SectionHeader(title: "Calendar", systemImage: "calendar")

                if settings.calendarConnected {
                    HStack(spacing: 8) {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundStyle(WarmthColor.emberOrange)
                        Text("Connected")
                            .warmthText(.Warmth.body)
                        Spacer(minLength: 0)
                    }

                    Button {
                        WarmthHaptics.selection()
                        settings.calendarConnected = false
                    } label: {
                        Label("Disconnect", systemImage: "minus.circle")
                            .font(.Warmth.footnote)
                            .foregroundStyle(WarmthColor.emberRed)
                    }
                    .buttonStyle(.plain)
                } else {
                    Text("Link your calendar to enrich connections with meeting context.")
                        .warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)

                    EmberButton(title: "Connect Calendar", systemImage: "calendar.badge.plus", fill: false) {
                        WarmthHaptics.success()
                        settings.calendarConnected = true
                    }
                }

                Text("Calendar integration is a stub for now.")
                    .warmthText(.Warmth.caption, color: WarmthColor.inkSecondary)
            }
        }
    }
}

// MARK: - 6. Footer

private struct SettingsFooter: View {
    private var versionText: String {
        let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
        let build = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"
        return "Version \(version) (\(build))"
    }

    var body: some View {
        VStack(spacing: 6) {
            Text("Warmth")
                .font(.Warmth.title)
                .foregroundStyle(WarmthColor.ink)
                .overlay(WarmthColor.emberGradient.mask(
                    Text("Warmth").font(.Warmth.title)
                ))
            Text("Never forget a conversation.")
                .warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)
            Text(versionText)
                .warmthText(.Warmth.caption, color: WarmthColor.inkSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12)
    }
}

#Preview {
    SettingsView()
        .environment(AppModel.preview)
}

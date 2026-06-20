import SwiftUI

/// Step 4 — optional calendar enrichment. The "Connect" action is a stub that just
/// flips `settings.calendarConnected`; the step is fully skippable.
struct CalendarStepView: View {
    @Environment(AppModel.self) private var model
    let advance: () -> Void

    var body: some View {
        @Bindable var settings = model.settings

        VStack(spacing: 24) {
            VStack(spacing: 12) {
                Image(systemName: "calendar.badge.clock")
                    .font(.system(size: 44, weight: .semibold))
                    .foregroundStyle(WarmthColor.emberGradient)

                Text("Connect Calendar")
                    .warmthText(.Warmth.largeTitle)

                Text("Optional — let Warmth match faces to your meetings so every connection comes with context.")
                    .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                    .multilineTextAlignment(.center)
            }

            GlassCard {
                VStack(alignment: .leading, spacing: 14) {
                    enrichmentRow(icon: "person.text.rectangle",
                                  title: "Who you met",
                                  detail: "Attendee names from your events")
                    enrichmentRow(icon: "mappin.and.ellipse",
                                  title: "Where & when",
                                  detail: "Location and timing for each intro")
                    enrichmentRow(icon: "sparkles",
                                  title: "Smarter recall",
                                  detail: "Richer context on every connection")
                }
            }

            VStack(spacing: 12) {
                EmberButton(
                    title: settings.calendarConnected ? "Connected" : "Connect Calendar",
                    systemImage: settings.calendarConnected ? "checkmark" : "calendar"
                ) {
                    settings.calendarConnected = true
                    WarmthHaptics.success()
                    advance()
                }

                Button {
                    advance()
                } label: {
                    Text("Skip for now")
                        .warmthText(.Warmth.subheadline, color: WarmthColor.inkSecondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                }
                .buttonStyle(.plain)
            }
        }
    }

    private func enrichmentRow(icon: String, title: String, detail: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.Warmth.headline)
                .foregroundStyle(WarmthColor.emberOrange)
                .frame(width: 26)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).warmthText(.Warmth.subheadline)
                Text(detail).warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)
            }
            Spacer(minLength: 0)
        }
    }
}

#Preview {
    ZStack {
        MeshGradientBackground()
        CalendarStepView(advance: {})
            .padding()
    }
    .environment(AppModel.preview)
}

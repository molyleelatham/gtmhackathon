import SwiftUI
import WidgetKit

/// Routes each supported complication family to a tailored layout.
struct WarmthComplicationView: View {
    @Environment(\.widgetFamily) private var family
    let entry: WarmthComplicationEntry

    var body: some View {
        switch family {
        case .accessoryCircular: CircularView(state: entry.state)
        case .accessoryCorner: CornerView(state: entry.state)
        case .accessoryInline: InlineView(state: entry.state)
        case .accessoryRectangular: RectangularView(state: entry.state)
        default: CircularView(state: entry.state)
        }
    }
}

// MARK: - Families

private struct CircularView: View {
    let state: WatchSharedState
    var body: some View {
        ZStack {
            AccessoryWidgetBackground()
            if state.isRecording {
                VStack(spacing: 1) {
                    Image(systemName: "waveform")
                        .font(.system(size: 12, weight: .bold))
                    if let start = state.recordingStartedAt {
                        Text(start, style: .timer)
                            .font(.system(size: 9, weight: .semibold, design: .rounded))
                            .monospacedDigit()
                            .lineLimit(1)
                            .minimumScaleFactor(0.6)
                    }
                }
                .foregroundStyle(WidgetEmber.red)
            } else {
                Image(systemName: "flame.fill")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundStyle(WidgetEmber.red)
            }
        }
        .widgetLabel("Warmth")
    }
}

private struct CornerView: View {
    let state: WatchSharedState
    var body: some View {
        Image(systemName: state.isRecording ? "waveform" : "flame.fill")
            .font(.system(size: 18, weight: .bold))
            .foregroundStyle(WidgetEmber.red)
            .widgetLabel {
                if state.isRecording, let start = state.recordingStartedAt {
                    Text(start, style: .timer)
                } else {
                    Text("Warmth")
                }
            }
    }
}

private struct InlineView: View {
    let state: WatchSharedState
    var body: some View {
        if state.isRecording, let start = state.recordingStartedAt {
            Label {
                Text("Capturing ") + Text(start, style: .timer)
            } icon: {
                Image(systemName: "waveform")
            }
        } else {
            Label("Warmth — tap to capture", systemImage: "flame.fill")
        }
    }
}

private struct RectangularView: View {
    let state: WatchSharedState
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: state.isRecording ? "waveform" : "flame.fill")
                .font(.system(size: 20, weight: .bold))
                .foregroundStyle(WidgetEmber.red)
            VStack(alignment: .leading, spacing: 1) {
                if state.isRecording {
                    if let start = state.recordingStartedAt {
                        Text(start, style: .timer)
                            .font(.system(size: 17, weight: .bold, design: .rounded))
                            .monospacedDigit()
                    } else {
                        Text("Capturing").font(.system(size: 15, weight: .bold))
                    }
                    Text(personLine)
                        .font(.system(size: 12))
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                } else {
                    Text("Warmth").font(.system(size: 15, weight: .bold))
                    Text("Tap to start capturing")
                        .font(.system(size: 12))
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }
            Spacer(minLength: 0)
        }
        .containerBackground(.clear, for: .widget)
    }

    private var personLine: String {
        switch (state.lastPersonName, state.lastPersonOrg) {
        case let (name?, org?) where !name.isEmpty && !org.isEmpty: return "\(name) · \(org)"
        case let (name?, _) where !name.isEmpty: return name
        default: return "Listening…"
        }
    }
}

/// Tinted ember for the (otherwise monochrome-rendered) accessory widgets.
enum WidgetEmber {
    static let red = Color(red: 1.0, green: 0x2D / 255, blue: 0x1A / 255)
}

#Preview("Rectangular — recording", as: .accessoryRectangular) {
    WarmthWatchWidget()
} timeline: {
    WarmthComplicationEntry(date: .now, state: .sample)
}

#Preview("Circular — idle", as: .accessoryCircular) {
    WarmthWatchWidget()
} timeline: {
    WarmthComplicationEntry(date: .now, state: .idle)
}

#Preview("Inline — recording", as: .accessoryInline) {
    WarmthWatchWidget()
} timeline: {
    WarmthComplicationEntry(date: .now, state: .sample)
}

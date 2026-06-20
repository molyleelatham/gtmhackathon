import SwiftUI
import WidgetKit

/// Warmth quick-launch + live-status complication.
///
/// Tapping any family opens the watch app (default complication tap behavior).
/// While the phone is capturing it shows a recording glyph + elapsed timer;
/// otherwise it shows idle ember branding.
struct WarmthWatchWidget: Widget {
    let kind = "WarmthWatchWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: WarmthComplicationProvider()) { entry in
            WarmthComplicationView(entry: entry)
        }
        .configurationDisplayName("Warmth")
        .description("Start capture and see live recording status from your wrist.")
        .supportedFamilies([
            .accessoryCircular,
            .accessoryCorner,
            .accessoryInline,
            .accessoryRectangular
        ])
    }
}

@main
struct WarmthWatchWidgetBundle: WidgetBundle {
    var body: some Widget {
        WarmthWatchWidget()
    }
}

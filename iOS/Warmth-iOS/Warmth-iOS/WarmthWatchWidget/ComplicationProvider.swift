import WidgetKit

/// A single timeline entry carrying the latest mirrored capture state.
struct WarmthComplicationEntry: TimelineEntry {
    let date: Date
    let state: WatchSharedState
}

/// Feeds the complication from the App Group snapshot the watch app writes.
///
/// We rely on `WidgetCenter.reloadAllTimelines()` (called by the watch app when
/// recording state changes) rather than scheduled refreshes, so a single entry
/// with a `.never` policy is sufficient. The elapsed time renders via a
/// self-updating `Text(_, style: .timer)`, so it ticks without new entries.
struct WarmthComplicationProvider: TimelineProvider {
    func placeholder(in context: Context) -> WarmthComplicationEntry {
        WarmthComplicationEntry(date: Date(), state: .sample)
    }

    func getSnapshot(in context: Context,
                     completion: @escaping (WarmthComplicationEntry) -> Void) {
        let state = context.isPreview ? .sample : WatchSharedStore.load()
        completion(WarmthComplicationEntry(date: Date(), state: state))
    }

    func getTimeline(in context: Context,
                     completion: @escaping (Timeline<WarmthComplicationEntry>) -> Void) {
        let entry = WarmthComplicationEntry(date: Date(), state: WatchSharedStore.load())
        completion(Timeline(entries: [entry], policy: .never))
    }
}

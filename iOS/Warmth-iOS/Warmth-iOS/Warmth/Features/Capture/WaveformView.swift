import SwiftUI

/// Live audio waveform rendered as a row of ember bars whose heights are driven by
/// the speech service's normalized `audioLevel`. Each bar gets a slightly different
/// phase so the wave reads as organic rather than a flat block.
struct WaveformView: View {
    /// Normalized 0...1 microphone level.
    var level: Double
    var barCount: Int = 5
    var spacing: CGFloat = 7

    var body: some View {
        TimelineView(.animation) { timeline in
            let t = timeline.date.timeIntervalSinceReferenceDate
            GeometryReader { geo in
                let width = (geo.size.width - spacing * CGFloat(barCount - 1)) / CGFloat(barCount)
                HStack(alignment: .center, spacing: spacing) {
                    ForEach(0..<barCount, id: \.self) { index in
                        Capsule(style: .continuous)
                            .fill(WarmthColor.warmWhite)
                            .frame(
                                width: width,
                                height: barHeight(for: index, time: t, maxHeight: geo.size.height)
                            )
                    }
                }
                .frame(width: geo.size.width, height: geo.size.height, alignment: .center)
            }
        }
    }

    /// Compute a bar height blending the live level with a per-bar travelling sine
    /// so the middle bars tend to swing wider than the edges.
    private func barHeight(for index: Int, time: TimeInterval, maxHeight: CGFloat) -> CGFloat {
        let clamped = max(0, min(1, level))
        let phase = Double(index) * 0.7
        let wobble = (sin(time * 6 + phase) + 1) / 2          // 0...1
        // Edge bars are damped so the shape feels rounded.
        let centerBias = 1 - abs(Double(index) - Double(barCount - 1) / 2) / Double(barCount)
        let amplitude = (0.25 + 0.75 * clamped) * (0.55 + 0.45 * wobble) * (0.6 + 0.4 * centerBias)
        let minHeight = maxHeight * 0.14
        return minHeight + (maxHeight - minHeight) * CGFloat(amplitude)
    }
}

#Preview {
    ZStack {
        Circle().fill(WarmthColor.emberGradient).frame(width: 220, height: 220)
        WaveformView(level: 0.7)
            .frame(width: 120, height: 90)
    }
}

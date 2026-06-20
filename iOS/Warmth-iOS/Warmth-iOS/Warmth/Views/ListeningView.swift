import SwiftUI

/// Root view: shows the passive-listening state, the live capture transcript,
/// and the most recent qualified lead.
struct ListeningView: View {
    @EnvironmentObject private var engine: ConferenceListeningEngine

    var body: some View {
        VStack(spacing: 24) {
            statusHeader

            if !engine.liveTranscript.isEmpty {
                ScrollView {
                    Text(engine.liveTranscript)
                        .font(.body)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(maxHeight: 160)
                .padding()
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }

            if let signal = engine.lastSignal {
                leadCard(signal)
            }

            Spacer()
            controlButton
        }
        .padding()
        .task { await engine.start() }
    }

    private var statusHeader: some View {
        VStack(spacing: 8) {
            Image(systemName: iconName)
                .font(.system(size: 44))
                .foregroundStyle(iconColor)
            Text(statusText)
                .font(.headline)
        }
        .padding(.top, 40)
    }

    private func leadCard(_ signal: Signal) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Lead detected")
                .font(.caption).foregroundStyle(.secondary)
            Text(signal.person.name)
                .font(.title2).bold()
            if let company = signal.company?.name {
                Text(company).foregroundStyle(.secondary)
            }
            HStack {
                Text("ICP score")
                Spacer()
                Text("\(Int(signal.score))")
                    .bold()
                    .foregroundStyle(signal.isPreScoreHint ? .green : .orange)
            }
            .font(.subheadline)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var controlButton: some View {
        Button {
            switch engine.state {
            case .idle: Task { await engine.start() }
            default: engine.stop()
            }
        } label: {
            Text(engine.state == .idle ? "Start Listening" : "Stop")
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.borderedProminent)
        .tint(engine.state == .idle ? .blue : .red)
    }

    private var iconName: String {
        switch engine.state {
        case .idle: return "mic.slash"
        case .listening: return "ear"
        case .capturing: return "waveform"
        }
    }

    private var iconColor: Color {
        switch engine.state {
        case .idle: return .gray
        case .listening: return .blue
        case .capturing: return .green
        }
    }

    private var statusText: String {
        switch engine.state {
        case .idle: return "Idle"
        case .listening: return "Listening for names…"
        case .capturing(let name): return "Capturing \(name ?? "conversation")…"
        }
    }
}

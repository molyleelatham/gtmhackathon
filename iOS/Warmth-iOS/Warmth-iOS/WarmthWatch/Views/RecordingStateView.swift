import SwiftUI

struct RecordingStateView: View {
    @StateObject private var wcService = WatchConnectivityService.shared
    
    var body: some View {
        VStack(spacing: 20) {
            if wcService.isRecording {
                PulsingDot()
                    .frame(width: 60, height: 60)
                
                Text("Recording Active")
                    .font(.headline)
                
                Button("Stop") {
                    wcService.toggleRecording()
                }
                .buttonStyle(.borderedProminent)
            } else {
                Image(systemName: "mic.slash")
                    .font(.system(size: 40))
                    .foregroundColor(.gray)
                
                Text("Not Recording")
                    .font(.headline)
                    .foregroundColor(.gray)
            }
        }
        .padding()
    }
}

struct PulsingDot: View {
    @State private var isPulsing = false
    
    var body: some View {
        Circle()
            .fill(Color.red)
            .frame(width: 20, height: 20)
            .scaleEffect(isPulsing ? 1.5 : 1.0)
            .opacity(isPulsing ? 0.5 : 1.0)
            .onAppear {
                withAnimation(.easeInOut(duration: 0.8).repeatForever()) {
                    isPulsing.toggle()
                }
            }
    }
}
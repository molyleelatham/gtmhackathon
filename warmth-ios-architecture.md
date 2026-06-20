# Warmth — iOS Personal CRM Recording App

> **iOS/watchOS Native Conference Intelligence**
> Personal CRM · iOS 17+ · watchOS 10+ · SwiftUI · Porcupine · WatchConnectivity

---

## Vision Overview

Warmth is a native iOS personal CRM recording app that uses always-listening wake word detection on iPhone to seamlessly record conference conversations. The Apple Watch serves as a remote control via complications, with minimal UI for recording state management. All processing happens on-device with optional cloud sync for CRM integration.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  iOS APP (iPhone)                                                  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Wake Word Engine (Porcupine iOS)                            │  │
│  │ - Offline wake word detection ("Hey Anna")                   │  │
│  │ - Continuous background listening                            │  │
│  │ - Low battery consumption                                    │  │
│  │ - Privacy-focused (no cloud audio)                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Audio Session Manager (AVAudioSession)                       │  │
│  │ - Background audio configuration                            │  │
│  │ - Interruption handling (calls, other apps)                 │  │
│  │ - Battery optimization                                      │  │
│  │ - Audio format: 16kHz, mono, PCM                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Recording Engine                                             │  │
│  │ - Deepgram Nova-3 WebSocket streaming                       │  │
│  │ - Real-time transcription                                    │  │
│  │ - Conversation intelligence capture                          │  │
│  │ - Local storage + optional cloud sync                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ CRM Integration Layer                                        │  │
│  │ - Local Core Data storage                                   │  │
│  │ - CloudKit sync for multi-device                             │  │
│  │ - API integration (Zero CRM, Google MCP)                     │  │
│  │ - Conversation intelligence models                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ SwiftUI UI Layer                                             │  │
│  │ - Main app interface                                         │  │
│  │ - Recording controls                                         │  │
│  │ - Conversation viewer                                        │  │
│  │ - Settings & configuration                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↑
                    ┌─────────┴─────────┐
                    │ WatchConnectivity │
                    │   (WCSession)     │
                    └─────────┬─────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  watchOS APP (Apple Watch)                                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ WidgetKit Complications                                       │  │
│  │ - Circular complication (recording toggle)                   │  │
│  │ - Rectangular complication (recording status)                │  │
│  │ - Corner complications (quick status indicator)              │  │
│  │ - SwiftUI-based, timeline provider                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Minimal Watch App                                            │  │
│  │ - Recording state display (pulsing red dot)                  │  │
│  │ - Stop button                                                │  │
│  │ - Status indicators                                          │  │
│  │ - Launches via complication tap                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Warmth/
├── Warmth.xcodeproj                 # Xcode project file
│
├── Warmth/                          # iOS App Target
│   ├── App/
│   │   ├── WarmthApp.swift          # App entry point
│   │   ├── WarmthAppDelegate.swift  # App lifecycle & background handling
│   │   └── SceneDelegate.swift      # Scene management
│   │
│   ├── Views/
│   │   ├── MainTabView.swift        # Main tab interface
│   │   ├── RecordingsListView.swift # List of recordings
│   │   ├── RecordingDetailView.swift # Single conversation view
│   │   ├── SettingsView.swift       # App settings
│   │   └── Components/
│   │       ├── RecordingControl.swift # Recording controls
│   │       ├── ConversationCard.swift # Conversation preview
│   │       └── StatusIndicator.swift # Status display
│   │
│   ├── Models/
│   │   ├── Recording.swift          # Recording data model
│   │   ├── Conversation.swift       # Conversation intelligence model
│   │   ├── Contact.swift            # Contact/CRM model
│   │   └── AppSettings.swift        # User settings
│   │
│   ├── ViewModels/
│   │   ├── RecordingsViewModel.swift # Recordings list logic
│   │   ├── RecordingViewModel.swift  # Single recording logic
│   │   └── SettingsViewModel.swift   # Settings logic
│   │
│   ├── Services/
│   │   ├── WakeWordEngine.swift     # Porcupine wake word detection
│   │   ├── AudioSessionManager.swift # AVAudioSession configuration
│   │   ├── RecordingEngine.swift    # Deepgram streaming & transcription
│   │   ├── ConversationIntelligence.swift # AI analysis
│   │   ├── CRMIntegration.swift     # Zero CRM, Google MCP
│   │   ├── CloudKitSync.swift       # CloudKit synchronization
│   │   └── WatchConnectivityService.swift # iPhone WCSession handling
│   │
│   ├── Persistence/
│   │   ├── CoreDataManager.swift    # Core Data stack
│   │   ├── RecordingStore.swift     # Recording CRUD operations
│   │   └── Models.xcdatamodeld      # Core Data model
│   │
│   ├── Resources/
│   │   ├── Assets.xcassets          # Images, colors
│   │   └── Localizable.strings      # Localization
│   │
│   ├── Supporting Files/
│   │   ├── Info.plist               # iOS app configuration
│   │   └── entitlements.plist       # Background audio, etc.
│   │
│   └── Preview Content/
│       └── Preview Assets.xcassets # SwiftUI previews
│
├── WarmthWatch/                     # watchOS App Target
│   ├── App/
│   │   ├── WarmthWatchApp.swift     # Watch app entry point
│   │   └── WarmthWatchDelegate.swift # Watch lifecycle
│   │
│   ├── Views/
│   │   ├── RecordingStateView.swift # Recording state display
│   │   └── Components/
│   │       ├── PulsingDot.swift     # Recording indicator
│   │       └── StopButton.swift     # Stop recording button
│   │
│   ├── Complications/               # WidgetKit complications
│   │   ├── RecordingToggleProvider.swift # Circular toggle
│   │   ├── RecordingStatusProvider.swift  # Rectangular status
│   │   ├── CornerStatusProvider.swift     # Corner indicators
│   │   └── Models/
│   │       └── RecordingTimelineEntry.swift # Timeline entry model
│   │
│   ├── Services/
│   │   └── WatchConnectivityService.swift # Watch WCSession handling
│   │
│   ├── Resources/
│   │   ├── Assets.xcassets          # Watch-specific assets
│   │   └── Info.plist               # watchOS app configuration
│   │
│   └── Supporting Files/
│       └── entitlements.plist       # WatchKit capabilities
│
├── WarmthWatchWidgetExtension/      # watchOS Widget Extension
│   ├── RecordingToggleWidget.swift  # Circular widget
│   ├── RecordingStatusWidget.swift  # Rectangular widget
│   ├── CornerStatusWidget.swift      # Corner widget
│   └── Info.plist                   # Widget extension configuration
│
├── Shared/                          # Shared code between targets
│   ├── Models/
│   │   ├── RecordingState.swift     # Shared recording state enum
│   │   ├── WCMessage.swift          # WatchConnectivity message models
│   │   └── AppConstants.swift       # Shared constants
│   │
│   └── Utilities/
│       ├── Logger.swift             # Shared logging
│       └── Extensions.swift         # Shared extensions
│
├── Resources/                       # Shared resources
│   ├── Porcupine/                   # Wake word resources
│   │   └── hey_anna.ppn             # Custom wake word file
│   │
│   └── Documentation/
│       ├── API_Integration.md       # CRM API docs
│       └── WatchConnectivity_Protocol.md # WC protocol spec
│
├── Tests/
│   ├── WarmthTests/                 # iOS app tests
│   └── WarmthWatchTests/            # watchOS app tests
│
├── Documentation/
│   ├── ARCHITECTURE.md              # This file
│   ├── WATCHCONNECTIVITY.md         # WC implementation guide
│   ├── WAKEWORD.md                  # Wake word implementation guide
│   └── ROADMAP.md                   # Development roadmap
│
└── README.md                        # Project README
```

---

## iOS App Technical Specifications

### 1. Wake Word Engine (Porcupine iOS)

```swift
// Services/WakeWordEngine.swift
import Porcupine
import AVFoundation

class WakeWordEngine: NSObject {
    private var porcupineManager: PvPorcupineManager?
    private var isListening = false
    private let wakeWordCallback: () -> Void
    
    init(wakeWordCallback: @escaping () -> Void) {
        self.wakeWordCallback = wakeWordCallback
        super.init()
    }
    
    func startListening() throws {
        let keywordPath = Bundle.main.path(forResource: "hey_anna", ofType: "ppn")
        let accessKey = Bundle.main.object(forInfoDictionaryKey: "PorcupineAccessKey") as? String ?? ""
        
        porcupineManager = PvPorcupineManager(
            accessKey: accessKey,
            keywordPaths: [keywordPath],
            sensitivities: [0.5],
            onDetection: { [weak self] keywordIndex in
                self?.handleWakeWordDetection()
            }
        )
        
        try porcupineManager?.start()
        isListening = true
    }
    
    private func handleWakeWordDetection() {
        wakeWordCallback()
    }
    
    func stopListening() {
        porcupineManager?.stop()
        isListening = false
    }
}
```

### 2. Audio Session Manager

```swift
// Services/AudioSessionManager.swift
import AVFoundation

class AudioSessionManager {
    static let shared = AudioSessionManager()
    
    private let audioSession = AVAudioSession.sharedInstance()
    
    func configureBackgroundAudio() throws {
        try audioSession.setCategory(
            .playAndRecord,
            mode: .default,
            options: [.defaultToSpeaker, .allowBluetooth]
        )
        
        try audioSession.setActive(true)
        
        // Configure for background audio
        try audioSession.setPreferredSampleRate(16000.0)
        try audioSession.setPreferredIOBufferDuration(0.005) // 5ms buffer
    }
    
    func handleInterruption(_ notification: Notification) {
        guard let userInfo = notification.userInfo,
              let typeValue = userInfo[AVAudioSessionInterruptionTypeKey] as? UInt,
              let type = AVAudioSession.InterruptionType(rawValue: typeValue) else {
            return
        }
        
        switch type {
        case .began:
            pauseRecording()
        case .ended:
            if let optionsValue = userInfo[AVAudioSessionInterruptionOptionKey] as? UInt {
                let options = AVAudioSession.InterruptionOptions(rawValue: optionsValue)
                if options.contains(.shouldResume) {
                    resumeRecording()
                }
            }
        @unknown default:
            break
        }
    }
}
```

### 3. Background Configuration

**Info.plist additions:**
```xml
<key>UIBackgroundModes</key>
<array>
    <string>audio</string>
</array>

<key>NSMicrophoneUsageDescription</key>
<string>Warmth needs microphone access to record conversations for your personal CRM.</string>

<key>PorcupineAccessKey</key>
<string>YOUR_PORCUPINE_ACCESS_KEY</string>
```

---

## watchOS App Technical Specifications

### 1. WidgetKit Complications

```swift
// Complications/RecordingToggleProvider.swift
import WidgetKit
import SwiftUI

struct RecordingToggleProvider: TimelineProvider {
    func placeholder(in context: Context) -> RecordingToggleEntry {
        RecordingToggleEntry(date: Date(), isRecording: false)
    }
    
    func getSnapshot(in context: Context, completion: @escaping (RecordingToggleEntry) -> Void) {
        let entry = RecordingToggleEntry(date: Date(), isRecording: WatchConnectivityService.shared.isRecording)
        completion(entry)
    }
    
    func getTimeline(in context: Context, completion: @escaping (Timeline<RecordingToggleEntry>) -> Void) {
        let currentDate = Date()
        let refreshDate = Calendar.current.date(byAdding: .minute, value: 1, to: currentDate)!
        
        let entry = RecordingToggleEntry(date: currentDate, isRecording: WatchConnectivityService.shared.isRecording)
        let timeline = Timeline(entries: [entry], policy: .after(refreshDate))
        completion(timeline)
    }
}

struct RecordingToggleEntry: TimelineEntry {
    let date: Date
    let isRecording: Bool
}

struct RecordingToggleWidget: Widget {
    let kind: String = "RecordingToggleWidget"
    
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: RecordingToggleProvider()) { entry in
            RecordingToggleView(entry: entry)
        }
        .configurationDisplayName("Recording Toggle")
        .description("Toggle conversation recording")
        .supportedFamilies([.accessoryCircular])
    }
}
```

### 2. WatchConnectivity Service

```swift
// Services/WatchConnectivityService.swift (Watch)
import WatchConnectivity

class WatchConnectivityService: NSObject, ObservableObject {
    static let shared = WatchConnectivityService()
    
    @Published var isRecording = false
    @Published var lastError: String?
    
    private let session: WCSession
    
    override init() {
        self.session = WCSession.default
        super.init()
        
        if WCSession.isSupported() {
            session.delegate = self
            session.activate()
        }
    }
    
    func toggleRecording() {
        let message: [String: Any] = [
            "action": "toggleRecording",
            "timestamp": Date().timeIntervalSince1970
        ]
        
        session.sendMessage(message, replyHandler: { response in
            DispatchQueue.main.async {
                if let isRecording = response["isRecording"] as? Bool {
                    self.isRecording = isRecording
                }
            }
        }, errorHandler: { error in
            DispatchQueue.main.async {
                self.lastError = error.localizedDescription
            }
        })
    }
}

extension WatchConnectivityService: WCSessionDelegate {
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        if let error = error {
            self.lastError = error.localizedDescription
        }
    }
    
    func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        DispatchQueue.main.async {
            if let action = message["action"] as? String {
                switch action {
                case "recordingStateChanged":
                    if let isRecording = message["isRecording"] as? Bool {
                        self.isRecording = isRecording
                    }
                default:
                    break
                }
            }
        }
    }
}
```

### 3. Watch App UI

```swift
// Views/RecordingStateView.swift
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
                
                Button(action: {
                    wcService.toggleRecording()
                }) {
                    Text("Stop")
                        .font(.headline)
                        .foregroundColor(.white)
                        .padding()
                        .background(Color.red)
                        .cornerRadius(10)
                }
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
```

---

## iPhone WatchConnectivity Service

```swift
// Services/WatchConnectivityService.swift (iPhone)
import WatchConnectivity

class WatchConnectivityService: NSObject, ObservableObject {
    static let shared = WatchConnectivityService()
    
    @Published var isRecording = false
    @Published var watchConnected = false
    
    private let session: WCSession
    private let recordingEngine: RecordingEngine
    
    override init() {
        self.session = WCSession.default
        self.recordingEngine = RecordingEngine.shared
        super.init()
        
        if WCSession.isSupported() {
            session.delegate = self
            session.activate()
        }
    }
    
    private func sendRecordingStateToWatch() {
        let message: [String: Any] = [
            "action": "recordingStateChanged",
            "isRecording": isRecording,
            "timestamp": Date().timeIntervalSince1970
        ]
        
        if session.isReachable {
            session.sendMessage(message, replyHandler: nil)
        } else {
            // Queue for when watch becomes reachable
            session.transferUserInfo(message)
        }
    }
    
    func toggleRecording() {
        if isRecording {
            recordingEngine.stopRecording()
        } else {
            recordingEngine.startRecording()
        }
        
        isRecording.toggle()
        sendRecordingStateToWatch()
    }
}

extension WatchConnectivityService: WCSessionDelegate {
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        DispatchQueue.main.async {
            self.watchConnected = activationState == .activated
        }
    }
    
    func sessionDidBecomeInactive(_ session: WCSession) {
        DispatchQueue.main.async {
            self.watchConnected = false
        }
    }
    
    func sessionDidDeactivate(_ session: WCSession) {
        DispatchQueue.main.async {
            self.watchConnected = false
        }
        session.activate()
    }
    
    func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        DispatchQueue.main.async {
            if let action = message["action"] as? String {
                switch action {
                case "toggleRecording":
                    self.toggleRecording()
                default:
                    break
                }
            }
        }
    }
    
    func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        DispatchQueue.main.async {
            if let isRecording = applicationContext["isRecording"] as? Bool {
                self.isRecording = isRecording
            }
        }
    }
}
```

---

## Battery Optimization Strategy

### 1. Adaptive Listening

```swift
class BatteryOptimizedWakeWord: WakeWordEngine {
    private let batteryMonitor = BatteryMonitor()
    
    override func startListening() throws {
        // Adjust listening frequency based on battery level
        let batteryLevel = batteryMonitor.currentLevel
        
        if batteryLevel < 20 {
            // Low power mode: reduce check frequency
            try startLowPowerListening()
        } else if batteryLevel < 50 {
            // Medium power mode
            try startMediumPowerListening()
        } else {
            // Full power mode
            try super.startListening()
        }
    }
    
    private func startLowPowerListening() throws {
        // Implement interval-based listening instead of continuous
        // Check for wake word every 5 seconds instead of continuously
    }
}
```

### 2. Conference Mode Detection

```swift
class ConferenceModeManager {
    @Published var isConferenceMode = false
    
    func enableConferenceMode() {
        isConferenceMode = true
        // Enable full wake word detection
        // Disable battery optimizations
        // Increase audio quality
    }
    
    func disableConferenceMode() {
        isConferenceMode = false
        // Enable battery optimizations
        // Reduce wake word check frequency
    }
}
```

---

## Development Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Set up Xcode project with iOS and watchOS targets
- [ ] Implement basic SwiftUI UI for iOS app
- [ ] Create Core Data models for recordings
- [ ] Set up WidgetKit extension for watchOS
- [ ] Implement basic WatchConnectivity infrastructure

### Phase 2: Wake Word Engine (Week 3-4)
- [ ] Integrate Porcupine SDK for wake word detection
- [ ] Train custom "Hey Anna" wake word
- [ ] Implement background audio session management
- [ ] Add interruption handling
- [ ] Test battery consumption

### Phase 3: Recording Engine (Week 5-6)
- [ ] Implement Deepgram Nova-3 WebSocket streaming
- [ ] Add real-time transcription display
- [ ] Implement local audio storage
- [ ] Add conversation intelligence capture
- [ ] Create recording management UI

### Phase 4: Watch Integration (Week 7-8)
- [ ] Implement all complication sizes
- [ ] Create watch app recording state UI
- [ ] Implement WatchConnectivity message handling
- [ ] Add background app refresh support
- [ ] Test watch-to-iPhone communication

### Phase 5: CRM Integration (Week 9-10)
- [ ] Implement CloudKit sync
- [ ] Add Zero CRM API integration
- [ ] Implement Google MCP for email drafting
- [ ] Add conversation intelligence analysis
- [ ] Create contact management features

### Phase 6: Polish & Testing (Week 11-12)
- [ ] Battery optimization testing
- [ ] Background execution testing
- [ ] UI/UX refinement
- [ ] Error handling and edge cases
- [ ] App Store submission preparation

---

## Key Technical Considerations

### 1. Privacy & Security
- All wake word processing happens on-device
- Audio files stored locally with optional cloud sync
- End-to-end encryption for CloudKit sync
- User-controlled data sharing with CRM systems

### 2. Performance
- Wake word detection: <5% CPU usage
- Memory footprint: <50MB when idle
- Recording: ~100MB per hour of audio
- Battery impact: <5% per hour in conference mode

### 3. User Experience
- Frictionless wake word activation
- Instant recording start (<100ms)
- Clear visual feedback on both devices
- Graceful handling of interruptions
- Offline-first architecture

### 4. App Store Guidelines
- Comply with background audio restrictions
- Provide clear microphone usage description
- Handle user permissions gracefully
- Ensure battery usage is acceptable
- Follow Human Interface Guidelines

---

This architecture provides a solid foundation for building a native iOS/watchOS personal CRM recording app with always-listening wake word detection and seamless Apple Watch integration.
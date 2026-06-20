# Warmth iOS App

Native iOS/watchOS personal CRM recording app with phrase-triggered recording, manual controls, and Apple Watch integration.

## Features

- **Phrase Trigger**: Say **"Hi, I'm Zack"** or **"I'm Zack"** while the app is in the foreground to start recording (Apple Speech framework, on-device)
- **Manual Recording**: Tap on iPhone or use Apple Watch controls to start and stop recording
- **Siri Shortcuts**: Optional voice shortcuts for hands-free start/stop
- **Background Recording**: Continuous recording with proper AVAudioSession management
- **Apple Watch Control**: WidgetKit complications for remote recording control
- **WatchConnectivity**: Seamless iPhone-Watch communication
- **Deepgram Integration**: Real-time transcription via WebSocket
- **CRM Integration**: Connects to backend API for data sync

## Phrase trigger

The iPhone app listens for hardcoded phrases when active in the foreground:

| Spoken phrase | Normalized match |
|---------------|------------------|
| Hi, I'm Zack | `hi im zack` |
| I'm Zack | `im zack` |

Matching is case-insensitive and ignores punctuation. On detection, the app plays haptic feedback and calls `RecordingEngine.shared.startRecording()`.

Implementation: `Warmth/Services/PhraseTriggerEngine.swift` (Apple `Speech` + `SFSpeechRecognizer` — no Porcupine or third-party wake-word SDK).

Phrase listening stops when the app moves to background; use manual or Watch controls there.

## Structure

- `Warmth/` - Main iOS app target
- `WarmthWatch/` - watchOS app target
- `WarmthWatchWidgetExtension/` - WidgetKit complications
- `Shared/` - Shared code between targets

## Integration with Backend

The iOS app integrates with the Python backend via REST API:

- **POST /api/recordings** - Upload audio files
- **GET /api/conversations** - Fetch conversation intelligence
- **WebSocket /ws/transcript** - Real-time transcript updates

## Development

Requires:
- Xcode 15+
- iOS 17+
- watchOS 10+

## Setup

1. Configure backend API URL in `AppConstants.swift`
2. Add required Info.plist usage descriptions (no `.xcodeproj` is checked into this repo — add these when creating the Xcode project):

```xml
<key>NSMicrophoneUsageDescription</key>
<string>Warmth needs microphone access to record conversations and detect the phrase trigger.</string>
<key>NSSpeechRecognitionUsageDescription</key>
<string>Warmth uses on-device speech recognition to detect "Hi, I'm Zack" and start recording.</string>
```

3. Build and run on a **physical device** for reliable phrase detection (simulator mic/speech can be flaky)
4. Grant microphone and speech recognition when prompted
5. With the app in the foreground, say **"Hi, I'm Zack"** — you should feel haptic feedback and recording should start

## Testing phrase trigger

1. Run the iOS app on device with the app visible (foreground)
2. Accept microphone + speech recognition permissions
3. Speak clearly: **"Hi, I'm Zack"** or **"I'm Zack"**
4. Expect medium haptic + `RecordingEngine.isRecording == true`
5. Repeat within 3 seconds should not re-trigger (cooldown)

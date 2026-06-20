# Warmth iOS App

Native iOS/watchOS event-intelligence app. Capture introductions via **Siri**, **Action Button**, **Apple Watch**, **in-app orb**, or optional **passive floor listening** at events.

## Capture triggers (MVP)

| Trigger | How | Preference key |
|---------|-----|----------------|
| **Siri** | “Hey Siri, I'm meeting Sarah with Warmth” | `siri` |
| **Action Button** | Assign *Start Warmth Capture* in iOS Settings | `actionButton` |
| **Watch** | Tap wrist to start/stop | `watch` |
| **Manual** | Tap ember orb on Capture tab | `manual` |
| **Floor listening** | Contact-name wake words → 30s auto-capture (in-app, foreground) | `passiveFloorListening` |

All active capture paths route through `AppModel.startCapture(source:personName:)` → `SpeechService.startRecording()`.

Passive floor listening uses a separate pipeline (`EventListeningEngine`) with Soniqo contact-name wake words. It pauses while a manual/Siri/watch capture is recording.

## Active capture pipeline

```
Siri / Action Button / Watch / Orb tap
      ↓
AppModel.startCapture(source:personName:)
      ↓
SpeechService (AVAudioEngine + SFSpeechRecognizer)
      ↓
stop → capturePerson(from:) → SignalClient → backend
```

## Passive floor listening (optional)

```
MicrophoneStream (16 kHz)
      ↓
WakeWordEngine (Soniqo) — "hey anna", contact first names
      ↓
30s CaptureWindow + ICP-biased transcription
      ↓
AppModel.capturePerson(from:)
```

Enabled in onboarding or **Settings → Capture methods → Floor listening**. Only runs while the app is foregrounded.

## Structure

- `Warmth/App/AppModel.swift` — unified capture router + passive coordinator
- `Warmth/Intents/WarmthCaptureIntents.swift` — Siri + Action Button App Intents
- `Warmth/Services/Settings/CaptureActivationPreferences.swift` — user prefs
- `Warmth/Features/Capture/CaptureView.swift` — hero orb + floor listening banner
- `Warmth/Services/EventListeningEngine.swift` — passive event pipeline
- `WarmthWatch/` — watchOS companion (tap to start/stop phone capture)

## Dependencies

- Firebase Auth, Google Sign-In
- [SpeechWakeWord](https://github.com/soniqo/speech-swift) (Soniqo) — contact-name detection for floor listening only

## Device testing checklist

1. **Siri** — “Hey Siri, I'm meeting Anna with Warmth” → app opens, recording, name in header
2. **Action Button** — assign Start Warmth Capture → recording starts
3. **Watch** — tap watch → phone records (requires paired watch app)
4. **Orb** — tap ember orb → recording; tap again or Stop & save → uploads
5. **Floor listening** — enable in Settings, foreground app, say “hey Anna” → 30s window + signal
6. **Disabled method** — turn off Watch in Settings → watch tap ignored
7. **Permissions** — deny mic → graceful error banner on Capture

## Development

Requires:
- Xcode 15+
- iOS 17+ (`SFCustomLanguageModelData` for floor listening)
- Physical device for mic, Siri, and Soniqo wake-word models

```bash
cd iOS/Warmth-iOS
xcodegen generate
xcodebuild build -scheme Warmth \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  -quiet
```

Bundle ID: `com.warmth.gtmhackathon`

## Setup

1. Firebase iOS app — `Warmth-iOS/Warmth/GoogleService-Info.plist` in Warmth target
2. `xcodegen generate` after editing `project.yml`
3. Grant microphone + speech recognition on first launch
4. Choose capture methods in onboarding; adjust anytime in Settings

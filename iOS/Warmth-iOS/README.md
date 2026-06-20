# Warmth iOS App

Native iOS/watchOS event-intelligence app. The phone passively listens for
**contact names** (wake words), opens a short on-device capture window when one
is heard, builds a social graph from the conversation, scores the lead against
your ICP, and pushes qualified leads to the backend → Zero CRM.

## Pipeline

```
AVAudioEngine (iPhone mic, 16kHz Float32)        MicrophoneStream.swift
      ↓  raw PCM chunks  +  16kHz mono [Float]
Soniqo WakeWordDetector (CoreML, Neural Engine)  WakeWordEngine.swift
      keywords: ["hey anna", "hey james", contact names…]
      ↓  on detection: name + timestamp
┌────────────────────────────────────────────┐
│  30-second capture window opens            │  CaptureWindow.swift
│  SFSpeechRecognizer (on-device)            │
│  + SFCustomLanguageModelData (ICP vocab)   │  ICPVocabulary.swift
│       ↓  rolling transcript                │
│  SocialGraphEngine (NLTagger)              │  SocialGraphEngine.swift
│  ├── Named entity extraction (names, orgs) │
│  ├── Relationship pattern detection        │
│  ├── ICP keyword proximity scoring         │
│  └── PersonNode graph update               │
└────────────────────────────────────────────┘
      ↓  Signal(person, company, relationships, score)   Signal.swift
WatchConnectivity → Watch haptic (lead detected!)  WatchConnectivityService.swift
      ↓
Backend POST /api/signals → Zero CRM → follow-up sequence   SignalAPIClient.swift
```

`EventListeningEngine.swift` is the orchestrator that wires these together
and exposes `state` / `liveTranscript` / `lastSignal` to the UI (`ListeningView.swift`).

## How it works

1. **Mic** — `MicrophoneStream` runs a single shared `AVAudioEngine` input tap and
   fans every buffer out as (a) the raw `AVAudioPCMBuffer` for the recognizer and
   (b) a downsampled 16 kHz mono `[Float]` for the wake-word detector.
2. **Wake word** — `WakeWordEngine` wraps the Soniqo `SpeechWakeWord` detector.
   Keywords are built **dynamically** from the watchlist (`WatchlistProvider`):
   for each name it registers `"hey <name>"` (boost 0.6) and the bare first name
   (boost 0.4). A detection maps back to the contact name via a phrase→name table.
3. **Capture window** — on detection, `EventListeningEngine` opens a 30 s
   `CaptureWindow`. Recognition is on-device and biased toward ICP terms via an
   `SFCustomLanguageModelData` model built from `ICPVocabulary` ("RevOps",
   "Series B", …). While capturing, mic buffers are appended to the request and
   wake-word pushes are paused to avoid re-triggering.
4. **Social graph** — `SocialGraphEngine` runs `NLTagger` NER (personal + org
   names), detects relationship cues ("works with", "reports to", "introduced me
   to"), scores ICP keywords by proximity to the person/org, and accumulates
   `PersonNode`s across windows.
5. **Signal** — the window yields a `Signal(person, company, relationships,
   score)`. If `score >= 50` it's a lead: the watch buzzes
   (`WKInterfaceDevice.play(.notification)`) and the signal is `POST`ed to
   `/api/signals`.

## Watchlist

`WatchlistProvider` seeds a sample list of first names. In production, hydrate it
from the user's Zero CRM contacts (e.g. `GET /api/contacts`) before an event and
call `WatchlistProvider.shared.update(names:)`, then restart the engine so the
wake-word detector re-configures.

## ICP vocabulary

`ICPVocabulary` mirrors the backend ICP config (`packages/core/models/icp.py`):
weighted keywords used both to bias speech recognition and to score leads.
Scoring matches the backend pre-scorer (keyword weights + event-audio bonus,
capped at 100).

## Structure

- `Warmth/` — Main iOS app target
  - `App/WarmthApp.swift` — app entry; starts `EventListeningEngine`
  - `Models/` — `Signal.swift`, `ICPVocabulary.swift`
  - `Services/` — mic, wake word, capture, social graph, API client, orchestrator
  - `Views/ListeningView.swift` — listening state + live transcript + last lead
- `WarmthWatch/` — watchOS app target (haptic + lead banner)
- `WarmthWatchWidgetExtension/` — WidgetKit complications
- `Shared/` — shared code

## Dependencies

Add the Soniqo wake-word package via **Swift Package Manager** to the **Warmth**
target:

```
https://github.com/soniqo/speech-swift   (product: SpeechWakeWord)
```

> **API note:** the orchestrator reads the matched phrase from
> `WakeWordDetection.keyword`. If the package names that property differently
> (e.g. `phrase`), update `matchedName(from:)` in `EventListeningEngine.swift`.

## Integration with Backend

- **POST `/api/signals`** — primary path; sends `Signal` JSON (snake_case,
  ISO-8601 dates). Backend forwards qualified leads to Zero CRM and starts the
  follow-up sequence.

Set the base URL via the `WARMTH_API_BASE_URL` Info.plist key (defaults to
`http://localhost:8000`).

## Development

Requires:
- Xcode 15+
- iOS 17+ (uses `SFCustomLanguageModelData`)
- watchOS 10+

## Setup

1. **Firebase iOS app** (registered in project `warmth-gtm-hackathon`):
   - Bundle ID: `com.warmth.gtmhackathon`
   - Config file: `Warmth-iOS/Warmth/GoogleService-Info.plist`
   - Add the plist to the **Warmth** target (Copy Bundle Resources).

2. Add the `SpeechWakeWord` SPM dependency (see **Dependencies**).

3. Add required Info.plist keys (no `.xcodeproj` is checked into this repo — add
   these when creating the Xcode project):

```xml
<key>NSMicrophoneUsageDescription</key>
<string>Warmth listens for contact names to capture conversation intelligence.</string>
<key>NSSpeechRecognitionUsageDescription</key>
<string>Warmth uses on-device speech recognition to transcribe conversations after a name is heard.</string>
<key>WARMTH_API_BASE_URL</key>
<string>http://localhost:8000</string>
```

4. Build and run on a **physical device** (simulator mic/speech and the Neural
   Engine wake-word model are unreliable in the simulator).
5. Grant microphone + speech recognition when prompted.
6. With the app foregrounded, say a watchlist name (e.g. **"hey Anna"**) — a
   capture window opens; if ICP terms are heard, the watch buzzes and a lead is
   posted.

## Testing

1. Run on device; accept microphone + speech permissions.
2. Say **"hey Anna"** (a seeded watchlist name). Expect `state == .capturing`.
3. During the 30 s window, mention ICP terms ("we're scaling RevOps after our
   Series B"). Expect a `Signal` with `score >= 50`, a watch haptic, and a
   `POST /api/signals`.
4. Watch face shows the 🔥 Lead banner with name + ICP score.

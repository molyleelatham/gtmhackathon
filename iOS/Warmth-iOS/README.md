# Warmth iOS App

Native iOS/watchOS personal CRM recording app with wake word detection and Apple Watch integration.

## Features

- **Wake Word Detection**: "Hey Anna" triggers recording using Porcupine (offline)
- **Background Recording**: Continuous recording with proper AVAudioSession management
- **Apple Watch Control**: WidgetKit complications for remote recording control
- **WatchConnectivity**: Seamless iPhone-Watch communication
- **Deepgram Integration**: Real-time transcription via WebSocket
- **CRM Integration**: Connects to backend API for data sync

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
- Porcupine SDK access key

## Setup

1. Add Porcupine access key to `Info.plist`
2. Configure backend API URL in `AppConstants.swift`
3. Build and run on physical device (wake word requires device)
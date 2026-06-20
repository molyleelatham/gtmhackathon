# Warmth iOS App

Native iOS/watchOS personal CRM recording app with multiple triggering methods and Apple Watch integration.

## Features

- **Multiple Triggering Methods**: Manual controls, Apple Watch complications, Siri shortcuts
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

## Setup

1. Configure backend API URL in `AppConstants.swift`
2. Build and run on physical device or simulator
3. Grant microphone permission when prompted
4. Use Apple Watch complications or manual controls to start recording
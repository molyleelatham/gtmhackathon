import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from packages.core.schemas.transcript_schema import TranscriptEvent
from packages.integrations.asr.deepgram.client import DeepgramEventClient


async def test_microphone_pipeline():
    """Test microphone pipeline with Deepgram"""
    print("🧪 Testing Microphone Pipeline...")
    
    # Check API key
    if not os.getenv("DEEPGRAM_API_KEY"):
        print("❌ DEEPGRAM_API_KEY environment variable not set")
        return
    
    try:
        # This is a placeholder - actual microphone testing would require
        # PyAudio and audio hardware setup
        
        print("📦 Initializing Deepgram client...")
        
        async def on_transcript(event: TranscriptEvent):
            print(f"🎤 Transcript: {event.transcript}")
            print(f"   Speaker: {event.speaker}")
            print(f"   Confidence: {event.confidence}")
            print(f"   Final: {event.is_final}")
        
        client = DeepgramEventClient(on_transcript=on_transcript)
        
        print("⚠️  Note: Full microphone testing requires:")
        print("   - PyAudio installation")
        print("   - Working microphone hardware")
        print("   - Audio capture setup")
        print("\n✅ Deepgram client initialized successfully!")
        print("📝 To test full microphone pipeline, ensure audio dependencies are installed.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_microphone_pipeline())
import asyncio
import websockets
import json
import os
from typing import Optional, Callable, Any
from ....core.schemas.transcript_schema import TranscriptEvent


class DeepgramConferenceClient:
    """Deepgram Nova-3 WebSocket client for conference transcription"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        on_transcript: Optional[Callable[[TranscriptEvent], Any]] = None
    ):
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        self.on_transcript = on_transcript
        
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable must be set")
        
        # Configure Deepgram URL with parameters
        self.url = self._build_deepgram_url()
    
    def _build_deepgram_url(self) -> str:
        """Build Deepgram WebSocket URL with configuration"""
        base_url = "wss://api.deepgram.com/v1/listen"
        
        params = [
            "model=nova-3",
            "diarize=true",
            "interim_results=true",
            "endpointing=500",
            # Boost ICP keywords
            "keyterm=RevOps",
            "keyterm=HubSpot", 
            "keyterm=Salesforce",
            "keyterm=pipeline",
            "keyterm=attribution",
            "keyterm=Series",
            "keyterm=Sales+Engineer",
            "keyterm=CRM"
        ]
        
        return f"{base_url}?{'&'.join(params)}"
    
    async def stream(self, audio_stream):
        """
        Stream audio to Deepgram for transcription
        
        Args:
            audio_stream: Async generator that yields audio chunks
        """
        async with websockets.connect(
            self.url,
            extra_headers={"Authorization": f"Token {self.api_key}"}
        ) as websocket:
            
            # Create tasks for sending and receiving
            send_task = asyncio.create_task(self._send_audio(websocket, audio_stream))
            receive_task = asyncio.create_task(self._receive_transcripts(websocket))
            
            # Wait for both tasks to complete
            await asyncio.gather(send_task, receive_task, return_exceptions=True)
    
    async def _send_audio(self, websocket, audio_stream):
        """Send audio chunks to Deepgram"""
        try:
            async for chunk in audio_stream:
                await websocket.send(chunk)
        except Exception as e:
            print(f"Error sending audio: {e}")
    
    async def _receive_transcripts(self, websocket):
        """Receive and process transcripts from Deepgram"""
        try:
            async for message in websocket:
                data = json.loads(message)
                
                # Extract transcript from Deepgram response
                if "channel" in data and "alternatives" in data["channel"]:
                    alternative = data["channel"]["alternatives"][0]
                    transcript = alternative.get("transcript", "")
                    
                    if transcript:
                        event = TranscriptEvent(
                            transcript=transcript,
                            speaker=data.get("channel", {}).get("speaker", 0),
                            confidence=alternative.get("confidence", 0.0),
                            is_final=data.get("is_final", False),
                            words=alternative.get("words", [])
                        )
                        
                        if self.on_transcript:
                            await self.on_transcript(event)
        except Exception as e:
            print(f"Error receiving transcripts: {e}")
    
    async def transcribe_file(self, audio_file_path: str) -> list[TranscriptEvent]:
        """
        Transcribe an audio file using Deepgram REST API
        
        Args:
            audio_file_path: Path to audio file
        
        Returns:
            List of transcript events
        """
        import httpx
        
        url = "https://api.deepgram.com/v1/listen"
        params = {
            "model": "nova-3",
            "diarize": "true",
            "punctuate": "true"
        }
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/wav"
        }
        
        with open(audio_file_path, "rb") as audio_file:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    url,
                    params=params,
                    headers=headers,
                    content=audio_file.read()
                )
                response.raise_for_status()
                result = response.json()
        
        # Convert Deepgram response to TranscriptEvents
        events = []
        if "results" in result and "channels" in result["results"]:
            for channel in result["results"]["channels"]:
                for alternative in channel["alternatives"]:
                    words = alternative.get("words", [])
                    for word in words:
                        event = TranscriptEvent(
                            transcript=word.get("word", ""),
                            speaker=word.get("speaker", 0),
                            confidence=word.get("confidence", 0.0),
                            is_final=True,
                            words=[word]
                        )
                        events.append(event)
        
        return events
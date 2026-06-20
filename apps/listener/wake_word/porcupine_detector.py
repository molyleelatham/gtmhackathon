import pvporcupine
import pyaudio
import struct
from typing import Optional, Callable


class PorcupineWakeWordDetector:
    """Wake word detector using Picovoice Porcupine"""
    
    def __init__(
        self,
        access_key: str,
        wake_word_callback: Optional[Callable] = None,
        sensitivity: float = 0.5
    ):
        """
        Initialize Porcupine wake word detector
        
        Args:
            access_key: Picovoice access key
            wake_word_callback: Callback function when wake word is detected
            sensitivity: Detection sensitivity (0.0 to 1.0)
        """
        self.access_key = access_key
        self.wake_word_callback = wake_word_callback
        self.sensitivity = sensitivity
        
        # Initialize Porcupine
        try:
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[self._get_wake_word_path()],
                sensitivities=[sensitivity]
            )
        except Exception as e:
            print(f"Failed to initialize Porcupine: {e}")
            self.porcupine = None
        
        # Audio configuration
        self.sample_rate = 16000
        self.frame_length = self.porcupine.frame_length if self.porcupine else 512
        self.is_running = False
        
        # PyAudio instance
        self.audio = None
        self.stream = None
    
    def _get_wake_word_path(self) -> str:
        """
        Get path to wake word file.
        In production, this would be a trained custom wake word file.
        For demo, we'll use a built-in keyword.
        """
        # For demo purposes, use built-in "porcupine" keyword
        # In production, train custom "Hey Anna" wake word
        # return "hey_anna.ppn"
        return None  # Use default keyword
    
    def start_detection(self):
        """Start wake word detection"""
        if not self.porcupine:
            print("Porcupine not initialized, cannot start detection")
            return
        
        self.is_running = True
        self.audio = pyaudio.PyAudio()
        
        try:
            self.stream = self.audio.open(
                rate=self.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.frame_length,
                input_device_index=None
            )
            
            print("🎤 Wake word detection started...")
            
            while self.is_running:
                try:
                    # Read audio frame
                    pcm = self.stream.read(self.frame_length, exception_on_overflow=False)
                    pcm = struct.unpack_from("h" * self.frame_length, pcm)
                    
                    # Process for wake word
                    result = self.porcupine.process(pcm)
                    
                    if result >= 0:
                        print(f"✅ Wake word detected! (keyword index: {result})")
                        if self.wake_word_callback:
                            self.wake_word_callback()
                
                except KeyboardInterrupt:
                    print("\n⏹️  Detection stopped by user")
                    break
                except Exception as e:
                    print(f"❌ Error in detection loop: {e}")
                    break
        
        finally:
            self.stop_detection()
    
    def stop_detection(self):
        """Stop wake word detection"""
        self.is_running = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.audio:
            self.audio.terminate()
        
        print("🛑 Wake word detection stopped")
    
    def process_audio_frame(self, audio_frame: bytes) -> bool:
        """
        Process a single audio frame for wake word detection
        
        Args:
            audio_frame: Audio frame as bytes
        
        Returns:
            True if wake word detected, False otherwise
        """
        if not self.porcupine:
            return False
        
        try:
            pcm = struct.unpack_from("h" * self.frame_length, audio_frame)
            result = self.porcupine.process(pcm)
            return result >= 0
        except Exception as e:
            print(f"Error processing audio frame: {e}")
            return False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.porcupine:
            self.porcupine.delete()
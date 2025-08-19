"""
Voice loop for the AI Language Tutor application.
Handles audio capture and playback.
"""

import threading
import queue
import pyaudio
import wave
import numpy as np
from openai import OpenAI
import requests
import tempfile
import os
import time
from io import BytesIO
import pygame
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from utils.logger import get_logger
from core.event_bus import EventBus, EventTypes
from config import config


@dataclass
class AudioConfig:
    """Audio configuration settings."""
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    audio_format: int = pyaudio.paInt16
    silence_threshold: float = 1.5
    min_speech_duration: float = 0.5
    rms_threshold: int = 10
    zcr_threshold: float = 0.001
    debug_audio: bool = True


class VoiceLoop:
    """Handles audio capture, processing, and playback."""
    
    def __init__(self, event_bus: EventBus):
        self.logger = get_logger(__name__)
        self.event_bus = event_bus
        
        # Audio configuration - balanced to detect speech while filtering noise
        self.config = AudioConfig(
            sample_rate=16000,
            chunk_size=1024,
            channels=1,
            silence_threshold=1.0,  # Reduced for faster response
            min_speech_duration=0.5,  # Reduced for more responsive detection
            rms_threshold=60,  # Keep strict RMS threshold
            zcr_threshold=0.03,  # Keep strict ZCR threshold
            debug_audio=True
        )
        
        # Audio processing
        self.audio = pyaudio.PyAudio()
        self.recording = False
        self.audio_queue = queue.Queue()
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        # OpenAI client
        self.client = OpenAI(api_key=config.openai_api_key)
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        self.logger.info("VoiceLoop initialized")
    
    def start_recording(self) -> bool:
        """Start audio recording with Voice Activity Detection."""
        if self.recording:
            self.logger.warning("Recording already in progress")
            return False
        
        try:
            self.recording = True
            self.event_bus.publish(EventTypes.AUDIO_STARTED)
            
            # Start recording in background thread
            threading.Thread(target=self._continuous_record_audio, daemon=True).start()
            
            self.logger.info("Recording started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self.recording = False
            return False
    
    def stop_recording(self) -> bool:
        """Stop audio recording."""
        if not self.recording:
            self.logger.warning("No recording in progress")
            return False
        
        try:
            self.recording = False
            self.event_bus.publish(EventTypes.AUDIO_STOPPED)
            
            self.logger.info("Recording stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            return False
    
    def _continuous_record_audio(self):
        """Continuous recording with voice activity detection"""
        try:
            # Find default input device
            try:
                input_device = self.audio.get_default_input_device_info()['index']
                self.logger.info(f"Using audio device: {self.audio.get_device_info_by_index(input_device)['name']}")
            except Exception as e:
                self.logger.error(f"Error setting up audio device: {e}")
                # Try to find any available input device
                for i in range(self.audio.get_device_count()):
                    device_info = self.audio.get_device_info_by_index(i)
                    if device_info['maxInputChannels'] > 0:
                        input_device = i
                        self.logger.info(f"Using fallback audio device: {device_info['name']}")
                        break
                else:
                    input_device = None
            
            stream = self.audio.open(
                format=self.config.audio_format,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=self.config.chunk_size
            )
            
            frames = []
            last_speech_time = time.time()
            speech_started = False
            
            self.logger.info("Audio stream opened, starting VAD")
            
            while self.recording:
                try:
                    data = stream.read(self.config.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Check for speech activity every few chunks
                    if len(frames) % 4 == 0:  # Check every ~0.25 seconds
                        has_speech = self._has_speech_content(frames[-4:])  # Check last 4 chunks
                        
                        if has_speech:
                            if not speech_started:
                                speech_started = True
                                self.logger.info("🎤 Speech detected - recording...")
                            last_speech_time = time.time()
                        elif speech_started:
                            # Check if we've been silent long enough
                            silence_duration = time.time() - last_speech_time
                            speech_duration = last_speech_time - (time.time() - len(frames) * self.config.chunk_size / self.config.sample_rate)
                            
                            if silence_duration >= self.config.silence_threshold and speech_duration >= self.config.min_speech_duration:
                                self.logger.info(f"🔇 Silence detected ({silence_duration:.1f}s) - processing audio...")
                                # Process the recorded audio
                                if frames:
                                    threading.Thread(target=self._process_audio, args=(frames,), daemon=True).start()
                                frames = []
                                speech_started = False
                                last_speech_time = time.time()
                    
                except Exception as e:
                    self.logger.error(f"Audio recording error: {e}")
                    break
            
            # Process any remaining audio when stopping
            if frames and speech_started:
                threading.Thread(target=self._process_audio, args=(frames,), daemon=True).start()
                    
            stream.stop_stream()
            stream.close()
                
        except Exception as e:
            self.logger.error(f"Recording setup error: {e}")
            self.event_bus.publish(EventTypes.AUDIO_ERROR, {"error": str(e)})
    
    def _has_speech_content(self, frames: List[bytes]) -> bool:
        """Check if audio frames contain meaningful speech content"""
        try:
            # Convert frames to numpy array
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            
            # Calculate RMS (Root Mean Square) to measure audio level
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Calculate zero crossing rate (indicates speech vs silence)
            zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
            zero_crossing_rate = zero_crossings / len(audio_data)
            
            # Thresholds for speech detection (balanced for sensitivity and filtering)
            rms_threshold = 40  # Lowered for better speech detection
            zcr_threshold = 0.02  # Lowered for better speech detection
            
            # Check if audio meets speech criteria
            has_speech = rms > rms_threshold and zero_crossing_rate > zcr_threshold
            
            # Additional checks for different speech patterns (more sensitive)
            if rms > 100:  # Lowered for loud speech
                has_speech = True
            elif rms > 60 and zero_crossing_rate > 0.15:  # Lowered thresholds
                has_speech = True
            elif rms > 40 and zero_crossing_rate > 0.25:  # Lowered thresholds
                has_speech = True
            
            if self.config.debug_audio:
                status = "PASS" if has_speech else "FILTERED"
                print(f"Audio {status} - RMS: {rms:.0f}, ZCR: {zero_crossing_rate:.4f}")
            
            return has_speech
            
        except Exception as e:
            print(f"Speech detection error: {e}")
            return True  # Default to processing if detection fails
    
    def _process_audio(self, frames: List[bytes]):
        """Process recorded audio through Whisper and get AI response."""
        try:
            # Skip processing if frames are empty
            if not frames:
                return
                
            # Check if audio has meaningful content (not just silence/noise)
            # Commented out to match original working version
            # if self.config.debug_audio and not self._has_speech_content(frames):
            #     return  # Skip processing if no meaningful audio
            
            # Save audio to temporary file
            temp_file = None
            try:
                temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_filename = temp_file.name
                temp_file.close()
                
                with wave.open(temp_filename, 'wb') as wav_file:
                    wav_file.setnchannels(self.config.channels)
                    wav_file.setsampwidth(self.audio.get_sample_size(self.config.audio_format))
                    wav_file.setframerate(self.config.sample_rate)
                    wav_file.writeframes(b''.join(frames))
                
                # Transcribe with Whisper
                with open(temp_filename, 'rb') as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                
                # Clean up temp file
                try:
                    os.unlink(temp_filename)
                except:
                    pass
                
                if transcript.text.strip():
                    user_text = transcript.text.strip()
                    
                    # Filter out very short or meaningless responses (extremely aggressive)
                    meaningless_responses = [
                        'thank you', 'thanks', 'okay', 'ok', 'yeah', 'yes', 'no', 'uh', 'um', 'ah',
                        'hmm', 'mm', 'mhm', 'uh huh', 'uh-uh', 'nope', 'yep', 'sure', 'right',
                        'okay', 'alright', 'got it', 'gotcha', 'mhm', 'uh-huh', 'thank', 'thx',
                        'ty', 'k', 'y', 'n', 'm', 'h', 'a', 'e', 'i', 'o', 'u', 'thank', 'thanks',
                        'thank you', 'thankyou', 'thx', 'ty', 'tks', 'tku', 'tq', 'tqvm'
                    ]
                    
                    # Check for any variation of "thank you" in the text
                    text_lower = user_text.lower().strip()
                    if any(phrase in text_lower for phrase in ['thank', 'thx', 'ty', 'tks', 'tku', 'tq']):
                        self.logger.debug(f"Filtered out thank you variation: '{user_text}'")
                        return
                    
                    if (len(user_text) < 3 or  # Reduced minimum length
                        user_text.lower().strip() in meaningless_responses or
                        user_text in ['.', '..', '...', ',', '!', '?'] or
                        len(user_text.strip()) == 0 or
                        text_lower in ['thank', 'thanks', 'thank you', 'thankyou']):  # Extra check for thank you
                        self.logger.debug(f"Filtered out short/meaningless response: '{user_text}'")
                        return  # Skip very short or meaningless responses
                    
                    # Publish user message event
                    self.event_bus.publish(EventTypes.USER_MESSAGE, {
                        "text": user_text,
                        "timestamp": time.time()
                    })
                    
                    # Get AI response in background
                    threading.Thread(target=self._get_ai_response, args=(user_text,), daemon=True).start()
                    
            except Exception as e:
                # Clean up temp file on error
                if temp_file and os.path.exists(temp_filename):
                    try:
                        os.unlink(temp_filename)
                    except:
                        pass
                raise e
                
        except Exception as e:
            self.logger.error(f"Audio processing error: {e}")
            self.event_bus.publish(EventTypes.AUDIO_ERROR, {"error": str(e)})
    
    def _get_ai_response(self, user_text: str):
        """Get AI response and convert to speech."""
        try:
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_text})
            
            # Keep only last 10 messages to avoid context overflow
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            # Prepare messages for API call
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Keep responses short and conversational."}
            ] + self.conversation_history
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=80,  # Reduced for faster responses
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Add AI response to history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Publish AI response event
            self.event_bus.publish(EventTypes.AI_RESPONSE, {
                "text": ai_response,
                "timestamp": time.time()
            })
            
            # Convert to speech
            self._text_to_speech(ai_response)
            
        except Exception as e:
            self.logger.error(f"AI response error: {e}")
            self.event_bus.publish(EventTypes.AI_ERROR, {"error": str(e)})
    
    def _text_to_speech(self, text: str):
        """Convert text to speech using ElevenLabs."""
        try:
            url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": config.elevenlabs_api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Save audio to temporary file and play
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name
                
                # Play audio using pygame
                self._play_audio(temp_file_path)
                
                # Publish TTS completion event
                self.event_bus.publish(EventTypes.TTS_COMPLETED, {
                    "text": text,
                    "timestamp": time.time()
                })
                
            else:
                self.logger.error(f"TTS API error: {response.status_code}")
                self.event_bus.publish(EventTypes.TTS_ERROR, {"error": f"API error: {response.status_code}"})
                
        except Exception as e:
            self.logger.error(f"TTS error: {e}")
            self.event_bus.publish(EventTypes.TTS_ERROR, {"error": str(e)})
    
    def _play_audio(self, file_path: str):
        """Play audio using pygame for background playback."""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.logger.debug(f"Playing audio: {file_path}")
            
            # Clean up the temp file after a short delay
            def cleanup():
                time.sleep(2)  # Wait for playback to start
                try:
                    os.unlink(file_path)
                except:
                    pass
            
            threading.Thread(target=cleanup, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
    
    def cleanup(self):
        """Clean up audio resources."""
        try:
            self.recording = False
            pygame.mixer.quit()
            self.audio.terminate()
            self.logger.info("VoiceLoop cleanup completed")
        except Exception as e:
            self.logger.error(f"VoiceLoop cleanup error: {e}")

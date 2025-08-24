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
from datetime import datetime
from io import BytesIO
import pygame
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from utils.logger import get_logger
from core.event_bus import EventBus, EventTypes
from config import config
from data.database import DatabaseManager


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
        
        # Audio configuration - balanced for responsiveness and accuracy
        self.config = AudioConfig(
            sample_rate=16000,
            chunk_size=1024,
            channels=1,
            silence_threshold=1.2,  # Slightly reduced for faster response
            min_speech_duration=0.4,  # Slightly reduced for more responsive detection
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
        
        # Database manager for logging
        self.db_manager = DatabaseManager()
        
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
            
            # Thresholds for speech detection (fine-tuned for better balance)
            rms_threshold = 35  # Lowered to catch more speech while filtering noise
            zcr_threshold = 0.08  # Lowered to be more sensitive to speech patterns
            # Check if audio meets speech criteria
            has_speech = rms > rms_threshold and zero_crossing_rate > zcr_threshold
            
            # Additional checks for different speech patterns (balanced approach)
            if rms > 70:  # Loud speech
                has_speech = True
            elif rms > 45 and zero_crossing_rate > 0.12:  # Medium speech with moderate ZCR
                has_speech = True
            elif rms > 30 and zero_crossing_rate > 0.18:  # Lower RMS but higher ZCR
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
                        file=audio_file,
                        language=config.learning.target_language  # Use configured target language
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
                    
                    # Additional filtering for random audio and noise
                    if (len(user_text) < 4 or  # Increased minimum length
                        user_text.lower().strip() in meaningless_responses or
                        user_text in ['.', '..', '...', ',', '!', '?'] or
                        len(user_text.strip()) == 0 or
                        text_lower in ['thank', 'thanks', 'thank you', 'thankyou'] or
                        # Filter out random character sequences and noise
                        len(set(user_text.lower())) < 3 or  # Too few unique characters
                        user_text.count(' ') > len(user_text) * 0.8 or  # Too many spaces
                        any(char.isdigit() for char in user_text) and len(user_text) < 10):  # Numbers in short text
                        self.logger.debug(f"Filtered out noise/random audio: '{user_text}'")
                        return  # Skip noise and random audio
                    
                    # Log user message if not in test mode
                    if not config.learning.test_mode:
                        self._log_conversation_message("user", "text", user_text, config.learning.target_language)
                    
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
            
            # Prepare messages for API call with language context
            target_lang = config.learning.target_language
            native_lang = config.learning.native_language
            
            # Create language-aware system prompt
            if target_lang != native_lang:
                system_prompt = f"You are an AI language tutor helping someone learn {self._get_language_name(target_lang)}. " \
                               f"The user's native language is {self._get_language_name(native_lang)}. " \
                               f"Respond in {self._get_language_name(target_lang)} and keep responses short and conversational. " \
                               f"Provide gentle corrections and encourage learning."
            else:
                system_prompt = "You are a helpful AI assistant. Keep responses short and conversational."
            
            messages = [
                {"role": "system", "content": system_prompt}
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
            
            # Log AI response if not in test mode
            if not config.learning.test_mode:
                self._log_conversation_message("ai", "text", ai_response, config.learning.target_language)
            
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
            # Select voice based on target language for better pronunciation
            voice_id = self._get_voice_for_language(config.learning.target_language)
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": config.elevenlabs_api_key
            }
            
            # Use multilingual model for better language support
            model_id = "eleven_multilingual_v2" if config.learning.target_language != "en" else "eleven_monolingual_v1"
            
            data = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": 0.7,  # Increased for more consistent pronunciation
                    "similarity_boost": 0.8,  # Increased for better voice quality
                    "style": 0.0,  # Neutral style for language learning
                    "use_speaker_boost": True,  # Enhance speaker clarity
                    "speaking_rate": 0.75  # Slow down speech rate (0.75 = 75% of normal speed)
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
    
    def _get_language_name(self, lang_code: str) -> str:
        """Convert language code to language name."""
        language_names = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish',
            'pl': 'Polish',
            'tr': 'Turkish',
            'el': 'Greek'
        }
        return language_names.get(lang_code, lang_code.upper())
    
    def _get_voice_for_language(self, lang_code: str) -> str:
        """Get the best ElevenLabs voice ID for the target language."""
        # ElevenLabs voice IDs optimized for different languages
        # These are high-quality voices that work well with the multilingual model
        voice_mapping = {
            'en': '21m00Tcm4TlvDq8ikWAM',  # Rachel - English
            'es': 'EXAVITQu4vr4xnSDxMaL',  # Bella - Spanish
            'fr': 'yoZ06aMxZJJ28mfd3POQ',  # Josh - French
            'de': 'AZnzlk1XvdvUeBnXmlld',  # Domi - German
            'it': 'pNInz6obpgDQGcFmaJgB',  # Adam - Italian
            'pt': 'VR6AewLTigWG4xSOukaG',  # Arnold - Portuguese
            'ru': 'VR6AewLTigWG4xSOukaG',  # Arnold - Russian (good for Slavic languages)
            'ja': 'VR6AewLTigWG4xSOukaG',  # Arnold - Japanese
            'ko': 'VR6AewLTigWG4xSOukaG',  # Arnold - Korean
            'zh': 'VR6AewLTigWG4xSOukaG',  # Arnold - Chinese
            'ar': 'VR6AewLTigWG4xSOukaG',  # Arnold - Arabic
            'hi': 'VR6AewLTigWG4xSOukaG',  # Arnold - Hindi
            'nl': 'VR6AewLTigWG4xSOukaG',  # Arnold - Dutch
            'sv': 'VR6AewLTigWG4xSOukaG',  # Arnold - Swedish
            'da': 'VR6AewLTigWG4xSOukaG',  # Arnold - Danish
            'no': 'VR6AewLTigWG4xSOukaG',  # Arnold - Norwegian
            'fi': 'VR6AewLTigWG4xSOukaG',  # Arnold - Finnish
            'pl': 'VR6AewLTigWG4xSOukaG',  # Arnold - Polish
            'tr': 'VR6AewLTigWG4xSOukaG',  # Arnold - Turkish
            'el': 'VR6AewLTigWG4xSOukaG'   # Arnold - Greek
        }
        return voice_mapping.get(lang_code, '21m00Tcm4TlvDq8ikWAM')  # Default to Rachel
    
    def cleanup(self):
        """Clean up audio resources."""
        try:
            self.recording = False
            pygame.mixer.quit()
            self.audio.terminate()
            self.logger.info("VoiceLoop cleanup completed")
        except Exception as e:
            self.logger.error(f"VoiceLoop cleanup error: {e}")
    
    def _log_conversation_message(self, sender: str, message_type: str, content: str, language: str):
        """Log a conversation message to the database."""
        try:
            # Get current session ID
            session_id = "test_session"  # Default for now
            # TODO: Get actual session ID from session manager
            
            self.db_manager.insert('conversation_messages', {
                'session_id': session_id,
                'sender': sender,
                'message_type': message_type,
                'content': content,
                'language': language,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.debug(f"Logged {sender} message: {content[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Error logging conversation message: {e}")

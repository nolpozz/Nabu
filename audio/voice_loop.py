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
    
    def __init__(self, event_bus: EventBus, session_manager=None):
        self.logger = get_logger(__name__)
        self.event_bus = event_bus
        self.session_manager = session_manager
        
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
            rms_threshold = 40  # Lowered to catch more speech while filtering noise
            zcr_threshold = 0.03  # Lowered to be more sensitive to speech patterns
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
                    
                    # Extract and add new vocabulary from user message
                    if self.session_manager:
                        self._extract_and_add_vocabulary(user_text)
                    
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
            
            # Create language-aware system prompt with learning context
            if target_lang != native_lang:
                # Get user's learning context from database
                user_context = self._get_user_learning_context()
                vocab_context = self._get_recent_vocabulary_context()
                
                # Check if user needs specific information and use tools
                tool_context = self._get_tool_context(user_text, user_context)
                
                # Prepare vocabulary context for the AI
                all_vocab = vocab_context.get('all_vocabulary', {})
                vocab_words = all_vocab.get('words', [])
                vocab_translations = all_vocab.get('translations', {})
                mastery_levels = all_vocab.get('mastery_levels', {})
                
                # Create vocabulary context string
                if vocab_words:
                    vocab_context_str = f"Available vocabulary ({len(vocab_words)} words): "
                    vocab_context_str += ", ".join([f"{word} ({vocab_translations.get(word, 'no translation')})" for word in vocab_words[:20]])  # Show first 20 words
                    if len(vocab_words) > 20:
                        vocab_context_str += f" ... and {len(vocab_words) - 20} more words"
                else:
                    vocab_context_str = "No vocabulary words learned yet"
                
                system_prompt = f"""You are Nabu, an advanced AI language tutor helping someone learn {self._get_language_name(target_lang)}. 

LEARNING CONTEXT:
- User's native language: {self._get_language_name(native_lang)}
- Current proficiency level: {user_context.get('proficiency_level', 'Beginner')}
- Learning style: {user_context.get('learning_style', 'Conversational')}
- Recent vocabulary focus: {vocab_context.get('recent_words', 'General conversation')}
- Areas of difficulty: {user_context.get('difficulties', 'None noted')}
- Total vocabulary words: {vocab_context.get('vocab_count', 0)}

VOCABULARY CONTEXT:
{vocab_context_str}

{tool_context}

TEACHING APPROACH:
- Respond primarily in {self._get_language_name(target_lang)} with occasional {self._get_language_name(native_lang)} explanations when needed
- Keep responses conversational and engaging (2-3 sentences max)
- Provide gentle, contextual corrections when appropriate
- Adapt difficulty based on user's responses
- Encourage active participation and questions
- Use real-world examples and cultural context when relevant

VOCABULARY INTEGRATION:
- Naturally introduce words from the user's vocabulary list above
- Prioritize words with lower mastery levels for reinforcement
- Reinforce recently learned words through repetition
- Provide context for new vocabulary usage
- Use vocabulary appropriate to the user's current level
- When introducing new words, provide brief translations in {self._get_language_name(native_lang)} if helpful

MEDIA PREFERENCES:
- If the user asks for media recommendations but has no preferences saved, ask about their interests
- Ask about movies, TV shows, music genres, podcasts, or books they enjoy
- Use their responses to provide personalized recommendations
- Encourage them to share what they like to watch, listen to, or read

Remember: You are a supportive, patient tutor focused on building confidence and practical language skills."""
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
    
    def _get_user_learning_context(self) -> Dict[str, Any]:
        """Get user's learning context from database."""
        try:
            # Get user profile information
            user_query = "SELECT proficiency_level, learning_goals FROM user_profile LIMIT 1"
            user_result = self.db_manager.execute_query(user_query)
            
            # Get recent session statistics
            session_query = """
                SELECT AVG(engagement_score) as avg_engagement, 
                       AVG(difficulty_level) as avg_difficulty,
                       COUNT(*) as total_sessions
                FROM learning_sessions 
                WHERE ended_at IS NOT NULL 
                ORDER BY ended_at DESC LIMIT 10
            """
            session_result = self.db_manager.execute_query(session_query)
            
            # Get recent vocabulary usage patterns
            vocab_query = """
                SELECT word, times_used, mastery_level 
                FROM vocabulary 
                WHERE language = ? 
                ORDER BY updated_at DESC LIMIT 5
            """
            vocab_result = self.db_manager.execute_query(vocab_query, (config.learning.target_language,))
            
            context = {
                'proficiency_level': user_result[0][0] if user_result else 'Beginner',
                'learning_style': 'Conversational',  # Default
                'difficulties': 'None noted',  # Default
                'avg_engagement': session_result[0][0] if session_result and session_result[0][0] else 0.5,
                'avg_difficulty': session_result[0][1] if session_result and session_result[0][1] else 1.0,
                'total_sessions': session_result[0][2] if session_result and session_result[0][2] else 0,
                'recent_vocab': [row[0] for row in vocab_result] if vocab_result else []
            }
            
            # Determine learning style based on engagement patterns
            if context['avg_engagement'] > 0.7:
                context['learning_style'] = 'Highly Engaged'
            elif context['avg_engagement'] > 0.4:
                context['learning_style'] = 'Moderately Engaged'
            else:
                context['learning_style'] = 'Needs Encouragement'
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting user learning context: {e}")
            return {
                'proficiency_level': 'Beginner',
                'learning_style': 'Conversational',
                'difficulties': 'None noted',
                'avg_engagement': 0.5,
                'avg_difficulty': 1.0,
                'total_sessions': 0,
                'recent_vocab': []
            }
    
    def _get_recent_vocabulary_context(self) -> Dict[str, Any]:
        """Get comprehensive vocabulary context for conversation."""
        try:
            # Get recently learned vocabulary
            recent_query = """
                SELECT word, translation, times_seen, mastery_level 
                FROM vocabulary 
                WHERE language = ? 
                ORDER BY updated_at DESC LIMIT 10
            """
            recent_result = self.db_manager.execute_query(recent_query, (config.learning.target_language,))
            
            # Get vocabulary that needs reinforcement
            reinforcement_query = """
                SELECT word, translation 
                FROM vocabulary 
                WHERE language = ? AND mastery_level < 0.5 
                ORDER BY RANDOM() LIMIT 5
            """
            reinforcement_result = self.db_manager.execute_query(reinforcement_query, (config.learning.target_language,))
            
            # Get ALL vocabulary words for the target language (for AI context)
            all_vocab_query = """
                SELECT word, translation, mastery_level, times_seen, times_used
                FROM vocabulary 
                WHERE language = ? 
                ORDER BY mastery_level ASC, times_seen ASC
            """
            all_vocab_result = self.db_manager.execute_query(all_vocab_query, (config.learning.target_language,))
            
            # Create comprehensive vocabulary context
            context = {
                'recent_words': [row[0] for row in recent_result[:5]] if recent_result else [],
                'recent_translations': {row[0]: row[1] for row in recent_result} if recent_result else {},
                'needs_reinforcement': [row[0] for row in reinforcement_result] if reinforcement_result else [],
                'vocab_count': len(all_vocab_result) if all_vocab_result else 0,
                # Full vocabulary list for AI context
                'all_vocabulary': {
                    'words': [row[0] for row in all_vocab_result] if all_vocab_result else [],
                    'translations': {row[0]: row[1] for row in all_vocab_result} if all_vocab_result else {},
                    'mastery_levels': {row[0]: row[2] for row in all_vocab_result} if all_vocab_result else {},
                    'usage_stats': {row[0]: {'seen': row[3], 'used': row[4]} for row in all_vocab_result} if all_vocab_result else {}
                }
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting vocabulary context: {e}")
            return {
                'recent_words': [],
                'recent_translations': {},
                'needs_reinforcement': [],
                'vocab_count': 0,
                'all_vocabulary': {
                    'words': [],
                    'translations': {},
                    'mastery_levels': {},
                    'usage_stats': {}
                }
            }
    
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
    
    def _get_tool_context(self, user_text: str, user_context: Dict[str, Any]) -> str:
        """Get additional context from tools based on user input."""
        tool_context = ""
        
        try:
            # Check if user is asking about specific vocabulary
            if self._needs_vocabulary_lookup(user_text):
                vocab_data = self._vocabulary_lookup_tool(user_text)
                if vocab_data:
                    tool_context += f"\nVOCABULARY LOOKUP: {vocab_data}\n"
            
            # Check if user is asking for media recommendations
            if self._needs_media_recommendation(user_text):
                media_data = self._media_recommendation_tool(user_text, user_context)
                if media_data:
                    tool_context += f"\nMEDIA RECOMMENDATIONS: {media_data}\n"
            
            # Check if user is asking for grammar help
            if self._needs_grammar_help(user_text):
                grammar_data = self._grammar_help_tool(user_text)
                if grammar_data:
                    tool_context += f"\nGRAMMAR HELP: {grammar_data}\n"
            
            # Check if user is sharing media preferences
            if self._is_sharing_media_preferences(user_text):
                self._save_media_preferences(user_text)
                tool_context += f"\nMEDIA PREFERENCES SAVED: User preferences have been recorded for future recommendations.\n"
                    
        except Exception as e:
            self.logger.error(f"Error getting tool context: {e}")
        
        return tool_context
    
    def _needs_vocabulary_lookup(self, user_text: str) -> bool:
        """Check if user is asking about specific vocabulary."""
        vocab_keywords = [
            'word', 'vocabulary', 'meaning', 'translate', 'translation', 
            'what does', 'how do you say', 'what is the word for',
            'palabra', 'vocabulario', 'significado', 'traducir',  # Spanish
            'mot', 'vocabulaire', 'signification', 'traduire',    # French
            'wort', 'vokabular', 'bedeutung', 'übersetzen'       # German
        ]
        user_lower = user_text.lower()
        return any(keyword in user_lower for keyword in vocab_keywords)
    
    def _needs_media_recommendation(self, user_text: str) -> bool:
        """Check if user is asking for media recommendations."""
        media_keywords = [
            'movie', 'film', 'song', 'music', 'video', 'media', 'practice',
            'recommend', 'suggestion', 'watch', 'listen', 'learn',
            'película', 'canción', 'música', 'video', 'recomendar',  # Spanish
            'film', 'chanson', 'musique', 'vidéo', 'recommander',    # French
            'film', 'lied', 'musik', 'video', 'empfehlen'           # German
        ]
        user_lower = user_text.lower()
        return any(keyword in user_lower for keyword in media_keywords)
    
    def _needs_grammar_help(self, user_text: str) -> bool:
        """Check if user is asking for grammar help."""
        grammar_keywords = [
            'grammar', 'sentence', 'structure', 'conjugation', 'tense',
            'grammatical', 'correct', 'incorrect', 'mistake', 'error',
            'gramática', 'oración', 'estructura', 'conjugación',     # Spanish
            'grammaire', 'phrase', 'structure', 'conjugaison',       # French
            'grammatik', 'satz', 'struktur', 'konjugation'          # German
        ]
        user_lower = user_text.lower()
        return any(keyword in user_lower for keyword in grammar_keywords)
    
    def _is_sharing_media_preferences(self, user_text: str) -> bool:
        """Check if user is sharing their media preferences."""
        preference_keywords = [
            'like', 'love', 'enjoy', 'favorite', 'prefer', 'watch', 'listen', 'read',
            'movie', 'film', 'show', 'series', 'tv', 'television', 'music', 'song', 'band',
            'podcast', 'book', 'genre', 'comedy', 'drama', 'action', 'romance', 'thriller',
            'documentary', 'sci-fi', 'fantasy', 'horror', 'rock', 'pop', 'jazz', 'classical',
            'me gusta', 'me encanta', 'favorito', 'prefiero', 'mirar', 'escuchar',  # Spanish
            'j\'aime', 'j\'adore', 'favori', 'préfère', 'regarder', 'écouter',      # French
            'mag', 'liebe', 'favorit', 'bevorzuge', 'schauen', 'hören'              # German
        ]
        user_lower = user_text.lower()
        return any(keyword in user_lower for keyword in preference_keywords)
    
    def _save_media_preferences(self, user_text: str):
        """Save user's media preferences to the database."""
        try:
            # Extract media preferences from user text
            preferences = self._extract_media_preferences(user_text)
            
            if preferences:
                # Update user profile with media preferences
                update_query = """
                    UPDATE user_profile 
                    SET media_preferences = ? 
                    WHERE id = (SELECT id FROM user_profile LIMIT 1)
                """
                self.db_manager.execute_query(update_query, (preferences,))
                self.logger.info(f"Saved media preferences: {preferences}")
                
        except Exception as e:
            self.logger.error(f"Error saving media preferences: {e}")
    
    def _extract_media_preferences(self, user_text: str) -> str:
        """Extract media preferences from user text."""
        try:
            import re
            
            # Define media categories and their keywords
            media_categories = {
                'movies': ['movie', 'film', 'cinema', 'película', 'film'],
                'tv_shows': ['show', 'series', 'tv', 'television', 'serie', 'télévision'],
                'music': ['music', 'song', 'band', 'artist', 'música', 'canción', 'musique', 'chanson'],
                'podcasts': ['podcast', 'audio', 'podcast'],
                'books': ['book', 'novel', 'reading', 'libro', 'livre', 'buch'],
                'genres': ['comedy', 'drama', 'action', 'romance', 'thriller', 'documentary', 
                          'sci-fi', 'fantasy', 'horror', 'rock', 'pop', 'jazz', 'classical',
                          'comedia', 'drama', 'acción', 'romance', 'thriller', 'documental',
                          'comédie', 'drame', 'action', 'romance', 'thriller', 'documentaire']
            }
            
            preferences = []
            user_lower = user_text.lower()
            
            # Extract mentioned media types and genres
            for category, keywords in media_categories.items():
                for keyword in keywords:
                    if keyword in user_lower:
                        # Get the context around the keyword
                        pattern = rf'\b\w*\s*\w*\s*{re.escape(keyword)}\s*\w*\s*\w*\b'
                        matches = re.findall(pattern, user_lower)
                        if matches:
                            preferences.extend(matches)
            
            # Clean and format preferences
            if preferences:
                # Remove duplicates and clean up
                unique_prefs = list(set([pref.strip() for pref in preferences if len(pref.strip()) > 2]))
                return ', '.join(unique_prefs[:10])  # Limit to 10 preferences
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error extracting media preferences: {e}")
            return ""
    
    def _vocabulary_lookup_tool(self, user_text: str) -> str:
        """Look up specific vocabulary word from user's database."""
        try:
            import re
            
            # Extract potential words from user text
            language = config.learning.target_language
            if language == 'ru':
                pattern = r'\b[а-яё]+\b'
            elif language == 'es':
                pattern = r'\b[a-záéíóúñü]+\b'
            elif language == 'fr':
                pattern = r'\b[a-zàâäéèêëïîôöùûüÿç]+\b'
            elif language == 'de':
                pattern = r'\b[a-zäöüß]+\b'
            else:
                pattern = r'\b[a-z]+\b'
            
            words = re.findall(pattern, user_text.lower())
            
            if not words:
                return ""
            
            # Look up the first word found
            word = words[0]
            query = """
                SELECT word, translation, mastery_level, times_seen, times_used 
                FROM vocabulary 
                WHERE word = ? AND language = ?
            """
            result = self.db_manager.execute_query(query, (word, language))
            
            if result:
                word_data = result[0]
                return f"Word: {word_data[0]}, Translation: {word_data[1]}, Mastery: {word_data[2]:.1%}, Seen: {word_data[3]}x, Used: {word_data[4]}x"
            else:
                return f"Word '{word}' not found in your vocabulary. Consider adding it!"
                
        except Exception as e:
            self.logger.error(f"Error in vocabulary lookup tool: {e}")
            return ""
    
    def _media_recommendation_tool(self, user_text: str, user_context: Dict[str, Any]) -> str:
        """Get media recommendations based on user's level and interests."""
        try:
            # Check if we have user media preferences
            preferences_query = """
                SELECT media_preferences FROM user_profile 
                WHERE media_preferences IS NOT NULL AND media_preferences != ''
                LIMIT 1
            """
            preferences_result = self.db_manager.execute_query(preferences_query)
            
            # If no preferences exist, return guidance for the AI to ask questions
            if not preferences_result or not preferences_result[0][0]:
                return "MEDIA PREFERENCES NEEDED: Ask the user about their media preferences (movies, TV shows, music genres, podcasts, books) to provide personalized recommendations."
            
            # Determine user's proficiency level for recommendations
            proficiency = user_context.get('proficiency_level', 'Beginner')
            level_mapping = {
                'Beginner': 1,
                'Intermediate': 2,
                'Advanced': 3
            }
            user_level = level_mapping.get(proficiency, 1)
            
            # Get media recommendations
            query = """
                SELECT title, type, difficulty_level, duration_minutes, description
                FROM media_recommendations 
                WHERE language = ? AND difficulty_level <= ?
                ORDER BY difficulty_level ASC, RANDOM()
                LIMIT 3
            """
            result = self.db_manager.execute_query(query, (config.learning.target_language, user_level))
            
            if result:
                recommendations = []
                for row in result:
                    title, media_type, level, duration, description = row
                    recommendations.append(f"{title} ({media_type}, {duration}min, level {level})")
                
                return f"Recommended for you: {'; '.join(recommendations)}"
            else:
                return "No media recommendations available for your level yet."
                
        except Exception as e:
            self.logger.error(f"Error in media recommendation tool: {e}")
            return ""
    
    def _grammar_help_tool(self, user_text: str) -> str:
        """Provide grammar help based on user's question."""
        try:
            # Simple grammar help based on keywords
            grammar_topics = {
                'conjugation': 'Focus on verb conjugations in present tense first, then past and future.',
                'tense': 'Start with present tense, then learn past tense, and finally future tense.',
                'sentence': 'Basic sentence structure: Subject + Verb + Object. Add adjectives before nouns.',
                'structure': 'Word order is important. In most cases: Subject comes first, verb second.',
                'grammar': 'Practice with simple sentences first, then gradually add complexity.',
                'conjugación': 'Enfócate en las conjugaciones de verbos en tiempo presente primero.',
                'tiempo': 'Comienza con el tiempo presente, luego aprende el pasado y finalmente el futuro.',
                'oración': 'Estructura básica: Sujeto + Verbo + Objeto. Los adjetivos van antes de los sustantivos.',
                'conjugaison': 'Concentrez-vous d\'abord sur les conjugaisons au présent.',
                'temps': 'Commencez par le présent, puis apprenez le passé et enfin le futur.'
            }
            
            user_lower = user_text.lower()
            for topic, help_text in grammar_topics.items():
                if topic in user_lower:
                    return help_text
            
            return "For grammar help, try asking about specific topics like 'conjugation', 'tense', or 'sentence structure'."
            
        except Exception as e:
            self.logger.error(f"Error in grammar help tool: {e}")
            return ""
    
    def _extract_and_add_vocabulary(self, text: str):
        """Extract vocabulary words from text and add to session."""
        try:
            import re
            
            # Language-specific word extraction patterns
            language = config.learning.target_language
            if language == 'ru':
                # Russian word pattern (Cyrillic characters)
                pattern = r'\b[а-яё]+\b'
            elif language == 'es':
                # Spanish word pattern
                pattern = r'\b[a-záéíóúñü]+\b'
            elif language == 'fr':
                # French word pattern
                pattern = r'\b[a-zàâäéèêëïîôöùûüÿç]+\b'
            elif language == 'de':
                # German word pattern
                pattern = r'\b[a-zäöüß]+\b'
            else:
                # Default: English-like pattern
                pattern = r'\b[a-z]+\b'
            
            # Extract words
            words = re.findall(pattern, text.lower())
            
            # Filter out common words and short words
            common_words = {
                'ru': {'и', 'в', 'не', 'на', 'я', 'быть', 'он', 'что', 'это', 'как'},
                'es': {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se'},
                'fr': {'le', 'la', 'de', 'et', 'à', 'un', 'être', 'etre', 'avoir', 'il'},
                'de': {'der', 'die', 'das', 'und', 'in', 'den', 'von', 'zu', 'mit', 'sich'},
                'en': {'the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that'}
            }
            
            filtered_words = [
                word for word in words 
                if len(word) > 2 and word not in common_words.get(language, common_words['en'])
            ]
            
            # Add unique words to session
            for word in set(filtered_words):
                if self.session_manager:
                    self.session_manager.add_new_vocabulary(word)
                    self.logger.debug(f"Added vocabulary word: {word}")
                    
        except Exception as e:
            self.logger.error(f"Error extracting vocabulary: {e}")

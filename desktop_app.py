import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import pyaudio
import wave
import numpy as np
from openai import OpenAI
import requests
import base64
import tempfile
import os
import time
from io import BytesIO
from dotenv import load_dotenv
import pygame

class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎤 AI Voice Assistant - Desktop")
        self.root.geometry("800x600")
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"800x600+{x}+{y}")
        
        # Load environment variables
        load_dotenv()
        
        # Get API Keys from environment variables
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        
        # Validate API keys
        if not self.openai_api_key or not self.elevenlabs_api_key:
            raise ValueError("Missing API keys! Please check your .env file.")
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        
        # Voice Activity Detection settings
        self.silence_threshold = 1.5  # seconds of silence to stop recording
        self.min_speech_duration = 0.5  # minimum speech duration before stopping
        
        # Audio processing
        self.audio = pyaudio.PyAudio()
        self.recording = False
        self.audio_queue = queue.Queue()
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        # OpenAI client
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Conversation history
        self.conversation_history = []
        
        # Debug mode for audio levels
        self.debug_audio = True  # Set to False to disable debug output
        
        self.setup_ui()
        self.setup_audio()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎤 AI Voice Assistant", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        self.record_button = ttk.Button(button_frame, text="🎤 Start Recording (Ctrl+R)", command=self.toggle_recording)
        self.record_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="🗑️ Clear (Ctrl+C)", command=self.clear_conversation)
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Add quit button
        self.quit_button = ttk.Button(button_frame, text="❌ Quit (Esc)", command=self.root.quit)
        self.quit_button.pack(side=tk.LEFT)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Click 'Start Recording' to begin", foreground="blue")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # Conversation display
        self.conversation_text = scrolledtext.ScrolledText(main_frame, height=20, width=80)
        self.conversation_text.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Audio playback info
        self.audio_label = ttk.Label(main_frame, text="Audio responses will play automatically")
        self.audio_label.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        # Add keyboard shortcuts
        self.root.bind('<Control-r>', lambda e: self.toggle_recording())
        self.root.bind('<Control-c>', lambda e: self.clear_conversation())
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
    def setup_audio(self):
        # Find default input device
        try:
            self.input_device = self.audio.get_default_input_device_info()['index']
            print(f"Using audio device: {self.audio.get_device_info_by_index(self.input_device)['name']}")
        except Exception as e:
            print(f"Error setting up audio device: {e}")
            # Try to find any available input device
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    self.input_device = i
                    print(f"Using fallback audio device: {device_info['name']}")
                    break
        
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        self.recording = True
        self.record_button.config(text="⏹️ Stop Recording")
        self.status_label.config(text="Recording... Speak now!", foreground="red")
        
        # Start continuous recording thread
        self.record_thread = threading.Thread(target=self.continuous_record_audio, daemon=True)
        self.record_thread.start()
        
    def stop_recording(self):
        self.recording = False
        self.record_button.config(text="🎤 Start Recording")
        self.status_label.config(text="Processing...", foreground="orange")
        
    def continuous_record_audio(self):
        """Continuous recording with voice activity detection"""
        try:
            stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.input_device,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            last_speech_time = time.time()
            speech_started = False
            
            while self.recording:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Check for speech activity every few chunks
                    if len(frames) % 4 == 0:  # Check every ~0.25 seconds
                        has_speech = self.has_speech_content(frames[-4:])  # Check last 4 chunks
                        
                        if has_speech:
                            if not speech_started:
                                speech_started = True
                                print("🎤 Speech detected - recording...")
                            last_speech_time = time.time()
                        elif speech_started:
                            # Check if we've been silent long enough
                            silence_duration = time.time() - last_speech_time
                            speech_duration = last_speech_time - (time.time() - len(frames) * self.chunk_size / self.sample_rate)
                            
                            if silence_duration >= self.silence_threshold and speech_duration >= self.min_speech_duration:
                                print(f"🔇 Silence detected ({silence_duration:.1f}s) - processing audio...")
                                # Process the recorded audio
                                if frames:
                                    threading.Thread(target=self.process_audio, args=(frames,), daemon=True).start()
                                frames = []
                                speech_started = False
                                last_speech_time = time.time()
                    
                except Exception as e:
                    print(f"Audio recording error: {e}")
                    break
            
            # Process any remaining audio when stopping
            if frames and speech_started:
                threading.Thread(target=self.process_audio, args=(frames,), daemon=True).start()
                    
            stream.stop_stream()
            stream.close()
                
        except Exception as e:
            print(f"Recording setup error: {e}")
            self.root.after(0, lambda: self.status_label.config(text=f"Recording error: {str(e)}", foreground="red"))
            
    def process_audio(self, frames):
        try:
            # Skip processing if frames are empty
            if not frames:
                return
                
            # Check if audio has meaningful content (not just silence/noise)
            # Set to False to disable audio filtering completely
            if self.debug_audio and not self.has_speech_content(frames):
                return  # Skip processing if no meaningful audio
            
            # Save audio to temporary file
            temp_file = None
            try:
                temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_filename = temp_file.name
                temp_file.close()
                
                with wave.open(temp_filename, 'wb') as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(self.audio.get_sample_size(self.audio_format))
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(b''.join(frames))
                
                # Transcribe with Whisper
                with open(temp_filename, 'rb') as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
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
                    
                    # Filter out very short or meaningless responses
                    if len(user_text) < 2 or user_text in ['.', '..', '...', ',', '!', '?']:
                        return  # Skip very short responses
                    
                    self.root.after(0, lambda: self.update_conversation(f"👤 You: {user_text}"))
                    self.root.after(0, lambda: self.status_label.config(text="Getting AI response...", foreground="orange"))
                    
                    # Get AI response in background
                    threading.Thread(target=self.get_ai_response, args=(user_text,), daemon=True).start()
                    
            except Exception as e:
                # Clean up temp file on error
                if temp_file and os.path.exists(temp_filename):
                    try:
                        os.unlink(temp_filename)
                    except:
                        pass
                raise e
                
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}", foreground="red"))
            print(f"Audio processing error: {e}")
    
    def has_speech_content(self, frames):
        """Check if audio frames contain meaningful speech content"""
        try:
            # Convert frames to numpy array
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            
            # Calculate RMS (Root Mean Square) to measure audio level
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Calculate zero crossing rate (indicates speech vs silence)
            zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
            zero_crossing_rate = zero_crossings / len(audio_data)
            
            # Thresholds for speech detection (very sensitive for quiet microphones)
            rms_threshold = 10  # Much lower for quiet microphones
            zcr_threshold = 0.001  # Much lower for speech detection
            
            # Check if audio meets speech criteria
            has_speech = rms > rms_threshold and zero_crossing_rate > zcr_threshold
            
            # Additional checks for different speech patterns
            if rms > 50:  # Lowered from 1000
                has_speech = True
            elif rms > 20 and zero_crossing_rate > 0.05:  # Moderate volume with speech-like patterns
                has_speech = True
            elif rms > 15 and zero_crossing_rate > 0.1:  # Even more sensitive for quiet speech
                has_speech = True
            
            if self.debug_audio:
                status = "PASS" if has_speech else "FILTERED"
                print(f"Audio {status} - RMS: {rms:.0f}, ZCR: {zero_crossing_rate:.4f}")
            
            return has_speech
            
        except Exception as e:
            print(f"Speech detection error: {e}")
            return True  # Default to processing if detection fails
            
    def get_ai_response(self, user_text):
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
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=100,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Add AI response to history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            self.root.after(0, lambda: self.update_conversation(f"🤖 AI: {ai_response}"))
            
            # Convert to speech
            self.text_to_speech(ai_response)
            
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"AI Error: {str(e)}", foreground="red"))
            print(f"AI response error: {e}")
            
    def text_to_speech(self, text):
        try:
            url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
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
                
                # Play audio using system default player
                self.play_audio(temp_file_path)
                self.root.after(0, lambda: self.status_label.config(text="Ready for next input", foreground="green"))
                
            else:
                self.root.after(0, lambda: self.status_label.config(text=f"TTS Error: {response.status_code}", foreground="red"))
                
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"TTS Error: {str(e)}", foreground="red"))
            print(f"TTS error: {e}")
            
    def play_audio(self, file_path):
        """Play audio using pygame for background playback"""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            print(f"Playing audio: {file_path}")
            
            # Clean up the temp file after a short delay
            def cleanup():
                time.sleep(2)  # Wait for playback to start
                try:
                    os.unlink(file_path)
                except:
                    pass
            
            threading.Thread(target=cleanup, daemon=True).start()
            
        except Exception as e:
            print(f"Audio playback error: {e}")
            # Fallback: try to open with default application
            try:
                import subprocess
                import platform
                if platform.system() == "Windows":
                    os.startfile(file_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["afplay", file_path])
                else:  # Linux
                    subprocess.run(["xdg-open", file_path])
            except:
                print("Could not play audio automatically.")
            
    def update_conversation(self, message):
        self.conversation_text.insert(tk.END, message + "\n\n")
        self.conversation_text.see(tk.END)
        
    def clear_conversation(self):
        self.conversation_text.delete(1.0, tk.END)
        self.conversation_history = []  # Clear conversation history
        
    def on_closing(self):
        self.recording = False
        self.audio.terminate()
        pygame.mixer.quit()
        self.root.destroy()

def main():
    try:
        root = tk.Tk()
        app = VoiceAssistantGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please check your .env file and ensure API keys are set correctly.")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()

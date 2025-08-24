"""
Conversation frame for the AI Language Tutor application.
Handles the main conversation interface and voice interaction.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any, List, Optional
import threading
import time

from utils.logger import get_logger
from core.event_bus import EventBus, EventTypes
from core.session_manager import SessionManager
from ui.theme import DarkTheme
from config import config


class ConversationFrame:
    """Main conversation interface."""
    
    def __init__(self, parent: tk.Widget, event_bus: EventBus, session_manager: SessionManager, voice_loop=None):
        self.logger = get_logger(__name__)
        self.parent = parent
        self.event_bus = event_bus
        self.session_manager = session_manager
        self.voice_loop = voice_loop  # Reference to the VoiceLoop instance
        self.theme = DarkTheme()
        
        # Conversation state
        self.messages: List[Dict[str, Any]] = []
        self.is_recording = False
        
        # Create main frame
        self.frame = self.theme.create_styled_frame(parent)
        
        # Initialize UI components
        self._setup_ui()
        self._setup_event_handlers()
        
        self.logger.info("Conversation frame initialized")
    
    def _setup_ui(self):
        """Setup the conversation UI components."""
        # Configure grid weights
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        
        # Title
        self.title_label = self.theme.create_styled_label(
            self.frame, 
            text="🎤 Nabu - AI Language Tutor",
            size='xl'
        )
        self.title_label.grid(row=0, column=0, pady=(self.theme.SPACING['lg'], self.theme.SPACING['md']))
        
        # Conversation area
        self.conversation_frame = self.theme.create_styled_frame(self.frame)
        self.conversation_frame.grid(row=1, column=0, sticky='nsew', padx=self.theme.SPACING['md'])
        self.conversation_frame.grid_columnconfigure(0, weight=1)
        self.conversation_frame.grid_rowconfigure(0, weight=1)
        
        # Text area for conversation
        self.conversation_text = scrolledtext.ScrolledText(
            self.conversation_frame,
            wrap=tk.WORD,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], self.theme.FONT_SIZES['base']),
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            insertbackground=self.theme.TEXT_PRIMARY,
            selectbackground=self.theme.ACCENT_BLUE,
            selectforeground=self.theme.TEXT_PRIMARY,
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.theme.BORDER_DEFAULT,
            highlightcolor=self.theme.ACCENT_BLUE,
            padx=self.theme.SPACING['lg'],
            pady=self.theme.SPACING['lg']
        )
        self.conversation_text.grid(row=0, column=0, sticky='nsew')
        
        # Control panel
        self.control_frame = self.theme.create_styled_frame(self.frame)
        self.control_frame.grid(row=2, column=0, sticky='ew', pady=(self.theme.SPACING['md'], 0))
        self.control_frame.grid_columnconfigure(1, weight=1)
        
        # Status label
        self.status_label = self.theme.create_styled_label(
            self.control_frame,
            text="Ready to start conversation",
            size='sm'
        )
        self.status_label.grid(row=0, column=0, columnspan=3, pady=(0, self.theme.SPACING['md']))
        
        # Control buttons
        self.record_button = self.theme.create_styled_button(
            self.control_frame,
            text="🎤 Start Recording",
            command=self._toggle_recording,
        )
        self.record_button.grid(row=1, column=0, padx=(0, self.theme.SPACING['sm']))
        
        self.end_session_button = self.theme.create_styled_button(
            self.control_frame,
            text="⏹️ End Session",
            command=self._end_session,
            style="primary"
        )
        self.record_button.grid(row=1, column=0, padx=(0, self.theme.SPACING['sm']))
        
        self.end_session_button = self.theme.create_styled_button(
            self.control_frame,
            text="⏹️ End Session",
            command=self._end_session,
            style="secondary"
        )
        self.end_session_button.grid(row=1, column=1, padx=self.theme.SPACING['sm'])
        
        self.clear_button = self.theme.create_styled_button(
            self.control_frame,
            text="🗑️ Clear",
            command=self._clear_conversation,
            style="secondary"
        )
        self.clear_button.grid(row=1, column=2, padx=(self.theme.SPACING['sm'], 0))
        
        # Test mode toggle
        self.test_mode_var = tk.BooleanVar(value=config.learning.test_mode)
        self.test_mode_checkbox = tk.Checkbutton(
            self.control_frame,
            text="🧪 Test Mode (no logging)",
            variable=self.test_mode_var,
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            selectcolor=self.theme.ELEVATED_BG,
            activebackground=self.theme.PRIMARY_BG,
            activeforeground=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], self.theme.FONT_SIZES['sm']),
            command=self._toggle_test_mode
        )
        self.test_mode_checkbox.grid(row=2, column=0, columnspan=3, pady=(self.theme.SPACING['sm'], 0), sticky='w')
        
        # Add welcome message
        self._add_system_message("Welcome to Nabu! Click 'Start Recording' to begin your conversation.")
    
    def _setup_event_handlers(self):
        """Setup event handlers for audio and session events."""
        # Audio events
        self.event_bus.subscribe(EventTypes.AUDIO_STARTED, self._on_audio_started)
        self.event_bus.subscribe(EventTypes.AUDIO_STOPPED, self._on_audio_stopped)
        self.event_bus.subscribe(EventTypes.AUDIO_ERROR, self._on_audio_error)
        
        # Message events
        self.event_bus.subscribe(EventTypes.USER_MESSAGE, self._on_user_message)
        self.event_bus.subscribe(EventTypes.AI_RESPONSE, self._on_ai_response)
        self.event_bus.subscribe(EventTypes.AI_ERROR, self._on_ai_error)
        
        # TTS events
        self.event_bus.subscribe(EventTypes.TTS_COMPLETED, self._on_tts_completed)
        self.event_bus.subscribe(EventTypes.TTS_ERROR, self._on_tts_error)
        
        # Session events
        self.event_bus.subscribe(EventTypes.SESSION_STARTED, self._on_session_started)
        self.event_bus.subscribe(EventTypes.SESSION_ENDED, self._on_session_ended)
    
    def _toggle_recording(self):
        """Toggle recording state."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """Start audio recording."""
        try:
            # Start a new session if not already active
            if not self.session_manager.get_current_session():
                session_id = self.session_manager.start_session(mode="conversation")
                self.logger.info(f"Started new session: {session_id}")
            
            # Start recording using the VoiceLoop instance
            if self.voice_loop and self.voice_loop.start_recording():
                self.is_recording = True
                self.record_button.config(text="⏸️ Stop Recording")
                self.status_label.config(text="Recording... Speak now!")
                self.logger.info("Recording started")
            else:
                self.status_label.config(text="Failed to start recording - VoiceLoop not available")
                
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self.status_label.config(text=f"Error: {str(e)}")
    
    def _stop_recording(self):
        """Stop audio recording."""
        try:
            if self.voice_loop and self.voice_loop.stop_recording():
                self.is_recording = False
                self.record_button.config(text="🎤 Start Recording")
                self.status_label.config(text="Processing...")
                self.logger.info("Recording stopped")
            else:
                self.status_label.config(text="Failed to stop recording - VoiceLoop not available")
                
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            self.status_label.config(text=f"Error: {str(e)}")
    
    def _end_session(self):
        """End the current session and generate notes."""
        try:
            if self.is_recording:
                self._stop_recording()
            
            current_session = self.session_manager.get_current_session()
            if current_session:
                session_id = self.session_manager.end_session()
                self._add_system_message(f"Session ended. Generating learning notes...")
                self.status_label.config(text="Session ended. Notes generated!")
                self.logger.info(f"Session ended: {current_session}")
                
                # Navigate back to dashboard after a short delay
                self.frame.after(2000, lambda: self.event_bus.publish(EventTypes.NAVIGATE_TO_DASHBOARD))
            else:
                self.status_label.config(text="No active session")
                
        except Exception as e:
            self.logger.error(f"Failed to end session: {e}")
            self.status_label.config(text=f"Error: {str(e)}")
    
    def _clear_conversation(self):
        """Clear the conversation display."""
        self.conversation_text.delete(1.0, tk.END)
        self.messages.clear()
        self._add_system_message("Conversation cleared. Ready to start new conversation.")
        self.logger.info("Conversation cleared")
    
    def _toggle_test_mode(self):
        """Toggle test mode on/off."""
        config.learning.test_mode = self.test_mode_var.get()
        status = "enabled" if config.learning.test_mode else "disabled"
        self._add_system_message(f"🧪 Test mode {status} - conversations will not be logged to database.")
        self.logger.info(f"Test mode {status}")
    
    def _add_message(self, sender: str, text: str, message_type: str = "user"):
        """Add a message to the conversation display."""
        timestamp = time.strftime("%H:%M:%S")
        
        # Format message
        if message_type == "user":
            formatted_message = f"[{timestamp}] 👤 You: {text}\n\n"
            color = self.theme.TEXT_PRIMARY
        elif message_type == "ai":
            formatted_message = f"[{timestamp}] 🤖 AI: {text}\n\n"
            color = self.theme.ACCENT_BLUE
        else:  # system
            formatted_message = f"[{timestamp}] ℹ️ {text}\n\n"
            color = self.theme.TEXT_SECONDARY
        
        # Add to text area
        self.conversation_text.insert(tk.END, formatted_message)
        
        # Apply color (basic implementation - could be enhanced with tags)
        # For now, we'll use the default color scheme
        
        # Auto-scroll to bottom
        self.conversation_text.see(tk.END)
        
        # Store message
        self.messages.append({
            "sender": sender,
            "text": text,
            "type": message_type,
            "timestamp": timestamp
        })
    
    def _add_system_message(self, text: str):
        """Add a system message to the conversation."""
        self._add_message("System", text, "system")
    
    # Event handlers
    def _on_audio_started(self, data: Dict[str, Any] = None):
        """Handle audio started event."""
        self.status_label.config(text="Recording... Speak now!")
    
    def _on_audio_stopped(self, data: Dict[str, Any] = None):
        """Handle audio stopped event."""
        self.status_label.config(text="Processing audio...")
    
    def _on_audio_error(self, data: Dict[str, Any] = None):
        """Handle audio error event."""
        error = data.get("error", "Unknown error") if data else "Unknown error"
        self.status_label.config(text=f"Audio Error: {error}")
        self._add_system_message(f"Audio Error: {error}")
    
    def _on_user_message(self, data: Dict[str, Any]):
        """Handle user message event."""
        text = data.get("text", "")
        if text:
            self._add_message("User", text, "user")
            # Track message for note generation
            self.session_manager.add_conversation_message("user", text)
            self.status_label.config(text="Getting AI response...")
    
    def _on_ai_response(self, data: Dict[str, Any]):
        """Handle AI response event."""
        text = data.get("text", "")
        if text:
            self._add_message("AI", text, "ai")
            # Track message for note generation
            self.session_manager.add_conversation_message("ai", text)
            self.status_label.config(text="Converting to speech...")
    
    def _on_ai_error(self, data: Dict[str, Any]):
        """Handle AI error event."""
        error = data.get("error", "Unknown error") if data else "Unknown error"
        self.status_label.config(text=f"AI Error: {error}")
        self._add_system_message(f"AI Error: {error}")
    
    def _on_tts_completed(self, data: Dict[str, Any]):
        """Handle TTS completed event."""
        self.status_label.config(text="Ready for next input")
    
    def _on_tts_error(self, data: Dict[str, Any]):
        """Handle TTS error event."""
        error = data.get("error", "Unknown error") if data else "Unknown error"
        self.status_label.config(text=f"TTS Error: {error}")
        self._add_system_message(f"TTS Error: {error}")
    
    def _on_session_started(self, data: Dict[str, Any]):
        """Handle session started event."""
        session_id = data.get("session_id", "unknown") if data else "unknown"
        self._add_system_message(f"Session started: {session_id}")
    
    def _on_session_ended(self, data: Dict[str, Any]):
        """Handle session ended event."""
        session_id = data.get("session_id", "unknown") if data else "unknown"
        self._add_system_message(f"Session ended: {session_id}")
    
    def pack(self, **kwargs):
        """Pack the conversation frame."""
        return self.frame.pack(**kwargs)
    
    def pack_forget(self):
        """Hide the conversation frame."""
        return self.frame.pack_forget()
    
    def grid(self, **kwargs):
        """Grid the conversation frame."""
        return self.frame.grid(**kwargs)
    
    def grid_forget(self):
        """Hide the conversation frame."""
        return self.frame.grid_forget()

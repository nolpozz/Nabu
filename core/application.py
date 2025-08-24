"""
Main application controller for the AI Language Tutor.
Orchestrates all application components and manages the application lifecycle.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Optional

from utils.logger import get_logger
from core.event_bus import EventBus, EventTypes
from core.session_manager import SessionManager
from audio.voice_loop import VoiceLoop
from agent.orchestrator import AgentOrchestrator
from data.database import DatabaseManager
from ui.theme import DarkTheme
from ui.tab_manager import TabManager
from ui.conversation import ConversationFrame
from config import config


class TutorApplication:
    """Main application controller."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("Initializing TutorApplication")
        
        # Initialize core components
        self.db_manager = DatabaseManager()
        self.event_bus = EventBus()
        self.session_manager = SessionManager(self.db_manager, self.event_bus)
        
        # Initialize audio and agent components first
        self.voice_loop: Optional[VoiceLoop] = None
        self.agent_orchestrator: Optional[AgentOrchestrator] = None
        
        # Initialize audio components before UI
        self._initialize_audio_components()
        self._initialize_ai_agent()
        
        # Initialize UI (which needs the audio components)
        self._initialize_ui()
        self._setup_event_handlers()
        
        self.logger.info("TutorApplication initialized successfully")
    
    def _initialize_ui(self):
        """Initialize UI components."""
        self.logger.info("Initializing UI components")
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("AI Language Tutor")
        self.root.geometry(f"{config.ui.window_width}x{config.ui.window_height}")
        
        # Add window identification
        self.root.wm_attributes("-topmost", False)
        self.root.focus_force()
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (config.ui.window_width // 2)
        y = (self.root.winfo_screenheight() // 2) - (config.ui.window_height // 2)
        self.root.geometry(f"{config.ui.window_width}x{config.ui.window_height}+{x}+{y}")
        
        # Apply theme
        self.theme = DarkTheme()
        self.theme.apply_to_window(self.root)
        
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create main content frame
        self.main_content = tk.Frame(self.root, bg=self.theme.PRIMARY_BG)
        self.main_content.grid(row=0, column=0, sticky='nsew')
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)
        
        # Create tab manager
        self.logger.info("Creating tab manager...")
        self.tab_manager = TabManager(
            self.main_content, 
            self.event_bus, 
            self.session_manager,
            self.db_manager
        )
        
        # Create conversation frame
        self.logger.info("Creating conversation frame...")
        self.conversation_frame = ConversationFrame(
            self.main_content,
            self.event_bus, 
            self.session_manager,
            voice_loop=self.voice_loop
        )
        
        # Show tabs initially (TabManager handles its own display)
        self.current_frame = self.tab_manager.main_container
        self.tab_manager.main_container.grid(row=0, column=0, sticky='nsew')
        
        # Hide conversation frame initially
        self.conversation_frame.frame.grid_remove()
        
        # Set window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.logger.info("UI components initialized")
    
    def _initialize_audio_components(self):
        """Initialize audio processing components."""
        self.logger.info("Initializing audio components")
        
        try:
            self.voice_loop = VoiceLoop(self.event_bus)
            self.logger.info("Audio components initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize audio components: {e}")
            # Continue without audio functionality
            self.voice_loop = None
    
    def _initialize_ai_agent(self):
        """Initialize AI agent components."""
        self.logger.info("Initializing AI agent")
        
        try:
            self.agent_orchestrator = AgentOrchestrator(self.event_bus, self.session_manager, self.db_manager)
            self.logger.info("AI agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI agent: {e}")
            # Continue without AI agent functionality
            self.agent_orchestrator = None
    
    def _setup_event_handlers(self):
        """Setup event handlers for navigation and application lifecycle."""
        self.logger.info("Setting up event handlers")
        
        # Navigation events
        self.event_bus.subscribe(EventTypes.NAVIGATE_TO_DASHBOARD, self._show_dashboard)
        self.event_bus.subscribe(EventTypes.NAVIGATE_TO_CONVERSATION, self._show_conversation)
        self.event_bus.subscribe(EventTypes.NAVIGATE_TO_TAB, self._navigate_to_tab)
        
        # Application lifecycle events
        self.event_bus.subscribe(EventTypes.APPLICATION_SHUTDOWN, self._shutdown)
        
        # Audio events - delegate to voice loop if available
        self.event_bus.subscribe(EventTypes.AUDIO_STARTED, self._on_audio_started)
        self.event_bus.subscribe(EventTypes.AUDIO_STOPPED, self._on_audio_stopped)
        
        self.logger.info("Event handlers set up")
    
    def _show_dashboard(self, data: dict = None):
        """Show the dashboard frame."""
        self.logger.info("Navigating to dashboard")
        
        # Hide current frame
        if self.current_frame:
            self.current_frame.grid_forget()
        
        # Show tab manager
        self.current_frame = self.tab_manager.main_container
        self.tab_manager.main_container.grid(row=0, column=0, sticky='nsew')
        
        # Refresh tab data
        self.tab_manager.refresh_current_tab()
    
    def _show_conversation(self, data: dict = None):
        """Show the conversation frame."""
        self.logger.info("Navigating to conversation")
        
        # Hide current frame
        if self.current_frame:
            self.current_frame.grid_forget()
        
        # Show conversation
        self.current_frame = self.conversation_frame.frame
        self.conversation_frame.frame.grid(row=0, column=0, sticky='nsew')
    
    def _navigate_to_tab(self, data: dict = None):
        """Navigate to a specific tab."""
        if data and 'tab' in data:
            tab_name = data['tab']
            self.logger.info(f"Navigating to tab: {tab_name}")
            
            # Show dashboard first if we're not already there
            if self.current_frame != self.tab_manager.main_container:
                self._show_dashboard()
            
            # Switch to the specific tab
            self.tab_manager.switch_to_tab(tab_name)
    
    def _on_audio_started(self, data: dict = None):
        """Handle audio started event."""
        self.logger.debug("Audio started")
        # Update conversation frame if it's the current frame
        if self.current_frame == self.conversation_frame.frame:
            self.conversation_frame._on_audio_started(data)
    
    def _on_audio_stopped(self, data: dict = None):
        """Handle audio stopped event."""
        self.logger.debug("Audio stopped")
        # Update conversation frame if it's the current frame
        if self.current_frame == self.conversation_frame.frame:
            self.conversation_frame._on_audio_stopped(data)
    
    def _shutdown(self, data: dict = None):
        """Handle application shutdown."""
        self.logger.info("Application shutdown requested")
        self.root.quit()
    
    def _on_closing(self):
        """Handle window closing."""
        self.logger.info("Window closing")
        self._cleanup()
        self.root.destroy()
    
    def run(self):
        """Start the application main loop."""
        self.logger.info("Starting application main loop")
        
        try:
            # Start background services
            self._start_background_services()
            
            # Start main loop
            self.root.mainloop()
            
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            self._cleanup()
    
    def _start_background_services(self):
        """Start background services."""
        self.logger.info("Starting background services")
        
        # Start session manager background tasks
        self.session_manager.start_background_tasks()
        
        # Start agent orchestrator background tasks
        if self.agent_orchestrator:
            self.agent_orchestrator.start_background_tasks()
    
    def _cleanup(self):
        """Clean up application resources."""
        self.logger.info("Cleaning up application resources")
        
        try:
            # Stop background services
            if self.agent_orchestrator:
                self.agent_orchestrator.stop_background_tasks()
            
            self.session_manager.stop_background_tasks()
            
            # Clean up audio resources
            if self.voice_loop:
                self.voice_loop.cleanup()
            
            # Close database connections
            if self.db_manager:
                self.db_manager.close()
            
            self.logger.info("Application cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

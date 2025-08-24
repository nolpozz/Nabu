"""
Dashboard frame for the AI Language Tutor application.
Shows learning statistics and provides navigation to conversation mode.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

from utils.logger import get_logger
from core.event_bus import EventBus, EventTypes
from core.session_manager import SessionManager
from .theme import DarkTheme
from config import config


class DashboardFrame:
    """Dashboard frame showing learning statistics and navigation."""
    
    def __init__(self, parent: tk.Widget, event_bus: EventBus, session_manager: SessionManager):
        self.parent = parent
        self.event_bus = event_bus
        self.session_manager = session_manager
        self.theme = DarkTheme()
        self.logger = get_logger(__name__)
        
        # Create the main frame
        self.frame = self.theme.create_styled_frame(parent)
        self.frame.configure(bg=self.theme.PRIMARY_BG)
        
        # Initialize UI components
        self._create_widgets()
        self._setup_layout()
        
        self.logger.info("Dashboard frame initialized")
        self.logger.info(f"Dashboard frame created with parent: {parent}")
        self.logger.info(f"Dashboard frame widget: {self.frame}")
    
    def _create_widgets(self):
        """Create dashboard widgets."""
        # Main content area (no sidebar needed)
        self.main_content = tk.Frame(
            self.frame,
            bg=self.theme.PRIMARY_BG,
            relief='flat',
            bd=0
        )
        
        # Welcome section
        self.welcome_frame = tk.Frame(self.main_content, bg=self.theme.PRIMARY_BG, relief='flat', bd=0)
        self.welcome_title = tk.Label(
            self.welcome_frame,
            text="Welcome, User",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 32, 'bold')
        )
        self.welcome_subtitle = tk.Label(
            self.welcome_frame,
            text="Your language learning journey continues here.",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_SECONDARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 16)
        )
        
        # Stats cards container
        self.stats_container = tk.Frame(self.main_content, bg=self.theme.PRIMARY_BG, relief='flat', bd=0)
        
        # Words Learned card
        self.words_card = tk.Frame(
            self.stats_container,
            bg=self.theme.ELEVATED_BG,
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=self.theme.BORDER_DEFAULT
        )
        
        self.words_icon = tk.Label(
            self.words_card,
            text="📚",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 24)
        )
        self.words_title = tk.Label(
            self.words_card,
            text="Words Learned",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 16, 'bold')
        )
        self.words_count = tk.Label(
            self.words_card,
            text="1,245",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 32, 'bold')
        )
        self.words_description = tk.Label(
            self.words_card,
            text="Total vocabulary acquired across all languages.",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_SECONDARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
            wraplength=200
        )
        
        # Conversation Stats card
        self.conversation_card = tk.Frame(
            self.stats_container,
            bg=self.theme.ELEVATED_BG,
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=self.theme.BORDER_DEFAULT
        )
        
        self.conversation_icon = tk.Label(
            self.conversation_card,
            text="📊",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 24)
        )
        self.conversation_title = tk.Label(
            self.conversation_card,
            text="Conversation Stats",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 16, 'bold')
        )
        self.conversation_count = tk.Label(
            self.conversation_card,
            text="124",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 32, 'bold')
        )
        self.conversation_subtitle = tk.Label(
            self.conversation_card,
            text="Total conversations",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_SECONDARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 14)
        )
        
        # Conversation stats details
        self.stats_details = tk.Frame(self.conversation_card, bg=self.theme.ELEVATED_BG, relief='flat', bd=0)
        
        self.avg_time_frame = tk.Frame(self.stats_details, bg=self.theme.ELEVATED_BG, relief='flat', bd=0)
        self.time_icon = tk.Label(
            self.avg_time_frame,
            text="⏱️",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_SECONDARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        )
        self.avg_time_text = tk.Label(
            self.avg_time_frame,
            text="Avg. 15.3 minutes",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_SECONDARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        )
        
        self.avg_words_frame = tk.Frame(self.stats_details, bg=self.theme.ELEVATED_BG, relief='flat', bd=0)
        self.words_icon_small = tk.Label(
            self.avg_words_frame,
            text="📝",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_SECONDARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        )
        self.avg_words_text = tk.Label(
            self.avg_words_frame,
            text="Avg. 28 new words",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_SECONDARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        )
        
        # Start Conversation button
        self.start_button = tk.Button(
            self.main_content,
            text="▶ Start Conversation",
            bg=self.theme.ACCENT_BLUE,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 16, 'bold'),
            relief='flat',
            bd=0,
            padx=40,
            pady=16,
            cursor='hand2',
            command=self._start_conversation
        )
    
    def _setup_layout(self):
        """Set up the dashboard layout."""
        self.logger.info("Setting up dashboard layout")
        
        # Main content (full width since sidebar is handled by TabManager)
        self.main_content.pack(fill='both', expand=True, padx=40, pady=20)
        self.main_content.grid_columnconfigure(0, weight=1)
        
        # Welcome section
        self.welcome_frame.pack(fill='x', pady=(0, 40))
        self.welcome_title.pack(anchor='w')
        self.welcome_subtitle.pack(anchor='w', pady=(5, 0))
        
        # Stats container
        self.stats_container.pack(fill='x', pady=(0, 40))
        self.stats_container.grid_columnconfigure(0, weight=1)
        self.stats_container.grid_columnconfigure(1, weight=1)
        
        # Words Learned card
        self.words_card.grid(row=0, column=0, sticky='ew', padx=(0, 15))
        self.words_card.grid_columnconfigure(0, weight=1)
        
        self.words_icon.grid(row=0, column=0, sticky='w', pady=(20, 10), padx=20)
        self.words_title.grid(row=1, column=0, sticky='w', pady=(0, 10), padx=20)
        self.words_count.grid(row=2, column=0, sticky='w', pady=(0, 10), padx=20)
        self.words_description.grid(row=3, column=0, sticky='w', pady=(0, 20), padx=20)
        
        # Conversation Stats card
        self.conversation_card.grid(row=0, column=1, sticky='ew', padx=(15, 0))
        self.conversation_card.grid_columnconfigure(0, weight=1)
        
        self.conversation_icon.grid(row=0, column=0, sticky='w', pady=(20, 10), padx=20)
        self.conversation_title.grid(row=1, column=0, sticky='w', pady=(0, 10), padx=20)
        self.conversation_count.grid(row=2, column=0, sticky='w', pady=(0, 5), padx=20)
        self.conversation_subtitle.grid(row=3, column=0, sticky='w', pady=(0, 15), padx=20)
        
        # Stats details
        self.stats_details.grid(row=4, column=0, sticky='w', pady=(0, 20), padx=20)
        
        self.avg_time_frame.pack(anchor='w', pady=(0, 5))
        self.time_icon.pack(side=tk.LEFT)
        self.avg_time_text.pack(side=tk.LEFT, padx=(5, 0))
        
        self.avg_words_frame.pack(anchor='w')
        self.words_icon_small.pack(side=tk.LEFT)
        self.avg_words_text.pack(side=tk.LEFT, padx=(5, 0))
        
        # Start Conversation button
        self.start_button.pack(pady=(0, 40))
        
        # Add hover effects to button
        self.start_button.bind('<Enter>', lambda e: self.start_button.configure(
            bg=self._lighten_color(self.theme.ACCENT_BLUE, 0.2)
        ))
        self.start_button.bind('<Leave>', lambda e: self.start_button.configure(
            bg=self.theme.ACCENT_BLUE
        ))
        self.start_button.bind('<Button-1>', lambda e: self.start_button.configure(
            bg=self._darken_color(self.theme.ACCENT_BLUE, 0.2)
        ))
        self.start_button.bind('<ButtonRelease-1>', lambda e: self.start_button.configure(
            bg=self._lighten_color(self.theme.ACCENT_BLUE, 0.2)
        ))
    
    def _lighten_color(self, color: str, factor: float) -> str:
        """Lighten a hex color by a factor."""
        # Convert hex to RGB
        color = color.lstrip('#')
        r, g, b = int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)
        
        # Lighten
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _darken_color(self, color: str, factor: float) -> str:
        """Darken a hex color by a factor."""
        # Convert hex to RGB
        color = color.lstrip('#')
        r, g, b = int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)
        
        # Darken
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _start_conversation(self):
        """Start a conversation session."""
        self.logger.info("Starting conversation session")
        
        # Start a new session
        session_id = self.session_manager.start_session(mode="conversation")
        
        # Navigate to conversation
        self.event_bus.publish(EventTypes.NAVIGATE_TO_CONVERSATION)
    
    def refresh_data(self):
        """Refresh dashboard data."""
        self.logger.debug("Refreshing dashboard data")
        
        # Get session statistics
        stats = self.session_manager.get_statistics()
        
        # Update conversation stats
        total_conversations = stats.get('total_sessions', 0)
        self.conversation_count.config(text=str(total_conversations))
        
        # Get real vocabulary stats from database
        try:
            # Count total vocabulary words for the current language
            vocab_query = "SELECT COUNT(*) FROM vocabulary WHERE language = ?"
            vocab_count = self.session_manager.db.execute_query(vocab_query, (config.learning.target_language,))
            total_vocab = vocab_count[0][0] if vocab_count else 0
            
            # Count mastered vocabulary (mastery_level >= 80%)
            mastered_query = "SELECT COUNT(*) FROM vocabulary WHERE language = ? AND mastery_level >= 80"
            mastered_count = self.session_manager.db.execute_query(mastered_query, (config.learning.target_language,))
            mastered_vocab = mastered_count[0][0] if mastered_count else 0
            
            # Update vocabulary stats
            self.words_count.config(text=str(total_vocab))
            self.words_description.config(text=f"Total vocabulary for {config.learning.target_language.upper()}. {mastered_vocab} words mastered.")
            
        except Exception as e:
            self.logger.error(f"Error loading vocabulary stats: {e}")
            # Fallback to placeholder
            self.words_count.config(text="0")
            self.words_description.config(text="Vocabulary data unavailable")
    
    def update_data(self, data: Dict[str, Any]):
        """Update dashboard with new data."""
        self.logger.debug(f"Updating dashboard with data: {list(data.keys())}")
        
        # Update specific components based on data
        if 'conversations' in data:
            self.conversation_count.config(text=str(data['conversations']))
        
        if 'vocabulary' in data:
            self.words_count.config(text=str(data['vocabulary']))
    
    def pack(self, **kwargs):
        """Pack the dashboard frame."""
        return self.frame.pack(**kwargs)
    
    def pack_forget(self):
        """Hide the dashboard frame."""
        return self.frame.pack_forget()
    
    def grid(self, **kwargs):
        """Grid the dashboard frame."""
        return self.frame.grid(**kwargs)
    
    def grid_forget(self):
        """Hide the dashboard frame."""
        return self.frame.grid_forget()
    
    def on_tab_activated(self):
        """Called when this tab is activated."""
        # Refresh dashboard data
        self.refresh_data()
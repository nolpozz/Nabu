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
    
    def _create_widgets(self):
        """Create dashboard widgets."""
        # Left sidebar
        self.sidebar = tk.Frame(
            self.frame,
            bg=self.theme.SURFACE_BG,
            width=250,
            relief='flat',
            bd=0
        )
        
        # Logo in sidebar
        self.logo_frame = tk.Frame(self.sidebar, bg=self.theme.SURFACE_BG, relief='flat', bd=0)
        self.logo_label = tk.Label(
            self.logo_frame,
            text="★ logo",
            bg=self.theme.SURFACE_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 18, 'bold')
        )
        
        # Navigation tabs
        self.nav_frame = tk.Frame(self.sidebar, bg=self.theme.SURFACE_BG, relief='flat', bd=0)
        
        # Navigation buttons with icons
        self.nav_buttons = {}
        nav_items = [
            ("📚 Vocab", "vocab"),
            ("💬 Media", "media"), 
            ("📝 Notes", "notes"),
            ("📖 Grammar", "grammar")
        ]
        
        for text, key in nav_items:
            btn = tk.Button(
                self.nav_frame,
                text=text,
                bg=self.theme.SURFACE_BG,
                fg=self.theme.TEXT_PRIMARY,
                font=(self.theme.FONT_FAMILY_PRIMARY[0], 14),
                relief='flat',
                bd=0,
                padx=20,
                pady=12,
                anchor='w',
                cursor='hand2'
            )
            self.nav_buttons[key] = btn
            
            # Highlight first item (Vocab) as active
            if key == "vocab":
                btn.configure(bg=self.theme.ELEVATED_BG)
        
        # Main content area
        self.main_content = tk.Frame(
            self.frame,
            bg=self.theme.PRIMARY_BG,
            relief='flat',
            bd=0
        )
        
        # Header
        self.header = tk.Frame(self.main_content, bg=self.theme.PRIMARY_BG, relief='flat', bd=0)
        # Header left: logo placeholder
        self.header_logo = tk.Label(
            self.header,
            text="logo",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 16, 'bold')
        )
        
        # Header right content (profile icon)
        self.header_right = tk.Frame(self.header, bg=self.theme.PRIMARY_BG, relief='flat', bd=0)
        self.profile_icon = tk.Label(
            self.header_right,
            text="👤",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 20)
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
        
        # Footer
        self.footer = tk.Frame(self.main_content, bg=self.theme.PRIMARY_BG, relief='flat', bd=0)
        
        self.footer_left = tk.Label(
            self.footer,
            text="Made with Yisily",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_MUTED,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        )
        
        self.footer_center = tk.Frame(self.footer, bg=self.theme.PRIMARY_BG, relief='flat', bd=0)
        footer_links = ["Resources", "Legal", "Contact Us"]
        for link in footer_links:
            link_label = tk.Label(
                self.footer_center,
                text=link,
                bg=self.theme.PRIMARY_BG,
                fg=self.theme.TEXT_MUTED,
                font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
                cursor='hand2'
            )
            link_label.pack(side=tk.LEFT, padx=10)
        
        self.footer_right = tk.Frame(self.footer, bg=self.theme.PRIMARY_BG, relief='flat', bd=0)
        social_icons = ["f", "🐦", "in"]
        for icon in social_icons:
            icon_label = tk.Label(
                self.footer_right,
                text=icon,
                bg=self.theme.PRIMARY_BG,
                fg=self.theme.TEXT_MUTED,
                font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
                cursor='hand2'
            )
            icon_label.pack(side=tk.LEFT, padx=5)
    
    def _setup_layout(self):
        """Set up the dashboard layout."""
        # Configure main frame grid
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)
        self.sidebar.grid_propagate(False)  # Maintain fixed width
        
        # Logo
        self.logo_frame.pack(fill='x', padx=20, pady=(20, 30))
        self.logo_label.pack(anchor='w')
        
        # Navigation
        self.nav_frame.pack(fill='x', padx=0, pady=0)
        for i, (key, btn) in enumerate(self.nav_buttons.items()):
            btn.pack(fill='x', padx=0, pady=0)
            # Add hover effects
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self.theme.ELEVATED_BG))
            btn.bind('<Leave>', lambda e, b=btn, k=key: b.configure(
                bg=self.theme.ELEVATED_BG if k == "vocab" else self.theme.SURFACE_BG
            ))
        
        # Main content
        self.main_content.grid(row=0, column=1, sticky='nsew', padx=40, pady=20)
        self.main_content.grid_columnconfigure(0, weight=1)
        
        # Header
        self.header.pack(fill='x', pady=(0, 20))
        self.header.grid_columnconfigure(0, weight=1)
        
        # Header contents: logo left, profile right
        self.header_logo.pack(side=tk.LEFT)
        self.profile_icon.pack(side=tk.RIGHT)
        
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
            bg=self.theme._lighten_color(self.theme.ACCENT_BLUE, 0.2)
        ))
        self.start_button.bind('<Leave>', lambda e: self.start_button.configure(
            bg=self.theme.ACCENT_BLUE
        ))
        self.start_button.bind('<Button-1>', lambda e: self.start_button.configure(
            bg=self.theme._darken_color(self.theme.ACCENT_BLUE, 0.2)
        ))
        self.start_button.bind('<ButtonRelease-1>', lambda e: self.start_button.configure(
            bg=self.theme._lighten_color(self.theme.ACCENT_BLUE, 0.2)
        ))
        
        # Footer
        self.footer.pack(fill='x', side=tk.BOTTOM)
        self.footer.grid_columnconfigure(1, weight=1)
        
        self.footer_left.grid(row=0, column=0, sticky='w')
        self.footer_center.grid(row=0, column=1)
        self.footer_right.grid(row=0, column=2, sticky='e')
    
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
        
        # TODO: Get vocabulary and other stats from database
        # For now, using placeholder data from the design
    
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

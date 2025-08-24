"""
Tab manager for the Nabu dashboard.
Handles navigation between different sections of the application.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional

from utils.logger import get_logger
from .theme import DarkTheme
from .dashboard import DashboardFrame
from .vocab_tab import VocabTab
from .media_tab import MediaTab
from .grammar_tab import GrammarTab
from .notes_tab import NotesTab
from core.event_bus import EventBus, EventTypes
from core.session_manager import SessionManager
from config import config


class TabManager:
    """Manages tabs for the Nabu dashboard with sidebar navigation."""
    
    def __init__(self, parent_frame: tk.Frame, event_bus: EventBus, session_manager: SessionManager, db_manager=None):
        self.parent_frame = parent_frame
        self.event_bus = event_bus
        self.session_manager = session_manager
        self.db_manager = db_manager
        self.logger = get_logger(__name__)
        self.theme = DarkTheme()
        
        # Main container
        self.main_container = None
        self.sidebar = None
        self.content_area = None
        self.tabs = {}
        self.tab_frames = {}  # Container frames for each tab
        self.current_tab = None
        self.nav_buttons = {}  # Initialize nav_buttons dictionary
        
        self._create_layout()
        self._setup_navigation()  # Setup navigation first
        self._create_tabs()       # Then create tabs
        self._show_tab('home')    # Finally show the home tab
    
    def _create_layout(self):
        """Create the main layout with sidebar and content area."""
        # Main container
        self.main_container = tk.Frame(self.parent_frame, bg=self.theme.PRIMARY_BG)
        self.main_container.pack(fill='both', expand=True)
        
        # Configure grid weights
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = tk.Frame(
            self.main_container,
            bg=self.theme.SURFACE_BG,
            width=250,
            relief='flat',
            bd=0
        )
        self.sidebar.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)
        self.sidebar.grid_propagate(False)  # Maintain fixed width
        
        # Content area
        self.content_area = tk.Frame(
            self.main_container,
            bg=self.theme.PRIMARY_BG,
            relief='flat',
            bd=0
        )
        self.content_area.grid(row=0, column=1, sticky='nsew', padx=0, pady=0)
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)
    
    def _create_tabs(self):
        """Create all the tab content."""
        # Create container frames for each tab
        self.tab_frames = {}
        
        # Home tab (Dashboard)
        self.tab_frames['home'] = tk.Frame(self.content_area, bg=self.theme.PRIMARY_BG)
        self.tab_frames['home'].grid(row=0, column=0, sticky='nsew')
        self.tab_frames['home'].grid_columnconfigure(0, weight=1)
        self.tab_frames['home'].grid_rowconfigure(0, weight=1)
        self.tabs['home'] = DashboardFrame(self.tab_frames['home'], self.event_bus, self.session_manager)
        self.tabs['home'].frame.pack(fill='both', expand=True)
        
        # Vocab tab
        self.tab_frames['vocab'] = tk.Frame(self.content_area, bg=self.theme.PRIMARY_BG)
        self.tab_frames['vocab'].grid(row=0, column=0, sticky='nsew')
        self.tab_frames['vocab'].grid_columnconfigure(0, weight=1)
        self.tab_frames['vocab'].grid_rowconfigure(0, weight=1)
        self.tabs['vocab'] = VocabTab(self.tab_frames['vocab'], self.event_bus, self.session_manager, self.db_manager)
        
        # Media tab
        self.tab_frames['media'] = tk.Frame(self.content_area, bg=self.theme.PRIMARY_BG)
        self.tab_frames['media'].grid(row=0, column=0, sticky='nsew')
        self.tab_frames['media'].grid_columnconfigure(0, weight=1)
        self.tab_frames['media'].grid_rowconfigure(0, weight=1)
        self.tabs['media'] = MediaTab(self.tab_frames['media'], self.event_bus, self.session_manager, self.db_manager)
        
        # Grammar tab
        self.tab_frames['grammar'] = tk.Frame(self.content_area, bg=self.theme.PRIMARY_BG)
        self.tab_frames['grammar'].grid(row=0, column=0, sticky='nsew')
        self.tab_frames['grammar'].grid_columnconfigure(0, weight=1)
        self.tab_frames['grammar'].grid_rowconfigure(0, weight=1)
        self.tabs['grammar'] = GrammarTab(self.tab_frames['grammar'], self.event_bus, self.session_manager, self.db_manager)
        
        # Notes tab
        self.tab_frames['notes'] = tk.Frame(self.content_area, bg=self.theme.PRIMARY_BG)
        self.tab_frames['notes'].grid(row=0, column=0, sticky='nsew')
        self.tab_frames['notes'].grid_columnconfigure(0, weight=1)
        self.tab_frames['notes'].grid_rowconfigure(0, weight=1)
        self.tabs['notes'] = NotesTab(self.tab_frames['notes'], self.event_bus, self.session_manager, self.db_manager)
        
        # Set default tab
        self.current_tab = 'home'
    
    def _setup_navigation(self):
        """Setup sidebar navigation."""
        # Logo in sidebar
        logo_frame = tk.Frame(self.sidebar, bg=self.theme.SURFACE_BG, relief='flat', bd=0)
        logo_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        logo_label = tk.Label(
            logo_frame,
            text="★ Nabu",
            bg=self.theme.SURFACE_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 18, 'bold')
        )
        logo_label.pack(anchor='w')
        
        # Language selector
        language_frame = tk.Frame(self.sidebar, bg=self.theme.SURFACE_BG, relief='flat', bd=0)
        language_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        language_label = tk.Label(
            language_frame,
            text="Language:",
            bg=self.theme.SURFACE_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12, 'bold')
        )
        language_label.pack(anchor='w', pady=(0, 5))
        
        language_var = tk.StringVar(value=config.learning.target_language)
        language_combo = ttk.Combobox(
            language_frame,
            textvariable=language_var,
            values=['ru', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'zh'],
            state='readonly',
            width=8,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        )
        language_combo.pack(anchor='w')
        language_combo.bind('<<ComboboxSelected>>', self._on_language_changed)
        
        # Navigation buttons
        nav_frame = tk.Frame(self.sidebar, bg=self.theme.SURFACE_BG, relief='flat', bd=0)
        nav_frame.pack(fill='x', padx=0, pady=0)
        
        # Navigation buttons with icons
        nav_items = [
            ("🏠 Home", "home"),
            ("📚 Vocab", "vocab"),
            ("💬 Media", "media"), 
            ("📝 Notes", "notes"),
            ("📖 Grammar", "grammar")
        ]
        
        for text, key in nav_items:
            btn = tk.Button(
                nav_frame,
                text=text,
                bg=self.theme.SURFACE_BG,
                fg=self.theme.TEXT_PRIMARY,
                font=(self.theme.FONT_FAMILY_PRIMARY[0], 14),
                relief='flat',
                bd=0,
                padx=20,
                pady=12,
                anchor='w',
                cursor='hand2',
                command=lambda k=key: self._navigate_to_tab(k)
            )
            self.nav_buttons[key] = btn
            btn.pack(fill='x', padx=0, pady=0)
            
            # Add hover effects
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self.theme.ELEVATED_BG))
            btn.bind('<Leave>', lambda e, b=btn, k=key: b.configure(
                bg=self.theme.ELEVATED_BG if k == "home" else self.theme.SURFACE_BG
            ))
        
        # Highlight Home as active initially
        self.nav_buttons['home'].configure(bg=self.theme.ELEVATED_BG)
        
        # Subscribe to navigation events
        self.event_bus.subscribe(EventTypes.NAVIGATE_TO_HOME, lambda _: self.switch_to_tab('home'))
        self.event_bus.subscribe(EventTypes.NAVIGATE_TO_VOCAB, lambda _: self.switch_to_tab('vocab'))
        self.event_bus.subscribe(EventTypes.NAVIGATE_TO_MEDIA, lambda _: self.switch_to_tab('media'))
        self.event_bus.subscribe(EventTypes.NAVIGATE_TO_GRAMMAR, lambda _: self.switch_to_tab('grammar'))
        self.event_bus.subscribe(EventTypes.NAVIGATE_TO_NOTES, lambda _: self.switch_to_tab('notes'))
    
    def _navigate_to_tab(self, tab_name: str):
        """Navigate to a specific tab."""
        self.logger.info(f"Navigating to tab: {tab_name}")
        self.switch_to_tab(tab_name)
    
    def _on_language_changed(self, event):
        """Handle language selection change."""
        new_language = event.widget.get()
        self.logger.info(f"Language changed to: {new_language}")
        
        # Update config
        config.learning.target_language = new_language
        
        # Publish event to notify other components
        self.event_bus.publish(EventTypes.LANGUAGE_CHANGED, {"language": new_language})
    
    def _show_tab(self, tab_name: str):
        """Show a specific tab and hide others."""
        # Hide all tab frames
        for tab_key, frame in self.tab_frames.items():
            frame.grid_remove()
        
        # Show the selected tab frame
        if tab_name in self.tab_frames:
            self.tab_frames[tab_name].grid(row=0, column=0, sticky='nsew')
            
            # Update button highlighting
            for key, btn in self.nav_buttons.items():
                btn.configure(bg=self.theme.ELEVATED_BG if key == tab_name else self.theme.SURFACE_BG)
    
    def switch_to_tab(self, tab_name: str):
        """Switch to a specific tab."""
        if tab_name in self.tabs:
            self.current_tab = tab_name
            self._show_tab(tab_name)
            self.logger.info(f"Switched to tab: {tab_name}")
            
            # Notify the tab that it's been activated
            if hasattr(self.tabs[tab_name], 'on_tab_activated'):
                self.tabs[tab_name].on_tab_activated()
    
    def refresh_current_tab(self):
        """Refresh the currently active tab."""
        if self.current_tab in self.tabs and hasattr(self.tabs[self.current_tab], 'refresh_data'):
            self.tabs[self.current_tab].refresh_data()
    
    def get_current_tab(self) -> str:
        """Get the name of the currently active tab."""
        return self.current_tab

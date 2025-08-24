"""
Vocabulary tab for the Nabu application.
Displays vocabulary words being learned with their translations and progress.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils.logger import get_logger
from .theme import DarkTheme
from core.event_bus import EventBus, EventTypes
from core.session_manager import SessionManager
from data.database import DatabaseManager
from config import config


class VocabTab:
    """Vocabulary tab component."""
    
    def __init__(self, parent_frame: tk.Frame, event_bus: EventBus, session_manager: SessionManager, db_manager=None):
        self.parent_frame = parent_frame
        self.event_bus = event_bus
        self.session_manager = session_manager
        self.logger = get_logger(__name__)
        self.theme = DarkTheme()
        self.db_manager = db_manager or DatabaseManager()
        
        # UI components
        self.vocab_list = None
        self.search_entry = None
        self.filter_combo = None
        self.add_word_frame = None
        
        self._create_ui()
        self._setup_event_handlers()
        self._load_vocabulary()
        
        # Subscribe to language change events
        self.event_bus.subscribe(EventTypes.LANGUAGE_CHANGED, self._on_language_changed)
    
    def on_tab_activated(self):
        """Called when this tab is activated."""
        self._load_vocabulary()
    
    def _create_ui(self):
        """Create the vocabulary tab UI."""
        # Main container
        main_frame = tk.Frame(self.parent_frame, bg=self.theme.PRIMARY_BG)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.theme.PRIMARY_BG)
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="📚 Vocabulary",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 24, 'bold')
        )
        title_label.pack(side='left')
        
        # Controls frame
        controls_frame = tk.Frame(main_frame, bg=self.theme.PRIMARY_BG)
        controls_frame.pack(fill='x', pady=(0, 20))
        
        # Search and filter
        search_frame = tk.Frame(controls_frame, bg=self.theme.PRIMARY_BG)
        search_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(
            search_frame,
            text="Search:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left', padx=(0, 10))
        
        self.search_entry = tk.Entry(
            search_frame,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            insertbackground=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=self.theme.BORDER_DEFAULT,
            highlightcolor=self.theme.ACCENT_BLUE
        )
        self.search_entry.pack(side='left', padx=(0, 20))
        self.search_entry.bind('<KeyRelease>', self._on_search)
        
        tk.Label(
            search_frame,
            text="Filter:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left', padx=(0, 10))
        
        self.filter_combo = ttk.Combobox(
            search_frame,
            values=['All', 'Learning', 'Review', 'Mastered'],
            state='readonly',
            width=12
        )
        self.filter_combo.set('All')
        self.filter_combo.pack(side='left', padx=(0, 20))
        self.filter_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Add word button
        add_button = tk.Button(
            controls_frame,
            text="➕ Add Word",
            bg=self.theme.ACCENT_BLUE,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12, 'bold'),
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._show_add_word_dialog
        )
        add_button.pack(side='right')
        
        # Vocabulary list
        list_frame = tk.Frame(main_frame, bg=self.theme.PRIMARY_BG)
        list_frame.pack(fill='both', expand=True)
        
        # Create Treeview for vocabulary
        columns = ('Word', 'Translation', 'Difficulty', 'Mastery', 'Times Seen', 'Times Used', 'Last Review')
        self.vocab_list = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        # Configure columns
        self.vocab_list.heading('Word', text='Word')
        self.vocab_list.heading('Translation', text='Translation')
        self.vocab_list.heading('Difficulty', text='Difficulty')
        self.vocab_list.heading('Mastery', text='Mastery %')
        self.vocab_list.heading('Times Seen', text='Times Seen')
        self.vocab_list.heading('Times Used', text='Times Used')
        self.vocab_list.heading('Last Review', text='Last Review')
        
        # Column widths
        self.vocab_list.column('Word', width=120)
        self.vocab_list.column('Translation', width=150)
        self.vocab_list.column('Difficulty', width=70)
        self.vocab_list.column('Mastery', width=70)
        self.vocab_list.column('Times Seen', width=80)
        self.vocab_list.column('Times Used', width=80)
        self.vocab_list.column('Last Review', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.vocab_list.yview)
        self.vocab_list.configure(yscrollcommand=scrollbar.set)
        
        # Pack list and scrollbar
        self.vocab_list.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to edit
        self.vocab_list.bind('<Double-1>', self._on_word_double_click)
        
        # Style the Treeview
        style = ttk.Style()
        style.configure('Treeview',
                       background=self.theme.ELEVATED_BG,
                       foreground=self.theme.TEXT_PRIMARY,
                       fieldbackground=self.theme.ELEVATED_BG,
                       rowheight=30)
        style.configure('Treeview.Heading',
                       background=self.theme.PRIMARY_BG,
                       foreground=self.theme.TEXT_PRIMARY,
                       relief='flat')
        style.map('Treeview',
                 background=[('selected', self.theme.ACCENT_BLUE)],
                 foreground=[('selected', self.theme.TEXT_PRIMARY)])
    
    def _setup_event_handlers(self):
        """Setup event handlers."""
        self.event_bus.subscribe(EventTypes.VOCABULARY_LEARNED, self._on_vocab_learned)
        self.event_bus.subscribe(EventTypes.VOCABULARY_REVIEWED, self._on_vocab_reviewed)
    
    def _load_vocabulary(self):
        """Load vocabulary from database with conversation statistics."""
        try:
            # Clear existing items
            for item in self.vocab_list.get_children():
                self.vocab_list.delete(item)
            
            # Get vocabulary with conversation statistics
            query = """
                SELECT v.word, v.translation, v.difficulty_level, v.mastery_level, 
                       v.last_reviewed,
                       COALESCE(seen_count.times_seen, 0) as times_seen,
                       COALESCE(used_count.times_used, 0) as times_used
                FROM vocabulary v
                LEFT JOIN (
                    SELECT content, COUNT(*) as times_seen
                    FROM conversation_messages 
                    WHERE sender = 'ai' AND language = ?
                    GROUP BY LOWER(content)
                ) seen_count ON LOWER(v.word) IN (LOWER(seen_count.content))
                LEFT JOIN (
                    SELECT content, COUNT(*) as times_used  
                    FROM conversation_messages
                    WHERE sender = 'user' AND language = ?
                    GROUP BY LOWER(content)
                ) used_count ON LOWER(v.word) IN (LOWER(used_count.content))
                WHERE v.language = ? 
                ORDER BY v.difficulty_level DESC, v.mastery_level ASC
            """
            
            results = self.db_manager.execute_query(
                query, 
                (config.learning.target_language, config.learning.target_language, config.learning.target_language)
            )
            
            for row in results:
                word, translation, difficulty, mastery, last_review, times_seen, times_used = row
                
                # Format dates
                last_review_str = last_review[:10] if last_review else 'Never'
                
                # Format mastery as percentage
                mastery_str = f"{mastery:.0f}%" if mastery else "0%"
                
                # Insert into treeview
                self.vocab_list.insert('', 'end', values=(
                    word, translation, difficulty, mastery_str, 
                    times_seen, times_used, last_review_str
                ))
            
            self.logger.info(f"Loaded {len(results)} vocabulary words for {config.learning.target_language}")
            
        except Exception as e:
            self.logger.error(f"Error loading vocabulary: {e}")
    
    def _on_search(self, event):
        """Handle search input."""
        search_term = self.search_entry.get().lower()
        self._filter_vocabulary(search_term, self.filter_combo.get())
    
    def _on_language_changed(self, data):
        """Handle language change events."""
        self.logger.info(f"Language changed to: {data.get('language', 'unknown')}")
        self._load_vocabulary()
    
    def _on_filter_changed(self, event):
        """Handle filter selection."""
        search_term = self.search_entry.get().lower()
        self._filter_vocabulary(search_term, self.filter_combo.get())
    
    def _filter_vocabulary(self, search_term: str, filter_type: str):
        """Filter vocabulary based on search term and filter type."""
        # This would implement filtering logic
        # For now, just reload all vocabulary
        self._load_vocabulary()
    
    def _show_add_word_dialog(self):
        """Show dialog to add a new word."""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Add New Word")
        dialog.geometry("400x300")
        dialog.configure(bg=self.theme.PRIMARY_BG)
        dialog.transient(self.parent_frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"400x300+{x}+{y}")
        
        # Form fields
        tk.Label(
            dialog,
            text="Word:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(pady=(20, 5))
        
        word_entry = tk.Entry(
            dialog,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
            width=30
        )
        word_entry.pack(pady=(0, 15))
        
        tk.Label(
            dialog,
            text="Translation:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(pady=(0, 5))
        
        translation_entry = tk.Entry(
            dialog,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
            width=30
        )
        translation_entry.pack(pady=(0, 15))
        
        tk.Label(
            dialog,
            text="Difficulty Level:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(pady=(0, 5))
        
        difficulty_combo = ttk.Combobox(
            dialog,
            values=['1', '2', '3', '4', '5'],
            state='readonly',
            width=10
        )
        difficulty_combo.set('1')
        difficulty_combo.pack(pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.theme.PRIMARY_BG)
        button_frame.pack(pady=20)
        
        def save_word():
            word = word_entry.get().strip()
            translation = translation_entry.get().strip()
            difficulty = int(difficulty_combo.get())
            
            if word and translation:
                try:
                    self.db_manager.insert('vocabulary', {
                        'word': word,
                        'translation': translation,
                        'language': config.learning.target_language,
                        'difficulty_level': difficulty,
                        'mastery_score': 0.0,
                        'created_at': datetime.now().isoformat()
                    })
                    self._load_vocabulary()
                    dialog.destroy()
                    self.logger.info(f"Added new word: {word}")
                except Exception as e:
                    self.logger.error(f"Error adding word: {e}")
        
        save_button = tk.Button(
            button_frame,
            text="Save",
            bg=self.theme.ACCENT_BLUE,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            command=save_word
        )
        save_button.pack(side='left', padx=(0, 10))
        
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            command=dialog.destroy
        )
        cancel_button.pack(side='left')
    
    def _on_word_double_click(self, event):
        """Handle double-click on a word to edit."""
        selection = self.vocab_list.selection()
        if selection:
            item = self.vocab_list.item(selection[0])
            values = item['values']
            if values:
                word = values[0]
                self.logger.info(f"Edit word: {word}")
                # TODO: Implement edit dialog
    
    def _on_vocab_learned(self, data: Dict[str, Any]):
        """Handle vocabulary learned event."""
        self._load_vocabulary()
    
    def _on_vocab_reviewed(self, data: Dict[str, Any]):
        """Handle vocabulary reviewed event."""
        self._load_vocabulary()
    
    def on_tab_activated(self):
        """Called when this tab is activated."""
        self._load_vocabulary()
    
    def refresh_data(self):
        """Refresh the vocabulary data."""
        self._load_vocabulary()

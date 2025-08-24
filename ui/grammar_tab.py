"""
Grammar tab for the Nabu application.
Displays grammar topics the user struggles with, including rules and examples.
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


class GrammarTab:
    """Grammar tab component."""
    
    def __init__(self, parent_frame: tk.Frame, event_bus: EventBus, session_manager: SessionManager, db_manager=None):
        self.parent_frame = parent_frame
        self.event_bus = event_bus
        self.session_manager = session_manager
        self.logger = get_logger(__name__)
        self.theme = DarkTheme()
        self.db_manager = db_manager or DatabaseManager()
        
        # UI components
        self.grammar_list = None
        self.search_entry = None
        self.filter_combo = None
        
        self._create_ui()
        self._setup_event_handlers()
        self._load_grammar_topics()
    
    def on_tab_activated(self):
        """Called when this tab is activated."""
        self._load_grammar_topics()
    
    def _create_ui(self):
        """Create the grammar tab UI."""
        # Main container
        main_frame = tk.Frame(self.parent_frame, bg=self.theme.PRIMARY_BG)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.theme.PRIMARY_BG)
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="📝 Grammar Topics",
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
            text="Difficulty:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left', padx=(0, 10))
        
        self.filter_combo = ttk.Combobox(
            search_frame,
            values=['All', 'Beginner', 'Intermediate', 'Advanced'],
            state='readonly',
            width=12
        )
        self.filter_combo.set('All')
        self.filter_combo.pack(side='left', padx=(0, 20))
        self.filter_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Add topic button
        add_button = tk.Button(
            controls_frame,
            text="➕ Add Topic",
            bg=self.theme.ACCENT_BLUE,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12, 'bold'),
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._show_add_topic_dialog
        )
        add_button.pack(side='right')
        
        # Grammar topics list
        list_frame = tk.Frame(main_frame, bg=self.theme.PRIMARY_BG)
        list_frame.pack(fill='both', expand=True)
        
        # Create Treeview for grammar topics
        columns = ('Topic', 'Difficulty', 'Mastery', 'Last Practiced', 'Next Review', 'Struggles')
        self.grammar_list = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        # Configure columns
        self.grammar_list.heading('Topic', text='Topic')
        self.grammar_list.heading('Difficulty', text='Difficulty')
        self.grammar_list.heading('Mastery', text='Mastery %')
        self.grammar_list.heading('Last Practiced', text='Last Practiced')
        self.grammar_list.heading('Next Review', text='Next Review')
        self.grammar_list.heading('Struggles', text='Struggles')
        
        # Column widths
        self.grammar_list.column('Topic', width=200)
        self.grammar_list.column('Difficulty', width=100)
        self.grammar_list.column('Mastery', width=80)
        self.grammar_list.column('Last Practiced', width=120)
        self.grammar_list.column('Next Review', width=120)
        self.grammar_list.column('Struggles', width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.grammar_list.yview)
        self.grammar_list.configure(yscrollcommand=scrollbar.set)
        
        # Pack list and scrollbar
        self.grammar_list.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to view details
        self.grammar_list.bind('<Double-1>', self._on_topic_double_click)
        
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
        pass  # No specific events for grammar tab yet
    
    def _load_grammar_topics(self):
        """Load grammar topics from database."""
        try:
            # Clear existing items
            for item in self.grammar_list.get_children():
                self.grammar_list.delete(item)
            
            # Get grammar topics from database
            query = """
                SELECT topic, difficulty_level, mastery_score, last_practiced, 
                       next_review, user_struggles
                FROM grammar_topics 
                WHERE language = ? 
                ORDER BY difficulty_level ASC, mastery_score ASC
            """
            
            results = self.db_manager.execute_query(
                query, 
                (config.learning.target_language,)
            )
            
            for row in results:
                topic, difficulty, mastery, last_practiced, next_review, struggles = row
                
                # Format dates
                last_practiced_str = last_practiced[:10] if last_practiced else 'Never'
                next_review_str = next_review[:10] if next_review else 'Due'
                
                # Format mastery as percentage
                mastery_str = f"{mastery:.0f}%" if mastery else "0%"
                
                # Format struggles (truncate if too long)
                struggles_str = struggles[:20] + "..." if struggles and len(struggles) > 20 else (struggles or "None")
                
                # Insert into treeview
                self.grammar_list.insert('', 'end', values=(
                    topic, difficulty, mastery_str, last_practiced_str, 
                    next_review_str, struggles_str
                ))
            
            self.logger.info(f"Loaded {len(results)} grammar topics")
            
        except Exception as e:
            self.logger.error(f"Error loading grammar topics: {e}")
    
    def _on_search(self, event):
        """Handle search input."""
        search_term = self.search_entry.get().lower()
        self._filter_topics(search_term, self.filter_combo.get())
    
    def _on_filter_changed(self, event):
        """Handle filter selection."""
        search_term = self.search_entry.get().lower()
        self._filter_topics(search_term, self.filter_combo.get())
    
    def _filter_topics(self, search_term: str, filter_type: str):
        """Filter grammar topics based on search term and filter type."""
        # This would implement filtering logic
        # For now, just reload all topics
        self._load_grammar_topics()
    
    def _show_add_topic_dialog(self):
        """Show dialog to add a new grammar topic."""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Add Grammar Topic")
        dialog.geometry("500x600")
        dialog.configure(bg=self.theme.PRIMARY_BG)
        dialog.transient(self.parent_frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"500x600+{x}+{y}")
        
        # Form fields
        tk.Label(
            dialog,
            text="Topic:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(pady=(20, 5))
        
        topic_entry = tk.Entry(
            dialog,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
            width=40
        )
        topic_entry.pack(pady=(0, 15))
        
        tk.Label(
            dialog,
            text="Description:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(pady=(0, 5))
        
        description_text = scrolledtext.ScrolledText(
            dialog,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 11),
            width=50,
            height=4,
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=self.theme.BORDER_DEFAULT,
            highlightcolor=self.theme.ACCENT_BLUE
        )
        description_text.pack(pady=(0, 15))
        
        tk.Label(
            dialog,
            text="Rules:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(pady=(0, 5))
        
        rules_text = scrolledtext.ScrolledText(
            dialog,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 11),
            width=50,
            height=3,
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=self.theme.BORDER_DEFAULT,
            highlightcolor=self.theme.ACCENT_BLUE
        )
        rules_text.pack(pady=(0, 15))
        
        tk.Label(
            dialog,
            text="Examples:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(pady=(0, 5))
        
        examples_text = scrolledtext.ScrolledText(
            dialog,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 11),
            width=50,
            height=3,
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=self.theme.BORDER_DEFAULT,
            highlightcolor=self.theme.ACCENT_BLUE
        )
        examples_text.pack(pady=(0, 15))
        
        # Difficulty frame
        difficulty_frame = tk.Frame(dialog, bg=self.theme.PRIMARY_BG)
        difficulty_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            difficulty_frame,
            text="Difficulty Level:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left', padx=(0, 10))
        
        difficulty_combo = ttk.Combobox(
            difficulty_frame,
            values=['1', '2', '3', '4', '5'],
            state='readonly',
            width=10
        )
        difficulty_combo.set('1')
        difficulty_combo.pack(side='left')
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.theme.PRIMARY_BG)
        button_frame.pack(pady=20)
        
        def save_topic():
            topic = topic_entry.get().strip()
            description = description_text.get(1.0, tk.END).strip()
            rules = rules_text.get(1.0, tk.END).strip()
            examples = examples_text.get(1.0, tk.END).strip()
            difficulty = int(difficulty_combo.get())
            
            if topic:
                try:
                    self.db_manager.insert('grammar_topics', {
                        'topic': topic,
                        'language': config.learning.target_language,
                        'difficulty_level': difficulty,
                        'description': description if description else None,
                        'rules': rules if rules else None,
                        'examples': examples if examples else None,
                        'mastery_score': 0.0
                    })
                    self._load_grammar_topics()
                    dialog.destroy()
                    self.logger.info(f"Added new grammar topic: {topic}")
                except Exception as e:
                    self.logger.error(f"Error adding grammar topic: {e}")
        
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
            command=save_topic
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
    
    def _on_topic_double_click(self, event):
        """Handle double-click on a grammar topic to view details."""
        selection = self.grammar_list.selection()
        if selection:
            item = self.grammar_list.item(selection[0])
            values = item['values']
            if values:
                topic = values[0]
                self.logger.info(f"View grammar topic details: {topic}")
                self._show_topic_details(topic)
    
    def _show_topic_details(self, topic: str):
        """Show detailed view of a grammar topic."""
        try:
            # Get topic details from database
            query = """
                SELECT topic, difficulty_level, description, examples, rules,
                       user_struggles, mastery_score, last_practiced, next_review, notes
                FROM grammar_topics 
                WHERE topic = ? AND language = ?
            """
            
            results = self.db_manager.execute_query(query, (topic, config.learning.target_language))
            
            if results:
                row = results[0]
                self._show_topic_dialog(row)
            else:
                self.logger.warning(f"Grammar topic not found: {topic}")
                
        except Exception as e:
            self.logger.error(f"Error loading grammar topic details: {e}")
    
    def _show_topic_dialog(self, topic_data):
        """Show grammar topic details dialog."""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title(f"Grammar Topic - {topic_data[0]}")
        dialog.geometry("700x600")
        dialog.configure(bg=self.theme.PRIMARY_BG)
        dialog.transient(self.parent_frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"700x600+{x}+{y}")
        
        # Title
        title_label = tk.Label(
            dialog,
            text=topic_data[0],
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 18, 'bold')
        )
        title_label.pack(pady=(20, 10))
        
        # Info frame
        info_frame = tk.Frame(dialog, bg=self.theme.PRIMARY_BG)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        # Difficulty and mastery
        diff_mastery_frame = tk.Frame(info_frame, bg=self.theme.PRIMARY_BG)
        diff_mastery_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            diff_mastery_frame,
            text=f"Difficulty: {topic_data[1]}/5",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left', padx=(0, 20))
        
        mastery_str = f"{topic_data[6]:.0f}%" if topic_data[6] else "0%"
        tk.Label(
            diff_mastery_frame,
            text=f"Mastery: {mastery_str}",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left')
        
        # Description
        if topic_data[2]:  # description
            tk.Label(
                dialog,
                text="Description:",
                bg=self.theme.PRIMARY_BG,
                fg=self.theme.TEXT_PRIMARY,
                font=(self.theme.FONT_FAMILY_PRIMARY[0], 14, 'bold'),
                anchor='w'
            ).pack(anchor='w', padx=20, pady=(20, 5))
            
            description_text = scrolledtext.ScrolledText(
                dialog,
                bg=self.theme.ELEVATED_BG,
                fg=self.theme.TEXT_PRIMARY,
                font=(self.theme.FONT_FAMILY_PRIMARY[0], 11),
                width=70,
                height=3,
                relief='flat',
                bd=1,
                highlightthickness=1,
                highlightbackground=self.theme.BORDER_DEFAULT,
                state='normal'
            )
            description_text.pack(padx=20, pady=(0, 20), fill='x')
            description_text.insert(1.0, topic_data[2])
            description_text.config(state='disabled')
        
        # Rules
        if topic_data[4]:  # rules
            tk.Label(
                dialog,
                text="Rules:",
                bg=self.theme.PRIMARY_BG,
                fg=self.theme.TEXT_PRIMARY,
                font=(self.theme.FONT_FAMILY_PRIMARY[0], 14, 'bold'),
                anchor='w'
            ).pack(anchor='w', padx=20, pady=(0, 5))
            
            rules_text = scrolledtext.ScrolledText(
                dialog,
                bg=self.theme.ELEVATED_BG,
                fg=self.theme.TEXT_PRIMARY,
                font=(self.theme.FONT_FAMILY_PRIMARY[0], 11),
                width=70,
                height=3,
                relief='flat',
                bd=1,
                highlightthickness=1,
                highlightbackground=self.theme.BORDER_DEFAULT,
                state='normal'
            )
            rules_text.pack(padx=20, pady=(0, 20), fill='x')
            rules_text.insert(1.0, topic_data[4])
            rules_text.config(state='disabled')
        
        # Examples
        if topic_data[3]:  # examples
            tk.Label(
                dialog,
                text="Examples:",
                bg=self.theme.PRIMARY_BG,
                fg=self.theme.TEXT_PRIMARY,
                font=(self.theme.FONT_FAMILY_PRIMARY[0], 14, 'bold'),
                anchor='w'
            ).pack(anchor='w', padx=20, pady=(0, 5))
            
            examples_text = scrolledtext.ScrolledText(
                dialog,
                bg=self.theme.ELEVATED_BG,
                fg=self.theme.TEXT_PRIMARY,
                font=(self.theme.FONT_FAMILY_PRIMARY[0], 11),
                width=70,
                height=3,
                relief='flat',
                bd=1,
                highlightthickness=1,
                highlightbackground=self.theme.BORDER_DEFAULT,
                state='normal'
            )
            examples_text.pack(padx=20, pady=(0, 20), fill='x')
            examples_text.insert(1.0, topic_data[3])
            examples_text.config(state='disabled')
        
        # Close button
        close_button = tk.Button(
            dialog,
            text="Close",
            bg=self.theme.ACCENT_BLUE,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
            relief='flat',
            bd=0,
            padx=30,
            pady=10,
            command=dialog.destroy
        )
        close_button.pack(pady=20)
    
    def on_tab_activated(self):
        """Called when this tab is activated."""
        self._load_grammar_topics()
    
    def refresh_data(self):
        """Refresh the grammar topics data."""
        self._load_grammar_topics()

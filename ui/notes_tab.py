"""
Notes tab for the Nabu application.
Displays user notes for language learning with categories and priority levels.
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


class NotesTab:
    """Notes tab component."""
    
    def __init__(self, parent_frame: tk.Frame, event_bus: EventBus, session_manager: SessionManager, db_manager=None):
        self.parent_frame = parent_frame
        self.event_bus = event_bus
        self.session_manager = session_manager
        self.logger = get_logger(__name__)
        self.theme = DarkTheme()
        self.db_manager = db_manager or DatabaseManager()
        
        # UI components
        self.notes_list = None
        self.search_entry = None
        self.filter_combo = None
        
        self._create_ui()
        self._setup_event_handlers()
        self._load_notes()
        
        # Subscribe to language change events
        self.event_bus.subscribe(EventTypes.LANGUAGE_CHANGED, self._on_language_changed)
    
    def on_tab_activated(self):
        """Called when this tab is activated."""
        self._load_notes()
    
    def _create_ui(self):
        """Create the notes tab UI."""
        # Main container
        main_frame = tk.Frame(self.parent_frame, bg=self.theme.PRIMARY_BG)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.theme.PRIMARY_BG)
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="📖 Notes",
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
            text="Category:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left', padx=(0, 10))
        
        self.filter_combo = ttk.Combobox(
            search_frame,
            values=['All', 'General', 'Grammar', 'Vocabulary', 'Pronunciation', 'Culture'],
            state='readonly',
            width=12
        )
        self.filter_combo.set('All')
        self.filter_combo.pack(side='left', padx=(0, 20))
        self.filter_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Add note button
        add_button = tk.Button(
            controls_frame,
            text="➕ Add Note",
            bg=self.theme.ACCENT_BLUE,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12, 'bold'),
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._show_add_note_dialog
        )
        add_button.pack(side='right')
        
        # Notes list
        list_frame = tk.Frame(main_frame, bg=self.theme.PRIMARY_BG)
        list_frame.pack(fill='both', expand=True)
        
        # Create Treeview for notes
        columns = ('Title', 'Category', 'Priority', 'Created', 'Updated', 'Tags')
        self.notes_list = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        # Configure columns
        self.notes_list.heading('Title', text='Title')
        self.notes_list.heading('Category', text='Category')
        self.notes_list.heading('Priority', text='Priority')
        self.notes_list.heading('Created', text='Created')
        self.notes_list.heading('Updated', text='Updated')
        self.notes_list.heading('Tags', text='Tags')
        
        # Column widths
        self.notes_list.column('Title', width=200)
        self.notes_list.column('Category', width=100)
        self.notes_list.column('Priority', width=80)
        self.notes_list.column('Created', width=100)
        self.notes_list.column('Updated', width=100)
        self.notes_list.column('Tags', width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.notes_list.yview)
        self.notes_list.configure(yscrollcommand=scrollbar.set)
        
        # Pack list and scrollbar
        self.notes_list.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to view details
        self.notes_list.bind('<Double-1>', self._on_note_double_click)
        
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
        pass  # No specific events for notes tab yet
    
    def _load_notes(self):
        """Load notes from database."""
        try:
            # Clear existing items
            for item in self.notes_list.get_children():
                self.notes_list.delete(item)
            
            # Get notes from database - filter by language
            current_language = config.learning.target_language
            
            # Language-specific filtering logic
            if current_language == 'ru':
                # Russian notes
                query = """
                    SELECT title, content, tags, created_at, updated_at
                    FROM user_notes 
                    WHERE title LIKE '%Russian%' OR content LIKE '%Russian%' OR tags LIKE '%russian%'
                    ORDER BY created_at DESC
                """
            elif current_language == 'es':
                # Spanish notes
                query = """
                    SELECT title, content, tags, created_at, updated_at
                    FROM user_notes 
                    WHERE title LIKE '%Spanish%' OR content LIKE '%Spanish%' OR tags LIKE '%spanish%'
                    ORDER BY created_at DESC
                """
            elif current_language == 'fr':
                # French notes
                query = """
                    SELECT title, content, tags, created_at, updated_at
                    FROM user_notes 
                    WHERE title LIKE '%French%' OR content LIKE '%French%' OR tags LIKE '%french%'
                    ORDER BY created_at DESC
                """
            elif current_language == 'de':
                # German notes
                query = """
                    SELECT title, content, tags, created_at, updated_at
                    FROM user_notes 
                    WHERE title LIKE '%German%' OR content LIKE '%German%' OR tags LIKE '%german%'
                    ORDER BY created_at DESC
                """
            elif current_language == 'ja':
                # Japanese notes
                query = """
                    SELECT title, content, tags, created_at, updated_at
                    FROM user_notes 
                    WHERE title LIKE '%Japanese%' OR content LIKE '%Japanese%' OR tags LIKE '%japanese%'
                    ORDER BY created_at DESC
                """
            elif current_language == 'zh':
                # Chinese notes
                query = """
                    SELECT title, content, tags, created_at, updated_at
                    FROM user_notes 
                    WHERE title LIKE '%Chinese%' OR content LIKE '%Chinese%' OR tags LIKE '%chinese%'
                    ORDER BY created_at DESC
                """
            else:
                # Default: show all notes
                query = """
                    SELECT title, content, tags, created_at, updated_at
                    FROM user_notes 
                    ORDER BY created_at DESC
                """
            
            results = self.db_manager.execute_query(query)
            
            for row in results:
                title, content, tags, created_at, updated_at = row
                
                # Format dates
                created_str = created_at[:10] if created_at else 'Unknown'
                updated_str = updated_at[:10] if updated_at else 'Never'
                
                # Use content as category for now (first 20 chars)
                category = content[:20] + "..." if content and len(content) > 20 else (content or "General")
                
                # Default priority to Low
                priority_str = 'Low'
                
                # Format tags (truncate if too long)
                tags_str = tags[:20] + "..." if tags and len(tags) > 20 else (tags or "None")
                
                # Insert into treeview
                self.notes_list.insert('', 'end', values=(
                    title, category, priority_str, created_str, updated_str, tags_str
                ))
            
            self.logger.info(f"Loaded {len(results)} notes")
            
        except Exception as e:
            self.logger.error(f"Error loading notes: {e}")
    
    def _on_search(self, event):
        """Handle search input."""
        search_term = self.search_entry.get().lower()
        self._filter_notes(search_term, self.filter_combo.get())
    
    def _on_filter_changed(self, event):
        """Handle filter selection."""
        search_term = self.search_entry.get().lower()
        self._filter_notes(search_term, self.filter_combo.get())
    
    def _on_language_changed(self, data):
        """Handle language change events."""
        self.logger.info(f"Language changed to: {data.get('language', 'unknown')}")
        self._load_notes()
    
    def _filter_notes(self, search_term: str, filter_type: str):
        """Filter notes based on search term and filter type."""
        # This would implement filtering logic
        # For now, just reload all notes
        self._load_notes()
    
    def _show_add_note_dialog(self):
        """Show dialog to add a new note."""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Add New Note")
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
            text="Title:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(pady=(20, 5))
        
        title_entry = tk.Entry(
            dialog,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
            width=40
        )
        title_entry.pack(pady=(0, 15))
        
        # Category and priority frame
        cat_pri_frame = tk.Frame(dialog, bg=self.theme.PRIMARY_BG)
        cat_pri_frame.pack(fill='x', pady=(0, 15))
        
        # Category
        cat_frame = tk.Frame(cat_pri_frame, bg=self.theme.PRIMARY_BG)
        cat_frame.pack(side='left', padx=(0, 20))
        
        tk.Label(
            cat_frame,
            text="Category:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(anchor='w')
        
        category_combo = ttk.Combobox(
            cat_frame,
            values=['General', 'Grammar', 'Vocabulary', 'Pronunciation', 'Culture'],
            state='readonly',
            width=15
        )
        category_combo.set('General')
        category_combo.pack(pady=(5, 0))
        
        # Priority
        pri_frame = tk.Frame(cat_pri_frame, bg=self.theme.PRIMARY_BG)
        pri_frame.pack(side='left')
        
        tk.Label(
            pri_frame,
            text="Priority:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(anchor='w')
        
        priority_combo = ttk.Combobox(
            pri_frame,
            values=['Low', 'Medium', 'High'],
            state='readonly',
            width=10
        )
        priority_combo.set('Medium')
        priority_combo.pack(pady=(5, 0))
        
        tk.Label(
            dialog,
            text="Content:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(pady=(20, 5))
        
        content_text = scrolledtext.ScrolledText(
            dialog,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 11),
            width=50,
            height=12,
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=self.theme.BORDER_DEFAULT,
            highlightcolor=self.theme.ACCENT_BLUE
        )
        content_text.pack(pady=(0, 15))
        
        tk.Label(
            dialog,
            text="Tags (comma-separated):",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(pady=(0, 5))
        
        tags_entry = tk.Entry(
            dialog,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
            width=40
        )
        tags_entry.pack(pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.theme.PRIMARY_BG)
        button_frame.pack(pady=20)
        
        def save_note():
            title = title_entry.get().strip()
            category = category_combo.get()
            priority_map = {'Low': 1, 'Medium': 2, 'High': 3}
            priority = priority_map[priority_combo.get()]
            content = content_text.get(1.0, tk.END).strip()
            tags = tags_entry.get().strip()
            
            if title and content:
                try:
                    self.db_manager.insert('user_notes', {
                        'title': title,
                        'content': content,
                        'category': category,
                        'language': config.learning.target_language,
                        'priority': priority,
                        'tags': tags if tags else None,
                        'created_at': datetime.now().isoformat(),
                        'archived': 0
                    })
                    self._load_notes()
                    dialog.destroy()
                    self.logger.info(f"Added new note: {title}")
                except Exception as e:
                    self.logger.error(f"Error adding note: {e}")
        
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
            command=save_note
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
    
    def _on_note_double_click(self, event):
        """Handle double-click on a note to view details."""
        selection = self.notes_list.selection()
        if selection:
            item = self.notes_list.item(selection[0])
            values = item['values']
            if values:
                title = values[0]
                self.logger.info(f"View note details: {title}")
                self._show_note_details(title)
    
    def _show_note_details(self, title: str):
        """Show detailed view of a note."""
        try:
            # Get note details from database
            query = """
                SELECT title, content, category, priority, tags, created_at, updated_at
                FROM user_notes 
                WHERE title = ? AND language = ? AND archived = 0
            """
            
            results = self.db_manager.execute_query(query, (title, config.learning.target_language))
            
            if results:
                row = results[0]
                self._show_note_dialog(row)
            else:
                self.logger.warning(f"Note not found: {title}")
                
        except Exception as e:
            self.logger.error(f"Error loading note details: {e}")
    
    def _show_note_dialog(self, note_data):
        """Show note details dialog."""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title(f"Note - {note_data[0]}")
        dialog.geometry("600x500")
        dialog.configure(bg=self.theme.PRIMARY_BG)
        dialog.transient(self.parent_frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")
        
        # Title
        title_label = tk.Label(
            dialog,
            text=note_data[0],
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 18, 'bold')
        )
        title_label.pack(pady=(20, 10))
        
        # Info frame
        info_frame = tk.Frame(dialog, bg=self.theme.PRIMARY_BG)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        # Category and priority
        cat_pri_frame = tk.Frame(info_frame, bg=self.theme.PRIMARY_BG)
        cat_pri_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            cat_pri_frame,
            text=f"Category: {note_data[2]}",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left', padx=(0, 20))
        
        priority_map = {1: 'Low', 2: 'Medium', 3: 'High'}
        priority_str = priority_map.get(note_data[3], 'Low')
        tk.Label(
            cat_pri_frame,
            text=f"Priority: {priority_str}",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left')
        
        # Dates
        dates_frame = tk.Frame(info_frame, bg=self.theme.PRIMARY_BG)
        dates_frame.pack(fill='x', pady=(0, 10))
        
        created_str = note_data[5][:10] if note_data[5] else 'Unknown'
        tk.Label(
            dates_frame,
            text=f"Created: {created_str}",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left', padx=(0, 20))
        
        updated_str = note_data[6][:10] if note_data[6] else 'Never'
        tk.Label(
            dates_frame,
            text=f"Updated: {updated_str}",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left')
        
        # Tags
        if note_data[4]:  # tags
            tk.Label(
                dialog,
                text=f"Tags: {note_data[4]}",
                bg=self.theme.PRIMARY_BG,
                fg=self.theme.TEXT_PRIMARY,
                font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
                anchor='w'
            ).pack(anchor='w', padx=20, pady=(10, 5))
        
        # Content
        tk.Label(
            dialog,
            text="Content:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 14, 'bold'),
            anchor='w'
        ).pack(anchor='w', padx=20, pady=(20, 5))
        
        content_text = scrolledtext.ScrolledText(
            dialog,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 11),
            width=70,
            height=12,
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=self.theme.BORDER_DEFAULT,
            state='normal'
        )
        content_text.pack(padx=20, pady=(0, 20), fill='both', expand=True)
        content_text.insert(1.0, note_data[1])
        content_text.config(state='disabled')
        
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
        self._load_notes()
    
    def refresh_data(self):
        """Refresh the notes data."""
        self._load_notes()

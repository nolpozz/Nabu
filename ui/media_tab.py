"""
Media tab for the Nabu application.
Displays recommended songs, movies, and other media for language learning.
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


class MediaTab:
    """Media tab component."""
    
    def __init__(self, parent_frame: tk.Frame, event_bus: EventBus, session_manager: SessionManager, db_manager=None):
        self.parent_frame = parent_frame
        self.event_bus = event_bus
        self.session_manager = session_manager
        self.logger = get_logger(__name__)
        self.theme = DarkTheme()
        self.db_manager = db_manager or DatabaseManager()
        
        # UI components
        self.media_list = None
        self.filter_combo = None
        self.search_entry = None
        
        self._create_ui()
        self._setup_event_handlers()
        self._load_media()
    
    def on_tab_activated(self):
        """Called when this tab is activated."""
        self._load_media()
    
    def _create_ui(self):
        """Create the media tab UI."""
        # Main container
        main_frame = tk.Frame(self.parent_frame, bg=self.theme.PRIMARY_BG)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.theme.PRIMARY_BG)
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="🎬 Media Recommendations",
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
            text="Type:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left', padx=(0, 10))
        
        self.filter_combo = ttk.Combobox(
            search_frame,
            values=['All', 'Movies', 'Songs', 'Podcasts', 'Books', 'Videos'],
            state='readonly',
            width=12
        )
        self.filter_combo.set('All')
        self.filter_combo.pack(side='left', padx=(0, 20))
        self.filter_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Add media button
        add_button = tk.Button(
            controls_frame,
            text="➕ Add Media",
            bg=self.theme.ACCENT_BLUE,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12, 'bold'),
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._show_add_media_dialog
        )
        add_button.pack(side='right')
        
        # Media list
        list_frame = tk.Frame(main_frame, bg=self.theme.PRIMARY_BG)
        list_frame.pack(fill='both', expand=True)
        
        # Create Treeview for media
        columns = ('Title', 'Type', 'Language', 'Difficulty', 'Duration', 'Rating', 'Status')
        self.media_list = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        # Configure columns
        self.media_list.heading('Title', text='Title')
        self.media_list.heading('Type', text='Type')
        self.media_list.heading('Language', text='Language')
        self.media_list.heading('Difficulty', text='Difficulty')
        self.media_list.heading('Duration', text='Duration')
        self.media_list.heading('Rating', text='Rating')
        self.media_list.heading('Status', text='Status')
        
        # Column widths
        self.media_list.column('Title', width=200)
        self.media_list.column('Type', width=80)
        self.media_list.column('Language', width=80)
        self.media_list.column('Difficulty', width=80)
        self.media_list.column('Duration', width=80)
        self.media_list.column('Rating', width=60)
        self.media_list.column('Status', width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.media_list.yview)
        self.media_list.configure(yscrollcommand=scrollbar.set)
        
        # Pack list and scrollbar
        self.media_list.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to view details
        self.media_list.bind('<Double-1>', self._on_media_double_click)
        
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
        pass  # No specific events for media tab yet
    
    def _load_media(self):
        """Load media recommendations from database."""
        try:
            # Clear existing items
            for item in self.media_list.get_children():
                self.media_list.delete(item)
            
            # Get media from database
            query = """
                SELECT title, type, language, difficulty_level, duration_minutes,
                       user_rating, completion_percentage
                FROM media_recommendations 
                WHERE language = ? 
                ORDER BY recommended_at DESC
            """
            
            results = self.db_manager.execute_query(
                query, 
                (config.learning.target_language,)
            )
            
            for row in results:
                title, media_type, language, difficulty, duration, rating, completion = row
                
                # Format duration
                duration_str = f"{duration}min" if duration else "N/A"
                
                # Format rating
                rating_str = f"{rating}/5" if rating else "Not rated"
                
                # Format status
                if completion == 100:
                    status = "Completed"
                elif completion > 0:
                    status = f"{completion:.0f}%"
                else:
                    status = "Not started"
                
                # Insert into treeview
                self.media_list.insert('', 'end', values=(
                    title, media_type, language, difficulty, 
                    duration_str, rating_str, status
                ))
            
            self.logger.info(f"Loaded {len(results)} media items")
            
        except Exception as e:
            self.logger.error(f"Error loading media: {e}")
    
    def _on_search(self, event):
        """Handle search input."""
        search_term = self.search_entry.get().lower()
        self._filter_media(search_term, self.filter_combo.get())
    
    def _on_filter_changed(self, event):
        """Handle filter selection."""
        search_term = self.search_entry.get().lower()
        self._filter_media(search_term, self.filter_combo.get())
    
    def _filter_media(self, search_term: str, filter_type: str):
        """Filter media based on search term and filter type."""
        # This would implement filtering logic
        # For now, just reload all media
        self._load_media()
    
    def _show_add_media_dialog(self):
        """Show dialog to add a new media item."""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Add New Media")
        dialog.geometry("500x400")
        dialog.configure(bg=self.theme.PRIMARY_BG)
        dialog.transient(self.parent_frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"500x400+{x}+{y}")
        
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
        
        tk.Label(
            dialog,
            text="Type:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(pady=(0, 5))
        
        type_combo = ttk.Combobox(
            dialog,
            values=['Movie', 'Song', 'Podcast', 'Book', 'Video'],
            state='readonly',
            width=20
        )
        type_combo.set('Movie')
        type_combo.pack(pady=(0, 15))
        
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
        
        # URL and difficulty frame
        info_frame = tk.Frame(dialog, bg=self.theme.PRIMARY_BG)
        info_frame.pack(fill='x', pady=(0, 15))
        
        # URL
        url_frame = tk.Frame(info_frame, bg=self.theme.PRIMARY_BG)
        url_frame.pack(side='left', padx=(0, 20))
        
        tk.Label(
            url_frame,
            text="URL (optional):",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(anchor='w')
        
        url_entry = tk.Entry(
            url_frame,
            bg=self.theme.ELEVATED_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12),
            width=25
        )
        url_entry.pack(pady=(5, 0))
        
        # Difficulty
        difficulty_frame = tk.Frame(info_frame, bg=self.theme.PRIMARY_BG)
        difficulty_frame.pack(side='left')
        
        tk.Label(
            difficulty_frame,
            text="Difficulty:",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(anchor='w')
        
        difficulty_combo = ttk.Combobox(
            difficulty_frame,
            values=['1', '2', '3', '4', '5'],
            state='readonly',
            width=10
        )
        difficulty_combo.set('3')
        difficulty_combo.pack(pady=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.theme.PRIMARY_BG)
        button_frame.pack(pady=20)
        
        def save_media():
            title = title_entry.get().strip()
            media_type = type_combo.get()
            description = description_text.get(1.0, tk.END).strip()
            url = url_entry.get().strip()
            difficulty = int(difficulty_combo.get())
            
            if title and media_type:
                try:
                    self.db_manager.insert('media_recommendations', {
                        'title': title,
                        'type': media_type,
                        'language': config.learning.target_language,
                        'difficulty_level': difficulty,
                        'description': description if description else None,
                        'url': url if url else None,
                        'recommended_at': datetime.now().isoformat()
                    })
                    self._load_media()
                    dialog.destroy()
                    self.logger.info(f"Added new media: {title}")
                except Exception as e:
                    self.logger.error(f"Error adding media: {e}")
        
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
            command=save_media
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
    
    def _on_media_double_click(self, event):
        """Handle double-click on a media item to view details."""
        selection = self.media_list.selection()
        if selection:
            item = self.media_list.item(selection[0])
            values = item['values']
            if values:
                title = values[0]
                self.logger.info(f"View media details: {title}")
                self._show_media_details(title)
    
    def _show_media_details(self, title: str):
        """Show detailed view of a media item."""
        try:
            # Get media details from database
            query = """
                SELECT title, type, language, difficulty_level, duration_minutes,
                       url, description, tags, notes, user_rating, completion_percentage
                FROM media_recommendations 
                WHERE title = ? AND language = ?
            """
            
            results = self.db_manager.execute_query(query, (title, config.learning.target_language))
            
            if results:
                row = results[0]
                self._show_media_dialog(row)
            else:
                self.logger.warning(f"Media item not found: {title}")
                
        except Exception as e:
            self.logger.error(f"Error loading media details: {e}")
    
    def _show_media_dialog(self, media_data):
        """Show media details dialog."""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title(f"Media Details - {media_data[0]}")
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
            text=media_data[0],
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 18, 'bold')
        )
        title_label.pack(pady=(20, 10))
        
        # Info frame
        info_frame = tk.Frame(dialog, bg=self.theme.PRIMARY_BG)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        # Type and language
        type_lang_frame = tk.Frame(info_frame, bg=self.theme.PRIMARY_BG)
        type_lang_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            type_lang_frame,
            text=f"Type: {media_data[1]}",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left', padx=(0, 20))
        
        tk.Label(
            type_lang_frame,
            text=f"Language: {media_data[2]}",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left')
        
        # Difficulty and duration
        diff_dur_frame = tk.Frame(info_frame, bg=self.theme.PRIMARY_BG)
        diff_dur_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            diff_dur_frame,
            text=f"Difficulty: {media_data[3]}/5",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left', padx=(0, 20))
        
        duration_str = f"{media_data[4]} minutes" if media_data[4] else "Duration not specified"
        tk.Label(
            diff_dur_frame,
            text=f"Duration: {duration_str}",
            bg=self.theme.PRIMARY_BG,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY_PRIMARY[0], 12)
        ).pack(side='left')
        
        # Description
        if media_data[6]:  # description
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
                width=60,
                height=6,
                relief='flat',
                bd=1,
                highlightthickness=1,
                highlightbackground=self.theme.BORDER_DEFAULT,
                state='normal'
            )
            description_text.pack(padx=20, pady=(0, 20), fill='both', expand=True)
            description_text.insert(1.0, media_data[6])
            description_text.config(state='disabled')
        
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
        self._load_media()
    
    def refresh_data(self):
        """Refresh the media data."""
        self._load_media()

"""
Dark theme system for the AI Language Tutor application.
Provides modern, Apple/Linear/Perplexity-inspired styling.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any


class DarkTheme:
    """Dark theme with modern styling."""
    
    # Base colors
    PRIMARY_BG = "#0A0A0B"           # Deep black background
    SURFACE_BG = "#111113"           # Card/panel background
    ELEVATED_BG = "#1A1A1C"          # Modal/dialog background
    
    # Text colors
    TEXT_PRIMARY = "#FFFFFF"         # Primary text
    TEXT_SECONDARY = "#A1A1AA"       # Secondary text
    TEXT_MUTED = "#71717A"           # Muted text
    
    # Accent colors
    ACCENT_BLUE = "#3B82F6"          # Primary action color
    ACCENT_GREEN = "#10B981"         # Success/positive
    ACCENT_ORANGE = "#F59E0B"        # Warning/attention
    ACCENT_RED = "#EF4444"           # Error/negative
    ACCENT_PURPLE = "#8B5CF6"        # Secondary accent
    
    # Interactive states
    HOVER_OVERLAY = "#FFFFFF10"      # Subtle hover effect
    PRESSED_OVERLAY = "#FFFFFF05"    # Pressed state
    
    # Borders and dividers
    BORDER_SUBTLE = "#27272A"        # Subtle borders
    BORDER_DEFAULT = "#3F3F46"       # Default borders
    
    # Gradients
    GRADIENT_PRIMARY = "linear-gradient(135deg, #3B82F6, #8B5CF6)"
    GRADIENT_SURFACE = "linear-gradient(135deg, #111113, #1A1A1C)"
    
    # Typography
    FONT_FAMILY_PRIMARY = ("SF Pro Display", "Segoe UI", "Arial")
    FONT_FAMILY_MONO = ("SF Mono", "Consolas", "Monaco")
    
    FONT_SIZES = {
        'xs': 11,    # Small labels
        'sm': 13,    # Body text small
        'base': 15,  # Body text
        'lg': 18,    # Large text
        'xl': 24,    # Headings
        '2xl': 32,   # Large headings
        '3xl': 48    # Display text
    }
    
    # Component specifications
    BORDER_RADIUS = {
        'sm': 6,
        'md': 12,
        'lg': 16,
        'xl': 24
    }
    
    SPACING = {
        'xs': 4,
        'sm': 8,
        'md': 16,
        'lg': 24,
        'xl': 32,
        '2xl': 48,
        '3xl': 64
    }
    
    SHADOWS = {
        'sm': "0 1px 3px rgba(0, 0, 0, 0.3)",
        'md': "0 4px 6px rgba(0, 0, 0, 0.3)",
        'lg': "0 10px 15px rgba(0, 0, 0, 0.3)",
        'xl': "0 20px 25px rgba(0, 0, 0, 0.3)"
    }
    
    def __init__(self):
        # Don't initialize style here - it creates a hidden window
        self.style = None
    
    def apply_to_window(self, window: tk.Tk) -> None:
        """Apply the theme to a window."""
        window.configure(bg=self.PRIMARY_BG)
        
        # Initialize style after main window exists to prevent hidden window
        if self.style is None:
            self.style = ttk.Style()
            self._configure_style()
        
        # Configure window icon and title bar (commented out to prevent issues)
        # try:
        #     window.iconbitmap("assets/icons/app_icon.ico")
        # except:
        #     pass  # Icon not available
        
        # Set window properties
        window.option_add('*TFrame*background', self.PRIMARY_BG)
        window.option_add('*TLabel*background', self.PRIMARY_BG)
        window.option_add('*TButton*background', self.SURFACE_BG)
    
    def _configure_style(self) -> None:
        """Configure ttk styles."""
        # Configure the style
        self.style.theme_use('clam')
        
        # Configure common styles
        self.style.configure(
            'TFrame',
            background=self.PRIMARY_BG,
            borderwidth=0
        )
        
        self.style.configure(
            'TLabel',
            background=self.PRIMARY_BG,
            foreground=self.TEXT_PRIMARY,
            font=(self.FONT_FAMILY_PRIMARY[0], self.FONT_SIZES['base'])
        )
        
        self.style.configure(
            'TButton',
            background=self.SURFACE_BG,
            foreground=self.TEXT_PRIMARY,
            borderwidth=0,
            focuscolor='none',
            font=(self.FONT_FAMILY_PRIMARY[0], self.FONT_SIZES['base']),
            padding=(self.SPACING['md'], self.SPACING['sm'])
        )
        
        self.style.map(
            'TButton',
            background=[
                ('active', self.ELEVATED_BG),
                ('pressed', self.ELEVATED_BG)
            ],
            foreground=[
                ('active', self.TEXT_PRIMARY),
                ('pressed', self.TEXT_PRIMARY)
            ]
        )
        
        # Primary button style
        self.style.configure(
            'Primary.TButton',
            background=self.ACCENT_BLUE,
            foreground=self.TEXT_PRIMARY,
            font=(self.FONT_FAMILY_PRIMARY[0], self.FONT_SIZES['base'], 'bold')
        )
        
        self.style.map(
            'Primary.TButton',
            background=[
                ('active', self._darken_color(self.ACCENT_BLUE, 0.1)),
                ('pressed', self._darken_color(self.ACCENT_BLUE, 0.2))
            ]
        )
        
        # Success button style
        self.style.configure(
            'Success.TButton',
            background=self.ACCENT_GREEN,
            foreground=self.TEXT_PRIMARY
        )
        
        # Danger button style
        self.style.configure(
            'Danger.TButton',
            background=self.ACCENT_RED,
            foreground=self.TEXT_PRIMARY
        )
        
        # Entry style
        self.style.configure(
            'TEntry',
            fieldbackground=self.SURFACE_BG,
            foreground=self.TEXT_PRIMARY,
            borderwidth=1,
            relief='flat',
            font=(self.FONT_FAMILY_PRIMARY[0], self.FONT_SIZES['base'])
        )
        
        self.style.map(
            'TEntry',
            fieldbackground=[
                ('focus', self.ELEVATED_BG),
                ('active', self.ELEVATED_BG)
            ],
            bordercolor=[
                ('focus', self.ACCENT_BLUE),
                ('active', self.BORDER_DEFAULT)
            ]
        )
        
        # Text widget style
        self.style.configure(
            'TText',
            background=self.SURFACE_BG,
            foreground=self.TEXT_PRIMARY,
            borderwidth=0,
            font=(self.FONT_FAMILY_PRIMARY[0], self.FONT_SIZES['base'])
        )
        
        # Scrollbar style
        self.style.configure(
            'TScrollbar',
            background=self.SURFACE_BG,
            bordercolor=self.BORDER_DEFAULT,
            arrowcolor=self.TEXT_SECONDARY,
            troughcolor=self.PRIMARY_BG,
            width=12
        )
        
        self.style.map(
            'TScrollbar',
            background=[
                ('active', self.ELEVATED_BG),
                ('pressed', self.ELEVATED_BG)
            ]
        )
        
        # Notebook (tab) style
        self.style.configure(
            'TNotebook',
            background=self.PRIMARY_BG,
            borderwidth=0
        )
        
        self.style.configure(
            'TNotebook.Tab',
            background=self.SURFACE_BG,
            foreground=self.TEXT_SECONDARY,
            borderwidth=0,
            padding=(self.SPACING['lg'], self.SPACING['sm']),
            font=(self.FONT_FAMILY_PRIMARY[0], self.FONT_SIZES['base'])
        )
        
        self.style.map(
            'TNotebook.Tab',
            background=[
                ('selected', self.ELEVATED_BG),
                ('active', self.ELEVATED_BG)
            ],
            foreground=[
                ('selected', self.TEXT_PRIMARY),
                ('active', self.TEXT_PRIMARY)
            ]
        )
        
        # Treeview style
        self.style.configure(
            'Treeview',
            background=self.SURFACE_BG,
            foreground=self.TEXT_PRIMARY,
            fieldbackground=self.SURFACE_BG,
            borderwidth=0,
            font=(self.FONT_FAMILY_PRIMARY[0], self.FONT_SIZES['base'])
        )
        
        self.style.configure(
            'Treeview.Heading',
            background=self.ELEVATED_BG,
            foreground=self.TEXT_PRIMARY,
            borderwidth=0,
            font=(self.FONT_FAMILY_PRIMARY[0], self.FONT_SIZES['base'], 'bold')
        )
        
        self.style.map(
            'Treeview',
            background=[
                ('selected', self.ACCENT_BLUE),
                ('active', self.ELEVATED_BG)
            ],
            foreground=[
                ('selected', self.TEXT_PRIMARY),
                ('active', self.TEXT_PRIMARY)
            ]
        )
    
    def _darken_color(self, color: str, factor: float) -> str:
        """Darken a hex color by a factor."""
        # Convert hex to RGB
        color = color.lstrip('#')
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # Darken
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def create_styled_frame(self, parent: tk.Widget, **kwargs) -> tk.Frame:
        """Create a styled frame with the theme."""
        frame = tk.Frame(
            parent,
            bg=self.SURFACE_BG,
            relief='flat',
            bd=0,
            **kwargs
        )
        return frame
    
    def create_styled_button(self, parent: tk.Widget, text: str, style: str = "primary", **kwargs) -> tk.Button:
        """Create a styled button with the theme."""
        # Determine button colors based on style
        if style == "primary":
            bg_color = self.ACCENT_BLUE
            hover_color = self._lighten_color(self.ACCENT_BLUE, 0.2)
            pressed_color = self._darken_color(self.ACCENT_BLUE, 0.2)
        elif style == "secondary":
            bg_color = self.SURFACE_BG
            hover_color = self.ELEVATED_BG
            pressed_color = self._darken_color(self.SURFACE_BG, 0.1)
        else:
            bg_color = self.SURFACE_BG
            hover_color = self.ELEVATED_BG
            pressed_color = self._darken_color(self.SURFACE_BG, 0.1)
        
        button = tk.Button(
            parent,
            text=text,
            bg=bg_color,
            fg=self.TEXT_PRIMARY,
            font=(self.FONT_FAMILY_PRIMARY[0], self.FONT_SIZES['base'], 'bold'),
            relief='flat',
            bd=0,
            padx=self.SPACING['lg'],
            pady=self.SPACING['md'],
            cursor='hand2',
            **kwargs
        )
        
        # Add hover effects
        button.bind('<Enter>', lambda e: button.configure(bg=hover_color))
        button.bind('<Leave>', lambda e: button.configure(bg=bg_color))
        button.bind('<Button-1>', lambda e: button.configure(bg=pressed_color))
        button.bind('<ButtonRelease-1>', lambda e: button.configure(bg=hover_color))
        
        return button
    
    def create_styled_label(self, parent: tk.Widget, text: str, size: str = 'base', **kwargs) -> tk.Label:
        """Create a styled label with the theme."""
        font_size = self.FONT_SIZES.get(size, self.FONT_SIZES['base'])
        
        label = tk.Label(
            parent,
            text=text,
            bg=self.PRIMARY_BG,
            fg=self.TEXT_PRIMARY,
            font=(self.FONT_FAMILY_PRIMARY[0], font_size),
            **kwargs
        )
        return label
    
    def create_styled_entry(self, parent: tk.Widget, **kwargs) -> tk.Entry:
        """Create a styled entry with the theme."""
        entry = tk.Entry(
            parent,
            bg=self.SURFACE_BG,
            fg=self.TEXT_PRIMARY,
            insertbackground=self.TEXT_PRIMARY,
            font=(self.FONT_FAMILY_PRIMARY[0], self.FONT_SIZES['base']),
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=self.BORDER_DEFAULT,
            highlightcolor=self.ACCENT_BLUE,
            **kwargs
        )
        return entry
    
    def create_styled_text(self, parent: tk.Widget, **kwargs) -> tk.Text:
        """Create a styled text widget with the theme."""
        text_widget = tk.Text(
            parent,
            bg=self.SURFACE_BG,
            fg=self.TEXT_PRIMARY,
            insertbackground=self.TEXT_PRIMARY,
            selectbackground=self.ACCENT_BLUE,
            selectforeground=self.TEXT_PRIMARY,
            font=(self.FONT_FAMILY_PRIMARY[0], self.FONT_SIZES['base']),
            relief='flat',
            bd=0,
            padx=self.SPACING['sm'],
            pady=self.SPACING['sm'],
            **kwargs
        )
        return text_widget
    
    def get_color(self, color_name: str) -> str:
        """Get a color by name."""
        return getattr(self, color_name.upper(), self.TEXT_PRIMARY)
    
    def get_spacing(self, size: str) -> int:
        """Get spacing by size."""
        return self.SPACING.get(size, self.SPACING['md'])
    
    def get_font_size(self, size: str) -> int:
        """Get font size by name."""
        return self.FONT_SIZES.get(size, self.FONT_SIZES['base'])
    
    def get_border_radius(self, size: str) -> int:
        """Get border radius by size."""
        return self.BORDER_RADIUS.get(size, self.BORDER_RADIUS['md'])
    
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


# Global theme instance
theme = DarkTheme()

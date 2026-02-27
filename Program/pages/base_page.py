"""
pages/base_page.py - Base class for pages
"""

import tkinter as tk
from config import COLORS


class BasePage(tk.Frame):
    """Base class for all pages"""
    
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.controller = controller
        self.colors = COLORS
    
    def on_show(self):
        """Called when page is shown. Override in subclass."""
        pass
    
    def create_header(self, title, subtitle=""):
        """Creates page header"""
        header_frame = tk.Frame(self, bg=self.colors["bg_card"])
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_frame = tk.Frame(header_frame, bg=self.colors["bg_card"])
        title_frame.pack(fill="x", padx=25, pady=20)
        
        tk.Label(
            title_frame,
            text=title,
            font=("Segoe UI", 28, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"]
        ).pack(side="left")
        
        if subtitle:
            tk.Label(
                title_frame,
                text=subtitle,
                font=("Segoe UI", 11),
                bg=self.colors["bg_card"],
                fg=self.colors["text_secondary"]
            ).pack(side="left", padx=20)
        
        return header_frame
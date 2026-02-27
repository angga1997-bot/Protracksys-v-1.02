"""
components/sidebar.py - Navigation sidebar component
"""

import tkinter as tk
from config import COLORS, APP_CONFIG
import tkinter as tk
from PIL import Image, ImageTk
import os

class Sidebar(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["bg_sidebar"], width=220)
        self.pack_propagate(False)
        
        self.controller = controller
        self.buttons = {}
        
        self._create_widgets()
    
    def _create_widgets(self):
        self._create_logo()
        self._create_separator()
        
        tk.Label(
            self, text="MENU",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg_sidebar"],
            fg=COLORS["text_secondary"]
        ).pack(anchor="w", padx=25, pady=(0, 10))
        
        # Menu buttons
        self._create_menu_button("dashboard", "🏠", "Dashboard")
        self._create_menu_button("history", "📜", "History")  # NEW
        self._create_menu_button("table_settings", "📋", "Table Settings")
        self._create_menu_button("plc_settings", "🔌", "PLC Settings")
        self._create_menu_button("trigger_settings", "⚡", "Trigger")
        self._create_menu_button("shift_schedule", "📅", "Shift Schedule")  # NEW
        self._create_menu_button("register_mp", "👥", "Register MP")
        
        tk.Frame(self, bg=COLORS["bg_sidebar"]).pack(fill="both", expand=True)
        
        self._create_separator()
        self._create_menu_button("help", "❓", "Help")
        self._create_exit_button()
    
    def _create_logo(self):
        logo_frame = tk.Frame(self, bg=COLORS["bg_sidebar"])
        logo_frame.pack(fill="x", pady=20)

        try:
            ico_path = os.path.join("icons", "logo.png")
            img = Image.open(ico_path)
            img = img.resize((90, 90), Image.LANCZOS)
            self.logo_icon = ImageTk.PhotoImage(img)
            tk.Label(
                logo_frame,
                image=self.logo_icon,
                bg=COLORS["bg_sidebar"]
            ).pack()
        except Exception:
            # Fallback emoji if image not found
            tk.Label(logo_frame, text="📊", font=("Segoe UI", 32),
                     bg=COLORS["bg_sidebar"], fg=COLORS["accent"]).pack()

        tk.Label(logo_frame, text="ProTrackSys", font=("Segoe UI", 14, "bold"),
                bg=COLORS["bg_sidebar"], fg=COLORS["text_primary"]).pack()
        tk.Label(logo_frame, text="Production Tracking", font=("Segoe UI", 11),
                bg=COLORS["bg_sidebar"], fg=COLORS["text_secondary"]).pack()
        tk.Label(logo_frame, text="Data System", font=("Segoe UI", 11),
                bg=COLORS["bg_sidebar"], fg=COLORS["text_secondary"]).pack()
    
    def _create_separator(self):
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x", padx=20, pady=10)
    
    def _create_menu_button(self, page_name, icon, text):
        btn_frame = tk.Frame(self, bg=COLORS["bg_sidebar"])
        btn_frame.pack(fill="x", padx=15, pady=2)
        
        btn = tk.Button(
            btn_frame, text=f"{icon}  {text}",
            font=("Segoe UI", 10),
            bg=COLORS["bg_sidebar"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_hover"],
            relief="flat", cursor="hand2",
            anchor="w", padx=15, pady=10,
            command=lambda: self.controller.show_page(page_name)
        )
        btn.pack(fill="x")
        
        self.buttons[page_name] = btn
        
        btn.bind("<Enter>", lambda e, b=btn, p=page_name: self._on_hover(b, p, True))
        btn.bind("<Leave>", lambda e, b=btn, p=page_name: self._on_hover(b, p, False))
    
    def _create_exit_button(self):
        btn_frame = tk.Frame(self, bg=COLORS["bg_sidebar"])
        btn_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        tk.Button(
            btn_frame, text="🚪  EXIT",
            font=("Segoe UI", 10),
            bg=COLORS["accent_red"],
            fg="#1e1e2e",
            relief="flat", cursor="hand2",
            pady=10,
            command=self.controller.quit
        ).pack(fill="x")
    
    def _on_hover(self, button, page_name, entering):
        if self.controller.active_page != page_name:
            button.configure(bg=COLORS["bg_hover"] if entering else COLORS["bg_sidebar"])
    
    def set_active(self, page_name):
        for name, btn in self.buttons.items():
            if name == page_name:
                btn.configure(bg=COLORS["accent"], fg="#1e1e2e")
            else:
                btn.configure(bg=COLORS["bg_sidebar"], fg=COLORS["text_primary"])
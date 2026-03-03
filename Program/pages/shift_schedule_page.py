"""
pages/shift_schedule_page.py - Shift Schedule Page
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pages.base_page import BasePage
from config import COLORS, DAYS_OF_WEEK, DEFAULT_SHIFT_SCHEDULE


class ShiftSchedulePage(BasePage):
    """Shift Schedule Settings Page"""
    
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.schedule_widgets = {}
        self._create_widgets()
    
    def _create_widgets(self):
        """Create widgets"""
        # Header
        self.create_header("📅 Shift Schedule", "Daily shift schedule settings")
        
        # Scrollable content
        canvas = tk.Canvas(self, bg=self.colors["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.colors["bg_dark"])
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Current shift display
        self._create_current_shift_section(scroll_frame)
        
        # Shift 1 section
        self._create_shift_section(scroll_frame, "shift_1", "Shift 1 (Day)")
        
        # Shift 2 section
        self._create_shift_section(scroll_frame, "shift_2", "Shift 2 (Night)")
        
        # Save button
        self._create_save_button(scroll_frame)
        
        # MouseWheel handled globally in main.py
    
    def _create_current_shift_section(self, parent):
        """Current shift section"""
        section = tk.Frame(parent, bg=self.colors["accent_teal"], padx=20, pady=15)
        section.pack(fill="x", padx=10, pady=10)
        
        tk.Label(
            section,
            text="⏰ Current Shift",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["accent_teal"],
            fg="#1e1e2e"
        ).pack(anchor="w")
        
        self.current_shift_label = tk.Label(
            section,
            text="Loading...",
            font=("Segoe UI", 12),
            bg=self.colors["accent_teal"],
            fg="#1e1e2e"
        )
        self.current_shift_label.pack(anchor="w", pady=(5, 0))
        
        self._update_current_shift()
    
    def _update_current_shift(self):
        """Update current shift display"""
        shift_info = self.controller.shift_manager.get_current_shift()
        
        if shift_info:
            text = f"🟢 {shift_info['name']} | {shift_info['day']} | {shift_info['start']} - {shift_info['end']}"
        else:
            text = "⚪ No active shift at the moment"
        
        self.current_shift_label.configure(text=text)
        
        # Refresh every minute
        self.after(60000, self._update_current_shift)
    
    def _create_shift_section(self, parent, shift_key, title):
        """Section for one shift"""
        section = tk.LabelFrame(
            parent,
            text=f"📋 {title}",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            padx=20,
            pady=15
        )
        section.pack(fill="x", padx=10, pady=10)
        
        self.schedule_widgets[shift_key] = {}
        
        schedule = self.controller.shift_manager.get_schedule()
        shift_data = schedule.get(shift_key, DEFAULT_SHIFT_SCHEDULE.get(shift_key, {}))
        
        # Header row
        header_frame = tk.Frame(section, bg=self.colors["bg_card"])
        header_frame.pack(fill="x", pady=(0, 10))
        
        headers = [("Day", 80), ("Enable", 60), ("Start", 80), ("End", 80)]
        for text, width in headers:
            tk.Label(
                header_frame, text=text,
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["bg_card"],
                fg=self.colors["text_secondary"],
                width=width // 8
            ).pack(side="left", padx=5)
        
        # Day rows
        for day in DAYS_OF_WEEK:
            day_config = shift_data.get(day, {"start": "07:30", "end": "19:30", "enabled": True})
            self._create_day_row(section, shift_key, day, day_config)
    
    def _create_day_row(self, parent, shift_key, day, config):
        """Create row for one day"""
        row = tk.Frame(parent, bg=self.colors["bg_card"])
        row.pack(fill="x", pady=3)
        
        widgets = {}
        
        # Day name
        tk.Label(
            row, text=day,
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            width=10, anchor="w"
        ).pack(side="left", padx=5)
        
        # Enable checkbox
        enabled_var = tk.BooleanVar(value=config.get("enabled", True))
        cb = tk.Checkbutton(
            row,
            variable=enabled_var,
            bg=self.colors["bg_card"],
            activebackground=self.colors["bg_card"],
            selectcolor=self.colors["bg_hover"]
        )
        cb.pack(side="left", padx=15)
        widgets["enabled"] = enabled_var
        
        # Start time
        start_entry = tk.Entry(
            row,
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            relief="flat", width=8
        )
        start_entry.insert(0, config.get("start", "07:30"))
        start_entry.pack(side="left", padx=5, ipady=4)
        widgets["start"] = start_entry
        
        # Separator
        tk.Label(
            row, text="-",
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"]
        ).pack(side="left", padx=5)
        
        # End time
        end_entry = tk.Entry(
            row,
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            relief="flat", width=8
        )
        end_entry.insert(0, config.get("end", "19:30"))
        end_entry.pack(side="left", padx=5, ipady=4)
        widgets["end"] = end_entry
        
        # Store widgets
        self.schedule_widgets[shift_key][day] = widgets
    
    def _create_save_button(self, parent):
        """Save button"""
        frame = tk.Frame(parent, bg=self.colors["bg_dark"])
        frame.pack(fill="x", padx=10, pady=20)
        
        tk.Button(
            frame,
            text="💾 Save Shift Schedule",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["accent_green"],
            fg="#1e1e2e",
            relief="flat",
            cursor="hand2",
            padx=40,
            pady=15,
            command=self._save_schedule
        ).pack()
    
    def _save_schedule(self):
        """Save shift schedule"""
        schedule = {}
        
        for shift_key, days_widgets in self.schedule_widgets.items():
            schedule[shift_key] = {"name": f"Shift {shift_key[-1]}"}
            
            for day, widgets in days_widgets.items():
                schedule[shift_key][day] = {
                    "enabled": widgets["enabled"].get(),
                    "start": widgets["start"].get().strip(),
                    "end": widgets["end"].get().strip()
                }
        
        self.controller.shift_manager.save_schedule(schedule)
        self.controller.shift_manager.reload_schedule()
        
        messagebox.showinfo("Success", "✅ Shift schedule saved successfully!")
        self._update_current_shift()
    
    def on_show(self):
        """Called when page is shown"""
        self._update_current_shift()
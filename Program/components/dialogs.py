"""
components/dialogs.py - Dialog components
"""

import tkinter as tk
from tkinter import ttk
from config import COLORS


class AddRowDialog(tk.Toplevel):

    
    def __init__(self, parent, columns, data_manager):
        super().__init__(parent)
        
        self.title("➕ Add new Data")
        self.geometry("500x400")
        self.configure(bg=COLORS["bg_card"])
        
        self.data_manager = data_manager
        self.result = None
        self.entries = []
        
        self._create_widgets(columns)
        
        self.transient(parent)
        self.grab_set()
    
    def _create_widgets(self, columns):
        """Membuat widget dialog"""
        # Header
        tk.Label(
            self,
            text="➕ Add New Data",
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"]
        ).pack(pady=20)
        
        # Form
        form_frame = tk.Frame(self, bg=COLORS["bg_card"])
        form_frame.pack(fill="both", expand=True, padx=30)
        
        for col in columns:
            row_frame = tk.Frame(form_frame, bg=COLORS["bg_card"])
            row_frame.pack(fill="x", pady=8)
            
            tk.Label(
                row_frame,
                text=f"{col}:",
                font=("Segoe UI", 11),
                bg=COLORS["bg_card"],
                fg=COLORS["text_secondary"],
                width=15,
                anchor="w"
            ).pack(side="left")
            
            entry = tk.Entry(
                row_frame,
                font=("Segoe UI", 11),
                bg=COLORS["bg_hover"],
                fg=COLORS["text_primary"],
                relief="flat"
            )
            entry.pack(side="left", fill="x", expand=True, ipady=8)
            self.entries.append(entry)
        
        # Buttons
        btn_frame = tk.Frame(self, bg=COLORS["bg_card"])
        btn_frame.pack(pady=20)
        
        tk.Button(
            btn_frame,
            text="💾 SAVE",
            font=("Segoe UI", 11),
            bg=COLORS["accent_green"],
            fg="#1e1e2e",
            relief="flat",
            padx=25,
            pady=10,
            command=self._save
        ).pack(side="left", padx=10)
        
        tk.Button(
            btn_frame,
            text="❌ CANCEL",
            font=("Segoe UI", 11),
            bg=COLORS["accent_red"],
            fg="#1e1e2e",
            relief="flat",
            padx=25,
            pady=10,
            command=self.destroy
        ).pack(side="left", padx=10)
    
    def _save(self):
        """Simpan data"""
        self.result = [entry.get() for entry in self.entries]
        self.destroy()


class NotificationToast:
    """Toast notification"""
    
    @staticmethod
    def show(parent, message, duration=2000):
        """Menampilkan toast notification"""
        toast = tk.Toplevel(parent)
        toast.overrideredirect(True)
        toast.configure(bg=COLORS["accent_green"])
        
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 150
        y = parent.winfo_rooty() + 50
        toast.geometry(f"300x40+{x}+{y}")
        
        tk.Label(
            toast,
            text=message,
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["accent_green"],
            fg="#1e1e2e"
        ).pack(expand=True)
        
        toast.after(duration, toast.destroy)
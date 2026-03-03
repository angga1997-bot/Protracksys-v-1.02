"""
pages/trigger_settings_page.py - PLC Trigger Settings Page
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

from pages.base_page import BasePage
from config import COLORS, PLC_MEMORY_AREAS, TRIGGER_TYPES, TRIGGER_ACTIONS


class TriggerSettingsPage(BasePage):
    """PLC Trigger Settings Page"""
    
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.image_trigger_widgets = []
        self._create_widgets()
    
    def _create_widgets(self):
        """Creates widgets"""
        # Header
        self.create_header("⚡ Trigger Settings", "PLC trigger settings")
        
        # Scrollable content
        canvas = tk.Canvas(self, bg=self.colors["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.colors["bg_dark"])
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Info section
        self._create_info_section(scroll_frame)
        
        # Main trigger section
        self._create_main_trigger_section(scroll_frame)
        
        # Image triggers section
        self._create_image_triggers_section(scroll_frame)
        
        # Save button
        self._create_save_button(scroll_frame)
        
        # MouseWheel handled globally in main.py
    
    def _create_info_section(self, parent):
        """Info section + Live PLC Monitor panel"""
        info = tk.Frame(parent, bg=self.colors["accent_yellow"], padx=20, pady=15)
        info.pack(fill="x", padx=10, pady=(10, 4))
        
        tk.Label(
            info,
            text="⚡ About PLC Triggers",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["accent_yellow"],
            fg="#1e1e2e"
        ).pack(anchor="w")
        
        tk.Label(
            info,
            text="Triggers are used to send data to the table automatically.\n"
                 "• Main Trigger: Primary trigger to save all data\n"
                 "• Image Trigger: Separate trigger to capture image from folder\n"
                 "• Use Rising Edge for a single trigger when the signal rises",
            font=("Segoe UI", 10),
            bg=self.colors["accent_yellow"],
            fg="#1e1e2e",
            justify="left"
        ).pack(anchor="w", pady=(5, 0))
        
        # ── Live Monitor Panel ────────────────────────────────────────
        monitor = tk.LabelFrame(
            parent,
            text="🔬 Live PLC Monitor",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["accent_purple"],
            padx=20, pady=12
        )
        monitor.pack(fill="x", padx=10, pady=(4, 8))
        
        row = tk.Frame(monitor, bg=self.colors["bg_card"])
        row.pack(fill="x")
        
        # Connection lamp
        tk.Label(row, text="PLC Connection:", font=("Segoe UI", 10),
                 bg=self.colors["bg_card"], fg=self.colors["text_secondary"]
                 ).pack(side="left", padx=(0, 6))
        self._conn_lamp = tk.Label(row, text="⬤", font=("Segoe UI", 18),
                                    bg=self.colors["bg_card"], fg="#555555")
        self._conn_lamp.pack(side="left")
        self._conn_label = tk.Label(row, text="Not connected",
                                     font=("Segoe UI", 9), bg=self.colors["bg_card"],
                                     fg=self.colors["text_secondary"])
        self._conn_label.pack(side="left", padx=(4, 20))
        
        # Trigger bit lamp
        tk.Label(row, text="Trigger Bit:", font=("Segoe UI", 10),
                 bg=self.colors["bg_card"], fg=self.colors["text_secondary"]
                 ).pack(side="left", padx=(0, 6))
        self._bit_lamp = tk.Label(row, text="⬤", font=("Segoe UI", 18),
                                   bg=self.colors["bg_card"], fg="#555555")
        self._bit_lamp.pack(side="left")
        self._bit_label = tk.Label(row, text="OFF",
                                    font=("Segoe UI", 9, "bold"),
                                    bg=self.colors["bg_card"],
                                    fg=self.colors["text_secondary"])
        self._bit_label.pack(side="left", padx=(4, 20))
        
        # Raw word value
        self._word_label = tk.Label(row, text="Word: —",
                                     font=("Segoe UI", 9),
                                     bg=self.colors["bg_card"],
                                     fg=self.colors["text_secondary"])
        self._word_label.pack(side="left", padx=(0, 20))
        
        # Buttons
        btn_frame = tk.Frame(monitor, bg=self.colors["bg_card"])
        btn_frame.pack(fill="x", pady=(8, 0))
        
        self._monitor_btn = tk.Button(
            btn_frame, text="▶ Start Monitor",
            font=("Segoe UI", 10),
            bg=self.colors["accent_green"], fg="#1e1e2e",
            relief="flat", cursor="hand2", padx=12, pady=4,
            command=self._toggle_live_monitor
        )
        self._monitor_btn.pack(side="left", padx=(0, 10))
        
        self._monitor_status = tk.Label(
            btn_frame, text="Click 'Start Monitor' to watch PLC in real-time",
            font=("Segoe UI", 9, "italic"),
            bg=self.colors["bg_card"], fg=self.colors["text_secondary"]
        )
        self._monitor_status.pack(side="left")
        
        self._live_monitor_running = False
        self._live_monitor_client = None
    
    # ── Live Monitor helpers ──────────────────────────────────────────
    
    def _toggle_live_monitor(self):
        if self._live_monitor_running:
            self._stop_live_monitor()
        else:
            self._start_live_monitor()
    
    def _start_live_monitor(self):
        from utils.plc_fins import PLCFinsClient
        self._live_monitor_running = True
        self._monitor_btn.configure(text="■ Stop Monitor",
                                     bg=self.colors["accent_red"])
        self._monitor_status.configure(text="Connecting…")
        
        def _connect():
            client = PLCFinsClient(self.controller.plc_config)
            ok, msg = client.connect()
            if ok:
                self._live_monitor_client = client
                self.after(0, lambda: self._monitor_status.configure(
                    text=f"Connected ✓  {msg[:50]}"))
                self.after(0, lambda: self._conn_lamp.configure(fg="#a6e3a1"))
                self.after(0, lambda: self._conn_label.configure(
                    text="Connected", fg=self.colors["accent_green"]))
                self.after(0, self._poll_trigger_bit)
            else:
                self._live_monitor_running = False
                self.after(0, lambda: self._conn_lamp.configure(fg="#f38ba8"))
                self.after(0, lambda: self._conn_label.configure(
                    text="Failed", fg=self.colors["accent_red"]))
                self.after(0, lambda: self._monitor_status.configure(
                    text=f"❌ {msg}"))
                self.after(0, lambda: self._monitor_btn.configure(
                    text="▶ Start Monitor", bg=self.colors["accent_green"]))
        
        import threading
        threading.Thread(target=_connect, daemon=True).start()
    
    def _stop_live_monitor(self):
        self._live_monitor_running = False
        if self._live_monitor_client:
            try: self._live_monitor_client.disconnect()
            except: pass
            self._live_monitor_client = None
        self._conn_lamp.configure(fg="#555555")
        self._conn_label.configure(text="Not connected",
                                    fg=self.colors["text_secondary"])
        self._bit_lamp.configure(fg="#555555")
        self._bit_label.configure(text="OFF", fg=self.colors["text_secondary"])
        self._word_label.configure(text="Word: —")
        self._monitor_btn.configure(text="▶ Start Monitor",
                                     bg=self.colors["accent_green"])
        self._monitor_status.configure(text="Monitor stopped.")
    
    def _poll_trigger_bit(self):
        """Read main trigger address and update lamps. Reschedule every 400ms."""
        if not self._live_monitor_running or not self._live_monitor_client:
            return
        try:
            area   = self.main_area_var.get()
            addr   = int(self.main_addr_entry.get())
            bit    = int(self.main_bit_entry.get())
        except Exception:
            self.after(400, self._poll_trigger_bit)
            return
        
        def _read():
            client = self._live_monitor_client
            if not client or not client.connected:
                self.after(0, self._stop_live_monitor)
                return
            ok, data = client.read_memory(area, addr, 1)
            if ok and data:
                word = data[0]
                bit_val = (word >> bit) & 1
                self.after(0, lambda: self._update_bit_lamp(bit_val, word))
            else:
                # connection lost
                self.after(0, lambda: self._conn_lamp.configure(fg="#f38ba8"))
                self.after(0, lambda: self._conn_label.configure(
                    text="Read failed", fg=self.colors["accent_red"]))
            if self._live_monitor_running:
                self.after(400, self._poll_trigger_bit)
        
        import threading
        threading.Thread(target=_read, daemon=True).start()
    
    def _update_bit_lamp(self, bit_val, word):
        if bit_val:
            self._bit_lamp.configure(fg="#a6e3a1")   # green
            self._bit_label.configure(text="ON ✓", fg=self.colors["accent_green"])
        else:
            self._bit_lamp.configure(fg="#f38ba8")   # red
            self._bit_label.configure(text="OFF", fg=self.colors["accent_red"])
        self._word_label.configure(text=f"Word: {word}  (bit{self.main_bit_entry.get()}={bit_val})")
    
    def on_hide(self):
        """Stop monitor when navigating away."""
        self._stop_live_monitor()

    
    def _create_main_trigger_section(self, parent):
        """Main trigger section"""
        section = tk.LabelFrame(
            parent,
            text="🎯 Main Trigger (Save Data)",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            padx=20,
            pady=15
        )
        section.pack(fill="x", padx=10, pady=10)
        
        config = self.controller.data_manager.trigger_config
        
        # Enable checkbox
        row0 = tk.Frame(section, bg=self.colors["bg_card"])
        row0.pack(fill="x", pady=10)
        
        self.main_enabled_var = tk.BooleanVar(value=config.get("enabled", False))
        tk.Checkbutton(
            row0, text="Enable Main Trigger",
            variable=self.main_enabled_var,
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["bg_card"],
            selectcolor=self.colors["bg_hover"]
        ).pack(side="left")
        
        # Trigger Address
        row1 = tk.Frame(section, bg=self.colors["bg_card"])
        row1.pack(fill="x", pady=10)
        
        tk.Label(
            row1, text="Trigger Address:",
            font=("Segoe UI", 11),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"],
            width=15, anchor="w"
        ).pack(side="left")
        
        trigger_addr = config.get("trigger_address", {})
        
        # Area type
        self.main_area_var = tk.StringVar(value=trigger_addr.get("area_type", "DM"))
        area_combo = ttk.Combobox(
            row1,
            textvariable=self.main_area_var,
            values=list(PLC_MEMORY_AREAS.keys()),
            width=8,
            state="readonly"
        )
        area_combo.pack(side="left", padx=5)
        
        # Address
        self.main_addr_entry = tk.Entry(
            row1,
            font=("Segoe UI", 11),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            relief="flat", width=8
        )
        self.main_addr_entry.insert(0, str(trigger_addr.get("address", 100)))
        self.main_addr_entry.pack(side="left", padx=5, ipady=4)
        
        # Bit
        tk.Label(
            row1, text="Bit:",
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"]
        ).pack(side="left", padx=(15, 5))
        
        self.main_bit_entry = tk.Entry(
            row1,
            font=("Segoe UI", 11),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            relief="flat", width=5
        )
        self.main_bit_entry.insert(0, str(trigger_addr.get("bit", 0)))
        self.main_bit_entry.pack(side="left", padx=5, ipady=4)
        
        # Preview
        self.main_preview = tk.Label(
            row1, text="",
            font=("Segoe UI", 10, "italic"),
            bg=self.colors["bg_card"],
            fg=self.colors["accent"]
        )
        self.main_preview.pack(side="left", padx=20)
        
        # Update preview
        def update_preview(*args):
            area = self.main_area_var.get()
            try:
                addr = int(self.main_addr_entry.get())
                bit = int(self.main_bit_entry.get())
                prefix = PLC_MEMORY_AREAS.get(area, {}).get("prefix", area)
                self.main_preview.configure(text=f"📍 {prefix}{addr}.{bit:02d}")
            except:
                self.main_preview.configure(text="")
        
        self.main_area_var.trace("w", update_preview)
        self.main_addr_entry.bind("<KeyRelease>", update_preview)
        self.main_bit_entry.bind("<KeyRelease>", update_preview)
        update_preview()
        
        # Trigger Type
        row2 = tk.Frame(section, bg=self.colors["bg_card"])
        row2.pack(fill="x", pady=10)
        
        tk.Label(
            row2, text="Trigger Type:",
            font=("Segoe UI", 11),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"],
            width=15, anchor="w"
        ).pack(side="left")
        
        self.main_type_var = tk.StringVar(value=config.get("trigger_type", "rising"))
        for key, text in TRIGGER_TYPES.items():
            tk.Radiobutton(
                row2, text=text, value=key,
                variable=self.main_type_var,
                font=("Segoe UI", 9),
                bg=self.colors["bg_card"],
                fg=self.colors["text_primary"],
                activebackground=self.colors["bg_card"],
                selectcolor=self.colors["bg_hover"]
            ).pack(side="left", padx=5)
        
        # Action
        row3 = tk.Frame(section, bg=self.colors["bg_card"])
        row3.pack(fill="x", pady=10)
        
        tk.Label(
            row3, text="Action:",
            font=("Segoe UI", 11),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"],
            width=15, anchor="w"
        ).pack(side="left")
        
        self.main_action_var = tk.StringVar(value=config.get("action", "save_data"))
        action_combo = ttk.Combobox(
            row3,
            textvariable=self.main_action_var,
            values=list(TRIGGER_ACTIONS.values()),
            width=30,
            state="readonly"
        )
        action_combo.pack(side="left", padx=5)
        
        # Map value to display
        action_map = {v: k for k, v in TRIGGER_ACTIONS.items()}
        current_action = config.get("action", "save_data")
        action_combo.set(TRIGGER_ACTIONS.get(current_action, "Save Data to Table"))
        
        # Auto reset
        row4 = tk.Frame(section, bg=self.colors["bg_card"])
        row4.pack(fill="x", pady=10)
        
        self.auto_reset_var = tk.BooleanVar(value=config.get("auto_reset", True))
        tk.Checkbutton(
            row4, text="Auto Reset Trigger",
            variable=self.auto_reset_var,
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["bg_card"],
            selectcolor=self.colors["bg_hover"]
        ).pack(side="left")
        
        tk.Label(
            row4, text="Delay (ms):",
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"]
        ).pack(side="left", padx=(20, 5))
        
        self.reset_delay_entry = tk.Entry(
            row4,
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            relief="flat", width=8
        )
        self.reset_delay_entry.insert(0, str(config.get("reset_delay", 500)))
        self.reset_delay_entry.pack(side="left", ipady=3)
    
    def _create_image_triggers_section(self, parent):
        """Image triggers section"""
        section = tk.LabelFrame(
            parent,
            text="📷 Image Triggers (Capture Image from Folder)",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            padx=20,
            pady=15
        )
        section.pack(fill="x", padx=10, pady=10)
        
        # Info
        info_frame = tk.Frame(section, bg=self.colors["bg_hover"], padx=15, pady=10)
        info_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            info_frame,
            text="📷 Image Trigger will capture the latest image from the specified folder\n"
                 "    every time the trigger is active. The image will be saved and displayed in the Image column.",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            justify="left"
        ).pack(anchor="w")
        
        # Container untuk image triggers
        self.image_triggers_frame = tk.Frame(section, bg=self.colors["bg_card"])
        self.image_triggers_frame.pack(fill="x", pady=10)
        
        # Load existing triggers
        self._load_image_triggers()
        
        # Add button
        btn_frame = tk.Frame(section, bg=self.colors["bg_card"])
        btn_frame.pack(fill="x", pady=10)
        
        tk.Button(
            btn_frame, text="➕ Add Image Trigger",
            font=("Segoe UI", 10),
            bg=self.colors["accent_green"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", padx=15, pady=8,
            command=self._add_image_trigger
        ).pack(side="left")
    
    def _load_image_triggers(self):
        """Load image triggers dari config"""
        for widget in self.image_triggers_frame.winfo_children():
            widget.destroy()
        self.image_trigger_widgets = []
        
        triggers = self.controller.data_manager.trigger_config.get("image_triggers", [])
        
        for idx, trigger in enumerate(triggers):
            self._create_image_trigger_widget(idx, trigger)
    
    def _create_image_trigger_widget(self, idx, trigger_data=None):
        """Membuat widget untuk satu image trigger"""
        if trigger_data is None:
            trigger_data = {
                "name": f"Image Trigger {idx + 1}",
                "enabled": True,
                "folder_path": "",
                "address": {"area_type": "DM", "address": 200, "bit": 0},
                "trigger_type": "rising"
            }
        
        frame = tk.LabelFrame(
            self.image_triggers_frame,
            text=f"Image Trigger #{idx + 1}",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            padx=15,
            pady=10
        )
        frame.pack(fill="x", pady=5)
        
        widgets = {"frame": frame}
        
        # Row 1: Enable & Name
        row1 = tk.Frame(frame, bg=self.colors["bg_hover"])
        row1.pack(fill="x", pady=5)
        
        enabled_var = tk.BooleanVar(value=trigger_data.get("enabled", True))
        tk.Checkbutton(
            row1, text="Enable",
            variable=enabled_var,
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["bg_hover"],
            selectcolor=self.colors["bg_card"]
        ).pack(side="left")
        widgets["enabled"] = enabled_var
        
        tk.Label(
            row1, text="Name:",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"]
        ).pack(side="left", padx=(20, 5))
        
        name_entry = tk.Entry(
            row1,
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            relief="flat", width=20
        )
        name_entry.insert(0, trigger_data.get("name", ""))
        name_entry.pack(side="left", ipady=3)
        widgets["name"] = name_entry
        
        # Delete button
        tk.Button(
            row1, text="🗑️",
            font=("Segoe UI", 9),
            bg=self.colors["accent_red"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2",
            command=lambda f=frame, w=widgets: self._delete_image_trigger(f, w)
        ).pack(side="right")
        
        # Row 2: Trigger Address
        row2 = tk.Frame(frame, bg=self.colors["bg_hover"])
        row2.pack(fill="x", pady=5)
        
        tk.Label(
            row2, text="Address:",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"]
        ).pack(side="left")
        
        addr_config = trigger_data.get("address", {})
        
        area_var = tk.StringVar(value=addr_config.get("area_type", "DM"))
        area_combo = ttk.Combobox(
            row2,
            textvariable=area_var,
            values=list(PLC_MEMORY_AREAS.keys()),
            width=6,
            state="readonly"
        )
        area_combo.pack(side="left", padx=5)
        widgets["area_type"] = area_var
        
        addr_entry = tk.Entry(
            row2,
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            relief="flat", width=8
        )
        addr_entry.insert(0, str(addr_config.get("address", 200)))
        addr_entry.pack(side="left", padx=5, ipady=3)
        widgets["address"] = addr_entry
        
        tk.Label(
            row2, text="Bit:",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"]
        ).pack(side="left", padx=(10, 5))
        
        bit_entry = tk.Entry(
            row2,
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            relief="flat", width=4
        )
        bit_entry.insert(0, str(addr_config.get("bit", 0)))
        bit_entry.pack(side="left", ipady=3)
        widgets["bit"] = bit_entry
        
        tk.Label(
            row2, text="Type:",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"]
        ).pack(side="left", padx=(20, 5))
        
        type_var = tk.StringVar(value=trigger_data.get("trigger_type", "rising"))
        type_combo = ttk.Combobox(
            row2,
            textvariable=type_var,
            values=list(TRIGGER_TYPES.keys()),
            width=10,
            state="readonly"
        )
        type_combo.pack(side="left")
        widgets["trigger_type"] = type_var
        
        # Row 3: Folder Path
        row3 = tk.Frame(frame, bg=self.colors["bg_hover"])
        row3.pack(fill="x", pady=5)
        
        tk.Label(
            row3, text="Folder:",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"]
        ).pack(side="left")
        
        folder_entry = tk.Entry(
            row3,
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            relief="flat", width=40
        )
        folder_entry.insert(0, trigger_data.get("folder_path", ""))
        folder_entry.pack(side="left", padx=5, ipady=3)
        widgets["folder_path"] = folder_entry
        
        tk.Button(
            row3, text="📁 Browse",
            font=("Segoe UI", 9),
            bg=self.colors["accent"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2",
            command=lambda e=folder_entry: self._browse_folder(e)
        ).pack(side="left", padx=5)
        
        self.image_trigger_widgets.append(widgets)
    
    def _browse_folder(self, entry_widget):
        """Browse folder"""
        folder = filedialog.askdirectory(title="Select Image Folder")
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)
    
    def _add_image_trigger(self):
        """Tambah image trigger baru"""
        self._create_image_trigger_widget(len(self.image_trigger_widgets))
    
    def _delete_image_trigger(self, frame, widgets):
        """Hapus image trigger"""
        if len(self.image_trigger_widgets) > 0:
            frame.destroy()
            self.image_trigger_widgets.remove(widgets)
    
    def _create_save_button(self, parent):
        """Tombol simpan"""
        frame = tk.Frame(parent, bg=self.colors["bg_dark"])
        frame.pack(fill="x", padx=10, pady=20)
        
        tk.Button(
            frame,
            text="💾 Save Trigger Configuration",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["accent_green"],
            fg="#1e1e2e",
            relief="flat",
            cursor="hand2",
            padx=40,
            pady=15,
            command=self._save_config
        ).pack()
    
    def _save_config(self):
        """Simpan konfigurasi trigger"""
        try:
            # Main trigger
            action_map = {v: k for k, v in TRIGGER_ACTIONS.items()}
            
            config = {
                "enabled": self.main_enabled_var.get(),
                "trigger_address": {
                    "area_type": self.main_area_var.get(),
                    "address": int(self.main_addr_entry.get()),
                    "bit": int(self.main_bit_entry.get())
                },
                "trigger_type": self.main_type_var.get(),
                "action": action_map.get(self.main_action_var.get(), "save_data"),
                "auto_reset": self.auto_reset_var.get(),
                "reset_delay": int(self.reset_delay_entry.get()),
                "image_triggers": []
            }
            
            # Image triggers
            for widgets in self.image_trigger_widgets:
                img_trigger = {
                    "name": widgets["name"].get().strip(),
                    "enabled": widgets["enabled"].get(),
                    "folder_path": widgets["folder_path"].get().strip(),
                    "address": {
                        "area_type": widgets["area_type"].get(),
                        "address": int(widgets["address"].get()),
                        "bit": int(widgets["bit"].get())
                    },
                    "trigger_type": widgets["trigger_type"].get()
                }
                config["image_triggers"].append(img_trigger)
            
            self.controller.data_manager.trigger_config = config
            self.controller.data_manager.save_trigger_config()
            
            messagebox.showinfo("Success", "✅ Trigger configuration saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def on_show(self):
        """Called when page is shown"""
        self._load_image_triggers()
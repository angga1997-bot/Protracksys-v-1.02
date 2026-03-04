"""
pages/trigger_settings_page.py - PLC Trigger Settings Page
"""

import threading
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
        # Live monitor state
        self._monitor_running = False
        self._monitor_client = None
        self._last_main_bit = 0   # for rising-edge detection
        # Widgets set later
        self.main_area_var = None
        self.main_addr_entry = None
        self.main_bit_entry = None
        self._main_lamp = None
        self._main_lamp_lbl = None
        self._create_widgets()
    
    def _create_widgets(self):
        """Creates widgets"""
        self.create_header("⚡ Trigger Settings", "PLC trigger settings")
        
        canvas = tk.Canvas(self, bg=self.colors["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.colors["bg_dark"])
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        self._create_info_section(scroll_frame)
        self._create_main_trigger_section(scroll_frame)
        self._create_image_triggers_section(scroll_frame)
        self._create_save_button(scroll_frame)
    
    # ================================================================
    # INFO SECTION
    # ================================================================

    def _create_info_section(self, parent):
        """Info section"""
        info = tk.Frame(parent, bg=self.colors["accent_yellow"], padx=20, pady=15)
        info.pack(fill="x", padx=10, pady=10)
        
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
                 "• 🟢 Lamp = bit ON   🔴 Lamp = bit OFF   ⚫ Lamp = not connected",
            font=("Segoe UI", 10),
            bg=self.colors["accent_yellow"],
            fg="#1e1e2e",
            justify="left"
        ).pack(anchor="w", pady=(5, 0))
    
    # ================================================================
    # MAIN TRIGGER SECTION
    # ================================================================

    def _create_main_trigger_section(self, parent):
        """Main trigger section"""
        section = tk.LabelFrame(
            parent,
            text="🎯 Main Trigger (Save Data)",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            padx=20, pady=15
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
        
        # Trigger Address row  ── with LAMP on far right
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
        
        self.main_area_var = tk.StringVar(value=trigger_addr.get("area_type", "WR"))
        area_combo = ttk.Combobox(
            row1,
            textvariable=self.main_area_var,
            values=list(PLC_MEMORY_AREAS.keys()),
            width=8, state="readonly"
        )
        area_combo.pack(side="left", padx=5)
        
        self.main_addr_entry = tk.Entry(
            row1, font=("Segoe UI", 11),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            relief="flat", width=8
        )
        self.main_addr_entry.insert(0, str(trigger_addr.get("address", 100)))
        self.main_addr_entry.pack(side="left", padx=5, ipady=4)
        
        tk.Label(row1, text="Bit:", font=("Segoe UI", 10),
                 bg=self.colors["bg_card"], fg=self.colors["text_secondary"]
                 ).pack(side="left", padx=(15, 5))
        
        self.main_bit_entry = tk.Entry(
            row1, font=("Segoe UI", 11),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            relief="flat", width=5
        )
        self.main_bit_entry.insert(0, str(trigger_addr.get("bit", 0)))
        self.main_bit_entry.pack(side="left", padx=5, ipady=4)
        
        # Preview label
        self.main_preview = tk.Label(
            row1, text="",
            font=("Segoe UI", 10, "italic"),
            bg=self.colors["bg_card"], fg=self.colors["accent"]
        )
        self.main_preview.pack(side="left", padx=15)
        
        # ── LAMP indicator ──────────────────────────────────
        self._main_lamp = tk.Label(
            row1, text="⬤", font=("Segoe UI", 22),
            bg=self.colors["bg_card"], fg="#444444"
        )
        self._main_lamp.pack(side="left", padx=(10, 2))
        self._main_lamp_lbl = tk.Label(
            row1, text="—", font=("Segoe UI", 9, "bold"),
            bg=self.colors["bg_card"], fg=self.colors["text_secondary"]
        )
        self._main_lamp_lbl.pack(side="left")
        # ────────────────────────────────────────────────────
        
        def update_preview(*args):
            area = self.main_area_var.get()
            try:
                addr = int(self.main_addr_entry.get())
                bit  = int(self.main_bit_entry.get())
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
        
        tk.Label(row2, text="Trigger Type:", font=("Segoe UI", 11),
                 bg=self.colors["bg_card"], fg=self.colors["text_secondary"],
                 width=15, anchor="w").pack(side="left")
        
        self.main_type_var = tk.StringVar(value=config.get("trigger_type", "rising"))
        for key, text in TRIGGER_TYPES.items():
            tk.Radiobutton(
                row2, text=text, value=key,
                variable=self.main_type_var,
                font=("Segoe UI", 9),
                bg=self.colors["bg_card"], fg=self.colors["text_primary"],
                activebackground=self.colors["bg_card"],
                selectcolor=self.colors["bg_hover"]
            ).pack(side="left", padx=5)
        
        # Action
        row3 = tk.Frame(section, bg=self.colors["bg_card"])
        row3.pack(fill="x", pady=10)
        
        tk.Label(row3, text="Action:", font=("Segoe UI", 11),
                 bg=self.colors["bg_card"], fg=self.colors["text_secondary"],
                 width=15, anchor="w").pack(side="left")
        
        self.main_action_var = tk.StringVar(value=config.get("action", "save_data"))
        action_combo = ttk.Combobox(
            row3, textvariable=self.main_action_var,
            values=list(TRIGGER_ACTIONS.values()),
            width=30, state="readonly"
        )
        action_combo.pack(side="left", padx=5)
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
            bg=self.colors["bg_card"], fg=self.colors["text_primary"],
            activebackground=self.colors["bg_card"],
            selectcolor=self.colors["bg_hover"]
        ).pack(side="left")
        
        tk.Label(row4, text="Delay (ms):", font=("Segoe UI", 10),
                 bg=self.colors["bg_card"], fg=self.colors["text_secondary"]
                 ).pack(side="left", padx=(20, 5))
        
        self.reset_delay_entry = tk.Entry(
            row4, font=("Segoe UI", 10),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            relief="flat", width=8
        )
        self.reset_delay_entry.insert(0, str(config.get("reset_delay", 500)))
        self.reset_delay_entry.pack(side="left", ipady=3)
    
    # ================================================================
    # IMAGE TRIGGERS SECTION
    # ================================================================

    def _create_image_triggers_section(self, parent):
        """Image triggers section"""
        section = tk.LabelFrame(
            parent,
            text="📷 Image Triggers (Capture Image from Folder)",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg_card"], fg=self.colors["text_primary"],
            padx=20, pady=15
        )
        section.pack(fill="x", padx=10, pady=10)
        
        info_frame = tk.Frame(section, bg=self.colors["bg_hover"], padx=15, pady=10)
        info_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            info_frame,
            text="📷 Image Trigger will capture the latest image from the specified folder\n"
                 "    every time the trigger is active. The image will be saved and displayed in the Image column.",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            justify="left"
        ).pack(anchor="w")
        
        self.image_triggers_frame = tk.Frame(section, bg=self.colors["bg_card"])
        self.image_triggers_frame.pack(fill="x", pady=10)
        
        self._load_image_triggers()
        
        btn_frame = tk.Frame(section, bg=self.colors["bg_card"])
        btn_frame.pack(fill="x", pady=10)
        
        tk.Button(
            btn_frame, text="➕ Add Image Trigger",
            font=("Segoe UI", 10),
            bg=self.colors["accent_green"], fg="#1e1e2e",
            relief="flat", cursor="hand2", padx=15, pady=8,
            command=self._add_image_trigger
        ).pack(side="left")
    
    def _load_image_triggers(self):
        for widget in self.image_triggers_frame.winfo_children():
            widget.destroy()
        self.image_trigger_widgets = []
        triggers = self.controller.data_manager.trigger_config.get("image_triggers", [])
        for idx, trigger in enumerate(triggers):
            self._create_image_trigger_widget(idx, trigger)
    
    def _create_image_trigger_widget(self, idx, trigger_data=None):
        if trigger_data is None:
            trigger_data = {
                "name": f"Image Trigger {idx + 1}",
                "enabled": True, "folder_path": "",
                "address": {"area_type": "WR", "address": 200, "bit": 0},
                "trigger_type": "rising"
            }
        
        frame = tk.LabelFrame(
            self.image_triggers_frame,
            text=f"Image Trigger #{idx + 1}",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            padx=15, pady=10
        )
        frame.pack(fill="x", pady=5)
        
        widgets = {"frame": frame}
        
        # Row 1: Enable & Name
        row1 = tk.Frame(frame, bg=self.colors["bg_hover"])
        row1.pack(fill="x", pady=5)
        
        enabled_var = tk.BooleanVar(value=trigger_data.get("enabled", True))
        tk.Checkbutton(
            row1, text="Enable", variable=enabled_var,
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            activebackground=self.colors["bg_hover"],
            selectcolor=self.colors["bg_card"]
        ).pack(side="left")
        widgets["enabled"] = enabled_var
        
        tk.Label(row1, text="Name:", font=("Segoe UI", 10),
                 bg=self.colors["bg_hover"], fg=self.colors["text_secondary"]
                 ).pack(side="left", padx=(20, 5))
        
        name_entry = tk.Entry(
            row1, font=("Segoe UI", 10),
            bg=self.colors["bg_card"], fg=self.colors["text_primary"],
            relief="flat", width=20
        )
        name_entry.insert(0, trigger_data.get("name", ""))
        name_entry.pack(side="left", ipady=3)
        widgets["name"] = name_entry
        
        tk.Button(
            row1, text="🗑️", font=("Segoe UI", 9),
            bg=self.colors["accent_red"], fg="#1e1e2e",
            relief="flat", cursor="hand2",
            command=lambda f=frame, w=widgets: self._delete_image_trigger(f, w)
        ).pack(side="right")
        
        # Row 2: Trigger Address  ── with LAMP on far right
        row2 = tk.Frame(frame, bg=self.colors["bg_hover"])
        row2.pack(fill="x", pady=5)
        
        tk.Label(row2, text="Address:", font=("Segoe UI", 10),
                 bg=self.colors["bg_hover"], fg=self.colors["text_secondary"]
                 ).pack(side="left")
        
        addr_config = trigger_data.get("address", {})
        
        area_var = tk.StringVar(value=addr_config.get("area_type", "WR"))
        area_combo = ttk.Combobox(
            row2, textvariable=area_var,
            values=list(PLC_MEMORY_AREAS.keys()),
            width=6, state="readonly"
        )
        area_combo.pack(side="left", padx=5)
        widgets["area_type"] = area_var
        
        addr_entry = tk.Entry(
            row2, font=("Segoe UI", 10),
            bg=self.colors["bg_card"], fg=self.colors["text_primary"],
            relief="flat", width=8
        )
        addr_entry.insert(0, str(addr_config.get("address", 200)))
        addr_entry.pack(side="left", padx=5, ipady=3)
        widgets["address"] = addr_entry
        
        tk.Label(row2, text="Bit:", font=("Segoe UI", 10),
                 bg=self.colors["bg_hover"], fg=self.colors["text_secondary"]
                 ).pack(side="left", padx=(10, 5))
        
        bit_entry = tk.Entry(
            row2, font=("Segoe UI", 10),
            bg=self.colors["bg_card"], fg=self.colors["text_primary"],
            relief="flat", width=4
        )
        bit_entry.insert(0, str(addr_config.get("bit", 0)))
        bit_entry.pack(side="left", ipady=3)
        widgets["bit"] = bit_entry
        
        tk.Label(row2, text="Type:", font=("Segoe UI", 10),
                 bg=self.colors["bg_hover"], fg=self.colors["text_secondary"]
                 ).pack(side="left", padx=(20, 5))
        
        type_var = tk.StringVar(value=trigger_data.get("trigger_type", "rising"))
        type_combo = ttk.Combobox(
            row2, textvariable=type_var,
            values=list(TRIGGER_TYPES.keys()),
            width=10, state="readonly"
        )
        type_combo.pack(side="left")
        widgets["trigger_type"] = type_var
        
        # ── LAMP indicator ──────────────────────────────────
        lamp = tk.Label(
            row2, text="⬤", font=("Segoe UI", 22),
            bg=self.colors["bg_hover"], fg="#444444"
        )
        lamp.pack(side="left", padx=(15, 2))
        lamp_lbl = tk.Label(
            row2, text="—", font=("Segoe UI", 9, "bold"),
            bg=self.colors["bg_hover"], fg=self.colors["text_secondary"]
        )
        lamp_lbl.pack(side="left")
        widgets["lamp"] = lamp
        widgets["lamp_lbl"] = lamp_lbl
        # ────────────────────────────────────────────────────
        
        # Row 3: Folder Path
        row3 = tk.Frame(frame, bg=self.colors["bg_hover"])
        row3.pack(fill="x", pady=5)
        
        tk.Label(row3, text="Folder:", font=("Segoe UI", 10),
                 bg=self.colors["bg_hover"], fg=self.colors["text_secondary"]
                 ).pack(side="left")
        
        folder_entry = tk.Entry(
            row3, font=("Segoe UI", 10),
            bg=self.colors["bg_card"], fg=self.colors["text_primary"],
            relief="flat", width=40
        )
        folder_entry.insert(0, trigger_data.get("folder_path", ""))
        folder_entry.pack(side="left", padx=5, ipady=3)
        widgets["folder_path"] = folder_entry
        
        tk.Button(
            row3, text="📁 Browse", font=("Segoe UI", 9),
            bg=self.colors["accent"], fg="#1e1e2e",
            relief="flat", cursor="hand2",
            command=lambda e=folder_entry: self._browse_folder(e)
        ).pack(side="left", padx=5)
        
        self.image_trigger_widgets.append(widgets)
    
    def _browse_folder(self, entry_widget):
        folder = filedialog.askdirectory(title="Select Image Folder")
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)
    
    def _add_image_trigger(self):
        self._create_image_trigger_widget(len(self.image_trigger_widgets))
    
    def _delete_image_trigger(self, frame, widgets):
        if len(self.image_trigger_widgets) > 0:
            frame.destroy()
            self.image_trigger_widgets.remove(widgets)
    
    # ================================================================
    # SAVE BUTTON
    # ================================================================

    def _create_save_button(self, parent):
        frame = tk.Frame(parent, bg=self.colors["bg_dark"])
        frame.pack(fill="x", padx=10, pady=20)
        
        tk.Button(
            frame, text="💾 Save Trigger Configuration",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["accent_green"], fg="#1e1e2e",
            relief="flat", cursor="hand2",
            padx=40, pady=15,
            command=self._save_config
        ).pack()
    
    def _save_config(self):
        try:
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
            # Restart monitor with new config
            self._start_monitor()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    # ================================================================
    # LIVE LAMP MONITOR  (auto-start on show, stop on hide)
    # ================================================================

    def _start_monitor(self):
        """Connect to PLC and start polling all trigger addresses."""
        self._stop_monitor()
        self._monitor_running = True
        self._set_all_lamps("#888888", "…")  # grey while connecting
        
        def _connect():
            from utils.plc_fins import PLCFinsClient
            client = PLCFinsClient(self.controller.plc_config)
            ok, msg = client.connect()
            if ok and self._monitor_running:
                self._monitor_client = client
                self.after(0, self._poll_all)
            else:
                self._monitor_running = False
                self.after(0, lambda: self._set_all_lamps("#f38ba8", "No PLC"))
        
        threading.Thread(target=_connect, daemon=True).start()
    
    def _stop_monitor(self):
        self._monitor_running = False
        if self._monitor_client:
            try: self._monitor_client.disconnect()
            except: pass
            self._monitor_client = None
        self._set_all_lamps("#444444", "—")
    
    def _set_all_lamps(self, color, text):
        """Reset all lamps to a given color and text."""
        try:
            if self._main_lamp:
                self._main_lamp.configure(fg=color)
            if self._main_lamp_lbl:
                self._main_lamp_lbl.configure(text=text)
            for w in self.image_trigger_widgets:
                if "lamp" in w:
                    w["lamp"].configure(fg=color)
                    w["lamp_lbl"].configure(text=text)
        except Exception:
            pass
    
    def _poll_all(self):
        """Read all trigger addresses in background, update lamps, reschedule."""
        if not self._monitor_running or not self._monitor_client:
            return
        
        # Snapshot current addresses from UI
        try:
            main_area = self.main_area_var.get()
            main_addr = int(self.main_addr_entry.get())
            main_bit  = int(self.main_bit_entry.get())
        except Exception:
            self.after(500, self._poll_all)
            return
        
        image_configs = []
        for w in self.image_trigger_widgets:
            try:
                image_configs.append({
                    "area": w["area_type"].get(),
                    "addr": int(w["address"].get()),
                    "bit":  int(w["bit"].get()),
                    "lamp": w["lamp"],
                    "lbl":  w["lamp_lbl"]
                })
            except Exception:
                pass
        
        def _read():
            client = self._monitor_client
            if not client or not client.connected:
                self.after(0, lambda: self._set_all_lamps("#f38ba8", "Err"))
                self._monitor_running = False
                return
            
            # Main trigger
            ok, data = client.read_memory(main_area, main_addr, 1)
            if ok and data:
                word    = data[0]
                bit_val = (word >> main_bit) & 1
                color   = "#a6e3a1" if bit_val else "#f38ba8"
                text    = "ON" if bit_val else "OFF"
                self.after(0, lambda c=color, t=text: (
                    self._main_lamp.configure(fg=c),
                    self._main_lamp_lbl.configure(text=t, fg=c)
                ))
                # Rising edge → save data to dashboard (same as PLC Read button)
                if bit_val == 1 and self._last_main_bit == 0:
                    self.after(0, self._trigger_save_data)
                self._last_main_bit = bit_val
            
            # Image triggers
            for cfg in image_configs:
                ok2, data2 = client.read_memory(cfg["area"], cfg["addr"], 1)
                lamp = cfg["lamp"]; lbl = cfg["lbl"]
                if ok2 and data2:
                    bv     = (data2[0] >> cfg["bit"]) & 1
                    color2 = "#a6e3a1" if bv else "#f38ba8"
                    text2  = "ON" if bv else "OFF"
                    self.after(0, lambda l=lamp, lb=lbl, c=color2, t=text2: (
                        l.configure(fg=c), lb.configure(text=t, fg=c)
                    ))
            
            if self._monitor_running:
                self.after(400, self._poll_all)
        
        threading.Thread(target=_read, daemon=True).start()
    
    def _trigger_save_data(self):
        """Rising edge on main trigger lamp → save data to dashboard (same as PLC Read button)."""
        dashboard = self.controller.pages.get("dashboard")
        if not dashboard:
            print("[TriggerSettings] Dashboard page not found.")
            return
        
        # Share the already-open monitor client so dashboard doesn't open a 2nd connection
        dashboard._plc_client = self._monitor_client
        print(f"[TriggerSettings] Rising edge detected → saving data row")
        dashboard._read_plc_and_save_row(capture_images=True)
    
    # ================================================================
    # PAGE LIFECYCLE
    # ================================================================

    def on_show(self):
        """Auto-start monitor when page opens."""
        self._load_image_triggers()
        self._last_main_bit = 0  # reset edge state on page open
        self._start_monitor()
    
    def on_hide(self):
        """Stop monitor when navigating away."""
        self._stop_monitor()
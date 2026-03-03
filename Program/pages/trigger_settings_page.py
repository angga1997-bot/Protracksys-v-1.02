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
                 "• Use Rising Edge for a single trigger when the signal rises",
            font=("Segoe UI", 10),
            bg=self.colors["accent_yellow"],
            fg="#1e1e2e",
            justify="left"
        ).pack(anchor="w", pady=(5, 0))
    
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
"""
pages/plc_settings_page.py - PLC FINS TCP/IP Settings Page
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from pages.base_page import BasePage
from config import COLORS, PLC_MEMORY_AREAS
from utils.plc_fins import PLCFinsClient


class PLCSettingsPage(BasePage):
    """PLC FINS TCP/IP connection settings page"""
    
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.conn_entries = {}
        self.area_widgets = []
        self._create_widgets()
    
    def _create_widgets(self):
        """Creates page widgets"""
        # Header
        self.create_header("🔌 PLC Settings", "FINS TCP/IP connection configuration")
        
        # Main content dengan scroll
        canvas = tk.Canvas(self, bg=self.colors["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.colors["bg_dark"])
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Sections
        self._create_connection_section(scroll_frame)
        self._create_read_areas_section(scroll_frame)
        self._create_test_section(scroll_frame)
        self._create_save_button(scroll_frame)
        
        # Mouse wheel
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    def _create_connection_section(self, parent):
        """Creates connection section"""
        section = tk.LabelFrame(
            parent,
            text="🌐 TCP/IP Connection",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            padx=20,
            pady=15
        )
        section.pack(fill="x", padx=10, pady=10)
        
        config = self.controller.plc_config.get("connection", {})
        
        # Grid layout
        grid_frame = tk.Frame(section, bg=self.colors["bg_card"])
        grid_frame.pack(fill="x", pady=10)
        
        fields = [
            ("PLC IP Address", "plc_ip", config.get("plc_ip", "192.168.1.1"), 0, 0),
            ("PLC Port", "plc_port", str(config.get("plc_port", 9600)), 0, 1),
            ("Timeout (sec)", "timeout", str(config.get("timeout", 5)), 1, 0),
        ]
        
        for label, key, default, row, col in fields:
            self._create_input_field(grid_frame, label, key, default, row, col)
        
        # Info FINS
        info_frame = tk.Frame(section, bg=self.colors["accent_yellow"], padx=15, pady=10)
        info_frame.pack(fill="x", pady=10)
        
        tk.Label(
            info_frame,
            text="💡 Info: Default FINS TCP port is 9600.",
            font=("Segoe UI", 9),
            bg=self.colors["accent_yellow"],
            fg="#1e1e2e"
        ).pack(anchor="w")
    
    def _create_input_field(self, parent, label, key, default, row, col):
        """Creates input field"""
        frame = tk.Frame(parent, bg=self.colors["bg_card"])
        frame.grid(row=row, column=col, padx=15, pady=8, sticky="w")
        
        tk.Label(
            frame,
            text=f"{label}:",
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"],
            width=18,
            anchor="w"
        ).pack(side="left")
        
        entry = tk.Entry(
            frame,
            font=("Segoe UI", 11),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            relief="flat",
            width=20
        )
        entry.insert(0, default)
        entry.pack(side="left", ipady=6)
        
        self.conn_entries[key] = entry
    
    def _create_read_areas_section(self, parent):
        """Creates memory read areas section"""
        section = tk.LabelFrame(
            parent,
            text="📖 Memory Read Areas",
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
            text="📍 Specify PLC memory areas to be read (DM, CIO, WR, HR, AR, EM)",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"]
        ).pack(anchor="w")
        
        # Area list frame
        self.areas_frame = tk.Frame(section, bg=self.colors["bg_card"])
        self.areas_frame.pack(fill="x", pady=10)
        
        # Header
        header_frame = tk.Frame(self.areas_frame, bg=self.colors["bg_active"])
        header_frame.pack(fill="x", pady=(0, 5))
        
        headers = [("✓", 3), ("Area Name", 15), ("Type", 8), ("Start Addr", 12), ("Length", 10), ("Action", 6)]
        for text, width in headers:
            tk.Label(
                header_frame,
                text=text,
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["bg_active"],
                fg=self.colors["text_primary"],
                width=width,
                pady=8
            ).pack(side="left", padx=2)
        
        # Area entries container
        self.area_rows_frame = tk.Frame(self.areas_frame, bg=self.colors["bg_card"])
        self.area_rows_frame.pack(fill="x")
        
        # Add button
        btn_frame = tk.Frame(section, bg=self.colors["bg_card"])
        btn_frame.pack(fill="x", pady=10)
        
        tk.Button(
            btn_frame,
            text="➕ Add Area",
            font=("Segoe UI", 10),
            bg=self.colors["accent_green"],
            fg="#1e1e2e",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8,
            command=self._add_read_area
        ).pack(side="left")
        
        # Memory area reference
        self._create_memory_reference(section)
    
    def _create_memory_reference(self, parent):
        """Creates memory area reference"""
        ref_frame = tk.LabelFrame(
            parent,
            text="📚 Omron PLC Memory Area Reference",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            padx=10,
            pady=10
        )
        ref_frame.pack(fill="x", pady=10)
        
        ref_data = [
            ("DM", "Data Memory", "D0 - D32767", "General purpose data storage"),
            ("CIO", "Core I/O", "CIO 0 - CIO 6143", "I/O and internal relays"),
            ("WR", "Work Area", "W0 - W511", "Temporary work relays"),
            ("HR", "Holding Area", "H0 - H1535", "Retained data"),
            ("AR", "Auxiliary Area", "A0 - A959", "System/auxiliary area"),
            ("EM", "Extended Memory", "E0_0 - E18_32767", "Extended memory")
        ]
        
        for area, name, range_text, desc in ref_data:
            row = tk.Frame(ref_frame, bg=self.colors["bg_hover"])
            row.pack(fill="x", pady=2)
            
            tk.Label(
                row, text=area, font=("Segoe UI", 9, "bold"),
                bg=self.colors["accent"], fg="#1e1e2e",
                width=5, padx=5
            ).pack(side="left", padx=(0, 10))
            
            tk.Label(
                row, text=f"{name} ({range_text})",
                font=("Segoe UI", 9),
                bg=self.colors["bg_hover"],
                fg=self.colors["text_primary"],
                width=30, anchor="w"
            ).pack(side="left")
            
            tk.Label(
                row, text=desc,
                font=("Segoe UI", 9),
                bg=self.colors["bg_hover"],
                fg=self.colors["text_secondary"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True)
    
    def _load_read_areas(self):
        """Load read areas from config"""
        # Clear existing
        for widget in self.area_rows_frame.winfo_children():
            widget.destroy()
        self.area_widgets = []
        
        # Load areas
        areas = self.controller.plc_config.get("read_areas", [])
        
        if not areas:
            # Add default area
            areas = [{"name": "Data Area 1", "area_type": "DM", "start_address": 0, "length": 10, "enabled": True}]
        
        for area in areas:
            self._create_area_row(area)
    
    def _create_area_row(self, area_data=None):
        """Creates read area row"""
        if area_data is None:
            area_data = {
                "name": f"Area {len(self.area_widgets) + 1}",
                "area_type": "DM",
                "start_address": 0,
                "length": 10,
                "enabled": True
            }
        
        row_frame = tk.Frame(self.area_rows_frame, bg=self.colors["bg_card"])
        row_frame.pack(fill="x", pady=2)
        
        widgets = {}
        
        # Enabled checkbox
        enabled_var = tk.BooleanVar(value=area_data.get("enabled", True))
        cb = tk.Checkbutton(
            row_frame,
            variable=enabled_var,
            bg=self.colors["bg_card"],
            activebackground=self.colors["bg_card"],
            selectcolor=self.colors["bg_hover"]
        )
        cb.pack(side="left", padx=5)
        widgets["enabled"] = enabled_var
        
        # Name
        name_entry = tk.Entry(
            row_frame,
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            width=15,
            relief="flat"
        )
        name_entry.insert(0, area_data.get("name", ""))
        name_entry.pack(side="left", padx=5, ipady=4)
        widgets["name"] = name_entry
        
        # Area type dropdown
        type_var = tk.StringVar(value=area_data.get("area_type", "DM"))
        type_combo = ttk.Combobox(
            row_frame,
            textvariable=type_var,
            values=list(PLC_MEMORY_AREAS.keys()),
            width=6,
            state="readonly"
        )
        type_combo.pack(side="left", padx=5)
        widgets["area_type"] = type_var
        
        # Start address
        addr_entry = tk.Entry(
            row_frame,
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            width=10,
            relief="flat"
        )
        addr_entry.insert(0, str(area_data.get("start_address", 0)))
        addr_entry.pack(side="left", padx=5, ipady=4)
        widgets["start_address"] = addr_entry
        
        # Length
        len_entry = tk.Entry(
            row_frame,
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            width=8,
            relief="flat"
        )
        len_entry.insert(0, str(area_data.get("length", 10)))
        len_entry.pack(side="left", padx=5, ipady=4)
        widgets["length"] = len_entry
        
        # Delete button
        del_btn = tk.Button(
            row_frame,
            text="🗑️",
            font=("Segoe UI", 9),
            bg=self.colors["accent_red"],
            fg="#1e1e2e",
            relief="flat",
            cursor="hand2",
            command=lambda f=row_frame, w=widgets: self._delete_area_row(f, w)
        )
        del_btn.pack(side="left", padx=5)
        
        widgets["frame"] = row_frame
        self.area_widgets.append(widgets)
    
    def _add_read_area(self):
        """Add new read area"""
        self._create_area_row()
    
    def _delete_area_row(self, frame, widgets):
        """Delete area row"""
        if len(self.area_widgets) > 1:
            frame.destroy()
            self.area_widgets.remove(widgets)
        else:
            messagebox.showwarning("Warning", "At least 1 read area must exist!")
    
    def _create_test_section(self, parent):
        """Creates connection test section"""
        section = tk.LabelFrame(
            parent,
            text="🔧 Test Connection",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            padx=20,
            pady=15
        )
        section.pack(fill="x", padx=10, pady=10)
        
        # Buttons
        btn_frame = tk.Frame(section, bg=self.colors["bg_card"])
        btn_frame.pack(fill="x", pady=10)
        
        self.test_btn = tk.Button(
            btn_frame,
            text="🔌 Test Connection",
            font=("Segoe UI", 11),
            bg=self.colors["accent"],
            fg="#1e1e2e",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            command=self._test_connection
        )
        self.test_btn.pack(side="left", padx=10)
        
        self.read_btn = tk.Button(
            btn_frame,
            text="📖 Test Read Data",
            font=("Segoe UI", 11),
            bg=self.colors["accent_purple"],
            fg="#1e1e2e",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            command=self._test_read
        )
        self.read_btn.pack(side="left", padx=10)
        
        # Status
        self.status_frame = tk.Frame(section, bg=self.colors["bg_hover"], padx=15, pady=10)
        self.status_frame.pack(fill="x", pady=10)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Status: Not tested yet",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"]
        )
        self.status_label.pack(anchor="w")
        
        # Result text
        self.result_text = tk.Text(
            section,
            font=("Consolas", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            height=8,
            relief="flat",
            padx=10,
            pady=10
        )
        self.result_text.pack(fill="x", pady=10)
        self.result_text.insert("1.0", "Test results will appear here...")
        self.result_text.configure(state="disabled")
    
    def _create_save_button(self, parent):
        """Creates save button"""
        save_frame = tk.Frame(parent, bg=self.colors["bg_dark"])
        save_frame.pack(fill="x", padx=10, pady=20)
        
        tk.Button(
            save_frame,
            text="💾 Save All Configuration",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["accent_green"],
            fg="#1e1e2e",
            relief="flat",
            cursor="hand2",
            padx=40,
            pady=15,
            command=self._save_config
        ).pack()
    
    def _update_status(self, message, color="text_secondary"):
        """Update status label"""
        self.status_label.configure(
            text=f"Status: {message}",
            fg=self.colors.get(color, self.colors["text_secondary"])
        )
    
    def _update_result(self, text):
        """Update result text"""
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")
    
    def _get_current_config(self):
        """Get current configuration from input"""
        config = {
            "connection": {},
            "read_areas": []
        }
        
        # Connection
        for key, entry in self.conn_entries.items():
            value = entry.get().strip()
            if key in ["plc_port", "timeout"]:
                try:
                    value = int(value)
                except:
                    value = 9600 if key == "plc_port" else 5
            config["connection"][key] = value
        
        # Read areas
        for widgets in self.area_widgets:
            try:
                area = {
                    "name": widgets["name"].get().strip(),
                    "area_type": widgets["area_type"].get(),
                    "start_address": int(widgets["start_address"].get()),
                    "length": int(widgets["length"].get()),
                    "enabled": widgets["enabled"].get()
                }
                config["read_areas"].append(area)
            except:
                pass
        
        return config
    
    def _test_connection(self):
        """Test connection to PLC"""
        self._update_status("Connecting...", "accent_yellow")
        self.test_btn.configure(state="disabled")
        
        def do_test():
            config = self._get_current_config()
            client = PLCFinsClient(config)
            success, message = client.test_connection()
            
            self.after(0, lambda: self._on_test_complete(success, message))
        
        threading.Thread(target=do_test, daemon=True).start()
    
    def _on_test_complete(self, success, message):
        """Callback after test complete"""
        self.test_btn.configure(state="normal")
        
        if success:
            self._update_status("✅ Connection successful!", "accent_green")
            self._update_result(f"✅ Connection Test Successful!\n\n{message}")
        else:
            self._update_status(f"❌ {message}", "accent_red")
            self._update_result(f"❌ Connection Test Failed!\n\nError: {message}")
    
    def _test_read(self):
        """Test read data from PLC"""
        self._update_status("Reading data...", "accent_yellow")
        self.read_btn.configure(state="disabled")
        
        def do_read():
            config = self._get_current_config()
            client = PLCFinsClient(config)
            
            success, msg = client.connect()
            if not success:
                self.after(0, lambda: self._on_read_complete(False, f"Connection failed: {msg}", []))
                return
            
            results = []
            for area in config["read_areas"]:
                if area.get("enabled", True):
                    ok, data = client.read_memory(
                        area["area_type"],
                        area["start_address"],
                        area["length"]
                    )
                    results.append({
                        "area": area,
                        "success": ok,
                        "data": data
                    })
            
            client.disconnect()
            self.after(0, lambda: self._on_read_complete(True, "Finished", results))
        
        threading.Thread(target=do_read, daemon=True).start()
    
    def _on_read_complete(self, success, message, results):
        """Callback after read complete - shows full table with hex + ASCII"""
        self.read_btn.configure(state="normal")

        if not success:
            self._update_status(f"❌ {message}", "accent_red")
            self._update_result(f"❌ Read Test Failed!\n\nError: {message}")
            return

        output = "📖 PLC Data Reading Results:\n"
        output += "=" * 65 + "\n\n"

        for r in results:
            area = r["area"]
            output += (f"📍 {area['name']}  |  "
                       f"{area['area_type']} {area['start_address']}  |  "
                       f"Length: {area['length']} words\n")

            if not r["success"]:
                output += f"   ❌ Error: {r['data']}\n\n"
                continue

            words = r["data"]
            if not isinstance(words, (list, tuple)):
                output += f"   ❌ Unexpected data type: {type(words)}\n\n"
                continue

            output += f"   ✅ OK — {len(words)} word(s) received\n"
            output += f"   {'Addr':<8} {'Dec':>6}  {'Hex':>6}  {'ASCII':>5}\n"
            output += "   " + "-" * 40 + "\n"

            base = area["start_address"]
            for i, w in enumerate(words):
                addr = base + i
                # ASCII: high byte → char1, low byte → char2
                hi = (w >> 8) & 0xFF
                lo = w & 0xFF
                c1 = chr(hi) if 0x20 <= hi <= 0x7E else "."
                c2 = chr(lo) if 0x20 <= lo <= 0x7E else "."
                ascii_str = c1 + c2
                output += f"   {area['area_type']}{addr:<5}  {w:>6}  0x{w:04X}   {ascii_str}\n"

            output += "\n"

        self._update_status(f"✅ Read OK — {sum(len(r['data']) if r['success'] and isinstance(r['data'], list) else 0 for r in results)} word(s) total",
                            "accent_green")
        self._update_result(output)
    
    def _save_config(self):
        """Save configuration"""
        config = self._get_current_config()
        
        # Validasi
        conn = config["connection"]
        if not conn.get("plc_ip"):
            messagebox.showerror("Error", "PLC IP Address must be filled!")
            return
        
        if not config["read_areas"]:
            messagebox.showerror("Error", "At least 1 read area must exist!")
            return
        
        # Simpan
        self.controller.plc_config.update(config)
        self.controller.save_plc_config()
        
        messagebox.showinfo("Success", "✅ PLC configuration saved successfully!")
    
    def on_show(self):
        """Called when page is shown"""
        self._load_read_areas()
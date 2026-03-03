"""
pages/table_settings_page.py - Table settings page with column reordering
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pages.base_page import BasePage
from config import COLORS, PLC_MEMORY_AREAS


class TableSettingsPage(BasePage):
    """Table structure settings page with image support and reordering"""
    
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.column_widgets = []
        self._create_widgets()
    
    def _create_widgets(self):
        """Creates widgets"""
        # Header
        self.create_header("📋 Table Settings", "Configure table structure and data sources")
        
        # Scrollable content
        self.canvas = tk.Canvas(self, bg=self.colors["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=self.colors["bg_dark"])
        
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Info section
        self._create_info_section(self.scroll_frame)
        
        # Columns section
        self._create_columns_section(self.scroll_frame)
        
        # Preview section
        self._create_preview_section(self.scroll_frame)
        
        # Save button
        self._create_save_button(self.scroll_frame)
        
        # MouseWheel handled globally in main.py
    
    def _create_info_section(self, parent):
        """Info section"""
        info = tk.Frame(parent, bg=self.colors["accent_yellow"], padx=20, pady=15)
        info.pack(fill="x", padx=10, pady=10)
        
        tk.Label(
            info,
            text="💡 Data Source Configuration",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["accent_yellow"],
            fg="#1e1e2e"
        ).pack(anchor="w")
        
        tk.Label(
            info,
            text="Each column can be pulled from:\n"
                 "• Manual Input - Data entered manually\n"
                 "• PLC Memory - Data from PLC reading\n"
                 "• Image Folder - Latest image from folder (by trigger)\n"
                 "• Auto Number/Date/Time - Automatic\n\n"
                 "💡 Use ⬆️ ⬇️ buttons to shift column order, or click 📍 to move to a specific position",
            font=("Segoe UI", 10),
            bg=self.colors["accent_yellow"],
            fg="#1e1e2e",
            justify="left"
        ).pack(anchor="w", pady=(5, 0))
    
    def _create_columns_section(self, parent):
        """Columns settings section"""
        section = tk.LabelFrame(
            parent,
            text="📋 Column Configuration",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            padx=20,
            pady=15
        )
        section.pack(fill="x", padx=10, pady=10)
        
        # Quick reorder sub-section
        reorder_frame = tk.Frame(section, bg=self.colors["bg_card"])
        reorder_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            reorder_frame,
            text="🔄 Quick Reorder:",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"]
        ).pack(side="left")
        
        tk.Button(
            reorder_frame, text="🔀 Reverse Order",
            font=("Segoe UI", 9),
            bg=self.colors["accent_purple"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", padx=10, pady=3,
            command=self._reverse_columns
		).pack(side="left", padx=5)
        
        tk.Button(
            reorder_frame, text="🔃 Reset Default",
            font=("Segoe UI", 9),
            bg=self.colors["accent_orange"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", padx=10, pady=3,
            command=self._reset_to_default
        ).pack(side="left", padx=5)
        
        self.columns_frame = tk.Frame(section, bg=self.colors["bg_card"])
        self.columns_frame.pack(fill="x", pady=10)
        
        # Add column buttons
        btn_frame = tk.Frame(section, bg=self.colors["bg_card"])
        btn_frame.pack(fill="x", pady=10)
        
        tk.Label(
            btn_frame,
            text="➕ Add Column:",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"]
        ).pack(side="left", padx=(0, 10))
        
        buttons = [
            ("📝 Manual", "manual", "accent_green"),
            ("📊 PLC", "plc", "accent_purple"),
            ("📷 Image", "image", "accent_orange"),
            ("🔢 No.", "auto_number", "accent_teal"),
            ("📅 Date", "auto_date", "accent_yellow"),
            ("🕐 Time", "auto_time", "accent_pink")
        ]
        
        for text, source, color in buttons:
            tk.Button(
                btn_frame, text=text,
                font=("Segoe UI", 9),
                bg=self.colors[color],
                fg="#1e1e2e", relief="flat",
                cursor="hand2", padx=10, pady=5,
                command=lambda s=source: self._add_column(s)
            ).pack(side="left", padx=3)
    
    def _create_preview_section(self, parent):
        """Section preview"""
        section = tk.LabelFrame(
            parent,
            text="👁️ Column Order Preview",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            padx=20,
            pady=15
        )
        section.pack(fill="x", padx=10, pady=10)
        
        self.preview_frame = tk.Frame(section, bg=self.colors["bg_card"])
        self.preview_frame.pack(fill="x", pady=10)
    
    def _create_save_button(self, parent):
        """Save button"""
        frame = tk.Frame(parent, bg=self.colors["bg_dark"])
        frame.pack(fill="x", padx=10, pady=20)
        
        tk.Button(
            frame,
            text="💾 Save All Changes",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["accent"],
            fg="#1e1e2e",
            relief="flat",
            cursor="hand2",
            padx=40,
            pady=15,
            command=self._save_settings
        ).pack()
    
    def _load_columns(self):
        """Load column list"""
        for w in self.columns_frame.winfo_children():
            w.destroy()
        self.column_widgets = []
        
        columns = self.controller.table_data.get("columns", [])
        
        for idx, col in enumerate(columns):
            self._create_column_widget(idx, col)
    
    def _create_column_widget(self, idx, col_data):
        """Create widget for one column"""
        if isinstance(col_data, str):
            col_data = {
                "name": col_data,
                "width": 150,
                "data_source": "manual",
                "plc_config": None,
                "image_config": None
            }
        
        total_columns = len(self.controller.table_data.get("columns", []))
        
        # Main frame
        col_frame = tk.LabelFrame(
            self.columns_frame,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            padx=15,
            pady=10
        )
        col_frame.pack(fill="x", pady=5)
        
        widgets = {"frame": col_frame, "index": idx}
        
        # Header row with position controls
        header_row = tk.Frame(col_frame, bg=self.colors["bg_hover"])
        header_row.pack(fill="x", pady=(0, 8))
        
        # Position indicator
        pos_frame = tk.Frame(header_row, bg=self.colors["accent"], padx=8, pady=2)
        pos_frame.pack(side="left")
        
        tk.Label(
            pos_frame,
            text=f"#{idx + 1}",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["accent"],
            fg="#1e1e2e"
        ).pack(side="left")
        
        # Move buttons
        move_frame = tk.Frame(header_row, bg=self.colors["bg_hover"])
        move_frame.pack(side="left", padx=10)
        
        # Move to top button
        tk.Button(
            move_frame, text="⏫",
            font=("Segoe UI", 9),
            bg=self.colors["accent_teal"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", width=3,
            command=lambda i=idx: self._move_column_to_top(i),
            state="normal" if idx > 0 else "disabled"
        ).pack(side="left", padx=1)
        
        # Move up button
        tk.Button(
            move_frame, text="⬆️",
            font=("Segoe UI", 9),
            bg=self.colors["accent_green"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", width=3,
            command=lambda i=idx: self._move_column_up(i),
            state="normal" if idx > 0 else "disabled"
        ).pack(side="left", padx=1)
        
        # Move down button
        tk.Button(
            move_frame, text="⬇️",
            font=("Segoe UI", 9),
            bg=self.colors["accent_green"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", width=3,
            command=lambda i=idx: self._move_column_down(i),
            state="normal" if idx < total_columns - 1 else "disabled"
        ).pack(side="left", padx=1)
        
        # Move to bottom button
        tk.Button(
            move_frame, text="⏬",
            font=("Segoe UI", 9),
            bg=self.colors["accent_teal"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", width=3,
            command=lambda i=idx: self._move_column_to_bottom(i),
            state="normal" if idx < total_columns - 1 else "disabled"
        ).pack(side="left", padx=1)
        
        # Move to specific position button
        tk.Button(
            move_frame, text="📍 Move to...",
            font=("Segoe UI", 9),
            bg=self.colors["accent_purple"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", padx=5,
            command=lambda i=idx: self._move_column_to_position(i)
        ).pack(side="left", padx=5)
        
        # Source type badge
        source = col_data.get("data_source", "manual")
        source_colors = {
            "manual": self.colors["accent"],
            "plc": self.colors["accent_purple"],
            "image": self.colors["accent_orange"],
            "auto_number": self.colors["accent_teal"],
            "auto_date": self.colors["accent_yellow"],
            "auto_time": self.colors["accent_pink"]
        }
        source_icons = {
            "manual": "📝", "plc": "📊", "image": "📷",
            "auto_number": "🔢", "auto_date": "📅", "auto_time": "🕐"
        }
        
        tk.Label(
            header_row,
            text=f"{source_icons.get(source, '')} {source.upper()}",
            font=("Segoe UI", 9, "bold"),
            bg=source_colors.get(source, self.colors["accent"]),
            fg="#1e1e2e",
            padx=8, pady=2
        ).pack(side="left", padx=10)
        
        # Delete button (right side)
        tk.Button(
            header_row, text="🗑️ Delete",
            font=("Segoe UI", 9),
            bg=self.colors["accent_red"],
            fg="#1e1e2e", relief="flat",
            cursor="hand2", padx=8,
            command=lambda i=idx: self._delete_column(i)
        ).pack(side="right")
        
        # Row 1: Name & Width
        row1 = tk.Frame(col_frame, bg=self.colors["bg_hover"])
        row1.pack(fill="x", pady=5)
        
        tk.Label(
            row1, text="Name:",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"]
        ).pack(side="left")
        
        name_entry = tk.Entry(
            row1,
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            relief="flat", width=20
        )
        name_entry.insert(0, col_data.get("name", ""))
        name_entry.pack(side="left", padx=5, ipady=4)
        widgets["name"] = name_entry
        
        tk.Label(
            row1, text="Width:",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"]
        ).pack(side="left", padx=(20, 5))
        
        width_entry = tk.Entry(
            row1,
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            relief="flat", width=6
        )
        width_entry.insert(0, str(col_data.get("width", 150)))
        width_entry.pack(side="left", ipady=4)
        widgets["width"] = width_entry
        
        tk.Label(
            row1, text="px",
            font=("Segoe UI", 9),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"]
        ).pack(side="left", padx=2)
        
        # Row 2: Data Source
        row2 = tk.Frame(col_frame, bg=self.colors["bg_hover"])
        row2.pack(fill="x", pady=5)
        
        tk.Label(
            row2, text="Source:",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"]
        ).pack(side="left")
        
        source_var = tk.StringVar(value=col_data.get("data_source", "manual"))
        widgets["data_source"] = source_var
        
        sources = [
            ("Manual", "manual"),
            ("PLC", "plc"),
            ("Image", "image"),
            ("No.", "auto_number"),
            ("Date", "auto_date"),
            ("Time", "auto_time")
        ]
        
        for text, value in sources:
            tk.Radiobutton(
                row2, text=text, value=value,
                variable=source_var,
                font=("Segoe UI", 9),
                bg=self.colors["bg_hover"],
                fg=self.colors["text_primary"],
                activebackground=self.colors["bg_hover"],
                selectcolor=self.colors["bg_card"],
                command=lambda f=col_frame, w=widgets: self._on_source_change(f, w)
            ).pack(side="left", padx=3)
        
        # PLC Config Frame
        plc_frame = tk.Frame(col_frame, bg=self.colors["accent_purple"], padx=10, pady=8)
        widgets["plc_frame"] = plc_frame
        
        plc_config = col_data.get("plc_config") or {}
        
        plc_row = tk.Frame(plc_frame, bg=self.colors["accent_purple"])
        plc_row.pack(fill="x")
        
        tk.Label(
            plc_row, text="📊 Area:",
            font=("Segoe UI", 9),
            bg=self.colors["accent_purple"],
            fg="#1e1e2e"
        ).pack(side="left")
        
        area_var = tk.StringVar(value=plc_config.get("area_type", "DM"))
        area_combo = ttk.Combobox(
            plc_row, textvariable=area_var,
            values=list(PLC_MEMORY_AREAS.keys()),
            width=5, state="readonly"
        )
        area_combo.pack(side="left", padx=3)
        widgets["area_type"] = area_var
        
        tk.Label(plc_row, text="Start:", font=("Segoe UI", 9),
                bg=self.colors["accent_purple"], fg="#1e1e2e").pack(side="left", padx=(10, 3))
        
        start_entry = tk.Entry(plc_row, font=("Segoe UI", 9),
                              bg=self.colors["bg_card"], fg=self.colors["text_primary"],
                              insertbackground=self.colors["text_primary"],
                              relief="flat", width=6)
        start_entry.insert(0, str(plc_config.get("start_address", 0)))
        start_entry.pack(side="left", ipady=2)
        widgets["start_address"] = start_entry
        
        tk.Label(plc_row, text="Format:", font=("Segoe UI", 9),
                bg=self.colors["accent_purple"], fg="#1e1e2e").pack(side="left", padx=(10, 3))
        
        format_var = tk.StringVar(value=plc_config.get("data_format", "ascii"))
        format_combo = ttk.Combobox(
            plc_row, textvariable=format_var,
            values=["ascii", "word"],
            width=6, state="readonly"
        )
        format_combo.pack(side="left", ipady=0)
        widgets["data_format"] = format_var
        
        tk.Label(plc_row, text="Words:", font=("Segoe UI", 9),
                bg=self.colors["accent_purple"], fg="#1e1e2e").pack(side="left", padx=(10, 3))
        
        len_entry = tk.Entry(plc_row, font=("Segoe UI", 9),
                            bg=self.colors["bg_card"], fg=self.colors["text_primary"],
                            insertbackground=self.colors["text_primary"],
                            relief="flat", width=5)
        len_entry.insert(0, str(plc_config.get("length", 10)))
        len_entry.pack(side="left", ipady=2)
        widgets["length"] = len_entry
        
        # Image Config Frame
        image_frame = tk.Frame(col_frame, bg=self.colors["accent_orange"], padx=10, pady=8)
        widgets["image_frame"] = image_frame
        
        image_config = col_data.get("image_config") or {}
        
        img_row1 = tk.Frame(image_frame, bg=self.colors["accent_orange"])
        img_row1.pack(fill="x", pady=2)
        
        tk.Label(
            img_row1, text="📷 Folder:",
            font=("Segoe UI", 9),
            bg=self.colors["accent_orange"],
            fg="#1e1e2e"
        ).pack(side="left")
        
        folder_entry = tk.Entry(
            img_row1,
            font=("Segoe UI", 9),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            relief="flat", width=35
        )
        folder_entry.insert(0, image_config.get("folder_path", ""))
        folder_entry.pack(side="left", padx=5, ipady=2)
        widgets["folder_path"] = folder_entry
        
        tk.Button(
            img_row1, text="📁",
            font=("Segoe UI", 8),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            relief="flat", cursor="hand2",
            command=lambda e=folder_entry: self._browse_folder(e)
        ).pack(side="left", padx=3)
        
        img_row2 = tk.Frame(image_frame, bg=self.colors["accent_orange"])
        img_row2.pack(fill="x", pady=2)
        
        tk.Label(
            img_row2, text="Trigger Index:",
            font=("Segoe UI", 9),
            bg=self.colors["accent_orange"],
            fg="#1e1e2e"
        ).pack(side="left")
        
        trigger_options = ["0 (Main Trigger)"]
        image_triggers = self.controller.data_manager.trigger_config.get("image_triggers", [])
        for i, t in enumerate(image_triggers):
            trigger_options.append(f"{i + 1}: {t.get('name', f'Trigger {i + 1}')}")
        
        trigger_var = tk.StringVar(value=trigger_options[image_config.get("trigger_index", 0)] if trigger_options else "0")
        trigger_combo = ttk.Combobox(
            img_row2,
            textvariable=trigger_var,
            values=trigger_options,
            width=25,
            state="readonly"
        )
        trigger_combo.pack(side="left", padx=5)
        widgets["trigger_index"] = trigger_var
        
        # Show/hide config frames
        if source_var.get() == "plc":
            plc_frame.pack(fill="x", pady=5)
        elif source_var.get() == "image":
            image_frame.pack(fill="x", pady=5)
        
        self.column_widgets.append(widgets)
    
    # ================================================================
    # REORDER FUNCTIONS
    # ================================================================
    
    def _move_column_up(self, index):
        """Move column up"""
        if index > 0:
            self._swap_columns(index, index - 1)
    
    def _move_column_down(self, index):
        """Move column down"""
        columns = self.controller.table_data.get("columns", [])
        if index < len(columns) - 1:
            self._swap_columns(index, index + 1)
    
    def _move_column_to_top(self, index):
        """Move column to the very top"""
        if index > 0:
            self._move_column(index, 0)
    
    def _move_column_to_bottom(self, index):
        """Move column to the very bottom"""
        columns = self.controller.table_data.get("columns", [])
        if index < len(columns) - 1:
            self._move_column(index, len(columns) - 1)
    
    def _move_column_to_position(self, current_index):
        """Move column to a specific position"""
        columns = self.controller.table_data.get("columns", [])
        total = len(columns)
        
        # Create custom dialog
        dialog = MoveToPositionDialog(
            self, 
            current_index + 1, 
            total,
            self.colors
        )
        self.wait_window(dialog)
        
        if dialog.result is not None:
            new_position = dialog.result - 1  # Convert to 0-based index
            if 0 <= new_position < total and new_position != current_index:
                self._move_column(current_index, new_position)
    
    def _swap_columns(self, idx1, idx2):
        """Swap positions of two columns"""
        columns = self.controller.table_data.get("columns", [])
        rows = self.controller.table_data.get("rows", [])
        
        # Swap columns
        columns[idx1], columns[idx2] = columns[idx2], columns[idx1]
        
        # Swap data in rows
        for row in rows:
            if idx1 < len(row) and idx2 < len(row):
                row[idx1], row[idx2] = row[idx2], row[idx1]
        
        # Reload UI
        self._load_columns()
        self._load_preview()
    
    def _move_column(self, from_idx, to_idx):
        """Move column from position A to position B"""
        columns = self.controller.table_data.get("columns", [])
        rows = self.controller.table_data.get("rows", [])
        
        # Move column
        col = columns.pop(from_idx)
        columns.insert(to_idx, col)
        
        # Move data in rows
        for row in rows:
            if from_idx < len(row):
                val = row.pop(from_idx)
                row.insert(to_idx, val)
        
        # Reload UI
        self._load_columns()
        self._load_preview()
    
    def _reverse_columns(self):
        """Reverse all column order"""
        if messagebox.askyesno("Confirm", "Reverse all column order?"):
            columns = self.controller.table_data.get("columns", [])
            rows = self.controller.table_data.get("rows", [])
            
            # Reverse columns
            columns.reverse()
            
            # Reverse data in rows
            for row in rows:
                row.reverse()
            
            # Reload UI
            self._load_columns()
            self._load_preview()
    
    def _reset_to_default(self):
        """Reset to default structure"""
        if messagebox.askyesno("Confirm", "Reset all columns to default?\nAll row data will be deleted!"):
            self.controller.table_data = {
                "columns": [
                    {"name": "No", "width": 60, "data_source": "auto_number", "plc_config": None, "image_config": None},
                    {"name": "Date", "width": 120, "data_source": "auto_date", "plc_config": None, "image_config": None},
                    {"name": "Time", "width": 100, "data_source": "auto_time", "plc_config": None, "image_config": None},
                ],
                "rows": []
            }
            self._load_columns()
            self._load_preview()
    
    # ================================================================
    # OTHER FUNCTIONS
    # ================================================================
    
    def _browse_folder(self, entry_widget):
        """Browse folder"""
        folder = filedialog.askdirectory(title="Select Image Folder")
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)
    
    def _on_source_change(self, col_frame, widgets):
        """Handle source change"""
        source = widgets["data_source"].get()
        plc_frame = widgets["plc_frame"]
        image_frame = widgets["image_frame"]
        
        plc_frame.pack_forget()
        image_frame.pack_forget()
        
        if source == "plc":
            plc_frame.pack(fill="x", pady=5)
        elif source == "image":
            image_frame.pack(fill="x", pady=5)
    
    def _add_column(self, source_type):
        """Add column"""
        names = {
            "manual": "New Column",
            "plc": "PLC Data",
            "image": "Image",
            "auto_number": "No",
            "auto_date": "Date",
            "auto_time": "Time"
        }
        
        new_col = {
            "name": names.get(source_type, "Column"),
            "width": 150 if source_type not in ["auto_number", "auto_time"] else 80,
            "data_source": source_type,
            "plc_config": {"area_type": "DM", "start_address": 0, 
                          "data_index": len(self.column_widgets), "length": 150} if source_type == "plc" else None,
            "image_config": {"folder_path": "", "trigger_index": 0} if source_type == "image" else None
        }
        
        self.controller.table_data["columns"].append(new_col)
        self._create_column_widget(len(self.column_widgets), new_col)
        self._load_preview()
    
    def _delete_column(self, index):
        """Delete column"""
        if len(self.column_widgets) > 1:
            col_name = ""
            columns = self.controller.table_data.get("columns", [])
            if index < len(columns):
                col = columns[index]
                col_name = col.get("name", "") if isinstance(col, dict) else col
            
            if messagebox.askyesno("Confirm", f"Delete column '{col_name}' (position {index + 1})?"):
                if index < len(self.controller.table_data["columns"]):
                    self.controller.table_data["columns"].pop(index)
                for row in self.controller.table_data.get("rows", []):
                    if index < len(row):
                        row.pop(index)
                self._load_columns()
                self._load_preview()
        else:
            messagebox.showwarning("Warning", "At least 1 column must exist!")
    
    def _load_preview(self):
        """Load preview"""
        for w in self.preview_frame.winfo_children():
            w.destroy()
        
        columns = self.controller.table_data.get("columns", [])
        
        # Create scrollable preview
        preview_canvas = tk.Canvas(
            self.preview_frame, 
            bg=self.colors["bg_card"], 
            highlightthickness=0,
            height=60
        )
        preview_scroll = ttk.Scrollbar(
            self.preview_frame, 
            orient="horizontal", 
            command=preview_canvas.xview
        )
        preview_inner = tk.Frame(preview_canvas, bg=self.colors["bg_card"])
        
        preview_canvas.configure(xscrollcommand=preview_scroll.set)
        preview_scroll.pack(side="bottom", fill="x")
        preview_canvas.pack(side="top", fill="x")
        preview_canvas.create_window((0, 0), window=preview_inner, anchor="nw")
        
        preview_inner.bind("<Configure>", 
                          lambda e: preview_canvas.configure(scrollregion=preview_canvas.bbox("all")))
        
        for idx, col in enumerate(columns):
            if isinstance(col, dict):
                name = col.get("name", "Column")
                width = col.get("width", 150)
                source = col.get("data_source", "manual")
            else:
                name = col
                width = 150
                source = "manual"
            
            colors_map = {
                "manual": self.colors["accent"],
                "plc": self.colors["accent_purple"],
                "image": self.colors["accent_orange"],
                "auto_number": self.colors["accent_teal"],
                "auto_date": self.colors["accent_yellow"],
                "auto_time": self.colors["accent_pink"]
            }
            icons = {
                "manual": "📝", "plc": "📊", "image": "📷", 
                "auto_number": "🔢", "auto_date": "📅", "auto_time": "🕐"
            }
            
            bg = colors_map.get(source, self.colors["accent"])
            icon = icons.get(source, "")
            
            col_label = tk.Frame(preview_inner, bg=bg, padx=5, pady=5)
            col_label.grid(row=0, column=idx, padx=1, pady=1)
            
            tk.Label(
                col_label,
                text=f"#{idx + 1}",
                font=("Segoe UI", 8),
                bg=bg, fg="#1e1e2e"
            ).pack()
            
            tk.Label(
                col_label,
                text=f"{icon} {name}",
                font=("Segoe UI", 9, "bold"),
                bg=bg, fg="#1e1e2e",
                width=max(width // 10, 8)
            ).pack()
    
    def _save_settings(self):
        """Save settings"""
        new_columns = []
        
        for widgets in self.column_widgets:
            try:
                name = widgets["name"].get().strip() or "Column"
                width = max(50, min(500, int(widgets["width"].get())))
                source = widgets["data_source"].get()
                
                col = {
                    "name": name,
                    "width": width,
                    "data_source": source,
                    "plc_config": None,
                    "image_config": None
                }
                
                if source == "plc":
                    col["plc_config"] = {
                        "area_type": widgets["area_type"].get(),
                        "start_address": int(widgets["start_address"].get()),
                        "data_index": 0,
                        "data_format": widgets.get("data_format").get() if "data_format" in widgets else "ascii",
                        "length": int(widgets["length"].get()),
                        "ascii_length": int(widgets["length"].get())
                    }
                elif source == "image":
                    trigger_str = widgets["trigger_index"].get()
                    trigger_idx = 0
                    if trigger_str.startswith("0"):
                        trigger_idx = 0
                    else:
                        try:
                            trigger_idx = int(trigger_str.split(":")[0])
                        except:
                            trigger_idx = 0
                    
                    col["image_config"] = {
                        "folder_path": widgets["folder_path"].get().strip(),
                        "trigger_index": trigger_idx
                    }
                
                new_columns.append(col)
            except Exception as e:
                print(f"Error: {e}")
        
        # Adjust rows
        new_col_count = len(new_columns)
        for row in self.controller.table_data.get("rows", []):
            while len(row) < new_col_count:
                row.append("")
            while len(row) > new_col_count:
                row.pop()
        
        self.controller.table_data["columns"] = new_columns
        self.controller.save_table_data()
        
        messagebox.showinfo("Success", "✅ Settings saved successfully!")
        self._load_columns()
        self._load_preview()
    
    def refresh_all(self):
        self._load_columns()
        self._load_preview()
    
    def on_show(self):
        self.refresh_all()


# ================================================================
# MOVE TO POSITION DIALOG
# ================================================================

class MoveToPositionDialog(tk.Toplevel):
    """Dialog to move to a specific position"""
    
    def __init__(self, parent, current_pos, total, colors):
        super().__init__(parent)
        
        self.colors = colors
        self.result = None
        self.current_pos = current_pos
        self.total = total
        
        self.title("📍 Move to Position")
        self.geometry("350x200")
        self.configure(bg=colors["bg_card"])
        self.resizable(False, False)
        
        self._create_widgets()
        
        self.transient(parent)
        self.grab_set()
        
        # Center
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.winfo_screenheight() // 2) - (200 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Focus on entry
        self.pos_entry.focus_set()
        self.pos_entry.select_range(0, tk.END)
    
    def _create_widgets(self):
        # Title
        tk.Label(
            self,
            text="📍 Move Column to Position",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"]
        ).pack(pady=15)
        
        # Info
        tk.Label(
            self,
            text=f"Current position: #{self.current_pos}\nTotal columns: {self.total}",
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"]
        ).pack()
        
        # Input frame
        input_frame = tk.Frame(self, bg=self.colors["bg_card"])
        input_frame.pack(pady=15)
        
        tk.Label(
            input_frame,
            text="Move to position:",
            font=("Segoe UI", 11),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"]
        ).pack(side="left", padx=5)
        
        self.pos_var = tk.StringVar(value=str(self.current_pos))
        self.pos_entry = tk.Entry(
            input_frame,
            textvariable=self.pos_var,
            font=("Segoe UI", 12),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            width=5,
            justify="center"
        )
        self.pos_entry.pack(side="left", padx=5, ipady=5)
        self.pos_entry.bind("<Return>", lambda e: self._confirm())
        
        tk.Label(
            input_frame,
            text=f"(1 - {self.total})",
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"]
        ).pack(side="left", padx=5)
        
        # Buttons
        btn_frame = tk.Frame(self, bg=self.colors["bg_card"])
        btn_frame.pack(pady=15)
        
        tk.Button(
            btn_frame,
            text="✅ Move",
            font=("Segoe UI", 11),
            bg=self.colors["accent_green"],
            fg="#1e1e2e",
            relief="flat",
            cursor="hand2",
            padx=20, pady=8,
            command=self._confirm
        ).pack(side="left", padx=10)
        
        tk.Button(
            btn_frame,
            text="❌ Cancel",
            font=("Segoe UI", 11),
            bg=self.colors["accent_red"],
            fg="#1e1e2e",
            relief="flat",
            cursor="hand2",
            padx=20, pady=8,
            command=self.destroy
        ).pack(side="left", padx=10)
    
    def _confirm(self):
        try:
            pos = int(self.pos_var.get())
            if 1 <= pos <= self.total:
                self.result = pos
                self.destroy()
            else:
                messagebox.showwarning(
                    "Invalid", 
                    f"Position must be between 1 - {self.total}"
                )
        except ValueError:
            messagebox.showwarning("Invalid", "Masukkan angka yang valid")
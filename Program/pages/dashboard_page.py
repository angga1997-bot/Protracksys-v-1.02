"""
pages/dashboard_page.py - Dashboard with Clean Layout (Large Photo)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, date, time as dt_time
from PIL import Image, ImageTk
import os
import csv

from pages.base_page import BasePage
from components.dialogs import NotificationToast
from utils.plc_fins import PLCFinsClient
from config import COLORS, DEFAULT_SHIFT_SCHEDULE


class DashboardPage(BasePage):
    
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.plc_data = {}
        self.is_reading = False
        self.photo_refs = {}
        
        # Section visibility
        self.id_section_visible = True
        self.summary_section_visible = True
        
        # Pagination
        self.current_page = 0
        self.rows_per_page = 10
        
        # Shift tracking
        self.last_shift = None
        
        # _plc_client is shared from AppController's global trigger
        # (AppController sets this before calling _read_plc_and_save_row)
        self._plc_client = None
        self._trigger_monitor = None   # kept for compatibility, not used
        
        # Track last captured image per folder (path -> filename)
        # so we can detect when a NEW image has arrived
        self._last_captured_file = {}
        
        self._create_widgets()
        self._update_clock()
    
    def _create_widgets(self):
        """Membuat widget"""
        self._create_header_with_date()
        self._create_main_content()
        self._create_control_section()
        self._create_table_section()
    
    # ================================================================
    # HEADER
    # ================================================================
    
    def _create_header_with_date(self):
        """Header dengan tampilan tanggal dan shift"""
        header_frame = tk.Frame(self, bg=self.colors["bg_card"])
        header_frame.pack(fill="x", padx=10, pady=10)
        
        left_frame = tk.Frame(header_frame, bg=self.colors["bg_card"])
        left_frame.pack(side="left", padx=20, pady=10)

        # Load custom icon
        icon_path = os.path.join("icons", "dashboard.png")
        img = Image.open(icon_path)
        img = img.resize((100, 80), Image.LANCZOS)
        self.dashboard_icon = ImageTk.PhotoImage(img)
            
        # Label dengan custom icon
        title_label = tk.Label(
                left_frame, 
                text=" Dashboard",
                image=self.dashboard_icon,
                compound="left",
                font=("Segoe UI", 18, "bold"),
                bg=self.colors["bg_card"],
                fg=self.colors["text_primary"]
            )
        title_label.image = self.dashboard_icon
        title_label.pack(anchor="w")
            
                
        # Subtitle (di luar try-except)
        tk.Label(
            left_frame, 
            text="Production Tracking Data System",
            font=("Segoe UI", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"]
        ).pack(anchor="w")
        
        right_frame = tk.Frame(header_frame, bg=self.colors["bg_card"])
        right_frame.pack(side="right", padx=20, pady=10)
        
        # Date box
        date_box = tk.Frame(right_frame, bg=self.colors["accent"], padx=12, pady=8)
        date_box.pack(side="left", padx=3)
        self.date_label = tk.Label(date_box, text="", font=("Segoe UI", 11, "bold"),
                                   bg=self.colors["accent"], fg="#1e1e2e")
        self.date_label.pack()
        
        # Time box
        time_box = tk.Frame(right_frame, bg=self.colors["accent_purple"], padx=12, pady=8)
        time_box.pack(side="left", padx=3)
        self.time_label = tk.Label(time_box, text="", font=("Segoe UI", 11, "bold"),
                                   bg=self.colors["accent_purple"], fg="#1e1e2e")
        self.time_label.pack()
        
        # Shift box
        shift_box = tk.Frame(right_frame, bg=self.colors["accent_green"], padx=12, pady=8)
        shift_box.pack(side="left", padx=3)
        self.shift_label = tk.Label(shift_box, text="", font=("Segoe UI", 11, "bold"),
                                    bg=self.colors["accent_green"], fg="#1e1e2e")
        self.shift_label.pack()
        
        # Today count box
        count_box = tk.Frame(right_frame, bg=self.colors["accent_orange"], padx=12, pady=8)
        count_box.pack(side="left", padx=3)
        self.today_count_label = tk.Label(count_box, text="", font=("Segoe UI", 11, "bold"),
                                          bg=self.colors["accent_orange"], fg="#1e1e2e")
        self.today_count_label.pack()
    
    def _update_clock(self):
        """Update clock setiap detik"""
        now = datetime.now()
        
        days_indo = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        months_indo = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        day_name = days_indo[now.weekday()]
        date_str = f"{day_name}, {now.day} {months_indo[now.month]} {now.year}"
        time_str = now.strftime("%H:%M:%S")
        
        self.date_label.configure(text=f"📅 {date_str}")
        self.time_label.configure(text=f"🕐 {time_str}")
        
        current_shift = self._get_current_shift()
        self.shift_label.configure(text=f"🏭 {current_shift}")
        
        if self.last_shift is not None and self.last_shift != current_shift:
            self._on_shift_change(current_shift)
        self.last_shift = current_shift
        
        today_count = self._get_today_shift_count(self._get_shift_number())
        self.today_count_label.configure(text=f"📊 Today: {today_count}")
        
        self.after(1000, self._update_clock)
    
    def _on_shift_change(self, new_shift):
        """Handle shift change: save current data to database and clear table"""
        rows = self.controller.table_data.get("rows", [])
        if rows:
            columns = self.controller.table_data.get("columns", [])
            col_names = [col.get("name", "Column") if isinstance(col, dict) else col for col in columns]
            
            # Use last shift name for the data we're clearing
            last_shift_name = self.last_shift if self.last_shift else "Shift 2" # fallback
            shift_date = self.controller.shift_manager.get_shift_date()
            
            for row in rows:
                data_dict = {}
                product_no = 0
                images_list = []
                
                for idx, val in enumerate(row):
                    if idx < len(col_names):
                        name = col_names[idx]
                        data_dict[name] = val
                        
                        # Try to extract product_no
                        if any(k in name.lower() for k in ["no", "number"]):
                            try:
                                if "-" in str(val):
                                    product_no = int(str(val).split("-")[-1])
                                else:
                                    product_no = int(val)
                            except: pass
                        
                        # Track images
                        if "image" in name.lower() and val:
                            if isinstance(val, list):
                                images_list.extend(val)
                            else:
                                images_list.append(val)
                
                self.controller.db.insert_production(
                    last_shift_name,
                    shift_date.isoformat(),
                    product_no,
                    data_dict,
                    images_list
                )

        # Clear JSON data for the new shift
        self.controller.table_data["rows"] = []
        self.controller.save_table_data()
        
        self.current_page = 0
        self._refresh_table()
        NotificationToast.show(self, f"🔄 Shift changed to {new_shift}")
    
    def _get_current_shift(self):
        now = datetime.now()
        current_time = now.time()
        if dt_time(7, 30) <= current_time < dt_time(19, 30):
            return "Shift 1"
        return "Shift 2"
    
    def _get_shift_number(self):
        return 1 if "1" in self._get_current_shift() else 2
    
    def _get_today_shift_count(self, shift_number):
        rows = self.controller.table_data.get("rows", [])
        columns = self.controller.table_data.get("columns", [])
        column_names = [col.get("name", "") if isinstance(col, dict) else col for col in columns]
        
        date_col_idx = None
        no_col_idx = None
        
        for idx, name in enumerate(column_names):
            name_lower = name.lower()
            if any(keyword in name_lower for keyword in ["tanggal", "date", "tgl"]):
                date_col_idx = idx
            if any(keyword in name_lower for keyword in ["no", "number", "nomor", "id_status"]):
                no_col_idx = idx
        
        if date_col_idx is None:
            return 0
        
        today = date.today().isoformat()
        count = 0
        
        for row in rows:
            if date_col_idx < len(row) and str(row[date_col_idx])[:10] == today:
                if no_col_idx is not None and no_col_idx < len(row):
                    if str(row[no_col_idx]).startswith(f"{shift_number}-"):
                        count += 1
                else:
                    count += 1
        
        return count
    
    def _generate_auto_number(self):
        shift_number = self._get_shift_number()
        shift_count = self._get_today_shift_count(shift_number)
        return f"{shift_number}-{shift_count + 1:02d}"
    
    # ================================================================
    # MAIN CONTENT - 40% ID Display : 60% Summary
    # ================================================================
    
    def _create_main_content(self):
        """Membuat konten utama dengan proporsi 40:60"""
        self.main_frame = tk.Frame(self, bg=self.colors["bg_dark"])
        self.main_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.sections_container = tk.Frame(self.main_frame, bg=self.colors["bg_dark"])
        self.sections_container.pack(fill="both", expand=True)
        
        self.sections_container.grid_columnconfigure(0, weight=40, uniform="section")
        self.sections_container.grid_columnconfigure(1, weight=60, uniform="section")
        self.sections_container.grid_rowconfigure(0, weight=1)
        
        self._create_id_section()
        self._create_summary_section()
    
    # ================================================================
    # ID DISPLAY SECTION - FOTO BESAR & TEKS PENUH
    # ================================================================
    
    def _create_id_section(self):
        """ID Display section - 40% width dengan 2 kartu"""
        self.id_frame = tk.Frame(self.sections_container, bg=self.colors["bg_card"])
        self.id_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Header
        header = tk.Frame(self.id_frame, bg=self.colors["bg_card"])
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        self.id_toggle_btn = tk.Button(
            header, text="▼", font=("Segoe UI", 8),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            relief="flat", cursor="hand2", width=3,
            command=self._toggle_id_section
        )
        self.id_toggle_btn.pack(side="left")
        
        tk.Label(
            header, text="👥 ID Display",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"]
        ).pack(side="left", padx=5)
        
        tk.Button(
            header, text="⚙️", font=("Segoe UI", 8),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            relief="flat", cursor="hand2", width=3,
            command=self._show_id_settings
        ).pack(side="right")
        
        # Content
        self.id_content = tk.Frame(self.id_frame, bg=self.colors["bg_card"])
        self.id_content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # 2 Cards with grid
        cards_container = tk.Frame(self.id_content, bg=self.colors["bg_card"])
        cards_container.pack(fill="both", expand=True)
        
        cards_container.grid_columnconfigure(0, weight=1, uniform="card")
        cards_container.grid_columnconfigure(1, weight=1, uniform="card")
        cards_container.grid_rowconfigure(0, weight=1)
        
        self.id_card_1 = self._create_id_card_large(cards_container, "OPR 1", 1)
        self.id_card_1.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        
        self.id_card_2 = self._create_id_card_large(cards_container, "OPR 2", 2)
        self.id_card_2.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
    
    def _toggle_id_section(self):
        """Toggle ID section visibility"""
        self.id_section_visible = not self.id_section_visible
        
        if self.id_section_visible:
            self.id_content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self.id_toggle_btn.configure(text="▼")
        else:
            self.id_content.pack_forget()
            self.id_toggle_btn.configure(text="▶")
    
    def _create_id_card_large(self, parent, title, card_num):
        """Membuat kartu ID dengan foto besar dan teks penuh ke kanan"""
        card = tk.Frame(parent, bg=self.colors["bg_hover"])
        
        # Header dengan title
        header = tk.Frame(card, bg=self.colors["bg_hover"])
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        tk.Label(
            header, text=title,
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["bg_hover"],
            fg=self.colors["accent"]
        ).pack(side="left")
        
        # Main content area - horizontal layout
        content = tk.Frame(card, bg=self.colors["bg_hover"])
        content.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        # Configure grid for photo and info side by side
        content.grid_columnconfigure(0, weight=0)  # Photo - fixed
        content.grid_columnconfigure(1, weight=1)  # Info - expand to fill
        content.grid_rowconfigure(0, weight=1)
        
        # Photo Frame - BIGGER SIZE (75x75)
        photo_frame = tk.Frame(content, bg=self.colors["bg_active"], width=75, height=75)
        photo_frame.grid(row=0, column=0, sticky="nw", padx=(0, 10))
        photo_frame.grid_propagate(False)
        
        tk.Label(
            photo_frame, text="👤",
            font=("Segoe UI", 28),
            bg=self.colors["bg_active"],
            fg=self.colors["text_secondary"]
        ).pack(expand=True)
        
        # Info Frame - EXPAND TO RIGHT EDGE
        info_frame = tk.Frame(content, bg=self.colors["bg_hover"])
        info_frame.grid(row=0, column=1, sticky="nsew")
        
        # ID Label - Full width
        id_label = tk.Label(
            info_frame, text="ID: -",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_primary"],
            anchor="w"
        )
        id_label.pack(fill="x", anchor="w")
        
        # Name Label - Full width
        name_label = tk.Label(
            info_frame, text="-",
            font=("Segoe UI", 10),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"],
            anchor="w"
        )
        name_label.pack(fill="x", anchor="w", pady=(2, 0))
        
        # Status Label - Full width
        status_label = tk.Label(
            info_frame, text="⚪ Waiting",
            font=("Segoe UI", 9),
            bg=self.colors["bg_hover"],
            fg=self.colors["text_secondary"],
            anchor="w"
        )
        status_label.pack(fill="x", anchor="w", pady=(2, 0))
        
        # Source combo - full width at bottom
        combo_frame = tk.Frame(card, bg=self.colors["bg_hover"])
        combo_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        column_names = self.controller.data_manager.get_column_names()
        source_var = tk.StringVar()
        
        source_combo = ttk.Combobox(
            combo_frame,
            textvariable=source_var,
            values=["-- select column --"] + column_names,
            state="readonly"
        )
        source_combo.pack(fill="x")
        source_combo.set("-- select column --")
        
        config = self.controller.data_manager.dashboard_config.get(f"id_display_{card_num}", {})
        saved_source = config.get("source_column")
        if saved_source and saved_source in column_names:
            source_combo.set(saved_source)
        
        source_combo.bind("<<ComboboxSelected>>", 
                         lambda e, cn=card_num, sv=source_var: self._on_source_change(cn, sv.get()))
        
        # Store references
        card.photo_frame = photo_frame
        card.id_label = id_label
        card.name_label = name_label
        card.status_label = status_label
        card.source_var = source_var
        card.source_combo = source_combo
        card.card_num = card_num
        
        return card
    
    def _on_source_change(self, card_num, column_name):
        config_key = f"id_display_{card_num}"
        
        if config_key not in self.controller.data_manager.dashboard_config:
            self.controller.data_manager.dashboard_config[config_key] = {}
        
        self.controller.data_manager.dashboard_config[config_key]["source_column"] = \
            None if column_name == "-- select column --" else column_name
        
        self.controller.data_manager.save_dashboard_config()
        self._update_id_displays()
    
    def _update_id_displays(self):
        rows = self.controller.table_data.get("rows", [])
        columns = self.controller.table_data.get("columns", [])
        column_names = [col["name"] if isinstance(col, dict) else col for col in columns]
        
        self.id_card_1.source_combo["values"] = ["-- select column --"] + column_names
        self.id_card_2.source_combo["values"] = ["-- select column --"] + column_names
        
        for card_num, card in [(1, self.id_card_1), (2, self.id_card_2)]:
            config = self.controller.data_manager.dashboard_config.get(f"id_display_{card_num}", {})
            source_column = config.get("source_column")
            
            if not source_column or source_column not in column_names:
                self._reset_id_card(card)
                continue
            
            col_idx = column_names.index(source_column)
            
            if rows:
                last_row = rows[-1]
                if col_idx < len(last_row):
                    self._display_member_info(card, str(last_row[col_idx]))
                else:
                    self._reset_id_card(card)
            else:
                self._reset_id_card(card)
    
    def _display_member_info(self, card, id_value):
        for widget in card.photo_frame.winfo_children():
            widget.destroy()
        
        if not id_value or id_value in ["", "N/A"]:
            self._reset_id_card(card)
            return
        
        member = self.controller.data_manager.get_member_by_id(id_value)
        
        if member:
            card.id_label.configure(text=f"ID: {member['id_number']}")
            card.name_label.configure(text=member['name'])
            card.status_label.configure(text="🟢 Regist", fg=self.colors["accent_green"])
            
            if member.get("photo"):
                photo_path = self.controller.data_manager.get_photo_path(member["photo"])
                if photo_path and os.path.exists(photo_path):
                    try:
                        img = Image.open(photo_path)
                        img.thumbnail((130, 130))
                        photo = ImageTk.PhotoImage(img)
                        self.photo_refs[f"card_{card.card_num}"] = photo
                        tk.Label(card.photo_frame, image=photo, bg=self.colors["bg_active"]).pack(expand=True)
                        return
                    except:
                        pass
            
            tk.Label(card.photo_frame, text="👤", font=("Segoe UI", 28),
                     bg=self.colors["bg_active"], fg=self.colors["accent_green"]).pack(expand=True)
        else:
            card.id_label.configure(text=f"ID: {id_value}")
            card.name_label.configure(text="(not found)")
            card.status_label.configure(text="🔴 not registered", fg=self.colors["accent_red"])
            tk.Label(card.photo_frame, text="❓", font=("Segoe UI", 28),
                     bg=self.colors["bg_active"], fg=self.colors["accent_red"]).pack(expand=True)
    
    def _reset_id_card(self, card):
        for widget in card.photo_frame.winfo_children():
            widget.destroy()
        
        tk.Label(card.photo_frame, text="👤", font=("Segoe UI", 28),
                 bg=self.colors["bg_active"], fg=self.colors["text_secondary"]).pack(expand=True)
        
        card.id_label.configure(text="ID: -")
        card.name_label.configure(text="-")
        card.status_label.configure(text="⚪ Waiting", fg=self.colors["text_secondary"])
    
    def _show_id_settings(self):
        dialog = IDDisplaySettingsDialog(self, self.controller)
        self.wait_window(dialog)
        self._update_id_displays()
    
    # ================================================================
    # SUMMARY SECTION (60% WIDTH)
    # ================================================================
    
    def _create_summary_section(self):
        """Summary section - 60% width"""
        self.summary_frame = tk.Frame(self.sections_container, bg=self.colors["bg_card"])
        self.summary_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Header
        header = tk.Frame(self.summary_frame, bg=self.colors["bg_card"])
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        self.summary_toggle_btn = tk.Button(
            header, text="▼", font=("Segoe UI", 8),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            relief="flat", cursor="hand2", width=3,
            command=self._toggle_summary_section
        )
        self.summary_toggle_btn.pack(side="left")
        
        tk.Label(
            header, text="📈 Summary Breakdown",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"]
        ).pack(side="left", padx=5)
        
        self.summary_info_label = tk.Label(
            header, text="", font=("Segoe UI", 9),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"]
        )
        self.summary_info_label.pack(side="left", padx=15)
        
        tk.Button(
            header, text="⚙️ Settings", font=("Segoe UI", 8),
            bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
            relief="flat", cursor="hand2", padx=8,
            command=self._show_summary_settings
        ).pack(side="right")
        
        # Content
        self.summary_content = tk.Frame(self.summary_frame, bg=self.colors["bg_card"])
        self.summary_content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self._update_summary_breakdown()
    
    def _toggle_summary_section(self):
        self.summary_section_visible = not self.summary_section_visible
        
        if self.summary_section_visible:
            self.summary_content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self.summary_toggle_btn.configure(text="▼")
        else:
            self.summary_content.pack_forget()
            self.summary_toggle_btn.configure(text="▶")
    
    def _update_summary_breakdown(self):
        """Update summary breakdown - FULL WIDTH TABLE"""
        for widget in self.summary_content.winfo_children():
            widget.destroy()
        
        config = self.controller.data_manager.dashboard_config.get("summary_breakdown", {})
        group_by_col = config.get("group_by_column")
        sum_col = config.get("sum_column", "COUNT")
        shift_filter = config.get("shift_filter", "All")
        
        if not group_by_col:
            info_frame = tk.Frame(self.summary_content, bg=self.colors["bg_hover"], padx=20, pady=20)
            info_frame.pack(fill="both", expand=True)
            
            tk.Label(info_frame, text="💡 Click ⚙️ to setup summary",
                     font=("Segoe UI", 10), bg=self.colors["bg_hover"],
                     fg=self.colors["text_secondary"]).pack(expand=True)
            tk.Label(info_frame, text="Select Group By and Sum columns",
                     font=("Segoe UI", 9), bg=self.colors["bg_hover"],
                     fg=self.colors["text_secondary"]).pack()
            return
        
        rows = self.controller.table_data.get("rows", [])
        columns = self.controller.table_data.get("columns", [])
        column_names = [col.get("name", "") if isinstance(col, dict) else col for col in columns]
        
        group_col_idx = column_names.index(group_by_col) if group_by_col in column_names else None
        sum_col_idx = column_names.index(sum_col) if sum_col in column_names and sum_col != "COUNT" else None
        is_count_mode = sum_col == "COUNT"
        
        if group_col_idx is None:
            return
        
        # Find no column for shift filtering
        no_col_idx = None
        for idx, name in enumerate(column_names):
            if any(keyword in name.lower() for keyword in ["no", "number", "nomor"]):
                no_col_idx = idx
                break
        
        # Group data
        grouped_data = {}
        
        for row in rows:
            if shift_filter != "All" and no_col_idx is not None and no_col_idx < len(row):
                no_value = str(row[no_col_idx])
                if shift_filter == "Shift 1" and not no_value.startswith("1-"):
                    continue
                elif shift_filter == "Shift 2" and not no_value.startswith("2-"):
                    continue
            
            if group_col_idx < len(row):
                group_key = str(row[group_col_idx]) if row[group_col_idx] else "(Empty)"
                
                if group_key not in grouped_data:
                    grouped_data[group_key] = {"count": 0, "sum": 0}
                
                grouped_data[group_key]["count"] += 1
                
                if sum_col_idx is not None and sum_col_idx < len(row):
                    try:
                        grouped_data[group_key]["sum"] += float(str(row[sum_col_idx]).replace(",", ""))
                    except:
                        pass
        
        self.summary_info_label.configure(text=f"📊 {group_by_col} | 🔢 {sum_col} | 🏭 {shift_filter}")
        
        if not grouped_data:
            tk.Label(self.summary_content, text="📭 No data available",
                     font=("Segoe UI", 10), bg=self.colors["bg_card"],
                     fg=self.colors["text_secondary"]).pack(expand=True, pady=20)
            return
        
        # Create scrollable table
        table_frame = tk.Frame(self.summary_content, bg=self.colors["bg_card"])
        table_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(table_frame, bg=self.colors["bg_card"], highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        
        inner = tk.Frame(canvas, bg=self.colors["bg_card"])
        
        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", on_canvas_configure)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.configure(yscrollcommand=scrollbar_y.set)
        
        scrollbar_y.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Configure grid columns
        num_columns = 3 if not is_count_mode else 2
        inner.grid_columnconfigure(0, weight=3, uniform="sumcol")
        inner.grid_columnconfigure(1, weight=1, uniform="sumcol")
        if not is_count_mode:
            inner.grid_columnconfigure(2, weight=1, uniform="sumcol")
        
        # Header
        tk.Label(inner, text=f"📋 {group_by_col}", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["accent"], fg="#1e1e2e", padx=15, pady=10, anchor="w"
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        
        tk.Label(inner, text="📊 Qty Data", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["accent"], fg="#1e1e2e", padx=15, pady=10
        ).grid(row=0, column=1, sticky="nsew", padx=1)
        
        if not is_count_mode:
            tk.Label(inner, text=f"🔢 {sum_col}", font=("Segoe UI", 10, "bold"),
                     bg=self.colors["accent"], fg="#1e1e2e", padx=15, pady=10
            ).grid(row=0, column=2, sticky="nsew", padx=(1, 0))
        
        # Data rows
        total_count = 0
        total_sum = 0
        
        sorted_items = sorted(
            grouped_data.items(),
            key=lambda x: x[1]["sum"] if not is_count_mode else x[1]["count"],
            reverse=True
        )
        
        for idx, (group_key, values) in enumerate(sorted_items):
            bg_color = self.colors["bg_hover"] if idx % 2 == 0 else self.colors["bg_active"]
            row_num = idx + 1
            
            tk.Label(inner, text=group_key, font=("Segoe UI", 10, "bold"),
                     bg=bg_color, fg=self.colors["text_primary"], padx=15, pady=8, anchor="w"
            ).grid(row=row_num, column=0, sticky="nsew", padx=(0, 1), pady=1)
            
            tk.Label(inner, text=str(values["count"]), font=("Segoe UI", 10),
                     bg=bg_color, fg=self.colors["accent_teal"], padx=15, pady=8
            ).grid(row=row_num, column=1, sticky="nsew", padx=1, pady=1)
            
            total_count += values["count"]
            
            if not is_count_mode:
                tk.Label(inner, text=self._format_number(values["sum"]),
                         font=("Segoe UI", 10, "bold"), bg=bg_color,
                         fg=self.colors["accent_green"], padx=15, pady=8
                ).grid(row=row_num, column=2, sticky="nsew", padx=(1, 0), pady=1)
                total_sum += values["sum"]
        
        # Total row
        total_row = len(sorted_items) + 1
        
        tk.Label(inner, text="TOTAL", font=("Segoe UI", 11, "bold"),
                 bg=self.colors["accent_purple"], fg="#1e1e2e", padx=15, pady=10, anchor="w"
        ).grid(row=total_row, column=0, sticky="nsew", padx=(0, 1), pady=(3, 0))
        
        tk.Label(inner, text=str(total_count), font=("Segoe UI", 11, "bold"),
                 bg=self.colors["accent_purple"], fg="#1e1e2e", padx=15, pady=10
        ).grid(row=total_row, column=1, sticky="nsew", padx=1, pady=(3, 0))
        
        if not is_count_mode:
            tk.Label(inner, text=self._format_number(total_sum), font=("Segoe UI", 11, "bold"),
                     bg=self.colors["accent_purple"], fg="#1e1e2e", padx=15, pady=10
            ).grid(row=total_row, column=2, sticky="nsew", padx=(1, 0), pady=(3, 0))
        
        # MouseWheel handled globally in main.py
    
    def _format_number(self, value):
        if isinstance(value, float) and value == int(value):
            return f"{int(value):,}".replace(",", ".")
        elif isinstance(value, float):
            return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{value:,}".replace(",", ".")
    
    def _show_summary_settings(self):
        dialog = SummarySettingsDialog(self, self.controller)
        self.wait_window(dialog)
        self._update_summary_breakdown()
    
    # ================================================================
    # CONTROL SECTION
    # ================================================================
    
    def _create_control_section(self):
        control_frame = tk.Frame(self, bg=self.colors["bg_card"])
        control_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        inner = tk.Frame(control_frame, bg=self.colors["bg_card"])
        inner.pack(fill="x", padx=15, pady=10)
        
        self.stats_label = tk.Label(inner, text="0 rows | 0 Columns",
                                    font=("Segoe UI", 10), bg=self.colors["bg_card"],
                                    fg=self.colors["text_primary"])
        self.stats_label.pack(side="left")
        
        btn_frame = tk.Frame(inner, bg=self.colors["bg_card"])
        btn_frame.pack(side="right")
        
        buttons = [
            ("📡 PLC Read", self.colors["accent_purple"], self._read_plc_data),
            ("➕ Add Manual", self.colors["accent_green"], self._add_row),
            ("🔄 Refresh", self.colors["accent"], self._refresh_table),
            ("🗑️ Clear All", self.colors["accent_red"], self._clear_all),
            #("📁 Save", self.colors["accent_orange"], self._export_csv),
        ]
        
        for text, color, cmd in buttons:
            btn = tk.Button(btn_frame, text=text, font=("Segoe UI", 9),
                           bg=color, fg="#1e1e2e", relief="flat", cursor="hand2",
                           padx=8, pady=3, command=cmd)
            btn.pack(side="left", padx=2)
            
            if "PLC" in text:
                self.read_plc_btn = btn
        
        self.plc_status = tk.Label(inner, text="PLC: ⚪", font=("Segoe UI", 9),
                                   bg=self.colors["bg_card"], fg=self.colors["text_secondary"])
        self.plc_status.pack(side="right", padx=10)
    
    # ================================================================
    # TABLE SECTION WITH PAGINATION
    # ================================================================
    
    def _create_table_section(self):
        table_container = tk.Frame(self, bg=self.colors["bg_card"])
        table_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.table_frame = tk.Frame(table_container, bg=self.colors["bg_card"])
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_table()
    
    def _create_table(self):
        """Create table with pagination"""
        for w in self.table_frame.winfo_children():
            w.destroy()
        
        columns = self.controller.table_data.get("columns", [])
        all_rows = self.controller.table_data.get("rows", [])
        
        all_rows_reversed = list(reversed(all_rows))
        
        total_rows = len(all_rows_reversed)
        total_pages = max(1, (total_rows + self.rows_per_page - 1) // self.rows_per_page)
        
        if self.current_page >= total_pages:
            self.current_page = max(0, total_pages - 1)
        
        start_idx = self.current_page * self.rows_per_page
        end_idx = min(start_idx + self.rows_per_page, total_rows)
        page_rows = all_rows_reversed[start_idx:end_idx]
        
        self._update_stats(total_rows, len(columns))
        
        canvas = tk.Canvas(self.table_frame, bg=self.colors["bg_card"], highlightthickness=0)
        h_scroll = ttk.Scrollbar(self.table_frame, orient="horizontal", command=canvas.xview)
        v_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.colors["bg_card"])
        
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        if total_rows > self.rows_per_page:
            self._create_pagination_controls(total_pages)
        
        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Header
        tk.Label(inner, text="#", font=("Segoe UI", 9, "bold"),
                 bg=self.colors["accent_red"], fg="#1e1e2e", width=4, height=2
        ).grid(row=0, column=0, padx=1, pady=1, sticky="nsew")
        
        for idx, col in enumerate(columns):
            name = col.get("name", "Column") if isinstance(col, dict) else col
            width = col.get("width", 120) if isinstance(col, dict) else 120
            source = col.get("data_source", "manual") if isinstance(col, dict) else "manual"
            
            colors_map = {
                "manual": self.colors["accent"],
                "plc": self.colors["accent_purple"],
                "image": self.colors["accent_orange"],
                "auto_number": self.colors["accent_teal"],
                "auto_date": self.colors["accent_yellow"],
                "auto_time": self.colors["accent_pink"]
            }
            icons = {"plc": "📊", "image": "📷", "auto_number": "🔢", "auto_date": "📅", "auto_time": "🕐"}
            
            header_text = f"{icons.get(source, '')} {name}".strip()
            
            tk.Label(inner, text=header_text, font=("Segoe UI", 9, "bold"),
                     bg=colors_map.get(source, self.colors["accent"]), fg="#1e1e2e",
                     width=max(width // 9, 8), height=2
            ).grid(row=0, column=idx + 1, padx=1, pady=1, sticky="nsew")
        
        # Rows
        for row_idx, row_data in enumerate(page_rows):
            actual_idx = len(all_rows) - 1 - (start_idx + row_idx)
            bg = self.colors["bg_hover"] if row_idx % 2 == 0 else self.colors["bg_active"]
            
            tk.Button(inner, text="🗑️", font=("Segoe UI", 8),
                     bg=self.colors["accent_red"], fg="#1e1e2e", relief="flat",
                     cursor="hand2", width=3,
                     command=lambda i=actual_idx: self._delete_row(i)
            ).grid(row=row_idx + 1, column=0, padx=1, pady=1, sticky="nsew")
            
            for col_idx, col in enumerate(columns):
                width = col.get("width", 120) if isinstance(col, dict) else 120
                source = col.get("data_source", "manual") if isinstance(col, dict) else "manual"
                value = row_data[col_idx] if col_idx < len(row_data) else ""
                
                if source == "image" and value:
                    # Images are stored in CAPTURED_DIR after copy; fall back to source folder
                    from config import CAPTURED_DIR
                    img_path = os.path.join(CAPTURED_DIR, str(value))
                    if not os.path.isfile(img_path):
                        # fallback: look in the configured folder
                        folder = col.get("image_config", {}).get("folder_path", "").strip()
                        if not folder:
                            t_idx = col.get("image_config", {}).get("trigger_index", 0)
                            trigs = self.controller.data_manager.trigger_config.get("image_triggers", [])
                            if 0 <= t_idx - 1 < len(trigs):
                                folder = trigs[t_idx - 1].get("folder_path", "")
                            elif trigs:
                                folder = trigs[0].get("folder_path", "")
                        if folder:
                            img_path = os.path.join(folder, str(value))
                    if img_path and os.path.isfile(img_path):
                        try:
                            img = Image.open(img_path)
                            img.thumbnail((60, 60))
                            photo = ImageTk.PhotoImage(img)
                            self.photo_refs[f"r{row_idx}_c{col_idx}"] = photo
                            final_path = img_path
                            btn = tk.Button(inner, image=photo, bg=bg, activebackground=self.colors["bg_hover"],
                                            relief="flat", cursor="hand2",
                                            command=lambda p=final_path: self._show_image_zoom(p))
                            btn.grid(row=row_idx + 1, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                            continue
                        except Exception as e:
                            print(f"[ImageRender] {e}")
                
                tk.Label(inner, text=str(value), font=("Segoe UI", 9),
                        bg=bg, fg=self.colors["text_primary"],
                        width=max(width // 9, 8), height=2
                ).grid(row=row_idx + 1, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
        
        if not page_rows:
            tk.Label(inner, text="📭 No data available", font=("Segoe UI", 11),
                     bg=self.colors["bg_card"], fg=self.colors["text_secondary"], pady=30
            ).grid(row=1, column=0, columnspan=len(columns) + 1, sticky="nsew")
        # MouseWheel handled globally in main.py
    
    def _create_pagination_controls(self, total_pages):
        pag_frame = tk.Frame(self.table_frame, bg=self.colors["bg_card"])
        pag_frame.pack(fill="x", pady=(0, 5))
        
        inner = tk.Frame(pag_frame, bg=self.colors["bg_card"])
        inner.pack()
        
        tk.Button(inner, text="⏮", font=("Segoe UI", 9),
                 bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
                 relief="flat", cursor="hand2", width=3,
                 state="normal" if self.current_page > 0 else "disabled",
                 command=lambda: self._go_to_page(0)).pack(side="left", padx=2)
        
        tk.Button(inner, text="◀", font=("Segoe UI", 9),
                 bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
                 relief="flat", cursor="hand2", width=3,
                 state="normal" if self.current_page > 0 else "disabled",
                 command=lambda: self._go_to_page(self.current_page - 1)).pack(side="left", padx=2)
        
        tk.Label(inner, text=f"Page {self.current_page + 1} / {total_pages}",
                font=("Segoe UI", 10), bg=self.colors["bg_card"],
                fg=self.colors["text_primary"], padx=15).pack(side="left")
        
        tk.Button(inner, text="▶", font=("Segoe UI", 9),
                 bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
                 relief="flat", cursor="hand2", width=3,
                 state="normal" if self.current_page < total_pages - 1 else "disabled",
                 command=lambda: self._go_to_page(self.current_page + 1)).pack(side="left", padx=2)
        
        tk.Button(inner, text="⏭", font=("Segoe UI", 9),
                 bg=self.colors["bg_hover"], fg=self.colors["text_primary"],
                 relief="flat", cursor="hand2", width=3,
                 state="normal" if self.current_page < total_pages - 1 else "disabled",
                 command=lambda: self._go_to_page(total_pages - 1)).pack(side="left", padx=2)
        
        tk.Label(inner, text="  Per page:", font=("Segoe UI", 9),
                bg=self.colors["bg_card"], fg=self.colors["text_secondary"]).pack(side="left", padx=(15, 5))
        
        rpp_var = tk.StringVar(value=str(self.rows_per_page))
        rpp_combo = ttk.Combobox(inner, textvariable=rpp_var,
                                 values=["10", "25", "50", "100"], width=5, state="readonly")
        rpp_combo.pack(side="left")
        rpp_combo.bind("<<ComboboxSelected>>", lambda e: self._change_rows_per_page(int(rpp_var.get())))
    
    def _go_to_page(self, page):
        self.current_page = page
        self._create_table()
    
    def _change_rows_per_page(self, rows):
        self.rows_per_page = rows
        self.current_page = 0
        self._create_table()
    
    def _update_stats(self, rows, cols):
        self.stats_label.configure(text=f"{rows} rows | {cols} columns")
    
    # ================================================================
    # ROW OPERATIONS
    # ================================================================
    
    def _add_row(self):
        columns = self.controller.table_data.get("columns", [])
        
        new_row = []
        manual_columns = []
        manual_indices = []
        
        for idx, col in enumerate(columns):
            if isinstance(col, dict):
                source = col.get("data_source", "manual")
                col_name = col.get("name", "Column")
                
                if source == "auto_number":
                    new_row.append(self._generate_auto_number())
                elif source == "auto_date":
                    new_row.append(datetime.now().strftime("%Y-%m-%d"))
                elif source == "auto_time":
                    new_row.append(datetime.now().strftime("%H:%M:%S"))
                elif source in ["plc", "image"]:
                    new_row.append("")
                else:
                    new_row.append("")
                    manual_columns.append(col_name)
                    manual_indices.append(idx)
            else:
                new_row.append("")
                manual_columns.append(col)
                manual_indices.append(idx)
        
        if manual_columns:
            dialog = AddRowDialog(self, manual_columns, self.colors)
            self.wait_window(dialog)
            
            if dialog.result:
                for i, value in enumerate(dialog.result):
                    if i < len(manual_indices):
                        new_row[manual_indices[i]] = value
            else:
                return
        
        self.controller.table_data["rows"].append(new_row)
        self.controller.save_table_data()
        self.current_page = 0
        self._refresh_table()
        self._update_id_displays()
        self._update_summary_breakdown()
        NotificationToast.show(self, "✅ Added Data")
    
    def _delete_row(self, index):
        rows = self.controller.table_data.get("rows", [])
        if 0 <= index < len(rows):
            if messagebox.askyesno("Confirm", f"Delete Data?"):
                rows.pop(index)
                self.controller.save_table_data()
                self._refresh_table()
                self._update_id_displays()
                self._update_summary_breakdown()
    
    def _clear_all(self):
        rows = self.controller.table_data.get("rows", [])
        if rows and messagebox.askyesno("Confirm", f"Delete Data {len(rows)} data?"):
            self.controller.table_data["rows"] = []
            self.controller.save_table_data()
            self.current_page = 0
            self._refresh_table()
            self._update_id_displays()
            self._update_summary_breakdown()
    
    def _export_csv(self):
        from tkinter import filedialog
        
        columns = self.controller.table_data.get("columns", [])
        rows = self.controller.table_data.get("rows", [])
        
        if not rows:
            messagebox.showwarning("Warning", "Haven't Data")
            return
        
        col_names = [col.get("name", "Column") if isinstance(col, dict) else col for col in columns]
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
            initialfilename=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(col_names)
                writer.writerows(rows)
            messagebox.showinfo("Success", f"✅ Exported:\n{filename}")
    
    def _refresh_table(self):
        self._create_table()
        self._update_summary_breakdown()
    
    def _show_image_zoom(self, img_path):
        """Show zoomed image in a centered popup window."""
        if not img_path or not os.path.isfile(img_path):
            return
        
        zoom_win = tk.Toplevel(self)
        zoom_win.title(f"🔍 {os.path.basename(img_path)}")
        zoom_win.configure(bg="#0f0f0f")
        zoom_win.attributes("-topmost", True)
        
        # Determine max size
        sw = zoom_win.winfo_screenwidth()
        sh = zoom_win.winfo_screenheight()
        max_w = int(sw * 0.85)
        max_h = int(sh * 0.85)
        
        try:
            img = Image.open(img_path)
            img_w, img_h = img.size
            # Scale to fit screen
            scale = min(max_w / img_w, max_h / img_h, 1.0)
            new_w = max(1, int(img_w * scale))
            new_h = max(1, int(img_h * scale))
            img = img.resize((new_w, new_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            win_w = new_w + 20
            win_h = new_h + 60
            x = (sw - win_w) // 2
            y = (sh - win_h) // 2
            zoom_win.geometry(f"{win_w}x{win_h}+{x}+{y}")
            
            tk.Label(zoom_win, image=photo, bg="#0f0f0f").pack(pady=(10, 5))
            zoom_win._photo = photo  # keep reference
            
            tk.Label(zoom_win, text=os.path.basename(img_path),
                     font=("Segoe UI", 9), bg="#0f0f0f", fg="#aaaaaa").pack()
            
            tk.Button(zoom_win, text="✖ Close", font=("Segoe UI", 10),
                      bg=self.colors["accent_red"], fg="#1e1e2e",
                      relief="flat", cursor="hand2", padx=15,
                      command=zoom_win.destroy).pack(pady=5)
            
            # Close on click or Escape
            zoom_win.bind("<Button-1>", lambda e: zoom_win.destroy())
            zoom_win.bind("<Escape>", lambda e: zoom_win.destroy())
            
        except Exception as e:
            zoom_win.destroy()
            print(f"[Zoom] Error: {e}")

    # ================================================================
    # PLC TRIGGER MONITOR
    # ================================================================

    @staticmethod
    def _words_to_ascii(words):
        """Convert list of PLC uint16 words to ASCII string (stops at 0x00)."""
        result = ""
        for w in words:
            hi = (w >> 8) & 0xFF
            lo = w & 0xFF
            if hi == 0:
                break
            result += chr(hi) if 0x20 <= hi <= 0x7E else "?"
            if lo == 0:
                break
            result += chr(lo) if 0x20 <= lo <= 0x7E else "?"
        return result.strip()

    def _extract_plc_value(self, cfg, plc_data):
        """Extract one column value from plc_data dict. Supports 'word' and 'ascii' formats."""
        key   = f"{cfg['area_type']}_{cfg['start_address']}_{cfg['length']}"
        words = plc_data.get(key, [])
        if not words:
            return "N/A"
        idx = cfg.get("data_index", 0)
        if cfg.get("data_format", "word") == "ascii":
            n = cfg.get("ascii_length", 1)
            slc = words[idx: idx + n] if idx < len(words) else []
            return self._words_to_ascii(slc) if slc else "N/A"
        else:
            return str(words[idx]) if 0 <= idx < len(words) else "N/A"

    def _capture_image_for_column(self, col, trigger_time=None):
        """Capture the latest image for an 'image' column using last-used tracker.
        Grabs the newest file in the folder; if it's new (different from last used),
        copies it to CAPTURED_DIR. Always returns a result even if same file."""
        from utils.image_capture import ImageCapture
        
        img_cfg = col.get("image_config") or {}
        folder  = img_cfg.get("folder_path", "").strip()
        t_idx   = img_cfg.get("trigger_index", 0)
        
        if not folder:
            trigs = self.controller.data_manager.trigger_config.get("image_triggers", [])
            if 0 <= t_idx - 1 < len(trigs):
                folder = trigs[t_idx - 1].get("folder_path", "")
            elif trigs:
                folder = trigs[0].get("folder_path", "")
        
        if not folder or not os.path.isdir(folder):
            print(f"[ImageCapture] Folder not found: {folder!r}")
            return ""
        
        cap = ImageCapture()
        ok, result = cap.capture_and_copy(folder, prefix="IMG")
        if ok:
            fname = os.path.basename(result)
            self._last_captured_file[folder] = fname
            print(f"[ImageCapture] Saved: {result}")
            return fname
        print(f"[ImageCapture] No image in folder: {result}")
        return ""

    def _on_plc_trigger(self, event):
        """Legacy stub — global trigger now handled by AppController."""
        pass

    def _handle_trigger_event(self, event):
        """Legacy stub — global trigger now handled by AppController."""
        pass


    def _read_plc_and_save_row(self, capture_images=True):
        """Read PLC via a FRESH dedicated connection then insert a new row."""
        columns = self.controller.table_data.get("columns", [])
        # Collect unique read areas
        areas = {}
        for col in columns:
            if isinstance(col, dict) and col.get("data_source") == "plc" and col.get("plc_config"):
                cfg = col["plc_config"]
                key = f"{cfg['area_type']}_{cfg['start_address']}_{cfg['length']}"
                if key not in areas:
                    areas[key] = cfg
        plc_data = {}
        if areas:
            dc = getattr(self, "_plc_client", None)
            must_disconnect = False
            ok = False
            msg = ""
            
            if not dc or not dc.connected:
                dc = PLCFinsClient(self.controller.plc_config)
                ok, msg = dc.connect()
                must_disconnect = True
            else:
                ok = True
                
            if ok:
                for key, cfg in areas.items():
                    rd_ok, data = dc.read_memory(cfg["area_type"], cfg["start_address"], cfg["length"])
                    plc_data[key] = data if rd_ok else []
                    if not rd_ok:
                        print(f"[Trigger] read_memory failed {key}: {data}")
                if must_disconnect:
                    dc.disconnect()
            else:
                print(f"[Trigger] Data connection failed: {msg}")
        # Build row
        new_row = []
        for col in columns:
            if not isinstance(col, dict):
                new_row.append("")
                continue
            source = col.get("data_source", "manual")
            if source == "auto_number":
                new_row.append(self._generate_auto_number())
            elif source == "auto_date":
                new_row.append(datetime.now().strftime("%Y-%m-%d"))
            elif source == "auto_time":
                new_row.append(datetime.now().strftime("%H:%M:%S"))
            elif source == "plc" and col.get("plc_config"):
                new_row.append(self._extract_plc_value(col["plc_config"], plc_data))
            elif source == "image":
                new_row.append(self._capture_image_for_column(col) if capture_images else "")
            else:
                new_row.append("")
        self.controller.table_data["rows"].append(new_row)
        self.controller.save_table_data()
        self.current_page = 0
        self._refresh_table()
        self._update_id_displays()
        self._update_summary_breakdown()
        NotificationToast.show(self, "⚡ PLC Trigger: Data Saved")
        print(f"[Trigger] Row inserted at {datetime.now().strftime('%H:%M:%S')}")

    def _update_last_row_image(self, img_trigger_cfg, trigger_index=None, trigger_time=None):
        """Image trigger fired: capture latest image and update the matching column.
        
        Uses last-used-file tracking so we detect NEW images without relying
        on timestamps (camera may save image BEFORE PLC bit goes ON).

        Args:
            img_trigger_cfg: The image trigger settings dict (folder_path, etc.)
            trigger_index:   0-based index of the image trigger (0=first, 1=second...)
            trigger_time:    unused, kept for API compatibility
        """
        rows    = self.controller.table_data.get("rows", [])
        columns = self.controller.table_data.get("columns", [])
        if not rows:
            print("[ImageTrigger] No rows in table — skipping")
            return
        
        folder = img_trigger_cfg.get("folder_path", "").strip()
        if not folder or not os.path.isdir(folder):
            print(f"[ImageTrigger] Folder not found: {folder!r}")
            return
        
        from utils.image_capture import ImageCapture
        cap = ImageCapture()
        
        # Get the newest image in the source folder (no timestamp filter)
        ok, src_path = cap.get_latest_image(folder)
        if not ok:
            print(f"[ImageTrigger] No image found: {src_path}")
            return
        
        src_name = os.path.basename(src_path)
        last_used = self._last_captured_file.get(folder, "")
        
        if src_name == last_used:
            print(f"[ImageTrigger] Same image as before ({src_name}) — still capturing")
        else:
            print(f"[ImageTrigger] New image detected: {src_name}")
        
        # Always copy it (even if same file — trigger means 'take a photo NOW')
        import shutil
        from datetime import datetime as _dt
        from config import CAPTURED_DIR
        ext = os.path.splitext(src_name)[1]
        new_name = f"TRIG_{_dt.now().strftime('%Y%m%d_%H%M%S_%f')}{ext}"
        dest_path = os.path.join(CAPTURED_DIR, new_name)
        try:
            shutil.copy2(src_path, dest_path)
        except Exception as ex:
            print(f"[ImageTrigger] Copy failed: {ex}")
            return
        
        self._last_captured_file[folder] = src_name
        filename = new_name
        
        # Match this trigger to the correct image column by trigger_index
        last_row = rows[-1]
        matched_idx = None
        for col_idx, col in enumerate(columns):
            if isinstance(col, dict) and col.get("data_source") == "image":
                col_t_idx = col.get("image_config", {}).get("trigger_index", 1) - 1  # 1-based → 0-based
                if trigger_index is not None:
                    if col_t_idx == trigger_index:
                        matched_idx = col_idx
                        break
                else:
                    matched_idx = col_idx  # fallback: first image column
                    break
        
        if matched_idx is None:
            print(f"[ImageTrigger] No image column matched for trigger_index={trigger_index}")
            return
        
        while len(last_row) <= matched_idx:
            last_row.append("")
        last_row[matched_idx] = filename
        
        self.controller.save_table_data()
        self._refresh_table()
        NotificationToast.show(self, f"📷 Image: {filename}")
        print(f"[ImageTrigger] idx={trigger_index} → col={matched_idx}: {filename}")

    # ================================================================
    # PLC FUNCTIONS (manual 'PLC Read' button)
    # ================================================================
    
    def _read_plc_data(self):
        if self.is_reading:
            return
        
        self.is_reading = True
        self.read_plc_btn.configure(state="disabled", text="...")
        self.plc_status.configure(text="PLC: 🟡", fg=self.colors["accent_yellow"])
        
        def do_read():
            areas = {}
            for col in self.controller.table_data.get("columns", []):
                if isinstance(col, dict) and col.get("data_source") == "plc" and col.get("plc_config"):
                    cfg = col["plc_config"]
                    key = f"{cfg['area_type']}_{cfg['start_address']}_{cfg['length']}"
                    if key not in areas:
                        areas[key] = cfg
            
            client = getattr(self, "_plc_client", None)
            must_disconnect = False
            ok = False
            msg = ""
            
            if not client or not client.connected:
                # Need to spin up a manual connection
                client = PLCFinsClient(self.controller.plc_config)
                ok, msg = client.connect()
                must_disconnect = True
            else:
                ok = True
                
            if not ok:
                self.after(0, lambda: self._on_plc_complete(False, msg, {}))
                return
            
            plc_data = {}
            for key, cfg in areas.items():
                rd_ok, data = client.read_memory(cfg["area_type"], cfg["start_address"], cfg["length"])
                plc_data[key] = data if rd_ok else []
            
            if must_disconnect:
                client.disconnect()
                
            self.after(0, lambda: self._on_plc_complete(True, "OK", plc_data))
        
        threading.Thread(target=do_read, daemon=True).start()
    
    def _on_plc_complete(self, success, msg, plc_data):
        self.is_reading = False
        self.read_plc_btn.configure(state="normal", text="📡 PLC Read")
        
        if success:
            self.plc_data = plc_data
            self.plc_status.configure(text="PLC: 🟢", fg=self.colors["accent_green"])
            self._add_row_from_plc()
            NotificationToast.show(self, "✅ PLC OK")
        else:
            self.plc_status.configure(text="PLC: 🔴", fg=self.colors["accent_red"])
            messagebox.showerror("Error", msg)
    
    def _add_row_from_plc(self):
        """Build a row from already-read self.plc_data and insert it."""
        columns = self.controller.table_data.get("columns", [])
        new_row  = []

        for col in columns:
            if not isinstance(col, dict):
                new_row.append("")
                continue

            source = col.get("data_source", "manual")

            if source == "auto_number":
                new_row.append(self._generate_auto_number())
            elif source == "auto_date":
                new_row.append(datetime.now().strftime("%Y-%m-%d"))
            elif source == "auto_time":
                new_row.append(datetime.now().strftime("%H:%M:%S"))
            elif source == "plc" and col.get("plc_config"):
                new_row.append(self._extract_plc_value(col["plc_config"], self.plc_data))
            elif source == "image":
                new_row.append(self._capture_image_for_column(col))
            else:
                new_row.append("")

        self.controller.table_data["rows"].append(new_row)
        self.controller.save_table_data()
        self.current_page = 0
        self._refresh_table()
        self._update_id_displays()
        self._update_summary_breakdown()
    
    def on_show(self):
        self._refresh_table()
        self._update_id_displays()
        self._update_summary_breakdown()


# ================================================================
# DIALOGS
# ================================================================

class AddRowDialog(tk.Toplevel):
    def __init__(self, parent, columns, colors):
        super().__init__(parent)
        self.colors = colors
        self.result = None
        self.entries = []
        
        self.title("➕ Add Data")
        self.geometry("380x400")
        self.configure(bg=colors["bg_card"])
        
        tk.Label(self, text="➕ Add Data", font=("Segoe UI", 13, "bold"),
                 bg=colors["bg_card"], fg=colors["text_primary"]).pack(pady=12)
        
        canvas = tk.Canvas(self, bg=colors["bg_card"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg=colors["bg_card"])
        
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=15, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        for col in columns:
            frame = tk.Frame(content, bg=colors["bg_card"])
            frame.pack(fill="x", pady=4)
            
            tk.Label(frame, text=col, font=("Segoe UI", 10, "bold"),
                     bg=colors["bg_card"], fg=colors["text_primary"],
                     width=20, anchor="w").pack(side="left")
            
            entry = tk.Entry(frame, font=("Segoe UI", 10),
                            bg=colors["bg_hover"], fg=colors["text_primary"],
                            insertbackground=colors["text_primary"], width=22)
            entry.pack(side="left", fill="x", expand=True, ipady=4)
            entry.bind("<Return>", lambda e: self._next_or_save())
            self.entries.append(entry)
        
        btn_frame = tk.Frame(self, bg=colors["bg_card"])
        btn_frame.pack(pady=12)
        
        tk.Button(btn_frame, text="💾 Save", font=("Segoe UI", 10),
                  bg=colors["accent_green"], fg="#1e1e2e", relief="flat",
                  padx=18, pady=5, command=self._save).pack(pady=5)
        
        tk.Button(btn_frame, text="❌ Cancel", font=("Segoe UI", 10),
                  bg=colors["accent_red"], fg="#1e1e2e", relief="flat",
                  padx=18, pady=5, command=self.destroy).pack(pady=5)
        
        self.transient(parent)
        self.grab_set()
        self._center_dialog()
        
        if self.entries:
            self.entries[0].focus_set()
    
    def _center_dialog(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 190
        y = (self.winfo_screenheight() // 2) - 200
        self.geometry(f"+{x}+{y}")
    
    def _next_or_save(self):
        current = self.focus_get()
        if current in self.entries:
            idx = self.entries.index(current)
            if idx < len(self.entries) - 1:
                self.entries[idx + 1].focus_set()
            else:
                self._save()
    
    def _save(self):
        self.result = [e.get() for e in self.entries]
        self.destroy()


class SummarySettingsDialog(tk.Toplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.colors = parent.colors
        
        self.title("⚙️ Setting Summary")
        self.geometry("420x380")
        self.configure(bg=self.colors["bg_card"])
        
        tk.Label(self, text="⚙️ Setting Summary", font=("Segoe UI", 13, "bold"),
                 bg=self.colors["bg_card"], fg=self.colors["text_primary"]).pack(pady=12)
        
        column_names = self.controller.data_manager.get_column_names()
        config = self.controller.data_manager.dashboard_config.get("summary_breakdown", {})
        
        # Group by
        frame1 = tk.Frame(self, bg=self.colors["bg_hover"], padx=12, pady=10)
        frame1.pack(fill="x", padx=20, pady=6)
        
        tk.Label(frame1, text="📊 Group By :", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["bg_hover"], fg=self.colors["text_primary"]).pack(anchor="w")
        tk.Label(frame1, text="Example: PN Body, Model, Type", font=("Segoe UI", 9),
                 bg=self.colors["bg_hover"], fg=self.colors["text_secondary"]).pack(anchor="w")
        
        self.group_var = tk.StringVar(value=config.get("group_by_column", ""))
        ttk.Combobox(frame1, textvariable=self.group_var,
                     values=["-- Haven't --"] + column_names, width=28,
                     state="readonly").pack(anchor="w", pady=5)
        if not self.group_var.get():
            self.group_var.set("-- None --")
        
        # Sum column
        frame2 = tk.Frame(self, bg=self.colors["bg_hover"], padx=12, pady=10)
        frame2.pack(fill="x", padx=20, pady=6)
        
        tk.Label(frame2, text="🔢 Sum Column :", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["bg_hover"], fg=self.colors["text_primary"]).pack(anchor="w")
        tk.Label(frame2, text="COUNT = Counting Rows", font=("Segoe UI", 9),
                 bg=self.colors["bg_hover"], fg=self.colors["text_secondary"]).pack(anchor="w")
        
        self.sum_var = tk.StringVar(value=config.get("sum_column", "COUNT"))
        ttk.Combobox(frame2, textvariable=self.sum_var,
                     values=["COUNT"] + column_names, width=28,
                     state="readonly").pack(anchor="w", pady=5)
        
        # Shift filter
        frame3 = tk.Frame(self, bg=self.colors["bg_hover"], padx=12, pady=10)
        frame3.pack(fill="x", padx=20, pady=6)
        
        tk.Label(frame3, text="🏭 Filter Shift:", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["bg_hover"], fg=self.colors["text_primary"]).pack(anchor="w")
        
        self.shift_var = tk.StringVar(value=config.get("shift_filter", "All"))
        ttk.Combobox(frame3, textvariable=self.shift_var,
                     values=["All", "Shift 1", "Shift 2"], width=28,
                     state="readonly").pack(anchor="w", pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self, bg=self.colors["bg_card"])
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="💾 Save", font=("Segoe UI", 10),
                  bg=self.colors["accent_green"], fg="#1e1e2e", relief="flat",
                  padx=18, pady=5, command=self._save).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="❌ Cancel", font=("Segoe UI", 10),
                  bg=self.colors["accent_red"], fg="#1e1e2e", relief="flat",
                  padx=18, pady=5, command=self.destroy).pack(side="left", padx=5)
        
        self.transient(parent)
        self.grab_set()
        self._center_dialog()
    
    def _center_dialog(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 210
        y = (self.winfo_screenheight() // 2) - 190
        self.geometry(f"+{x}+{y}")
    
    def _save(self):
        config = {
            "group_by_column": self.group_var.get() if self.group_var.get() != "-- None --" else None,
            "sum_column": self.sum_var.get(),
            "shift_filter": self.shift_var.get()
        }
        self.controller.data_manager.dashboard_config["summary_breakdown"] = config
        self.controller.data_manager.save_dashboard_config()
        NotificationToast.show(self.master, "✅ Save!")
        self.destroy()


class IDDisplaySettingsDialog(tk.Toplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.colors = parent.colors
        
        self.title("⚙️ ID Display")
        self.geometry("380x280")
        self.configure(bg=self.colors["bg_card"])
        
        tk.Label(self, text="⚙️ ID Display Settings", font=("Segoe UI", 13, "bold"),
                 bg=self.colors["bg_card"], fg=self.colors["text_primary"]).pack(pady=12)
        
        column_names = self.controller.data_manager.get_column_names()
        
        for i, label in enumerate(["Operator 1:", "Operator 2:"], 1):
            frame = tk.Frame(self, bg=self.colors["bg_card"])
            frame.pack(fill="x", padx=25, pady=8)
            
            tk.Label(frame, text=label, font=("Segoe UI", 10),
                     bg=self.colors["bg_card"], fg=self.colors["text_primary"],
                     width=10, anchor="w").pack(side="left")
            
            config = self.controller.data_manager.dashboard_config.get(f"id_display_{i}", {})
            var = tk.StringVar(value=config.get("source_column", ""))
            combo = ttk.Combobox(frame, textvariable=var,
                                values=["-- Tidak Aktif --"] + column_names, width=22, state="readonly")
            combo.pack(side="left")
            if not var.get():
                combo.set("-- Inactive --")
            
            setattr(self, f"combo{i}_var", var)
        
        btn_frame = tk.Frame(self, bg=self.colors["bg_card"])
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="💾 Save", font=("Segoe UI", 10),
                  bg=self.colors["accent_green"], fg="#1e1e2e", relief="flat",
                  padx=18, pady=5, command=self._save).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="❌ Cancel", font=("Segoe UI", 10),
                  bg=self.colors["accent_red"], fg="#1e1e2e", relief="flat",
                  padx=18, pady=5, command=self.destroy).pack(side="left", padx=5)
        
        self.transient(parent)
        self.grab_set()
        self._center_dialog()
    
    def _center_dialog(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 190
        y = (self.winfo_screenheight() // 2) - 140
        self.geometry(f"+{x}+{y}")
    
    def _save(self):
        dm = self.controller.data_manager
        
        for i in [1, 2]:
            key = f"id_display_{i}"
            if key not in dm.dashboard_config:
                dm.dashboard_config[key] = {}
            
            val = getattr(self, f"combo{i}_var").get()
            dm.dashboard_config[key]["source_column"] = None if val == "-- Inactive --" else val
        
        dm.save_dashboard_config()
        self.destroy()
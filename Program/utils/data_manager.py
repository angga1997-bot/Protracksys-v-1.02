"""
utils/data_manager.py - JSON data management
"""

import json
import os
import shutil
from datetime import datetime
from config import (
    AUTO_FILL_KEYWORDS, DEFAULT_PLC_CONFIG, DEFAULT_TRIGGER_CONFIG,
    DATA_DIR, PHOTOS_DIR, DEFAULT_DASHBOARD_CONFIG, CAPTURED_DIR
)


class DataManager:
    """Class to manage application data"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.photos_dir = PHOTOS_DIR
        self.captured_dir = CAPTURED_DIR
        
        self.table_file = os.path.join(self.data_dir, "table_data.json")
        self.plc_file = os.path.join(self.data_dir, "plc_config.json")
        self.mp_file = os.path.join(self.data_dir, "mp_register.json")
        self.dashboard_file = os.path.join(self.data_dir, "dashboard_config.json")
        self.trigger_file = os.path.join(self.data_dir, "trigger_config.json")
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.photos_dir, exist_ok=True)
        os.makedirs(self.captured_dir, exist_ok=True)
        
        self.table_data = self._load_table_data()
        self.plc_config = self._load_plc_config()
        self.mp_register = self._load_mp_register()
        self.dashboard_config = self._load_dashboard_config()
        self.trigger_config = self._load_trigger_config()
        
        self.plc_data_cache = {}
    
    def _load_table_data(self):
        """Load table data from file"""
        default_data = {
            "columns": [
                {"name": "No", "width": 60, "data_source": "auto_number", "plc_config": None, "image_config": None},
                {"name": "Date", "width": 120, "data_source": "auto_date", "plc_config": None, "image_config": None},
                {"name": "Time", "width": 100, "data_source": "auto_time", "plc_config": None, "image_config": None},
                {"name": "Operator_ID", "width": 120, "data_source": "plc", 
                 "plc_config": {"area_type": "DM", "start_address": 0, "data_index": 0, "length": 150},
                 "image_config": None},
                {"name": "Image", "width": 150, "data_source": "image", 
                 "plc_config": None,
                 "image_config": {"folder_path": "", "trigger_index": 0}}
            ],
            "rows": []
        }
        
        if os.path.exists(self.table_file):
            try:
                with open(self.table_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("columns") and isinstance(data["columns"][0], str):
                        data = self._migrate_old_format(data)
                    return data
            except:
                pass
        
        return default_data
    
    def _migrate_old_format(self, old_data):
        """Migrate old data format"""
        new_columns = []
        old_columns = old_data.get("columns", [])
        old_widths = old_data.get("column_widths", [])
        
        for i, col_name in enumerate(old_columns):
            width = old_widths[i] if i < len(old_widths) else 150
            new_columns.append({
                "name": col_name,
                "width": width,
                "data_source": "manual",
                "plc_config": None,
                "image_config": None
            })
        
        return {"columns": new_columns, "rows": old_data.get("rows", [])}
    
    def _load_plc_config(self):
        if os.path.exists(self.plc_file):
            try:
                with open(self.plc_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return DEFAULT_PLC_CONFIG.copy()
    
    def _load_mp_register(self):
        default_data = {"members": []}
        if os.path.exists(self.mp_file):
            try:
                with open(self.mp_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return default_data
    
    def _load_dashboard_config(self):
        if os.path.exists(self.dashboard_file):
            try:
                with open(self.dashboard_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return DEFAULT_DASHBOARD_CONFIG.copy()
    
    def _load_trigger_config(self):
        if os.path.exists(self.trigger_file):
            try:
                with open(self.trigger_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return DEFAULT_TRIGGER_CONFIG.copy()
    
    def save_table_data(self):
        with open(self.table_file, "w", encoding="utf-8") as f:
            json.dump(self.table_data, f, indent=4, ensure_ascii=False)
    
    def save_plc_config(self):
        with open(self.plc_file, "w", encoding="utf-8") as f:
            json.dump(self.plc_config, f, indent=4, ensure_ascii=False)
    
    def save_mp_register(self):
        with open(self.mp_file, "w", encoding="utf-8") as f:
            json.dump(self.mp_register, f, indent=4, ensure_ascii=False)
    
    def save_dashboard_config(self):
        with open(self.dashboard_file, "w", encoding="utf-8") as f:
            json.dump(self.dashboard_config, f, indent=4, ensure_ascii=False)
    
    def save_trigger_config(self):
        with open(self.trigger_file, "w", encoding="utf-8") as f:
            json.dump(self.trigger_config, f, indent=4, ensure_ascii=False)
    
    # ===== MP Register Methods =====
    
    def add_member(self, id_number, name, photo_path=None):
        for member in self.mp_register["members"]:
            if member["id_number"] == id_number:
                return False, "ID already registered!"
        
        saved_photo = None
        if photo_path and os.path.exists(photo_path):
            ext = os.path.splitext(photo_path)[1]
            saved_photo = f"{id_number}{ext}"
            dest_path = os.path.join(self.photos_dir, saved_photo)
            shutil.copy2(photo_path, dest_path)
        
        member = {
            "id_number": str(id_number),
            "name": name,
            "photo": saved_photo,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.mp_register["members"].append(member)
        self.save_mp_register()
        return True, "Member added successfully!"
    
    def update_member(self, id_number, name=None, photo_path=None):
        for member in self.mp_register["members"]:
            if member["id_number"] == str(id_number):
                if name:
                    member["name"] = name
                
                if photo_path and os.path.exists(photo_path):
                    if member.get("photo"):
                        old_photo = os.path.join(self.photos_dir, member["photo"])
                        if os.path.exists(old_photo):
                            os.remove(old_photo)
                    
                    ext = os.path.splitext(photo_path)[1]
                    saved_photo = f"{id_number}{ext}"
                    dest_path = os.path.join(self.photos_dir, saved_photo)
                    shutil.copy2(photo_path, dest_path)
                    member["photo"] = saved_photo
                
                member["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_mp_register()
                return True, "Member updated successfully!"
        
        return False, "Member not found!"
    
    def delete_member(self, id_number):
        for i, member in enumerate(self.mp_register["members"]):
            if member["id_number"] == str(id_number):
                if member.get("photo"):
                    photo_path = os.path.join(self.photos_dir, member["photo"])
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                
                self.mp_register["members"].pop(i)
                self.save_mp_register()
                return True, "Member deleted successfully!"
        
        return False, "Member not found!"
    
    def get_member_by_id(self, id_number):
        for member in self.mp_register["members"]:
            if member["id_number"] == str(id_number):
                return member
        return None
    
    def get_photo_path(self, photo_filename):
        if photo_filename:
            return os.path.join(self.photos_dir, photo_filename)
        return None
    
    def get_column_names(self):
        return [col["name"] if isinstance(col, dict) else col for col in self.table_data["columns"]]
    
    # ============================================================
    # Tambahkan di class DataManager (data_manager.py)
    # ============================================================

    # Tambahkan setelah method get_column_names()

    def get_summary_config(self):
        """Get summary configuration"""
        return self.dashboard_config.get("summary_columns", [])

    def set_summary_config(self, columns):
        """Set summary columns configuration"""
        self.dashboard_config["summary_columns"] = columns
        self.save_dashboard_config()

    def get_shift_column(self):
        """Get shift column for filtering"""
        return self.dashboard_config.get("summary_shift_column")

    def set_shift_column(self, column_name):
        """Set shift column for filtering"""
        self.dashboard_config["summary_shift_column"] = column_name
        self.save_dashboard_config()

    def get_numeric_columns(self):
        """Get columns that likely contain numeric data"""
        numeric_keywords = ["qty", "jumlah", "total", "count", "amount", 
                            "quantity", "unit", "pcs", "actual", "target",
                            "defect", "ng", "ok", "reject"]
        
        columns = self.get_column_names()
        numeric_cols = []
        
        for col in columns:
            col_lower = col.lower()
            for keyword in numeric_keywords:
                if keyword in col_lower:
                    numeric_cols.append(col)
                    break
        
        return numeric_cols

    def calculate_column_sum(self, column_name, shift_filter=None):
        """Calculate sum of a column with optional shift filter"""
        columns = self.get_column_names()
        rows = self.table_data.get("rows", [])
        
        if column_name not in columns:
            return 0
        
        col_idx = columns.index(column_name)
        shift_col_idx = None
        shift_column = self.get_shift_column()
        
        if shift_column and shift_column in columns:
            shift_col_idx = columns.index(shift_column)
        
        total = 0
        for row in rows:
            # Apply shift filter if needed
            if shift_filter and shift_filter != "All" and shift_col_idx is not None:
                if shift_col_idx < len(row) and str(row[shift_col_idx]) != shift_filter:
                    continue
            
            if col_idx < len(row):
                try:
                    value = row[col_idx]
                    if value is not None and value != "":
                        total += float(str(value).replace(",", ""))
                except (ValueError, TypeError):
                    pass
        
        return total

    def get_unique_shifts(self):
        """Get unique shift values from data"""
        shift_column = self.get_shift_column()
        if not shift_column:
            return []
        
        columns = self.get_column_names()
        if shift_column not in columns:
            return []
        
        col_idx = columns.index(shift_column)
        rows = self.table_data.get("rows", [])
        
        shifts = set()
        for row in rows:
            if col_idx < len(row) and row[col_idx]:
                shifts.add(str(row[col_idx]))
        
        return sorted(list(shifts))

    def get_row_count_by_shift(self, shift_value=None):
        """Get row count, optionally filtered by shift"""
        rows = self.table_data.get("rows", [])
        
        if not shift_value or shift_value == "All":
            return len(rows)
        
        shift_column = self.get_shift_column()
        if not shift_column:
            return len(rows)
        
        columns = self.get_column_names()
        if shift_column not in columns:
            return len(rows)
        
        col_idx = columns.index(shift_column)
        
        count = 0
        for row in rows:
            if col_idx < len(row) and str(row[col_idx]) == shift_value:
                count += 1
        
        return count
    
    def detect_column_type(self, column_name):
        name_lower = column_name.lower().strip()
        
        for keyword in AUTO_FILL_KEYWORDS["datetime"]:
            if keyword in name_lower:
                return "datetime"
        
        for keyword in AUTO_FILL_KEYWORDS["date"]:
            if keyword in name_lower:
                return "date"
        
        for keyword in AUTO_FILL_KEYWORDS["time"]:
            if keyword in name_lower:
                return "time"
        
        return "text"
    
    def get_auto_value(self, column_type):
        now = datetime.now()
        
        if column_type == "date":
            return now.strftime("%Y-%m-%d")
        elif column_type == "time":
            return now.strftime("%H:%M:%S")
        elif column_type == "datetime":
            return now.strftime("%Y-%m-%d %H:%M:%S")
        
        return ""
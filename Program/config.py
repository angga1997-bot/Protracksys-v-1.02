"""
config.py - Konfigurasi global aplikasi
"""

import os
from datetime import time

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")
CAPTURED_DIR = os.path.join(DATA_DIR, "captured")
DATABASE_FILE = os.path.join(DATA_DIR, "app_database.db")

# Pastikan folder ada
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(CAPTURED_DIR, exist_ok=True)

# Warna tema aplikasi
COLORS = {
    "bg_dark": "#11111b",
    "bg_sidebar": "#181825",
    "bg_card": "#1e1e2e",
    "bg_hover": "#313244",
    "bg_active": "#45475a",
    "accent": "#89b4fa",
    "accent_green": "#a6e3a1",
    "accent_red": "#f38ba8",
    "accent_yellow": "#f9e2af",
    "accent_orange": "#fab387",
    "accent_purple": "#cba6f7",
    "accent_pink": "#f5c2e7",
    "accent_teal": "#94e2d5",
    "accent_blue": "#74c7ec",
    "text_primary": "#cdd6f4",
    "text_secondary": "#a6adc8",
    "border": "#313244"
}

# Konfigurasi aplikasi
APP_CONFIG = {
    "title": "Production Tracking Data System",
    "version": "1.0.0",
    "window_size": "1500x900",
    "min_size": (1200, 800)
}

# Days of week
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_MAP = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6
}

# Default Shift Schedule
DEFAULT_SHIFT_SCHEDULE = {
    "shift_1": {
        "name": "Shift 1",
        "Monday": {"start": "07:30", "end": "19:30", "enabled": True},
        "Tuesday": {"start": "07:30", "end": "19:30", "enabled": True},
        "Wednesday": {"start": "07:30", "end": "19:30", "enabled": True},
        "Thursday": {"start": "07:30", "end": "19:30", "enabled": True},
        "Friday": {"start": "07:30", "end": "19:30", "enabled": True},
        "Saturday": {"start": "07:30", "end": "19:30", "enabled": False},
        "Sunday": {"start": "07:30", "end": "19:30", "enabled": False}
    },
    "shift_2": {
        "name": "Shift 2",
        "Monday": {"start": "19:30", "end": "07:30", "enabled": True},
        "Tuesday": {"start": "19:30", "end": "07:30", "enabled": True},
        "Wednesday": {"start": "19:30", "end": "07:30", "enabled": True},
        "Thursday": {"start": "19:30", "end": "07:30", "enabled": True},
        "Friday": {"start": "19:30", "end": "07:30", "enabled": True},
        "Saturday": {"start": "19:30", "end": "07:30", "enabled": False},
        "Sunday": {"start": "19:30", "end": "07:30", "enabled": False}
    }
}

# Keyword untuk auto-fill
AUTO_FILL_KEYWORDS = {
    "date": ["date", "tanggal", "tgl"],
    "time": ["time", "waktu", "jam"],
    "datetime": ["datetime", "timestamp", "created", "updated"],
    "product_no": ["product_no", "no_product", "prod_no", "pn", "assy_no"]
}

# PLC Memory Areas
PLC_MEMORY_AREAS = {
    "DM": {"code": 0x82, "name": "Data Memory", "prefix": "D"},
    "CIO": {"code": 0x30, "name": "CIO Area", "prefix": "CIO"},
    "WR": {"code": 0x31, "name": "Work Area", "prefix": "W"},
    "HR": {"code": 0x32, "name": "Holding Area", "prefix": "H"},
    "AR": {"code": 0x33, "name": "Auxiliary Area", "prefix": "A"}
}

# Trigger Types
TRIGGER_TYPES = {
    "rising": "Rising Edge (OFF → ON)",
    "falling": "Falling Edge (ON → OFF)",
    "level_on": "Level ON",
    "level_off": "Level OFF"
}

# Trigger Actions
TRIGGER_ACTIONS = {
    "save_data": "Save Data to Table",
    "capture_image": "Capture Image + Save Data",
    "capture_only": "Capture Image Only"
}

# Default Configs
DEFAULT_PLC_CONFIG = {
    "connection": {
        "plc_ip": "192.168.1.1",
        "plc_port": 9600,
        "timeout": 5
    },
    "read_areas": [
        {"name": "Main Data", "area_type": "DM", "start_address": 0, "length": 150, "enabled": True}
    ]
}

DEFAULT_TRIGGER_CONFIG = {
    "enabled": False,
    "trigger_address": {
        "area_type": "DM",
        "address": 100,
        "bit": 0
    },
    "trigger_type": "rising",
    "action": "save_data",
    "auto_reset": True,
    "reset_delay": 500,
    "image_triggers": []
}

DEFAULT_DASHBOARD_CONFIG = {
    # ID Display settings
    "id_display_1": {
        "enabled": True, 
        "source_column": None, 
        "title": "OPERATOR 1"
    },
    "id_display_2": {
        "enabled": True, 
        "source_column": None, 
        "title": "OPERATOR 2"
    },
    
    # === Summary settings ===
    "summary_columns": [],  # List kolom yang akan di-summary
    "summary_shift_column": None,  # Kolom untuk filter shift
    
    # Summary display settings
    "summary_settings": {
        "show_total_rows": True,
        "show_filtered_info": True,
        "auto_refresh": True,
        "refresh_interval": 5000  # ms
    }
}

# Summary Operations
SUMMARY_OPERATIONS = {
    "SUM": {"name": "Total (SUM)", "icon": "Σ", "description": "Sum of all values"},
    "AVG": {"name": "Average (AVG)", "icon": "x̄", "description": "Calculate average"},
    "COUNT": {"name": "Count (COUNT)", "icon": "#", "description": "Count number of rows"},
    "MIN": {"name": "Minimum (MIN)", "icon": "↓", "description": "Smallest value"},
    "MAX": {"name": "Maximum (MAX)", "icon": "↑", "description": "Largest value"}
}

# Summary Icons
SUMMARY_ICONS = ["📊", "📈", "📉", "💰", "📦", "🔢", "⚡", "🎯", "✅", "❌", "⚠️", "🏭", "👥", "🕐", "📋"]

PHOTO_CONFIG = {
    "max_size": (150, 150),
    "thumbnail_size": (80, 80),
    "allowed_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
}

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif"]

# Photo Config
PHOTO_CONFIG = {
    "max_size": (150, 150),
    "thumbnail_size": (80, 80),
    "allowed_extensions": IMAGE_EXTENSIONS
}
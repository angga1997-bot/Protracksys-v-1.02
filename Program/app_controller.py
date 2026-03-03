"""
app_controller.py - Controller utama aplikasi
"""

import tkinter as tk
from config import COLORS, APP_CONFIG
from components.sidebar import Sidebar
from pages.dashboard_page import DashboardPage
from pages.table_settings_page import TableSettingsPage
from pages.plc_settings_page import PLCSettingsPage
from pages.trigger_settings_page import TriggerSettingsPage
from pages.register_mp_page import RegisterMPPage
from pages.history_page import HistoryPage
from pages.shift_schedule_page import ShiftSchedulePage
from pages.help_page import HelpPage
from utils.data_manager import DataManager
from utils.database import Database
from utils.shift_manager import ShiftManager


class AppController(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title(APP_CONFIG["title"])
        self.geometry(APP_CONFIG["window_size"])
        self.minsize(*APP_CONFIG["min_size"])
        self.configure(bg=COLORS["bg_dark"])
        
        # Set custom desktop/taskbar icon from icons/desktop.png
        try:
            from PIL import Image, ImageTk
            import os
            icon_path = os.path.join("icons", "app.png")
            if os.path.exists(icon_path):
                icon_img = Image.open(icon_path).resize((86, 86), Image.LANCZOS)
                self._icon_photo = ImageTk.PhotoImage(icon_img)
                self.iconphoto(True, self._icon_photo)
        except Exception:
            pass  # Silently skip if file not found or PIL unavailable
        
        # Initialize database
        self.db = Database()
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Initialize shift manager
        self.shift_manager = ShiftManager(self.db)
        
        self.colors = COLORS
        self.active_page = "dashboard"
        self.pages = {}
        
        self._create_layout()
        self._create_pages()
        self.show_page("dashboard")
    
    def _create_layout(self):
        self.sidebar = Sidebar(self, self)
        self.sidebar.pack(side="left", fill="y")
        
        self.content_area = tk.Frame(self, bg=COLORS["bg_dark"])
        self.content_area.pack(side="right", fill="both", expand=True)
        
        self.page_container = tk.Frame(self.content_area, bg=COLORS["bg_dark"])
        self.page_container.pack(fill="both", expand=True, padx=15, pady=15)
    
    def _create_pages(self):
        self.pages["dashboard"] = DashboardPage(self.page_container, self)
        self.pages["history"] = HistoryPage(self.page_container, self)
        self.pages["table_settings"] = TableSettingsPage(self.page_container, self)
        self.pages["plc_settings"] = PLCSettingsPage(self.page_container, self)
        self.pages["trigger_settings"] = TriggerSettingsPage(self.page_container, self)
        self.pages["shift_schedule"] = ShiftSchedulePage(self.page_container, self)
        self.pages["register_mp"] = RegisterMPPage(self.page_container, self)
        self.pages["help"] = HelpPage(self.page_container, self)
        
        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
    
    def show_page(self, page_name):
        if page_name not in self.pages:
            return
        
        # Notify previous page it is being hidden
        if self.active_page and self.active_page != page_name:
            prev = self.pages.get(self.active_page)
            if prev and hasattr(prev, 'on_hide'):
                prev.on_hide()
        
        self.sidebar.set_active(page_name)
        self.active_page = page_name
        
        page = self.pages[page_name]
        page.tkraise()
        
        if hasattr(page, 'on_show'):
            page.on_show()
    
    @property
    def table_data(self):
        return self.data_manager.table_data
    
    @property
    def plc_config(self):
        return self.data_manager.plc_config
    
    @property
    def trigger_config(self):
        return self.data_manager.trigger_config
    
    def save_table_data(self):
        self.data_manager.save_table_data()
    
    def save_plc_config(self):
        self.data_manager.save_plc_config()
    
    def save_trigger_config(self):
        self.data_manager.save_trigger_config()
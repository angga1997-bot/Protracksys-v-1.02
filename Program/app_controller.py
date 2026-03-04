"""
app_controller.py - Controller utama aplikasi
"""

import tkinter as tk
import threading
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
            pass

        # Initialize database
        self.db = Database()
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Initialize shift manager
        self.shift_manager = ShiftManager(self.db)
        
        self.colors = COLORS
        self.active_page = "dashboard"
        self.pages = {}
        
        # Global trigger monitor (runs always regardless of page)
        self._global_plc_client = None
        self._global_trigger_monitor = None
        
        self._create_layout()
        self._create_pages()
        self.show_page("dashboard")
        
        # Start the global trigger engine after pages are built
        self.after(500, self._start_global_trigger)
    
    # ================================================================
    # LAYOUT & PAGES
    # ================================================================

    def _create_layout(self):
        self.sidebar = Sidebar(self, self)
        self.sidebar.pack(side="left", fill="y")
        
        self.content_area = tk.Frame(self, bg=COLORS["bg_dark"])
        self.content_area.pack(side="right", fill="both", expand=True)
        
        self.page_container = tk.Frame(self.content_area, bg=COLORS["bg_dark"])
        self.page_container.pack(fill="both", expand=True, padx=15, pady=15)
    
    def _create_pages(self):
        self.pages["dashboard"]        = DashboardPage(self.page_container, self)
        self.pages["history"]          = HistoryPage(self.page_container, self)
        self.pages["table_settings"]   = TableSettingsPage(self.page_container, self)
        self.pages["plc_settings"]     = PLCSettingsPage(self.page_container, self)
        self.pages["trigger_settings"] = TriggerSettingsPage(self.page_container, self)
        self.pages["shift_schedule"]   = ShiftSchedulePage(self.page_container, self)
        self.pages["register_mp"]      = RegisterMPPage(self.page_container, self)
        self.pages["help"]             = HelpPage(self.page_container, self)
        
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
    
    # ================================================================
    # GLOBAL PLC TRIGGER ENGINE
    # ================================================================

    def _start_global_trigger(self):
        """Start global PLC trigger monitor. Runs on all pages."""
        self._stop_global_trigger()

        trigger_cfg = self.data_manager.trigger_config
        if not trigger_cfg.get("enabled", False):
            print("[GlobalTrigger] Trigger disabled — not starting.")
            self._update_plc_status("⚪ Trigger off", "text_secondary")
            return

        from utils.plc_fins import PLCFinsClient
        self._global_plc_client = PLCFinsClient(self.plc_config)
        self._update_plc_status("🟡 Connecting…", "accent_yellow")
        print("[GlobalTrigger] Connecting to PLC…")

        def _connect():
            ok, msg = self._global_plc_client.connect()
            self.after(0, lambda: self._on_global_connect(ok, msg))

        threading.Thread(target=_connect, daemon=True).start()

    def _on_global_connect(self, ok, msg):
        if not ok:
            print(f"[GlobalTrigger] Connect failed: {msg}")
            self._update_plc_status("🔴 PLC Error", "accent_red")
            self.after(15000, self._start_global_trigger)   # retry in 15 s
            return

        print(f"[GlobalTrigger] Connected: {msg}")
        self._update_plc_status("🟢 Trigger ON", "accent_green")

        from utils.trigger_monitor import TriggerMonitor
        trigger_cfg = self.data_manager.trigger_config
        self._global_trigger_monitor = TriggerMonitor(
            plc_client=self._global_plc_client,
            config=trigger_cfg,
            callback=self._on_global_trigger_event
        )
        self._global_trigger_monitor.start()

    def _stop_global_trigger(self):
        if self._global_trigger_monitor:
            try: self._global_trigger_monitor.stop()
            except Exception: pass
            self._global_trigger_monitor = None
        if self._global_plc_client:
            try: self._global_plc_client.disconnect()
            except Exception: pass
            self._global_plc_client = None

    def _on_global_trigger_event(self, event):
        """Relay trigger event to Tkinter main thread (thread-safe)."""
        self.after(0, lambda: self._handle_global_trigger(event))

    def _handle_global_trigger(self, event):
        """Handle trigger event — dispatched on the Tkinter main thread."""
        action      = event.get("action", "save_data")
        trigger_key = event.get("trigger_key", "main")
        img_cfg     = event.get("config")           # only set for image triggers
        trigger_time = event.get("timestamp")       # datetime when trigger fired

        dashboard = self.pages.get("dashboard")
        if not dashboard:
            return

        if trigger_key == "main" or action == "save_data":
            # Pass the global client so the dashboard reuses the same socket
            dashboard._plc_client = self._global_plc_client
            print(f"[GlobalTrigger] Main trigger → saving data row")
            dashboard._read_plc_and_save_row(capture_images=True)

        elif action == "capture_image" and img_cfg:
            # trigger_key is like "image_0", "image_1", ...
            try:
                trigger_index = int(trigger_key.split("_")[1])  # 0-based
            except (IndexError, ValueError):
                trigger_index = 0
            print(f"[GlobalTrigger] Image trigger {trigger_index} → capturing image")
            dashboard._update_last_row_image(
                img_cfg,
                trigger_index=trigger_index,
                trigger_time=trigger_time
            )


    def _update_plc_status(self, text, color_key):
        """Update PLC status label on dashboard if visible."""
        dashboard = self.pages.get("dashboard")
        if dashboard and hasattr(dashboard, "plc_status"):
            try:
                dashboard.plc_status.configure(
                    text=f"PLC: {text}",
                    fg=COLORS.get(color_key, COLORS["text_secondary"])
                )
            except Exception:
                pass

    def restart_global_trigger(self):
        """Called after saving trigger config to reload the monitor."""
        self.data_manager.reload_trigger_config()
        self._start_global_trigger()

    # ================================================================
    # PROPERTIES
    # ================================================================

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
"""
pages/__init__.py
"""

from pages.base_page import BasePage
from pages.dashboard_page import DashboardPage
from pages.table_settings_page import TableSettingsPage
from pages.plc_settings_page import PLCSettingsPage
from pages.trigger_settings_page import TriggerSettingsPage
from pages.register_mp_page import RegisterMPPage
from pages.history_page import HistoryPage
from pages.shift_schedule_page import ShiftSchedulePage
from pages.help_page import HelpPage
from PIL import Image, ImageTk
import os

__all__ = [
    'BasePage',
    'DashboardPage',
    'TableSettingsPage',
    'PLCSettingsPage',
    'TriggerSettingsPage',
    'RegisterMPPage',
    'HistoryPage',
    'ShiftSchedulePage',
    'HelpPage'
]
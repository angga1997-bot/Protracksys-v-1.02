"""
pages/help_page.py - Help Page
"""

import tkinter as tk
from pages.base_page import BasePage


class HelpPage(BasePage):
    """Help and documentation page"""
    
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._create_widgets()
    
    def _create_widgets(self):
        """Creates widgets"""
        self.create_header("❓ Help & Documentation")
        
        content = tk.Frame(self, bg=self.colors["bg_card"])
        content.pack(fill="both", expand=True, padx=10)
        
        help_text = """
        ╔══════════════════════════════════════════════════════════════════════════════════╗
        ║                        📊 TABLE + PLC APPLICATION GUIDE                          ║
        ╠══════════════════════════════════════════════════════════════════════════════════╣
        ║                                                                                  ║
        ║  🏠 DASHBOARD                                                                    ║
        ║  ─────────────                                                                   ║
        ║  • View and manage table data                                                    ║
        ║  • Click 🗑️ on each row to delete                                              ║
        ║  • Date/Time columns are auto-filled when adding data                            ║
        ║  • Export data to CSV                                                            ║
        ║                                                                                  ║
        ║  📋 TABLE SETTINGS                                                               ║
        ║  ─────────────────                                                               ║
        ║  • Add/delete/edit column names                                                  ║
        ║  • Set column width (50-500 px)                                                  ║
        ║  • Quick add for Date/Time columns                                               ║
        ║                                                                                  ║
        ║  🔌 PLC SETTINGS (FINS TCP/IP)                                                   ║
        ║  ──────────────────────────────                                                  ║
        ║  • Connection config: IP, Port, Network/Node/Unit Address                        ║
        ║  • Default FINS port: 9600                                                       ║
        ║  • Set memory areas: DM, CIO, WR, HR, AR, EM                                     ║
        ║  • Test connection and read data                                                 ║
        ║                                                                                  ║
        ║  📖 OMRON PLC MEMORY AREAS                                                       ║
        ║  ─────────────────────────                                                       ║
        ║  • DM (Data Memory)     : D0 - D32767    - General data storage                  ║
        ║  • CIO (Core I/O)       : CIO 0 - 6143   - I/O and internal relays               ║
        ║  • WR (Work Area)       : W0 - W511      - Temporary work relays                 ║
        ║  • HR (Holding Area)    : H0 - H1535     - Retained data                         ║
        ║  • AR (Auxiliary Area)  : A0 - A959      - System/auxiliary area                 ║
        ║  • EM (Extended Memory) : E0_0 - E18_32767 - Extended data memory                ║
        ║                                                                                  ║
        ║  🕐 AUTO-FILL DATE/TIME                                                          ║
        ║  ───────────────────────                                                         ║
        ║  • 📅 Column "date/record date"       → YYYY-MM-DD                              ║
        ║  • 🕐 Column "time/waktu"             → HH:MM:SS                                ║
        ║  • 📆 Column "datetime/timestamp"    → YYYY-MM-DD HH:MM:SS                       ║
        ║                                                                                  ║
        ║  💾 DATA FILES                                                                   ║
        ║  ─────────────                                                                   ║
        ║  • data/table_data.json  - Table data                                            ║
        ║  • data/plc_config.json  - PLC configuration                                     ║
        ║                                                                                  ║
        ╚══════════════════════════════════════════════════════════════════════════════════╝
        """
        
        tk.Label(
            content,
            text=help_text,
            font=("Consolas", 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            justify="left",
            anchor="nw",
            padx=20,
            pady=20
        ).pack(fill="both", expand=True)

"""
main.py - Entry point aplikasi
"""

import sys
import os

# Fix working directory when running as PyInstaller .exe
# --onefile: resources are in sys._MEIPASS (hidden temp folder - users cannot access)
# --onedir: resources are alongside the exe
if getattr(sys, 'frozen', False):
    if hasattr(sys, '_MEIPASS'):
        os.chdir(sys._MEIPASS)   # --onefile: use embedded hidden temp folder
    else:
        os.chdir(os.path.dirname(sys.executable))  # --onedir fallback

import tkinter as tk
from PIL import Image, ImageTk

from app_controller import AppController


def show_splash(root):
    """Show splash screen as a Toplevel on the root window."""
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)   # Remove title bar / borders
    splash.attributes("-topmost", True)
    splash.configure(bg="#0f0f1a")

    try:
        img = Image.open(os.path.join("icons", "login.png"))
        img.thumbnail((500, 500), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img, master=root)
        lbl = tk.Label(splash, image=photo, bg="#0f0f1a", bd=0)
        lbl.image = photo
        lbl.pack(pady=20, padx=20)
    except Exception:
        tk.Label(splash, text="Loading...", font=("Segoe UI", 16),
                 bg="#0f0f1a", fg="white").pack(pady=40, padx=60)

    tk.Label(splash, text="Production Tracking Data System",
             font=("Segoe UI", 11), bg="#0f0f1a", fg="#a0a0c0").pack(pady=(0, 5))
    tk.Label(splash, text="Loading, please wait...",
             font=("Segoe UI", 9), bg="#0f0f1a", fg="#4a4a6a").pack(pady=(0, 20))

    # Center splash on screen
    splash.update_idletasks()
    w = splash.winfo_reqwidth()
    h = splash.winfo_reqheight()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    splash.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    return splash


def main():
    # Create the main app as the single Tk root (but keep it hidden)
    app = AppController()
    app.withdraw()

    # Global MouseWheel handler for the entire application (scrolls canvas under cursor)
    def _global_mouse_wheel(event):
        try:
            widget = event.widget.winfo_containing(event.x_root, event.y_root)
        except Exception:
            return
            
        while widget:
            if isinstance(widget, tk.Canvas):
                try:
                    widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
                except Exception:
                    pass
                break
            widget = getattr(widget, "master", None)

    app.bind_all("<MouseWheel>", _global_mouse_wheel)


    # Show splash as Toplevel on top of the hidden main window
    splash = show_splash(app)
    app.update()

    # After 2.5 seconds: close splash and reveal main window
    def close_splash():
        splash.destroy()
        app.deiconify()

    app.after(2500, close_splash)
    app.mainloop()



if __name__ == "__main__":
    main()


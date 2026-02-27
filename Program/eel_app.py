"""
eel_app.py - Eel Application Entry Point
Login screen for Production Tracking Data System
Run with: python eel_app.py
"""

import eel
import sys
import os

# Initialize Eel with the web folder
eel.init('web')


# ================================================================
# PYTHON FUNCTIONS EXPOSED TO JAVASCRIPT
# ================================================================

@eel.expose
def login(username, password):
    """
    Validate login credentials.
    Returns: dict with 'success' (bool) and 'message' (str)

    TODO: Replace with real credential validation (e.g. from a database or config file)
    """
    # Simple demo credentials - replace with your real validation logic
    VALID_USERS = {
        "admin": "admin123",
        "operator": "operator123",
    }

    if username in VALID_USERS and VALID_USERS[username] == password:
        print(f"[LOGIN] User '{username}' logged in successfully.")

        # After successful login, open the main app
        eel.spawn(open_main_app)

        return {"success": True, "message": "Login successful!"}
    else:
        print(f"[LOGIN] Failed login attempt for user '{username}'.")
        return {"success": False, "message": "Invalid username or password"}


def open_main_app():
    """
    Called after successful login.
    Currently just closes eel. 
    You can extend this to launch the main tkinter app or another Eel page.
    """
    import time
    time.sleep(1.2)  # Brief pause to show success message

    # Option 1: Launch the main tkinter application
    # import subprocess
    # subprocess.Popen([sys.executable, "main.py"])
    # eel.shutdown()

    # Option 2: Navigate to a dashboard page (if built)
    # eel.show('dashboard.html')

    # For now: print and exit
    print("[APP] Login successful - proceeding to main application.")
    os._exit(0)


# ================================================================
# START EEL APP
# ================================================================

if __name__ == "__main__":
    print("Starting Production Tracking Data System...")
    print("Opening login window...")

    try:
        eel.start(
            'login.html',
            size=(480, 700),
            position=('center', 'center'),
            mode='chrome',
            port=8686,
            close_callback=lambda p, c: os._exit(0)
        )
    except (SystemExit, EnvironmentError):
        # Fallback to default browser if Chrome not found
        eel.start(
            'login.html',
            size=(480, 700),
            mode='default',
            port=8686,
            close_callback=lambda p, c: os._exit(0)
        )

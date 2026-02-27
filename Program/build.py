"""
build.py - Script to package ProTrackSys as a standalone .exe
Run with: python build.py
"""

import subprocess
import sys
import os
import shutil

# Fix emoji output on Windows terminals
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

APP_NAME = "ProTrackSys"
MAIN_SCRIPT = "main.py"
ICON = os.path.join("icons", "app.png")

def clean():
    """Remove previous build artifacts"""
    for folder in ["dist", "build"]:
        if os.path.exists(folder):
            print(f"Cleaning {folder}/...")
            shutil.rmtree(folder, ignore_errors=True)
    spec_file = f"{APP_NAME}.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)

def build():
    print("=" * 50)
    print(f"Building {APP_NAME}...")
    print("=" * 50)

    # Check required folders exist
    for folder in ["icons", "data"]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created missing folder: {folder}/")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",                        # Single .exe - icons embedded inside, not visible to user
        "--windowed",                       # No console window
        "--name", APP_NAME,
        "--icon", ICON,
        "--add-data", "icons;icons",        # Bundle icons folder (hidden inside .exe)
        "--add-data", "web;web",            # Bundle web folder
        "--add-data", "data;data",          # Bundle data folder
        MAIN_SCRIPT
    ]

    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = os.path.join("dist", APP_NAME, f"{APP_NAME}.exe")
        print("\n" + "=" * 50)
        print("✅ Build successful!")
        print(f"📁 Location: {os.path.abspath(exe_path)}")
        print("=" * 50)
        print("\nTo run: double-click the .exe in the dist folder")
        print("To share: copy the entire dist\\ProTrackSys\\ folder")
    else:
        print("\n❌ Build failed! Check the output above for errors.")
        sys.exit(1)

if __name__ == "__main__":
    clean()
    build()

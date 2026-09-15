"""
Standalone Desktop Executable Builder for Neon Snake Arcade.
Compiles Python, Pygame, and all game logic into a single self-contained NeonSnake.exe
using PyInstaller. The output .exe runs on any Windows PC without needing Python installed.
"""

import os
import sys
import subprocess

def build():
    print("=========================================================")
    print(" Building Standalone Desktop Executable: NeonSnake.exe   ")
    print("=========================================================")

    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("[!] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",           # Also test onefile
        "--onefile",          # Pack everything into a single executable file!
        "--windowed",         # No black console window
        "--name", "NeonSnake",
        "main.py",
    ]

    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    dist_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "NeonSnake.exe")
    if os.path.exists(dist_exe):
        size_mb = os.path.getsize(dist_exe) / (1024 * 1024)
        print("=========================================================")
        print(f" SUCCESS! Standalone executable created:")
        print(f" -> {dist_exe} ({size_mb:.1f} MB)")
        print(f" You can copy this .exe to ANY Windows PC and play!")
        print("=========================================================")
    else:
        print("[!] Build finished, check dist/ directory.")

if __name__ == "__main__":
    build()

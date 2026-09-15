"""
Universal Entry Point for Neon Snake Arcade.
Compatible with Desktop (Windows, macOS, Linux) and Mobile (Android via python-for-android / Buildozer / Pydroid 3).
"""

import sys
import os

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from snake_game import SnakeGame

def main():
    game = SnakeGame()
    game.run()

if __name__ == "__main__":
    main()

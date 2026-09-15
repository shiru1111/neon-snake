# 🐍 Neon Snake Arcade (Python)

A modern, polished retro arcade Snake game built in Python using **Pygame**.

![Snake Arcade Preview](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.6+-green?style=for-the-badge)

---

## ✨ Features

- **Fixed Speed (20 steps/second)**: Consistent, fast, and smooth pace throughout the game (no sudden acceleration).
- **5-Second Auto-Restart on Death**: Displays your final score card with a clean 5-second countdown timer, then automatically starts a new game (or press <kbd>R</kbd> / <kbd>SPACE</kbd> to restart instantly).
- **Smarter Autonomous AI**:
  - Longest-path tail stalling prevents tight-corridor traps.
  - Box-method connected space evaluation prevents entering dead-end pockets.
  - Precise tail growth timing ensures zero self-collisions right after eating.
- **Interactive In-Game Cheats & Abilities**:
  - <kbd>Q</kbd> Key: **Spawn Extra Food** anywhere on the board (multi-food support with smart AI targeting).
  - <kbd>E</kbd> Key: **Bomb the Snake**, shaving off 3 tail segments with an explosive burst and bass thud (with safe minimum length protection).
- **Satisfying & Eye-Friendly Aesthetics**:
  - Calming deep twilight navy palette (`#0d131d`) with subtle dot-grid markers to prevent eye strain.
  - Smooth flowing tapered snake body with seamless capsule joints and a sleek tapered tail.
  - Expressive glossy snake eyes with directional pupils and lively specular reflections.
  - Floating popup text notifications (`+10`, `+50 STAR!`, `💥 BOMB! -3`, `+🍎 FOOD`).
- **Fixed Game Modes**:
  - **Manual Player Mode**: Play yourself using Arrow keys or WASD.
  - **Smart AI Autopilot**: Watch the autonomous AI navigate at fixed 20 speed.
- **Procedural 8-Bit Audio**: Built-in sound synthesis for eating, collecting bonus stars, explosions, food spawning, and clicks—**zero audio files required!**
- **Dual Food System**:
  - **Ruby Apple**: Standard food (+10 pts, grows snake by 1).
  - **Timed Golden Star**: Spawns every 5 apples, stays for 8 seconds (+50 pts + time bonus, grows snake by 2).
- **Particle System**: Sparkles on eat and spawn, plus fiery explosion bursts when bombing or crashing.
- **Wins & Losses Lifetime Record Tracking**:
  - Tracks total Wins, Losses, and Win Rate persistently in `highscore.json`.
  - Reaching a target score milestone (>= 500 pts) or setting a new High Score record counts as a **WIN** with triumphant fanfare sound!
  - Real-time `RECORD (W/L)` HUD counter, match result banner (Victory/Defeat), and main menu summary.
- **Pure Desktop & Mobile Application**:
  - **Windows Desktop Executable (`NeonSnake.exe`)**: Built into `dist/NeonSnake.exe`—runs on ANY Windows desktop/laptop without needing Python installed!
  - **Android Mobile App (`.apk`)**: Full touch controls & swipe steering configured for Android APK packaging via Buildozer / GitHub Actions / Pydroid 3.

---

## 🎮 Controls

| Action | Keyboard | Mobile / Touchscreen (CP) |
| :--- | :--- | :--- |
| **Move** | <kbd>↑</kbd> <kbd>↓</kbd> <kbd>←</kbd> <kbd>→</kbd> or <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> | **Swipe anywhere** or tap on-screen **D-Pad** |
| **+Food Cheat** | <kbd>Q</kbd> | Tap on-screen **[+🍎 FOOD]** button |
| **Bomb Cheat** | <kbd>E</kbd> | Tap on-screen **[💥 BOMB]** button |
| **Select Mode** | <kbd>1</kbd> (Manual) / <kbd>2</kbd> (AI) | **Tap Mode Cards** directly |
| **Pause / Resume** | <kbd>Space</kbd> or <kbd>P</kbd> | Tap top-right **[Pause]** button |
| **Sound Toggle** | <kbd>M</kbd> | Tap top-right **[SFX]** button |
| **Restart Game** | <kbd>R</kbd> | Tap screen on Game Over |
| **Main Menu** | <kbd>ESC</kbd> | Tap **Main Menu** button |

---

## 🚀 How to Run & Play

### 1. Play on Another Desktop (No Python Required!)
- Simply copy **`dist\NeonSnake.exe`** to any Windows computer and double-click to play!
- To re-build the executable at any time:
  ```powershell
  py build_desktop.py
  # or double-click build_desktop.bat
  ```

### 2. Play on Mobile Phone (Android App)
You have 3 easy ways to run as a pure mobile app:

- **Method A: Direct on Phone via Pydroid 3 (Instant, No Compile)**
  1. Install **Pydroid 3** from Google Play Store on your Android phone.
  2. Inside Pydroid 3, open the game folder and tap `Pip` -> install `pygame`.
  3. Open `main.py` and tap the **Play** button!
  4. The game launches in full screen with touch controls, virtual D-Pad, and swipe navigation.

- **Method B: Cloud APK Build with GitHub Actions (Free & Automatic)**
  1. Push this repository to GitHub.
  2. Go to the **Actions** tab on GitHub -> select **Build Android APK** -> click **Run workflow**.
  3. When finished (~5 min), download the generated **`NeonSnake-Android-APK`** artifact and install the `.apk` on your phone!

- **Method C: Local Build with Buildozer (Linux / WSL)**
  ```bash
  pip install buildozer
  buildozer android debug
  ```
  The resulting `.apk` will be output into the `bin/` directory.

### 3. Run from Python Source Code
```bash
py main.py
# or
python main.py
```



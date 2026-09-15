[app]

# (str) Title of your application
title = Neon Snake Arcade

# (str) Package name
package.name = neonsnake

# (str) Package domain (needed for android/ios packaging)
package.domain = org.arcade

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (list) List of inclusions using pattern matching
source.include_patterns = *.py, *.json

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,pygame-ce

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2

# (str) Path to local recipes directory
p4a.local_recipes = ./p4a-recipes

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = all

# (bool) Indicate if the application should be fullscreen to the user
fullscreen = 1

# (list) Permissions
android.permissions = VIBRATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk
android.skip_update = False

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug with command output)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 0

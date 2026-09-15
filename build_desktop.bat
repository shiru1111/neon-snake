@echo off
title Building Neon Snake Desktop Executable (.exe)
echo ========================================================
echo  Building NeonSnake.exe (Standalone Windows Executable)
echo ========================================================
py build_desktop.py
if errorlevel 1 (
    echo [ERROR] Build failed. Make sure Python is installed.
    pause
    exit /b 1
)
echo.
echo Standalone executable is located in: dist\NeonSnake.exe
echo You can copy NeonSnake.exe to any Windows desktop and double-click to play!
pause

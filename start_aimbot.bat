@echo off
title AI-Aimbot Launcher

echo.
echo ====================================
echo      AI-Aimbot Launcher
echo ====================================
echo.

echo [INFO] Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [!] Virtual environment not found, using system Python
)

echo.
echo [INFO] Checking Python dependencies...

python -c "import tkinter" 2>nul
if errorlevel 1 (
    echo [!] Installing tkinter...
    pip install tk
)

python -c "import serial" 2>nul
if errorlevel 1 (
    echo [!] Installing pyserial...
    pip install pyserial
)

python -c "import cv2" 2>nul
if errorlevel 1 (
    echo [!] Installing opencv-python...
    pip install opencv-python
)

python -c "import torch" 2>nul
if errorlevel 1 (
    echo [!] Installing torch...
    pip install torch torchvision
)

echo [OK] Dependencies check completed
echo.
echo [INFO] Starting AI-Aimbot GUI...
echo.

python aimbot_gui.py

echo.
echo [INFO] AI-Aimbot exited
pause
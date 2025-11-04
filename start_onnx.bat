@echo off
setlocal ENABLEDELAYEDEXPANSION
title AI-Aimbot ONNX Launcher

echo ====================================
echo   AI-Aimbot ONNX Launcher
echo ====================================

rem Select Python and Pip (prefer .venv)
set PY=python
set PIP=pip
if exist ".venv\Scripts\python.exe" (
    set PY=.venv\Scripts\python.exe
    echo [INFO] Using venv Python: %PY%
)
if exist ".venv\Scripts\pip.exe" (
    set PIP=.venv\Scripts\pip.exe
    echo [INFO] Using venv Pip: %PIP%
)

echo [INFO] Checking Python dependencies...
%PY% -c "import onnxruntime" 2>nul || (
    echo [!] Installing onnxruntime-gpu...
    %PIP% install onnxruntime-gpu
)
%PY% -c "import GPUtil" 2>nul || (
    echo [!] Installing GPUtil...
    %PIP% install GPUtil
)
%PY% -c "import numpy" 2>nul || (
    echo [!] Installing numpy...
    %PIP% install numpy
)
%PY% -c "import win32api" 2>nul || (
    echo [!] Installing pywin32...
    %PIP% install pywin32
)
%PY% -c "import bettercam" 2>nul || (
    echo [!] Installing bettercam...
    %PIP% install bettercam
)

echo [OK] Dependencies check completed
echo [INFO] Starting main_onnx.py...

%PY% main_onnx.py

echo.
echo [INFO] AI-Aimbot exited
pause
endlocal
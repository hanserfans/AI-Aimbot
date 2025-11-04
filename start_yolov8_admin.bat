@echo off
title 瓦洛兰特 YOLOv8 自动瞄准 - 管理员模式
echo.
echo ========================================
echo    瓦洛兰特 YOLOv8 自动瞄准系统
echo ========================================
echo.
echo 正在以管理员权限启动...
echo.

REM 检查是否以管理员权限运行
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ 管理员权限确认
    goto :run_program
) else (
    echo ❌ 需要管理员权限，正在重新启动...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:run_program
echo.
echo 🔄 激活虚拟环境...
cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo.
echo 🎯 启动瓦洛兰特YOLOv8自动瞄准...
echo.
echo 📋 控制说明:
echo    - 按住鼠标右键: 激活自动瞄准
echo    - 按 Q 键: 退出程序
echo    - 按 R 键: 显示状态信息
echo.
echo ⚠️ 请确保瓦洛兰特游戏已启动
echo.

python main_yolov8.py

echo.
echo 程序已退出，按任意键关闭窗口...
pause >nul
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-Hub鼠标移动修复补丁
修复MouseMove.py中的参数处理问题
"""

import ctypes
import sys
import os

# 添加mouse_driver路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))

from mouse_driver.MouseMove import (
    mouse_open, handle, found, MOUSE_IO, call_mouse, clamp_char
)

def fixed_mouse_move_internal(button: int, x: int, y: int, wheel: int) -> bool:
    """
    修复后的内部鼠标移动函数
    替换原有的_mouse_move_internal
    """
    # 确保设备已打开
    if not found or handle == 0:
        if not mouse_open():
            return False
    
    # 限制参数范围
    x_clamped = clamp_char(x)
    y_clamped = clamp_char(y)
    btn_byte = clamp_char(button)
    wheel_byte = clamp_char(wheel)
    
    # 创建MOUSE_IO结构体
    io = MOUSE_IO()
    try:
        io.button = ctypes.c_char(btn_byte.to_bytes(1, 'little', signed=True))
        io.x = ctypes.c_char(x_clamped.to_bytes(1, 'little', signed=True))
        io.y = ctypes.c_char(y_clamped.to_bytes(1, 'little', signed=True))
        io.wheel = ctypes.c_char(wheel_byte.to_bytes(1, 'little', signed=True))
        io.unk1 = ctypes.c_char(b'\x00')
    except Exception:
        return False
    
    # 调用底层函数
    return call_mouse(io)

def fixed_ghub_move(x: int, y: int) -> None:
    """
    修复后的ghub_move函数
    """
    # 确保设备已初始化
    if not found:
        if not mouse_open():
            print("G-Hub device not available. Please ensure Logitech G-Hub is installed and running.")
            return
    
    # 调用修复后的内部函数
    fixed_mouse_move_internal(0, x, y, 0)

# 应用补丁
def apply_ghub_fix():
    """应用G-Hub修复补丁"""
    import mouse_driver.MouseMove as mm
    
    # 替换函数
    mm._mouse_move_internal = fixed_mouse_move_internal
    mm.ghub_move = fixed_ghub_move
    mm.mouse_move = fixed_ghub_move
    
    print("✅ G-Hub修复补丁已应用")
    return True

if __name__ == "__main__":
    apply_ghub_fix()

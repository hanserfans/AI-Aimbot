#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终G-Hub修复补丁
修复MouseMove.py中的c_char字段赋值问题
确保在瓦洛兰特中正常工作
"""

import ctypes
import sys
import os

# 添加mouse_driver路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))

from mouse_driver.MouseMove import (
    mouse_open, handle, found, MOUSE_IO, call_mouse, clamp_char
)

def correct_mouse_move_internal(button: int, x: int, y: int, wheel: int) -> bool:
    """
    正确的内部鼠标移动函数
    修复c_char字段赋值问题
    """
    global handle
    
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
        # 正确的c_char字段赋值 - 直接赋值整数
        io.button = btn_byte
        io.x = x_clamped
        io.y = y_clamped
        io.wheel = wheel_byte
        io.unk1 = 0
    except Exception:
        return False
    
    # 调用底层函数
    return call_mouse(io)

def correct_ghub_move(x: int, y: int) -> None:
    """
    正确的ghub_move函数
    """
    # 确保设备已初始化
    if not found:
        if not mouse_open():
            print("G-Hub device not available. Please ensure Logitech G-Hub is installed and running.")
            return
    
    # 调用正确的内部函数
    correct_mouse_move_internal(0, x, y, 0)

# 应用最终修复
def apply_final_ghub_fix():
    """应用最终G-Hub修复补丁"""
    import mouse_driver.MouseMove as mm
    
    # 替换函数
    mm._mouse_move_internal = correct_mouse_move_internal
    mm.ghub_move = correct_ghub_move
    mm.mouse_move = correct_ghub_move
    
    print("✅ 最终G-Hub修复补丁已应用")
    print("🎯 现在G-Hub驱动应该能在瓦洛兰特中正常工作了！")
    return True

if __name__ == "__main__":
    apply_final_ghub_fix()

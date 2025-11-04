#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极G-Hub修复补丁
正确处理有符号字节值的c_char字段赋值
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

def signed_byte_to_char(value: int) -> int:
    """将有符号整数转换为c_char可接受的值"""
    clamped = clamp_char(value)
    if clamped < 0:
        return 256 + clamped  # 二进制补码
    else:
        return clamped

def ultimate_mouse_move_internal(button: int, x: int, y: int, wheel: int) -> bool:
    """
    终极内部鼠标移动函数
    正确处理有符号字节值
    """
    global handle
    
    # 确保设备已打开
    if not found or handle == 0:
        if not mouse_open():
            return False
    
    # 处理参数
    x_clamped = clamp_char(x)
    y_clamped = clamp_char(y)
    btn_byte = clamp_char(button)
    wheel_byte = clamp_char(wheel)
    
    # 转换为c_char可接受的值
    btn_char = signed_byte_to_char(btn_byte)
    x_char = signed_byte_to_char(x_clamped)
    y_char = signed_byte_to_char(y_clamped)
    wheel_char = signed_byte_to_char(wheel_byte)
    
    # 创建MOUSE_IO结构体
    io = MOUSE_IO()
    try:
        io.button = btn_char
        io.x = x_char
        io.y = y_char
        io.wheel = wheel_char
        io.unk1 = 0
    except Exception:
        return False
    
    # 调用底层函数
    return call_mouse(io)

def ultimate_ghub_move(x: int, y: int) -> None:
    """
    终极ghub_move函数
    """
    # 确保设备已初始化
    if not found:
        if not mouse_open():
            print("G-Hub device not available. Please ensure Logitech G-Hub is installed and running.")
            return
    
    # 调用终极内部函数
    ultimate_mouse_move_internal(0, x, y, 0)

# 应用终极修复
def apply_ultimate_ghub_fix():
    """应用终极G-Hub修复补丁"""
    import mouse_driver.MouseMove as mm
    
    # 替换函数
    mm._mouse_move_internal = ultimate_mouse_move_internal
    mm.ghub_move = ultimate_ghub_move
    mm.mouse_move = ultimate_ghub_move
    
    print("✅ 终极G-Hub修复补丁已应用")
    print("🎯 G-Hub驱动现在应该能在瓦洛兰特中完美工作了！")
    return True

if __name__ == "__main__":
    apply_ultimate_ghub_fix()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-Hub最终修复补丁
基于深度分析和测试的稳定解决方案
"""

import time
import ctypes

def safe_ghub_move_patch(x, y):
    """安全的G-Hub移动函数补丁"""
    from mouse_driver.MouseMove import found, handle, call_mouse, MOUSE_IO, ghub_move
    
    if not found:
        return False
    
    def signed_byte_to_char(value):
        """安全的字节转换"""
        clamped = max(-128, min(127, value))
        if clamped < 0:
            return clamped + 256
        return clamped
    
    def direct_call_move(x, y):
        """直接调用call_mouse"""
        try:
            mouse_io = MOUSE_IO()
            mouse_io.button = ctypes.c_char(0)
            mouse_io.x = ctypes.c_char(signed_byte_to_char(x))
            mouse_io.y = ctypes.c_char(signed_byte_to_char(y))
            mouse_io.wheel = ctypes.c_char(0)
            mouse_io.unk1 = ctypes.c_char(0)
            
            result = call_mouse(handle, mouse_io)
            return result == 1
        except:
            return False
    
    # 对于所有移动，直接使用call_mouse
    # 这避免了ghub_move的数值范围问题
    return direct_call_move(x, y)

# 应用补丁
def apply_patch():
    """应用G-Hub修复补丁"""
    import mouse_driver.MouseMove as mm
    
    # 备份原函数
    mm._original_ghub_move = mm.ghub_move
    
    # 替换为修复版本
    def patched_ghub_move(x, y):
        return safe_ghub_move_patch(x, y)
    
    mm.ghub_move = patched_ghub_move
    print("✅ G-Hub修复补丁已应用")

if __name__ == "__main__":
    apply_patch()

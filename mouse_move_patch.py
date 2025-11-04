
# 在MouseMove.py末尾添加以下代码作为备用方案

import ctypes
from ctypes import wintypes

def reliable_mouse_move(dx, dy):
    """可靠的鼠标移动函数 - 自动回退到Win32 API"""
    try:
        # 首先尝试G-Hub移动
        ghub_move(dx, dy)
        
        # 验证移动是否生效
        user32 = ctypes.windll.user32
        point_before = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(point_before))
        
        import time
        time.sleep(0.05)
        
        point_after = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(point_after))
        
        # 如果位置没有变化，使用Win32备用方案
        if point_before.x == point_after.x and point_before.y == point_after.y:
            user32.mouse_event(0x0001, int(dx), int(dy), 0, 0)
            
    except Exception:
        # 如果G-Hub完全失败，直接使用Win32
        user32 = ctypes.windll.user32
        user32.mouse_event(0x0001, int(dx), int(dy), 0, 0)

# 替换原有的mouse_move函数
mouse_move = reliable_mouse_move

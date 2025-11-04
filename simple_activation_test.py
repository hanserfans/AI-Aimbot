#!/usr/bin/env python3
"""简单的激活键测试"""
import win32api
import time

print("简单激活键测试 - 按右键或Caps Lock测试")
print("按 Ctrl+C 退出")

try:
    while True:
        caps_lock_pressed = win32api.GetKeyState(0x14) & 0x0001
        right_mouse_pressed = win32api.GetKeyState(0x02) & 0x8000
        
        status = []
        if right_mouse_pressed:
            status.append("右键")
        if caps_lock_pressed:
            status.append("Caps Lock")
        
        if status:
            print(f"激活: {' + '.join(status)}")
        else:
            print("无激活键", end="\r")
        
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n测试结束")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按键诊断脚本 - 检测Caps Lock和鼠标右键的实际状态
用于诊断按键混淆问题
"""

import win32api
import time
from auto_trigger_system import get_trigger_system

def main():
    print("🔍 按键诊断工具")
    print("=" * 50)
    
    # 初始化扳机系统
    trigger_system = get_trigger_system()
    print(f"📊 扳机系统状态: {'✅ 启用' if trigger_system.enabled else '❌ 禁用'}")
    
    print("\n🎯 按键状态监控:")
    print("   • Caps Lock (0x14) - 应该激活瞄准")
    print("   • 鼠标右键 (0x02) - 应该激活扳机")
    print("   • 按 Ctrl+C 退出")
    print("-" * 50)
    
    last_caps_state = False
    last_right_mouse_state = False
    
    try:
        while True:
            # 检测 Caps Lock (0x14)
            caps_pressed = win32api.GetKeyState(0x14) < 0
            
            # 检测鼠标右键 (0x02)
            right_mouse_pressed = win32api.GetKeyState(0x02) < 0
            
            # 只在状态改变时打印
            if caps_pressed != last_caps_state:
                status = "🟢 按下" if caps_pressed else "🔴 释放"
                print(f"[{time.strftime('%H:%M:%S')}] Caps Lock (0x14): {status}")
                last_caps_state = caps_pressed
            
            if right_mouse_pressed != last_right_mouse_state:
                status = "🟢 按下" if right_mouse_pressed else "🔴 释放"
                print(f"[{time.strftime('%H:%M:%S')}] 鼠标右键 (0x02): {status}")
                
                # 检查扳机系统状态
                if right_mouse_pressed:
                    cooldown_status = "❄️ 冷却中" if trigger_system.is_on_cooldown() else "🔥 可触发"
                    print(f"                    扳机状态: {cooldown_status}")
                
                last_right_mouse_state = right_mouse_pressed
            
            # 同时按下时的特殊提示
            if caps_pressed and right_mouse_pressed:
                print(f"[{time.strftime('%H:%M:%S')}] ⚠️  同时按下 Caps Lock 和鼠标右键")
            
            time.sleep(0.05)  # 50ms检测间隔
            
    except KeyboardInterrupt:
        print("\n\n✅ 诊断完成")
        print("📋 诊断结果:")
        print("   • 如果Caps Lock能正常检测但不激活瞄准 → 瞄准逻辑问题")
        print("   • 如果鼠标右键能正常检测但不开火 → 扳机逻辑问题")
        print("   • 如果按键检测异常 → 按键码问题")

if __name__ == "__main__":
    main()
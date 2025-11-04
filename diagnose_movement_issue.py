#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鼠标移动问题诊断脚本
用于诊断为什么鼠标移动一次后停止，以及激活键检测问题
"""

import time
import win32api
import win32con

def diagnose_movement_issue():
    """诊断鼠标移动停止的问题"""
    print("🔍 鼠标移动问题诊断脚本")
    print("=" * 50)
    print("问题描述: 鼠标移动一次后停止，显示'目标偏离中心 28.0px，无激活键按下'")
    print()
    
    print("📋 检查项目:")
    print("1. 激活键检测逻辑")
    print("2. 移动循环机制")
    print("3. 键盘状态检测")
    print()
    
    print("🎯 激活键说明:")
    print("   • 右键 (0x02) - 激活瞄准+扳机")
    print("   • Caps Lock (0x14) - 仅激活瞄准")
    print()
    
    print("⌨️ 请按住激活键进行测试...")
    print("按 ESC 键退出")
    print()
    
    last_right_state = False
    last_caps_state = False
    movement_count = 0
    
    while True:
        try:
            # 检测ESC键退出
            if win32api.GetKeyState(0x1B) < 0:  # ESC
                print("\n👋 退出诊断")
                break
            
            # 检测激活键状态
            right_mouse_pressed = win32api.GetKeyState(0x02) < 0  # 右键
            caps_lock_pressed = win32api.GetKeyState(0x14) < 0   # Caps Lock
            
            # 检测状态变化
            if right_mouse_pressed != last_right_state:
                status = "🟢 按下" if right_mouse_pressed else "🔴 释放"
                print(f"[{time.strftime('%H:%M:%S')}] 右键 (0x02): {status}")
                last_right_state = right_mouse_pressed
            
            if caps_lock_pressed != last_caps_state:
                status = "🟢 按下" if caps_lock_pressed else "🔴 释放"
                print(f"[{time.strftime('%H:%M:%S')}] Caps Lock (0x14): {status}")
                last_caps_state = caps_lock_pressed
            
            # 模拟主循环的激活键检测逻辑
            activation_detected = False
            activation_type = ""
            
            if right_mouse_pressed:
                activation_detected = True
                activation_type = "右键 (瞄准+扳机)"
            elif caps_lock_pressed:
                activation_detected = True
                activation_type = "Caps Lock (仅瞄准)"
            
            # 显示当前状态
            if activation_detected:
                movement_count += 1
                print(f"[{time.strftime('%H:%M:%S')}] ✅ 激活键检测成功: {activation_type}")
                print(f"                    📊 模拟移动次数: {movement_count}")
                
                # 模拟移动逻辑
                if movement_count % 10 == 0:  # 每10次显示一次详细信息
                    print(f"                    🎯 如果有目标，此时应该执行鼠标移动")
                    print(f"                    📍 移动后应该继续检测目标位置")
                    print(f"                    🔄 如果目标仍偏离中心，应该继续移动")
            else:
                if movement_count > 0:
                    print(f"[{time.strftime('%H:%M:%S')}] ❌ 无激活键按下 - 停止移动")
                    print(f"                    📊 总移动次数: {movement_count}")
                    movement_count = 0
            
            time.sleep(0.1)  # 100ms检测间隔
            
        except KeyboardInterrupt:
            print("\n👋 用户中断，退出诊断")
            break
    
    print("\n📋 诊断总结:")
    print("=" * 50)
    print("🔍 可能的问题原因:")
    print("1. 激活键检测逻辑正确，但用户没有持续按住激活键")
    print("2. 主循环中的激活键检测可能有时序问题")
    print("3. 移动完成后没有重新检测激活键状态")
    print("4. 移动逻辑可能在单次移动后退出了激活状态检测")
    print()
    print("💡 建议解决方案:")
    print("1. 确保持续按住激活键（右键或Caps Lock）")
    print("2. 检查主循环中的激活键检测时序")
    print("3. 优化移动逻辑，确保连续移动直到目标对齐")
    print("4. 添加更详细的调试信息显示激活键状态")

def test_continuous_activation():
    """测试连续激活键检测"""
    print("\n🔄 连续激活键检测测试")
    print("=" * 30)
    print("请按住右键或Caps Lock，观察检测连续性...")
    print("按 ESC 退出")
    
    detection_count = 0
    start_time = time.time()
    
    while True:
        try:
            if win32api.GetKeyState(0x1B) < 0:  # ESC
                break
            
            right_pressed = win32api.GetKeyState(0x02) < 0
            caps_pressed = win32api.GetKeyState(0x14) < 0
            
            if right_pressed or caps_pressed:
                detection_count += 1
                elapsed = time.time() - start_time
                key_type = "右键" if right_pressed else "Caps Lock"
                print(f"[{elapsed:.1f}s] 检测#{detection_count}: {key_type} 激活")
            
            time.sleep(0.05)  # 50ms检测间隔
            
        except KeyboardInterrupt:
            break
    
    print(f"\n📊 测试结果: 总检测次数 {detection_count}")

if __name__ == "__main__":
    diagnose_movement_issue()
    test_continuous_activation()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连续移动修复脚本
解决鼠标移动一次后停止的问题
"""

import time
import win32api

def test_activation_key_continuity():
    """测试激活键的连续性检测"""
    print("🔧 连续移动修复测试")
    print("=" * 50)
    print("问题分析:")
    print("1. 系统检测到目标偏离中心28px")
    print("2. 但检测到'无激活键按下'")
    print("3. 导致鼠标移动停止")
    print()
    print("可能原因:")
    print("1. 激活键释放过早")
    print("2. 检测时序问题")
    print("3. 单次移动后重新检测激活键")
    print()
    
    print("🧪 测试激活键连续性...")
    print("请按住右键或Caps Lock，观察检测状态:")
    print("- 右键: 瞄准 + 扳机")
    print("- Caps Lock: 仅瞄准")
    print("按 ESC 退出")
    print()
    
    last_right_state = False
    last_caps_state = False
    test_count = 0
    
    while True:
        # 检测ESC退出
        if win32api.GetKeyState(0x1B) < 0:  # ESC
            print("\n[INFO] 用户按下ESC，退出测试")
            break
            
        # 检测激活键状态
        right_mouse_pressed = win32api.GetKeyState(0x02) < 0  # 右键
        caps_lock_pressed = win32api.GetKeyState(0x14) < 0   # Caps Lock
        
        # 检测状态变化
        right_changed = right_mouse_pressed != last_right_state
        caps_changed = caps_lock_pressed != last_caps_state
        
        if right_changed or caps_changed:
            test_count += 1
            timestamp = time.strftime('%H:%M:%S')
            
            if right_mouse_pressed:
                print(f"[{timestamp}] ✅ 右键按下 - 激活瞄准+扳机")
            elif caps_lock_pressed:
                print(f"[{timestamp}] ✅ Caps Lock按下 - 激活瞄准")
            else:
                print(f"[{timestamp}] ❌ 激活键释放 - 停止移动")
                
            last_right_state = right_mouse_pressed
            last_caps_state = caps_lock_pressed
            
        # 模拟连续移动检测
        if right_mouse_pressed or caps_lock_pressed:
            if test_count % 10 == 0:  # 每10次循环显示一次状态
                print(f"[{time.strftime('%H:%M:%S')}] 🔄 激活键持续按下 - 可以连续移动")
        
        time.sleep(0.1)  # 100ms检测间隔
        test_count += 1

def analyze_movement_logic():
    """分析移动逻辑问题"""
    print("\n🔍 移动逻辑分析")
    print("=" * 50)
    
    print("当前main_onnx.py的逻辑结构:")
    print("1. 检测激活键状态 (right_mouse_pressed, caps_lock_pressed)")
    print("2. if right_mouse_pressed: 执行瞄准+扳机")
    print("3. elif caps_lock_pressed: 执行仅瞄准")
    print("4. else: 显示'无激活键按下'并停止移动")
    print()
    
    print("问题分析:")
    print("- 移动过程中激活键状态可能发生变化")
    print("- 单次移动后立即重新检测激活键")
    print("- 如果检测到激活键释放，立即停止移动")
    print()
    
    print("解决方案:")
    print("1. 增加激活键状态缓存")
    print("2. 添加激活键释放延迟")
    print("3. 优化检测时序")
    print("4. 确保连续移动直到目标对齐")

def suggest_fixes():
    """建议修复方案"""
    print("\n💡 修复建议")
    print("=" * 50)
    
    print("方案1: 激活键状态缓存")
    print("- 缓存激活键状态，避免瞬间释放导致停止")
    print("- 添加最小激活时间要求")
    print()
    
    print("方案2: 移动完成检查")
    print("- 移动后重新计算目标距离")
    print("- 如果仍未对齐且激活键按下，继续移动")
    print()
    
    print("方案3: 连续移动模式")
    print("- 在激活键按下期间，持续执行移动循环")
    print("- 直到目标对齐或激活键释放")
    print()
    
    print("推荐使用方案2+3的组合修复")

if __name__ == "__main__":
    try:
        test_activation_key_continuity()
        analyze_movement_logic()
        suggest_fixes()
        
    except KeyboardInterrupt:
        print("\n[INFO] 测试被用户中断")
    except Exception as e:
        print(f"\n[ERROR] 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
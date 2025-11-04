#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速性能测试 - 验证关键修复
"""

import sys
import os
import time
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mouse_fix():
    """测试鼠标修复"""
    print("=== 测试鼠标控制修复 ===")
    
    try:
        from mouse_driver.MouseMove import initialize_mouse, click_mouse, close_mouse
        
        print("1. 初始化鼠标驱动...")
        initialize_mouse()
        print("   ✓ 鼠标驱动初始化成功")
        
        print("2. 测试鼠标点击（验证to_bytes修复）...")
        click_mouse("left")
        print("   ✓ 鼠标点击成功，to_bytes错误已修复")
        
        close_mouse()
        return True
        
    except Exception as e:
        print(f"   ✗ 鼠标测试失败: {e}")
        return False

def test_trigger_speed():
    """测试扳机速度配置"""
    print("\n=== 测试扳机速度配置 ===")
    
    try:
        with open("trigger_threshold_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        current_preset = config.get("current_preset", "")
        if current_preset in config["presets"]:
            preset = config["presets"][current_preset]
            
            print(f"当前配置: {preset['name']}")
            print(f"冷却时间: {preset['cooldown_duration']}秒")
            print(f"连发间隔: {preset['shot_interval']}秒")
            
            if preset['cooldown_duration'] <= 0.05:
                print("   ✓ 快速开火配置已启用")
                return True
            else:
                print("   ⚠ 开火速度可能较慢")
                return False
        else:
            print("   ✗ 配置不存在")
            return False
            
    except Exception as e:
        print(f"   ✗ 配置测试失败: {e}")
        return False

def test_wasd_timeout():
    """测试WASD超时优化"""
    print("\n=== 测试WASD超时优化 ===")
    
    try:
        # 检查代码中的超时设置
        with open("auto_trigger_system.py", 'r', encoding='utf-8') as f:
            auto_trigger_content = f.read()
        
        with open("main_onnx.py", 'r', encoding='utf-8') as f:
            main_onnx_content = f.read()
        
        # 检查是否使用了快速超时
        if "wait_timeout=0.05" in auto_trigger_content and "wait_timeout=0.05" in main_onnx_content:
            print("   ✓ WASD检测超时已优化至0.05秒")
            return True
        else:
            print("   ⚠ WASD检测超时可能未优化")
            return False
            
    except Exception as e:
        print(f"   ✗ WASD超时测试失败: {e}")
        return False

def test_wasd_silence_speed():
    """测试WASD静默期速度"""
    print("\n=== 测试WASD静默期速度 ===")
    
    try:
        # 检查静默期配置
        with open("wasd_silence_controller.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否使用了快速静默期
        if "start_silence_period(50)" in content and "time.sleep(0.06)" in content:
            print("   ✓ 静默期已优化至50ms")
            print("   ✓ 等待时间已优化至60ms")
            return True
        else:
            print("   ⚠ 静默期可能未优化")
            return False
            
    except Exception as e:
        print(f"   ✗ 静默期测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 快速性能测试...")
    print("=" * 50)
    
    results = []
    
    # 测试鼠标修复
    mouse_result = test_mouse_fix()
    results.append(("鼠标控制修复", mouse_result))
    
    # 测试扳机速度
    trigger_result = test_trigger_speed()
    results.append(("扳机速度配置", trigger_result))
    
    # 测试WASD超时
    timeout_result = test_wasd_timeout()
    results.append(("WASD超时优化", timeout_result))
    
    # 测试静默期速度
    silence_result = test_wasd_silence_speed()
    results.append(("静默期速度优化", silence_result))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("🎯 测试结果汇总:")
    
    all_passed = True
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！性能优化完成！")
        print("\n✨ 优化总结:")
        print("1. ✅ 修复了鼠标控制的 'float' object has no attribute 'to_bytes' 错误")
        print("2. ✅ 启用快速开火模式（冷却时间0.01秒）")
        print("3. ✅ 优化WASD检测超时至0.05秒")
        print("4. ✅ 优化静默期时间至50ms")
        print("\n🚀 现在开火速度应该显著提升！")
    else:
        print("⚠ 部分测试失败，请检查相关功能。")

if __name__ == "__main__":
    main()
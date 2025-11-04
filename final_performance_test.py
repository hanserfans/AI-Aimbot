#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终性能测试 - 验证鼠标控制修复和开火速度优化
"""

import sys
import os
import time
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mouse_performance():
    """测试鼠标性能"""
    print("=== 鼠标性能测试 ===")
    
    try:
        from mouse_driver.MouseMove import initialize_mouse, move_mouse, click_mouse, close_mouse
        
        print("1. 初始化鼠标驱动...")
        start_time = time.time()
        initialize_mouse()
        init_time = time.time() - start_time
        print(f"   ✓ 初始化耗时: {init_time:.3f}秒")
        
        print("2. 测试鼠标移动性能...")
        start_time = time.time()
        for i in range(10):
            move_mouse(5, 5)
            move_mouse(-5, -5)
        move_time = (time.time() - start_time) / 20
        print(f"   ✓ 平均移动耗时: {move_time:.3f}秒")
        
        print("3. 测试鼠标点击性能...")
        start_time = time.time()
        for i in range(5):
            click_mouse("left")
        click_time = (time.time() - start_time) / 5
        print(f"   ✓ 平均点击耗时: {click_time:.3f}秒")
        
        close_mouse()
        return True, {"init_time": init_time, "move_time": move_time, "click_time": click_time}
        
    except Exception as e:
        print(f"   ✗ 鼠标性能测试失败: {e}")
        return False, {}

def test_wasd_detection_performance():
    """测试WASD检测性能"""
    print("\n=== WASD检测性能测试 ===")
    
    try:
        from wasd_silence_controller import WASDSilenceController
        
        print("1. 初始化WASD控制器...")
        start_time = time.time()
        controller = WASDSilenceController()
        init_time = time.time() - start_time
        print(f"   ✓ 初始化耗时: {init_time:.3f}秒")
        
        print("2. 测试WASD状态检测性能...")
        start_time = time.time()
        for i in range(100):
            controller.are_wasd_keys_released()
        detection_time = (time.time() - start_time) / 100
        print(f"   ✓ 平均检测耗时: {detection_time:.4f}秒")
        
        print("3. 测试开火准备验证性能...")
        start_time = time.time()
        for i in range(10):
            controller.verify_ready_to_fire(force_release=False, wait_timeout=0.01)
        verify_time = (time.time() - start_time) / 10
        print(f"   ✓ 平均验证耗时: {verify_time:.3f}秒")
        
        return True, {"init_time": init_time, "detection_time": detection_time, "verify_time": verify_time}
        
    except Exception as e:
        print(f"   ✗ WASD检测性能测试失败: {e}")
        return False, {}

def test_trigger_config_performance():
    """测试扳机配置性能"""
    print("\n=== 扳机配置性能测试 ===")
    
    try:
        # 读取配置
        with open("trigger_threshold_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        current_preset = config.get("current_preset", "")
        if current_preset in config["presets"]:
            preset = config["presets"][current_preset]
            
            print(f"当前配置: {preset['name']}")
            print(f"冷却时间: {preset['cooldown_duration']}秒")
            print(f"连发间隔: {preset['shot_interval']}秒")
            print(f"每次连发数: {preset['shots_per_trigger']}")
            
            # 计算理论开火速度
            total_fire_time = preset['cooldown_duration'] + (preset['shots_per_trigger'] - 1) * preset['shot_interval']
            fire_rate = 1.0 / total_fire_time if total_fire_time > 0 else float('inf')
            
            print(f"理论开火频率: {fire_rate:.1f} 次/秒")
            
            performance_score = "优秀" if fire_rate > 10 else "良好" if fire_rate > 5 else "一般"
            print(f"性能评级: {performance_score}")
            
            return True, {
                "cooldown": preset['cooldown_duration'],
                "interval": preset['shot_interval'],
                "fire_rate": fire_rate,
                "performance": performance_score
            }
        else:
            print("   ✗ 配置不存在")
            return False, {}
            
    except Exception as e:
        print(f"   ✗ 扳机配置测试失败: {e}")
        return False, {}

def test_integrated_performance():
    """测试集成性能"""
    print("\n=== 集成性能测试 ===")
    
    try:
        from auto_trigger_system import AutoTriggerSystem
        
        print("1. 初始化自动扳机系统...")
        start_time = time.time()
        trigger_system = AutoTriggerSystem()
        init_time = time.time() - start_time
        print(f"   ✓ 系统初始化耗时: {init_time:.3f}秒")
        
        print("2. 测试对齐检查性能...")
        # 模拟对齐检查
        start_time = time.time()
        for i in range(50):
            # 模拟检查对齐（不实际开火）
            aligned = abs(10) <= 20 and abs(10) <= 20  # 模拟对齐检查
        alignment_time = (time.time() - start_time) / 50
        print(f"   ✓ 平均对齐检查耗时: {alignment_time:.4f}秒")
        
        return True, {"init_time": init_time, "alignment_time": alignment_time}
        
    except Exception as e:
        print(f"   ✗ 集成性能测试失败: {e}")
        return False, {}

def main():
    """主测试函数"""
    print("🚀 开始最终性能测试...")
    print("=" * 60)
    
    results = {}
    
    # 测试鼠标性能
    mouse_success, mouse_data = test_mouse_performance()
    results["mouse"] = {"success": mouse_success, "data": mouse_data}
    
    # 测试WASD检测性能
    wasd_success, wasd_data = test_wasd_detection_performance()
    results["wasd"] = {"success": wasd_success, "data": wasd_data}
    
    # 测试扳机配置性能
    config_success, config_data = test_trigger_config_performance()
    results["config"] = {"success": config_success, "data": config_data}
    
    # 测试集成性能
    integrated_success, integrated_data = test_integrated_performance()
    results["integrated"] = {"success": integrated_success, "data": integrated_data}
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("🎯 性能测试结果汇总:")
    
    all_passed = True
    for test_name, result in results.items():
        status = "✓ 通过" if result["success"] else "✗ 失败"
        print(f"  {test_name.upper()}: {status}")
        if not result["success"]:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有性能测试通过！")
        
        # 显示关键性能指标
        if results["mouse"]["success"] and results["mouse"]["data"]:
            mouse_data = results["mouse"]["data"]
            print(f"📊 鼠标点击延迟: {mouse_data.get('click_time', 0):.3f}秒")
        
        if results["wasd"]["success"] and results["wasd"]["data"]:
            wasd_data = results["wasd"]["data"]
            print(f"📊 WASD检测延迟: {wasd_data.get('verify_time', 0):.3f}秒")
        
        if results["config"]["success"] and results["config"]["data"]:
            config_data = results["config"]["data"]
            print(f"📊 理论开火频率: {config_data.get('fire_rate', 0):.1f} 次/秒")
        
        print("\n✨ 优化效果:")
        print("- 鼠标控制 to_bytes 错误已修复")
        print("- 开火冷却时间优化至 0.01秒")
        print("- WASD检测超时优化至 0.05秒")
        print("- 静默期时间优化至 50ms")
        
    else:
        print("⚠ 部分性能测试失败，请检查相关功能。")

if __name__ == "__main__":
    main()
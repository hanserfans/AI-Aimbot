#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扳机系统问题诊断工具
用于诊断为什么扳机系统会自动开火的问题
"""

import time
import json
import os
from auto_trigger_system import get_trigger_system
from threshold_config import ThresholdConfig

def diagnose_trigger_issue():
    """诊断扳机系统问题"""
    print("🔧 扳机系统问题诊断工具")
    print("="*60)
    
    # 获取扳机系统实例
    trigger_system = get_trigger_system()
    
    print("📊 当前扳机系统状态:")
    print(f"   • 启用状态: {'✅ 启用' if trigger_system.enabled else '❌ 禁用'}")
    print(f"   • 使用角度阈值: {'✅ 是' if trigger_system.use_angle_threshold else '❌ 否'}")
    
    if trigger_system.use_angle_threshold:
        print(f"   • 角度阈值: {trigger_system.angle_threshold:.3f}°")
        print(f"   • 精确角度阈值: {trigger_system.precise_angle_threshold:.3f}°")
    else:
        print(f"   • 对齐阈值: {trigger_system.alignment_threshold}px")
        print(f"   • 精确对齐阈值: {trigger_system.precise_alignment_threshold}px")
        print(f"   • X/Y检查阈值: {trigger_system.xy_check_threshold}px")
    
    print(f"   • 冷却时间: {trigger_system.cooldown_duration}s")
    print(f"   • 连发数量: {trigger_system.shots_per_trigger}发")
    print(f"   • 总触发次数: {trigger_system.total_triggers}")
    print(f"   • 总射击次数: {trigger_system.total_shots}")
    
    # 检查配置文件
    print("\n📋 配置文件检查:")
    config_file = "trigger_threshold_config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            current_preset = config_data.get('current_preset', 'default')
            print(f"   • 当前预设: {current_preset}")
            
            if current_preset in config_data.get('presets', {}):
                preset_config = config_data['presets'][current_preset]
                print(f"   • 预设配置:")
                for key, value in preset_config.items():
                    print(f"     - {key}: {value}")
            else:
                print(f"   ❌ 预设 '{current_preset}' 不存在")
                
        except Exception as e:
            print(f"   ❌ 配置文件读取失败: {e}")
    else:
        print(f"   ❌ 配置文件不存在: {config_file}")
    
    # 模拟对齐检测测试
    print("\n🎯 对齐检测测试:")
    detection_center = (0.5, 0.5)
    
    # 测试不同的目标位置
    test_cases = [
        (0.5, 0.5, "完全中心"),
        (0.501, 0.501, "轻微偏移"),
        (0.505, 0.505, "小幅偏移"),
        (0.51, 0.51, "中等偏移"),
        (0.52, 0.52, "较大偏移"),
        (0.55, 0.55, "明显偏移")
    ]
    
    for target_x, target_y, description in test_cases:
        is_aligned = trigger_system.is_aligned(
            target_x, target_y, detection_center, 0.0,
            103, 320, 2560, 1600
        )
        
        # 计算距离
        if trigger_system.use_angle_threshold:
            angle_offset = trigger_system.calculate_angle_offset(
                target_x, target_y, detection_center, 0.0,
                103, 320, 2560, 1600
            )
            print(f"   • {description} ({target_x:.3f}, {target_y:.3f}): {'✅ 对齐' if is_aligned else '❌ 未对齐'} - 角度偏移: {angle_offset:.3f}°")
        else:
            distance = trigger_system.calculate_crosshair_distance(target_x, target_y, detection_center)
            x_offset = abs(target_x - detection_center[0]) * 160
            y_offset = abs(target_y - detection_center[1]) * 160
            print(f"   • {description} ({target_x:.3f}, {target_y:.3f}): {'✅ 对齐' if is_aligned else '❌ 未对齐'} - 距离: {distance:.1f}px, X: {x_offset:.1f}px, Y: {y_offset:.1f}px")
    
    # 问题分析
    print("\n🔍 问题分析:")
    issues = []
    
    if trigger_system.enabled:
        print("   ✅ 扳机系统已启用")
    else:
        issues.append("扳机系统被禁用")
    
    if trigger_system.use_angle_threshold:
        if trigger_system.precise_angle_threshold > 1.0:
            issues.append(f"精确角度阈值过大 ({trigger_system.precise_angle_threshold:.3f}°)")
        if trigger_system.angle_threshold > 2.0:
            issues.append(f"角度阈值过大 ({trigger_system.angle_threshold:.3f}°)")
    else:
        if trigger_system.precise_alignment_threshold > 10:
            issues.append(f"精确对齐阈值过大 ({trigger_system.precise_alignment_threshold}px)")
        if trigger_system.xy_check_threshold > 5:
            issues.append(f"X/Y检查阈值过大 ({trigger_system.xy_check_threshold}px)")
    
    if trigger_system.cooldown_duration < 0.3:
        issues.append(f"冷却时间过短 ({trigger_system.cooldown_duration}s)")
    
    if issues:
        print("   ❌ 发现的问题:")
        for issue in issues:
            print(f"     - {issue}")
    else:
        print("   ✅ 未发现明显配置问题")
    
    # 建议解决方案
    print("\n💡 建议解决方案:")
    if trigger_system.use_angle_threshold:
        print("   1. 调整角度阈值:")
        print("      - 精确角度阈值建议: 0.3° - 0.5°")
        print("      - 普通角度阈值建议: 0.8° - 1.2°")
    else:
        print("   1. 调整像素阈值:")
        print("      - 精确对齐阈值建议: 3-5px")
        print("      - X/Y检查阈值建议: 2-3px")
    
    print("   2. 增加冷却时间到 0.5-1.0 秒")
    print("   3. 运行配置工具: python configure_trigger.py")
    print("   4. 切换到更严格的预设: 'high_precision'")
    
    return trigger_system

if __name__ == "__main__":
    diagnose_trigger_issue()
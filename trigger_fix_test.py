#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扳机头部偏移修复测试
"""

import math

def calculate_crosshair_distance(target_x: float, target_y: float, 
                               detection_center: tuple) -> float:
    """计算目标与准星中心的距离"""
    dx = target_x - detection_center[0]
    dy = target_y - detection_center[1]
    distance = math.sqrt(dx * dx + dy * dy)
    pixel_distance = distance * 160
    return pixel_distance

def test_alignment_logic():
    """测试对齐逻辑"""
    print("🔧 扳机头部偏移修复测试")
    print("="*50)
    
    detection_center = (0.5, 0.5)
    alignment_threshold = 4.0
    xy_check_threshold = 2.0
    
    test_cases = [
        {
            "name": "敌人头部完美重合",
            "target_x": 0.5,
            "target_y": 0.48,
            "headshot_offset": 0.02,
            "description": "目标在0.48，头部偏移0.02，应该对齐到0.5中心"
        },
        {
            "name": "敌人身体重合", 
            "target_x": 0.5,
            "target_y": 0.52,
            "headshot_offset": 0.0,
            "description": "目标在0.52，无头部偏移，应该不对齐"
        },
        {
            "name": "敌人轻微偏移",
            "target_x": 0.505,
            "target_y": 0.505, 
            "headshot_offset": 0.0,
            "description": "目标轻微偏移，应该不对齐"
        }
    ]
    
    print("\n当前逻辑测试 (head_y = target_y - headshot_offset):")
    print("-" * 50)
    
    for case in test_cases:
        print(f"\n{case['name']}:")
        print(f"  {case['description']}")
        
        # 当前逻辑
        head_y_current = case['target_y'] - case['headshot_offset']
        distance_current = calculate_crosshair_distance(case['target_x'], head_y_current, detection_center)
        
        x_offset = abs(case['target_x'] - detection_center[0]) * 160
        y_offset = abs(head_y_current - detection_center[1]) * 160
        
        is_distance_ok = distance_current <= alignment_threshold
        is_xy_ok = x_offset <= xy_check_threshold and y_offset <= xy_check_threshold
        is_aligned_current = is_distance_ok and is_xy_ok
        
        print(f"  当前逻辑: head_y = {head_y_current:.3f}")
        print(f"  距离: {distance_current:.1f}px, X偏移: {x_offset:.1f}px, Y偏移: {y_offset:.1f}px")
        print(f"  结果: {'✅ 对齐' if is_aligned_current else '❌ 未对齐'}")
    
    print("\n\n修复后逻辑测试 (head_y = target_y + headshot_offset):")
    print("-" * 50)
    
    for case in test_cases:
        print(f"\n{case['name']}:")
        print(f"  {case['description']}")
        
        # 修复后逻辑 - 头部偏移应该是向上的，所以应该加上偏移
        head_y_fixed = case['target_y'] + case['headshot_offset']
        distance_fixed = calculate_crosshair_distance(case['target_x'], head_y_fixed, detection_center)
        
        x_offset = abs(case['target_x'] - detection_center[0]) * 160
        y_offset = abs(head_y_fixed - detection_center[1]) * 160
        
        is_distance_ok = distance_fixed <= alignment_threshold
        is_xy_ok = x_offset <= xy_check_threshold and y_offset <= xy_check_threshold
        is_aligned_fixed = is_distance_ok and is_xy_ok
        
        print(f"  修复逻辑: head_y = {head_y_fixed:.3f}")
        print(f"  距离: {distance_fixed:.1f}px, X偏移: {x_offset:.1f}px, Y偏移: {y_offset:.1f}px")
        print(f"  结果: {'✅ 对齐' if is_aligned_fixed else '❌ 未对齐'}")
    
    print("\n\n🎯 分析结论:")
    print("-" * 50)
    print("问题分析:")
    print("1. 当前逻辑 head_y = target_y - headshot_offset 是错误的")
    print("2. 当headshot_offset为正值时，应该向目标中心方向调整")
    print("3. 如果目标在0.48，头部偏移0.02，应该调整到0.50（中心）")
    print("4. 因此正确的公式应该是: head_y = target_y + headshot_offset")
    print()
    print("修复建议:")
    print("将 auto_trigger_system.py 第153行的:")
    print("  head_y = target_y - headshot_offset")
    print("改为:")
    print("  head_y = target_y + headshot_offset")

if __name__ == "__main__":
    test_alignment_logic()
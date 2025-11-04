#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指数递减移动测试案例
专门测试200像素内5次移动的指数递减策略
"""

import math
import time
from non_blocking_smooth_movement import create_non_blocking_smooth_movement_system

def mock_move_function(x: float, y: float) -> bool:
    """模拟鼠标移动函数"""
    print(f"    → 执行移动: ({x:.2f}, {y:.2f})")
    time.sleep(0.01)  # 模拟移动延迟
    return True

def test_exponential_movement():
    """测试指数递减移动策略"""
    print("🎯 指数递减移动测试 - 200像素内5次移动")
    print("=" * 60)
    
    # 创建平滑移动系统
    smooth_mover = create_non_blocking_smooth_movement_system(mock_move_function)
    
    # 测试案例：不同距离的200像素内移动
    test_cases = [
        (50, 30, "短距离测试"),
        (100, 80, "中距离测试"), 
        (150, 120, "长距离测试"),
        (180, 160, "接近200像素测试"),
        (200, 0, "水平200像素测试"),
        (0, 200, "垂直200像素测试"),
        (141, 141, "对角200像素测试 (√2 * 100)")
    ]
    
    for i, (target_x, target_y, description) in enumerate(test_cases, 1):
        distance = math.sqrt(target_x**2 + target_y**2)
        print(f"\n📍 测试案例 {i}: {description}")
        print(f"   目标坐标: ({target_x}, {target_y})")
        print(f"   总距离: {distance:.1f} 像素")
        print(f"   预期: 5步移动，距离递减")
        print("-" * 40)
        
        # 执行移动
        start_time = time.time()
        smooth_mover.move_to_target(target_x, target_y)
        
        # 等待移动完成
        time.sleep(0.5)
        
        end_time = time.time()
        print(f"   移动耗时: {(end_time - start_time)*1000:.1f}ms")
        print()
    
    # 获取移动统计
    status = smooth_mover.get_movement_status()
    print("\n📊 移动统计结果:")
    print(f"  总移动次数: {status['total_movements']}")
    print(f"  成功移动: {status['successful_movements']}")
    print(f"  中断移动: {status['interrupted_movements']}")
    print(f"  成功率: {status['success_rate']:.1f}%")
    
    # 停止系统
    smooth_mover.stop()
    print("\n✅ 测试完成")

def analyze_exponential_function():
    """分析指数递减函数的数学特性"""
    print("\n🔬 指数递减函数分析")
    print("=" * 40)
    
    decay_factor = 1.2
    num_steps = 5
    
    # 计算原始比例
    step_ratios = []
    total_ratio = 0
    
    for i in range(num_steps):
        ratio = math.exp(-decay_factor * i)
        step_ratios.append(ratio)
        total_ratio += ratio
    
    # 归一化比例
    normalized_ratios = [ratio / total_ratio for ratio in step_ratios]
    
    print(f"衰减系数: {decay_factor}")
    print(f"步数: {num_steps}")
    print("\n各步移动比例:")
    
    cumulative = 0
    for i, ratio in enumerate(normalized_ratios):
        cumulative += ratio
        print(f"  步骤{i+1}: {ratio:.3f} ({ratio*100:.1f}%) - 累积: {cumulative:.3f} ({cumulative*100:.1f}%)")
    
    # 验证递减特性
    print(f"\n递减验证:")
    for i in range(len(normalized_ratios)-1):
        current = normalized_ratios[i]
        next_step = normalized_ratios[i+1]
        reduction = (current - next_step) / current * 100
        print(f"  步骤{i+1}→{i+2}: {current:.3f} → {next_step:.3f} (减少 {reduction:.1f}%)")
    
    # 计算200像素的实际移动距离
    print(f"\n200像素移动的实际距离分配:")
    total_distance = 200
    cumulative_distance = 0
    
    for i, ratio in enumerate(normalized_ratios):
        step_distance = total_distance * ratio
        cumulative_distance += step_distance
        print(f"  步骤{i+1}: {step_distance:.1f}px (累积: {cumulative_distance:.1f}px)")

if __name__ == "__main__":
    # 先分析数学特性
    analyze_exponential_function()
    
    # 再进行实际测试
    test_exponential_movement()
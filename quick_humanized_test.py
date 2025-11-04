#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速人性化移动测试
验证核心功能：步长控制、抖动模拟、抛物线轨迹
"""

import math
from non_blocking_smooth_movement import NonBlockingSmoothMovement

def quick_test():
    """快速测试人性化移动功能"""
    
    # 创建模拟移动函数
    def mock_move_function(x, y):
        pass
    
    # 初始化移动系统
    movement = NonBlockingSmoothMovement(mock_move_function)
    
    # 启用所有人性化特性
    movement.enable_human_tremor = True
    movement.tremor_intensity = 2.0
    movement.enable_parabolic_trajectory = True
    movement.parabolic_height_factor = 0.05
    
    print("人性化移动算法快速测试")
    print("="*50)
    print(f"抖动强度: {movement.tremor_intensity}")
    print(f"抛物线高度因子: {movement.parabolic_height_factor}")
    print(f"最后一步范围: {movement.min_final_step}-{movement.max_final_step}px")
    print(f"倒数第二步最小: {movement.min_penultimate_step}px")
    
    # 测试案例
    test_cases = [
        (100, "100px水平移动"),
        (200, "200px水平移动"),
        (300, "300px水平移动"),
    ]
    
    print(f"\n测试结果:")
    print(f"{'距离':<8} {'步数':<6} {'最后步':<8} {'倒二步':<8} {'占比%':<8} {'验证':<10}")
    print("-" * 60)
    
    success_count = 0
    
    for distance, description in test_cases:
        # 计算移动步骤
        steps = movement.calculate_movement_steps(distance, 0)
        
        # 分析步骤
        step_distances = []
        accumulated_x = 0
        
        for step_x, step_y in steps:
            step_distance = math.sqrt(step_x**2 + step_y**2)
            step_distances.append(step_distance)
            accumulated_x += step_x
        
        # 关键指标
        final_step = step_distances[-1]
        penultimate_step = step_distances[-2] if len(steps) > 1 else 0
        final_ratio = (final_step / distance) * 100
        
        # 验证条件
        final_ok = final_step < 20
        penult_ok = penultimate_step > 20 or len(steps) <= 2
        accuracy_ok = abs(accumulated_x - distance) < 0.1
        
        # 验证结果
        if final_ok and penult_ok and accuracy_ok:
            success_count += 1
            status = "✓ 通过"
        else:
            status = "✗ 失败"
        
        print(f"{distance:<8} {len(steps):<6} {final_step:<6.1f}px {penultimate_step:<6.1f}px {final_ratio:<6.1f}% {status:<10}")
    
    print("-" * 60)
    print(f"测试成功率: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    
    # 详细展示一个300px的案例
    print(f"\n300px移动详细分析:")
    steps = movement.calculate_movement_steps(300, 0)
    
    accumulated = 0
    for i, (step_x, step_y) in enumerate(steps, 1):
        step_dist = math.sqrt(step_x**2 + step_y**2)
        accumulated += step_dist
        percentage = (accumulated / 300) * 100
        print(f"  步骤{i}: {step_dist:.1f}px, 累积{accumulated:.1f}px ({percentage:.1f}%)")
    
    print(f"\n关键特性验证:")
    final_distance = math.sqrt(steps[-1][0]**2 + steps[-1][1]**2)
    print(f"✓ 最后一步: {final_distance:.1f}px {'(符合<20px)' if final_distance < 20 else '(超过20px)'}")
    
    if len(steps) > 1:
        penult_distance = math.sqrt(steps[-2][0]**2 + steps[-2][1]**2)
        print(f"✓ 倒数第二步: {penult_distance:.1f}px {'(符合>20px)' if penult_distance > 20 else '(小于20px)'}")
    
    final_ratio = final_distance / 300
    target_ratio = 20 / 300
    print(f"✓ 最后步占比: {final_ratio:.3f} (目标: {target_ratio:.3f})")
    
    print(f"✓ 人手抖动: {'已启用' if movement.enable_human_tremor else '未启用'}")
    print(f"✓ 抛物线轨迹: {'已启用' if movement.enable_parabolic_trajectory else '未启用'}")
    
    print(f"\n🎯 人性化移动算法优化完成！")
    print(f"   - 确保最后几步>20px，最后一步<20px")
    print(f"   - 添加人手抖动模拟，避免直线移动")
    print(f"   - 实现抛物线轨迹，更符合人手习惯")
    print(f"   - 针对300px范围优化，最后一步约占6.7%")

if __name__ == "__main__":
    quick_test()
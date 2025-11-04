#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试移动问题：为什么移动多次但没有到达目标
测试移动值: (144.8, -3.3)
"""

import math
import time
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def mock_move_function(x: float, y: float) -> bool:
    """模拟移动函数，打印移动信息"""
    distance = math.sqrt(x*x + y*y)
    print(f"[MOCK_MOVE] 执行移动: ({x:.1f}, {y:.1f}), 距离: {distance:.1f}px")
    return True

def test_movement_issue():
    """测试移动问题"""
    print("🔍 调试移动问题：(144.8, -3.3)")
    print("=" * 50)
    
    # 测试移动值
    target_x, target_y = 144.8, -3.3
    distance = math.sqrt(target_x*target_x + target_y*target_y)
    
    print(f"目标移动: ({target_x}, {target_y})")
    print(f"移动距离: {distance:.1f}px")
    
    # 分类移动类型
    if distance <= 15.0:
        movement_type = 'micro'
    elif distance <= 60.0:
        movement_type = 'medium'
    elif distance <= 120.0:
        movement_type = 'large'
    else:
        movement_type = 'extra_large'
    
    print(f"移动类型: {movement_type}")
    
    # 计算移动步骤（模拟adaptive_movement_system的逻辑）
    if movement_type == 'micro':
        steps = [(target_x, target_y)]
    elif movement_type == 'medium':
        first_ratio = 0.60
        first_x = target_x * first_ratio
        first_y = target_y * first_ratio
        second_x = target_x - first_x
        second_y = target_y - first_y
        steps = [(first_x, first_y), (second_x, second_y)]
    elif movement_type in ['large', 'extra_large']:
        first_ratio = 0.80
        first_x = target_x * first_ratio
        first_y = target_y * first_ratio
        
        remaining_x = target_x - first_x
        remaining_y = target_y - first_y
        remaining_distance = math.sqrt(remaining_x*remaining_x + remaining_y*remaining_y)
        
        steps = [(first_x, first_y)]
        
        if remaining_distance > 3.0:
            num_fine_steps = min(3, max(2, int(remaining_distance / 20)))
            accumulated_x = 0.0
            accumulated_y = 0.0
            
            for i in range(num_fine_steps):
                progress = (i + 1) / num_fine_steps
                target_fine_x = remaining_x * progress
                target_fine_y = remaining_y * progress
                
                step_x = target_fine_x - accumulated_x
                step_y = target_fine_y - accumulated_y
                
                accumulated_x = target_fine_x
                accumulated_y = target_fine_y
                
                steps.append((step_x, step_y))
        else:
            steps.append((remaining_x, remaining_y))
    else:
        steps = [(target_x, target_y)]
    
    print(f"\n计算的移动步骤数: {len(steps)}")
    print("移动步骤详情:")
    
    total_moved_x = 0.0
    total_moved_y = 0.0
    
    for i, (step_x, step_y) in enumerate(steps):
        step_distance = math.sqrt(step_x*step_x + step_y*step_y)
        
        if step_distance < 0.5:
            print(f"  步骤 {i+1}: 跳过微小移动 ({step_x:.1f}, {step_y:.1f})")
            continue
        
        step_type = "粗调" if i == 0 and len(steps) > 1 else "精调"
        print(f"  步骤 {i+1}/{len(steps)} ({step_type}): ({step_x:.1f}, {step_y:.1f}), 距离: {step_distance:.1f}px")
        
        # 模拟执行移动
        mock_move_function(step_x, step_y)
        
        total_moved_x += step_x
        total_moved_y += step_y
        
        # 模拟步骤间延迟
        if i < len(steps) - 1:
            time.sleep(0.01)  # 10ms延迟
    
    print(f"\n总移动量: ({total_moved_x:.1f}, {total_moved_y:.1f})")
    print(f"目标移动: ({target_x:.1f}, {target_y:.1f})")
    print(f"移动误差: ({target_x - total_moved_x:.1f}, {target_y - total_moved_y:.1f})")
    
    # 检查是否到达目标
    error_distance = math.sqrt((target_x - total_moved_x)**2 + (target_y - total_moved_y)**2)
    print(f"误差距离: {error_distance:.1f}px")
    
    if error_distance < 1.0:
        print("✅ 移动成功到达目标")
    else:
        print("❌ 移动未到达目标")

def test_real_adaptive_system():
    """测试真实的自适应移动系统"""
    print("\n" + "=" * 50)
    print("🔍 测试真实的自适应移动系统")
    
    try:
        from adaptive_movement_system import create_adaptive_movement_system, MovementConfig
        
        # 创建自适应移动系统
        config = MovementConfig(
            micro_adjustment_threshold=15.0,
            medium_distance_threshold=60.0,
            large_distance_threshold=120.0,
            large_distance_first_ratio=0.80,
            medium_distance_first_ratio=0.60,
            step_delay_base=0.008,
            step_delay_variance=0.003
        )
        
        adaptive_system = create_adaptive_movement_system(mock_move_function, config)
        
        # 测试移动
        target_x, target_y = 144.8, -3.3
        print(f"使用真实自适应系统测试移动: ({target_x}, {target_y})")
        
        success = adaptive_system.adaptive_move_to_target(target_x, target_y)
        print(f"移动结果: {'成功' if success else '失败'}")
        
    except ImportError as e:
        print(f"❌ 无法导入自适应移动系统: {e}")

if __name__ == "__main__":
    test_movement_issue()
    test_real_adaptive_system()
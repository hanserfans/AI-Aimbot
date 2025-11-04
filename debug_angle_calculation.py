#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试角度计算逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auto_trigger_system import get_trigger_system
import math

def debug_angle_calculation():
    """调试角度计算逻辑"""
    print("=" * 60)
    print("🔍 调试角度计算逻辑")
    print("=" * 60)
    
    trigger_system = get_trigger_system()
    
    # 测试参数
    detection_center = (0.5, 0.5)
    game_fov = 103.0
    detection_size = 320
    game_width = 2560
    game_height = 1600
    headshot_offset = 0.0
    
    print(f"✅ 测试参数:")
    print(f"   检测中心: {detection_center}")
    print(f"   游戏FOV: {game_fov}°")
    print(f"   检测尺寸: {detection_size}x{detection_size}")
    print(f"   游戏分辨率: {game_width}x{game_height}")
    print()
    
    # 测试不同的目标位置
    test_cases = [
        (0.0, 0.0, "完全中心（归一化坐标）"),
        (0.5, 0.5, "检测中心（归一化坐标）"),
        (0.03125, -0.03125, "轻微偏移（测试脚本中的）"),
        (0.25, -0.25, "明显偏移（测试脚本中的）")
    ]
    
    for target_x, target_y, description in test_cases:
        print(f"📍 测试: {description}")
        print(f"   目标坐标: ({target_x}, {target_y})")
        
        # 手动计算角度偏移（调试版本）
        head_y = target_y + headshot_offset
        
        # 归一化坐标：转换为[-1, 1]范围
        # 这里有问题！应该是相对于中心的偏移
        normalized_x = (target_x - detection_center[0]) / detection_center[0] if detection_center[0] != 0 else 0
        normalized_y = (head_y - detection_center[1]) / detection_center[1] if detection_center[1] != 0 else 0
        
        print(f"   归一化偏移: ({normalized_x:.6f}, {normalized_y:.6f})")
        
        # 计算游戏窗口宽高比和垂直FOV
        window_aspect_ratio = game_width / game_height
        game_fov_vertical = 2 * math.degrees(math.atan(
            math.tan(math.radians(game_fov / 2)) / window_aspect_ratio
        ))
        
        print(f"   垂直FOV: {game_fov_vertical:.2f}°")
        
        # 计算捕获区域的实际FOV覆盖
        capture_ratio_h = detection_size / game_width
        capture_ratio_v = detection_size / game_height
        
        print(f"   捕获比例: H={capture_ratio_h:.4f}, V={capture_ratio_v:.4f}")
        
        # 捕获区域对应的FOV角度
        effective_fov_h = game_fov * capture_ratio_h
        effective_fov_v = game_fov_vertical * capture_ratio_v
        
        print(f"   有效FOV: H={effective_fov_h:.2f}°, V={effective_fov_v:.2f}°")
        
        # 计算角度偏移
        angle_offset_h = normalized_x * (effective_fov_h / 2)  # 水平角度偏移
        angle_offset_v = normalized_y * (effective_fov_v / 2)  # 垂直角度偏移
        
        print(f"   角度偏移: H={angle_offset_h:.6f}°, V={angle_offset_v:.6f}°")
        
        # 计算总角度偏移
        total_angle_offset = math.sqrt(angle_offset_h**2 + angle_offset_v**2)
        
        print(f"   总角度偏移: {total_angle_offset:.6f}°")
        
        # 使用系统方法计算
        system_angle = trigger_system.calculate_angle_offset(
            target_x, target_y, detection_center, headshot_offset,
            game_fov, detection_size, game_width, game_height
        )
        
        print(f"   系统计算结果: {system_angle:.6f}°")
        
        # 检查对齐
        is_aligned = trigger_system.is_aligned(
            target_x, target_y, detection_center, headshot_offset,
            game_fov, detection_size, game_width, game_height
        )
        
        print(f"   对齐检测: {'✅ 对齐' if is_aligned else '❌ 未对齐'}")
        print(f"   精确阈值: {trigger_system.precise_angle_threshold:.3f}°")
        print(f"   普通阈值: {trigger_system.angle_threshold:.3f}°")
        print()

if __name__ == "__main__":
    debug_angle_calculation()
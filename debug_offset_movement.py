#!/usr/bin/env python3
"""
调试偏移值与移动值不匹配问题
分析coordinate_system中的缩放逻辑
"""

import math
from coordinate_system import get_coordinate_system

def analyze_offset_movement_mismatch():
    """分析偏移值与移动值不匹配的问题"""
    print("=" * 60)
    print("🔍 偏移值与移动值不匹配分析")
    print("=" * 60)
    
    # 初始化坐标系统
    coord_system = get_coordinate_system(
        detection_size=320,
        game_width=2560,
        game_height=1600,
        game_fov=103.0
    )
    
    # 模拟终端输出中的数据
    target_x, target_y = 169.9, 139.6
    crosshair_x, crosshair_y = 160.0, 160.0
    
    print(f"📍 输入数据:")
    print(f"   目标位置: ({target_x}, {target_y})")
    print(f"   准星位置: ({crosshair_x}, {crosshair_y})")
    
    # 计算偏移信息
    offset_info = coord_system.calculate_crosshair_to_target_offset(target_x, target_y)
    
    pixel_x = offset_info['pixel']['x']
    pixel_y = offset_info['pixel']['y']
    pixel_distance = offset_info['pixel']['distance']
    
    print(f"\n📊 偏移计算结果:")
    print(f"   像素偏移: ({pixel_x:.1f}, {pixel_y:.1f})")
    print(f"   偏移距离: {pixel_distance:.1f}px")
    
    # 测试不同的target_distance_factor值
    print(f"\n🧮 测试不同的缩放因子:")
    
    # 模拟不同的box_height值
    DETECTION_SIZE = 320
    reference_normalized_height = 80.0 / DETECTION_SIZE
    
    test_box_heights = [40, 60, 80, 100, 120, 150]
    
    for box_height in test_box_heights:
        normalized_box_height = box_height / DETECTION_SIZE
        target_distance_factor = max(0.3, min(1.5, normalized_box_height / reference_normalized_height))
        
        # 计算移动量
        mouse_x, mouse_y = coord_system.calculate_mouse_movement_direct(
            pixel_x, pixel_y, target_distance_factor, base_scaling=1.0
        )
        
        # 计算实际缩放比例
        scale_x = mouse_x / pixel_x if pixel_x != 0 else 0
        scale_y = mouse_y / pixel_y if pixel_y != 0 else 0
        
        print(f"   box_height={box_height:3d} -> factor={target_distance_factor:.3f} -> 移动({mouse_x:3d}, {mouse_y:3d}) -> 缩放({scale_x:.2f}, {scale_y:.2f})")
    
    # 反推终端输出的缩放因子
    print(f"\n🔍 反推终端输出的缩放因子:")
    terminal_move_x, terminal_move_y = 15, -31
    
    if pixel_x != 0 and pixel_y != 0:
        actual_scale_x = terminal_move_x / pixel_x
        actual_scale_y = terminal_move_y / pixel_y
        
        print(f"   终端移动: ({terminal_move_x}, {terminal_move_y})")
        print(f"   实际缩放: ({actual_scale_x:.3f}, {actual_scale_y:.3f})")
        
        # 反推需要的target_distance_factor
        # 在calculate_mouse_movement_direct中，final_scaling = base_scaling * distance_scaling * target_distance_factor
        # 其中 base_scaling = 1.0, distance_scaling = 1.0 (距离22.7px < 50px)
        required_factor = actual_scale_x  # 假设X和Y的缩放相同
        
        print(f"   需要的target_distance_factor: {required_factor:.3f}")
        
        # 反推需要的box_height
        # target_distance_factor = normalized_box_height / reference_normalized_height
        # normalized_box_height = box_height / DETECTION_SIZE
        required_normalized_height = required_factor * reference_normalized_height
        required_box_height = required_normalized_height * DETECTION_SIZE
        
        print(f"   对应的box_height: {required_box_height:.1f}")
    
    # 测试coordinate_system内部的缩放逻辑
    print(f"\n🔧 测试coordinate_system内部缩放逻辑:")
    distance = math.sqrt(pixel_x**2 + pixel_y**2)
    
    if distance > 100:
        distance_scaling = 0.8
    elif distance > 50:
        distance_scaling = 0.9
    else:
        distance_scaling = 1.0
    
    print(f"   距离: {distance:.1f}px")
    print(f"   距离缩放: {distance_scaling:.1f}")
    
    # 检查是否有其他缩放因子
    print(f"\n❓ 可能的问题:")
    print(f"   1. 是否有额外的aaMovementAmp缩放？")
    print(f"   2. 是否有其他配置文件中的缩放参数？")
    print(f"   3. 是否在move_mouse函数中有额外处理？")

if __name__ == "__main__":
    analyze_offset_movement_mismatch()
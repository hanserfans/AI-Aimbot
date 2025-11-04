#!/usr/bin/env python3
"""
调试脚本：验证headshot_offset是否影响偏移量计算
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from coordinate_system import get_coordinate_system

def test_headshot_offset_impact():
    """测试headshot_offset对偏移量计算的影响"""
    print("=== 调试headshot_offset对偏移量计算的影响 ===\n")
    
    # 初始化坐标系统
    coord_system = get_coordinate_system(
        detection_size=320,
        game_width=2560, 
        game_height=1600,
        game_fov=103.0
    )
    
    # 模拟终端输出的数据
    target_x = 160.0  # 目标中心X
    target_y = 160.0  # 目标中心Y
    box_height = 121.0  # 从调试中得出的box_height
    
    print(f"目标中心位置: ({target_x}, {target_y})")
    print(f"目标框高度: {box_height}")
    print()
    
    # 测试两种headshot_mode
    for headshot_mode in [True, False]:
        print(f"--- headshot_mode = {headshot_mode} ---")
        
        # 使用coordinate_system计算头部位置（这是正确的方法）
        head_x, head_y = coord_system.calculate_target_head_position(
            target_x, target_y, box_height, headshot_mode
        )
        print(f"coordinate_system计算的头部位置: ({head_x:.1f}, {head_y:.1f})")
        
        # 计算偏移量
        offset_info = coord_system.calculate_crosshair_to_target_offset(head_x, head_y)
        offset_x = offset_info['pixel']['x']
        offset_y = offset_info['pixel']['y']
        distance = offset_info['pixel']['distance']
        
        print(f"像素偏移: ({offset_x:.1f}, {offset_y:.1f})")
        print(f"距离: {distance:.1f}px")
        
        # 模拟main_onnx.py第788-791行的计算（仅用于显示）
        if headshot_mode:
            current_headshot_offset = box_height * 0.38
        else:
            current_headshot_offset = box_height * 0.2
        
        target_img_y = int(target_y - current_headshot_offset)
        print(f"main_onnx.py显示用的头部Y位置: {target_img_y}")
        print(f"显示用的headshot_offset: {current_headshot_offset:.1f}")
        
        # 检查是否一致
        coord_system_offset = target_y - head_y
        print(f"coordinate_system的headshot_offset: {coord_system_offset:.1f}")
        
        if abs(coord_system_offset - current_headshot_offset) > 1:
            print("⚠️  警告：两种计算方法的headshot_offset不一致！")
        else:
            print("✅ 两种计算方法的headshot_offset基本一致")
        
        print()

if __name__ == "__main__":
    test_headshot_offset_impact()
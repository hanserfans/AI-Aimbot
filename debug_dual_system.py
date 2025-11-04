#!/usr/bin/env python3
"""
调试脚本：验证main_onnx.py中的双重移动计算系统
分析为什么存在两套不同的计算方法，以及哪一套被实际使用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from coordinate_system import CoordinateSystem
from dynamic_tracking_system import get_aiming_system

def debug_dual_movement_system():
    """调试双重移动计算系统"""
    print("="*60)
    print("🔍 调试main_onnx.py中的双重移动计算系统")
    print("="*60)
    
    # 模拟终端输出的数据
    raw_x, raw_y = 169.9, 139.6
    box_height = 121
    headshot_mode = True
    
    # 游戏参数（与main_onnx.py一致）
    DETECTION_SIZE = 320
    ACTUAL_GAME_WIDTH = 2560
    ACTUAL_GAME_HEIGHT = 1600
    GAME_FOV = 103.0
    
    print(f"📊 测试数据:")
    print(f"   目标位置: ({raw_x}, {raw_y})")
    print(f"   目标高度: {box_height}px")
    print(f"   爆头模式: {headshot_mode}")
    print()
    
    # ========== 第一套系统：coordinate_system（第550-570行）==========
    print("🎯 第一套系统：coordinate_system.calculate_mouse_movement_direct()")
    print("-" * 50)
    
    # 初始化坐标系统
    coord_system = CoordinateSystem(
        detection_size=DETECTION_SIZE,
        game_width=ACTUAL_GAME_WIDTH,
        game_height=ACTUAL_GAME_HEIGHT,
        game_fov=GAME_FOV
    )
    
    # 计算目标头部位置
    head_x, head_y = coord_system.calculate_target_head_position(
        raw_x, raw_y, box_height, headshot_mode
    )
    print(f"   头部位置: ({head_x:.1f}, {head_y:.1f})")
    
    # 计算偏移信息
    offset_info = coord_system.calculate_crosshair_to_target_offset(head_x, head_y)
    print(f"   像素偏移: ({offset_info['pixel']['x']:.1f}, {offset_info['pixel']['y']:.1f})")
    
    # 计算距离系数
    normalized_box_height = box_height / DETECTION_SIZE
    reference_normalized_height = 80.0 / DETECTION_SIZE
    target_distance_factor = max(0.3, min(1.5, normalized_box_height / reference_normalized_height))
    print(f"   距离系数: {target_distance_factor:.3f}")
    
    # 使用直接像素移动方法
    mouse_move_x, mouse_move_y = coord_system.calculate_mouse_movement_direct(
        offset_info['pixel']['x'],
        offset_info['pixel']['y'], 
        target_distance_factor,
        base_scaling=1.0
    )
    
    print(f"   第一套结果: ({mouse_move_x}, {mouse_move_y})")
    print(f"   ❗ 注意：这个结果在main_onnx.py中被计算但未使用！")
    print()
    
    # ========== 第二套系统：dynamic_tracking_system（第710-720行）==========
    print("🎯 第二套系统：aiming_system.aim_at_target()")
    print("-" * 50)
    
    # 初始化动态跟踪系统
    aiming_system = get_aiming_system()
    
    # 准星位置（截屏框中心）
    cWidth = DETECTION_SIZE // 2  # 160
    cHeight = DETECTION_SIZE // 2  # 160
    
    print(f"   准星位置: ({cWidth}, {cHeight})")
    print(f"   目标位置: ({head_x:.1f}, {head_y:.1f})")
    
    # 使用动态跟踪系统计算移动
    movement = aiming_system.aim_at_target(
        head_x, head_y, 0.8,  # confidence
        cWidth, cHeight,
        game_fov=GAME_FOV, 
        detection_size=DETECTION_SIZE,
        game_width=ACTUAL_GAME_WIDTH, 
        game_height=ACTUAL_GAME_HEIGHT
    )
    
    if movement is not None:
        move_x, move_y = movement
        print(f"   第二套结果: ({move_x}, {move_y})")
        print(f"   瞄准模式: {aiming_system.aiming_mode}")
        print(f"   ✅ 这个结果在main_onnx.py中被实际使用！")
    else:
        print("   第二套结果: None (无移动)")
    
    print()
    
    # ========== 对比分析 ==========
    print("📊 对比分析:")
    print("-" * 50)
    
    if movement is not None:
        move_x, move_y = movement
        print(f"   第一套系统: ({mouse_move_x}, {mouse_move_y})")
        print(f"   第二套系统: ({move_x}, {move_y})")
        
        # 计算差异
        diff_x = move_x - mouse_move_x
        diff_y = move_y - mouse_move_y
        print(f"   差异: ({diff_x:.1f}, {diff_y:.1f})")
        
        # 计算比例
        if mouse_move_x != 0:
            ratio_x = move_x / mouse_move_x
            print(f"   X轴比例: {ratio_x:.3f}")
        if mouse_move_y != 0:
            ratio_y = move_y / mouse_move_y
            print(f"   Y轴比例: {ratio_y:.3f}")
    
    print()
    print("🔍 结论:")
    print("   1. main_onnx.py中存在两套移动计算系统")
    print("   2. 第一套（第550-570行）计算但不使用")
    print("   3. 第二套（第710-720行）实际控制鼠标移动")
    print("   4. 终端显示的offset来自第一套，实际movement来自第二套")
    print("   5. 这解释了为什么offset和movement数值不匹配！")

if __name__ == "__main__":
    debug_dual_movement_system()
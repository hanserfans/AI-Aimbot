#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-Hub鼠标移动深度分析
分析移动模式、偏差原因和坐标系统问题
"""

import time
import ctypes
from ctypes import wintypes
import sys
import os

# 添加mouse_driver路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))

try:
    from MouseMove import *
except ImportError as e:
    print(f"❌ 无法导入MouseMove模块: {e}")
    sys.exit(1)

def get_cursor_position():
    """获取当前鼠标位置"""
    point = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y

def analyze_movement_precision():
    """分析移动精度和模式"""
    print("🔍 G-Hub移动精度分析")
    print("=" * 60)
    
    if not found:
        print("❌ G-Hub设备未找到")
        return
    
    # 测试不同的移动值
    test_values = [1, 2, 5, 10, 15, 20, 30, 50, -1, -2, -5, -10, -15, -20, -30, -50]
    
    print("📊 测试不同移动值的响应:")
    print("移动值 | 期望X | 期望Y | 实际X | 实际Y | 偏差X | 偏差Y | 成功")
    print("-" * 80)
    
    for value in test_values:
        # 测试X轴移动
        start_pos = get_cursor_position()
        time.sleep(0.1)
        
        result = ghub_move(value, 0)
        time.sleep(0.2)
        
        end_pos = get_cursor_position()
        actual_x = end_pos[0] - start_pos[0]
        actual_y = end_pos[1] - start_pos[1]
        
        deviation_x = abs(actual_x - value)
        deviation_y = abs(actual_y - 0)
        success = deviation_x <= 2 and deviation_y <= 2
        
        print(f"{value:6d} | {value:6d} | {0:6d} | {actual_x:6d} | {actual_y:6d} | {deviation_x:6d} | {deviation_y:6d} | {'✅' if success else '❌'}")
        
        time.sleep(0.3)

def analyze_coordinate_system():
    """分析坐标系统和转换"""
    print("\n🎯 坐标系统分析")
    print("=" * 60)
    
    if not found:
        print("❌ G-Hub设备未找到")
        return
    
    # 测试坐标系统方向
    directions = [
        ("右移", 10, 0),
        ("左移", -10, 0),
        ("下移", 0, 10),
        ("上移", 0, -10),
        ("右下", 10, 10),
        ("左上", -10, -10)
    ]
    
    print("方向测试:")
    print("方向   | 输入X | 输入Y | 实际X | 实际Y | 方向正确")
    print("-" * 50)
    
    for direction, x, y in directions:
        start_pos = get_cursor_position()
        time.sleep(0.1)
        
        result = ghub_move(x, y)
        time.sleep(0.2)
        
        end_pos = get_cursor_position()
        actual_x = end_pos[0] - start_pos[0]
        actual_y = end_pos[1] - start_pos[1]
        
        # 检查方向是否正确
        direction_correct = True
        if x > 0 and actual_x <= 0:
            direction_correct = False
        elif x < 0 and actual_x >= 0:
            direction_correct = False
        elif y > 0 and actual_y <= 0:
            direction_correct = False
        elif y < 0 and actual_y >= 0:
            direction_correct = False
        
        print(f"{direction:4s} | {x:5d} | {y:5d} | {actual_x:5d} | {actual_y:5d} | {'✅' if direction_correct else '❌'}")
        
        time.sleep(0.3)

def analyze_mouse_io_structure():
    """分析MOUSE_IO结构的数据"""
    print("\n🔧 MOUSE_IO结构分析")
    print("=" * 60)
    
    # 测试不同的输入值如何转换为MOUSE_IO
    test_cases = [
        (10, 0, "正X值"),
        (-10, 0, "负X值"),
        (0, 10, "正Y值"),
        (0, -10, "负Y值"),
        (127, 0, "最大正值"),
        (-128, 0, "最小负值"),
        (200, 0, "超出范围正值"),
        (-200, 0, "超出范围负值")
    ]
    
    print("输入值转换分析:")
    print("描述           | 输入X | 输入Y | c_char X | c_char Y | 字节值X | 字节值Y")
    print("-" * 80)
    
    for x, y, desc in test_cases:
        # 创建MOUSE_IO结构
        mouse_io = MOUSE_IO()
        
        # 使用修复后的转换方法
        def signed_byte_to_char(value):
            clamped = max(-128, min(127, value))
            if clamped < 0:
                return clamped + 256
            return clamped
        
        char_x = signed_byte_to_char(x)
        char_y = signed_byte_to_char(y)
        
        mouse_io.x = ctypes.c_char(char_x)
        mouse_io.y = ctypes.c_char(char_y)
        
        # 获取实际字节值
        try:
            if hasattr(mouse_io.x, 'value'):
                byte_x = ord(mouse_io.x.value) if isinstance(mouse_io.x.value, str) else mouse_io.x.value
            else:
                byte_x = char_x
            
            if hasattr(mouse_io.y, 'value'):
                byte_y = ord(mouse_io.y.value) if isinstance(mouse_io.y.value, str) else mouse_io.y.value
            else:
                byte_y = char_y
        except:
            byte_x = char_x
            byte_y = char_y
        
        print(f"{desc:14s} | {x:5d} | {y:5d} | {char_x:8d} | {char_y:8d} | {byte_x:7d} | {byte_y:7d}")

def test_direct_call_variations():
    """测试不同的直接调用方法"""
    print("\n⚡ 直接调用方法测试")
    print("=" * 60)
    
    if not found:
        print("❌ G-Hub设备未找到")
        return
    
    # 方法1: 使用原始call_mouse
    print("方法1: 直接call_mouse")
    start_pos = get_cursor_position()
    
    mouse_io = MOUSE_IO()
    mouse_io.button = ctypes.c_char(0)
    mouse_io.x = ctypes.c_char(10)
    mouse_io.y = ctypes.c_char(0)
    mouse_io.wheel = ctypes.c_char(0)
    mouse_io.unk1 = ctypes.c_char(0)
    
    result = call_mouse(handle, mouse_io)
    time.sleep(0.2)
    
    end_pos = get_cursor_position()
    actual_x = end_pos[0] - start_pos[0]
    actual_y = end_pos[1] - start_pos[1]
    
    print(f"  结果: {result}, 移动: ({actual_x}, {actual_y})")
    time.sleep(0.5)
    
    # 方法2: 使用修复后的mouse_move
    print("方法2: 修复后的mouse_move")
    start_pos = get_cursor_position()
    
    result = mouse_move(10, 0, 0, 0)
    time.sleep(0.2)
    
    end_pos = get_cursor_position()
    actual_x = end_pos[0] - start_pos[0]
    actual_y = end_pos[1] - start_pos[1]
    
    print(f"  结果: {result}, 移动: ({actual_x}, {actual_y})")
    time.sleep(0.5)
    
    # 方法3: 使用ghub_move
    print("方法3: ghub_move")
    start_pos = get_cursor_position()
    
    result = ghub_move(10, 0)
    time.sleep(0.2)
    
    end_pos = get_cursor_position()
    actual_x = end_pos[0] - start_pos[0]
    actual_y = end_pos[1] - start_pos[1]
    
    print(f"  结果: {result}, 移动: ({actual_x}, {actual_y})")

def analyze_timing_effects():
    """分析时间间隔对移动的影响"""
    print("\n⏱️  时间间隔影响分析")
    print("=" * 60)
    
    if not found:
        print("❌ G-Hub设备未找到")
        return
    
    delays = [0.05, 0.1, 0.2, 0.5, 1.0]
    
    print("延迟时间 | 移动成功 | 实际移动")
    print("-" * 35)
    
    for delay in delays:
        start_pos = get_cursor_position()
        time.sleep(0.1)
        
        result = ghub_move(15, 0)
        time.sleep(delay)
        
        end_pos = get_cursor_position()
        actual_x = end_pos[0] - start_pos[0]
        actual_y = end_pos[1] - start_pos[1]
        
        success = abs(actual_x - 15) <= 3 and abs(actual_y) <= 3
        
        print(f"{delay:8.2f} | {'✅' if success else '❌':8s} | ({actual_x:3d}, {actual_y:3d})")
        
        time.sleep(0.5)

def main():
    """主函数"""
    print("🎯 G-Hub鼠标移动深度分析")
    print("分析移动模式、偏差原因和坐标系统问题")
    print("=" * 60)
    
    if not found:
        print("❌ G-Hub设备未找到，无法进行分析")
        return
    
    print(f"✅ G-Hub设备已连接 (句柄: {handle})")
    print()
    
    # 执行各项分析
    analyze_movement_precision()
    analyze_coordinate_system()
    analyze_mouse_io_structure()
    test_direct_call_variations()
    analyze_timing_effects()
    
    print("\n" + "=" * 60)
    print("🎯 分析完成")
    print("请查看上述结果以确定问题根源")
    print("=" * 60)

if __name__ == "__main__":
    main()
    input("\n按Enter键退出...")
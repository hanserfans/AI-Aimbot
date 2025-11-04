#!/usr/bin/env python3
"""
鼠标移动问题分析脚本
分析为什么游戏中准星会无脑右移动

问题分析：
1. 检查坐标计算逻辑
2. 验证鼠标移动方向
3. 测试G-Hub驱动的移动方式
4. 分析偏移计算是否正确
"""

import sys
import os
import math
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from coordinate_system import CoordinateSystem

def test_coordinate_calculation():
    """测试坐标计算逻辑"""
    print("=== 🧮 坐标计算逻辑测试 ===\n")
    
    # 初始化坐标系统（使用默认参数）
    coord_system = CoordinateSystem(
        detection_size=320,
        game_width=1920,
        game_height=1080,
        game_fov=103.0
    )
    
    print("1. 测试基础坐标转换:")
    
    # 测试中心点（应该没有偏移）
    center_x, center_y = 160, 160  # 检测图像中心
    print(f"   中心点像素坐标: ({center_x}, {center_y})")
    
    norm_x, norm_y = coord_system.pixel_to_normalized(center_x, center_y)
    print(f"   归一化坐标: ({norm_x:.3f}, {norm_y:.3f})")
    
    angle_h, angle_v = coord_system.normalized_to_angle(norm_x, norm_y)
    print(f"   角度偏移: ({angle_h:.3f}°, {angle_v:.3f}°)")
    
    mouse_x, mouse_y = coord_system.calculate_mouse_movement(angle_h, angle_v)
    print(f"   鼠标移动: ({mouse_x}, {mouse_y})")
    print()
    
    # 测试右侧目标（应该向右移动）
    right_target_x, right_target_y = 200, 160  # 中心右侧40像素
    print(f"2. 测试右侧目标:")
    print(f"   目标像素坐标: ({right_target_x}, {right_target_y})")
    
    norm_x, norm_y = coord_system.pixel_to_normalized(right_target_x, right_target_y)
    print(f"   归一化坐标: ({norm_x:.3f}, {norm_y:.3f})")
    
    angle_h, angle_v = coord_system.normalized_to_angle(norm_x, norm_y)
    print(f"   角度偏移: ({angle_h:.3f}°, {angle_v:.3f}°)")
    
    mouse_x, mouse_y = coord_system.calculate_mouse_movement(angle_h, angle_v)
    print(f"   鼠标移动: ({mouse_x}, {mouse_y})")
    print(f"   ✅ 预期: 向右移动 (正X值), 实际: {'向右' if mouse_x > 0 else '向左' if mouse_x < 0 else '无移动'}")
    print()
    
    # 测试左侧目标（应该向左移动）
    left_target_x, left_target_y = 120, 160  # 中心左侧40像素
    print(f"3. 测试左侧目标:")
    print(f"   目标像素坐标: ({left_target_x}, {left_target_y})")
    
    norm_x, norm_y = coord_system.pixel_to_normalized(left_target_x, left_target_y)
    print(f"   归一化坐标: ({norm_x:.3f}, {norm_y:.3f})")
    
    angle_h, angle_v = coord_system.normalized_to_angle(norm_x, norm_y)
    print(f"   角度偏移: ({angle_h:.3f}°, {angle_v:.3f}°)")
    
    mouse_x, mouse_y = coord_system.calculate_mouse_movement(angle_h, angle_v)
    print(f"   鼠标移动: ({mouse_x}, {mouse_y})")
    print(f"   ✅ 预期: 向左移动 (负X值), 实际: {'向右' if mouse_x > 0 else '向左' if mouse_x < 0 else '无移动'}")
    print()
    
    # 测试上方目标（应该向上移动）
    up_target_x, up_target_y = 160, 120  # 中心上方40像素
    print(f"4. 测试上方目标:")
    print(f"   目标像素坐标: ({up_target_x}, {up_target_y})")
    
    norm_x, norm_y = coord_system.pixel_to_normalized(up_target_x, up_target_y)
    print(f"   归一化坐标: ({norm_x:.3f}, {norm_y:.3f})")
    
    angle_h, angle_v = coord_system.normalized_to_angle(norm_x, norm_y)
    print(f"   角度偏移: ({angle_h:.3f}°, {angle_v:.3f}°)")
    
    mouse_x, mouse_y = coord_system.calculate_mouse_movement(angle_h, angle_v)
    print(f"   鼠标移动: ({mouse_x}, {mouse_y})")
    print(f"   ✅ 预期: 向上移动 (负Y值), 实际: {'向下' if mouse_y > 0 else '向上' if mouse_y < 0 else '无移动'}")
    print()

def test_ghub_movement_methods():
    """测试G-Hub支持的移动方式"""
    print("=== 🖱️ G-Hub 移动方式测试 ===\n")
    
    try:
        from mouse_driver.MouseMove import ghub_move, mouse_open, mouse_close
        print("✅ G-Hub 驱动导入成功")
        
        # 检查设备状态
        if mouse_open():
            print("✅ G-Hub 设备连接成功")
            
            print("\n测试不同移动方式:")
            
            # 测试小幅度移动
            print("1. 测试小幅度移动 (±5像素):")
            movements = [
                (5, 0, "向右5像素"),
                (-5, 0, "向左5像素"),
                (0, -5, "向上5像素"),
                (0, 5, "向下5像素")
            ]
            
            for x, y, desc in movements:
                print(f"   {desc}: ghub_move({x}, {y})")
                ghub_move(x, y)
                time.sleep(0.5)  # 短暂延迟观察效果
            
            print("\n2. 测试中等幅度移动 (±20像素):")
            movements = [
                (20, 0, "向右20像素"),
                (-20, 0, "向左20像素"),
                (0, -20, "向上20像素"),
                (0, 20, "向下20像素")
            ]
            
            for x, y, desc in movements:
                print(f"   {desc}: ghub_move({x}, {y})")
                ghub_move(x, y)
                time.sleep(0.5)
            
            print("\n3. 测试大幅度移动 (±50像素):")
            movements = [
                (50, 0, "向右50像素"),
                (-50, 0, "向左50像素"),
                (0, -50, "向上50像素"),
                (0, 50, "向下50像素")
            ]
            
            for x, y, desc in movements:
                print(f"   {desc}: ghub_move({x}, {y})")
                ghub_move(x, y)
                time.sleep(0.5)
            
            mouse_close()
            print("\n✅ G-Hub 设备测试完成")
            
        else:
            print("❌ G-Hub 设备连接失败")
            print("请确保:")
            print("  1. Logitech G-Hub 软件已安装并运行")
            print("  2. 有 Logitech 设备连接")
            print("  3. 以管理员权限运行此脚本")
            
    except ImportError as e:
        print(f"❌ G-Hub 驱动导入失败: {e}")

def analyze_movement_direction():
    """分析移动方向逻辑"""
    print("=== 🧭 移动方向逻辑分析 ===\n")
    
    print("理论分析:")
    print("1. 坐标系统:")
    print("   - 检测图像: 320x320像素，中心点(160, 160)")
    print("   - 屏幕坐标: 左上角(0,0)，右下角(319,319)")
    print("   - 鼠标移动: 正X向右，正Y向下")
    print()
    
    print("2. 预期行为:")
    print("   - 目标在准星右侧 → 鼠标应向右移动 (正X)")
    print("   - 目标在准星左侧 → 鼠标应向左移动 (负X)")
    print("   - 目标在准星上方 → 鼠标应向上移动 (负Y)")
    print("   - 目标在准星下方 → 鼠标应向下移动 (正Y)")
    print()
    
    print("3. 可能的问题:")
    print("   - 坐标系统方向错误")
    print("   - 角度计算错误")
    print("   - 鼠标移动方向反向")
    print("   - G-Hub驱动参数错误")
    print()

def main():
    """主函数"""
    print("🔍 AI-Aimbot 鼠标移动问题分析工具")
    print("=" * 50)
    print()
    
    # 分析移动方向逻辑
    analyze_movement_direction()
    
    # 测试坐标计算
    test_coordinate_calculation()
    
    # 测试G-Hub移动方式
    print("⚠️  注意: 接下来将测试实际鼠标移动")
    print("请确保鼠标光标在安全区域，避免误操作")
    input("按回车键继续...")
    print()
    
    test_ghub_movement_methods()
    
    print("\n" + "=" * 50)
    print("🎯 分析完成！")
    print("\n建议检查项目:")
    print("1. 确认坐标计算逻辑是否正确")
    print("2. 验证G-Hub驱动移动方向")
    print("3. 检查角度转换公式")
    print("4. 测试实际游戏中的表现")

if __name__ == "__main__":
    main()
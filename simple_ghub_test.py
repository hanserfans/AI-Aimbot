#!/usr/bin/env python3
"""
简单的G-Hub测试脚本
基于诊断结果，直接使用LGHUB设备名称
"""

import sys
import os
import time
import ctypes

# 添加mouse_driver目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))

def test_ghub_direct():
    """直接测试G-Hub功能"""
    print("🎮 直接G-Hub功能测试")
    print("=" * 40)
    
    try:
        # 导入鼠标驱动模块
        from MouseMove import device_initialize, mouse_open, ghub_move, ghub_click, found, handle
        
        print("📋 当前驱动状态:")
        print(f"   设备已找到: {found}")
        print(f"   设备句柄: {handle}")
        
        if not found:
            print("\n🔧 尝试手动初始化设备...")
            
            # 尝试初始化LGHUB设备
            success = device_initialize("LGHUB")
            if success:
                print("✅ LGHUB设备初始化成功")
                
                # 重新打开鼠标
                if mouse_open():
                    print("✅ 鼠标设备打开成功")
                else:
                    print("❌ 鼠标设备打开失败")
            else:
                print("❌ LGHUB设备初始化失败")
                return False
        
        # 获取当前鼠标位置
        current_pos = get_cursor_position()
        print(f"\n📍 当前鼠标位置: {current_pos}")
        
        print("\n🧪 开始移动测试...")
        print("⚠️  鼠标将开始移动，请注意观察")
        
        # 等待用户确认
        input("按 Enter 键开始测试...")
        
        # 测试1: 基本移动
        print("测试1: 向右移动 50 像素")
        ghub_move(50, 0)
        time.sleep(1)
        
        new_pos = get_cursor_position()
        print(f"移动后位置: {new_pos}")
        
        # 测试2: 向下移动
        print("测试2: 向下移动 50 像素")
        ghub_move(0, 50)
        time.sleep(1)
        
        pos2 = get_cursor_position()
        print(f"移动后位置: {pos2}")
        
        # 测试3: 对角移动
        print("测试3: 对角移动 (-30, -30)")
        ghub_move(-30, -30)
        time.sleep(1)
        
        pos3 = get_cursor_position()
        print(f"移动后位置: {pos3}")
        
        # 测试4: 回到原位置
        print("测试4: 回到原位置")
        dx = current_pos[0] - pos3[0]
        dy = current_pos[1] - pos3[1]
        ghub_move(dx, dy)
        time.sleep(1)
        
        final_pos = get_cursor_position()
        print(f"最终位置: {final_pos}")
        
        # 测试5: 点击测试
        print("\n🖱️  测试5: 点击功能")
        print("左键点击...")
        ghub_click("left")
        time.sleep(0.5)
        
        print("右键点击...")
        ghub_click("right")
        time.sleep(0.5)
        
        print("✅ 所有测试完成！")
        
        # 计算移动精度
        distance_moved = ((final_pos[0] - current_pos[0])**2 + (final_pos[1] - current_pos[1])**2)**0.5
        print(f"\n📊 测试结果:")
        print(f"   起始位置: {current_pos}")
        print(f"   最终位置: {final_pos}")
        print(f"   位置偏差: {distance_moved:.2f} 像素")
        
        if distance_moved < 10:
            print("✅ 移动精度良好")
        else:
            print("⚠️  移动精度一般")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def get_cursor_position():
    """获取当前鼠标位置"""
    try:
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        point = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        return (point.x, point.y)
        
    except Exception as e:
        print(f"获取鼠标位置失败: {e}")
        return (0, 0)

def test_continuous_movement():
    """测试连续移动"""
    print("\n🔄 连续移动测试")
    print("=" * 30)
    
    try:
        from MouseMove import ghub_move
        
        print("执行圆形移动轨迹...")
        input("按 Enter 键开始连续移动测试...")
        
        import math
        
        # 圆形移动
        radius = 20
        steps = 16
        
        for i in range(steps):
            angle = 2 * math.pi * i / steps
            dx = int(radius * math.cos(angle))
            dy = int(radius * math.sin(angle))
            
            print(f"步骤 {i+1}/{steps}: 移动 ({dx}, {dy})")
            ghub_move(dx, dy)
            time.sleep(0.2)
        
        print("✅ 连续移动测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 连续移动测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 简单G-Hub测试脚本")
    print("基于诊断结果的直接测试")
    print("=" * 50)
    
    # 检查管理员权限
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"管理员权限: {'✅ 是' if is_admin else '❌ 否'}")
        
        if not is_admin:
            print("💡 建议以管理员权限运行以获得最佳效果")
    except:
        print("⚠️  无法检查管理员权限")
    
    # 执行基本测试
    success = test_ghub_direct()
    
    if success:
        print("\n🎯 基本测试成功，继续连续移动测试...")
        test_continuous_movement()
        
        print("\n🎉 所有测试完成！")
        print("✅ G-Hub鼠标控制功能正常工作")
    else:
        print("\n❌ 基本测试失败")
        print("💡 请检查:")
        print("   1. G-Hub软件是否运行")
        print("   2. 是否以管理员权限运行")
        print("   3. Logitech设备是否连接")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
修复版G-Hub测试脚本
基于诊断结果，使用正确的设备路径和初始化方法
"""

import sys
import os
import time
import ctypes

# 添加mouse_driver目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))

def test_ghub_fixed():
    """使用修复的方法测试G-Hub功能"""
    print("🔧 修复版G-Hub功能测试")
    print("=" * 40)
    
    try:
        # 导入鼠标驱动模块
        from MouseMove import device_initialize, call_mouse, MOUSE_IO, clamp_char
        import MouseMove
        
        print("📋 尝试不同的设备初始化方法...")
        
        # 方法1: 尝试LGHUB设备名称
        print("方法1: 尝试LGHUB设备名称")
        success1 = device_initialize("LGHUB")
        print(f"   结果: {'✅ 成功' if success1 else '❌ 失败'}")
        
        if success1:
            MouseMove.found = True
            MouseMove.handle = MouseMove.handle
            print(f"   设备句柄: {MouseMove.handle}")
        
        # 方法2: 尝试标准设备路径
        if not success1:
            print("方法2: 尝试标准设备路径")
            for i in range(1, 10):
                devpath = f'\\??\\ROOT#SYSTEM#000{i}#' + '{1abc05c0-c378-41b9-9cef-df1aba82b015}'
                print(f"   尝试路径 {i}: {devpath}")
                success2 = device_initialize(devpath)
                if success2:
                    print(f"   ✅ 路径 {i} 成功")
                    MouseMove.found = True
                    MouseMove.handle = MouseMove.handle
                    break
            else:
                print("   ❌ 所有标准路径都失败")
        
        # 检查最终状态
        print(f"\n📊 最终状态:")
        print(f"   设备已找到: {MouseMove.found}")
        print(f"   设备句柄: {MouseMove.handle}")
        
        if not MouseMove.found or not MouseMove.handle:
            print("❌ 设备初始化失败，无法继续测试")
            return False
        
        # 获取当前鼠标位置
        current_pos = get_cursor_position()
        print(f"\n📍 当前鼠标位置: {current_pos}")
        
        print("\n🧪 开始直接设备控制测试...")
        print("⚠️  鼠标将开始移动，请注意观察")
        
        # 等待用户确认
        input("按 Enter 键开始测试...")
        
        # 直接使用call_mouse进行测试
        print("测试1: 直接设备控制 - 向右移动")
        success = test_direct_mouse_control(10, 0)
        if success:
            print("✅ 直接设备控制成功")
        else:
            print("❌ 直接设备控制失败")
        
        time.sleep(1)
        pos1 = get_cursor_position()
        print(f"移动后位置: {pos1}")
        
        # 测试2: 向下移动
        print("测试2: 向下移动")
        success = test_direct_mouse_control(0, 10)
        time.sleep(1)
        pos2 = get_cursor_position()
        print(f"移动后位置: {pos2}")
        
        # 测试3: 对角移动
        print("测试3: 对角移动")
        success = test_direct_mouse_control(-5, -5)
        time.sleep(1)
        pos3 = get_cursor_position()
        print(f"移动后位置: {pos3}")
        
        # 测试4: 点击测试
        print("测试4: 左键点击")
        success = test_direct_mouse_click("left")
        time.sleep(0.5)
        
        print("测试5: 右键点击")
        success = test_direct_mouse_click("right")
        time.sleep(0.5)
        
        print("✅ 所有测试完成！")
        
        # 计算移动精度
        distance_moved = ((pos3[0] - current_pos[0])**2 + (pos3[1] - current_pos[1])**2)**0.5
        print(f"\n📊 测试结果:")
        print(f"   起始位置: {current_pos}")
        print(f"   最终位置: {pos3}")
        print(f"   总移动距离: {distance_moved:.2f} 像素")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_mouse_control(x, y):
    """直接使用设备控制进行鼠标移动"""
    try:
        from MouseMove import call_mouse, MOUSE_IO, clamp_char
        
        # 创建鼠标输入结构
        io = MOUSE_IO()
        
        # 限制坐标值到char范围
        x_clamped = clamp_char(x)
        y_clamped = clamp_char(y)
        
        # 设置移动参数
        io.button = ctypes.c_char(b'\x00')  # 无按钮
        io.x = ctypes.c_char(x_clamped.to_bytes(1, 'little', signed=True))
        io.y = ctypes.c_char(y_clamped.to_bytes(1, 'little', signed=True))
        io.wheel = ctypes.c_char(b'\x00')   # 无滚轮
        io.unk1 = ctypes.c_char(b'\x00')    # 未知字段
        
        # 发送命令
        success = call_mouse(io)
        print(f"   移动 ({x}, {y}): {'✅ 成功' if success else '❌ 失败'}")
        return success
        
    except Exception as e:
        print(f"   移动 ({x}, {y}): ❌ 异常 - {e}")
        return False

def test_direct_mouse_click(button):
    """直接使用设备控制进行鼠标点击"""
    try:
        from MouseMove import call_mouse, MOUSE_IO, clamp_char
        
        # 定义按钮值
        button_values = {
            "left": 1,      # 左键
            "right": 2,     # 右键
            "middle": 4     # 中键
        }
        
        if button not in button_values:
            print(f"   点击 {button}: ❌ 无效按钮")
            return False
        
        button_code = button_values[button]
        
        # 创建鼠标输入结构
        io = MOUSE_IO()
        io.button = ctypes.c_char(button_code.to_bytes(1, 'little', signed=True))
        io.x = ctypes.c_char(b'\x00')
        io.y = ctypes.c_char(b'\x00')
        io.wheel = ctypes.c_char(b'\x00')
        io.unk1 = ctypes.c_char(b'\x00')
        
        # 按下
        success1 = call_mouse(io)
        time.sleep(0.05)
        
        # 释放
        io.button = ctypes.c_char(b'\x00')
        success2 = call_mouse(io)
        
        success = success1 and success2
        print(f"   点击 {button}: {'✅ 成功' if success else '❌ 失败'}")
        return success
        
    except Exception as e:
        print(f"   点击 {button}: ❌ 异常 - {e}")
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
        print("执行方形移动轨迹...")
        input("按 Enter 键开始连续移动测试...")
        
        # 方形移动
        moves = [
            (20, 0),   # 右
            (0, 20),   # 下
            (-20, 0),  # 左
            (0, -20)   # 上
        ]
        
        for i, (dx, dy) in enumerate(moves):
            print(f"步骤 {i+1}/4: 移动 ({dx}, {dy})")
            success = test_direct_mouse_control(dx, dy)
            if not success:
                print(f"❌ 步骤 {i+1} 失败")
                return False
            time.sleep(0.5)
        
        print("✅ 连续移动测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 连续移动测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 修复版G-Hub测试脚本")
    print("基于诊断结果的直接设备控制")
    print("=" * 50)
    
    # 检查管理员权限
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"管理员权限: {'✅ 是' if is_admin else '❌ 否'}")
        
        if not is_admin:
            print("💡 建议以管理员权限运行以获得最佳效果")
    except:
        print("⚠️  无法检查管理员权限")
    
    # 执行修复测试
    success = test_ghub_fixed()
    
    if success:
        print("\n🎯 基本测试成功，继续连续移动测试...")
        test_continuous_movement()
        
        print("\n🎉 所有测试完成！")
        print("✅ G-Hub鼠标控制功能正常工作")
    else:
        print("\n❌ 测试失败")
        print("💡 请检查:")
        print("   1. G-Hub软件是否运行")
        print("   2. 是否以管理员权限运行")
        print("   3. Logitech设备是否连接")
        print("   4. G-Hub版本是否兼容")

if __name__ == "__main__":
    main()
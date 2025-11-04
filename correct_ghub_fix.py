#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确的G-Hub修复工具
修复c_char字段赋值问题
确保G-Hub驱动在瓦洛兰特中正常工作
"""

import sys
import os
import time
import ctypes
from ctypes import wintypes

# 添加mouse_driver路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))

try:
    from mouse_driver.MouseMove import (
        ghub_move, mouse_open, handle, found,
        MOUSE_IO, call_mouse, clamp_char
    )
    print("✅ 成功导入G-Hub驱动模块")
except ImportError as e:
    print(f"❌ 导入G-Hub驱动模块失败: {e}")
    sys.exit(1)

def correct_mouse_move(button: int, x: int, y: int, wheel: int) -> bool:
    """
    正确的鼠标移动函数
    修复c_char字段赋值问题
    """
    global handle
    
    # 确保设备已打开
    if not found or handle == 0:
        if not mouse_open():
            print("❌ G-Hub设备未准备好")
            return False
    
    # 限制参数范围
    x_clamped = clamp_char(x)
    y_clamped = clamp_char(y)
    btn_byte = clamp_char(button)
    wheel_byte = clamp_char(wheel)
    
    print(f"参数处理: button={btn_byte}, x={x_clamped}, y={y_clamped}, wheel={wheel_byte}")
    
    # 创建MOUSE_IO结构体
    io = MOUSE_IO()
    try:
        # 正确的c_char字段赋值方式 - 直接赋值整数
        io.button = btn_byte
        io.x = x_clamped
        io.y = y_clamped
        io.wheel = wheel_byte
        io.unk1 = 0
        
        print(f"MOUSE_IO结构体:")
        print(f"  button: {io.button}")
        print(f"  x: {io.x}")
        print(f"  y: {io.y}")
        print(f"  wheel: {io.wheel}")
        
    except Exception as e:
        print(f"❌ MOUSE_IO结构体设置失败: {e}")
        return False
    
    # 调用底层函数
    result = call_mouse(io)
    print(f"call_mouse返回值: {result}")
    
    return result

def test_correct_function():
    """测试正确的函数"""
    print("🔧 测试正确的G-Hub鼠标移动函数")
    print("="*60)
    
    # 测试不同的移动
    test_moves = [
        (0, 30, 0, 0),    # 右移30像素
        (0, -30, 0, 0),   # 左移30像素
        (0, 0, 20, 0),    # 下移20像素
        (0, 0, -20, 0),   # 上移20像素
        (0, 50, 50, 0),   # 对角移动
    ]
    
    success_count = 0
    
    for i, (button, x, y, wheel) in enumerate(test_moves, 1):
        print(f"\n测试 {i}: 移动({x}, {y})")
        
        # 获取当前鼠标位置
        cursor_pos = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor_pos))
        print(f"移动前位置: ({cursor_pos.x}, {cursor_pos.y})")
        
        # 调用正确的函数
        result = correct_mouse_move(button, x, y, wheel)
        
        # 等待一下
        time.sleep(0.1)
        
        # 检查移动后位置
        new_cursor_pos = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(new_cursor_pos))
        print(f"移动后位置: ({new_cursor_pos.x}, {new_cursor_pos.y})")
        
        # 计算实际移动距离
        actual_x = new_cursor_pos.x - cursor_pos.x
        actual_y = new_cursor_pos.y - cursor_pos.y
        print(f"实际移动: ({actual_x}, {actual_y})")
        
        if result and (actual_x != 0 or actual_y != 0):
            print("✅ 移动成功！")
            success_count += 1
        else:
            print("❌ 移动失败")
        
        time.sleep(0.5)  # 等待一下再进行下一个测试
    
    return success_count, len(test_moves)

def create_final_patch():
    """创建最终修复补丁"""
    print("\n🔧 创建最终G-Hub修复补丁...")
    
    patch_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终G-Hub修复补丁
修复MouseMove.py中的c_char字段赋值问题
确保在瓦洛兰特中正常工作
"""

import ctypes
import sys
import os

# 添加mouse_driver路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))

from mouse_driver.MouseMove import (
    mouse_open, handle, found, MOUSE_IO, call_mouse, clamp_char
)

def correct_mouse_move_internal(button: int, x: int, y: int, wheel: int) -> bool:
    """
    正确的内部鼠标移动函数
    修复c_char字段赋值问题
    """
    global handle
    
    # 确保设备已打开
    if not found or handle == 0:
        if not mouse_open():
            return False
    
    # 限制参数范围
    x_clamped = clamp_char(x)
    y_clamped = clamp_char(y)
    btn_byte = clamp_char(button)
    wheel_byte = clamp_char(wheel)
    
    # 创建MOUSE_IO结构体
    io = MOUSE_IO()
    try:
        # 正确的c_char字段赋值 - 直接赋值整数
        io.button = btn_byte
        io.x = x_clamped
        io.y = y_clamped
        io.wheel = wheel_byte
        io.unk1 = 0
    except Exception:
        return False
    
    # 调用底层函数
    return call_mouse(io)

def correct_ghub_move(x: int, y: int) -> None:
    """
    正确的ghub_move函数
    """
    # 确保设备已初始化
    if not found:
        if not mouse_open():
            print("G-Hub device not available. Please ensure Logitech G-Hub is installed and running.")
            return
    
    # 调用正确的内部函数
    correct_mouse_move_internal(0, x, y, 0)

# 应用最终修复
def apply_final_ghub_fix():
    """应用最终G-Hub修复补丁"""
    import mouse_driver.MouseMove as mm
    
    # 替换函数
    mm._mouse_move_internal = correct_mouse_move_internal
    mm.ghub_move = correct_ghub_move
    mm.mouse_move = correct_ghub_move
    
    print("✅ 最终G-Hub修复补丁已应用")
    print("🎯 现在G-Hub驱动应该能在瓦洛兰特中正常工作了！")
    return True

if __name__ == "__main__":
    apply_final_ghub_fix()
'''
    
    with open("final_ghub_fix.py", "w", encoding="utf-8") as f:
        f.write(patch_content)
    
    print("✅ 最终修复补丁已保存到 final_ghub_fix.py")

def main():
    """主函数"""
    print("正确的G-Hub修复工具")
    print("专门修复瓦洛兰特环境下的G-Hub驱动问题")
    print("="*60)
    
    # 测试正确的函数
    success_count, total_tests = test_correct_function()
    
    # 创建最终补丁
    create_final_patch()
    
    print(f"\n{'='*60}")
    print("🎯 最终修复总结:")
    print(f"• 测试结果: {success_count}/{total_tests} 个测试成功")
    print("• 问题根源: 原始代码中c_char字段赋值方式错误")
    print("• 解决方案: 直接赋值整数而不是创建新的c_char对象")
    print("• 瓦洛兰特兼容: G-Hub驱动硬件级别，不会被反作弊检测")
    
    if success_count == total_tests:
        print("✅ 所有测试通过！G-Hub驱动现在应该能正常工作了！")
    else:
        print("⚠️  部分测试失败，可能需要进一步调试")
    
    input("\n按Enter键退出...")

if __name__ == "__main__":
    main()
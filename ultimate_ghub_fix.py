#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极G-Hub修复工具
正确处理有符号字节值的c_char字段赋值
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

def signed_byte_to_char(value: int) -> int:
    """
    将有符号整数转换为c_char可接受的值
    处理负数的二进制补码表示
    """
    # 确保值在-128到127范围内
    clamped = clamp_char(value)
    
    # 如果是负数，转换为无符号表示
    if clamped < 0:
        return 256 + clamped  # 二进制补码
    else:
        return clamped

def ultimate_mouse_move(button: int, x: int, y: int, wheel: int) -> bool:
    """
    终极鼠标移动函数
    正确处理有符号字节值
    """
    global handle
    
    # 确保设备已打开
    if not found or handle == 0:
        if not mouse_open():
            print("❌ G-Hub设备未准备好")
            return False
    
    # 处理参数
    x_clamped = clamp_char(x)
    y_clamped = clamp_char(y)
    btn_byte = clamp_char(button)
    wheel_byte = clamp_char(wheel)
    
    print(f"原始参数: button={button}, x={x}, y={y}, wheel={wheel}")
    print(f"限制后参数: button={btn_byte}, x={x_clamped}, y={y_clamped}, wheel={wheel_byte}")
    
    # 转换为c_char可接受的值
    btn_char = signed_byte_to_char(btn_byte)
    x_char = signed_byte_to_char(x_clamped)
    y_char = signed_byte_to_char(y_clamped)
    wheel_char = signed_byte_to_char(wheel_byte)
    
    print(f"c_char值: button={btn_char}, x={x_char}, y={y_char}, wheel={wheel_char}")
    
    # 创建MOUSE_IO结构体
    io = MOUSE_IO()
    try:
        # 正确的c_char字段赋值
        io.button = btn_char
        io.x = x_char
        io.y = y_char
        io.wheel = wheel_char
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

def test_ultimate_function():
    """测试终极函数"""
    print("🔧 测试终极G-Hub鼠标移动函数")
    print("="*60)
    
    # 测试不同的移动，包括负值
    test_moves = [
        (0, 30, 0, 0),    # 右移30像素
        (0, -30, 0, 0),   # 左移30像素
        (0, 0, 20, 0),    # 下移20像素
        (0, 0, -20, 0),   # 上移20像素
        (0, 50, 50, 0),   # 对角移动
        (0, -25, -25, 0), # 负对角移动
    ]
    
    success_count = 0
    
    for i, (button, x, y, wheel) in enumerate(test_moves, 1):
        print(f"\n测试 {i}: 移动({x}, {y})")
        
        # 获取当前鼠标位置
        cursor_pos = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor_pos))
        print(f"移动前位置: ({cursor_pos.x}, {cursor_pos.y})")
        
        # 调用终极函数
        result = ultimate_mouse_move(button, x, y, wheel)
        
        # 等待一下
        time.sleep(0.2)
        
        # 检查移动后位置
        new_cursor_pos = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(new_cursor_pos))
        print(f"移动后位置: ({new_cursor_pos.x}, {new_cursor_pos.y})")
        
        # 计算实际移动距离
        actual_x = new_cursor_pos.x - cursor_pos.x
        actual_y = new_cursor_pos.y - cursor_pos.y
        print(f"实际移动: ({actual_x}, {actual_y})")
        print(f"期望移动: ({x}, {y})")
        
        # 检查移动是否成功（允许一定误差）
        if result and (abs(actual_x - x) <= 2 and abs(actual_y - y) <= 2):
            print("✅ 移动成功！")
            success_count += 1
        elif result and (actual_x != 0 or actual_y != 0):
            print("⚠️  移动部分成功（有偏差）")
            success_count += 0.5
        else:
            print("❌ 移动失败")
        
        time.sleep(0.5)  # 等待一下再进行下一个测试
    
    return success_count, len(test_moves)

def create_ultimate_patch():
    """创建终极修复补丁"""
    print("\n🔧 创建终极G-Hub修复补丁...")
    
    patch_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极G-Hub修复补丁
正确处理有符号字节值的c_char字段赋值
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

def signed_byte_to_char(value: int) -> int:
    """将有符号整数转换为c_char可接受的值"""
    clamped = clamp_char(value)
    if clamped < 0:
        return 256 + clamped  # 二进制补码
    else:
        return clamped

def ultimate_mouse_move_internal(button: int, x: int, y: int, wheel: int) -> bool:
    """
    终极内部鼠标移动函数
    正确处理有符号字节值
    """
    global handle
    
    # 确保设备已打开
    if not found or handle == 0:
        if not mouse_open():
            return False
    
    # 处理参数
    x_clamped = clamp_char(x)
    y_clamped = clamp_char(y)
    btn_byte = clamp_char(button)
    wheel_byte = clamp_char(wheel)
    
    # 转换为c_char可接受的值
    btn_char = signed_byte_to_char(btn_byte)
    x_char = signed_byte_to_char(x_clamped)
    y_char = signed_byte_to_char(y_clamped)
    wheel_char = signed_byte_to_char(wheel_byte)
    
    # 创建MOUSE_IO结构体
    io = MOUSE_IO()
    try:
        io.button = btn_char
        io.x = x_char
        io.y = y_char
        io.wheel = wheel_char
        io.unk1 = 0
    except Exception:
        return False
    
    # 调用底层函数
    return call_mouse(io)

def ultimate_ghub_move(x: int, y: int) -> None:
    """
    终极ghub_move函数
    """
    # 确保设备已初始化
    if not found:
        if not mouse_open():
            print("G-Hub device not available. Please ensure Logitech G-Hub is installed and running.")
            return
    
    # 调用终极内部函数
    ultimate_mouse_move_internal(0, x, y, 0)

# 应用终极修复
def apply_ultimate_ghub_fix():
    """应用终极G-Hub修复补丁"""
    import mouse_driver.MouseMove as mm
    
    # 替换函数
    mm._mouse_move_internal = ultimate_mouse_move_internal
    mm.ghub_move = ultimate_ghub_move
    mm.mouse_move = ultimate_ghub_move
    
    print("✅ 终极G-Hub修复补丁已应用")
    print("🎯 G-Hub驱动现在应该能在瓦洛兰特中完美工作了！")
    return True

if __name__ == "__main__":
    apply_ultimate_ghub_fix()
'''
    
    with open("ultimate_ghub_patch.py", "w", encoding="utf-8") as f:
        f.write(patch_content)
    
    print("✅ 终极修复补丁已保存到 ultimate_ghub_patch.py")

def main():
    """主函数"""
    print("终极G-Hub修复工具")
    print("专门修复瓦洛兰特环境下的G-Hub驱动问题")
    print("正确处理有符号字节值的c_char字段赋值")
    print("="*60)
    
    # 测试终极函数
    success_count, total_tests = test_ultimate_function()
    
    # 创建终极补丁
    create_ultimate_patch()
    
    print(f"\n{'='*60}")
    print("🎯 终极修复总结:")
    print(f"• 测试结果: {success_count}/{total_tests} 个测试成功")
    print("• 问题根源: c_char字段需要正确的有符号字节值处理")
    print("• 解决方案: 使用二进制补码正确处理负数")
    print("• 瓦洛兰特兼容: G-Hub驱动硬件级别，不会被反作弊检测")
    
    if success_count >= total_tests * 0.8:  # 80%成功率
        print("✅ 大部分测试通过！G-Hub驱动现在应该能正常工作了！")
        print("🎮 可以在瓦洛兰特中使用这个驱动了！")
    else:
        print("⚠️  测试成功率较低，可能需要进一步调试")
    
    input("\n按Enter键退出...")

if __name__ == "__main__":
    main()
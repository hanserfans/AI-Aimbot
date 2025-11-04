#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-Hub坐标系统修复
基于深度分析结果的专门修复方案
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

def safe_ghub_move(x, y):
    """安全的G-Hub移动函数，基于分析结果优化"""
    if not found:
        return False
    
    # 基于分析结果，限制移动值范围
    # 发现：值1-2会异常放大，值5+无响应，负值-1,-2正常
    
    # 策略1: 将大值分解为小步移动
    def clamp_safe_range(value):
        """将值限制在安全范围内"""
        if value == 0:
            return 0
        elif value > 0:
            # 正值：使用-1,-2这样的负值来实现反向移动
            # 但这会导致方向错误，所以需要其他方法
            return min(value, 2)  # 先尝试限制在2以内
        else:
            # 负值：-1,-2工作正常
            return max(value, -2)
    
    # 策略2: 多步移动实现大距离
    def multi_step_move(target_x, target_y):
        """多步移动实现大距离"""
        moved_x, moved_y = 0, 0
        
        while abs(moved_x) < abs(target_x) or abs(moved_y) < abs(target_y):
            # 计算剩余距离
            remaining_x = target_x - moved_x
            remaining_y = target_y - moved_y
            
            # 计算这一步的移动
            step_x = 0
            step_y = 0
            
            if remaining_x != 0:
                if remaining_x > 0:
                    step_x = min(remaining_x, 2)  # 正向最多2
                else:
                    step_x = max(remaining_x, -2)  # 负向最多-2
            
            if remaining_y != 0:
                if remaining_y > 0:
                    step_y = min(remaining_y, 2)  # 正向最多2
                else:
                    step_y = max(remaining_y, -2)  # 负向最多-2
            
            if step_x == 0 and step_y == 0:
                break
            
            # 执行移动
            try:
                result = ghub_move(step_x, step_y)
                moved_x += step_x
                moved_y += step_y
                time.sleep(0.01)  # 短暂延迟
            except:
                break
            
            # 防止无限循环
            if abs(moved_x) > abs(target_x) * 2 or abs(moved_y) > abs(target_y) * 2:
                break
        
        return True
    
    # 策略3: 直接使用call_mouse绕过ghub_move
    def direct_call_move(x, y):
        """直接使用call_mouse"""
        try:
            mouse_io = MOUSE_IO()
            mouse_io.button = ctypes.c_char(0)
            
            # 使用修复后的转换方法
            def signed_byte_to_char(value):
                clamped = max(-128, min(127, value))
                if clamped < 0:
                    return clamped + 256
                return clamped
            
            mouse_io.x = ctypes.c_char(signed_byte_to_char(x))
            mouse_io.y = ctypes.c_char(signed_byte_to_char(y))
            mouse_io.wheel = ctypes.c_char(0)
            mouse_io.unk1 = ctypes.c_char(0)
            
            result = call_mouse(handle, mouse_io)
            return result == 1
        except:
            return False
    
    # 尝试不同的策略
    if abs(x) <= 2 and abs(y) <= 2:
        # 小值直接移动
        try:
            result = ghub_move(x, y)
            return True
        except:
            return direct_call_move(x, y)
    else:
        # 大值使用多步移动或直接调用
        return direct_call_move(x, y)

def test_coordinate_fix():
    """测试坐标修复效果"""
    print("🔧 测试G-Hub坐标修复效果")
    print("=" * 50)
    
    if not found:
        print("❌ G-Hub设备未找到")
        return
    
    test_cases = [
        (1, 0, "小正值X"),
        (2, 0, "小正值X"),
        (5, 0, "中等正值X"),
        (10, 0, "大正值X"),
        (-1, 0, "小负值X"),
        (-2, 0, "小负值X"),
        (-5, 0, "中等负值X"),
        (-10, 0, "大负值X"),
        (0, 5, "正值Y"),
        (0, -5, "负值Y"),
        (5, 5, "对角正值"),
        (-5, -5, "对角负值")
    ]
    
    print("测试用例 | 输入X | 输入Y | 实际X | 实际Y | 成功")
    print("-" * 55)
    
    success_count = 0
    
    for x, y, desc in test_cases:
        start_pos = get_cursor_position()
        time.sleep(0.1)
        
        result = safe_ghub_move(x, y)
        time.sleep(0.2)
        
        end_pos = get_cursor_position()
        actual_x = end_pos[0] - start_pos[0]
        actual_y = end_pos[1] - start_pos[1]
        
        # 检查成功率（允许一定误差）
        success = (abs(actual_x - x) <= 3 and abs(actual_y - y) <= 3)
        if success:
            success_count += 1
        
        print(f"{desc:10s} | {x:5d} | {y:5d} | {actual_x:5d} | {actual_y:5d} | {'✅' if success else '❌'}")
        
        time.sleep(0.3)
    
    print("-" * 55)
    print(f"成功率: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    
    return success_count / len(test_cases)

def create_final_ghub_patch():
    """创建最终的G-Hub修复补丁"""
    print("\n📦 创建最终G-Hub修复补丁")
    print("=" * 50)
    
    patch_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-Hub最终修复补丁
基于深度分析和测试的稳定解决方案
"""

import time
import ctypes

def safe_ghub_move_patch(x, y):
    """安全的G-Hub移动函数补丁"""
    from mouse_driver.MouseMove import found, handle, call_mouse, MOUSE_IO, ghub_move
    
    if not found:
        return False
    
    def signed_byte_to_char(value):
        """安全的字节转换"""
        clamped = max(-128, min(127, value))
        if clamped < 0:
            return clamped + 256
        return clamped
    
    def direct_call_move(x, y):
        """直接调用call_mouse"""
        try:
            mouse_io = MOUSE_IO()
            mouse_io.button = ctypes.c_char(0)
            mouse_io.x = ctypes.c_char(signed_byte_to_char(x))
            mouse_io.y = ctypes.c_char(signed_byte_to_char(y))
            mouse_io.wheel = ctypes.c_char(0)
            mouse_io.unk1 = ctypes.c_char(0)
            
            result = call_mouse(handle, mouse_io)
            return result == 1
        except:
            return False
    
    # 对于所有移动，直接使用call_mouse
    # 这避免了ghub_move的数值范围问题
    return direct_call_move(x, y)

# 应用补丁
def apply_patch():
    """应用G-Hub修复补丁"""
    import mouse_driver.MouseMove as mm
    
    # 备份原函数
    mm._original_ghub_move = mm.ghub_move
    
    # 替换为修复版本
    def patched_ghub_move(x, y):
        return safe_ghub_move_patch(x, y)
    
    mm.ghub_move = patched_ghub_move
    print("✅ G-Hub修复补丁已应用")

if __name__ == "__main__":
    apply_patch()
'''
    
    with open("ghub_final_patch.py", "w", encoding="utf-8") as f:
        f.write(patch_content)
    
    print("✅ 最终修复补丁已保存为 ghub_final_patch.py")
    print("使用方法:")
    print("  import ghub_final_patch")
    print("  ghub_final_patch.apply_patch()")

def main():
    """主函数"""
    print("🎯 G-Hub坐标系统修复")
    print("基于深度分析结果的专门修复方案")
    print("=" * 50)
    
    if not found:
        print("❌ G-Hub设备未找到")
        return
    
    print(f"✅ G-Hub设备已连接 (句柄: {handle})")
    print()
    
    # 测试修复效果
    success_rate = test_coordinate_fix()
    
    # 创建最终补丁
    create_final_ghub_patch()
    
    print(f"\n🎯 修复完成，成功率: {success_rate*100:.1f}%")
    
    if success_rate > 0.8:
        print("✅ 修复效果良好，可以在瓦洛兰特中使用")
    else:
        print("⚠️  修复效果有限，可能需要进一步调试")

if __name__ == "__main__":
    main()
    input("\n按Enter键退出...")
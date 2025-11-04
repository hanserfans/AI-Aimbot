#!/usr/bin/env python3
"""
G304快速诊断和修复脚本
"""

import sys
import os
import time

# 添加mouse_driver路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mouse_driver'))

def quick_g304_diagnosis():
    """快速G304诊断"""
    print("🔍 G304快速诊断")
    print("=" * 30)
    
    # 1. 检查驱动连接
    try:
        import MouseMove
        print(f"✓ MouseMove导入成功")
        print(f"  found: {getattr(MouseMove, 'found', 'N/A')}")
        print(f"  handle: {getattr(MouseMove, 'handle', 'N/A')}")
    except Exception as e:
        print(f"✗ MouseMove导入失败: {e}")
        return False
    
    # 2. 测试基本功能
    try:
        from ReliableMouseMove import get_cursor_position, mouse_move
        
        start_x, start_y = get_cursor_position()
        print(f"✓ 当前鼠标位置: ({start_x}, {start_y})")
        
        # 测试小移动
        print("测试鼠标移动...")
        if mouse_move(5, 0):
            time.sleep(0.2)
            new_x, new_y = get_cursor_position()
            if new_x != start_x or new_y != start_y:
                print("✓ 鼠标移动正常")
                # 恢复位置
                mouse_move(start_x - new_x, start_y - new_y)
                return True
            else:
                print("⚠️  鼠标移动调用成功但位置未变化")
                return False
        else:
            print("✗ 鼠标移动调用失败")
            return False
            
    except Exception as e:
        print(f"✗ 功能测试失败: {e}")
        return False

def force_g304_reconnect():
    """强制G304重连"""
    print("\n🔄 强制G304重连")
    print("=" * 30)
    
    try:
        # 清除模块缓存
        modules_to_clear = [name for name in sys.modules if 'MouseMove' in name]
        for module in modules_to_clear:
            del sys.modules[module]
        
        # 重新导入
        import MouseMove
        
        # 尝试关闭和重新打开
        if hasattr(MouseMove, 'mouse_close'):
            MouseMove.mouse_close()
            print("✓ 关闭现有连接")
        
        time.sleep(1)
        
        if hasattr(MouseMove, 'mouse_open'):
            result = MouseMove.mouse_open()
            print(f"✓ 重新连接结果: {result}")
        
        print(f"新状态 - found: {getattr(MouseMove, 'found', False)}")
        print(f"新状态 - handle: {getattr(MouseMove, 'handle', None)}")
        
        return getattr(MouseMove, 'found', False)
        
    except Exception as e:
        print(f"✗ 重连失败: {e}")
        return False

def test_g304_movement():
    """测试G304移动"""
    print("\n🧪 G304移动测试")
    print("=" * 30)
    
    try:
        from ReliableMouseMove import mouse_move, get_cursor_position
        
        start_x, start_y = get_cursor_position()
        print(f"起始位置: ({start_x}, {start_y})")
        
        # 测试序列
        movements = [
            (20, 0, "右20px"),
            (0, 20, "下20px"),
            (-20, 0, "左20px"),
            (0, -20, "上20px")
        ]
        
        success_count = 0
        for dx, dy, desc in movements:
            before_x, before_y = get_cursor_position()
            
            if mouse_move(dx, dy):
                time.sleep(0.3)
                after_x, after_y = get_cursor_position()
                
                actual_dx = after_x - before_x
                actual_dy = after_y - before_y
                
                print(f"{desc}: ({actual_dx}, {actual_dy})", end="")
                
                if abs(actual_dx) > 0 or abs(actual_dy) > 0:
                    print(" ✓")
                    success_count += 1
                else:
                    print(" ✗")
            else:
                print(f"{desc}: 调用失败 ✗")
        
        print(f"\n成功率: {success_count}/{len(movements)}")
        return success_count > 0
        
    except Exception as e:
        print(f"✗ 移动测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🖱️  G304快速修复工具")
    print("=" * 40)
    
    # 步骤1: 初始诊断
    if quick_g304_diagnosis():
        print("\n✅ G304工作正常，无需修复")
        return
    
    print("\n⚠️  检测到问题，尝试修复...")
    
    # 步骤2: 强制重连
    if force_g304_reconnect():
        print("\n✅ 重连成功，测试功能...")
        
        # 步骤3: 测试移动
        if test_g304_movement():
            print("\n🎉 G304修复成功！")
        else:
            print("\n⚠️  重连成功但移动功能异常")
            print("\n建议:")
            print("1. 检查G304的USB接收器是否正确连接")
            print("2. 尝试重新插拔USB接收器")
            print("3. 检查G304鼠标是否开机且电量充足")
            print("4. 在G-Hub软件中检查G304是否被识别")
    else:
        print("\n❌ 重连失败")
        print("\n可能的原因:")
        print("1. G304 USB接收器未连接")
        print("2. G304鼠标未开机或电量不足")
        print("3. G-Hub软件未正确识别G304")
        print("4. 需要管理员权限运行")
        
        print("\n建议操作:")
        print("1. 重新插拔G304的USB接收器")
        print("2. 确保G304鼠标开机且电量充足")
        print("3. 重启G-Hub软件")
        print("4. 以管理员身份运行此程序")

if __name__ == "__main__":
    main()
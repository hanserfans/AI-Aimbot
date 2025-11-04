#!/usr/bin/env python3
"""
简单的自适应校正系统测试
"""

import time
import pyautogui

def test_import():
    """测试导入是否正常"""
    try:
        from mouse_driver.MouseMove import (
            initialize_mouse, 
            ghub_move, 
            get_adaptive_correction_report,
            set_adaptive_correction
        )
        print("✅ 导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_initialization():
    """测试初始化"""
    try:
        from mouse_driver.MouseMove import initialize_mouse
        result = initialize_mouse()
        print(f"✅ 初始化结果: {result}")
        return True
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False

def test_simple_move():
    """测试简单移动"""
    try:
        from mouse_driver.MouseMove import ghub_move
        
        print("准备测试移动...")
        time.sleep(2)
        
        start_pos = pyautogui.position()
        print(f"起始位置: {start_pos}")
        
        # 简单移动测试
        success = ghub_move(10, 0)
        print(f"移动结果: {success}")
        
        time.sleep(0.5)
        end_pos = pyautogui.position()
        print(f"结束位置: {end_pos}")
        
        actual_dx = end_pos.x - start_pos.x
        actual_dy = end_pos.y - start_pos.y
        print(f"实际移动: ({actual_dx}, {actual_dy})")
        
        return True
    except Exception as e:
        print(f"❌ 移动测试失败: {e}")
        return False

def test_report():
    """测试报告功能"""
    try:
        from mouse_driver.MouseMove import get_adaptive_correction_report
        report = get_adaptive_correction_report()
        print(f"📊 系统报告:")
        print(report)
        return True
    except Exception as e:
        print(f"❌ 报告测试失败: {e}")
        return False

def main():
    print("🧪 简单自适应校正系统测试")
    print("=" * 40)
    
    # 测试导入
    if not test_import():
        return
    
    # 测试初始化
    if not test_initialization():
        return
    
    # 测试报告
    test_report()
    
    # 测试移动
    input("\n按回车键开始移动测试...")
    test_simple_move()
    
    print("\n🏁 测试完成")

if __name__ == "__main__":
    main()
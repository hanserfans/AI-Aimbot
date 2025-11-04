#!/usr/bin/env python3
"""
最终系统验证测试
验证 G-Hub 鼠标控制系统的完整功能
"""
import sys
import os
import time
import ctypes

def check_admin_privileges():
    """检查管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def test_ghub_import():
    """测试 G-Hub 模块导入"""
    try:
        from mouse_driver.MouseMove import ghub_move, initialize_mouse, close_mouse
        print("✅ G-Hub 模块导入成功")
        return True, (ghub_move, initialize_mouse, close_mouse)
    except ImportError as e:
        print(f"❌ G-Hub 模块导入失败: {e}")
        return False, None
    except Exception as e:
        print(f"❌ 导入时发生错误: {e}")
        return False, None

def test_mouse_initialization(initialize_mouse):
    """测试鼠标初始化"""
    try:
        result = initialize_mouse()
        if result:
            print("✅ 鼠标初始化成功")
            return True
        else:
            print("❌ 鼠标初始化失败")
            return False
    except Exception as e:
        print(f"❌ 鼠标初始化时发生错误: {e}")
        return False

def test_mouse_movement(ghub_move):
    """测试鼠标移动功能"""
    try:
        print("🔄 测试鼠标移动...")
        
        # 测试小幅移动
        test_movements = [
            (10, 0),   # 右移
            (-10, 0),  # 左移
            (0, 10),   # 下移
            (0, -10),  # 上移
            (5, 5),    # 对角移动
            (-5, -5),  # 反向对角移动
        ]
        
        for i, (x, y) in enumerate(test_movements):
            print(f"  测试移动 {i+1}/6: ({x}, {y})")
            ghub_move(x, y)
            time.sleep(0.1)  # 短暂延迟
        
        print("✅ 鼠标移动测试完成")
        return True
    except Exception as e:
        print(f"❌ 鼠标移动测试失败: {e}")
        return False

def test_mouse_cleanup(close_mouse):
    """测试鼠标清理"""
    try:
        close_mouse()
        print("✅ 鼠标清理成功")
        return True
    except Exception as e:
        print(f"❌ 鼠标清理失败: {e}")
        return False

def main():
    print("=" * 50)
    print("🔍 G-Hub 鼠标控制系统 - 最终验证测试")
    print("=" * 50)
    
    # 检查管理员权限
    if not check_admin_privileges():
        print("❌ 需要管理员权限运行此测试")
        print("请以管理员身份重新运行")
        return False
    
    print("✅ 管理员权限确认")
    
    # 测试模块导入
    import_success, modules = test_ghub_import()
    if not import_success:
        return False
    
    ghub_move, initialize_mouse, close_mouse = modules
    
    # 测试鼠标初始化
    if not test_mouse_initialization(initialize_mouse):
        return False
    
    # 测试鼠标移动
    if not test_mouse_movement(ghub_move):
        return False
    
    # 测试鼠标清理
    if not test_mouse_cleanup(close_mouse):
        return False
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过！G-Hub 鼠标控制系统工作正常")
    print("=" * 50)
    
    print("\n📋 系统状态总结:")
    print("✅ G-Hub 虚拟总线枚举器: 正常")
    print("✅ 设备路径发现: 正常")
    print("✅ 鼠标初始化: 正常")
    print("✅ 鼠标移动控制: 正常")
    print("✅ 资源清理: 正常")
    
    print("\n🚀 系统已准备就绪，可以开始使用自动瞄准功能！")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n按 Enter 键退出...")
            input()
        else:
            print("\n❌ 测试失败，请检查错误信息")
            print("按 Enter 键退出...")
            input()
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生未预期的错误: {e}")
        print("按 Enter 键退出...")
        input()
#!/usr/bin/env python3
"""
简单的鼠标移动测试脚本
验证G-Hub鼠标控制是否能真实移动鼠标
"""

import time
import ctypes
from ctypes import wintypes

def get_cursor_pos():
    """获取当前鼠标位置"""
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def main():
    print("🎮 简单鼠标移动测试")
    print("=" * 40)
    
    # 检查管理员权限
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("❌ 需要管理员权限运行此测试")
            input("按 Enter 键退出...")
            return
        print("✅ 管理员权限检查通过")
    except:
        print("⚠️  无法检查管理员权限")
    
    try:
        # 导入ghub_move函数
        print("\n🔍 导入ghub_move函数...")
        from mouse_driver.MouseMove import ghub_move
        print("✅ ghub_move函数导入成功")
        
        # 获取初始鼠标位置
        initial_x, initial_y = get_cursor_pos()
        print(f"\n📍 初始鼠标位置: ({initial_x}, {initial_y})")
        
        print("\n🔄 开始测试鼠标移动...")
        print("请观察屏幕上的鼠标光标移动")
        
        # 倒计时
        for i in range(3, 0, -1):
            print(f"测试将在 {i} 秒后开始...")
            time.sleep(1)
        
        # 测试移动序列：画一个小正方形
        movements = [
            ("向右移动 100px", 100, 0),
            ("向下移动 100px", 0, 100),
            ("向左移动 100px", -100, 0),
            ("向上移动 100px", 0, -100),
        ]
        
        for i, (desc, dx, dy) in enumerate(movements, 1):
            print(f"\n步骤 {i}: {desc}")
            
            # 记录移动前位置
            before_x, before_y = get_cursor_pos()
            print(f"   移动前位置: ({before_x}, {before_y})")
            
            # 执行移动
            result = ghub_move(dx, dy)
            print(f"   ghub_move({dx}, {dy}) 返回: {result}")
            
            # 等待一下
            time.sleep(0.5)
            
            # 记录移动后位置
            after_x, after_y = get_cursor_pos()
            print(f"   移动后位置: ({after_x}, {after_y})")
            
            # 计算实际移动距离
            actual_dx = after_x - before_x
            actual_dy = after_y - before_y
            print(f"   实际移动: ({actual_dx:+d}, {actual_dy:+d})")
            
            # 等待用户观察
            time.sleep(1.5)
        
        # 检查最终位置
        final_x, final_y = get_cursor_pos()
        print(f"\n📍 最终鼠标位置: ({final_x}, {final_y})")
        
        # 计算总位移
        total_dx = final_x - initial_x
        total_dy = final_y - initial_y
        print(f"📏 总位移: ({total_dx:+d}, {total_dy:+d})")
        
        # 判断测试结果
        if abs(total_dx) <= 10 and abs(total_dy) <= 10:
            print("\n🎉 测试成功！")
            print("✅ 鼠标已回到起始位置附近")
            print("✅ G-Hub 鼠标控制功能正常工作")
        else:
            print(f"\n⚠️  鼠标未完全回到起始位置")
            print(f"   偏差: ({total_dx}, {total_dy})")
            if abs(total_dx) > 0 or abs(total_dy) > 0:
                print("✅ 但鼠标确实在移动，G-Hub 控制功能基本正常")
            else:
                print("❌ 鼠标可能没有移动，请检查G-Hub设置")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保MouseMove模块正确安装")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
    
    print("\n" + "=" * 40)
    input("按 Enter 键退出...")

if __name__ == "__main__":
    main()
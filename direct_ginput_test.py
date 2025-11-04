#!/usr/bin/env python3
"""
直接使用g-input方式的鼠标控制测试
按照用户建议，直接使用原始g-input项目的方式
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

def main():
    print("🎯 直接使用g-input方式的鼠标控制测试")
    print("=" * 50)
    
    # 检查管理员权限
    is_admin = check_admin_privileges()
    print(f"管理员权限: {'✅ 是' if is_admin else '❌ 否'}")
    
    if not is_admin:
        print("⚠️  建议以管理员身份运行")
        print("🚀 命令: Start-Process powershell -ArgumentList \"-Command\", \"cd 'f:\\\\git\\\\AI-Aimbot'; python direct_ginput_test.py; Read-Host 'Press Enter to continue'\" -Verb RunAs")
        print()
    
    # 添加g-input路径
    ginput_path = os.path.join(os.path.dirname(__file__), 'mouse_driver', 'g-input-main', 'g-input-main')
    sys.path.insert(0, ginput_path)
    
    try:
        # 按照用户建议的方式导入
        import mouse as GHUB
        import win32api
        
        print("✅ 成功导入模块")
        
        # 初始化鼠标
        print("🔌 初始化鼠标...")
        GHUB.mouse_open()  # initialize mouse
        time.sleep(1)
        
        print(f"设备状态: {'✅ 已找到' if GHUB.found else '❌ 未找到'}")
        print(f"设备句柄: {GHUB.handle}")
        
        if not GHUB.found:
            print("❌ 设备未找到，无法继续测试")
            return False
        
        # 定义enabled函数
        def enabled():
            return win32api.GetKeyState(0x02) in (-127, -128)  # 0x02 is right click
        
        print("\n🖱️  鼠标控制测试")
        print("按住右键来测试鼠标移动")
        print("移动坐标: x=1, y=1")
        print("按 Ctrl+C 退出测试")
        
        x, y = 1, 1  # sample coordinates to move the mouse to
        
        try:
            move_count = 0
            while True:
                if enabled():
                    print(f"🎯 检测到右键按下，执行鼠标移动 ({x}, {y}) - 第{move_count + 1}次")
                    GHUB.mouse_move(0, x, y, 0)
                    move_count += 1
                    time.sleep(0.1)  # 短暂延迟
                    
                    if move_count >= 10:  # 测试10次后提示
                        print("✅ 已执行10次移动，继续测试或按Ctrl+C退出")
                        move_count = 0
                else:
                    time.sleep(0.05)  # 检查间隔
                    
        except KeyboardInterrupt:
            print("\n⏹️  用户中断测试")
        
        print("✅ 测试完成")
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 测试结果: {'✅ 成功' if success else '❌ 失败'}")
    
    if not success:
        print("\n💡 故障排除建议:")
        print("1. 确保以管理员身份运行")
        print("2. 确保G-Hub软件正在运行")
        print("3. 确保有Logitech设备连接")
        print("4. 尝试重启G-Hub软件")
    
    input("\n按 Enter 键退出...")
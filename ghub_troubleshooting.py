#!/usr/bin/env python3
"""
G-Hub故障排除和诊断工具
"""

import sys
import os
import subprocess
import psutil
import time

# 添加mouse_driver路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mouse_driver'))

try:
    import MouseMove
    print("✓ 成功导入MouseMove模块")
except ImportError as e:
    print(f"✗ 导入MouseMove模块失败: {e}")
    sys.exit(1)

def check_ghub_processes():
    """检查G-Hub相关进程"""
    print("\n=== 检查G-Hub进程 ===")
    
    ghub_processes = [
        "lghub.exe",
        "lghub_agent.exe", 
        "lghub_updater.exe",
        "lghub_system_tray.exe",
        "LogiOptionsExcelAddin.exe"
    ]
    
    running_processes = []
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower()
            for ghub_proc in ghub_processes:
                if ghub_proc.lower() in proc_name:
                    running_processes.append((proc.info['name'], proc.info['pid']))
                    print(f"✓ 找到进程: {proc.info['name']} (PID: {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not running_processes:
        print("⚠️  没有找到G-Hub相关进程")
        print("   请确保Logitech G HUB软件正在运行")
        return False
    
    return True

def check_ghub_installation():
    """检查G-Hub安装"""
    print("\n=== 检查G-Hub安装 ===")
    
    common_paths = [
        r"C:\Program Files\LGHUB\lghub.exe",
        r"C:\Program Files (x86)\LGHUB\lghub.exe",
        r"C:\Users\{}\AppData\Local\LGHUB\lghub.exe".format(os.getenv('USERNAME', '')),
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"✓ 找到G-Hub安装: {path}")
            return True
    
    print("⚠️  没有找到G-Hub安装")
    return False

def test_alternative_mouse_methods():
    """测试替代的鼠标控制方法"""
    print("\n=== 测试替代鼠标控制方法 ===")
    
    # 测试Windows API
    try:
        import ctypes
        from ctypes import wintypes
        
        user32 = ctypes.windll.user32
        
        # 获取当前位置
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        start_x, start_y = pt.x, pt.y
        print(f"当前鼠标位置: ({start_x}, {start_y})")
        
        # 尝试SetCursorPos
        print("测试SetCursorPos...")
        new_x, new_y = start_x + 100, start_y + 100
        result = user32.SetCursorPos(new_x, new_y)
        
        time.sleep(0.5)
        
        # 检查新位置
        user32.GetCursorPos(ctypes.byref(pt))
        actual_x, actual_y = pt.x, pt.y
        
        if actual_x == new_x and actual_y == new_y:
            print("✓ SetCursorPos工作正常")
            # 恢复位置
            user32.SetCursorPos(start_x, start_y)
        else:
            print("✗ SetCursorPos没有效果")
        
    except Exception as e:
        print(f"✗ Windows API测试失败: {e}")
    
    # 测试PyAutoGUI
    try:
        import pyautogui
        
        start_x, start_y = pyautogui.position()
        print(f"PyAutoGUI当前位置: ({start_x}, {start_y})")
        
        print("测试PyAutoGUI移动...")
        pyautogui.move(50, 50)
        time.sleep(0.5)
        
        new_x, new_y = pyautogui.position()
        if new_x != start_x or new_y != start_y:
            print("✓ PyAutoGUI工作正常")
            # 恢复位置
            pyautogui.moveTo(start_x, start_y)
        else:
            print("✗ PyAutoGUI没有效果")
            
    except ImportError:
        print("⚠️  PyAutoGUI未安装")
    except Exception as e:
        print(f"✗ PyAutoGUI测试失败: {e}")

def test_ghub_device_communication():
    """测试G-Hub设备通信"""
    print("\n=== 测试G-Hub设备通信 ===")
    
    # 检查设备句柄
    print(f"设备句柄: {MouseMove.handle}")
    print(f"设备状态: {MouseMove.found}")
    
    # 尝试不同的移动值
    test_values = [
        (1, 0),      # 最小移动
        (10, 0),     # 小移动
        (50, 0),     # 中等移动
        (127, 0),    # 最大正值
        (-127, 0),   # 最大负值
    ]
    
    for x, y in test_values:
        try:
            print(f"测试移动: ({x}, {y})")
            MouseMove.ghub_move(x, y)
            print("  ✓ 调用成功")
            time.sleep(0.2)
        except Exception as e:
            print(f"  ✗ 调用失败: {e}")

def provide_troubleshooting_steps():
    """提供故障排除步骤"""
    print("\n=== 故障排除建议 ===")
    
    print("1. 确保Logitech G HUB软件正在运行:")
    print("   - 打开Logitech G HUB应用程序")
    print("   - 确保你的鼠标已被识别")
    print("   - 检查鼠标是否在设备列表中")
    
    print("\n2. 检查鼠标兼容性:")
    print("   - 这个驱动主要适用于Logitech G系列鼠标")
    print("   - 确保你使用的是支持的鼠标型号")
    
    print("\n3. 权限问题:")
    print("   - 尝试以管理员身份运行程序")
    print("   - 检查Windows安全软件是否阻止了程序")
    
    print("\n4. G-Hub设置:")
    print("   - 在G-Hub中检查鼠标设置")
    print("   - 确保没有启用冲突的配置文件")
    print("   - 尝试重启G-Hub软件")
    
    print("\n5. 替代方案:")
    print("   - 如果G-Hub驱动不工作，可以使用Windows API")
    print("   - 或者使用PyAutoGUI等其他鼠标控制库")

def main():
    """主函数"""
    print("G-Hub故障排除和诊断工具")
    print("=" * 50)
    
    # 运行所有检查
    ghub_installed = check_ghub_installation()
    ghub_running = check_ghub_processes()
    
    # 测试设备通信
    test_ghub_device_communication()
    
    # 测试替代方法
    test_alternative_mouse_methods()
    
    # 提供建议
    provide_troubleshooting_steps()
    
    print("\n" + "=" * 50)
    print("诊断完成")
    
    if not ghub_running:
        print("\n⚠️  主要问题: G-Hub软件没有运行")
        print("   解决方案: 启动Logitech G HUB软件")
    elif MouseMove.found and MouseMove.handle:
        print("\n⚠️  设备连接正常但移动无效")
        print("   可能需要检查G-Hub设置或鼠标兼容性")
    else:
        print("\n⚠️  设备连接问题")
        print("   请检查鼠标连接和G-Hub配置")

if __name__ == "__main__":
    main()
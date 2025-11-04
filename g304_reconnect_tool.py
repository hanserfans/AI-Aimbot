#!/usr/bin/env python3
"""
G304鼠标重新连接和测试工具
专门针对罗技G304无线鼠标的驱动重新加载和测试
"""

import sys
import os
import time
import ctypes
from ctypes import wintypes

# 添加mouse_driver路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mouse_driver'))

def reload_mouse_driver():
    """重新加载鼠标驱动模块"""
    print("🔄 重新加载鼠标驱动模块...")
    
    # 清除已导入的模块
    modules_to_remove = []
    for module_name in sys.modules:
        if 'MouseMove' in module_name or 'ReliableMouseMove' in module_name:
            modules_to_remove.append(module_name)
    
    for module_name in modules_to_remove:
        print(f"  清除模块: {module_name}")
        del sys.modules[module_name]
    
    # 重新导入
    try:
        import MouseMove
        from ReliableMouseMove import get_driver, get_driver_status, mouse_move, get_cursor_position
        print("✓ 驱动模块重新加载成功")
        return True, MouseMove, get_driver, get_driver_status, mouse_move, get_cursor_position
    except Exception as e:
        print(f"✗ 驱动模块重新加载失败: {e}")
        return False, None, None, None, None, None

def check_g304_specific():
    """检查G304特定的连接状态"""
    print("\n🖱️  G304鼠标专项检查")
    print("=" * 40)
    
    # 检查G-Hub进程
    import psutil
    ghub_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'lghub' in proc.info['name'].lower():
                ghub_processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    print(f"G-Hub进程数量: {len(ghub_processes)}")
    for proc in ghub_processes:
        print(f"  - {proc['name']} (PID: {proc['pid']})")
    
    # 检查USB设备（G304是无线的，但接收器是USB）
    print("\n检查USB设备连接...")
    try:
        import subprocess
        result = subprocess.run(['powershell', '-Command', 
                               'Get-WmiObject -Class Win32_USBHub | Where-Object {$_.Description -like "*Logitech*"} | Select-Object Description, DeviceID'],
                               capture_output=True, text=True, timeout=10)
        if result.stdout:
            print("找到Logitech USB设备:")
            print(result.stdout)
        else:
            print("⚠️  没有找到Logitech USB设备")
    except Exception as e:
        print(f"USB设备检查失败: {e}")

def force_reconnect_g304():
    """强制重新连接G304"""
    print("\n🔄 强制重新连接G304...")
    
    success, MouseMove, get_driver, get_driver_status, mouse_move, get_cursor_position = reload_mouse_driver()
    if not success:
        return False
    
    # 尝试重新初始化MouseMove
    try:
        print("重新初始化MouseMove...")
        if hasattr(MouseMove, 'mouse_close'):
            MouseMove.mouse_close()
            print("  ✓ 关闭现有连接")
        
        time.sleep(1)
        
        if hasattr(MouseMove, 'mouse_open'):
            result = MouseMove.mouse_open()
            print(f"  重新打开结果: {result}")
        
        # 检查新状态
        print(f"  新的found状态: {getattr(MouseMove, 'found', 'N/A')}")
        print(f"  新的handle状态: {getattr(MouseMove, 'handle', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ 重新连接失败: {e}")
        return False

def test_g304_movement():
    """测试G304鼠标移动"""
    print("\n🧪 G304鼠标移动测试")
    print("=" * 40)
    
    success, MouseMove, get_driver, get_driver_status, mouse_move, get_cursor_position = reload_mouse_driver()
    if not success:
        return False
    
    # 获取驱动状态
    status = get_driver_status()
    print("当前驱动状态:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # 获取起始位置
    start_x, start_y = get_cursor_position()
    print(f"\n起始鼠标位置: ({start_x}, {start_y})")
    
    # 测试小幅移动
    print("\n测试小幅移动...")
    test_movements = [
        (10, 0, "右10px"),
        (0, 10, "下10px"),
        (-10, 0, "左10px"),
        (0, -10, "上10px")
    ]
    
    success_count = 0
    for dx, dy, desc in test_movements:
        before_x, before_y = get_cursor_position()
        print(f"  {desc}: 移动前({before_x}, {before_y})", end=" -> ")
        
        if mouse_move(dx, dy):
            time.sleep(0.2)
            after_x, after_y = get_cursor_position()
            actual_dx = after_x - before_x
            actual_dy = after_y - before_y
            print(f"移动后({after_x}, {after_y}), 实际移动({actual_dx}, {actual_dy})")
            
            if abs(actual_dx) > 0 or abs(actual_dy) > 0:
                success_count += 1
                print("    ✓ 成功")
            else:
                print("    ✗ 无移动")
        else:
            print("调用失败")
    
    # 测试大幅移动
    print(f"\n小幅移动成功率: {success_count}/{len(test_movements)}")
    
    if success_count > 0:
        print("\n测试大幅移动...")
        input("请观察屏幕，按Enter开始大幅移动测试...")
        
        large_movements = [
            (100, 0, "右100px"),
            (0, 100, "下100px"),
            (-100, 0, "左100px"),
            (0, -100, "上100px")
        ]
        
        for dx, dy, desc in large_movements:
            print(f"  {desc}...")
            mouse_move(dx, dy)
            time.sleep(0.5)
        
        print("✓ 大幅移动测试完成")
        
        # 返回起始位置
        current_x, current_y = get_cursor_position()
        return_dx = start_x - current_x
        return_dy = start_y - current_y
        mouse_move(return_dx, return_dy)
        print(f"返回起始位置附近")
    
    return success_count > 0

def main():
    """主函数"""
    print("🖱️  G304鼠标重新连接和测试工具")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 检查G304连接状态")
        print("2. 重新加载驱动模块")
        print("3. 强制重新连接G304")
        print("4. 测试G304鼠标移动")
        print("5. 完整重连和测试流程")
        print("6. 退出")
        
        choice = input("\n请输入选择 (1-6): ").strip()
        
        if choice == '1':
            check_g304_specific()
            
        elif choice == '2':
            reload_mouse_driver()
            
        elif choice == '3':
            force_reconnect_g304()
            
        elif choice == '4':
            test_g304_movement()
            
        elif choice == '5':
            print("\n🔄 执行完整重连和测试流程...")
            print("\n步骤1: 检查当前状态")
            check_g304_specific()
            
            print("\n步骤2: 强制重新连接")
            if force_reconnect_g304():
                print("\n步骤3: 测试鼠标移动")
                if test_g304_movement():
                    print("\n🎉 G304重连和测试成功!")
                else:
                    print("\n⚠️  G304连接成功但移动测试失败")
            else:
                print("\n❌ G304重连失败")
                
        elif choice == '6':
            print("退出工具")
            break
            
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序出错: {e}")
        import traceback
        traceback.print_exc()
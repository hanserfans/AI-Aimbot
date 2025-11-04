#!/usr/bin/env python3
"""
详细的G-Hub诊断脚本
检查G-Hub设备状态、权限和控制码
"""

import sys
import os
import time
import ctypes
import subprocess
import win32api
import win32file
import win32con

# 添加mouse_driver目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))

def check_admin_privileges():
    """检查管理员权限"""
    print("🔐 检查管理员权限")
    print("=" * 30)
    
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"管理员权限: {'✅ 是' if is_admin else '❌ 否'}")
        return is_admin
    except:
        print("⚠️  无法检查管理员权限")
        return False

def check_ghub_processes():
    """检查G-Hub进程"""
    print("\n🔍 检查G-Hub进程")
    print("=" * 30)
    
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq lghub*'], 
                              capture_output=True, text=True, shell=True)
        
        if 'lghub' in result.stdout.lower():
            print("✅ G-Hub进程正在运行")
            lines = result.stdout.split('\n')
            for line in lines:
                if 'lghub' in line.lower():
                    print(f"   {line.strip()}")
            return True
        else:
            print("❌ 未找到G-Hub进程")
            return False
            
    except Exception as e:
        print(f"❌ 检查G-Hub进程失败: {e}")
        return False

def check_ghub_version():
    """检查G-Hub版本"""
    print("\n📋 检查G-Hub版本")
    print("=" * 30)
    
    try:
        import winreg
        
        # 检查已安装程序
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        try:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            if "logitech" in display_name.lower() and "hub" in display_name.lower():
                                version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                print(f"✅ 找到: {display_name}")
                                print(f"   版本: {version}")
                                return version
                        except FileNotFoundError:
                            pass
                    i += 1
                except OSError:
                    break
        
        print("❌ 未找到G-Hub安装信息")
        return None
        
    except Exception as e:
        print(f"❌ 检查G-Hub版本失败: {e}")
        return None

def test_device_paths():
    """测试不同的设备路径"""
    print("\n🔧 测试设备路径")
    print("=" * 30)
    
    try:
        from MouseMove import device_initialize
        
        # 测试路径列表
        test_paths = [
            "LGHUB",
            "\\\\.\\LGHUB",
            "\\Device\\LGHUB",
            "\\??\\LGHUB",
        ]
        
        # 添加标准路径
        for i in range(1, 10):
            test_paths.append(f'\\??\\ROOT#SYSTEM#000{i}#' + '{1abc05c0-c378-41b9-9cef-df1aba82b015}')
        
        successful_paths = []
        
        for path in test_paths:
            print(f"测试路径: {path}")
            try:
                success = device_initialize(path)
                if success:
                    print(f"   ✅ 成功")
                    successful_paths.append(path)
                else:
                    print(f"   ❌ 失败")
            except Exception as e:
                print(f"   ❌ 异常: {e}")
        
        print(f"\n📊 成功的路径数量: {len(successful_paths)}")
        for path in successful_paths:
            print(f"   ✅ {path}")
        
        return successful_paths
        
    except Exception as e:
        print(f"❌ 测试设备路径失败: {e}")
        return []

def test_device_handle():
    """测试设备句柄"""
    print("\n🔗 测试设备句柄")
    print("=" * 30)
    
    try:
        from MouseMove import device_initialize, handle
        import MouseMove
        
        # 尝试初始化LGHUB设备
        success = device_initialize("LGHUB")
        
        print(f"设备初始化: {'✅ 成功' if success else '❌ 失败'}")
        print(f"设备句柄: {MouseMove.handle}")
        print(f"句柄类型: {type(MouseMove.handle)}")
        print(f"句柄值: {MouseMove.handle}")
        
        if MouseMove.handle:
            # 检查句柄是否有效
            try:
                # 尝试获取句柄信息
                handle_info = win32file.GetFileType(int(MouseMove.handle))
                print(f"句柄文件类型: {handle_info}")
                
                # 检查句柄是否可读写
                print("测试句柄访问权限...")
                return True
                
            except Exception as e:
                print(f"句柄验证失败: {e}")
                return False
        else:
            print("❌ 无效句柄")
            return False
            
    except Exception as e:
        print(f"❌ 测试设备句柄失败: {e}")
        return False

def test_device_io_control():
    """测试DeviceIoControl调用"""
    print("\n⚙️  测试DeviceIoControl")
    print("=" * 30)
    
    try:
        from MouseMove import device_initialize, call_mouse, MOUSE_IO, _DeviceIoControl
        import MouseMove
        
        # 确保设备已初始化
        if not MouseMove.handle:
            success = device_initialize("LGHUB")
            if not success:
                print("❌ 设备未初始化")
                return False
        
        print(f"使用句柄: {MouseMove.handle}")
        
        # 创建测试数据
        io = MOUSE_IO()
        io.button = ctypes.c_char(b'\x00')
        io.x = ctypes.c_char(b'\x01')  # 小幅移动
        io.y = ctypes.c_char(b'\x00')
        io.wheel = ctypes.c_char(b'\x00')
        io.unk1 = ctypes.c_char(b'\x00')
        
        print("测试数据结构:")
        print(f"   button: {io.button}")
        print(f"   x: {io.x}")
        print(f"   y: {io.y}")
        print(f"   wheel: {io.wheel}")
        print(f"   unk1: {io.unk1}")
        print(f"   结构大小: {ctypes.sizeof(io)}")
        
        # 测试不同的控制码
        control_codes = [
            0x2a2010,  # 原始控制码
            0x2a2000,  # 变体1
            0x2a2004,  # 变体2
            0x2a200c,  # 变体3
        ]
        
        for code in control_codes:
            print(f"\n测试控制码: 0x{code:x}")
            try:
                status, bytes_returned = _DeviceIoControl(
                    MouseMove.handle,
                    code,
                    ctypes.c_void_p(ctypes.addressof(io)),
                    ctypes.sizeof(io),
                    None,
                    0
                )
                
                print(f"   状态: {'✅ 成功' if status else '❌ 失败'}")
                print(f"   返回字节: {bytes_returned}")
                
                if status:
                    print(f"   ✅ 控制码 0x{code:x} 工作正常")
                    return True
                else:
                    # 获取详细错误信息
                    error_code = ctypes.windll.kernel32.GetLastError()
                    print(f"   错误代码: {error_code}")
                    
            except Exception as e:
                print(f"   异常: {e}")
        
        print("❌ 所有控制码都失败")
        return False
        
    except Exception as e:
        print(f"❌ 测试DeviceIoControl失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alternative_methods():
    """测试替代方法"""
    print("\n🔄 测试替代方法")
    print("=" * 30)
    
    # 测试Win32 API
    print("测试Win32 API鼠标控制:")
    try:
        current_pos = win32api.GetCursorPos()
        print(f"   当前位置: {current_pos}")
        
        # 小幅移动测试
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 1, 0, 0, 0)
        time.sleep(0.1)
        new_pos = win32api.GetCursorPos()
        print(f"   移动后位置: {new_pos}")
        
        if new_pos != current_pos:
            print("   ✅ Win32 API工作正常")
            
            # 恢复位置
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, -1, 0, 0, 0)
            return True
        else:
            print("   ❌ Win32 API移动失败")
            return False
            
    except Exception as e:
        print(f"   ❌ Win32 API测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 详细G-Hub诊断脚本")
    print("=" * 50)
    
    # 执行所有检查
    results = {}
    
    results['admin'] = check_admin_privileges()
    results['processes'] = check_ghub_processes()
    results['version'] = check_ghub_version()
    results['paths'] = test_device_paths()
    results['handle'] = test_device_handle()
    results['io_control'] = test_device_io_control()
    results['alternative'] = test_alternative_methods()
    
    # 总结报告
    print("\n📊 诊断总结")
    print("=" * 50)
    
    print(f"管理员权限: {'✅' if results['admin'] else '❌'}")
    print(f"G-Hub进程: {'✅' if results['processes'] else '❌'}")
    print(f"G-Hub版本: {'✅' if results['version'] else '❌'}")
    print(f"设备路径: {'✅' if results['paths'] else '❌'} ({len(results['paths'])} 个成功)")
    print(f"设备句柄: {'✅' if results['handle'] else '❌'}")
    print(f"IO控制: {'✅' if results['io_control'] else '❌'}")
    print(f"Win32替代: {'✅' if results['alternative'] else '❌'}")
    
    # 建议
    print("\n💡 建议:")
    if not results['admin']:
        print("   1. 以管理员权限运行")
    if not results['processes']:
        print("   2. 启动G-Hub软件")
    if not results['version']:
        print("   3. 安装正确版本的G-Hub (2021.3.9205)")
    if not results['io_control']:
        print("   4. 检查G-Hub设备驱动")
    if results['alternative']:
        print("   5. 可以使用Win32 API作为替代方案")

if __name__ == "__main__":
    main()
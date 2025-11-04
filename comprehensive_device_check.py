#!/usr/bin/env python3
"""
全面的 G-Hub 设备检查和诊断
"""
import ctypes
import ctypes.wintypes
import sys
import os
import subprocess
import winreg

# Windows API 常量
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = -1

def check_admin_privileges():
    """检查管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_logitech_devices():
    """检查连接的 Logitech 设备"""
    print("=== 检查 Logitech 设备 ===")
    
    # 通过 WMI 检查 USB 设备
    try:
        result = subprocess.run([
            'powershell', '-Command',
            'Get-WmiObject -Class Win32_PnPEntity | Where-Object {$_.Name -like "*Logitech*" -or $_.DeviceID -like "*VID_046D*"} | Select-Object Name, DeviceID, Status'
        ], capture_output=True, text=True, timeout=10)
        
        if result.stdout.strip():
            print("✅ 找到 Logitech 设备:")
            print(result.stdout)
        else:
            print("❌ 未找到 Logitech 设备")
            
    except Exception as e:
        print(f"❌ 检查设备时出错: {e}")

def check_ghub_processes():
    """检查 G-Hub 进程"""
    print("\n=== 检查 G-Hub 进程 ===")
    try:
        result = subprocess.run([
            'powershell', '-Command',
            'Get-Process -Name "*lghub*" -ErrorAction SilentlyContinue | Select-Object Name, Id, ProcessName'
        ], capture_output=True, text=True, timeout=10)
        
        if result.stdout.strip():
            print("✅ G-Hub 进程运行中:")
            print(result.stdout)
        else:
            print("❌ G-Hub 进程未运行")
            
    except Exception as e:
        print(f"❌ 检查进程时出错: {e}")

def test_device_paths():
    """测试不同的设备路径格式"""
    print("\n=== 测试设备路径 ===")
    
    # 标准 G-Hub GUID
    guids = [
        '{1abc05c0-c378-41b9-9cef-df1aba82b015}',  # 标准 G-Hub GUID
        '{1bc4b5a5-8d52-4136-9f9b-2c7cd1a1e6e6}',  # 备用 GUID
        '{4d1e55b2-f16f-11cf-88cb-001111000030}',  # HID GUID
    ]
    
    # 不同的路径格式
    path_formats = [
        '\\\\?\\ROOT#SYSTEM#000{i}#{guid}',
        '\\\\.\\ROOT#SYSTEM#000{i}#{guid}',
        '\\\\?\\ROOT#SYSTEM#{i:04d}#{guid}',
        '\\\\.\\ROOT#SYSTEM#{i:04d}#{guid}',
    ]
    
    for guid in guids:
        print(f"\n测试 GUID: {guid}")
        for path_format in path_formats:
            print(f"  路径格式: {path_format}")
            for i in range(10):
                path = path_format.format(i=i, guid=guid)
                try:
                    handle = ctypes.windll.kernel32.CreateFileW(
                        path,
                        GENERIC_READ | GENERIC_WRITE,
                        FILE_SHARE_READ | FILE_SHARE_WRITE,
                        None,
                        OPEN_EXISTING,
                        0,
                        None
                    )
                    
                    if handle != INVALID_HANDLE_VALUE:
                        print(f"    ✅ 成功: {path}")
                        ctypes.windll.kernel32.CloseHandle(handle)
                        return path  # 返回第一个成功的路径
                    else:
                        error = ctypes.windll.kernel32.GetLastError()
                        if error != 2:  # 不是 "文件未找到" 错误
                            print(f"    ❌ 失败: {path} (错误: {error})")
                            
                except Exception as e:
                    print(f"    ❌ 异常: {path} ({e})")
    
    return None

def check_registry_devices():
    """检查注册表中的设备信息"""
    print("\n=== 检查注册表设备信息 ===")
    
    try:
        # 检查设备枚举
        key_path = r"SYSTEM\CurrentControlSet\Enum\ROOT\SYSTEM"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    print(f"  找到设备: {subkey_name}")
                    
                    # 检查设备详细信息
                    device_key_path = f"{key_path}\\{subkey_name}"
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, device_key_path) as device_key:
                            try:
                                device_desc = winreg.QueryValueEx(device_key, "DeviceDesc")[0]
                                print(f"    描述: {device_desc}")
                            except:
                                pass
                            try:
                                class_guid = winreg.QueryValueEx(device_key, "ClassGUID")[0]
                                print(f"    类 GUID: {class_guid}")
                            except:
                                pass
                    except:
                        pass
                    
                    i += 1
                except OSError:
                    break
                    
    except Exception as e:
        print(f"❌ 检查注册表时出错: {e}")

def main():
    print("=== G-Hub 设备全面诊断 ===")
    print(f"管理员权限: {'是' if check_admin_privileges() else '否'}")
    
    if not check_admin_privileges():
        print("⚠️  建议以管理员权限运行此脚本")
    
    check_logitech_devices()
    check_ghub_processes()
    check_registry_devices()
    
    working_path = test_device_paths()
    
    if working_path:
        print(f"\n🎉 找到可用的设备路径: {working_path}")
    else:
        print("\n❌ 未找到可用的设备路径")
        print("\n可能的解决方案:")
        print("1. 确保 Logitech 鼠标已连接")
        print("2. 重启 G-Hub 软件")
        print("3. 重新插拔 Logitech 设备")
        print("4. 检查设备管理器中的设备状态")

if __name__ == "__main__":
    main()
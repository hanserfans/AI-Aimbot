#!/usr/bin/env python3
"""
G-Hub设备连接诊断脚本
详细检查G-Hub软件和设备连接状态
"""

import ctypes
import win32file
import ctypes.wintypes as wintypes
from ctypes import windll
import subprocess
import os
import time
import sys

def check_ghub_processes():
    """检查G-Hub相关进程"""
    print("🔍 检查G-Hub进程状态...")
    
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq lghub*'], 
                              capture_output=True, text=True, shell=True)
        
        if 'lghub' in result.stdout.lower():
            print("✅ G-Hub进程正在运行:")
            lines = result.stdout.split('\n')
            for line in lines:
                if 'lghub' in line.lower() and 'exe' in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        print(f"   {parts[0]} (PID: {parts[1]})")
            return True
        else:
            print("❌ 未找到G-Hub进程")
            return False
            
    except Exception as e:
        print(f"❌ 检查进程失败: {e}")
        return False

def check_ghub_services():
    """检查G-Hub相关服务"""
    print("\n🔧 检查G-Hub服务状态...")
    
    try:
        # 检查Logitech相关服务
        result = subprocess.run(['sc', 'query', 'type=', 'service', 'state=', 'all'], 
                              capture_output=True, text=True, shell=True)
        
        logitech_services = []
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            if 'logitech' in line.lower() or 'lghub' in line.lower():
                # 获取服务名
                if 'SERVICE_NAME:' in line:
                    service_name = line.split(':')[1].strip()
                    logitech_services.append(service_name)
        
        if logitech_services:
            print("✅ 找到Logitech服务:")
            for service in logitech_services:
                print(f"   {service}")
        else:
            print("⚠️  未找到Logitech相关服务")
            
    except Exception as e:
        print(f"❌ 检查服务失败: {e}")

def check_device_files():
    """检查G-Hub设备文件"""
    print("\n📁 检查G-Hub设备文件...")
    
    # 常见的G-Hub设备路径
    device_paths = [
        r"\\.\LGHUB",
        r"\\.\LGS",
        r"\\.\LogitechGaming",
        r"\\.\pipe\LGHubPipe",
    ]
    
    for device_path in device_paths:
        try:
            print(f"尝试访问: {device_path}")
            
            # 尝试打开设备文件
            handle = win32file.CreateFile(
                device_path,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            
            if handle != win32file.INVALID_HANDLE_VALUE:
                print(f"✅ 成功访问: {device_path}")
                win32file.CloseHandle(handle)
                return device_path
            else:
                print(f"❌ 无法访问: {device_path}")
                
        except Exception as e:
            print(f"❌ 访问 {device_path} 失败: {e}")
    
    print("❌ 未找到可访问的G-Hub设备文件")
    return None

def check_usb_devices():
    """检查USB设备"""
    print("\n🔌 检查USB设备...")
    
    try:
        # 使用wmic查询USB设备
        result = subprocess.run(['wmic', 'path', 'Win32_USBHub', 'get', 'DeviceID,Description'], 
                              capture_output=True, text=True, shell=True)
        
        if 'logitech' in result.stdout.lower():
            print("✅ 找到Logitech USB设备:")
            lines = result.stdout.split('\n')
            for line in lines:
                if 'logitech' in line.lower():
                    print(f"   {line.strip()}")
        else:
            print("⚠️  未找到Logitech USB设备")
            
    except Exception as e:
        print(f"❌ 检查USB设备失败: {e}")

def check_bluetooth_devices():
    """检查蓝牙设备"""
    print("\n📶 检查蓝牙设备...")
    
    try:
        # 使用PowerShell检查蓝牙设备
        ps_command = "Get-PnpDevice | Where-Object {$_.FriendlyName -like '*Logitech*' -or $_.FriendlyName -like '*G304*'} | Select-Object FriendlyName, Status"
        
        result = subprocess.run(['powershell', '-Command', ps_command], 
                              capture_output=True, text=True, shell=True)
        
        if result.stdout.strip():
            print("✅ 找到Logitech蓝牙设备:")
            print(result.stdout)
        else:
            print("⚠️  未找到Logitech蓝牙设备")
            
    except Exception as e:
        print(f"❌ 检查蓝牙设备失败: {e}")

def test_direct_device_access():
    """直接测试设备访问"""
    print("\n🧪 测试直接设备访问...")
    
    # 尝试不同的设备名称
    device_names = [
        "LGHUB",
        "LGS", 
        "LogitechGaming",
        "Logitech",
        "GHUB"
    ]
    
    for device_name in device_names:
        print(f"\n测试设备名称: {device_name}")
        
        try:
            # 添加mouse_driver到路径
            sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))
            
            # 导入设备初始化函数
            from MouseMove import device_initialize
            
            # 尝试初始化设备
            success = device_initialize(device_name)
            
            if success:
                print(f"✅ 设备 {device_name} 初始化成功!")
                return device_name
            else:
                print(f"❌ 设备 {device_name} 初始化失败")
                
        except Exception as e:
            print(f"❌ 测试设备 {device_name} 异常: {e}")
    
    print("❌ 所有设备名称测试失败")
    return None

def check_permissions():
    """检查权限"""
    print("\n🔐 检查权限状态...")
    
    try:
        # 检查是否以管理员权限运行
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        
        if is_admin:
            print("✅ 当前以管理员权限运行")
        else:
            print("⚠️  当前未以管理员权限运行")
            print("💡 建议以管理员权限重新运行脚本")
            
        return is_admin
        
    except Exception as e:
        print(f"❌ 检查权限失败: {e}")
        return False

def main():
    """主诊断函数"""
    print("🔍 G-Hub设备连接诊断工具")
    print("=" * 60)
    
    # 执行各项检查
    checks = [
        ("G-Hub进程检查", check_ghub_processes),
        ("G-Hub服务检查", check_ghub_services),
        ("权限检查", check_permissions),
        ("设备文件检查", check_device_files),
        ("USB设备检查", check_usb_devices),
        ("蓝牙设备检查", check_bluetooth_devices),
        ("直接设备访问测试", test_direct_device_access),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        try:
            result = check_func()
            results[check_name] = result
        except Exception as e:
            print(f"❌ {check_name}执行异常: {e}")
            results[check_name] = False
    
    # 显示诊断总结
    print("\n" + "="*60)
    print("📊 诊断结果总结:")
    print("="*60)
    
    for check_name, result in results.items():
        if isinstance(result, bool):
            status = "✅ 正常" if result else "❌ 异常"
        elif result is None:
            status = "⚠️  未找到"
        else:
            status = f"✅ 找到: {result}"
        
        print(f"{check_name}: {status}")
    
    # 提供建议
    print("\n💡 建议:")
    if not results.get("G-Hub进程检查", False):
        print("   1. 启动G-Hub软件")
    
    if not results.get("权限检查", False):
        print("   2. 以管理员权限运行脚本")
    
    if not results.get("USB设备检查", False) and not results.get("蓝牙设备检查", False):
        print("   3. 检查Logitech设备连接")
        print("   4. 确保设备已配对/插入")
    
    if not results.get("设备文件检查", False):
        print("   5. 重新安装G-Hub软件")
        print("   6. 检查G-Hub版本兼容性")

if __name__ == "__main__":
    main()
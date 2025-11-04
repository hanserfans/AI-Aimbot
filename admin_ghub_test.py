#!/usr/bin/env python3
"""
管理员权限G-Hub测试脚本
包含详细的错误诊断和多种控制代码测试
"""

import ctypes
import win32file
import ctypes.wintypes as wintypes
from ctypes import windll
import time
import subprocess
import os

def check_admin_privileges():
    """检查管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_ghub_processes():
    """获取G-Hub相关进程"""
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq lghub*'], 
                              capture_output=True, text=True)
        return result.stdout
    except:
        return "无法获取进程信息"

def clamp_char(value: int) -> int:
    return max(-128, min(127, value))

def _DeviceIoControl(devhandle, ioctl, inbuf, inbufsiz, outbuf, outbufsiz):
    DeviceIoControl_Fn = windll.kernel32.DeviceIoControl
    DeviceIoControl_Fn.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID
    ]
    DeviceIoControl_Fn.restype = wintypes.BOOL
    
    dwBytesReturned = wintypes.DWORD(0)
    lpBytesReturned = ctypes.byref(dwBytesReturned)
    status = DeviceIoControl_Fn(
        int(devhandle),
        ioctl,
        inbuf,
        inbufsiz,
        outbuf,
        outbufsiz,
        lpBytesReturned,
        None
    )
    return status, dwBytesReturned

class MOUSE_IO(ctypes.Structure):
    _fields_ = [
        ("button", ctypes.c_char),
        ("x", ctypes.c_char),
        ("y", ctypes.c_char),
        ("wheel", ctypes.c_char),
        ("unk1", ctypes.c_char)
    ]

def device_initialize(device_name: str):
    """初始化设备"""
    try:
        handle = win32file.CreateFileW(
            device_name,
            win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_ALWAYS,
            win32file.FILE_ATTRIBUTE_NORMAL,
            0
        )
        return handle
    except Exception as e:
        print(f"设备初始化失败 {device_name}: {e}")
        return None

def test_control_codes(handle):
    """测试不同的控制代码"""
    control_codes = [
        0x2a2010,  # 原始代码
        0x2a2000,  # 变体1
        0x2a2004,  # 变体2
        0x2a200c,  # 变体3
        0x2a2014,  # 变体4
        0x2a2018,  # 变体5
    ]
    
    print("\n🔍 测试不同的控制代码")
    print("-" * 40)
    
    # 创建测试数据
    io = MOUSE_IO()
    io.button = ctypes.c_char(b'\x00')
    io.x = ctypes.c_char(b'\x01')  # 微小移动
    io.y = ctypes.c_char(b'\x00')
    io.wheel = ctypes.c_char(b'\x00')
    io.unk1 = ctypes.c_char(b'\x00')
    
    for code in control_codes:
        print(f"测试控制代码: 0x{code:x}")
        status, bytes_returned = _DeviceIoControl(
            handle, 
            code,
            ctypes.c_void_p(ctypes.addressof(io)),
            ctypes.sizeof(io),
            None,
            0, 
        )
        
        if status:
            print(f"  ✅ 成功！返回字节: {bytes_returned.value}")
            return code
        else:
            error_code = ctypes.windll.kernel32.GetLastError()
            print(f"  ❌ 失败，错误代码: {error_code}")
    
    return None

def main():
    """主测试函数"""
    print("🔍 管理员权限G-Hub测试")
    print("=" * 50)
    
    # 检查管理员权限
    is_admin = check_admin_privileges()
    print(f"管理员权限: {'✅' if is_admin else '❌'}")
    
    if not is_admin:
        print("❌ 此脚本需要管理员权限运行")
        print("请右键点击PowerShell并选择'以管理员身份运行'")
        input("按Enter键退出...")
        return
    
    # 检查G-Hub进程
    print("\n🔍 检查G-Hub进程")
    ghub_processes = get_ghub_processes()
    print(ghub_processes)
    
    # 尝试初始化设备
    print("\n🔧 初始化LGHUB设备")
    handle = device_initialize("LGHUB")
    
    if not handle:
        print("❌ 无法初始化LGHUB设备")
        
        # 尝试标准路径
        print("\n🔧 尝试标准设备路径")
        for i in range(1, 5):
            devpath = f'\\??\\ROOT#SYSTEM#000{i}#' + '{1abc05c0-c378-41b9-9cef-df1aba82b015}'
            print(f"尝试: {devpath}")
            handle = device_initialize(devpath)
            if handle:
                print(f"✅ 成功初始化: {devpath}")
                break
    else:
        print(f"✅ LGHUB设备初始化成功，句柄: {handle}")
    
    if not handle:
        print("❌ 所有设备初始化都失败")
        input("按Enter键退出...")
        return
    
    # 测试不同的控制代码
    working_code = test_control_codes(handle)
    
    if working_code:
        print(f"\n🎯 找到工作的控制代码: 0x{working_code:x}")
        print("进行实际鼠标移动测试...")
        
        # 测试实际移动
        test_cases = [
            (0, 10, 0, 0, "右移10像素"),
            (0, -10, 0, 0, "左移10像素"),
            (0, 0, 10, 0, "下移10像素"),
            (0, 0, -10, 0, "上移10像素"),
        ]
        
        success_count = 0
        
        for button, x, y, wheel, description in test_cases:
            print(f"\n测试: {description}")
            
            io = MOUSE_IO()
            io.button = ctypes.c_char(button.to_bytes(1, 'little', signed=True))
            io.x = ctypes.c_char(x.to_bytes(1, 'little', signed=True))
            io.y = ctypes.c_char(y.to_bytes(1, 'little', signed=True))
            io.wheel = ctypes.c_char(wheel.to_bytes(1, 'little', signed=True))
            io.unk1 = ctypes.c_char(b'\x00')
            
            status, _ = _DeviceIoControl(
                handle, 
                working_code,
                ctypes.c_void_p(ctypes.addressof(io)),
                ctypes.sizeof(io),
                None,
                0, 
            )
            
            if status:
                print("  ✅ 成功")
                success_count += 1
            else:
                error_code = ctypes.windll.kernel32.GetLastError()
                print(f"  ❌ 失败，错误代码: {error_code}")
            
            time.sleep(1)
        
        print(f"\n📊 最终结果: {success_count}/{len(test_cases)} 成功")
        
    else:
        print("\n❌ 没有找到工作的控制代码")
        print("可能的原因:")
        print("  1. G-Hub版本不兼容")
        print("  2. 设备驱动问题")
        print("  3. 需要特殊的设备配置")
    
    # 清理
    try:
        win32file.CloseHandle(int(handle))
        print("\n✅ 设备句柄已关闭")
    except:
        print("\n⚠️  关闭设备句柄时出错")
    
    input("按Enter键退出...")

if __name__ == "__main__":
    main()
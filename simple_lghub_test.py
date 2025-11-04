#!/usr/bin/env python3
"""
简化的LGHUB测试脚本
直接使用LGHUB设备名，基于原始g-input实现
"""

import ctypes
import win32file
import ctypes.wintypes as wintypes
from ctypes import windll
import time

def clamp_char(value: int) -> int:
    """限制值到有符号字节范围"""
    return max(-128, min(127, value))

def _DeviceIoControl(devhandle, ioctl, inbuf, inbufsiz, outbuf, outbufsiz):
    """DeviceIoControl包装函数"""
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
    """原始g-input的MOUSE_IO结构"""
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
        print(f"设备初始化失败: {e}")
        return None

def call_mouse(handle, buffer: MOUSE_IO) -> bool:
    """发送鼠标输入到设备"""
    status, bytes_returned = _DeviceIoControl(
        handle, 
        0x2a2010,
        ctypes.c_void_p(ctypes.addressof(buffer)),
        ctypes.sizeof(buffer),
        None,
        0, 
    )
    
    if not status:
        error_code = ctypes.windll.kernel32.GetLastError()
        print(f"DeviceIoControl失败，错误代码: {error_code}")
    else:
        print(f"DeviceIoControl成功，返回字节: {bytes_returned.value}")
    
    return status

def mouse_move(handle, button: int, x: int, y: int, wheel: int) -> bool:
    """发送鼠标移动命令"""
    if not handle:
        print("❌ 无效的设备句柄")
        return False
    
    x_clamped = clamp_char(x)
    y_clamped = clamp_char(y)
    btn_byte = clamp_char(button)
    wheel_byte = clamp_char(wheel)

    print(f"发送命令: button={btn_byte}, x={x_clamped}, y={y_clamped}, wheel={wheel_byte}")

    io = MOUSE_IO()
    # 使用原始g-input的方式 - 用ctypes.c_char包装bytes
    io.button = ctypes.c_char(btn_byte.to_bytes(1, 'little', signed=True))
    io.x = ctypes.c_char(x_clamped.to_bytes(1, 'little', signed=True))
    io.y = ctypes.c_char(y_clamped.to_bytes(1, 'little', signed=True))
    io.wheel = ctypes.c_char(wheel_byte.to_bytes(1, 'little', signed=True))
    io.unk1 = ctypes.c_char(b'\x00')

    print(f"MOUSE_IO结构:")
    print(f"  button: {io.button.value}")
    print(f"  x: {io.x.value}")
    print(f"  y: {io.y.value}")
    print(f"  wheel: {io.wheel.value}")
    print(f"  unk1: {io.unk1.value}")

    return call_mouse(handle, io)

def check_admin_privileges():
    """检查管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    """主测试函数"""
    print("🔍 简化LGHUB测试")
    print("=" * 40)
    
    # 检查管理员权限
    is_admin = check_admin_privileges()
    print(f"管理员权限: {'✅' if is_admin else '❌'}")
    
    # 尝试初始化LGHUB设备
    print("\n🔧 初始化LGHUB设备")
    handle = device_initialize("LGHUB")
    
    if handle:
        print(f"✅ 设备初始化成功，句柄: {handle}")
        
        # 测试基本移动
        print("\n🎯 测试鼠标移动")
        
        test_cases = [
            (0, 1, 0, 0, "微小右移"),
            (0, -1, 0, 0, "微小左移"),
            (0, 0, 1, 0, "微小下移"),
            (0, 0, -1, 0, "微小上移"),
        ]
        
        success_count = 0
        
        for button, x, y, wheel, description in test_cases:
            print(f"\n测试: {description}")
            try:
                success = mouse_move(handle, button, x, y, wheel)
                if success:
                    print(f"   ✅ 成功")
                    success_count += 1
                else:
                    print(f"   ❌ 失败")
                time.sleep(0.5)  # 延迟观察效果
            except Exception as e:
                print(f"   ❌ 异常: {e}")
        
        print(f"\n📊 测试结果: {success_count}/{len(test_cases)} 成功")
        
        # 清理
        try:
            win32file.CloseHandle(int(handle))
            print("✅ 设备句柄已关闭")
        except:
            print("⚠️  关闭设备句柄时出错")
            
    else:
        print("❌ 设备初始化失败")
        print("可能的原因:")
        print("  1. G-Hub未运行")
        print("  2. 需要管理员权限")
        print("  3. 设备路径不正确")
        print("  4. G-Hub版本不兼容")

if __name__ == "__main__":
    main()
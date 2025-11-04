#!/usr/bin/env python3
"""
完全基于原始g-input实现的测试脚本
"""

import ctypes
import win32file
import ctypes.wintypes as wintypes
from ctypes import windll
import time

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

handle = 0
found = False

def device_initialize(device_name: str) -> bool:
    global handle
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
    except Exception as e:
        print("Error initializing device:", e)
        return False
    return bool(handle)

def mouse_open() -> bool:
    global found
    global handle

    if found and handle:
        return True

    # 首先尝试LGHUB设备名
    if device_initialize("LGHUB"):
        found = True
        print("✅ 使用LGHUB设备名初始化成功")
        return True

    # 然后尝试标准路径
    for i in range(1, 10):
        devpath = f'\\??\\ROOT#SYSTEM#000{i}#' + '{1abc05c0-c378-41b9-9cef-df1aba82b015}'
        print(f"尝试设备路径: {devpath}")
        if device_initialize(devpath):
            found = True
            print(f"✅ 使用路径 {devpath} 初始化成功")
            return True
        if i == 10:
            print('Failed to initialize device.')

    return False

def call_mouse(buffer: MOUSE_IO) -> bool:
    global handle
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
        print(f"DeviceIoControl failed to send mouse input. Error code: {error_code}")
    else:
        print(f"✅ DeviceIoControl成功，返回字节: {bytes_returned.value}")
    return status

def mouse_close() -> None:
    global handle
    if handle:
        win32file.CloseHandle(int(handle))
        handle = 0

def mouse_move(button: int, x: int, y: int, wheel: int) -> bool:
    """
    Sends a single relative mouse input to the GHUB device.
    """
    global handle

    x_clamped = clamp_char(x)
    y_clamped = clamp_char(y)
    btn_byte   = clamp_char(button)
    wheel_byte = clamp_char(wheel)

    print(f"发送命令: button={btn_byte}, x={x_clamped}, y={y_clamped}, wheel={wheel_byte}")

    io = MOUSE_IO()
    # c_char expects a bytes object of length 1 or an int in the range -128..127:
    io.button = ctypes.c_char(btn_byte.to_bytes(1, 'little', signed=True))
    io.x      = ctypes.c_char(x_clamped.to_bytes(1, 'little', signed=True))
    io.y      = ctypes.c_char(y_clamped.to_bytes(1, 'little', signed=True))
    io.wheel  = ctypes.c_char(wheel_byte.to_bytes(1, 'little', signed=True))
    io.unk1   = ctypes.c_char(b'\x00')

    success = call_mouse(io)
    if not success:
        print("❌ 鼠标输入失败，尝试重新初始化设备")
        mouse_close()
        if not mouse_open():
            print("Failed to reinitialize device after error.")
            return False
    
    return success

def check_admin_privileges():
    """检查管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    """主测试函数"""
    print("🔍 完全基于原始G-Input的测试")
    print("=" * 50)
    
    # 检查管理员权限
    is_admin = check_admin_privileges()
    print(f"管理员权限: {'✅' if is_admin else '❌'}")
    if not is_admin:
        print("⚠️  建议以管理员权限运行以获得最佳结果")
    
    # 尝试打开鼠标设备
    print("\n🔧 初始化G-Hub设备")
    if not mouse_open():
        print("❌ Ghub is not open or something else is wrong")
        return
    
    print(f"✅ 设备初始化成功，句柄: {handle}")
    
    # 测试基本移动
    print("\n🎯 测试鼠标移动")
    
    test_cases = [
        (0, 5, 0, 0, "右移5像素"),
        (0, -5, 0, 0, "左移5像素"),
        (0, 0, 5, 0, "下移5像素"),
        (0, 0, -5, 0, "上移5像素"),
        (1, 0, 0, 0, "左键点击"),
        (2, 0, 0, 0, "右键点击"),
    ]
    
    success_count = 0
    
    for button, x, y, wheel, description in test_cases:
        print(f"\n测试: {description}")
        try:
            success = mouse_move(button, x, y, wheel)
            if success:
                print(f"   ✅ 成功")
                success_count += 1
            else:
                print(f"   ❌ 失败")
            time.sleep(1)  # 延迟观察效果
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    print(f"\n📊 测试结果: {success_count}/{len(test_cases)} 成功")
    
    # 清理
    mouse_close()
    print("✅ 设备句柄已关闭")

if __name__ == "__main__":
    main()
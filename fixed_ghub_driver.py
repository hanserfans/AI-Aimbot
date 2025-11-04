#!/usr/bin/env python3
"""
基于原始g-input实现的修复版G-Hub驱动
解决了c_char赋值和函数签名问题
"""

import ctypes
import win32file
import ctypes.wintypes as wintypes
from ctypes import windll

def clamp_char(value: int) -> int:
    """将值限制在c_char范围内 (-128 到 127)"""
    return max(-128, min(127, value))

def _DeviceIoControl(devhandle, ioctl, inbuf, inbufsiz, outbuf, outbufsiz):
    """Windows DeviceIoControl API包装"""
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
    """G-Hub鼠标输入结构"""
    _fields_ = [
        ("button", ctypes.c_char),
        ("x", ctypes.c_char),
        ("y", ctypes.c_char),
        ("wheel", ctypes.c_char),
        ("unk1", ctypes.c_char)
    ]

# 全局变量
handle = 0
found = False

def device_initialize(device_name: str) -> bool:
    """初始化G-Hub设备"""
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
        return False
    return bool(handle)

def mouse_open() -> bool:
    """打开G-Hub鼠标设备"""
    global found, handle

    if found and handle:
        return True

    for i in range(1, 10):
        devpath = f'\\??\\ROOT#SYSTEM#000{i}#' + '{1abc05c0-c378-41b9-9cef-df1aba82b015}'
        if device_initialize(devpath):
            found = True
            return True
        if i == 10:
            print('Failed to initialize G-Hub device.')

    return False

def call_mouse(buffer: MOUSE_IO) -> bool:
    """发送鼠标输入到G-Hub设备"""
    global handle
    status, _ = _DeviceIoControl(
        handle, 
        0x2a2010,
        ctypes.c_void_p(ctypes.addressof(buffer)),
        ctypes.sizeof(buffer),
        None,
        0, 
    )
    if not status:
        print("DeviceIoControl failed to send mouse input.")
    return status

def mouse_close() -> None:
    """关闭G-Hub设备"""
    global handle
    if handle:
        win32file.CloseHandle(int(handle))
        handle = 0

def mouse_move(button: int, x: int, y: int, wheel: int) -> None:
    """
    发送鼠标移动命令到G-Hub设备
    使用原始实现的正确c_char赋值方式
    """
    global handle

    x_clamped = clamp_char(x)
    y_clamped = clamp_char(y)
    btn_byte = clamp_char(button)
    wheel_byte = clamp_char(wheel)

    io = MOUSE_IO()
    # 关键修复：使用to_bytes方法正确创建c_char
    io.button = ctypes.c_char(btn_byte.to_bytes(1, 'little', signed=True))
    io.x = ctypes.c_char(x_clamped.to_bytes(1, 'little', signed=True))
    io.y = ctypes.c_char(y_clamped.to_bytes(1, 'little', signed=True))
    io.wheel = ctypes.c_char(wheel_byte.to_bytes(1, 'little', signed=True))
    io.unk1 = ctypes.c_char(b'\x00')

    if not call_mouse(io):
        mouse_close()
        if not mouse_open():
            print("Failed to reinitialize device after error.")

def ghub_move(x: int, y: int) -> None:
    """
    简化的G-Hub移动函数
    兼容现有代码的接口
    """
    mouse_move(0, x, y, 0)

def ghub_click(button: str = "left") -> None:
    """G-Hub点击函数"""
    button_map = {
        "left": 1,
        "right": 2,
        "middle": 4
    }
    
    button_code = button_map.get(button.lower(), 1)
    
    # 按下
    mouse_move(button_code, 0, 0, 0)
    # 释放
    mouse_move(0, 0, 0, 0)

def test_fixed_driver():
    """测试修复后的驱动"""
    print("=== 测试修复后的G-Hub驱动 ===")
    
    # 连接设备
    if not mouse_open():
        print("✗ 无法连接G-Hub设备")
        return False
    
    print("✓ G-Hub设备连接成功")
    
    # 测试移动
    test_movements = [
        (1, 0),    # 右移1
        (0, 1),    # 下移1
        (-1, 0),   # 左移1
        (0, -1),   # 上移1
        (5, 5),    # 对角移动
        (-5, -5),  # 反向对角
        (10, 0),   # 较大移动
        (0, 10),
        (-10, 0),
        (0, -10),
        (20, 20),  # 大移动
        (-20, -20),
    ]
    
    success_count = 0
    for i, (x, y) in enumerate(test_movements):
        try:
            ghub_move(x, y)
            print(f"✓ 测试 {i+1}: 移动 ({x}, {y}) - 成功")
            success_count += 1
        except Exception as e:
            print(f"✗ 测试 {i+1}: 移动 ({x}, {y}) - 失败: {e}")
        
        import time
        time.sleep(0.1)
    
    # 关闭设备
    mouse_close()
    
    success_rate = (success_count / len(test_movements)) * 100
    print(f"\n成功率: {success_count}/{len(test_movements)} ({success_rate:.1f}%)")
    
    return success_rate > 90

if __name__ == "__main__":
    print("修复后的G-Hub驱动测试")
    print("=" * 50)
    
    success = test_fixed_driver()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ 驱动修复成功！可以集成到主项目中")
    else:
        print("✗ 驱动仍有问题，需要进一步调试")
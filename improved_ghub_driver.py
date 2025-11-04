#!/usr/bin/env python3
"""
Improved G-Hub Driver Implementation
Based on the original GHUB Mouse Exploit by Oliver-1-1
Refined and optimized for better reliability and performance
"""

import ctypes
import ctypes.wintypes as wintypes
from ctypes import windll
import win32file
import win32api
from time import sleep
import sys

# Global variables
handle = 0
found = False

class MOUSE_IO(ctypes.Structure):
    """Mouse IO structure for G-Hub communication"""
    _fields_ = [
        ("unk1", ctypes.c_uint8),
        ("button", ctypes.c_uint8), 
        ("x", ctypes.c_int8),
        ("y", ctypes.c_int8),
        ("wheel", ctypes.c_int8),
        ("unk2", ctypes.c_uint8)
    ]

def _DeviceIoControl(devhandle, ioctl, inbuf, inbufsiz, outbuf, outbufsiz):
    """
    DeviceIoControl function wrapper
    See: http://msdn.microsoft.com/en-us/library/aa363216(v=vs.85).aspx
    """
    DeviceIoControl_Fn = windll.kernel32.DeviceIoControl
    DeviceIoControl_Fn.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID
    ]
    DeviceIoControl_Fn.restype = wintypes.BOOL
    
    dwBytesReturned = wintypes.DWORD(0)
    status = DeviceIoControl_Fn(
        devhandle, ioctl, inbuf, inbufsiz, outbuf, outbufsiz,
        ctypes.byref(dwBytesReturned), None
    )
    return status, dwBytesReturned.value

def mouse_open() -> bool:
    """Open connection to G-Hub mouse driver"""
    global handle, found
    
    try:
        handle = win32file.CreateFile(
            "\\\\.\\HidHide",
            0x80000000 | 0x40000000,  # GENERIC_READ | GENERIC_WRITE
            0x00000001 | 0x00000002,  # FILE_SHARE_READ | FILE_SHARE_WRITE
            None,
            0x00000003,  # OPEN_EXISTING
            0,
            None
        )
        
        if handle == -1:
            print("Failed to open HidHide device")
            return False
            
        found = True
        print("Successfully connected to G-Hub driver")
        return True
        
    except Exception as e:
        print(f"Error opening G-Hub device: {e}")
        return False

def call_mouse(buffer) -> bool:
    """Send mouse command to G-Hub driver"""
    global handle
    
    try:
        status, bytes_returned = _DeviceIoControl(
            handle, 0x2a2010, 
            ctypes.c_void_p(ctypes.addressof(buffer)), 
            ctypes.sizeof(buffer),
            None, 0
        )
        return status != 0
    except Exception as e:
        print(f"Error calling mouse: {e}")
        return False

def mouse_close() -> None:
    """Close G-Hub mouse driver connection"""
    global handle, found
    
    try:
        if handle and handle != -1:
            win32file.CloseHandle(int(handle))
        handle = 0
        found = False
        print("G-Hub driver connection closed")
    except Exception as e:
        print(f"Error closing mouse: {e}")

def clamp_to_int8(value: int) -> int:
    """Clamp value to signed 8-bit integer range (-128 to 127)"""
    return max(-128, min(127, value))

def mouse_move(button: int, x: int, y: int, wheel: int) -> bool:
    """
    Move mouse using G-Hub driver
    
    Args:
        button: Mouse button state (0=none, 1=left, 2=right, 4=middle)
        x: X movement (-128 to 127)
        y: Y movement (-128 to 127) 
        wheel: Wheel movement (-128 to 127)
    
    Returns:
        bool: True if successful, False otherwise
    """
    global handle
    
    if not found or handle == 0:
        print("G-Hub driver not connected")
        return False
    
    # Clamp values to valid range
    x = clamp_to_int8(x)
    y = clamp_to_int8(y)
    wheel = clamp_to_int8(wheel)
    
    # Create mouse IO structure
    io = MOUSE_IO()
    io.unk1 = 0
    io.button = button & 0xFF
    io.x = x
    io.y = y
    io.wheel = wheel
    io.unk2 = 0
    
    # Send command
    success = call_mouse(io)
    
    if not success:
        print("Mouse command failed, attempting to reconnect...")
        mouse_close()
        if mouse_open():
            success = call_mouse(io)
    
    return success

def ghub_move(x: int, y: int) -> bool:
    """
    Simple mouse movement function (compatible with existing code)
    
    Args:
        x: X movement
        y: Y movement
    
    Returns:
        bool: True if successful
    """
    return mouse_move(0, x, y, 0)

def mouse_click(button: int, duration: float = 0.1) -> bool:
    """
    Click mouse button
    
    Args:
        button: Button to click (1=left, 2=right, 4=middle)
        duration: Click duration in seconds
    
    Returns:
        bool: True if successful
    """
    # Press button
    success1 = mouse_move(button, 0, 0, 0)
    sleep(duration)
    # Release button
    success2 = mouse_move(0, 0, 0, 0)
    
    return success1 and success2

def test_driver():
    """Test the G-Hub driver functionality"""
    print("=== G-Hub Driver Test ===")
    
    # Test connection
    if not mouse_open():
        print("❌ Failed to connect to G-Hub driver")
        return False
    
    print("✅ Connected to G-Hub driver")
    
    # Test basic movement
    print("Testing basic movement...")
    movements = [
        (1, 0), (-1, 0), (0, 1), (0, -1),  # Small movements
        (5, 0), (-5, 0), (0, 5), (0, -5),  # Medium movements
        (10, 10), (-10, -10)               # Diagonal movements
    ]
    
    success_count = 0
    for x, y in movements:
        if ghub_move(x, y):
            success_count += 1
            print(f"✅ Move ({x}, {y}) - Success")
        else:
            print(f"❌ Move ({x}, {y}) - Failed")
        sleep(0.1)
    
    print(f"Movement test: {success_count}/{len(movements)} successful")
    
    # Test click
    print("Testing mouse click...")
    if mouse_click(1):  # Left click
        print("✅ Mouse click - Success")
    else:
        print("❌ Mouse click - Failed")
    
    mouse_close()
    
    success_rate = (success_count / len(movements)) * 100
    print(f"Overall success rate: {success_rate:.1f}%")
    
    return success_rate > 80

if __name__ == "__main__":
    # Run test
    if test_driver():
        print("\n🎉 G-Hub driver is working properly!")
    else:
        print("\n⚠️  G-Hub driver needs debugging")
        
    # Interactive test mode
    print("\nPress 'q' to quit, or any other key to test movement...")
    while True:
        try:
            key = input().strip().lower()
            if key == 'q':
                break
            
            if not found:
                mouse_open()
            
            # Test small movement
            if ghub_move(2, 0):
                print("✅ Test movement successful")
            else:
                print("❌ Test movement failed")
                
        except KeyboardInterrupt:
            break
    
    mouse_close()
    print("Test completed.")
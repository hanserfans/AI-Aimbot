"""
Simplified Mouse Movement Module using direct g-input approach
直接使用g-input方式的简化鼠标移动模块
"""

import sys
import os
import ctypes
import win32file
import ctypes.wintypes as wintypes
from ctypes import windll

# Add g-input path to system path
g_input_path = os.path.join(os.path.dirname(__file__), 'g-input-main', 'g-input-main')
sys.path.insert(0, g_input_path)

def clamp_char(value: int) -> int:
    """Clamp value to signed char range (-128 to 127)"""
    return max(-128, min(127, value))

def _DeviceIoControl(devhandle, ioctl, inbuf, inbufsiz, outbuf, outbufsiz):
    """Direct DeviceIoControl implementation"""
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
    """Mouse input structure matching g-input format"""
    _fields_ = [
        ("button", ctypes.c_char),
        ("x", ctypes.c_char),
        ("y", ctypes.c_char),
        ("wheel", ctypes.c_char),
        ("unk1", ctypes.c_char)
    ]

class MouseMove:
    def __init__(self):
        self.handle = 0
        self.found = False
        self.initialized = False
        
        # Try to initialize
        self.initialized = self._mouse_open()
        if self.initialized:
            print("G-Hub mouse initialized successfully")
        else:
            print("Failed to initialize G-Hub mouse")
    
    def _device_initialize(self, device_name: str) -> bool:
        """Initialize specific device"""
        try:
            handle = win32file.CreateFileW(
                device_name,
                0x40000000 | 0x80000000,  # GENERIC_READ | GENERIC_WRITE
                0,  # No sharing
                None,  # Default security
                3,  # OPEN_EXISTING
                0,  # No flags
                None  # No template
            )
            
            if handle != -1:  # INVALID_HANDLE_VALUE
                self.handle = handle
                self.found = True
                return True
        except Exception as e:
            print(f"Device initialization failed for {device_name}: {e}")
        
        return False
    
    def _find_ghub_device(self):
        """Find and initialize G-Hub mouse device - Fixed to ROOT\\SYSTEM\\0004"""
        guid = '{1abc05c0-c378-41b9-9cef-df1aba82b015}'
        
        # 固定使用已知工作的设备 ROOT\SYSTEM\0004
        device_num = "0004"
        print(f"Using fixed G-Hub device: ROOT\\SYSTEM\\{device_num}")
        
        # 使用已知工作的设备路径格式
        device_paths = [
            f"\\\\?\\ROOT#SYSTEM#{device_num}#{guid}",  # 这是工作的格式
            f"\\\\.\\ROOT#SYSTEM#{device_num}#{guid}",
            f"\\\\??\\\\ROOT#SYSTEM#{device_num}#{guid}",
        ]
        
        for device_name in device_paths:
            print(f"Trying device path: {device_name}")
            if self._device_initialize(device_name):
                print(f"✅ Successfully connected to G-Hub device: ROOT\\SYSTEM\\{device_num}")
                return True
        
        print(f"❌ Failed to connect to fixed G-Hub device: ROOT\\SYSTEM\\{device_num}")
        return False
    
    def _mouse_open(self) -> bool:
        """Open G-Hub mouse device"""
        # 直接使用固定的G-Hub设备
        if self._find_ghub_device():
            return True
        
        print('❌ Failed to initialize G-Hub device.')
        return False
    
    def _call_mouse(self, buffer: MOUSE_IO) -> bool:
        """Send mouse input to device"""
        if not self.handle:
            return False
            
        status, _ = _DeviceIoControl(
            self.handle, 
            0x2a2010,
            ctypes.c_void_p(ctypes.addressof(buffer)),
            ctypes.sizeof(buffer),
            None,
            0, 
        )
        if not status:
            print("DeviceIoControl failed to send mouse input.")
        return status
    
    def move_mouse(self, x, y):
        """
        Move mouse using G-Hub direct approach with exact g-input format
        """
        if not self.initialized:
            return False
            
        try:
            # Clamp values to signed char range and ensure they are integers
            x_clamped = int(clamp_char(int(x)))
            y_clamped = int(clamp_char(int(y)))
            btn_byte = int(clamp_char(0))  # No button
            wheel_byte = int(clamp_char(0))  # No wheel
            
            # Create MOUSE_IO structure with exact format
            io = MOUSE_IO()
            io.button = ctypes.c_char(btn_byte.to_bytes(1, 'little', signed=True))
            io.x = ctypes.c_char(x_clamped.to_bytes(1, 'little', signed=True))
            io.y = ctypes.c_char(y_clamped.to_bytes(1, 'little', signed=True))
            io.wheel = ctypes.c_char(wheel_byte.to_bytes(1, 'little', signed=True))
            io.unk1 = ctypes.c_char(b'\x00')
            
            # Send mouse input
            if not self._call_mouse(io):
                self.close()
                if not self._mouse_open():
                    print("Failed to reinitialize device after error.")
                    return False
            
            return True
        except Exception as e:
            print(f"Mouse move failed: {e}")
            return False

    def click_mouse(self, button_type="left"):
        """
        Click mouse button using G-Hub direct approach
        button_type: "left" (1), "right" (2), "middle" (4)
        """
        if not self.initialized:
            return False
            
        try:
            # Map button types to values
            button_map = {
                "left": 1,
                "right": 2, 
                "middle": 4
            }
            
            button_value = button_map.get(button_type.lower(), 1)
            
            # Press button (button down)
            btn_byte = int(clamp_char(button_value))
            
            # Create MOUSE_IO structure for button press
            io = MOUSE_IO()
            io.button = ctypes.c_char(btn_byte.to_bytes(1, 'little', signed=True))
            io.x = ctypes.c_char(int(clamp_char(0)).to_bytes(1, 'little', signed=True))
            io.y = ctypes.c_char(int(clamp_char(0)).to_bytes(1, 'little', signed=True))
            io.wheel = ctypes.c_char(int(clamp_char(0)).to_bytes(1, 'little', signed=True))
            io.unk1 = ctypes.c_char(b'\x00')
            
            # Send button press
            if not self._call_mouse(io):
                return False
            
            # Small delay between press and release
            import time
            time.sleep(0.01)
            
            # Release button (button up)
            io.button = ctypes.c_char(int(clamp_char(0)).to_bytes(1, 'little', signed=True))
            
            # Send button release
            if not self._call_mouse(io):
                return False
            
            return True
        except Exception as e:
            print(f"Mouse click failed: {e}")
            return False
    
    def close(self):
        """Close mouse connection"""
        if self.handle:
            try:
                win32file.CloseHandle(int(self.handle))
                self.handle = 0
                self.found = False
                self.initialized = False
                print("G-Hub mouse closed")
            except Exception as e:
                print(f"Failed to close G-Hub mouse: {e}")

# Movement correction factor optimized for DPI 1600 (专门针对小幅移动优化)
MOVEMENT_CORRECTION_FACTOR = 1.022  # Optimized for 1600 DPI × 0.19 sensitivity (eDPI: 304)

# Adaptive correction system (optional)
USE_ADAPTIVE_CORRECTION = True  # Set to False to use fixed correction factor
adaptive_correction_instance = None

# Global mouse instance
mouse_instance = None

def initialize_mouse():
    """Initialize the global mouse instance"""
    global mouse_instance, adaptive_correction_instance, USE_ADAPTIVE_CORRECTION
    if mouse_instance is None:
        mouse_instance = MouseMove()
    
    # Initialize adaptive correction if enabled
    if USE_ADAPTIVE_CORRECTION and adaptive_correction_instance is None:
        try:
            import sys
            import os
            # Add the parent directory to path to import adaptive correction
            parent_dir = os.path.dirname(os.path.dirname(__file__))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            from improved_adaptive_correction import ImprovedAdaptiveCorrection
            adaptive_correction_instance = ImprovedAdaptiveCorrection(MOVEMENT_CORRECTION_FACTOR)
            print("✅ 自适应校正系统已启用")
        except ImportError as e:
            print(f"⚠️ 自适应校正系统导入失败，使用固定校正因子: {e}")
            USE_ADAPTIVE_CORRECTION = False
    
    return mouse_instance._mouse_open()

def move_mouse(x, y):
    """Global function to move mouse"""
    global mouse_instance
    if mouse_instance is None:
        initialize_mouse()
    
    if mouse_instance and mouse_instance.initialized:
        return mouse_instance.move_mouse(x, y)
    return False

def click_mouse(button_type="left"):
    """Global function to click mouse"""
    global mouse_instance
    if mouse_instance is None:
        initialize_mouse()
    
    if mouse_instance and mouse_instance.initialized:
        return mouse_instance.click_mouse(button_type)
    return False

def close_mouse():
    """Global function to close mouse"""
    global mouse_instance
    if mouse_instance:
        mouse_instance.close()
        mouse_instance = None

# Alias for compatibility with existing code
def ghub_move(x, y):
    """
    Move mouse using G-Hub with correction factor or adaptive correction
    使用G-Hub移动鼠标，应用校正因子或自适应校正
    """
    global mouse_instance, adaptive_correction_instance
    if mouse_instance is None or not mouse_instance._mouse_open():
        return False
    
    # Use adaptive correction if available and enabled
    if USE_ADAPTIVE_CORRECTION and adaptive_correction_instance is not None:
        try:
            # Initialize adaptive correction if needed
            if not adaptive_correction_instance.mouse_initialized:
                adaptive_correction_instance.mouse_initialized = True
            
            # Use adaptive correction system
            return adaptive_correction_instance.stable_move(x, y)
        except Exception as e:
            print(f"⚠️ 自适应校正失败，回退到固定校正: {e}")
            # Fall back to fixed correction factor
    
    # Apply fixed correction factor to compensate for G-Hub scaling
    corrected_x = x * MOVEMENT_CORRECTION_FACTOR
    corrected_y = y * MOVEMENT_CORRECTION_FACTOR
    
    return mouse_instance.move_mouse(corrected_x, corrected_y)

def ghub_click(button_type="left"):
    """Alias for click_mouse function for compatibility"""
    return click_mouse(button_type)

def get_adaptive_correction_report():
    """获取自适应校正系统的性能报告"""
    global adaptive_correction_instance
    if USE_ADAPTIVE_CORRECTION and adaptive_correction_instance is not None:
        return adaptive_correction_instance.get_performance_report()
    else:
        return "自适应校正系统未启用或未初始化"

def set_adaptive_correction(enabled: bool):
    """启用或禁用自适应校正系统"""
    global USE_ADAPTIVE_CORRECTION
    USE_ADAPTIVE_CORRECTION = enabled
    if enabled:
        print("✅ 自适应校正系统已启用")
    else:
        print("⚠️ 自适应校正系统已禁用，使用固定校正因子")

def save_adaptive_calibration(filename=None):
    """保存自适应校正的校准数据"""
    global adaptive_correction_instance
    if USE_ADAPTIVE_CORRECTION and adaptive_correction_instance is not None:
        if filename:
            adaptive_correction_instance.save_calibration(filename)
        else:
            adaptive_correction_instance.save_calibration()
        return True
    else:
        print("自适应校正系统未启用，无法保存校准数据")
        return False

# Auto-initialize when module is imported
if __name__ != "__main__":
    initialize_mouse()
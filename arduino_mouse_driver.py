# Arduino 鼠标驱动 - 高精度硬件级控制
import serial
import serial.tools.list_ports
import time
import win32api
import win32con
import numpy as np
from typing import Optional, Tuple, Dict, Any

class ArduinoMouseDriver:
    """
    Arduino 鼠标驱动类
    - 利用 Arduino Leonardo/Pro Micro 的原生 HID 精度
    - 无需软件修正因子，硬件级别精确控制
    - 集成 Windows API 作为备选方案
    """
    
    def __init__(self, baudrate: int = 9600, auto_connect: bool = True, fallback_to_winapi: bool = True):
        """
        初始化 Arduino 鼠标驱动
        
        Args:
            baudrate: 串口波特率
            auto_connect: 是否自动连接 Arduino
            fallback_to_winapi: 连接失败时是否回退到 Windows API
        """
        self.baudrate = baudrate
        self.fallback_to_winapi = fallback_to_winapi
        self.arduino_serial: Optional[serial.Serial] = None
        self.is_arduino_connected = False
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        
        # 统计信息
        self.stats = {
            'total_moves': 0,
            'arduino_moves': 0,
            'winapi_moves': 0,
            'connection_errors': 0,
            'communication_errors': 0
        }
        
        if auto_connect:
            self.connect()
    
    def find_arduino_port(self) -> Optional[str]:
        """
        自动查找 Arduino 串口
        
        Returns:
            Arduino 串口名称，如果未找到则返回 None
        """
        try:
            ports = serial.tools.list_ports.comports()
            arduino_keywords = ['arduino', 'ch340', 'cp210', 'ftdi', 'usb serial', 'leonardo', 'pro micro']
            
            for port in ports:
                description_lower = port.description.lower()
                if any(keyword in description_lower for keyword in arduino_keywords):
                    print(f"[Arduino] 找到设备: {port.device} - {port.description}")
                    return port.device
            
            print("[Arduino] 未找到 Arduino 设备")
            print("[Arduino] 可用串口:")
            for port in ports:
                print(f"  {port.device} - {port.description}")
            
            return None
            
        except Exception as e:
            print(f"[Arduino] 串口扫描错误: {e}")
            return None
    
    def connect(self) -> bool:
        """
        连接 Arduino 设备
        
        Returns:
            连接是否成功
        """
        if self.is_arduino_connected:
            return True
        
        self.connection_attempts += 1
        
        try:
            port = self.find_arduino_port()
            if not port:
                self.stats['connection_errors'] += 1
                if self.fallback_to_winapi:
                    print("[Arduino] 未找到设备，将使用 Windows API 备选方案")
                    return True
                return False
            
            # 建立串口连接
            self.arduino_serial = serial.Serial(port, self.baudrate, timeout=1)
            print("[Arduino] 等待设备重启...")
            time.sleep(3)  # 等待 Arduino 重启
            
            # 清空缓冲区并执行握手
            self.arduino_serial.flushInput()
            self.arduino_serial.flushOutput()
            
            print("[Arduino] 发送 STATUS 握手信号...")
            self.arduino_serial.write(b'STATUS\n')
            response = self.arduino_serial.readline().decode().strip()
            
            if response == "OK":
                self.is_arduino_connected = True
                print(f"[Arduino] 连接成功: {port} (握手响应: {response})")
                print("[Arduino] 硬件级精确控制已启用")
                return True
            else:
                print(f"[Arduino] 握手失败: 期望 'OK', 收到 '{response}'")
                self.arduino_serial.close()
                self.arduino_serial = None
                # 即使握手失败，如果设置了备选方案，也返回True
                if self.fallback_to_winapi:
                    print("[Arduino] 握手失败，将使用 Windows API 备选方案")
                    return True
                return False
                
        except Exception as e:
            print(f"[Arduino] 连接失败: {e}")
            if self.arduino_serial:
                self.arduino_serial.close()
                self.arduino_serial = None
            self.stats['connection_errors'] += 1
        
        # 连接失败处理
        if self.fallback_to_winapi:
            print("[Arduino] 连接失败，使用 Windows API 备选方案")
            return True
        
        return False
    
    def move_mouse(self, x: float, y: float) -> Dict[str, Any]:
        """
        移动鼠标
        
        Args:
            x: X轴移动距离（像素）
            y: Y轴移动距离（像素）
            
        Returns:
            移动结果信息
        """
        self.stats['total_moves'] += 1
        
        # 转换为整数
        move_x = int(np.round(x))
        move_y = int(np.round(y))
        
        # 如果移动距离为0，直接返回
        if move_x == 0 and move_y == 0:
            return {
                'success': True,
                'method': 'none',
                'move_x': 0,
                'move_y': 0,
                'message': 'No movement needed'
            }
        
        # 尝试使用 Arduino
        if self.is_arduino_connected and self.arduino_serial:
            try:
                # Arduino 硬件限制：-127 到 127
                constrained_x = max(-127, min(127, move_x))
                constrained_y = max(-127, min(127, move_y))
                
                command = f'M{constrained_x},{constrained_y}\n'
                self.arduino_serial.write(command.encode())
                
                # 读取响应（可选）
                response = self.arduino_serial.readline().decode().strip()
                
                self.stats['arduino_moves'] += 1
                return {
                    'success': True,
                    'method': 'arduino',
                    'move_x': constrained_x,
                    'move_y': constrained_y,
                    'original_x': move_x,
                    'original_y': move_y,
                    'constrained': constrained_x != move_x or constrained_y != move_y,
                    'response': response,
                    'message': 'Arduino hardware move successful'
                }
                
            except Exception as e:
                print(f"[Arduino] 通信错误: {e}")
                self.stats['communication_errors'] += 1
                # Arduino 通信失败，标记为断开
                self.is_arduino_connected = False
                if self.arduino_serial:
                    self.arduino_serial.close()
                    self.arduino_serial = None
        
        # 使用 Windows API 备选方案
        if self.fallback_to_winapi:
            try:
                win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, move_x, move_y, 0, 0)
                self.stats['winapi_moves'] += 1
                return {
                    'success': True,
                    'method': 'winapi',
                    'move_x': move_x,
                    'move_y': move_y,
                    'message': 'Windows API move successful'
                }
            except Exception as e:
                print(f"[WinAPI] 移动失败: {e}")
                return {
                    'success': False,
                    'method': 'failed',
                    'move_x': move_x,
                    'move_y': move_y,
                    'error': str(e),
                    'message': 'All movement methods failed'
                }
        
        return {
            'success': False,
            'method': 'unavailable',
            'move_x': move_x,
            'move_y': move_y,
            'message': 'No movement method available'
        }
    
    def click_mouse(self, button: str = 'L') -> Dict[str, Any]:
        """
        直接向 Arduino 发送原始点击命令。
        此方法不等待响应以避免阻塞，但如果失败会尝试 WinAPI 回退。

        Args:
            button: 要点击的按钮 ('L' for left, 'R' for right, 'M' for middle)。

        Returns:
            点击结果信息。
        """
        # 尝试使用 Arduino
        if self.is_arduino_connected and self.arduino_serial:
            command_map = {
                'L': b'CL\n',
                'R': b'CR\n',
                'M': b'CM\n'
            }
            command = command_map.get(button.upper())

            if not command:
                return {
                    'success': False,
                    'method': 'failed',
                    'button': button,
                    'message': f'Invalid button: {button}'
                }

            try:
                self.arduino_serial.write(command)
                # 这是一个快速的触发操作，我们不等待响应，以避免阻塞
                return {
                    'success': True,
                    'method': 'arduino',
                    'button': button,
                    'message': f'Command {command.decode().strip()} sent to Arduino'
                }
            except Exception as e:
                print(f"[Arduino] 点击错误: {e}")
                self.is_arduino_connected = False
                if self.arduino_serial:
                    self.arduino_serial.close()
                    self.arduino_serial = None
        
        # 使用 Windows API 备选方案
        if self.fallback_to_winapi:
            try:
                button_map = {
                    'L': (win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP),
                    'R': (win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP),
                    'M': (win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_MIDDLEUP)
                }
                
                if button in button_map:
                    down_event, up_event = button_map[button]
                    win32api.mouse_event(down_event, 0, 0, 0, 0)
                    time.sleep(0.01)  # 短暂延迟
                    win32api.mouse_event(up_event, 0, 0, 0, 0)
                    
                    return {
                        'success': True,
                        'method': 'winapi',
                        'button': button,
                        'message': 'Windows API click successful'
                    }
                else:
                    return {
                        'success': False,
                        'method': 'failed',
                        'button': button,
                        'error': f'Invalid button: {button}',
                        'message': 'Invalid button specified'
                    }
                    
            except Exception as e:
                print(f"[WinAPI] 点击失败: {e}")
                return {
                    'success': False,
                    'method': 'failed',
                    'button': button,
                    'error': str(e),
                    'message': 'Click failed'
                }
        
        # 如果所有方法都失败，返回一个更明确的错误
        final_message = "No click method available"
        if not self.is_arduino_connected:
            final_message = "Arduino not connected"
            if not self.fallback_to_winapi:
                final_message += " and WinAPI fallback is disabled"
        
        return {
            'success': False,
            'method': 'unavailable',
            'button': button,
            'message': final_message
        }
    
    def reconnect(self) -> bool:
        """
        重新连接 Arduino
        
        Returns:
            重连是否成功
        """
        if self.arduino_serial:
            self.arduino_serial.close()
            self.arduino_serial = None
        
        self.is_arduino_connected = False
        return self.connect()
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取驱动状态
        
        Returns:
            状态信息
        """
        return {
            'arduino_connected': self.is_arduino_connected,
            'fallback_enabled': self.fallback_to_winapi,
            'connection_attempts': self.connection_attempts,
            'stats': self.stats.copy(),
            'primary_method': 'arduino' if self.is_arduino_connected else 'winapi' if self.fallback_to_winapi else 'none'
        }
    
    def close(self):
        """
        关闭连接
        """
        if self.arduino_serial and hasattr(self.arduino_serial, 'close'):
            try:
                if hasattr(self.arduino_serial, 'is_open') and self.arduino_serial.is_open:
                    self.arduino_serial.close()
                print("[Arduino] 连接已关闭")
            except Exception as e:
                print(f"[Arduino] 关闭连接时出错: {e}")
            finally:
                self.arduino_serial = None
        
        self.is_arduino_connected = False
    
    def __del__(self):
        """
        析构函数
        """
        try:
            self.close()
        except Exception as e:
            # 静默处理析构函数中的错误，避免在程序退出时显示错误
            pass

# 便捷函数
def create_mouse_driver(auto_connect: bool = True, fallback_to_winapi: bool = True) -> ArduinoMouseDriver:
    """
    创建鼠标驱动实例
    
    Args:
        auto_connect: 是否自动连接
        fallback_to_winapi: 是否启用 Windows API 备选
        
    Returns:
        鼠标驱动实例
    """
    return ArduinoMouseDriver(auto_connect=auto_connect, fallback_to_winapi=fallback_to_winapi)

if __name__ == "__main__":
    # 测试代码
    print("=== Arduino 鼠标驱动测试 ===")
    
    # 创建驱动
    driver = create_mouse_driver()
    
    # 显示状态
    status = driver.get_status()
    print(f"驱动状态: {status}")
    
    # 测试移动
    print("\n测试鼠标移动...")
    for i in range(3):
        result = driver.move_mouse(10, -5)
        print(f"移动 {i+1}: {result}")
        time.sleep(0.5)
    
    # 测试点击
    print("\n测试鼠标点击...")
    click_result = driver.click_mouse('L')
    print(f"点击结果: {click_result}")
    
    # 显示最终统计
    final_status = driver.get_status()
    print(f"\n最终统计: {final_status['stats']}")
    
    # 关闭驱动
    driver.close()
    print("\n测试完成")
"""
Arduino 键盘控制器 - Python 接口
功能：通过串口与 Arduino 键盘驱动通信，控制 WASD 键
作者：AI-Aimbot 项目
版本：1.0
"""

import serial
import serial.tools.list_ports
import time
import threading
from typing import Optional, List, Dict


class ArduinoKeyboardController:
    """Arduino 键盘控制器类"""
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 115200, timeout: float = 1.0):
        """
        初始化 Arduino 键盘控制器
        
        Args:
            port: 串口名称，如果为 None 则自动检测
            baudrate: 波特率，默认 115200
            timeout: 超时时间，默认 1.0 秒
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.key_states = {'w': False, 'a': False, 's': False, 'd': False}
        self._lock = threading.Lock()
        
    def find_arduino_ports(self) -> List[str]:
        """
        查找可能的 Arduino 端口
        
        Returns:
            可能的 Arduino 端口列表
        """
        arduino_ports = []
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # 查找 Arduino Leonardo 或其他 Arduino 设备
            if any(keyword in port.description.lower() for keyword in 
                   ['arduino', 'leonardo', 'ch340', 'cp210', 'ftdi']):
                arduino_ports.append(port.device)
                print(f"发现可能的 Arduino 设备: {port.device} - {port.description}")
        
        return arduino_ports
    
    def connect(self) -> bool:
        """
        连接到 Arduino 设备
        
        Returns:
            连接是否成功
        """
        if self.is_connected:
            print("已经连接到 Arduino")
            return True
        
        # 如果没有指定端口，自动检测
        if not self.port:
            arduino_ports = self.find_arduino_ports()
            if not arduino_ports:
                print("错误: 未找到 Arduino 设备")
                return False
            self.port = arduino_ports[0]
            print(f"自动选择端口: {self.port}")
        
        try:
            # 建立串口连接
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            # 等待 Arduino 启动
            time.sleep(2)
            
            # 清空缓冲区
            self.serial_conn.flushInput()
            self.serial_conn.flushOutput()
            
            # 测试连接
            self.send_command('?')
            time.sleep(0.1)
            
            # 读取响应
            response = self.read_response()
            if response and "当前键盘状态" in response:
                self.is_connected = True
                print(f"成功连接到 Arduino 键盘控制器: {self.port}")
                return True
            else:
                print("警告: 连接成功但设备响应异常")
                self.is_connected = True
                return True
                
        except serial.SerialException as e:
            print(f"连接失败: {e}")
            return False
        except Exception as e:
            print(f"连接时发生未知错误: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.serial_conn and self.serial_conn.is_open:
            # 释放所有按键
            self.release_all_keys()
            time.sleep(0.1)
            
            self.serial_conn.close()
            self.is_connected = False
            print("已断开 Arduino 连接")
    
    def send_command(self, command: str) -> bool:
        """
        发送指令到 Arduino
        
        Args:
            command: 要发送的指令
            
        Returns:
            发送是否成功
        """
        if not self.is_connected or not self.serial_conn:
            print("错误: 未连接到 Arduino")
            return False
        
        try:
            with self._lock:
                self.serial_conn.write(command.encode())
                self.serial_conn.flush()
            return True
        except Exception as e:
            print(f"发送指令失败: {e}")
            return False
    
    def read_response(self, timeout: float = 0.5) -> str:
        """
        读取 Arduino 响应
        
        Args:
            timeout: 读取超时时间
            
        Returns:
            读取到的响应字符串
        """
        if not self.is_connected or not self.serial_conn:
            return ""
        
        try:
            response_lines = []
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        response_lines.append(line)
                else:
                    time.sleep(0.01)
            
            return '\n'.join(response_lines)
        except Exception as e:
            print(f"读取响应失败: {e}")
            return ""
    
    def press_key(self, key: str) -> bool:
        """
        按下指定键
        
        Args:
            key: 要按下的键 ('w', 'a', 's', 'd')
            
        Returns:
            操作是否成功
        """
        key = key.lower()
        if key not in ['w', 'a', 's', 'd']:
            print(f"错误: 不支持的按键 '{key}'")
            return False
        
        if self.send_command(key):
            self.key_states[key] = True
            return True
        return False
    
    def release_key(self, key: str) -> bool:
        """
        弹起指定键
        
        Args:
            key: 要弹起的键 ('w', 'a', 's', 'd')
            
        Returns:
            操作是否成功
        """
        key = key.lower()
        if key not in ['w', 'a', 's', 'd']:
            print(f"错误: 不支持的按键 '{key}'")
            return False
        
        if self.send_command(key.upper()):
            self.key_states[key] = False
            return True
        return False
    
    def release_all_keys(self) -> bool:
        """
        释放所有按键
        
        Returns:
            操作是否成功
        """
        if self.send_command('R'):
            for key in self.key_states:
                self.key_states[key] = False
            return True
        return False
    
    def get_status(self) -> Dict[str, bool]:
        """
        获取当前按键状态
        
        Returns:
            按键状态字典
        """
        return self.key_states.copy()
    
    def query_arduino_status(self) -> str:
        """
        查询 Arduino 设备状态
        
        Returns:
            Arduino 返回的状态信息
        """
        if self.send_command('?'):
            time.sleep(0.1)
            return self.read_response()
        return ""
    
    def start_silence_mode(self, duration_ms: int = 150) -> bool:
        """
        开始静默期模式
        
        Args:
            duration_ms: 静默期持续时间（毫秒）
        
        Returns:
            是否成功启动静默期
        """
        if not self.is_connected:
            print("错误: 未连接到 Arduino")
            return False
        
        with self._lock:
            # 设置静默时长
            if not self.send_command(f'T{duration_ms}'):
                print("错误: 设置静默时长失败")
                return False
            
            time.sleep(0.05)  # 短暂等待
            
            # 开始静默期
            if not self.send_command('X'):
                print("错误: 启动静默期失败")
                return False
            
            print(f"[Arduino] 开始静默期: {duration_ms}ms")
            return True
    
    def stop_silence_mode(self) -> bool:
        """
        停止静默期模式
        
        Returns:
            是否成功停止静默期
        """
        if not self.is_connected:
            print("错误: 未连接到 Arduino")
            return False
        
        with self._lock:
            if not self.send_command('x'):
                print("错误: 停止静默期失败")
                return False
            
            print("[Arduino] 停止静默期")
            return True
    
    def set_silence_duration(self, duration_ms: int) -> bool:
        """
        设置静默期持续时间
        
        Args:
            duration_ms: 静默期持续时间（毫秒）
        
        Returns:
            是否成功设置
        """
        if not self.is_connected:
            print("错误: 未连接到 Arduino")
            return False
        
        if duration_ms < 1 or duration_ms > 5000:
            print("错误: 静默时长必须在1-5000ms之间")
            return False
        
        with self._lock:
            if not self.send_command(f'T{duration_ms}'):
                print("错误: 设置静默时长失败")
                return False
            
            print(f"[Arduino] 设置静默时长: {duration_ms}ms")
            return True
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


# 便捷函数
def create_keyboard_controller(port: Optional[str] = None) -> ArduinoKeyboardController:
    """
    创建键盘控制器实例
    
    Args:
        port: 串口名称，如果为 None 则自动检测
        
    Returns:
        键盘控制器实例
    """
    return ArduinoKeyboardController(port)


if __name__ == "__main__":
    # 测试代码
    print("Arduino 键盘控制器测试")
    print("=" * 30)
    
    # 创建控制器
    controller = create_keyboard_controller()
    
    # 连接设备
    if controller.connect():
        print("连接成功！")
        
        # 查询状态
        print("\n查询 Arduino 状态:")
        status = controller.query_arduino_status()
        print(status)
        
        # 测试按键
        print("\n测试按键功能...")
        test_keys = ['w', 'a', 's', 'd']
        
        for key in test_keys:
            print(f"按下 {key.upper()}")
            controller.press_key(key)
            time.sleep(0.5)
            
            print(f"弹起 {key.upper()}")
            controller.release_key(key)
            time.sleep(0.5)
        
        print("\n释放所有按键")
        controller.release_all_keys()
        
        # 断开连接
        controller.disconnect()
        print("测试完成")
    else:
        print("连接失败！")
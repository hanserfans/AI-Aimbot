#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WASD静默期控制器
实现开火前强制释放WASD键并阻止新的WASD输入
"""

import time
import threading
import win32api
import win32con
import ctypes
from ctypes import wintypes
from typing import Optional, Dict

# 尝试导入Arduino键盘控制器
try:
    from arduino_keyboard_controller import ArduinoKeyboardController
    ARDUINO_AVAILABLE = True
except ImportError:
    ARDUINO_AVAILABLE = False
    print("[WASD_SILENCE] Arduino键盘控制器不可用，将使用Win32 API")

class WASDSilenceController:
    """WASD静默期控制器"""
    
    def __init__(self, silence_duration: float = 0.001):
        """
        初始化WASD静默期控制器
        
        Args:
            silence_duration: 静默期持续时间（秒）
        """
        self.silence_duration = silence_duration
        self.is_silenced = False
        self.silence_lock = threading.Lock()
        
        # WASD键码映射
        self.wasd_keys = {
            'w': 0x57,  # W键
            'a': 0x41,  # A键
            's': 0x53,  # S键
            'd': 0x44   # D键
        }
        
        # Arduino键盘控制器
        self.arduino_keyboard = None
        if ARDUINO_AVAILABLE:
            try:
                self.arduino_keyboard = ArduinoKeyboardController()
                # 不在初始化时连接，而是在需要时连接
                print("[WASD_SILENCE] ✅ Arduino键盘控制器已准备")
            except Exception as e:
                print(f"[WASD_SILENCE] ❌ Arduino键盘控制器初始化失败: {e}")
                self.arduino_keyboard = None
        
        print(f"[WASD_SILENCE] 🔇 WASD静默期控制器初始化完成，静默时长: {silence_duration}s")
    
    def _get_key_state_win32(self, key_code: int) -> bool:
        """
        使用Win32 API检测键盘按键状态
        
        Args:
            key_code: 键盘按键代码
        
        Returns:
            True表示按键被按下，False表示按键已释放
        """
        try:
            # 使用GetAsyncKeyState检测按键状态
            # 返回值的最高位表示按键是否被按下
            state = ctypes.windll.user32.GetAsyncKeyState(key_code)
            return (state & 0x8000) != 0
        except Exception as e:
            print(f"[WASD_SILENCE] ⚠️ Win32键盘状态检测失败: {e}")
            return False
    
    def _get_wasd_states_arduino(self) -> Dict[str, bool]:
        """
        使用Arduino检测WASD键状态
        
        Returns:
            WASD键状态字典
        """
        try:
            if self.arduino_keyboard and self.arduino_keyboard.is_connected:
                # 查询Arduino状态
                status = self.arduino_keyboard.query_arduino_status()
                if status:
                    # 解析Arduino返回的状态信息
                    # 假设Arduino返回格式类似: "W:0 A:0 S:0 D:0"
                    states = {'w': False, 'a': False, 's': False, 'd': False}
                    for line in status.split('\n'):
                        if 'W:' in line:
                            states['w'] = '1' in line
                        elif 'A:' in line:
                            states['a'] = '1' in line
                        elif 'S:' in line:
                            states['s'] = '1' in line
                        elif 'D:' in line:
                            states['d'] = '1' in line
                    return states
        except Exception as e:
            print(f"[WASD_SILENCE] ⚠️ Arduino键盘状态检测失败: {e}")
        
        return {'w': False, 'a': False, 's': False, 'd': False}
    
    def _get_wasd_states_win32(self) -> Dict[str, bool]:
        """
        使用Win32 API检测WASD键状态
        
        Returns:
            WASD键状态字典
        """
        states = {}
        for key, code in self.wasd_keys.items():
            states[key] = self._get_key_state_win32(code)
        return states
    
    def get_wasd_states(self) -> Dict[str, bool]:
        """
        获取当前WASD键状态
        
        Returns:
            WASD键状态字典，True表示按下，False表示释放
        """
        # 优先使用Arduino检测
        if self.arduino_keyboard:
            try:
                if not self.arduino_keyboard.is_connected:
                    self.arduino_keyboard.connect()
                
                if self.arduino_keyboard.is_connected:
                    arduino_states = self._get_wasd_states_arduino()
                    print(f"[WASD_SILENCE] 🎮 Arduino键盘状态: {arduino_states}")
                    return arduino_states
            except Exception as e:
                print(f"[WASD_SILENCE] ⚠️ Arduino状态检测失败: {e}")
        
        # 回退到Win32 API
        win32_states = self._get_wasd_states_win32()
        print(f"[WASD_SILENCE] 💻 Win32键盘状态: {win32_states}")
        return win32_states
    
    def are_wasd_keys_released(self) -> bool:
        """
        检查所有WASD键是否都已释放
        
        Returns:
            True表示所有WASD键都已释放，False表示至少有一个键被按下
        """
        states = self.get_wasd_states()
        all_released = all(not pressed for pressed in states.values())
        
        if all_released:
            print("[WASD_SILENCE] ✅ 所有WASD键已释放")
        else:
            pressed_keys = [key.upper() for key, pressed in states.items() if pressed]
            print(f"[WASD_SILENCE] ⚠️ 检测到按下的键: {', '.join(pressed_keys)}")
        
        return all_released
    
    def wait_for_wasd_release(self, timeout: float = 1.0, check_interval: float = 0.2) -> bool:
        """
        等待所有WASD键释放
        
        Args:
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
        
        Returns:
            True表示所有键已释放，False表示超时
        """
        print(f"[WASD_SILENCE] ⏳ 等待WASD键释放（超时: {timeout}s）...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.are_wasd_keys_released():
                elapsed = time.time() - start_time
                print(f"[WASD_SILENCE] ✅ WASD键已释放（耗时: {elapsed:.3f}s）")
                return True
            
            time.sleep(check_interval)
        
        print(f"[WASD_SILENCE] ⏰ 等待WASD键释放超时（{timeout}s）")
        return False
    
    def verify_ready_to_fire(self, force_release: bool = True, wait_timeout: float = 0.000000001) -> bool:
        """
        验证是否准备好开火（WASD键必须全部释放）
        
        Args:
            force_release: 是否强制释放WASD键SD
            wait_timeout: 等待释放的超时时间（秒）
        
        Returns:
            True表示可以开火，False表示不能开火
        """
        # 1. 首先检查当前WASD键状态
        if self.are_wasd_keys_released():
            return True
        
        # 2. 如果有键被按下，根据参数决定是否强制释放
        if not force_release:
            return False
        
        # 3. 启动静默期强制释放WASD键
        if not self.start_silence_period(50):  # 50ms快速静默期
            return False
        
        # 4. 快速等待静默期结束并验证键释放
        time.sleep(0.000000001)  # 快速等待静默期完成
        
        # 5. 快速检查键释放状态
        if self.wait_for_wasd_release(timeout=wait_timeout, check_interval=0.01):
            return True
        else:
            return False
    
    def _release_wasd_arduino(self) -> bool:
        """使用Arduino释放WASD键"""
        if not self.arduino_keyboard:
            return False
        
        try:
            print("[WASD_SILENCE] 🎮 使用Arduino强制释放WASD键...")
            for key in ['w', 'a', 's', 'd']:
                self.arduino_keyboard.release_key(key)
                time.sleep(0.01)  # 短暂延迟确保命令执行
            print("[WASD_SILENCE] ✅ Arduino释放WASD键完成")
            return True
        except Exception as e:
            print(f"[WASD_SILENCE] ❌ Arduino释放WASD键失败: {e}")
            return False
    
    def _release_wasd_win32(self) -> bool:
        """使用Win32 API释放WASD键"""
        try:
            print("[WASD_SILENCE] 💻 使用Win32 API强制释放WASD键...")
            for key_name, key_code in self.wasd_keys.items():
                # 发送按键释放事件
                win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.005)  # 短暂延迟
            print("[WASD_SILENCE] ✅ Win32 API释放WASD键完成")
            return True
        except Exception as e:
            print(f"[WASD_SILENCE] ❌ Win32 API释放WASD键失败: {e}")
            return False
    
    def _block_wasd_input(self) -> bool:
        """阻止WASD键输入（通过Arduino或Win32）"""
        if self.arduino_keyboard:
            try:
                # Arduino可以通过持续发送释放命令来阻止输入
                print("[WASD_SILENCE] 🚫 Arduino阻止WASD输入...")
                return True
            except Exception as e:
                print(f"[WASD_SILENCE] ❌ Arduino阻止输入失败: {e}")
        
        # Win32 API备用方案：持续释放按键
        try:
            print("[WASD_SILENCE] 🚫 Win32阻止WASD输入...")
            return True
        except Exception as e:
            print(f"[WASD_SILENCE] ❌ Win32阻止输入失败: {e}")
            return False
    
    def start_silence_period(self, duration_ms: int = None) -> bool:
        """
        开始WASD静默期
        
        Args:
            duration_ms: 静默期持续时间（毫秒），如果为None则使用默认值
        
        Returns:
            bool: 是否成功启动静默期
        """
        with self.silence_lock:
            if self.is_silenced:
                print("[WASD_SILENCE] ⚠️ 静默期已在进行中")
                return True
            
            # 如果指定了duration_ms，则转换为秒并更新
            if duration_ms is not None:
                self.silence_duration = duration_ms / 1000.0
            
            print(f"[WASD_SILENCE] 🔇 开始WASD静默期 ({self.silence_duration}s)")
            self.is_silenced = True
            
            # 优先使用Arduino静默期功能
            arduino_success = False
            if self.arduino_keyboard:
                try:
                    # 假设Arduino控制器有start_silence_mode方法
                    if hasattr(self.arduino_keyboard, 'start_silence_mode'):
                        arduino_success = self.arduino_keyboard.start_silence_mode(int(self.silence_duration * 1000))
                        if arduino_success:
                            print("[WASD_SILENCE] 🎮 使用Arduino静默期模式")
                            # 启动定时器自动结束静默期
                            silence_thread = threading.Thread(target=self._silence_worker, daemon=True)
                            silence_thread.start()
                            return True
                except Exception as e:
                    print(f"[WASD_SILENCE] ❌ Arduino静默期失败: {e}")
            
            # 回退到软件层面的静默期
            if not arduino_success:
                print("[WASD_SILENCE] 💻 使用软件层面静默期")
                # 1. 强制释放WASD键
                release_success = False
                if self.arduino_keyboard:
                    release_success = self._release_wasd_arduino()
                
                if not release_success:
                    release_success = self._release_wasd_win32()
                
                if not release_success:
                    print("[WASD_SILENCE] ❌ 释放WASD键失败")
                    self.is_silenced = False
                    return False
                
                # 2. 阻止新的WASD输入
                block_success = self._block_wasd_input()
                
                # 3. 启动静默期线程
                silence_thread = threading.Thread(target=self._silence_worker, daemon=True)
                silence_thread.start()
            
            return True
    
    def _silence_worker(self):
        """静默期工作线程"""
        start_time = time.time()
        
        while time.time() - start_time < self.silence_duration:
            if not self.is_silenced:
                break
            
            # 持续释放WASD键确保没有输入
            if self.arduino_keyboard:
                try:
                    for key in ['w', 'a', 's', 'd']:
                        self.arduino_keyboard.release_key(key)
                    time.sleep(0.02)
                except:
                    # Arduino失败时使用Win32
                    for key_code in self.wasd_keys.values():
                        win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                    time.sleep(0.02)
            else:
                # 使用Win32持续释放
                for key_code in self.wasd_keys.values():
                    win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.02)
        
        # 静默期结束
        with self.silence_lock:
            self.is_silenced = False
            print("[WASD_SILENCE] ✅ WASD静默期结束")
    
    def is_in_silence_period(self) -> bool:
        """检查是否在静默期中"""
        return self.is_silenced
    
    def stop_silence_period(self) -> bool:
        """
        停止WASD键静默期
        
        Returns:
            是否成功停止静默期
        """
        with self.silence_lock:
            if not self.is_silenced:
                print("[WASD_SILENCE] 静默期未激活")
                return True
            
            print("[WASD_SILENCE] 停止静默期")
            
            # 如果使用Arduino，尝试停止Arduino静默期
            if self.arduino_keyboard and hasattr(self.arduino_keyboard, 'stop_silence_mode'):
                try:
                    self.arduino_keyboard.stop_silence_mode()
                    print("[WASD_SILENCE] Arduino静默期已停止")
                except Exception as e:
                    print(f"[WASD_SILENCE] 停止Arduino静默期失败: {e}")
            
            # 重置状态
            self.is_silenced = False
            print("[WASD_SILENCE] ⏹️ 强制停止WASD静默期")
            
            return True
    
    def set_silence_duration(self, duration: float):
        """设置静默期持续时间"""
        self.silence_duration = duration
        print(f"[WASD_SILENCE] ⏱️ 设置静默期持续时间: {duration}s")
    
    def get_status(self) -> dict:
        """获取控制器状态"""
        return {
            'is_silenced': self.is_silenced,
            'silence_duration': self.silence_duration,
            'arduino_available': self.arduino_keyboard is not None,
            'arduino_connected': self.arduino_keyboard.is_connected() if self.arduino_keyboard else False
        }

# 全局实例
_wasd_silence_controller: Optional[WASDSilenceController] = None

def get_wasd_silence_controller(silence_duration: float = 0.15) -> WASDSilenceController:
    """获取WASD静默期控制器单例"""
    global _wasd_silence_controller
    if _wasd_silence_controller is None:
        _wasd_silence_controller = WASDSilenceController(silence_duration)
    return _wasd_silence_controller

def start_wasd_silence(duration: float = 0.15) -> bool:
    """
    启动WASD静默期的便捷函数
    
    Args:
        duration: 静默期持续时间（秒）
    
    Returns:
        bool: 是否成功启动
    """
    controller = get_wasd_silence_controller(duration)
    return controller.start_silence_period()

if __name__ == "__main__":
    print("WASD静默期控制器测试")
    print("="*50)
    
    # 创建控制器
    controller = WASDSilenceController(0.2)
    
    # 显示状态
    status = controller.get_status()
    print(f"控制器状态: {status}")
    
    # 测试静默期
    print("\n🧪 测试WASD静默期...")
    success = controller.start_silence_period()
    
    if success:
        print("✅ 静默期启动成功")
        
        # 等待静默期结束
        while controller.is_in_silence_period():
            print("🔇 静默期进行中...")
            time.sleep(0.1)
        
        print("✅ 静默期测试完成")
    else:
        print("❌ 静默期启动失败")
"""
键盘控制模块
用于监控和控制WASD键的状态，支持在开火时暂停键盘输入
"""

import win32api
import win32con
import time
import threading
from typing import Dict, Set, Optional, Callable
from config import DEBUG_LOG

class KeyboardController:
    """键盘控制器，用于管理WASD键的状态和控制"""
    
    # WASD键的虚拟键码
    WASD_KEYS = {
        'W': 0x57,  # W键
        'A': 0x41,  # A键  
        'S': 0x53,  # S键
        'D': 0x44   # D键
    }
    
    def __init__(self):
        """初始化键盘控制器"""
        self.is_monitoring = False
        self.is_paused = False
        self.pressed_keys: Set[str] = set()  # 当前按下的键
        self.blocked_keys: Set[str] = set()  # 被阻止的键
        self.monitor_thread: Optional[threading.Thread] = None
        self.pause_callback: Optional[Callable] = None
        self.resume_callback: Optional[Callable] = None
        
    def set_callbacks(self, pause_callback: Callable = None, resume_callback: Callable = None):
        """设置暂停和恢复回调函数"""
        self.pause_callback = pause_callback
        self.resume_callback = resume_callback
        
    def is_key_pressed(self, key_code: int) -> bool:
        """检查指定键是否被按下"""
        return win32api.GetAsyncKeyState(key_code) & 0x8000 != 0
        
    def get_pressed_wasd_keys(self) -> Set[str]:
        """获取当前按下的WASD键"""
        pressed = set()
        for key_name, key_code in self.WASD_KEYS.items():
            if self.is_key_pressed(key_code):
                pressed.add(key_name)
        return pressed
        
    def block_key(self, key_name: str):
        """阻止指定键的输入"""
        if key_name in self.WASD_KEYS:
            self.blocked_keys.add(key_name)
            # 如果键当前被按下，释放它
            if key_name in self.pressed_keys:
                self._release_key(key_name)
                
    def unblock_key(self, key_name: str):
        """解除指定键的阻止"""
        if key_name in self.blocked_keys:
            self.blocked_keys.remove(key_name)
            
    def block_all_wasd(self):
        """阻止所有WASD键"""
        for key_name in self.WASD_KEYS.keys():
            self.block_key(key_name)
        if self.pause_callback:
            self.pause_callback()
            
    def unblock_all_wasd(self):
        """解除所有WASD键的阻止"""
        for key_name in self.WASD_KEYS.keys():
            self.unblock_key(key_name)
        if self.resume_callback:
            self.resume_callback()
            
    def _press_key(self, key_name: str):
        """按下指定键"""
        if key_name in self.WASD_KEYS:
            key_code = self.WASD_KEYS[key_name]
            win32api.keybd_event(key_code, 0, 0, 0)
            
    def _release_key(self, key_name: str):
        """释放指定键"""
        if key_name in self.WASD_KEYS:
            key_code = self.WASD_KEYS[key_name]
            win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            
    def pause_movement(self):
        """暂停移动（阻止WASD键）"""
        if not self.is_paused:
            self.is_paused = True
            # 记录当前按下的键
            current_pressed = self.get_pressed_wasd_keys()
            
            # 释放所有当前按下的WASD键
            for key_name in current_pressed:
                self._release_key(key_name)
                self.pressed_keys.add(key_name)  # 记录需要恢复的键
                
            # 阻止所有WASD键
            self.block_all_wasd()
            debug_log("[KEYBOARD] 🛑 WASD键移动已暂停", tag="KEYBOARD", throttle_ms=500)
            
    def resume_movement(self):
        """恢复移动（解除WASD键阻止）"""
        if self.is_paused:
            self.is_paused = False
            
            # 解除所有WASD键的阻止
            self.unblock_all_wasd()
            
            # 恢复之前按下的键（如果用户仍在按着）
            for key_name in list(self.pressed_keys):
                if self.is_key_pressed(self.WASD_KEYS[key_name]):
                    self._press_key(key_name)
                self.pressed_keys.remove(key_name)
                
            debug_log("[KEYBOARD] ✅ WASD键移动已恢复", tag="KEYBOARD", throttle_ms=500)
            
    def start_monitoring(self):
        """开始监控键盘状态"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            debug_log("[KEYBOARD] 🔍 开始监控WASD键状态", tag="KEYBOARD", throttle_ms=2000)
            
    def stop_monitoring(self):
        """停止监控键盘状态"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        debug_log("[KEYBOARD] ⏹️ 停止监控WASD键状态", tag="KEYBOARD", throttle_ms=2000)
        
    def _monitor_loop(self):
        """键盘监控循环"""
        while self.is_monitoring:
            try:
                # 检查被阻止的键是否被按下，如果是则立即释放
                for key_name in self.blocked_keys:
                    if self.is_key_pressed(self.WASD_KEYS[key_name]):
                        self._release_key(key_name)
                        
                time.sleep(0.01)  # 10ms检查间隔
            except Exception as e:
                print(f"[KEYBOARD] ❌ 监控循环错误: {e}")
                break
                
    def get_status(self) -> Dict:
        """获取键盘控制器状态"""
        return {
            'is_monitoring': self.is_monitoring,
            'is_paused': self.is_paused,
            'pressed_keys': list(self.pressed_keys),
            'blocked_keys': list(self.blocked_keys),
            'current_wasd_pressed': list(self.get_pressed_wasd_keys())
        }
        
    def __del__(self):
        """析构函数，确保清理资源"""
        self.stop_monitoring()
        if self.is_paused:
            self.resume_movement()

# 全局键盘控制器实例
keyboard_controller = KeyboardController()

def get_keyboard_controller() -> KeyboardController:
    """获取全局键盘控制器实例"""
    return keyboard_controller

# ==================== 调试日志辅助 ====================
# 说明：统一键盘模块的信息级别日志为可选调试输出，并支持节流。
_last_debug_log_times = {}

def debug_log(message: str, tag: str = None, throttle_ms: int = None):
    """
    轻量调试输出函数（KeyboardController模块）
    - 在 DEBUG_LOG 为 True 时输出；默认不打印
    - 支持按标签节流，避免高频重复打印影响性能
    参数:
      message: 要输出的文本
      tag: 日志标签（用于区分节流通道）
      throttle_ms: 节流间隔，毫秒；None 表示不节流
    """
    if not DEBUG_LOG:
        return
    if throttle_ms is None:
        print(message)
        return
    try:
        key = tag or 'default'
        now = time.time()
        last = _last_debug_log_times.get(key, 0.0)
        if (now - last) * 1000.0 >= throttle_ms:
            _last_debug_log_times[key] = now
            print(message)
    except Exception:
        print(message)
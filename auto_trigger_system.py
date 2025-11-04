"""
自动扳机系统 (Auto Trigger System)

智能检测目标对齐并自动射击的系统
- 基于目标检测结果判断是否对齐
- 支持可配置的对齐阈值和冷却时间
- 提供连发射击功能
- 实时状态监控和统计
- 使用G-Hub驱动进行硬件级鼠标控制
- 支持多种预设配置和自定义阈值
"""

import subprocess

def run_diagnostic_script():
    """运行诊断脚本并打印输出"""
    try:
        print("\n[DIAGNOSTIC_RUN] 正在启动开火问题诊断脚本...")
        result = subprocess.run(
            ["python", "diagnose_fire_issue.py"],
            capture_output=True,
            text=True,
            check=True,
            encoding='gbk',
            errors='ignore'
        )
        print("[DIAGNOSTIC_RUN] 诊断脚本输出:")
        print(result.stdout)
        print("[DIAGNOSTIC_RUN] 诊断脚本执行完毕。")
    except FileNotFoundError:
        print("[DIAGNOSTIC_RUN] 错误: 未找到 `diagnose_fire_issue.py` 脚本。")
    except subprocess.CalledProcessError as e:
        print("[DIAGNOSTIC_RUN] 诊断脚本执行出错:")
        print(e.stdout)
        print(e.stderr)
    except Exception as e:
        print(f"[DIAGNOSTIC_RUN] 运行诊断脚本时发生未知错误: {e}")

# 在主逻辑开始前运行诊断
run_diagnostic_script()


import time
from typing import Optional, Tuple
import math
import win32api
import win32con
import serial
import serial.tools.list_ports
from keyboard_controller import get_keyboard_controller
from config import DEBUG_LOG

# Import Arduino mouse driver with fallback
from arduino_mouse_driver import ArduinoMouseDriver
print("[TRIGGER] Forcing Arduino driver availability to TRUE for debugging.")
ARDUINO_AVAILABLE = True

# Import Arduino keyboard controller with fallback - DISABLED
# 禁用Arduino键盘控制器，避免键盘检测导致的连接失败
print("[TRIGGER] Arduino 键盘控制器已禁用，避免键盘检测冲突")
ARDUINO_KEYBOARD_AVAILABLE = False

# Import WASD silence controller with fallback - DISABLED to prevent hanging
# try:
#     from wasd_silence_controller import WASDSilenceController
#     print("[TRIGGER] WASD静默期控制器导入成功")
#     WASD_SILENCE_AVAILABLE = True
# except ImportError as e:
#     print(f"[TRIGGER] WASD静默期控制器导入失败: {e}")
#     WASD_SILENCE_AVAILABLE = False
print("[TRIGGER] WASD静默期控制器已禁用，避免程序卡在静默期")
WASD_SILENCE_AVAILABLE = False

# Import G-Hub mouse driver with fallback
try:
    from mouse_driver.MouseMove import ghub_click
    print("[TRIGGER] G-Hub 驱动导入成功")
    GHUB_AVAILABLE = True
except ImportError as e:
    print(f"[TRIGGER] G-Hub 驱动导入失败: {e}")
    print("[TRIGGER] 将使用 Win32 API 作为备用方案")
    GHUB_AVAILABLE = False

# 尝试导入配置系统
try:
    from threshold_config import ThresholdConfig
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("[TRIGGER] 配置系统不可用，使用默认设置")


class AutoTriggerSystem:
    """自动扳机系统"""
    
    def __init__(self, use_config=True):
        """初始化自动扳机系统
        
        Args:
            use_config: 是否使用配置系统（默认True）
        """
        self.enabled = True  # 扳机功能是否启用（默认启用，可通过鼠标侧键2切换）
        
        # 初始化配置系统
        self.config_manager = None
        if use_config and CONFIG_AVAILABLE:
            try:
                self.config_manager = ThresholdConfig()
                self._load_config_values()
                print(f"[TRIGGER] 已加载配置: {self.config_manager.get_current_config()['name']}")
            except Exception as e:
                print(f"[TRIGGER] 配置系统初始化失败: {e}")
                self._set_default_values()
        else:
            self._set_default_values()
        
        # 统计信息
        self.total_triggers = 0  # 总触发次数
        self.total_shots = 0  # 总射击次数
        
        # 移动控制回调
        self.movement_stop_callback = None  # 停止移动的回调函数
        self.movement_resume_callback = None  # 恢复移动的回调函数
        self.is_firing = False  # 当前是否正在开火
        self.alignment_start_time = None  # 重合开始时间
        self.is_precisely_aligned_status = False  # 新增：用于跟踪精确重合状态

        # 新增：用于"多点重合"开火方案
        self.fire_event_window = 0.5  # 时间窗口（秒）- 增加到0.5秒，更宽松的检测
        self.fire_event_threshold = 2  # 在时间窗口内需要达到的重合次数 - 降低到1次
        self.alignment_events = []  # 存储最近的重合事件时间戳
        self.min_alignment_duration = 0.1  # 最小重合时间（秒）- 降低到0.05秒
        
        # 初始化Arduino驱动
        self.arduino_driver = None
        if ARDUINO_AVAILABLE:
            try:
                # 创建驱动并自动尝试连接
                self.arduino_driver = ArduinoMouseDriver(auto_connect=True, fallback_to_winapi=False)
                print("\n[SYSTEM_DEBUG] Arduino driver created. Auto-connect attempted.")
                # 若未连接则进行一次握手连接
                if not getattr(self.arduino_driver, 'is_arduino_connected', False):
                    print("[SYSTEM_DEBUG] Initial connect required; attempting handshake...")
                    connect_success = self.arduino_driver.connect()
                    print(f"[SYSTEM_DEBUG] Connect attempt finished. Success: {connect_success}")
                status_after_connect = self.arduino_driver.get_status()
                print(f"[SYSTEM_DEBUG] Status after init: {status_after_connect}\n")
                if self.arduino_driver.is_arduino_connected:
                    print("[TRIGGER] Arduino 驱动初始化成功，已连接到硬件")
                else:
                    print("[TRIGGER] Arduino 驱动初始化成功，但未连接到硬件")
            except Exception as e:
                print(f"[TRIGGER] Arduino 驱动初始化失败: {e}")
                self.arduino_driver = None
        
        # 初始化Arduino键盘控制器 - DISABLED
        self.arduino_keyboard = None

        
        # 初始化WASD静默期控制器 - DISABLED to prevent hanging
        self.wasd_silence_controller = None

        # if WASD_SILENCE_AVAILABLE:
        #     try:
        #         self.wasd_silence_controller = WASDSilenceController()
        #         print("[TRIGGER] WASD静默期控制器初始化成功")
        #     except Exception as e:
        #         print(f"[TRIGGER] WASD静默期控制器初始化失败: {e}")
        #         self.wasd_silence_controller = None
        
        # 键盘控制设置
        self.keyboard_release_duration = 0  # WASD键释放持续时间（秒）
        self.use_arduino_keyboard = True  # 是否使用Arduino键盘控制（优先级高于软件控制）
        self.use_wasd_silence = False  # 是否使用WASD静默期控制（已禁用）
    
    def _set_default_values(self):
        """设置默认阈值"""
        # 像素阈值（向后兼容）- 进一步放宽检测条件
        self.alignment_threshold = 45  # 阈值（像素）- 进一步放宽重合检测范围
        self.precise_alignment_threshold = 35  # 精确对齐阈值（像素）- 进一步放宽精确检测
        self.xy_check_threshold = 35.0  # X/Y轴检查阈值 - 进一步放宽轴向检测
        
        # 角度阈值（推荐使用）- 进一步放宽角度检测
        self.angle_threshold = 1.8  # 角度阈值（度）- 进一步大幅放宽对齐检测
        self.precise_angle_threshold = 1.2  # 精确角度阈值（度）- 进一步放宽精确检测
        self.use_angle_threshold = True  # 是否使用角度阈值（默认启用）
        
        # 其他设置 - 进一步加快响应速度
        self.last_fire_time = 0.0  # 上次开火时间
        self.cooldown_duration = 0.3  # 冷却时间（秒）- 默认0.3s，若有配置将覆盖
        self.shots_per_trigger = 2 # 每次触发的射击次数
        self.shot_interval = 0.1  # 连发间隔（秒）- 增加间隔以降低连发速度
    
    def _load_config_values(self):
        """从配置管理器加载数值"""
        if self.config_manager:
            config = self.config_manager.get_current_config()
            # 像素阈值配置
            self.alignment_threshold = config['alignment_threshold']
            self.precise_alignment_threshold = config['precise_alignment_threshold']
            self.xy_check_threshold = config.get('xy_check_threshold', 2.0)
            
            # 角度阈值配置
            self.angle_threshold = config.get('angle_threshold', 0.5)
            self.precise_angle_threshold = config.get('precise_angle_threshold', 0.3)
            self.use_angle_threshold = config.get('use_angle_threshold', True)
            
            # 其他配置
            self.cooldown_duration = config['cooldown_duration']
            self.shots_per_trigger = config['shots_per_trigger']
            self.shot_interval = config['shot_interval']
            self.last_fire_time = 0.0
        
        # 键盘控制器
        self.keyboard_controller = get_keyboard_controller()
        self.keyboard_stop_enabled = True  # 是否启用键盘停止功能
        
        print("[INFO] 自动扳机系统已初始化")
        if self.use_angle_threshold:
            print(f"[INFO] 🎯 使用角度阈值系统（推荐）")
            print(f"[INFO] 角度阈值: {self.angle_threshold:.3f}°")
            print(f"[INFO] 精确角度阈值: {self.precise_angle_threshold:.3f}°")
        else:
            print(f"[INFO] 📐 使用像素阈值系统（向后兼容）")
            print(f"[INFO] 对齐阈值: {self.alignment_threshold}像素")
            print(f"[INFO] 精确对齐阈值: {self.precise_alignment_threshold}像素")
            print(f"[INFO] XY检查阈值: {self.xy_check_threshold}像素")
        print(f"[INFO] 冷却时间: {self.cooldown_duration}秒")
        print(f"[INFO] 连发数量: {self.shots_per_trigger}发")
        print(f"[INFO] 连发间隔: {self.shot_interval}秒")
    
    def attach_arduino_driver(self, external_driver) -> bool:
        """将外部已连接的 Arduino 驱动注入并复用现有串口连接

        原理:
        - 复用主程序中已打开的串口，避免重复打开导致的拒绝访问
        - 仅在外部驱动已连接且串口处于打开状态时进行复用

        返回:
        - True: 复用成功
        - False: 外部驱动未就绪或复用失败
        """
        try:
            if (
                external_driver
                and getattr(external_driver, 'is_arduino_connected', False)
                and getattr(external_driver, 'arduino_serial', None)
                and getattr(external_driver.arduino_serial, 'is_open', False)
            ):
                self.arduino_driver = external_driver
                print("[TRIGGER] ✅ 已复用外部 Arduino 驱动连接")
                return True
            else:
                print("[TRIGGER] ⚠️ 外部 Arduino 驱动未就绪，无法复用")
                return False
        except Exception as e:
            print(f"[TRIGGER] ❌ 复用外部 Arduino 驱动失败: {e}")
            return False
    
    def toggle_trigger(self) -> bool:
        """切换扳机功能开关状态"""
        self.enabled = not self.enabled
        status = "启用" if self.enabled else "禁用"
        print(f"[INFO] 自动扳机功能已{status}")
        return self.enabled
    
    def set_enabled(self, enabled: bool):
        """设置扳机功能状态"""
        self.enabled = enabled
        status = "启用" if self.enabled else "禁用"
        print(f"[INFO] 自动扳机功能已{status}")
    
    def is_on_cooldown(self) -> bool:
        """检查是否在冷却时间内"""
        current_time = time.time()
        return (current_time - self.last_fire_time) < self.cooldown_duration
    
    def calculate_crosshair_distance(self, target_x: float, target_y: float, 
                                   detection_center: Tuple[float, float]) -> float:
        """
        计算目标与准星中心的距离
        
        Args:
            target_x: 目标在检测图像中的X坐标（归一化）
            target_y: 目标在检测图像中的Y坐标（归一化）
            detection_center: 检测图像中心坐标（归一化）
            
        Returns:
            距离（像素）
        """
        # 计算目标与准星中心的偏移
        offset_x = target_x - detection_center[0]
        offset_y = target_y - detection_center[1]
        
        # 计算欧几里得距离
        distance = math.sqrt(offset_x**2 + offset_y**2)
        
        # 转换为像素距离（假设检测图像为160x160）
        pixel_distance = distance * 160  # 检测图像尺寸
        
        return pixel_distance
    
    def calculate_angle_offset(self, target_x: float, target_y: float, 
                              detection_center: Tuple[float, float], 
                              headshot_offset: float = 0.0,
                              game_fov: float = 103.0, 
                              detection_size: int = 160,
                              game_width: int = 1920, 
                              game_height: int = 1080) -> float:
        """
        计算目标头部与准星的角度偏移
        
        Args:
            target_x: 目标在检测图像中的X坐标（归一化）
            target_y: 目标在检测图像中的Y坐标（归一化）
            detection_center: 检测图像中心坐标（归一化）
            headshot_offset: 头部偏移量（归一化）
            game_fov: 游戏水平FOV（度）
            detection_size: 检测图像尺寸
            game_width: 游戏窗口宽度
            game_height: 游戏窗口高度
            
        Returns:
            总角度偏移（度）
        """
        import math
        
        # 计算目标头部位置
        head_y = target_y + headshot_offset
        
        # 归一化坐标：转换为[-1, 1]范围
        normalized_x = (target_x - detection_center[0]) / detection_center[0] if detection_center[0] != 0 else 0
        normalized_y = (head_y - detection_center[1]) / detection_center[1] if detection_center[1] != 0 else 0
        
        # 计算游戏窗口宽高比和垂直FOV
        window_aspect_ratio = game_width / game_height
        game_fov_vertical = 2 * math.degrees(math.atan(
            math.tan(math.radians(game_fov / 2)) / window_aspect_ratio
        ))
        
        # 计算捕获区域的实际FOV覆盖
        capture_ratio_h = detection_size / game_width
        capture_ratio_v = detection_size / game_height
        
        # 捕获区域对应的FOV角度
        effective_fov_h = game_fov * capture_ratio_h
        effective_fov_v = game_fov_vertical * capture_ratio_v
        
        # 计算角度偏移
        angle_offset_h = normalized_x * (effective_fov_h / 2)  # 水平角度偏移
        angle_offset_v = normalized_y * (effective_fov_v / 2)  # 垂直角度偏移
        
        # 计算总角度偏移
        total_angle_offset = math.sqrt(angle_offset_h**2 + angle_offset_v**2)
        
        return total_angle_offset
    
    def is_aligned(self, target_x: float, target_y: float, 
                   detection_center: Tuple[float, float], 
                   headshot_offset: float = 0.0,
                   game_fov: float = 103.0,
                   detection_size: int = 160,
                   game_width: int = 2560,
                   game_height: int = 1600) -> bool:
        """
        检查目标头部是否与准星精确对齐
        支持像素阈值（向后兼容）和角度阈值（推荐）两种模式
        
        Args:
            target_x: 目标在检测图像中的X坐标（归一化）
            target_y: 目标在检测图像中的Y坐标（归一化）
            detection_center: 检测图像中心坐标（归一化）
            headshot_offset: 头部偏移量（归一化）
            game_fov: 游戏水平FOV（度）
            detection_size: 检测图像尺寸
            game_width: 游戏窗口宽度
            game_height: 游戏窗口高度
            
        Returns:
            是否精确对齐
        """
        # 计算目标头部位置
        head_y = target_y + headshot_offset
        
        if self.use_angle_threshold:
            # 使用角度阈值系统（推荐）
            angle_offset = self.calculate_angle_offset(
                target_x, target_y, detection_center, headshot_offset,
                game_fov, detection_size, game_width, game_height
            )
            
            # 使用角度阈值进行对齐检测
            is_precisely_aligned = angle_offset <= self.precise_angle_threshold
            is_roughly_aligned = angle_offset <= self.angle_threshold
            
            # 更新精确重合状态
            self.is_precisely_aligned_status = is_precisely_aligned
            
            if is_precisely_aligned:
                print(f"[TRIGGER] 🎯 目标精确重合！角度偏移: {angle_offset:.3f}° (阈值: {self.precise_angle_threshold:.3f}°)")
            elif is_roughly_aligned:
                print(f"[TRIGGER] ⚠️ 目标接近但未完全重合 - 角度偏移: {angle_offset:.3f}° (阈值: {self.angle_threshold:.3f}°)")
            
            return is_precisely_aligned
            
        else:
            # 使用像素阈值系统（向后兼容）
            distance = self.calculate_crosshair_distance(target_x, head_y, detection_center)
            
            # 使用更严格的精确对齐阈值
            is_precisely_aligned = distance <= self.precise_alignment_threshold
            
            # 额外检查：确保X和Y方向的偏移都很小
            x_offset = abs(target_x - detection_center[0]) * 160  # 转换为像素
            y_offset = abs(head_y - detection_center[1]) * 160    # 转换为像素
            
            # 要求X和Y方向的偏移都小于配置的阈值（更严格的重合检测）
            precise_x_y_check = x_offset <= self.xy_check_threshold and y_offset <= self.xy_check_threshold
            
            # 最终判断：距离和X/Y偏移都必须满足条件
            is_aligned = is_precisely_aligned and precise_x_y_check
            
            # 更新精确重合状态
            self.is_precisely_aligned_status = is_aligned
            
            if is_aligned:
                print(f"[TRIGGER] 🎯 目标精确重合！距离: {distance:.1f}px, X偏移: {x_offset:.1f}px, Y偏移: {y_offset:.1f}px")
            elif distance <= self.alignment_threshold:
                print(f"[TRIGGER] ⚠️ 目标接近但未完全重合 - 距离: {distance:.1f}px, X偏移: {x_offset:.1f}px, Y偏移: {y_offset:.1f}px")
            
            return is_aligned
    
    def _force_release_wasd_keys(self):
        """强制释放WASD键 - 优先使用Arduino键盘控制器"""
        try:
            # WASD静默期控制器已禁用，避免程序卡在静默期
            # 优先级1：Arduino键盘控制器
            if self.use_arduino_keyboard and self.arduino_keyboard:
                # 使用Arduino键盘控制器释放WASD键
                print("[TRIGGER] 🎮 使用Arduino强制释放WASD键...")
                
                # 释放所有WASD键
                wasd_keys = ['w', 'a', 's', 'd']
                for key in wasd_keys:
                    try:
                        self.arduino_keyboard.release_key(key)
                        print(f"[TRIGGER] ✅ Arduino释放 {key.upper()} 键")
                    except Exception as e:
                        print(f"[TRIGGER] ⚠️ Arduino释放 {key.upper()} 键失败: {e}")
                
                # 等待键盘释放完成
                time.sleep(self.keyboard_release_duration)
                print(f"[TRIGGER] ⏱️ WASD键释放完成，等待 {self.keyboard_release_duration}s")
                
            else:
                # 备用方案：使用Win32 API释放WASD键
                print("[TRIGGER] 🖥️ 使用Win32 API强制释放WASD键...")
                
                # WASD键的虚拟键码
                wasd_keycodes = {
                    'W': 0x57,
                    'A': 0x41, 
                    'S': 0x53,
                    'D': 0x44
                }
                
                for key_name, key_code in wasd_keycodes.items():
                    try:
                        # 强制释放键
                        win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                        print(f"[TRIGGER] ✅ Win32释放 {key_name} 键")
                    except Exception as e:
                        print(f"[TRIGGER] ⚠️ Win32释放 {key_name} 键失败: {e}")
                
                # 等待键盘释放完成
                time.sleep(self.keyboard_release_duration)
                print(f"[TRIGGER] ⏱️ WASD键释放完成，等待 {self.keyboard_release_duration}s")
                
        except Exception as e:
            print(f"[TRIGGER] ❌ 强制释放WASD键时发生错误: {e}")
    
    def fire_shots(self):
        """执行射击动作"""
        try:
            # 开火前停止鼠标移动和键盘输入
            self.is_firing = True
            self.stop_movement()
            
            # 强制释放WASD键 - 优先使用Arduino键盘控制器
            self._force_release_wasd_keys()
            
            # 停止WASD键移动（软件层面的备用方案）
            if self.keyboard_stop_enabled:
                self.keyboard_controller.pause_movement()
            
            print(f"[TRIGGER] 开始连发 {self.shots_per_trigger} 发子弹...")
            
            for i in range(self.shots_per_trigger):
                # 优先级：Arduino > G-Hub > Win32 API
                shot_success = False

                # 1. 复用当前进程已打开的 Arduino 串口，直接发送 'CL\n'
                try:
                    if (
                        not self.arduino_driver
                        or not self.arduino_driver.is_arduino_connected
                        or not self.arduino_driver.arduino_serial
                        or not getattr(self.arduino_driver.arduino_serial, 'is_open', False)
                    ):
                        print("[TRIGGER] ✗ Arduino串口未就绪，当前进程未持有连接")
                        shot_success = False
                    else:
                        ser = self.arduino_driver.arduino_serial
                        # 清空缓冲区并发送点击命令
                        try:
                            ser.flushInput(); ser.flushOutput()
                        except Exception:
                            # 某些驱动可能不支持 flush 方法，忽略
                            pass
                        ser.write(b'CL\n')
                        # 去除 200ms 等待与轮询读取，避免额外延迟
                        # 如需调试回显，可在此处非阻塞读取一次
                        try:
                            if ser.in_waiting:
                                _ = ser.read(ser.in_waiting)
                        except Exception:
                            pass
                        shot_success = True
                except Exception as e:
                    print(f"[TRIGGER] ❌ 复用串口开火失败: {e}")
                    shot_success = False
                    shot_success = False
               
                
                # 2. 备选：G-Hub驱动

                
                # 3. 最后备选：Win32 API

                
                if shot_success:
                    self.total_shots += 1
                
                # 连发间隔
                if i < self.shots_per_trigger - 1:
                    time.sleep(self.shot_interval)
            
            # 更新统计信息
            self.total_triggers += 1
            self.last_fire_time = time.time()
            
            # 开火结束后恢复鼠标移动和键盘输入
            self.is_firing = False
            self.resume_movement()
            
            # 结束WASD静默期
            if self.use_wasd_silence and self.wasd_silence_controller:
                try:
                    self.wasd_silence_controller.end_silence_period()
                    print("[TRIGGER] ✅ WASD静默期已结束")
                except Exception as e:
                    print(f"[TRIGGER] ⚠️ 结束WASD静默期失败: {e}")
            
            # 恢复WASD键移动
            if self.keyboard_stop_enabled:
                self.keyboard_controller.resume_movement()
            
            print(f"[TRIGGER] ✅ 连发完成！共{self.shots_per_trigger}发 (仅使用Arduino硬件驱动)")
            print(f"[TRIGGER] 📊 总触发次数: {self.total_triggers}, 总射击次数: {self.total_shots}")
            
        except Exception as e:
            print(f"[ERROR] 射击执行失败: {e}")
            # 确保在出错时也恢复控制
            self.is_firing = False
            self.resume_movement()
            if self.keyboard_stop_enabled:
                self.keyboard_controller.resume_movement()
    
    def check_alignment_status(self, target_x: float, target_y: float, 
                              detection_center: Tuple[float, float],
                              headshot_offset: float = 0.0,
                              game_fov: float = None, detection_size: int = None,
                              game_width: int = None, game_height: int = None) -> dict:
        """
        检查对齐状态，不受冷却时间影响，始终返回对齐信息
        
        Returns:
            dict: 包含对齐状态、距离、角度等信息的字典
        """
        if not self.enabled:
            return {"aligned": False, "reason": "扳机系统未启用"}
        
        # 始终进行对齐检测
        is_aligned = self.is_aligned(target_x, target_y, detection_center, headshot_offset,
                                   game_fov, detection_size, game_width, game_height)
        
        # 计算距离和角度信息
        distance = self.calculate_crosshair_distance(target_x, target_y, detection_center)
        angle = self.calculate_angle_offset(target_x, target_y, detection_center, headshot_offset,
                                          game_fov or 103.0, detection_size or 160,
                                          game_width or 2560, game_height or 1600)
        
        result = {
            "aligned": is_aligned,
            "distance_pixels": distance,
            "angle_degrees": angle,
            "on_cooldown": self.is_on_cooldown(),
            "cooldown_remaining": max(0, self.cooldown_duration - (time.time() - self.last_fire_time)) if self.is_on_cooldown() else 0,
            "can_fire": is_aligned and not self.is_on_cooldown()
        }
        
        if is_aligned:
            if self.is_on_cooldown():
                result["reason"] = f"对齐但冷却中，剩余{result['cooldown_remaining']:.2f}秒"
            else:
                result["reason"] = "已对齐，可以开火"
        else:
            result["reason"] = f"未对齐，距离{distance:.1f}像素，角度{angle:.2f}度"
        
        return result

    def is_precisely_aligned(self) -> bool:
        """检查是否处于精确重合状态"""
        return self.is_precisely_aligned_status
    
    def reset_alignment_status(self):
        """重置精确重合状态（当没有目标时调用）"""
        self.is_precisely_aligned_status = False

    def check_and_fire(self, target_x: float, target_y: float, 
                       detection_center: Tuple[float, float],
                       headshot_offset: float = 0.0,
                       game_fov: float = None, detection_size: int = None,
                       game_width: int = None, game_height: int = None) -> bool:
        """
        检查对齐并执行射击
        """
        # 检查扳机功能是否启用
        if not self.enabled:
            return False

        # 检查目标是否与准星对齐
        is_target_aligned = self.is_aligned(target_x, target_y, detection_center, headshot_offset,
                                          game_fov, detection_size, game_width, game_height)

        if is_target_aligned:
            current_time = time.time()
            self.alignment_events.append(current_time)

            # 清理过期事件
            self.alignment_events = [t for t in self.alignment_events if current_time - t <= self.fire_event_window]

            # 检查在时间窗口内是否满足开火阈值
            if len(self.alignment_events) >= self.fire_event_threshold:
                if not self.is_on_cooldown():
                    print(f"[TRIGGER] 🔥 在 {self.fire_event_window}s 内检测到 {len(self.alignment_events)} 次重合，满足开火条件！")
                    self.fire_shots()
                    self.alignment_events = []  # 开火后重置，避免连发
                    return True
        else:
            # 如果目标不再重合，可以考虑是否需要清空列表
            # 为了允许短暂中断，这里暂时不清空
            pass

        return False
    
    def get_status_info(self) -> dict:
        """获取扳机系统状态信息"""
        current_time = time.time()
        cooldown_remaining = max(0, self.cooldown_duration - (current_time - self.last_fire_time))
        
        return {
            "enabled": self.enabled,
            "alignment_threshold": self.alignment_threshold,
            "cooldown_duration": self.cooldown_duration,
            "cooldown_remaining": cooldown_remaining,
            "total_triggers": self.total_triggers,
            "total_shots": self.total_shots,
            "shots_per_trigger": self.shots_per_trigger,
            "is_on_cooldown": self.is_on_cooldown()
        }
    
    def print_status(self):
        """打印扳机系统状态"""
        status = self.get_status_info()
        print("\n" + "="*50)
        print("自动扳机系统状态报告")
        print("="*50)
        print(f"功能状态: {'启用' if status['enabled'] else '禁用'}")
        print(f"对齐阈值: {status['alignment_threshold']}像素")
        print(f"冷却时间: {status['cooldown_duration']}秒")
        print(f"连发数量: {status['shots_per_trigger']}发")
        print(f"总触发次数: {status['total_triggers']}")
        print(f"总射击次数: {status['total_shots']}")
        
        if status['is_on_cooldown']:
            print(f"冷却剩余: {status['cooldown_remaining']:.1f}秒")
        else:
            print("冷却状态: 就绪")
        
        print("="*50)
    
    def set_alignment_threshold(self, threshold: float):
        """设置对齐阈值"""
        self.alignment_threshold = threshold
        print(f"[INFO] 对齐阈值已设置为: {threshold}像素")
    
    def set_cooldown_duration(self, duration: float):
        """设置冷却时间"""
        self.cooldown_duration = duration
        print(f"[INFO] 冷却时间已设置为: {duration}秒")
    
    def set_shots_per_trigger(self, shots: int):
        """设置每次触发的射击次数"""
        self.shots_per_trigger = max(1, shots)
        print(f"[INFO] 连发数量已设置为: {self.shots_per_trigger}发")
    
    def set_shot_interval(self, interval: float):
        """设置连发间隔时间"""
        self.shot_interval = max(0.0, interval)
        print(f"[INFO] 连发间隔已设置为: {self.shot_interval}秒")
    
    def set_movement_callbacks(self, stop_callback=None, resume_callback=None):
        """
        设置移动控制回调函数
        
        Args:
            stop_callback: 停止移动的回调函数
            resume_callback: 恢复移动的回调函数
        """
        self.movement_stop_callback = stop_callback
        self.movement_resume_callback = resume_callback
        debug_log("[INFO] 移动控制回调函数已设置", tag="TRIGGER", throttle_ms=1000)
    
    def stop_movement(self):
        """停止鼠标移动"""
        if self.movement_stop_callback:
            self.movement_stop_callback()
            debug_log("[TRIGGER] 🛑 已停止鼠标移动", tag="TRIGGER", throttle_ms=500)
    
    def resume_movement(self):
        """恢复鼠标移动"""
        if self.movement_resume_callback:
            self.movement_resume_callback()
            debug_log("[TRIGGER] ▶️ 已恢复鼠标移动", tag="TRIGGER", throttle_ms=500)
    
    def is_currently_firing(self) -> bool:
        """检查是否正在开火"""
        return self.is_firing
    
    def set_keyboard_stop_enabled(self, enabled: bool):
        """
        设置是否启用键盘停止功能
        
        Args:
            enabled: 是否启用键盘停止功能
        """
        self.keyboard_stop_enabled = enabled
        status = "启用" if enabled else "禁用"
        debug_log(f"[INFO] 键盘停止功能已{status}", tag="KEYBOARD", throttle_ms=1000)
    
    def start_keyboard_monitoring(self):
        """开始键盘监控"""
        if hasattr(self, 'keyboard_controller'):
            self.keyboard_controller.start_monitoring()
            debug_log("[INFO] 键盘监控已启动", tag="KEYBOARD", throttle_ms=2000)
    
    def stop_keyboard_monitoring(self):
        """停止键盘监控"""
        if hasattr(self, 'keyboard_controller'):
            self.keyboard_controller.stop_monitoring()
            debug_log("[INFO] 键盘监控已停止", tag="KEYBOARD", throttle_ms=2000)
    
    def get_keyboard_status(self) -> dict:
        """获取键盘控制器状态"""
        if hasattr(self, 'keyboard_controller'):
            return self.keyboard_controller.get_status()
        return {}
    
    def reload_config(self):
        """重新加载配置"""
        if self.config_manager:
            try:
                self.config_manager.load_config()
                self._load_config_values()
                debug_log(f"[TRIGGER] 配置已重新加载: {self.config_manager.get_current_config()['name']}", tag="TRIGGER", throttle_ms=2000)
                return True
            except Exception as e:
                print(f"[TRIGGER] 重新加载配置失败: {e}")
                return False
        else:
            print("[TRIGGER] 配置系统不可用")
            return False
    
    def set_preset(self, preset_name):
        """设置预设配置
        
        Args:
            preset_name: 预设名称
            
        Returns:
            是否设置成功
        """
        if self.config_manager:
            if self.config_manager.set_preset(preset_name):
                self._load_config_values()
                print(f"[TRIGGER] 已切换到预设: {preset_name}")
                return True
            else:
                print(f"[TRIGGER] 预设不存在: {preset_name}")
                return False
        else:
            print("[TRIGGER] 配置系统不可用")
            return False
    
    def get_current_preset(self):
        """获取当前预设名称"""
        if self.config_manager:
            return self.config_manager.current_preset
        else:
            return "default"
    
    def list_presets(self):
        """列出所有可用预设"""
        if self.config_manager:
            self.config_manager.list_presets()
        else:
            print("[TRIGGER] 配置系统不可用")
    
    def get_config_info(self):
        """获取当前配置信息"""
        config_info = {
            'preset_name': self.get_current_preset(),
            'alignment_threshold': self.alignment_threshold,
            'precise_alignment_threshold': self.precise_alignment_threshold,
            'xy_check_threshold': self.xy_check_threshold,
            'cooldown_duration': self.cooldown_duration,
            'shots_per_trigger': self.shots_per_trigger,
            'shot_interval': self.shot_interval,
            'config_available': self.config_manager is not None
        }
        
        if self.config_manager:
            current_config = self.config_manager.get_current_config()
            config_info['preset_description'] = current_config.get('description', '')
            config_info['recommended_games'] = current_config.get('games', [])
        
        return config_info
    
    def apply_custom_thresholds(self, **kwargs):
        """应用自定义阈值设置
        
        Args:
            **kwargs: 阈值参数，如 alignment_threshold=3, cooldown_duration=0.4 等
        """
        updated = []
        
        if 'alignment_threshold' in kwargs:
            self.alignment_threshold = kwargs['alignment_threshold']
            updated.append(f"对齐阈值: {self.alignment_threshold}px")
        
        if 'precise_alignment_threshold' in kwargs:
            self.precise_alignment_threshold = kwargs['precise_alignment_threshold']
            updated.append(f"精确阈值: {self.precise_alignment_threshold}px")
        
        if 'xy_check_threshold' in kwargs:
            self.xy_check_threshold = kwargs['xy_check_threshold']
            updated.append(f"X/Y检查: {self.xy_check_threshold}px")
        
        if 'cooldown_duration' in kwargs:
            self.cooldown_duration = kwargs['cooldown_duration']
            updated.append(f"冷却时间: {self.cooldown_duration}s")
        
        if 'shots_per_trigger' in kwargs:
            self.shots_per_trigger = kwargs['shots_per_trigger']
            updated.append(f"连发数量: {self.shots_per_trigger}发")
        
        if 'shot_interval' in kwargs:
            self.shot_interval = kwargs['shot_interval']
            updated.append(f"连发间隔: {self.shot_interval}s")
        
        if updated:
            print(f"[TRIGGER] 已更新设置: {', '.join(updated)}")
        else:
            print("[TRIGGER] 未提供有效的阈值参数")


# 全局扳机系统实例
_trigger_system = None


def get_trigger_system() -> AutoTriggerSystem:
    """获取全局扳机系统实例"""
    global _trigger_system
    if _trigger_system is None:
        _trigger_system = AutoTriggerSystem()
        try:
            preset_name = _trigger_system.config_manager.get_current_config()['name'] if _trigger_system.config_manager else '默认值'
        except Exception:
            preset_name = '默认值'
        print(f"[TRIGGER_CONFIG] ⏱️ 冷却时间: {_trigger_system.cooldown_duration}s (来源: {preset_name})")
    return _trigger_system


def reset_trigger_system():
    """重置扳机系统"""
    global _trigger_system
    _trigger_system = None
    debug_log("[INFO] 扳机系统已重置", tag="TRIGGER", throttle_ms=2000)

# ==================== 调试日志辅助 ====================
# 说明：为减少信息级别日志在运行时的性能影响，这里提供一个轻量的调试输出函数。
# 与 main_onnxfix.py 保持一致风格，默认不输出，仅在 DEBUG_LOG=True 时打印，并支持按标签节流。
_last_debug_log_times = {}

def debug_log(message: str, tag: str = None, throttle_ms: int = None):
    """
    轻量调试输出函数（AutoTriggerSystem模块）
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


if __name__ == "__main__":
    # 测试代码
    trigger = get_trigger_system()
    
    # 测试基本功能
    print("测试自动扳机系统...")
    
    # 模拟检测中心
    detection_center = (0.5, 0.5)
    
    # 测试对齐检测
    print("\n测试对齐检测:")
    print(f"目标在中心 (0.5, 0.5): {trigger.is_aligned(0.5, 0.5, detection_center, 0.0, 103, 320, 2560, 1600)}")
    print(f"目标偏移较小 (0.51, 0.51): {trigger.is_aligned(0.51, 0.51, detection_center, 0.0, 103, 320, 2560, 1600)}")
    print(f"目标偏移较大 (0.6, 0.6): {trigger.is_aligned(0.6, 0.6, detection_center, 0.0, 103, 320, 2560, 1600)}")
    
    # 测试状态切换
    print("\n测试状态切换:")
    trigger.toggle_trigger()
    trigger.print_status()
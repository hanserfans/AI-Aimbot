import onnxruntime as ort
import numpy as np
import gc
import numpy as np
import cv2
# 纯净头部检测系统导入（无历史记忆）
from pure_current_frame_head_detection import (
    PureCurrentFrameHeadDetection, 
    SimpleSingleFrameCamera,
    PureRealtimeHeadSystem,
    initialize_pure_head_system,
    get_pure_head_position,
    clear_all_memory
)

# 优化的头部跟踪系统导入
from enhanced_latest_frame_system import EnhancedLatestFrameSystem, EnhancedMultiThreadedCamera
from optimized_head_tracking_system import OptimizedHeadTracker, HeadTrackingOptimizer
from realtime_head_detection_system import RealtimeHeadDetectionSystem

import time
import win32api
import win32con
import pandas as pd
import json
import os
from utils.general import (cv2, non_max_suppression, xyxy2xywh)
import torch

# Could be do with
# from config import *
# But we are writing it out for clarity for new devs
from config import aaMovementAmp, useMask, maskHeight, maskWidth, aaQuitKey, confidence, headshot_mode, cpsDisplay, visuals, onnxChoice, centerOfScreen, autoFire, autoFireShots, autoFireDelay, autoFireKey, screenShotWidth, screenShotHeight, pureTriggerFastMode, pureTriggerThreshold, showLiveFeed, maxTargets, targetSelectionStrategy
import gameSelection
from precision_aiming_optimizer import optimize_aiming_parameters, get_precision_report, save_aiming_data, load_aiming_data
from dynamic_tracking_system import get_aiming_system
from auto_trigger_system import get_trigger_system

from threshold_config import ThresholdConfig
from smooth_mouse_movement import create_smooth_movement_system

# 导入检测稳定性系统
try:
    from detection_stability_system import get_stability_system, create_stability_system
    DETECTION_STABILITY_AVAILABLE = True
    print("[INFO] ✅ 检测稳定性系统已加载到主程序")
except ImportError as e:
    print(f"[WARNING] 检测稳定性系统加载失败: {e}")
    DETECTION_STABILITY_AVAILABLE = False

# 导入头部位置平滑系统
try:
    from head_position_smoother import get_head_position_smoother, create_head_position_smoother
    HEAD_POSITION_SMOOTHER_AVAILABLE = True
    print("[INFO] ✅ 头部位置平滑系统已加载到主程序")
except ImportError as e:
    print(f"[WARNING] 头部位置平滑系统加载失败: {e}")
    HEAD_POSITION_SMOOTHER_AVAILABLE = False

# 导入目标队列系统
try:
    from target_queue_system import get_target_queue_system, create_target_queue_system
    TARGET_QUEUE_SYSTEM_AVAILABLE = True
    print("[INFO] ✅ 目标队列系统已加载到主程序")
except ImportError as e:
    print(f"[WARNING] 目标队列系统加载失败: {e}")
    TARGET_QUEUE_SYSTEM_AVAILABLE = False

# 导入增强检测配置
try:
    from enhanced_detection_config import get_enhanced_detection_config
    ENHANCED_DETECTION_AVAILABLE = True
    print("[INFO] ✅ 增强检测配置已加载到主程序")
except ImportError as e:
    print(f"[WARNING] 增强检测配置加载失败: {e}")
    ENHANCED_DETECTION_AVAILABLE = False

# 导入双GPU配置
try:
    from dual_gpu_config import initialize_dual_gpu, run_optimized_inference
    from gpu_monitor import start_gpu_monitoring, stop_gpu_monitoring, disable_gpu_monitoring, enable_gpu_monitoring
    DUAL_GPU_AVAILABLE = True
    print("[INFO] ✅ 双GPU配置已加载")
except ImportError as e:
    print(f"[WARNING] 双GPU配置加载失败: {e}")
    DUAL_GPU_AVAILABLE = False

# 导入GPU加速处理器
try:
    from gpu_accelerated_processor import get_gpu_processor, cleanup_gpu_processor
    from gpu_memory_manager import get_gpu_memory_manager, cleanup_gpu_memory_manager
    GPU_ACCELERATION_AVAILABLE = True
    print("[INFO] ✅ GPU加速处理器已加载")
except ImportError as e:
    print(f"[WARNING] GPU加速处理器加载失败: {e}")
    GPU_ACCELERATION_AVAILABLE = False

# 导入统一内存GPU处理器
try:
    from unified_memory_gpu_processor import get_unified_gpu_processor, cleanup_unified_gpu_processor
    from cuda_unified_memory_manager import get_unified_memory_manager, cleanup_unified_memory_manager
    UNIFIED_MEMORY_AVAILABLE = True
    print("[INFO] ✅ 统一内存GPU处理器已加载")
except ImportError as e:
    print(f"[WARNING] 统一内存GPU处理器加载失败: {e}")
    UNIFIED_MEMORY_AVAILABLE = False

# 导入目标预测和连续跟踪系统
try:
    from target_prediction_system import ContinuousTrackingSystem
    CONTINUOUS_TRACKING_AVAILABLE = True
    print("[INFO] ✅ 连续跟踪系统已加载（仅用于实时跟踪，不进行头部预测）")
except ImportError as e:
    print(f"[WARNING] 连续跟踪系统加载失败: {e}")
    CONTINUOUS_TRACKING_AVAILABLE = False

# 导入高性能截图系统
try:
    from high_performance_screenshot_system import HighPerformanceScreenshotSystem
    HIGH_PERFORMANCE_SCREENSHOT_AVAILABLE = True
    print("[INFO] ✅ 高性能截图系统已加载")
except ImportError as e:
    print(f"[WARNING] 高性能截图系统加载失败: {e}")
    HIGH_PERFORMANCE_SCREENSHOT_AVAILABLE = False

# 导入多线程AI处理系统
try:
    from multi_threaded_ai_processor import MultiThreadedAIProcessor
    MULTI_THREADED_AI_AVAILABLE = True
    print("[INFO] ✅ 多线程AI处理系统已加载")
except ImportError as e:
    print(f"[WARNING] 多线程AI处理系统加载失败: {e}")
    MULTI_THREADED_AI_AVAILABLE = False

# 导入性能监控系统
try:
    from performance_monitor_system import PerformanceMonitorSystem
    PERFORMANCE_MONITOR_AVAILABLE = True
    print("[INFO] ✅ 性能监控系统已加载")
except ImportError as e:
    print(f"[WARNING] 性能监控系统加载失败: {e}")
    PERFORMANCE_MONITOR_AVAILABLE = False

# 实际游戏窗口大小常量（用户提供）
ACTUAL_GAME_WIDTH = 2560   # 用户提供的实际游戏窗口宽度
ACTUAL_GAME_HEIGHT = 1600  # 用户提供的实际游戏窗口高度

# 检测和游戏参数常量
DETECTION_SIZE = 320       # 检测图像尺寸
GAME_FOV = 103.0          # 游戏水平FOV（度）

# 加载GUI配置
def load_gui_config():
    """加载GUI配置文件"""
    try:
        if os.path.exists("gui_config.json"):
            with open("gui_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            return config
        else:
            # 返回默认配置
            return {
                "control_method": "arduino",  # 默认使用Arduino
                "confidence": 0.4,
                "movement_amp": 0.4,
                "headshot_mode": True,
                "game_fov": 103,  # 默认FOV
                "max_targets": 5,  # 默认最大目标数量
                "target_selection_strategy": "closest"  # 默认筛选策略
            }
    except Exception as e:
        print(f"[ERROR] 加载配置失败: {str(e)}")
        # 返回默认配置
        return {
            "control_method": "arduino",  # 默认使用Arduino
            "confidence": 0.5,
            "movement_amp": 0.4,
            "headshot_mode": True,
            "game_fov": 103,  # 默认FOV
            "max_targets": 5,  # 默认最大目标数量
            "target_selection_strategy": "closest"  # 默认筛选策略
        }

# 加载配置
GUI_CONFIG = load_gui_config()
GAME_FOV = GUI_CONFIG.get("game_fov", 103)  # 获取用户配置的FOV，默认103

# 从GUI配置覆盖目标数量限制配置（如果存在）
if "max_targets" in GUI_CONFIG:
    maxTargets = GUI_CONFIG["max_targets"]
    print(f"[CONFIG] 从GUI配置加载最大目标数量: {maxTargets}")

if "target_selection_strategy" in GUI_CONFIG:
    targetSelectionStrategy = GUI_CONFIG["target_selection_strategy"]
    print(f"[CONFIG] 从GUI配置加载目标筛选策略: {targetSelectionStrategy}")

# FPS优化配置
FPS_OPTIMIZATION_ENABLED = True
TARGET_FPS = 300  # 目标FPS（基于测试结果294.3 FPS）
MAX_PROCESSING_TIME = 1.0 / TARGET_FPS  # 最大处理时间（约3.33ms）
ENABLE_GPU_ACCELERATION = True  # 启用GPU加速
REMOVE_SLEEP_DELAYS = True  # 移除睡眠延迟

# 高性能模式配置
HIGH_PERFORMANCE_MODE = True  # 启用高性能模式
DISABLE_MONITORING_IN_HIGH_PERF = True  # 在高性能模式下禁用监控
GPU_MONITOR_INTERVAL = 30.0 if HIGH_PERFORMANCE_MODE else 10.0  # 监控间隔（高性能模式下降低频率）

# 移动状态管理
movement_locked_target = None  # 锁定的移动目标
movement_lock_time = 0  # 移动锁定开始时间
MOVEMENT_LOCK_DURATION = 0.1  # 移动锁定持续时间（秒）
is_moving_to_target = False  # 是否正在移动到目标

print(f"[INFO] 🚀 FPS优化已启用 - 目标FPS: {TARGET_FPS}, 最大处理时间: {MAX_PROCESSING_TIME*1000:.2f}ms")
if HIGH_PERFORMANCE_MODE:
    print(f"[INFO] ⚡ 高性能模式已启用 - GPU监控间隔: {GPU_MONITOR_INTERVAL}s")

# 初始化鼠标控制系统（三层备选：Arduino > G-Hub > Win32 API）
ARDUINO_AVAILABLE = False
GHUB_AVAILABLE = False

# 1. 尝试导入Arduino驱动
try:
    from arduino_mouse_driver import ArduinoMouseDriver
    arduino_driver = ArduinoMouseDriver()
    arduino_driver.connect()  # 尝试连接
    
    # 检查真实的Arduino连接状态
    if arduino_driver.is_arduino_connected:
        print("[SUCCESS] Arduino 驱动连接成功")
        ARDUINO_AVAILABLE = True
    else:
        print("[WARNING] Arduino 驱动连接失败，尝试G-Hub驱动")
        arduino_driver = None
        ARDUINO_AVAILABLE = False
except ImportError as e:
    print(f"[WARNING] Arduino 驱动导入失败: {e}")
    arduino_driver = None
    ARDUINO_AVAILABLE = False

# Import Arduino keyboard controller with fallback - DISABLED
# 禁用Arduino键盘控制器，避免键盘检测导致的连接失败
print("[INFO] Arduino 键盘控制器已禁用，避免键盘检测冲突")
arduino_keyboard = None
ARDUINO_KEYBOARD_AVAILABLE = False

# Import WASD silence controller - DISABLED to prevent hanging
# 禁用WASD静默期控制器，因为会导致程序卡在静默期
print("[INFO] WASD静默期控制器已禁用，避免程序卡在静默期")
wasd_silence_controller = None
WASD_SILENCE_AVAILABLE = False

# 动态GPU显存分配函数
def get_optimal_gpu_memory_limit():
    """根据GPU实际显存容量和当前使用情况动态计算最优显存限制"""
    try:
        if torch.cuda.is_available():
            # 获取GPU总显存（字节）
            total_memory = torch.cuda.get_device_properties(0).total_memory
            total_memory_gb = total_memory / (1024**3)
            
            # 检查当前显存使用情况
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                current_usage_gb = 0
                if gpus:
                    current_usage_gb = gpus[0].memoryUsed / 1024  # MB转GB
            except:
                current_usage_gb = 0
            
            # 计算可用显存
            available_memory_gb = total_memory_gb - current_usage_gb
            
            # 智能动态分配策略：基于总显存和可用显存
            if total_memory_gb >= 12:  # 12GB+显存（如RTX 4070Ti+）
                allocation_ratio = 0.85 if available_memory_gb > 10 else 0.75
                gpu_mem_limit = int(total_memory * allocation_ratio)
                print(f"[INFO] 🚀 高端GPU模式: {total_memory_gb:.1f}GB总显存，{available_memory_gb:.1f}GB可用，分配{gpu_mem_limit/(1024**3):.1f}GB ({allocation_ratio*100:.0f}%)")
            elif total_memory_gb >= 8:  # 8GB显存（如RTX 4060）
                allocation_ratio = 0.80 if available_memory_gb > 6 else 0.70
                gpu_mem_limit = int(total_memory * allocation_ratio)
                print(f"[INFO] ⚡ 强GPU模式: {total_memory_gb:.1f}GB总显存，{available_memory_gb:.1f}GB可用，分配{gpu_mem_limit/(1024**3):.1f}GB ({allocation_ratio*100:.0f}%)")
            elif total_memory_gb >= 6:  # 6GB显存
                allocation_ratio = 0.75 if available_memory_gb > 4 else 0.65
                gpu_mem_limit = int(total_memory * allocation_ratio)
                print(f"[INFO] 🎯 中高端GPU模式: {total_memory_gb:.1f}GB总显存，{available_memory_gb:.1f}GB可用，分配{gpu_mem_limit/(1024**3):.1f}GB ({allocation_ratio*100:.0f}%)")
            elif total_memory_gb >= 4:  # 4GB显存
                allocation_ratio = 0.70 if available_memory_gb > 2.5 else 0.60
                gpu_mem_limit = int(total_memory * allocation_ratio)
                print(f"[INFO] 📱 中端GPU模式: {total_memory_gb:.1f}GB总显存，{available_memory_gb:.1f}GB可用，分配{gpu_mem_limit/(1024**3):.1f}GB ({allocation_ratio*100:.0f}%)")
            else:  # 4GB以下显存
                allocation_ratio = 0.60 if available_memory_gb > 2 else 0.50
                gpu_mem_limit = int(total_memory * allocation_ratio)
                print(f"[INFO] ⚠️ 入门级GPU模式: {total_memory_gb:.1f}GB总显存，{available_memory_gb:.1f}GB可用，分配{gpu_mem_limit/(1024**3):.1f}GB ({allocation_ratio*100:.0f}%)")
            
            # 安全检查：确保至少分配1GB，最多不超过可用显存的90%
            min_allocation = 1 * 1024 * 1024 * 1024  # 1GB
            max_allocation = int(available_memory_gb * 0.9 * 1024 * 1024 * 1024)
            
            gpu_mem_limit = max(min_allocation, min(gpu_mem_limit, max_allocation))
            
            # 如果显存紧张，给出警告
            if available_memory_gb < 2:
                print(f"[WARNING] ⚠️ 显存紧张！可用显存仅{available_memory_gb:.1f}GB，建议关闭其他GPU应用")
            elif available_memory_gb < 4:
                print(f"[INFO] 💡 显存适中，可用{available_memory_gb:.1f}GB，已优化分配策略")
            else:
                print(f"[INFO] ✅ 显存充足，可用{available_memory_gb:.1f}GB，启用强GPU模式")
            
            return gpu_mem_limit
        else:
            print("[WARNING] CUDA不可用，使用默认显存限制")
            return 2 * 1024 * 1024 * 1024  # 2GB默认值
    except Exception as e:
        print(f"[ERROR] 获取GPU显存信息失败: {e}")
        return 2 * 1024 * 1024 * 1024  # 2GB默认值

# 创建优化的ONNX会话配置
def create_optimized_onnx_session(model_path):
    """创建优化的ONNX会话，支持双GPU和动态显存优化"""
    
    # 优化的会话选项
    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    so.enable_mem_pattern = True
    so.enable_cpu_mem_arena = True
    so.enable_mem_reuse = True
    
    # 设置线程数以优化性能
    so.intra_op_num_threads = 16  # 优化线程数以充分利用32核CPU
    so.inter_op_num_threads = 8   # 增加并行操作线程数
    so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL  # 顺序执行以节省内存
    
    # 配置CUDA提供者（如果可用）
    providers = []
    if torch.cuda.is_available():
        # 动态获取最优显存限制
        gpu_mem_limit = get_optimal_gpu_memory_limit()
        
        cuda_provider_options = {
            'device_id': 0,
            'arena_extend_strategy': 'kNextPowerOfTwo',  # 更激进的内存分配策略
            'gpu_mem_limit': gpu_mem_limit,  # 使用动态计算的显存限制
            'cudnn_conv_algo_search': 'EXHAUSTIVE',  # 使用最优算法
            'do_copy_in_default_stream': True,
            'cudnn_conv_use_max_workspace': '1',
            'cudnn_conv1d_pad_to_nc1d': '1',
            'enable_cuda_graph': True,  # 启用CUDA图优化
            'tunable_op_enable': True,  # 启用可调优操作
            'cudnn_conv_use_max_workspace': True,  # 使用最大工作空间
        }
        providers.append(('CUDAExecutionProvider', cuda_provider_options))
        print(f"[INFO] ✅ CUDA提供者已配置，显存限制: {gpu_mem_limit/(1024**3):.1f}GB")
    
    # 添加CPU提供者作为备选
    providers.append('CPUExecutionProvider')
    
    try:
        # 创建ONNX会话
        session = ort.InferenceSession(model_path, sess_options=so, providers=providers)
        print(f"[INFO] ✅ ONNX会话创建成功，使用提供者: {session.get_providers()}")
        return session
    except Exception as e:
        print(f"[ERROR] ONNX会话创建失败: {e}")
        return None

# 2. 强制禁用G-Hub驱动，直接使用Win32 API（因为G-Hub不工作）
if not ARDUINO_AVAILABLE:
    print("[INFO] 强制禁用G-Hub驱动，因为G-Hub不工作")
    print("[INFO] 直接使用 Win32 API 作为鼠标控制方案")
    GHUB_AVAILABLE = False
    
    # 注释掉G-Hub导入，避免误用
    # try:
    #     from mouse_driver.MouseMove import ghub_move, ghub_click
    #     print("[SUCCESS] G-Hub 驱动导入成功")
    #     GHUB_AVAILABLE = True
    # except ImportError as e:
    #     print(f"[WARNING] G-Hub 驱动导入失败: {e}")
    #     print("[INFO] 将使用 Win32 API 作为备用方案")
    #     GHUB_AVAILABLE = False

# 打印当前使用的鼠标控制方法
if ARDUINO_AVAILABLE:
    print("[INFO] 当前鼠标控制方法: Arduino 硬件驱动")
elif GHUB_AVAILABLE:
    print("[INFO] 当前鼠标控制方法: G-Hub 驱动")
else:
    print("[INFO] 当前鼠标控制方法: Win32 API")

def move_mouse_direct(x, y):
    """直接鼠标移动函数（底层实现）"""
    try:
        if ARDUINO_AVAILABLE and arduino_driver:
            # 优先使用Arduino驱动
            success = arduino_driver.move_mouse(x, y)
            if success:
                print(f"[DEBUG] Arduino移动: ({x}, {y})")
                return True
            else:
                print("[WARNING] Arduino移动失败，切换到Win32 API")
        
        # 直接使用Win32 API（跳过G-Hub，因为G-Hub不工作）
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)
        print(f"[DEBUG] Win32移动: ({x}, {y})")
        return True
            
    except Exception as e:
        print(f"[ERROR] 鼠标移动失败: {e}")
        # 最后的备选方案：Win32 API
        try:
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)
            print(f"[DEBUG] 备用Win32移动: ({x}, {y})")
            return True
        except Exception as e2:
            print(f"[ERROR] 所有鼠标移动方法都失败: {e2}")
            return False


# 创建非阻塞平滑移动系统
from non_blocking_smooth_movement import create_non_blocking_smooth_movement_system
non_blocking_smooth_movement_system = create_non_blocking_smooth_movement_system(move_mouse_direct)

# 保留原有平滑移动系统作为备选
smooth_movement_system = create_smooth_movement_system(move_mouse_direct)


def move_mouse(x, y, use_smooth=True, use_non_blocking=True):
    """
    统一的鼠标移动函数，支持平滑移动和非阻塞移动
    
    Args:
        x: X轴移动距离
        y: Y轴移动距离
        use_smooth: 是否使用平滑移动（默认True）
        use_non_blocking: 是否使用非阻塞移动（默认True）
    """
    if use_smooth:
        if use_non_blocking:
            # 使用非阻塞平滑移动算法（推荐）
            return non_blocking_smooth_movement_system.move_to_target(x, y)
        else:
            # 使用传统阻塞平滑移动算法
            return smooth_movement_system.smooth_move_to_target(x, y)
    else:
        # 直接移动
        return move_mouse_direct(x, y)

def click_mouse(button='left'):
    """统一的鼠标点击函数，优先使用Arduino驱动，失败时回退到Win32 API"""
    try:
        if ARDUINO_AVAILABLE and arduino_driver:
            # 优先使用Arduino驱动 - 转换参数格式
            arduino_button_map = {
                'left': 'L',
                'right': 'R', 
                'middle': 'M'
            }
            arduino_button = arduino_button_map.get(button, 'L')
            result = arduino_driver.click_mouse(arduino_button)
            if result.get('success', False):
                print(f"[DEBUG] Arduino点击成功: {button} -> {arduino_button}")
                return True
            else:
                print(f"[WARNING] Arduino点击失败: {result.get('error', 'Unknown error')}，切换到Win32 API")
        
        # Arduino不可用或失败时，直接使用Win32 API
        if button == 'left':
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        elif button == 'right':
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        print(f"[DEBUG] Win32点击: {button}")
        return True
            
    except Exception as e:
        print(f"[ERROR] 鼠标点击失败: {e}")
        return False


def auto_fire():
    """
    自动开火函数 - 在瞄准完成后自动开火
    使用罗技G-Hub驱动进行鼠标点击，键盘按键仍使用Win32 API
    现在与AutoTriggerSystem共享冷却时间机制
    已删除WASD检测逻辑，直接开火
    """
    if not autoFire:
        return
    
    # 获取自动扳机系统实例来检查冷却时间
    trigger_system = get_trigger_system()
    
    # 检查是否在冷却时间内
    if trigger_system.is_on_cooldown():
        print(f"[AUTO_FIRE] ⏱️ 冷却中，剩余时间: {trigger_system.cooldown_duration - (time.time() - trigger_system.last_fire_time):.1f}秒")
        return
    
    # 🔥 直接开火（已删除WASD检测）
    print("[AUTO_FIRE] 🔥 直接开火，无WASD检测")
    
    # 使用Arduino驱动开火
    if ARDUINO_AVAILABLE:
        try:
            arduino_driver.click_mouse("L")
            print("[AUTO_FIRE] Arduino开火成功")
            # 更新扳机系统的开火时间
            trigger_system.last_fire_time = time.time()
            return
        except Exception as e:
            print(f"[AUTO_FIRE] Arduino开火失败: {e}")
    
    # Arduino不可用时，回退到Win32 API
    try:
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        time.sleep(0.01)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        print("[AUTO_FIRE] Win32 API开火成功")
        # 更新扳机系统的开火时间
        trigger_system.last_fire_time = time.time()
    except Exception as e:
        print(f"[AUTO_FIRE] Win32 API开火失败: {e}")

def check_realtime_fire_opportunity(targets_df, crosshair_x_320, crosshair_y_320):
    """
    实时检测鼠标与任意头部的重合，用于移动过程中的开火检测
    
    Args:
        targets_df: 当前帧检测到的所有目标
        crosshair_x_320: 当前准星在320坐标系中的X位置
        crosshair_y_320: 当前准星在320坐标系中的Y位置
    
    Returns:
        bool: 是否检测到开火机会并成功开火
    """
    # 获取扳机系统实例
    trigger_system = get_trigger_system()
    
    if not trigger_system.enabled or len(targets_df) == 0:
        return False
    
    # 遍历所有目标，检测是否有任何头部与准星重合
    for idx, target in targets_df.iterrows():
        # 获取目标的头部位置（假设头部在目标中心偏上）
        target_x = target['current_mid_x']
        target_y = target['current_mid_y']
        target_height = target['height']
        
        # 计算头部位置（在目标上方0.38处）
        head_x_320 = target_x
        head_y_320 = target_y - target_height * 0.38  # 使用固定0.38偏移
        
        # 计算准星与头部的距离
        distance = ((head_x_320 - crosshair_x_320)**2 + (head_y_320 - crosshair_y_320)**2)**0.5
        
        # 如果距离在开火阈值内
        if distance <= trigger_system.angle_threshold:
            print(f"[REALTIME_FIRE] 🎯 检测到开火机会！目标({head_x_320:.1f}, {head_y_320:.1f}) 距离: {distance:.1f}px")
            
            # 计算归一化坐标
            normalized_target_x = head_x_320 / DETECTION_SIZE
            normalized_target_y = head_y_320 / DETECTION_SIZE
            detection_center = (0.5, 0.5)
            
            # 进行扳机检测
            trigger_fired = trigger_system.check_and_fire(
                normalized_target_x, normalized_target_y, detection_center, 0,
                game_fov=GAME_FOV, detection_size=DETECTION_SIZE, 
                game_width=ACTUAL_GAME_WIDTH, game_height=ACTUAL_GAME_HEIGHT
            )
            
            if trigger_fired:
                print(f"[REALTIME_FIRE] 🔥 实时开火成功！")
                return True
            else:
                print(f"[REALTIME_FIRE] 开火条件不满足，距离: {distance:.1f}px")
    
    return False

def auto_fire_fast():
    """
    快速纯扳机模式开火函数 - 跳过WASD检测，专为纯扳机模式优化
    不进行任何键盘检测，直接开火以获得最快的响应速度
    """
    if not autoFire:
        return
    
    # 获取自动扳机系统实例来检查冷却时间
    trigger_system = get_trigger_system()
    
    # 检查是否在冷却时间内
    if trigger_system.is_on_cooldown():
        print(f"[FAST_FIRE] ⏱️ 冷却中，剩余时间: {trigger_system.cooldown_duration - (time.time() - trigger_system.last_fire_time):.1f}秒")
        return
    
    # 🚀 纯扳机模式：跳过所有WASD检测，直接开火
    print("[AUTO_FIRE_FAST] 🚀 启动快速纯扳机模式")
    
    try:
        # 直接开始开火，跳过所有WASD检测
        print(f"[AUTO_FIRE_FAST] 🔥 开始连续开火，共{autoFireShots}发，间隔{autoFireDelay}ms")
        
        for i in range(autoFireShots):
            if autoFireKey == "left_click":
                # 直接发送CL命令到Arduino，如果失败则使用备用方案
                success = False
                if ARDUINO_AVAILABLE and arduino_driver:
                    try:
                        result = arduino_driver.click_mouse("L")
                        if result.get('success', False):
                            print(f"[AUTO_FIRE_FAST] 🔥 第{i+1}发开火 (Arduino-CL)")
                            success = True
                        else:
                            print(f"[AUTO_FIRE_FAST] ⚠️ Arduino开火失败: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        print(f"[AUTO_FIRE_FAST] ⚠️ Arduino开火异常: {e}")
                
                # 如果Arduino失败，使用备用方案
                if not success:
                    if click_mouse("left"):
                        print(f"[AUTO_FIRE_FAST] 🔥 第{i+1}发开火 (备用方案-左键)")
                    else:
                        print(f"[AUTO_FIRE_FAST] ❌ 第{i+1}发开火失败")
                        
            elif autoFireKey == "right_click":
                # 直接发送CR命令到Arduino，如果失败则使用备用方案
                success = False
                if ARDUINO_AVAILABLE and arduino_driver:
                    try:
                        result = arduino_driver.click_mouse("R")
                        if result.get('success', False):
                            print(f"[AUTO_FIRE_FAST] 🔥 第{i+1}发开火 (Arduino-CR)")
                            success = True
                        else:
                            print(f"[AUTO_FIRE_FAST] ⚠️ Arduino开火失败: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        print(f"[AUTO_FIRE_FAST] ⚠️ Arduino开火异常: {e}")
                
                # 如果Arduino失败，使用备用方案
                if not success:
                    if click_mouse("right"):
                        print(f"[AUTO_FIRE_FAST] 🔥 第{i+1}发开火 (备用方案-右键)")
                    else:
                        print(f"[AUTO_FIRE_FAST] ❌ 第{i+1}发开火失败")
            elif autoFireKey == "space":
                # 键盘按键仍使用Win32 API
                win32api.keybd_event(0x20, 0, 0, 0)  # 按下空格
                if not REMOVE_SLEEP_DELAYS:
                    time.sleep(0.001)  # FPS优化：1ms延迟
                win32api.keybd_event(0x20, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放空格
                print(f"[AUTO_FIRE_FAST] 🔥 第{i+1}发开火 (空格)")
            elif autoFireKey == "f":
                # 键盘按键仍使用Win32 API
                win32api.keybd_event(0x46, 0, 0, 0)  # 按下F键
                if not REMOVE_SLEEP_DELAYS:
                    time.sleep(0.001)  # FPS优化：1ms延迟
                win32api.keybd_event(0x46, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放F键
                print(f"[AUTO_FIRE_FAST] 🔥 第{i+1}发开火 (F键)")
            elif autoFireKey == "r":
                # 键盘按键仍使用Win32 API
                win32api.keybd_event(0x52, 0, 0, 0)  # 按下R键
                if not REMOVE_SLEEP_DELAYS:
                    time.sleep(0.001)  # FPS优化：1ms延迟
                win32api.keybd_event(0x52, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放R键
                print(f"[AUTO_FIRE_FAST] 🔥 第{i+1}发开火 (R键)")
            
            # 如果不是最后一发，等待指定延迟
            if i < autoFireShots - 1:
                time.sleep(autoFireDelay / 1000.0)  # 转换毫秒为秒
                
        # 确定当前使用的驱动类型
        driver_type = "Arduino" if ARDUINO_AVAILABLE else ("G-Hub" if GHUB_AVAILABLE else "Win32 API")
        print(f"[AUTO_FIRE_FAST] ✅ 快速开火完成，共{autoFireShots}发 (使用{driver_type})")
        
        # 更新冷却时间
        trigger_system.last_fire_time = time.time()
        print(f"[AUTO_FIRE_FAST] ⏱️ 冷却时间已启动，持续{trigger_system.cooldown_duration}秒")
        
    except Exception as e:
        print(f"[ERROR] 快速自动开火失败: {e}")

def main():
    # 🎯 声明移动状态管理全局变量
    global movement_locked_target, movement_lock_time, is_moving_to_target
    
    # 显示启动横幅和扳机系统说明
    print("\n" + "="*60)
    print("🎯 AI瞄准机器人 - 自动扳机系统已集成")
    print("="*60)
    print("🔫 扳机系统功能:")
    print("   • 智能对齐检测 - 自动判断准星与目标对齐")
    print("   • G-Hub硬件级射击 - 使用罗技驱动进行鼠标控制")
    print("   • 连发射击 - 每次触发连发2枪")
    print("   • 冷却机制 - 0.5秒冷却防止过度射击")
    print("   • 默认启用 - 扳机系统启动时自动启用")
    print("\n⌨️  快捷键控制:")
    print("   • 鼠标右键 - 激活瞄准和扳机功能（按住瞄准+自动开火）")
    fast_mode_text = "快速模式" if pureTriggerFastMode else "标准模式"
    print(f"   • Caps Lock - 纯扳机模式（{fast_mode_text}，阈值: {pureTriggerThreshold}px）")
    print("   • R键 - 显示扳机系统状态")
    print("   • M键 - 切换瞄准模式")
    print("   • P键 - 显示精度报告")
    print("\n🔧 纯扳机模式配置:")
    print(f"   • 快速模式: {'启用' if pureTriggerFastMode else '禁用'} (跳过WASD检测)")
    print(f"   • 触发阈值: {pureTriggerThreshold} 像素")
    print("   • 配置文件: config.py (pureTriggerFastMode, pureTriggerThreshold)")
    print("="*60 + "\n")
    
    # External Function for running the game selection menu (gameSelection.py)
    result = gameSelection.gameSelection()
    if result is None:
        print("[ERROR] 游戏选择失败，程序退出")
        return
    
    camera, cWidth, cHeight, camera_type, videoGameWindow, region = result
    print("[INFO] 使用屏幕捕获方案: {}".format(camera_type))
    # 激活键状态缓存（用于连续移动）
    last_activation_time = 0
    activation_key_pressed = False
    last_right_mouse_state = False
    last_caps_lock_state = False
    

    # Used for forcing garbage collection
    count = 0
    sTime = time.time()
    
    # Live Feed窗口刷新控制（防止闪烁）
    live_feed_fps_limit = 60  # 限制Live Feed窗口刷新为60FPS
    live_feed_frame_interval = 1.0 / live_feed_fps_limit
    last_live_feed_time = 0

    
    # 初始化性能分析器
    from performance_analyzer import get_performance_analyzer
    perf_analyzer = get_performance_analyzer()
    print("[INFO] 🔍 性能分析器已初始化")
    
    # 初始化截图优化器
    from screenshot_optimizer import get_screenshot_optimizer
    screenshot_optimizer = get_screenshot_optimizer(camera, camera_type, region)  # 传递统一的截图区域
    screenshot_optimizer.enable_async_capture()  # 启用异步截图
    print("[INFO] 📸 截图优化器已初始化")
    print(f"[INFO] 📸 截图优化器使用区域: {region}")
    

    
    # 初始化精确瞄准优化器
    print("[INFO] 初始化精确瞄准优化器...")
    load_aiming_data()  # 加载历史数据
    
    # 初始化动态跟踪系统
    print("[INFO] 初始化动态跟踪系统...")
    aiming_system = get_aiming_system()
    aiming_system.tracker.movement_amp = aaMovementAmp
    print(f"[INFO] 当前瞄准模式: {aiming_system.aiming_mode}")
    
    # 初始化阈值配置管理器
    print("[INFO] 初始化阈值配置管理器...")
    threshold_config = ThresholdConfig()
    
    # 初始化自动扳机系统
    print("[INFO] 初始化自动扳机系统...")
    trigger_system = get_trigger_system()
    print(f"[INFO] 扳机功能状态: {'启用' if trigger_system.enabled else '禁用'}")
    print(f"[INFO] 对齐阈值: {trigger_system.alignment_threshold}像素")
    print(f"[INFO] 连发数量: {trigger_system.shots_per_trigger}发")
    print(f"[INFO] 冷却时间: {trigger_system.cooldown_duration}秒")
    print("[INFO] 🎯 扳机系统已就绪")
    print("   • 鼠标右键：瞄准+扳机模式")
    print("   • Caps Lock：纯扳机模式（不瞄准）")
    
    # 初始化连续跟踪系统
    continuous_tracker = None
    if CONTINUOUS_TRACKING_AVAILABLE:
        print("[INFO] 初始化连续跟踪系统...")
        continuous_tracker = ContinuousTrackingSystem(
            max_prediction_time=0.3,  # 最大预测时间300ms
            inertial_decay_rate=0.7,   # 惯性衰减率（调整为更快衰减）
            confidence_threshold=0.3   # 置信度阈值
        )
        print("[INFO] ✅ 连续跟踪系统已初始化")
        print("   • 目标预测：在未检测到目标时继续跟踪")
        print("   • 惯性移动：保持移动连续性")
        print("   • 智能切换：自动在实际目标和预测位置间切换")
    else:
        print("[WARNING] ⚠️ 连续跟踪系统不可用，将使用传统跟踪模式")
    
    # 初始化检测稳定性系统
    if DETECTION_STABILITY_AVAILABLE:
        print("[INFO] 初始化检测稳定性系统...")
        stability_system = create_stability_system(
            history_frames=10,          # 增加到10帧历史，提高稳定性
            confidence_smoothing=0.4,   # 增加置信度平滑系数
            position_smoothing=0.6,     # 大幅增加位置平滑系数，减少位置抖动
            min_detection_count=3,      # 增加到3次检测才认为稳定
            max_missing_frames=5        # 增加到5帧，避免短暂丢失
        )
        print("[INFO] ✅ 检测稳定性系统已初始化")
        print("   • 多帧历史：减少检测抖动")
        print("   • 置信度平滑：提高检测稳定性")
        print("   • 位置平滑：减少目标位置跳跃")
        print("   • 目标跟踪：保持目标连续性")
    else:
        print("[WARNING] ⚠️ 检测稳定性系统不可用，将使用原始检测结果")
        stability_system = None
    
    # 初始化头部位置平滑系统
    head_smoother = None
    if HEAD_POSITION_SMOOTHER_AVAILABLE:
        print("[INFO] 初始化头部位置平滑系统...")
        head_smoother = create_head_position_smoother(
            smoothing_factor=0.8,       # 高平滑系数，减少抖动
            history_size=10,            # 保持10个历史位置
            velocity_smoothing=0.6,     # 速度平滑
            min_movement_threshold=0.5  # 最小移动阈值
        )
        print("[INFO] ✅ 头部位置平滑系统已初始化")
        print("   • 高平滑系数：大幅减少位置抖动")
        print("   • 速度感知：根据移动速度调整平滑强度")
        print("   • 微小移动过滤：忽略小于0.5像素的移动")
        print("   • 位置预测：基于速度预测未来位置")
    else:
        print("[WARNING] ⚠️ 头部位置平滑系统不可用，将使用原始头部位置")
    
    # 配置动态跟踪系统的角度阈值
    print("[INFO] 配置动态跟踪系统角度阈值...")
    config_data = threshold_config.load_config()
    if config_data:
        aiming_system.update_threshold_config(
            angle_threshold=config_data.get('angle_threshold', 0.5),
            precise_angle_threshold=config_data.get('precise_angle_threshold', 0.3),
            use_angle_threshold=config_data.get('use_angle_threshold', True)
        )
    print("[INFO] ✅ 动态跟踪系统角度阈值配置完成")
    
    # 初始化高性能截图系统
    high_perf_screenshot = None
    if HIGH_PERFORMANCE_SCREENSHOT_AVAILABLE:
        print("[INFO] 初始化高性能截图系统...")
        high_perf_screenshot = HighPerformanceScreenshotSystem(
            target_fps=TARGET_FPS,
            num_capture_threads=2,      # 减少到2个截图线程，提高稳定性
            num_processing_threads=3,   # 减少到3个处理线程，避免帧序列混乱
            enable_gpu_acceleration=True,
            capture_method="auto"       # 自动选择最佳截图方法
        )
        high_perf_screenshot.start(region)
        print("[INFO] ✅ 高性能截图系统已启动")
        print(f"   • 目标FPS: {TARGET_FPS}")
        print(f"   • 截图线程数: 2")
        print(f"   • 处理线程数: 3")
        print(f"   • GPU加速: 启用")
        print(f"   • 截图方法: 自动选择")
        print(f"   • 截图区域: {region}")
    else:
        print("[WARNING] ⚠️ 高性能截图系统不可用，将使用传统截图方式")
    
    # 初始化多线程AI处理系统（增强版，集成帧时间顺序管理）
    multi_ai_processor = None
    if MULTI_THREADED_AI_AVAILABLE:
        print("[INFO] 初始化增强多线程AI处理系统（集成帧时间顺序管理）...")
        try:
            # 尝试导入增强版处理器
            from enhanced_multi_threaded_processor import EnhancedMultiThreadedAIProcessor
            
            multi_ai_processor = EnhancedMultiThreadedAIProcessor(
                model_path="yolov5s320Half.onnx",  # 使用实际的模型文件名
                num_inference_threads=2,    # 减少到2个推理线程，提高稳定性
                num_postprocess_threads=3,  # 减少到3个后处理线程，避免结果混乱
                batch_size=2,               # 减少批处理大小到2，提高响应速度
                enable_gpu_inference=True,
                max_frame_age=0.05          # 最大帧年龄50ms，确保处理最新帧
            )
            multi_ai_processor.start()
            print("[INFO] ✅ 增强多线程AI处理系统已启动")
            print(f"   • 推理线程数: 2")
            print(f"   • 后处理线程数: 3")
            print(f"   • 批处理大小: 2")
            print(f"   • GPU推理: 启用")
            print(f"   • 最大帧年龄: 50ms")
            print(f"   • 🕒 帧时间顺序管理: 启用")
            
        except ImportError:
            print("[WARNING] 增强版处理器不可用，使用标准版...")
            multi_ai_processor = MultiThreadedAIProcessor(
                model_path="yolov5s320Half.onnx",
                num_inference_threads=2,
                num_postprocess_threads=3,
                batch_size=2,
                enable_gpu_inference=True,
                enable_parallel_postprocess=True
            )
            multi_ai_processor.start()
            print("[INFO] ✅ 标准多线程AI处理系统已启动")
    else:
        print("[WARNING] ⚠️ 多线程AI处理系统不可用，将使用传统AI处理方式")
    
    # 初始化性能监控系统
    performance_monitor = None
    if PERFORMANCE_MONITOR_AVAILABLE:
        print("[INFO] 初始化性能监控系统...")
        performance_monitor = PerformanceMonitorSystem(
            update_interval=1.0,        # 每秒更新
            history_size=60,            # 保存60秒历史
            enable_gpu_monitoring=True,
            enable_detailed_stats=True
        )
        performance_monitor.start()
        print("[INFO] ✅ 性能监控系统已启动")
        print(f"   • 更新间隔: 1.0秒")
        print(f"   • 历史记录: 60个数据点")
        print(f"   • GPU监控: 启用")
        print(f"   • 详细统计: 启用")
    else:
        print("[WARNING] ⚠️ 性能监控系统不可用，将无法显示详细性能统计")
    
    # 移动控制状态管理
    movement_paused = False
    
    # 目标锁定机制变量
    locked_target = None  # 当前锁定的目标 {id, x, y, confidence, lock_time}
    lock_start_time = 0
    LOCK_DURATION = 3.0  # 目标锁定持续时间（秒）
    LOCK_DISTANCE_THRESHOLD = 30  # 目标锁定距离阈值（像素）
    target_lock_enabled = True  # 是否启用目标锁定
    
    # 🎯 头部跟踪记忆增强
    # 纯净头部检测系统（无历史记忆）
    pure_head_detector = PureCurrentFrameHeadDetection()
    
    # 移除所有历史记忆变量
    # head_position_history = []  # 已移除
    # MAX_HISTORY_SIZE = 0  # 已移除
    # head_velocity = {'x': 0, 'y': 0}  # 已移除
    
    print("[PURE_INTEGRATION] 纯净头部检测系统已初始化，无历史记忆")
    last_head_update_time = 0  # 上次头部位置更新时间
    last_mid_coord = None  # 上一帧的目标坐标
    
    print("[INFO] 🎯 目标锁定机制已初始化")
    print(f"[INFO] - 锁定持续时间: {LOCK_DURATION}秒")
    print(f"[INFO] - 锁定距离阈值: {LOCK_DISTANCE_THRESHOLD}像素")
    
    def pause_movement():
        """暂停鼠标移动"""
        nonlocal movement_paused
        movement_paused = True
        print("[MOVEMENT] ⏸️ 鼠标移动已暂停")
    
    def resume_movement():
        """恢复鼠标移动"""
        nonlocal movement_paused
        movement_paused = False
        print("[MOVEMENT] ▶️ 鼠标移动已恢复")
    
    # 设置扳机系统的移动控制回调
    trigger_system.set_movement_callbacks(pause_movement, resume_movement)
    
    # 启动键盘监控
    trigger_system.start_keyboard_monitoring()
    print("[INFO] 🎹 键盘监控已启动 - WASD键将在开火时自动暂停")

    # 目标锁定机制函数
    def calculate_head_position(target_row):
        """计算目标头部位置（始终在320坐标系下计算）"""
        mid_x = target_row['current_mid_x']
        mid_y = target_row['current_mid_y']
        box_height = target_row['height']
        
        # 修复：在增强检测模式下，所有瞄准计算都应该在320坐标系下进行
        # 不在这里进行坐标转换，保持320坐标系的一致性
        print(f"[DEBUG] 头部位置计算（320坐标系）: 目标({mid_x:.1f}, {mid_y:.1f}), 高度{box_height:.1f}")
        
        # 头部位置计算公式 = 目标中心 - box_height*0.38（向上偏移）
        # 使用固定0.38偏移，简洁有效
        headshot_offset = box_height * 0.38  # box_height*0.38的向上偏移
        
        head_x = mid_x
        head_y = mid_y - headshot_offset  # 头部位置：向上偏移box_height*0.38
        
        # 应用头部位置平滑
        if head_smoother is not None:
            smoothed_head_x, smoothed_head_y = head_smoother.update_position(head_x, head_y)
            print(f"[DEBUG] 原始头部位置: ({head_x:.1f}, {head_y:.1f})")
            print(f"[DEBUG] 平滑头部位置: ({smoothed_head_x:.1f}, {smoothed_head_y:.1f})")
            print(f"[DEBUG] 位置偏移: ({smoothed_head_x-head_x:.1f}, {smoothed_head_y-head_y:.1f})")
            return smoothed_head_x, smoothed_head_y
        else:
            print(f"[DEBUG] 计算头部位置: ({head_x:.1f}, {head_y:.1f}), 偏移: {headshot_offset:.1f}像素 (box_height*0.38)")
            return head_x, head_y
    
    def calculate_smoothed_head_position(target_x, target_y, box_height):
        """计算平滑的头部位置（辅助函数）"""
        headshot_offset = box_height * 0.38
        head_x = target_x
        head_y = target_y - headshot_offset  # 使用固定0.38偏移
        
        # 应用头部位置平滑
        if head_smoother is not None:
            smoothed_head_x, smoothed_head_y = head_smoother.update_position(head_x, head_y)
            return smoothed_head_x, smoothed_head_y
        else:
            return head_x, head_y
    
    def create_target_id(target_row):
        """创建基于头部位置的目标唯一标识"""
        head_x, head_y = calculate_head_position(target_row)
        confidence = target_row['confidence']
        return f"head_{int(head_x)}_{int(head_y)}_{int(confidence*100)}"
    
    def update_head_position_history(head_x, head_y, current_time):
        """纯净头部位置处理（无历史记忆）"""
        # 纯净系统不需要历史记忆，直接返回
        print(f"[PURE_HEAD] 当前帧头部位置: ({head_x:.1f}, {head_y:.1f}) - 无历史记忆")
        return True
    
    def predict_head_position(prediction_time_ms=50):
        """纯净系统不使用预测"""
        print("[PURE_HEAD] 纯净系统不使用预测功能")
        return None
    
    def get_stable_head_position():
        """纯净系统不使用稳定位置"""
        print("[PURE_HEAD] 纯净系统不使用稳定位置功能")
        return None
    
    def find_best_target_with_lock(targets, current_time):
        """智能目标选择：优先考虑锁定目标（基于头部位置），然后选择最佳新目标"""
        nonlocal locked_target, lock_start_time
        
        if not target_lock_enabled or len(targets) == 0:
            return targets.iloc[0] if len(targets) > 0 else None
        
        # 检查当前锁定是否过期
        if locked_target and (current_time - lock_start_time) > LOCK_DURATION:
            print(f"[TARGET_LOCK] 🔓 目标锁定已过期 ({LOCK_DURATION}秒)")
            locked_target = None
            lock_start_time = 0
        
        # 如果有锁定目标，尝试在当前检测结果中找到它
        if locked_target:
            locked_head_x, locked_head_y = locked_target['head_x'], locked_target['head_y']
            
            # 计算当前所有目标的头部位置
            targets['head_x'] = targets.apply(lambda row: calculate_head_position(row)[0], axis=1)
            targets['head_y'] = targets.apply(lambda row: calculate_head_position(row)[1], axis=1)
            
            # 在当前目标中寻找与锁定目标头部最接近的目标
            targets['distance_to_locked_head'] = targets.apply(
                lambda row: ((row['head_x'] - locked_head_x)**2 + (row['head_y'] - locked_head_y)**2)**0.5,
                axis=1
            )
            
            # 找到距离锁定目标头部最近的目标
            closest_to_locked = targets.loc[targets['distance_to_locked_head'].idxmin()]
            
            # 如果距离在阈值内，继续锁定这个目标
            if closest_to_locked['distance_to_locked_head'] <= LOCK_DISTANCE_THRESHOLD:
                # 🎯 关键改进：使用平滑更新锁定目标的头部位置
                new_head_x = closest_to_locked['head_x']
                new_head_y = closest_to_locked['head_y']
                
                # 更新头部位置历史记录
                update_head_position_history(new_head_x, new_head_y, current_time)
                
                # 应用头部位置平滑（避免锁定位置跳跃）
                if head_smoother is not None:
                    smoothed_head_x, smoothed_head_y = head_smoother.update_position(new_head_x, new_head_y)
                    locked_target['head_x'] = smoothed_head_x
                    locked_target['head_y'] = smoothed_head_y
                    print(f"[TARGET_LOCK] 🎯 平滑更新锁定头部位置: 原始({new_head_x:.1f},{new_head_y:.1f}) -> 平滑({smoothed_head_x:.1f},{smoothed_head_y:.1f})")
                else:
                    locked_target['head_x'] = new_head_x
                    locked_target['head_y'] = new_head_y
                    print(f"[TARGET_LOCK] 🎯 直接更新锁定头部位置: ({new_head_x:.1f},{new_head_y:.1f})")
                
                locked_target['x'] = closest_to_locked['current_mid_x']  # 保留中心点用于其他逻辑
                locked_target['y'] = closest_to_locked['current_mid_y']
                locked_target['confidence'] = closest_to_locked['confidence']
                
                print(f"[TARGET_LOCK] 🎯 继续锁定目标头部 - 距离: {closest_to_locked['distance_to_locked_head']:.1f}px")
                return closest_to_locked
            else:
                print(f"[TARGET_LOCK] 🔓 目标头部移动过远，解除锁定 - 距离: {closest_to_locked['distance_to_locked_head']:.1f}px")
                # 清除头部位置历史记录
                # 纯净系统无需清除历史记忆
                print("[PURE_HEAD] 纯净系统无需清除历史记忆")
                locked_target = None
                lock_start_time = 0
        
        # 没有锁定目标或锁定目标丢失，选择新目标
        # 计算所有目标的头部位置（如果还没有计算）
        if 'head_x' not in targets.columns:
            targets['head_x'] = targets.apply(lambda row: calculate_head_position(row)[0], axis=1)
            targets['head_y'] = targets.apply(lambda row: calculate_head_position(row)[1], axis=1)
        
        best_target = targets.iloc[0]  # 已经按距离准星排序
        
        # 🎯 锁定新目标时初始化头部记忆
        # 清除旧的头部位置历史记录
        # 纯净系统无需清除历史记忆
        # 优化的记忆清除
        # 纯净系统无需清除历史记忆
        # 纯净系统无需清除历史记忆
        print("[OPTIMIZED_HEAD] 已清除优化头部跟踪记忆")
        # 纯净系统无需清除历史记忆
        # 纯净系统无需清除历史记忆
        
        # 记录新目标的初始头部位置
        update_head_position_history(best_target['head_x'], best_target['head_y'], current_time)
        
        # 锁定新目标（基于头部位置）
        locked_target = {
            'head_x': best_target['head_x'],
            'head_y': best_target['head_y'],
            'x': best_target['current_mid_x'],  # 保留中心点用于其他逻辑
            'y': best_target['current_mid_y'],
            'confidence': best_target['confidence']
        }
        lock_start_time = current_time
        
        print(f"[TARGET_LOCK] 🔒 锁定新目标头部 - 位置: ({best_target['head_x']:.1f}, {best_target['head_y']:.1f})")
        print(f"[HEAD_MEMORY] 🧠 初始化头部记忆系统")
        return best_target
    
    def get_lock_status():
        """获取头部锁定状态信息"""
        if not locked_target:
            return "无头部锁定"
        
        remaining_time = LOCK_DURATION - (time.time() - lock_start_time)
        if remaining_time <= 0:
            return "头部锁定过期"
        
        head_x = locked_target.get('head_x', 0)
        head_y = locked_target.get('head_y', 0)
        
        # 纯净系统状态信息（无历史记忆）
        history_count = 0  # 纯净系统无历史记忆
        velocity_info = "纯净模式(无速度记忆)"
        
        # 如果启用了增强检测，显示原始320坐标和放大后坐标
        if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
            # 将放大后的坐标转换回320坐标系显示
            original_x = head_x / enhanced_config.SCALE_FACTOR
            original_y = head_y / enhanced_config.SCALE_FACTOR
            head_pos = f"({head_x:.0f},{head_y:.0f})[960] 原始({original_x:.0f},{original_y:.0f})[320]"
        else:
            head_pos = f"({head_x:.0f},{head_y:.0f})"
            
        return f"锁定头部{head_pos} 剩余{remaining_time:.1f}s 纯净模式 {velocity_info}"
    
    def get_predicted_or_locked_head_position():
        """获取预测的或锁定的头部位置（用于检测丢失时的补偿）"""
        if target_lock_enabled and locked_target:
            # 如果有锁定目标，优先使用锁定的头部位置
            return {
                'x': locked_target['head_x'],
                'y': locked_target['head_y'],
                'source': 'locked'
            }
        elif head_position_history:
            # 如果没有锁定目标但有历史记录，使用预测位置
            predicted_pos = predict_head_position()
            if predicted_pos:
                return {
                    'x': predicted_pos['x'],
                    'y': predicted_pos['y'],
                    'source': 'predicted'
                }
            else:
                # 使用稳定位置作为备选
                stable_pos = get_stable_head_position()
                if stable_pos:
                    return {
                        'x': stable_pos['x'],
                        'y': stable_pos['y'],
                        'source': 'stable'
                    }
        
        return None

    # 初始化增强检测配置
    global ENHANCED_DETECTION_AVAILABLE
    enhanced_config = None
    if ENHANCED_DETECTION_AVAILABLE:
        try:
            enhanced_config = get_enhanced_detection_config()
            print(f"[INFO] ✅ 增强检测配置初始化成功 - 截取区域: {enhanced_config.CAPTURE_SIZE}x{enhanced_config.CAPTURE_SIZE}")
        except Exception as e:
            print(f"[WARNING] 增强检测配置初始化失败: {e}")
            enhanced_config = None
            ENHANCED_DETECTION_AVAILABLE = False

    # 设置环境变量优化内存
    os.environ['OMP_NUM_THREADS'] = '16'  # 优化OpenMP线程数
    os.environ['MKL_NUM_THREADS'] = '16'  # 优化MKL线程数
    os.environ['NUMEXPR_NUM_THREADS'] = '16'  # 优化NumExpr线程数
    
    # 强制垃圾回收释放内存
    gc.collect()
    print("[INFO] 🧹 内存优化完成")


    
    # 初始化GPU加速处理器和内存管理器
    gpu_processor = None
    gpu_memory_manager = None
    unified_gpu_processor = None
    unified_memory_manager = None
    
    # 检查是否启用统一内存（从配置文件读取或默认启用）
    use_unified_memory = GUI_CONFIG.get("use_unified_memory", True)
    unified_memory_size_gb = GUI_CONFIG.get("unified_memory_size_gb", 2.0)
    
    if use_unified_memory and UNIFIED_MEMORY_AVAILABLE:
        print("[INFO] 🌐 初始化统一内存GPU处理器...")
        try:
            # 动态检测可用GPU数量
            available_gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
            if available_gpu_count >= 2 and DUAL_GPU_AVAILABLE:
                device_ids = [0, 1]
                print(f"[INFO] 🔍 检测到 {available_gpu_count} 个GPU，使用双GPU配置")
            elif available_gpu_count >= 1:
                device_ids = [0]
                print(f"[INFO] 🔍 检测到 {available_gpu_count} 个GPU，使用单GPU配置")
            else:
                device_ids = []
                print("[WARNING] 未检测到可用GPU，统一内存功能将受限")
            
            # 初始化统一内存管理器
            unified_memory_manager = get_unified_memory_manager(device_ids, unified_memory_size_gb)
            
            # 初始化统一内存GPU处理器
            unified_gpu_processor = get_unified_gpu_processor(
                device_id=0, 
                unified_memory_size_gb=unified_memory_size_gb,
                enable_auto_migration=True
            )
            
            print("[INFO] ✅ 统一内存GPU处理器初始化成功")
            print(f"[INFO] 🌐 统一内存池大小: {unified_memory_size_gb:.1f}GB")
            print("[INFO] 🔄 自动内存迁移已启用")
            
            # 显示统一内存使用情况
            memory_usage = unified_gpu_processor.get_memory_usage()
            for device, info in memory_usage.items():
                if isinstance(info, dict) and 'percent' in info:
                    print(f"[INFO] 📊 {device} 内存使用: {info['percent']:.1f}%")
                    
        except Exception as e:
            print(f"[WARNING] 统一内存GPU处理器初始化失败: {e}")
            print("[INFO] 🔄 回退到传统GPU加速处理器...")
            unified_gpu_processor = None
            unified_memory_manager = None
            use_unified_memory = False
    
    # 如果统一内存不可用或初始化失败，使用传统GPU加速
    if not use_unified_memory and GPU_ACCELERATION_AVAILABLE:
        print("[INFO] 🚀 初始化传统GPU加速处理器...")
        try:
            # 只使用第一个GPU（cuda:0）
            device_ids = [0]
            print("[INFO] 🔍 使用单GPU配置 (cuda:0)")
            gpu_memory_manager = get_gpu_memory_manager(device_ids, pool_size_gb=4.0)
            
            # 初始化GPU处理器
            gpu_processor = get_gpu_processor(device_id=0)
            
            print("[INFO] ✅ 传统GPU加速处理器初始化成功")
            print("[INFO] 💾 GPU内存管理器初始化成功")
            
            # 显示GPU内存使用情况
            memory_usage = gpu_memory_manager.get_memory_usage()
            for device, info in memory_usage.items():
                if 'percent' in info:
                    print(f"[INFO] 📊 {device} 内存使用: {info['percent']:.1f}%")
                    
        except Exception as e:
            print(f"[WARNING] 传统GPU加速初始化失败: {e}")
            gpu_processor = None
            gpu_memory_manager = None

    # 创建优化的ONNX会话
    if DUAL_GPU_AVAILABLE:
        print("[INFO] 🔄 初始化双GPU配置...")
        dual_gpu_manager = initialize_dual_gpu('yolov5s320Half.onnx')
        if dual_gpu_manager:
            print("[INFO] ✅ 双GPU管理器初始化成功")
            # 根据高性能模式配置启动GPU监控
            if HIGH_PERFORMANCE_MODE and DISABLE_MONITORING_IN_HIGH_PERF:
                print("[INFO] ⚡ 高性能模式：GPU监控已禁用以最大化瞄准性能")
                start_gpu_monitoring(monitor_interval=GPU_MONITOR_INTERVAL, enable_monitoring=False)
            else:
                start_gpu_monitoring(monitor_interval=GPU_MONITOR_INTERVAL, enable_monitoring=True)
        else:
            print("[WARNING] 双GPU初始化失败，使用单GPU模式")
            ort_sess = create_optimized_onnx_session('yolov5s320Half.onnx')
    else:
        ort_sess = create_optimized_onnx_session('yolov5s320Half.onnx')


    


    # Used for colors drawn on bounding boxes
    COLORS = np.random.uniform(0, 255, size=(1500, 3))

    # 设置非阻塞平滑移动系统的开火检测回调
    def fire_check_callback():
        """移动过程中的开火检测回调函数"""
        try:
            # 获取当前准星位置（320坐标系）
            crosshair_x_320 = centerOfScreen[0] * 320 // screenShotWidth
            crosshair_y_320 = centerOfScreen[1] * 320 // screenShotHeight
            
            # 检查是否有可开火的机会（使用最新的目标数据）
            if hasattr(fire_check_callback, 'latest_targets') and fire_check_callback.latest_targets is not None:
                targets_df = fire_check_callback.latest_targets
                if len(targets_df) > 0:
                    # 执行实时开火检测
                    fire_result = check_realtime_fire_opportunity(targets_df, crosshair_x_320, crosshair_y_320)
                    if fire_result:
                        print("[FIRE_CALLBACK] 🔥 移动过程中检测到开火机会")
                        return True
            return False
        except Exception as e:
            print(f"[FIRE_CALLBACK] ⚠️ 开火检测回调异常: {e}")
            return False
    
    # 初始化回调函数的目标数据
    fire_check_callback.latest_targets = None
    
    # 设置开火检测回调
    non_blocking_smooth_movement_system.set_fire_check_callback(fire_check_callback)
    print("[INFO] ✅ 非阻塞平滑移动系统开火检测回调已设置")
    print("[INFO] 🎯 移动过程中将进行实时开火检测，提高开火频率")

    # 系统就绪提示
    print("\n🚀 系统已就绪，开始运行...")
    print("💡 提示: 按鼠标右键激活瞄准+扳机，按Caps Lock激活纯扳机模式，按 R 键查看状态")
    print("⚠️  注意: 按 Q 键退出程序\n")
    
    # 初始化Live Feed窗口（如果启用）
    if showLiveFeed:
        # 确定Live Feed窗口尺寸
        if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
            live_feed_size = enhanced_config.CAPTURE_SIZE  # 640x640
            print(f"[INFO] 🖥️ 初始化Live Feed窗口 - 增强检测模式: {live_feed_size}x{live_feed_size}")
        else:
            live_feed_size = 320  # 默认320x320
            print(f"[INFO] 🖥️ 初始化Live Feed窗口 - 标准模式: {live_feed_size}x{live_feed_size}")
        
        # 创建可调整大小的窗口并设置初始尺寸
        cv2.namedWindow('Live Feed', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Live Feed', live_feed_size, live_feed_size)
        print(f"[INFO] ✅ Live Feed窗口已初始化为 {live_feed_size}x{live_feed_size} 像素")
    
    # Main loop Quit if Q is pressed
    last_mid_coord = None
    last_report_time = time.time()
    last_mode_switch_time = time.time()
    
    while win32api.GetAsyncKeyState(ord(aaQuitKey)) == 0:
        processing_start_time = time.time()
        
        # 检测P键显示精度报告
        if win32api.GetAsyncKeyState(ord('P')) & 0x8000:
            current_time = time.time()
            if current_time - last_report_time > 2:  # 防止重复触发
                print("\n" + "="*50)
                print(get_precision_report())
                print("="*50 + "\n")
                last_report_time = current_time
        
        # M键功能已移除 - 现在只使用静态瞄准模式
        
        # 检测鼠标第二个侧键切换扳机系统 - 已禁用
        # if win32api.GetAsyncKeyState(0x06) & 0x8000:  # 0x06 是鼠标第二个侧键的虚拟键码
        #     current_time = time.time()
        #     if current_time - last_mode_switch_time > 1:  # 防止重复触发
        #         trigger_system.toggle_trigger()
        #         last_mode_switch_time = current_time
        
        # 检测R键显示扳机系统状态
        if win32api.GetAsyncKeyState(ord('R')) & 0x8000:
            current_time = time.time()
            if current_time - last_report_time > 2:  # 防止重复触发
                trigger_system.print_status()
                last_report_time = current_time
        
        # 检查跟踪超时
        aiming_system.check_timeout()

        # 开始截图计时
        perf_analyzer.start_timer('screenshot')
        
        # 使用高性能截图系统（如果可用）
        if high_perf_screenshot is not None:
            # 从高性能截图系统获取处理好的帧
            frame_data = high_perf_screenshot.get_latest_frame()
            if frame_data is not None:
                npImg = frame_data['frame']
                print(f"[DEBUG] 🎯 使用高性能截图系统最新帧")
                # 记录性能监控数据
                if performance_monitor is not None:
                    performance_monitor.record_timing('screenshot_time', frame_data.get('capture_time', 0))
                    performance_monitor.record_timing('processing_time', frame_data.get('processing_time', 0))
            else:
                # 回退到传统截图 - 强制使用最新帧，禁用缓存
                npImg = screenshot_optimizer.get_optimized_frame(use_cache=False)
                print(f"[DEBUG] 🎯 回退到传统截图系统最新帧（无缓存）")
        else:
            # 使用传统优化截图捕获 - 强制使用最新帧，禁用缓存
            npImg = screenshot_optimizer.get_optimized_frame(use_cache=False)
            print(f"[DEBUG] 🎯 使用传统截图系统最新帧（无缓存）")
            
        if npImg is None:
            continue
            
        # 结束截图计时
        perf_analyzer.end_timer('screenshot')

        # 开始预处理计时
        perf_analyzer.start_timer('preprocessing')

        # 🔥 帧同步修复：延迟创建display_img，确保与最终处理的帧完全同步
        # 注意：display_img将在所有图像处理完成后创建，确保帧同步
        display_img = None  # 延迟创建，确保帧同步
        print(f"[FRAME_SYNC] 延迟创建display_img，确保与头部计算使用相同帧")

        # 应用掩码（如果启用）
        from config import maskSide # "temporary" workaround for bad syntax
        if useMask:
            mask_config = {
                'enabled': True,
                'side': maskSide,
                'width': maskWidth,
                'height': maskHeight
            }
            npImg = screenshot_optimizer.apply_mask_optimized(npImg, mask_config)
            print(f"[FRAME_SYNC] 掩码应用后npImg尺寸: {npImg.shape[1]}x{npImg.shape[0]}")

        # Store original image for coordinate calculations
        original_img = npImg.copy()
        
        # 增强检测：如果启用了增强检测配置，应用坐标缩放
        if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
            # 记录原始截取区域尺寸用于坐标转换
            original_capture_size = npImg.shape[0]  # 应该是640（增强检测配置的CAPTURE_SIZE）
            print(f"[DEBUG] 增强检测模式：原始截取区域 {original_capture_size}x{original_capture_size}")
        
        # 🔥 重要：仅对AI检测图像进行缩放，display_img保持原始640x640尺寸
        if npImg.shape[0] != 320 or npImg.shape[1] != 320:
            if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
                # 使用增强检测配置的缩放方法（仅缩放npImg用于AI检测）
                npImg = enhanced_config.resize_for_model(npImg)
                print(f"[DEBUG] 增强检测缩放：{original_capture_size}x{original_capture_size} -> 320x320 (仅AI检测)")
                if display_img is not None:
                    print(f"[LIVE_FEED_FIX] display_img保持原始尺寸: {display_img.shape[1]}x{display_img.shape[0]}")
                else:
                    print(f"[LIVE_FEED_FIX] display_img尚未创建")
            else:
                # 使用原有的缩放方法（仅缩放npImg用于AI检测）
                npImg = screenshot_optimizer.resize_frame_optimized(npImg, (320, 320))
                if display_img is not None:
                    print(f"[LIVE_FEED_FIX] display_img保持原始尺寸: {display_img.shape[1]}x{display_img.shape[0]}")
                else:
                    print(f"[LIVE_FEED_FIX] display_img尚未创建")

        # 使用GPU加速预处理（优先使用统一内存处理器）
        if unified_gpu_processor is not None and onnxChoice == 3:
            # 统一内存GPU加速预处理 - 自动CPU-GPU内存迁移
            try:
                im_tensor = unified_gpu_processor.preprocess_image_gpu(npImg, target_size=(320, 320))
                # 转换为numpy数组用于ONNX Runtime
                im = im_tensor.cpu().numpy()
                print(f"[DEBUG] 统一内存GPU预处理完成，形状: {im.shape}, 设备: {im_tensor.device}")
            except Exception as e:
                print(f"[WARNING] 统一内存GPU预处理失败，回退到传统GPU: {e}")
                # 回退到传统GPU预处理
                if gpu_processor is not None:
                    try:
                        im_tensor = gpu_processor.preprocess_image_gpu(npImg, target_size=(320, 320))
                        im = im_tensor.cpu().numpy()
                        print(f"[DEBUG] 传统GPU预处理完成，形状: {im.shape}, 设备: {im_tensor.device}")
                    except Exception as e2:
                        print(f"[WARNING] 传统GPU预处理也失败，回退到CPU: {e2}")
                        # 回退到原始CPU预处理
                        im = torch.from_numpy(npImg).to('cuda')
                        if im.shape[2] == 4:
                            im = im[:, :, :3]
                        im = torch.movedim(im, 2, 0)
                        im = im.half()
                        im /= 255
                        if len(im.shape) == 3:
                            im = im[None]
                        im = im.cpu().numpy()
                else:
                    # 回退到原始CPU预处理
                    im = torch.from_numpy(npImg).to('cuda')
                    if im.shape[2] == 4:
                        im = im[:, :, :3]
                    im = torch.movedim(im, 2, 0)
                    im = im.half()
                    im /= 255
                    if len(im.shape) == 3:
                        im = im[None]
                    im = im.cpu().numpy()
        elif gpu_processor is not None and onnxChoice == 3:
            # 传统GPU加速预处理 - 减少CPU负载，提高内存效率
            try:
                im_tensor = gpu_processor.preprocess_image_gpu(npImg, target_size=(320, 320))
                # 转换为numpy数组用于ONNX Runtime
                im = im_tensor.cpu().numpy()
                print(f"[DEBUG] 传统GPU预处理完成，形状: {im.shape}, 设备: {im_tensor.device}")
            except Exception as e:
                print(f"[WARNING] 传统GPU预处理失败，回退到CPU: {e}")
                # 回退到原始CPU预处理
                im = torch.from_numpy(npImg).to('cuda')
                if im.shape[2] == 4:
                    im = im[:, :, :3]
                im = torch.movedim(im, 2, 0)
                im = im.half()
                im /= 255
                if len(im.shape) == 3:
                    im = im[None]
                im = im.cpu().numpy()
        elif onnxChoice == 3:
            # NVIDIA GPU - 使用 PyTorch tensor 和 CUDA（原始方式）
            im = torch.from_numpy(npImg).to('cuda')
            if im.shape[2] == 4:
                # If the image has an alpha channel, remove it
                im = im[:, :, :3]
            im = torch.movedim(im, 2, 0)
            im = im.half()
            im /= 255
            if len(im.shape) == 3:
                im = im[None]
            # 转换为 numpy 数组用于 ONNX Runtime
            im = im.cpu().numpy()
        else:
            # AMD/CPU - 使用 numpy 数组，确保数据类型一致性
            im = torch.from_numpy(npImg)
            if im.shape[2] == 4:
                # If the image has an alpha channel, remove it
                im = im[:, :, :3]
            im = torch.movedim(im, 2, 0)  # 将通道维度移到第一个位置 (CHW格式)
            im = im.half()  # 转换为 float16
            im /= 255
            if len(im.shape) == 3:
                im = im[None]  # 添加批次维度 (NCHW格式)
            im = im.cpu().numpy()  # 转换为 numpy 数组用于 ONNX Runtime
            
        # 结束预处理计时
        perf_analyzer.end_timer('preprocessing')

        # 开始推理计时
        perf_analyzer.start_timer('inference')
        
        # 使用多线程AI处理系统（如果可用）
        if multi_ai_processor is not None:
            # 异步提交帧到多线程AI处理器
            frame_metadata = {
                'timestamp': time.time(),
                'frame_id': count,
                'confidence_threshold': confidence
            }
            
            # 提交帧进行异步处理（集成帧时间顺序管理）
            if multi_ai_processor.process_frame_async(npImg, frame_metadata):
                # 尝试获取处理结果
                ai_result = multi_ai_processor.get_result(timeout=0.001)
                if ai_result is not None:
                    # 使用AI处理结果
                    targets = ai_result['detections']
                    
                    # 显示帧时间顺序调试信息（如果是增强版处理器）
                    if hasattr(multi_ai_processor, 'frame_manager'):
                        frame_age = ai_result.get('frame_age', 0)
                        frame_id = ai_result.get('frame_id', 'unknown')
                        processing_delay = time.time() - frame_metadata['timestamp']
                        
                        # 在Live显示中添加帧时间信息
                        frame_time_info = f"Frame ID: {frame_id}, Age: {frame_age*1000:.1f}ms, Delay: {processing_delay*1000:.1f}ms"
                        if 'live_display_info' not in locals():
                            live_display_info = []
                        live_display_info.append(frame_time_info)
                        
                        # 定期打印帧时间统计（每100帧）
                        if count % 100 == 0:
                            print(f"[INFO] 🕒 帧时间顺序统计 (第{count}帧):")
                            print(f"   • 当前帧年龄: {frame_age*1000:.1f}ms")
                            print(f"   • 处理延迟: {processing_delay*1000:.1f}ms")
                            multi_ai_processor.print_performance_stats()
                    
                    # 记录性能监控数据
                    if performance_monitor is not None:
                        performance_monitor.record_timing('ai_inference_time', ai_result.get('inference_time', 0))
                        performance_monitor.record_timing('postprocess_time', ai_result.get('postprocess_time', 0))
                        # 记录帧年龄信息
                        if 'frame_age' in ai_result:
                            performance_monitor.record_timing('frame_age', ai_result['frame_age'])
                else:
                    # 如果没有结果，使用传统处理方式
                    targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
            else:
                # 队列满或帧被丢弃，使用传统处理方式
                if hasattr(multi_ai_processor, 'frame_manager'):
                    print(f"[WARNING] 🕒 帧被丢弃 (第{count}帧) - 可能过时或队列满")
                targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
        else:
            # 使用传统AI推理方式
            # 使用双GPU或单GPU推理
            if DUAL_GPU_AVAILABLE and 'dual_gpu_manager' in locals():
                # 使用双GPU负载均衡推理
                input_data = {dual_gpu_manager.nvidia_session.get_inputs()[0].name: im} if dual_gpu_manager.nvidia_session else {'images': im}
                outputs = run_optimized_inference(input_data, use_parallel=False)
            else:
                # 使用单GPU推理
                outputs = ort_sess.run(None, {ort_sess.get_inputs()[0].name: im})
                
            # 结束推理计时
            perf_analyzer.end_timer('inference')

            # 开始后处理计时
            perf_analyzer.start_timer('postprocessing')

            # 使用GPU加速后处理（优先使用统一内存处理器）
            if unified_gpu_processor is not None and onnxChoice == 3:
                try:
                    # 统一内存GPU加速后处理 - 自动CPU-GPU内存迁移
                    # 将ONNX输出的numpy数组转换为PyTorch张量
                    outputs_tensor = torch.from_numpy(outputs[0]).to('cuda')
                    targets_tensor = unified_gpu_processor.postprocess_detections_gpu(
                        outputs_tensor, 
                        conf_threshold=confidence
                    )
                    
                    # 转换为DataFrame格式
                    if targets_tensor.numel() > 0:
                        targets_np = targets_tensor.cpu().numpy()
                        targets = pd.DataFrame(
                            targets_np, 
                            columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"]
                        )
                    else:
                        targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                    
                    print(f"[DEBUG] 统一内存GPU后处理完成，检测到 {len(targets)} 个目标")
                except Exception as e:
                    print(f"[WARNING] 统一内存GPU后处理失败，回退到传统GPU后处理: {e}")
                    # 回退到传统GPU后处理
                    if gpu_processor is not None and onnxChoice == 3:
                        try:
                            # 传统GPU加速后处理 - 减少CPU负载，提高内存效率
                            outputs_tensor = torch.from_numpy(outputs[0]).to('cuda')
                            targets_tensor = gpu_processor.postprocess_detections_gpu(
                                outputs_tensor, 
                                conf_threshold=confidence
                            )
                            
                            # 转换为DataFrame格式
                            if targets_tensor.numel() > 0:
                                targets_np = targets_tensor.cpu().numpy()
                                targets = pd.DataFrame(
                                    targets_np, 
                                    columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"]
                                )
                            else:
                                targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                            
                            print(f"[DEBUG] 传统GPU后处理完成，检测到 {len(targets)} 个目标")
                        except Exception as e2:
                            print(f"[WARNING] 传统GPU后处理也失败，回退到CPU: {e2}")
                            # 回退到原始CPU后处理
                            outputs = non_max_suppression(torch.tensor(outputs[0]), confidence, 0.5)
                            targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                            for output in outputs:
                                if output is not None and len(output):
                                    for *box, conf, cls in output:
                                        x1, y1, x2, y2 = box
                                        targets = pd.concat([targets, pd.DataFrame({
                                            'current_mid_x': [(x1 + x2) / 2],
                                            'current_mid_y': [(y1 + y2) / 2],
                                            'width': [x2 - x1],
                                            'height': [y2 - y1],
                                            'confidence': [conf.item()]
                                        })], ignore_index=True)
                    else:
                        # 回退到原始CPU后处理
                        outputs = non_max_suppression(torch.tensor(outputs[0]), confidence, 0.5)
                        targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                        for output in outputs:
                            if output is not None and len(output):
                                for *box, conf, cls in output:
                                    x1, y1, x2, y2 = box
                                    targets = pd.concat([targets, pd.DataFrame({
                                        'current_mid_x': [(x1 + x2) / 2],
                                        'current_mid_y': [(y1 + y2) / 2],
                                        'width': [x2 - x1],
                                        'height': [y2 - y1],
                                        'confidence': [conf.item()]
                                    })], ignore_index=True)
            elif gpu_processor is not None and onnxChoice == 3:
                try:
                    # 传统GPU加速后处理 - 减少CPU负载，提高内存效率
                    outputs_tensor = torch.from_numpy(outputs[0]).to('cuda')
                    targets_tensor = gpu_processor.postprocess_detections_gpu(
                        outputs_tensor, 
                        conf_threshold=confidence
                    )
                    
                    # 转换为DataFrame格式
                    if targets_tensor.numel() > 0:
                        targets_np = targets_tensor.cpu().numpy()
                        targets = pd.DataFrame(
                            targets_np, 
                            columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"]
                        )
                    else:
                        targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                    
                    print(f"[DEBUG] 传统GPU后处理完成，检测到 {len(targets)} 个目标")
                except Exception as e:
                    print(f"[WARNING] 传统GPU后处理失败，回退到CPU: {e}")
                    # 回退到原始CPU后处理
                    outputs = non_max_suppression(torch.tensor(outputs[0]), confidence, 0.5)
                    targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                    for output in outputs:
                        if output is not None and len(output):
                            for *box, conf, cls in output:
                                x1, y1, x2, y2 = box
                                targets = pd.concat([targets, pd.DataFrame({
                                    'current_mid_x': [(x1 + x2) / 2],
                                    'current_mid_y': [(y1 + y2) / 2],
                                    'width': [x2 - x1],
                                    'height': [y2 - y1],
                                    'confidence': [conf.item()]
                                })], ignore_index=True)
            else:
                # 原始CPU后处理
                outputs = non_max_suppression(torch.tensor(outputs[0]), confidence, 0.5)
                targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                for output in outputs:
                    if output is not None and len(output):
                        for *box, conf, cls in output:
                            x1, y1, x2, y2 = box
                            targets = pd.concat([targets, pd.DataFrame({
                                'current_mid_x': [(x1 + x2) / 2],
                                'current_mid_y': [(y1 + y2) / 2],
                                'width': [x2 - x1],
                                'height': [y2 - y1],
                                'confidence': [conf.item()]
                            })], ignore_index=True)
            
            # 结束后处理计时
            perf_analyzer.end_timer('postprocessing')
        
        # 如果使用多线程AI处理，这里不需要单独的推理和后处理计时
        if multi_ai_processor is None:
            # 结束推理计时（仅在传统模式下）
            perf_analyzer.end_timer('inference')
        
        # 记录性能监控数据
        if performance_monitor is not None:
            performance_monitor.increment_counter('screenshot_count')
            performance_monitor.increment_counter('ai_processing_count')
        
        # 检测稳定性系统处理
        if DETECTION_STABILITY_AVAILABLE and stability_system is not None:
            targets = stability_system.process_detections(targets)
            print(f"[DEBUG] 检测稳定性系统处理完成，稳定目标数: {len(targets)}")
        
        # GPU加速后处理（优先使用统一内存处理器）
        elif unified_gpu_processor is not None and onnxChoice == 3:
            try:
                # 统一内存GPU加速后处理 - 最高性能
                # 将ONNX输出的numpy数组转换为PyTorch张量
                outputs_tensor = torch.from_numpy(outputs[0]).to('cuda')
                targets_tensor = unified_gpu_processor.postprocess_detections_gpu(
                    outputs_tensor, 
                    conf_threshold=confidence
                )
                
                # 转换为DataFrame格式
                if targets_tensor.numel() > 0:
                    targets_np = targets_tensor.cpu().numpy()
                    targets = pd.DataFrame(
                        targets_np, 
                        columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"]
                    )
                else:
                    targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                
                print(f"[DEBUG] 统一内存GPU后处理完成，检测到 {len(targets)} 个目标")
                
            except Exception as e:
                print(f"[WARNING] 统一内存GPU后处理失败，回退到传统GPU: {e}")
                # 回退到传统GPU后处理
                if gpu_processor is not None:
                    try:
                        # 使用传统GPU后处理
                        outputs_tensor = torch.from_numpy(outputs[0]).to('cuda')
                        targets_tensor = gpu_processor.postprocess_detections_gpu(
                            outputs_tensor, 
                            conf_threshold=confidence
                        )
                        
                        if targets_tensor.numel() > 0:
                            targets_np = targets_tensor.cpu().numpy()
                            targets = pd.DataFrame(
                                targets_np, 
                                columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"]
                            )
                        else:
                            targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                        
                        print(f"[DEBUG] 传统GPU后处理完成，检测到 {len(targets)} 个目标")
                        
                    except Exception as e2:
                        print(f"[WARNING] 传统GPU后处理也失败，回退到CPU: {e2}")
                        # 回退到CPU后处理
                        targets = pd.DataFrame(non_max_suppression(torch.from_numpy(outputs[0]), confidence, 0.45, None, False, max_det=1000)[0].cpu().numpy())
                        if len(targets) == 0:
                            targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                        else:
                            targets.columns = ['current_mid_x', 'current_mid_y', 'width', "height", "confidence", "class"]
                            targets = targets[['current_mid_x', 'current_mid_y', 'width', "height", "confidence"]]
                else:
                    # 回退到CPU后处理
                    targets = pd.DataFrame(non_max_suppression(torch.from_numpy(outputs[0]), confidence, 0.45, None, False, max_det=1000)[0].cpu().numpy())
                    if len(targets) == 0:
                        targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                    else:
                        targets.columns = ['current_mid_x', 'current_mid_y', 'width', "height", "confidence", "class"]
                        targets = targets[['current_mid_x', 'current_mid_y', 'width', "height", "confidence"]]
                        
        elif gpu_processor is not None and onnxChoice == 3:
            try:
                # 传统GPU加速后处理 - 减少CPU负载
                # 将ONNX输出的numpy数组转换为PyTorch张量
                outputs_tensor = torch.from_numpy(outputs[0]).to('cuda')
                targets_tensor = gpu_processor.postprocess_detections_gpu(
                    outputs_tensor, 
                    conf_threshold=confidence
                )
                
                # 转换为DataFrame格式
                if targets_tensor.numel() > 0:
                    targets_np = targets_tensor.cpu().numpy()
                    targets = pd.DataFrame(
                        targets_np, 
                        columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"]
                    )
                else:
                    targets = pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
                    
                print(f"[DEBUG] GPU后处理完成，检测到 {len(targets)} 个目标")
                
            except Exception as e:
                print(f"[WARNING] GPU后处理失败，回退到CPU: {e}")
                # 回退到原始CPU后处理
                im = torch.from_numpy(outputs[0]).to('cpu')
                pred = non_max_suppression(im, confidence, confidence, 0, False, max_det=10)
                
                targets = []
                for i, det in enumerate(pred):
                    gn = torch.tensor([npImg.shape[1], npImg.shape[0], npImg.shape[1], npImg.shape[0]])
                    if len(det):
                        for *xyxy, conf, cls in reversed(det):
                            targets.append((xyxy2xywh(torch.tensor(xyxy).view(
                                1, 4)) / gn).view(-1).tolist() + [float(conf)])
                
                targets = pd.DataFrame(
                    targets, columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
        else:
            # 原始CPU后处理
            im = torch.from_numpy(outputs[0]).to('cpu')

            # 使用固定置信度进行检测，并添加调试信息
            print(f"[CONFIDENCE_DEBUG] 当前置信度阈值: {confidence}")
            pred = non_max_suppression(
                im, confidence, confidence, 0, False, max_det=10)
            
            # 调试：显示所有检测结果（包括被过滤的）
            if len(pred) > 0 and len(pred[0]) > 0:
                all_detections = pred[0]
                print(f"[DETECTION_DEBUG] 检测到 {len(all_detections)} 个目标:")
                for i, detection in enumerate(all_detections):
                    x1, y1, x2, y2, conf, cls = detection
                    print(f"  目标{i+1}: 置信度={conf:.3f}, 类别={int(cls)}, 位置=({x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f})")
                    if conf < confidence:
                        print(f"    ⚠️ 该目标置信度低于阈值 {confidence}，应被过滤")
                    else:
                        print(f"    ✅ 该目标置信度符合要求")

            targets = []
            for i, det in enumerate(pred):
                s = ""
                # 使用原始图像的尺寸进行归一化 [width, height, width, height]
                gn = torch.tensor([npImg.shape[1], npImg.shape[0], npImg.shape[1], npImg.shape[0]])
                if len(det):
                    for c in det[:, -1].unique():
                        n = (det[:, -1] == c).sum()  # detections per class
                        s += f"{n} {int(c)}, "  # add to string

                    for *xyxy, conf, cls in reversed(det):
                        targets.append((xyxy2xywh(torch.tensor(xyxy).view(
                            1, 4)) / gn).view(-1).tolist() + [float(conf)])  # normalized xywh

            targets = pd.DataFrame(
                targets, columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
            
            # 应用目标数量限制和筛选策略
            if len(targets) > maxTargets:
                print(f"[TARGET_LIMIT] 检测到 {len(targets)} 个目标，限制为 {maxTargets} 个")
                
                # 根据筛选策略选择目标
                if targetSelectionStrategy == "highest_conf":
                    # 按置信度降序排列，选择置信度最高的目标
                    targets = targets.nlargest(maxTargets, 'confidence')
                    print(f"[TARGET_LIMIT] 使用最高置信度策略，选择置信度范围: {targets['confidence'].min():.3f} - {targets['confidence'].max():.3f}")
                elif targetSelectionStrategy == "largest":
                    # 按目标大小（高度*宽度）降序排列，选择最大的目标
                    targets['target_size'] = targets['width'] * targets['height']
                    targets = targets.nlargest(maxTargets, 'target_size')
                    print(f"[TARGET_LIMIT] 使用最大目标策略，选择大小范围: {targets['target_size'].min():.6f} - {targets['target_size'].max():.6f}")
                else:
                    # 默认策略：先按置信度筛选，再按距离选择（closest策略将在后续距离计算后应用）
                    targets = targets.nlargest(maxTargets, 'confidence')
                    print(f"[TARGET_LIMIT] 使用最近距离策略（预筛选），保留置信度最高的 {maxTargets} 个目标")
            
        # 结束后处理计时
        perf_analyzer.end_timer('postprocessing')
        
        # 应用检测稳定性系统
        if stability_system is not None:
            perf_analyzer.start_timer('stability_processing')
            original_count = len(targets)
            targets = stability_system.process_detections(targets)
            stable_count = len(targets)
            
            if original_count != stable_count:
                print(f"[STABILITY] 原始检测: {original_count} -> 稳定检测: {stable_count}")
            
            perf_analyzer.end_timer('stability_processing')
        
        # 使用实际游戏窗口大小（用户提供的常量）
        
        # 检测图像的中心坐标（用于距离计算）
        detection_center = [npImg.shape[1] / 2, npImg.shape[0] / 2]  # [160, 160] for 320x320 detection box

        # 调试输出：显示检测到的目标数量和图像信息
        if len(targets) > 0:
            print(f"[DEBUG] 检测到 {len(targets)} 个目标，最高置信度: {targets['confidence'].max():.3f}")
            
            # 图像尺寸和中心坐标调试信息
            print(f"[DEBUG] 检测图像尺寸: {npImg.shape[1]}x{npImg.shape[0]}")
            print(f"[DEBUG] 实际游戏窗口: {ACTUAL_GAME_WIDTH}x{ACTUAL_GAME_HEIGHT}")
            print(f"[DEBUG] 检测图像中心: {detection_center}")
            
            # 显示第一个目标的原始坐标（已经是像素坐标）
            first_target = targets.iloc[0]
            print(f"[DEBUG] 第一个目标原始像素坐标: x={first_target['current_mid_x']:.3f}, y={first_target['current_mid_y']:.3f}")
            print(f"[DEBUG] 目标框尺寸: width={first_target['width']:.3f}, height={first_target['height']:.3f}")
            print(f"[DEBUG] 目标置信度: {first_target['confidence']:.3f}")
            
            # 如果有多个目标，显示前3个目标的坐标
            if len(targets) > 1:
                print(f"[DEBUG] 检测到 {len(targets)} 个目标:")
                for i, target in targets.head(3).iterrows():
                    print(f"  目标{i}: x={target['current_mid_x']:.3f}, y={target['current_mid_y']:.3f}, conf={target['confidence']:.3f}")
            
            # non_max_suppression已经返回像素坐标，无需再次转换
            # 注释掉错误的坐标转换代码
            # targets['current_mid_x'] = targets['current_mid_x'] * npImg.shape[1]  # 宽度
            # targets['current_mid_y'] = targets['current_mid_y'] * npImg.shape[0]  # 高度
            # targets['height'] = targets['height'] * npImg.shape[0]  # 高度
            
            # 计算距离检测图像中心的距离（用于排序）
            targets['distance_from_center'] = ((targets['current_mid_x'] - detection_center[0])**2 + (targets['current_mid_y'] - detection_center[1])**2)**0.5
            
            # 优化目标选择：优先选择高置信度目标
            # 创建综合评分：置信度权重 + 距离权重（置信度越高越好，距离越近越好）
            confidence_weight = 2.0  # 置信度权重
            distance_weight = 1.0    # 距离权重
            
            # 标准化置信度和距离（0-1范围）
            max_confidence = targets['confidence'].max()
            min_confidence = targets['confidence'].min()
            if max_confidence > min_confidence:
                targets['normalized_confidence'] = (targets['confidence'] - min_confidence) / (max_confidence - min_confidence)
            else:
                targets['normalized_confidence'] = 1.0
            
            max_distance = targets['distance_from_center'].max()
            min_distance = targets['distance_from_center'].min()
            if max_distance > min_distance:
                targets['normalized_distance'] = 1.0 - (targets['distance_from_center'] - min_distance) / (max_distance - min_distance)
            else:
                targets['normalized_distance'] = 1.0
            
            # 计算综合评分（越高越好）
            targets['selection_score'] = (targets['normalized_confidence'] * confidence_weight + 
                                         targets['normalized_distance'] * distance_weight)
            
            print(f"[TARGET_SELECTION] 优化目标选择 - 置信度权重:{confidence_weight}, 距离权重:{distance_weight}")
            for idx, row in targets.iterrows():
                print(f"[TARGET_SELECTION] 目标{idx}: 置信度={row['confidence']:.3f}, 距离={row['distance_from_center']:.1f}, 评分={row['selection_score']:.3f}")
            
            # 按综合评分排序（降序，评分高的在前）
            targets = targets.sort_values('selection_score', ascending=False)
            
            # 🔥 更新开火检测回调的目标数据（移动过程中使用）
            if hasattr(fire_check_callback, 'latest_targets'):
                fire_check_callback.latest_targets = targets.copy()
                print(f"[FIRE_CALLBACK] 🎯 已更新移动过程开火检测目标数据，目标数量: {len(targets)}")
            
            # 计算目标头部到准星的距离（新增功能）
            def calculate_distance_to_crosshair(target_x, target_y, box_height, crosshair_x, crosshair_y):
                """
                计算目标头部到准星中心的距离
                
                Args:
                    target_x: 目标中心X坐标
                    target_y: 目标中心Y坐标  
                    box_height: 目标框高度
                    crosshair_x: 准星X坐标
                    crosshair_y: 准星Y坐标
                    
                Returns:
                    float: 头部到准星的距离
                """
                # 计算头部位置（头部在目标中心上方）
                # 使用平滑的头部位置计算
                head_x, head_y = calculate_smoothed_head_position(target_x, target_y, box_height)
                
                # 计算头部到准星的欧几里得距离
                distance = ((head_x - crosshair_x)**2 + (head_y - crosshair_y)**2)**0.5
                return distance
            
            # 为每个目标计算到准星的距离
            targets['distance_to_crosshair'] = targets.apply(
                lambda row: calculate_distance_to_crosshair(
                    row['current_mid_x'], row['current_mid_y'], row['height'], cWidth, cHeight
                ), axis=1
            )
            
            # 如果使用closest策略且目标数量仍然超过限制，进行最终筛选
            if targetSelectionStrategy == "closest" and len(targets) > maxTargets:
                targets = targets.nsmallest(maxTargets, 'distance_to_crosshair')
                print(f"[TARGET_LIMIT] 最近距离策略最终筛选，选择距离范围: {targets['distance_to_crosshair'].min():.1f} - {targets['distance_to_crosshair'].max():.1f} 像素")
        
        # If there are people in the center bounding box
        if len(targets) > 0:
            # 🎯 移动目标锁定机制
            current_time = time.time()
            
            # 检查是否需要锁定移动目标
            if movement_locked_target is None or (current_time - movement_lock_time) > MOVEMENT_LOCK_DURATION:
                # 选择新的移动目标（距离准星最近的目标）
                if len(targets) > 0:
                    closest_target = targets.iloc[0]  # 已经按距离排序
                    movement_locked_target = {
                        'x': closest_target['current_mid_x'],
                        'y': closest_target['current_mid_y'],
                        'height': closest_target['height'],
                        'confidence': closest_target.get('confidence', 1.0)
                    }
                    movement_lock_time = current_time
                    is_moving_to_target = True
                    print(f"[MOVEMENT_LOCK] 🎯 锁定新的移动目标: ({movement_locked_target['x']:.1f}, {movement_locked_target['y']:.1f})")
            else:
                print(f"[MOVEMENT_LOCK] 🔒 使用已锁定的移动目标: ({movement_locked_target['x']:.1f}, {movement_locked_target['y']:.1f})")
            
            # 更新连续跟踪系统（如果可用）
            if continuous_tracker is not None:
                # 获取最近的目标用于跟踪更新
                closest_target = targets.iloc[0]
                target_confidence = closest_target.get('confidence', 1.0)
                # 更新连续跟踪器的目标位置（用于实时跟踪）
                continuous_tracker.update_target(
                    closest_target['current_mid_x'], 
                    closest_target['current_mid_y'], 
                    target_confidence
                )
            
            # 使用锁定的移动目标进行瞄准计算
            selected_target = None  # 初始化selected_target变量
            if movement_locked_target is not None:
                xMid = movement_locked_target['x']
                yMid = movement_locked_target['y']
                box_height = movement_locked_target['height']
                # 为了兼容后续代码，创建一个selected_target对象
                selected_target = {
                    'current_mid_x': xMid,
                    'current_mid_y': yMid,
                    'height': box_height,
                    'confidence': movement_locked_target['confidence']
                }
                print(f"[MOVEMENT_TARGET] 使用锁定目标进行移动计算: ({xMid:.1f}, {yMid:.1f})")
            else:
                # 备选逻辑：使用新的目标锁定机制进行智能目标选择
                selected_target = find_best_target_with_lock(targets, current_time)
                
                if selected_target is not None:
                    # 获取选中目标的信息
                    xMid = selected_target['current_mid_x']
                    yMid = selected_target['current_mid_y']
                    box_height = selected_target['height']
                    
                    # 打印目标锁定状态信息
                    lock_status = get_lock_status()
                    print(f"[TARGET_LOCK] {lock_status}")
                else:
                    # 如果没有选中目标，使用原有逻辑作为备选
                    if (centerOfScreen):
                        targets = targets.sort_values("distance_to_crosshair")
                        print(f"[TARGET_SELECT] 备选逻辑：检测到 {len(targets)} 个目标，选择离准星最近的目标")
                    else:
                        targets = targets.sort_values("distance_from_center")
                    
                    xMid = targets.iloc[0].current_mid_x
                    yMid = targets.iloc[0].current_mid_y
                    box_height = targets.iloc[0].height
                    # 创建selected_target对象用于兼容
                    selected_target = {
                        'current_mid_x': xMid,
                        'current_mid_y': yMid,
                        'height': box_height,
                        'confidence': targets.iloc[0].get('confidence', 1.0)
                    }
            
            # 🎯 关键修复：根据检测状态选择头部位置进行瞄准计算
            # 初始化变量
            headshot_offset_320 = 0.0
            head_source = "UNKNOWN"
            
            if target_lock_enabled and locked_target and selected_target is not None:
                # 使用锁定的头部位置（已经是320坐标系）
                head_x_320 = locked_target['head_x']
                head_y_320 = locked_target['head_y']
                # 计算锁定目标的偏移量（用于调试显示）
                if headshot_mode:
                    headshot_offset_320 = box_height * 0.38
                else:
                    headshot_offset_320 = box_height * 0.2
                head_source = "LOCKED"
                print(f"[HEAD_LOCK_MAIN] 主循环使用锁定的头部位置: ({head_x_320:.1f}, {head_y_320:.1f})")
            else:
                # 检查是否检测丢失（目标置信度过低或无目标）
                detection_lost = selected_target is None or selected_target.get('confidence', 0) < confidence
                
                if detection_lost and target_lock_enabled:
                    # 纯净系统：检测丢失时不使用历史记忆或预测
                    # 直接跳过移动，等待下一帧检测
                    print(f"[PURE_HEAD_MAIN] 检测丢失，纯净系统等待下一帧检测（无历史记忆补偿）")
                    continue  # 跳过本次循环，等待下一帧
                    # 使用历史数据估算偏移量
                    headshot_offset_320 = box_height * (0.38 if headshot_mode else 0.2)
                else:
                    # 检测正常时：使用实际检测到的位置
                    # Calculate headshot offset (使用320坐标系，与Live Feed保持一致)
                    if headshot_mode:
                        headshot_offset_320 = box_height * 0.38
                    else:
                        headshot_offset_320 = box_height * 0.2
                    
                    # 使用纯净头部检测系统计算位置
                    target_data = {
                        'current_mid_x': xMid,
                        'current_mid_y': yMid,
                        'height': box_height,
                        'confidence': selected_target.get('confidence', 0.0)
                    }
                    
                    pure_head_pos = get_pure_head_position(target_data, headshot_mode)
                    if pure_head_pos:
                        head_x_320 = pure_head_pos['x']
                        head_y_320 = pure_head_pos['y']
                        head_source = "PURE_CURRENT_FRAME"
                        print(f"[PURE_HEAD_MAIN] 纯净头部位置: ({head_x_320:.1f}, {head_y_320:.1f})")
                    else:
                        # 备用计算
                        headshot_offset_320 = box_height * (0.38 if headshot_mode else 0.2)
                        head_x_320 = xMid
                        head_y_320 = yMid - headshot_offset_320
                        head_source = "FALLBACK"
                        print(f"[PURE_HEAD_MAIN] 备用头部位置: ({head_x_320:.1f}, {head_y_320:.1f})")

            # 鼠标移动计算：目标位置 - 准星位置（截图区域中心）
            # 使用统一的320坐标系头部位置进行瞄准计算
            mouseMove = [head_x_320 - cWidth, head_y_320 - cHeight]
            
            # 🔥 帧同步修复：在头部位置计算完成后创建display_img，确保完全同步
            if display_img is None:
                display_img = npImg.copy()  # 使用与头部计算相同的最终处理帧
                # 如果启用了掩码，也对显示图像应用掩码
                if useMask:
                    mask_config = {
                        'enabled': True,
                        'side': maskSide,
                        'width': maskWidth,
                        'height': maskHeight
                    }
                    display_img = screenshot_optimizer.apply_mask_optimized(display_img, mask_config)
                print(f"[FRAME_SYNC] 创建display_img与头部计算同步: {display_img.shape[1]}x{display_img.shape[0]}")
            
            # 添加调试输出：确认瞄准系统使用统一的320坐标系
            print(f"[UNIFIED_AIMING_DEBUG] 瞄准系统320坐标:")
            print(f"  目标位置: ({xMid:.3f}, {yMid:.3f})")
            print(f"  头部位置: ({head_x_320:.3f}, {head_y_320:.3f}) [{head_source}]")
            print(f"  头部偏移: {headshot_offset_320:.3f}")
            print(f"  鼠标移动: ({mouseMove[0]:.3f}, {mouseMove[1]:.3f})")
            print(f"  ✅ 瞄准系统坐标系统一：使用320坐标系")
            
            # 开始瞄准计时
            perf_analyzer.start_timer('aiming')
            
            # Moving the mouse
            # 检查鼠标右键或Caps Lock是否按下，并且没有暂停移动
            right_mouse_down = win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000
            caps_lock_down = win32api.GetKeyState(win32con.VK_CAPITAL) & 0x0001 # Caps Lock是切换键，需要GetKeyState

            # 旧的移动逻辑已禁用，现在使用下方的动态跟踪系统
            # if (right_mouse_down or caps_lock_down) and not movement_paused:
            #     move_mouse(mouseMove[0] * aaMovementAmp, mouseMove[1] * aaMovementAmp)

            # 结束瞄准计时
            perf_analyzer.end_timer('aiming')

            # 保存坐标用于跟踪和目标锁定
            # 只有在实际执行了瞄准移动后，才保存坐标用于跟踪
            if (right_mouse_down or caps_lock_down) and not movement_paused:
                last_mid_coord = [xMid, yMid]
                # 如果启用了目标锁定且当前有锁定目标，更新锁定目标的坐标
                if target_lock_enabled and locked_target is not None:
                    # 更新锁定目标的坐标信息
                    locked_target['current_mid_x'] = xMid
                    locked_target['current_mid_y'] = yMid
                    locked_target['height'] = box_height
            else:
                last_mid_coord = None # 如果没有瞄准，则清空last_mid_coord，避免下次激活时瞬移
                # 如果没有瞄准动作，清除目标锁定
                if target_lock_enabled:
                    locked_target = None
                    lock_start_time = None
                    print("[TARGET_LOCK] 瞄准停止，清除目标锁定")

        else:
            # 没有检测到目标时，尝试使用连续跟踪系统
            predicted_target = None
            # 移除头部预测逻辑 - 只使用实时检测到的目标
            # 不再使用虚拟预测目标，确保每次都处理最新检测到的真实目标
            predicted_target = None
            
            # 🔥 帧同步修复：即使没有目标也要创建display_img，确保Live Feed正常显示
            if display_img is None:
                display_img = npImg.copy()  # 使用与处理相同的最终帧
                # 如果启用了掩码，也对显示图像应用掩码
                if useMask:
                    mask_config = {
                        'enabled': True,
                        'side': maskSide,
                        'width': maskWidth,
                        'height': maskHeight
                    }
                    display_img = screenshot_optimizer.apply_mask_optimized(display_img, mask_config)
                print(f"[FRAME_SYNC] 无目标时创建display_img: {display_img.shape[1]}x{display_img.shape[0]}")
            
            # 如果没有检测到真实目标，清除相关状态
            if predicted_target is None:
                last_mid_coord = None
                # 没有检测到目标时，清除目标锁定
                if target_lock_enabled:
                    locked_target = None
                    lock_start_time = None
                print("[CONTINUOUS_TRACKING] 无可用的跟踪数据")
            else:
                # 使用预测目标更新坐标
                last_mid_coord = [predicted_target['current_mid_x'], predicted_target['current_mid_y']]

        # See what the bot sees
        if visuals:
            # 确保npImg是连续的numpy数组，兼容OpenCV
            if not npImg.flags['C_CONTIGUOUS']:
                npImg = np.ascontiguousarray(npImg)
            
            # 确保数据类型为uint8
            if npImg.dtype != np.uint8:
                npImg = npImg.astype(np.uint8)
            
            # Loops over every item identified and draws a bounding box
            for i in range(0, len(targets)):
                # 使用iloc来安全访问DataFrame行，避免索引问题
                row = targets.iloc[i]
                halfW = round(row["width"] / 2)
                halfH = round(row["height"] / 2)
                midX = row['current_mid_x']
                midY = row['current_mid_y']
                (startX, startY, endX, endY) = int(midX + halfW), int(midY +
                                                                      halfH), int(midX - halfW), int(midY - halfH)

                idx = 0
                # draw the bounding box and label on the frame
                label = "{}: {:.2f}%".format(
                    "Human", row["confidence"] * 100)
                cv2.rectangle(npImg, (startX, startY), (endX, endY),
                              COLORS[idx], 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(npImg, label, (startX, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)

        # Forced garbage cleanup every second
        count += 1
        if (time.time() - sTime) > 1:
            if cpsDisplay:
                print("CPS: {}".format(count))
                
            # 性能分析器报告
            perf_analyzer.frame_complete()
            if count % 5 == 0:  # 每5秒打印一次详细报告
                perf_analyzer.print_performance_report()
                
            count = 0
            sTime = time.time()
            
            # 每秒保存一次瞄准数据
            save_aiming_data()

            # Uncomment if you keep running into memory issues
            # gc.collect(generation=0)

        # 基本信息始终显示
        # 在FPS游戏中，鼠标指针就是准星，始终位于屏幕中心
        # 鼠标坐标 = 准星坐标 = 截图区域中心坐标 (320x320区域的中心是160,160)
        mouse_x = 160  # 截图区域中心X坐标
        mouse_y = 160  # 截图区域中心Y坐标
        
        # 准星位置（截图区域中心）
        crosshair_x = 160  # 截图区域中心X坐标
        crosshair_y = 160  # 截图区域中心Y坐标
        
        # 在图像上显示位置信息（仅在启用Live Feed时）
        if showLiveFeed and display_img is not None:
            info_y_offset = 30
            
            # 显示鼠标位置
            cv2.putText(display_img, f"Mouse: ({mouse_x}, {mouse_y})", 
                       (10, info_y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # 在Live Feed中绘制准星标记（使用正确的坐标转换）
            # 准星在320坐标系中的位置是(160, 160)，需要转换到显示坐标系
            crosshair_x_320 = 160  # 320坐标系中的准星X位置
            crosshair_y_320 = 160  # 320坐标系中的准星Y位置
            
            # 坐标转换：从320坐标系转换到显示坐标系
            if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
                # 增强检测模式：320 -> 截取区域 -> 显示坐标
                model_to_capture_scale = enhanced_config.SCALE_FACTOR  # 720/320 = 2.25
                capture_to_display_scale_x = display_img.shape[1] / enhanced_config.CAPTURE_SIZE
                capture_to_display_scale_y = display_img.shape[0] / enhanced_config.CAPTURE_SIZE
                
                crosshair_x_capture = crosshair_x_320 * model_to_capture_scale
                crosshair_y_capture = crosshair_y_320 * model_to_capture_scale
                crosshair_x_display = int(crosshair_x_capture * capture_to_display_scale_x)
                crosshair_y_display = int(crosshair_y_capture * capture_to_display_scale_y)
                
                print(f"[CROSSHAIR_ALIGNMENT] 增强模式准星坐标转换:")
                print(f"  320坐标: ({crosshair_x_320}, {crosshair_y_320})")
                print(f"  截取区域坐标: ({crosshair_x_capture:.1f}, {crosshair_y_capture:.1f})")
                print(f"  显示坐标: ({crosshair_x_display}, {crosshair_y_display})")
            else:
                # 标准模式：320 -> 显示坐标
                scale_x = display_img.shape[1] / 320
                scale_y = display_img.shape[0] / 320
                crosshair_x_display = int(crosshair_x_320 * scale_x)
                crosshair_y_display = int(crosshair_y_320 * scale_y)
                
                print(f"[CROSSHAIR_ALIGNMENT] 标准模式准星坐标转换:")
                print(f"  320坐标: ({crosshair_x_320}, {crosshair_y_320})")
                print(f"  缩放比例: ({scale_x:.2f}, {scale_y:.2f})")
                print(f"  显示坐标: ({crosshair_x_display}, {crosshair_y_display})")
            
            # 应用18像素偏差补偿（根据用户反馈）
            CROSSHAIR_OFFSET_Y = -18  # 向上补偿18像素
            crosshair_y_display += CROSSHAIR_OFFSET_Y
            
            print(f"[CROSSHAIR_CALIBRATION] 应用18像素Y轴补偿: {crosshair_y_display - CROSSHAIR_OFFSET_Y} -> {crosshair_y_display}")
            
            # 绘制校准后的准星标记
            cv2.circle(display_img, (crosshair_x_display, crosshair_y_display), 3, (255, 255, 0), -1)  # 实心圆点
            cv2.circle(display_img, (crosshair_x_display, crosshair_y_display), 8, (255, 255, 0), 1)   # 外围圆环
            cv2.putText(display_img, "CROSSHAIR", (crosshair_x_display + 15, crosshair_y_display), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # 显示准星位置信息
            cv2.putText(display_img, f"Crosshair 320: ({crosshair_x_320}, {crosshair_y_320})", 
                       (10, info_y_offset + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(display_img, f"Crosshair Display: ({crosshair_x_display}, {crosshair_y_display})", 
                       (10, info_y_offset + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # 显示校准信息
            cv2.putText(display_img, f"Crosshair (Calibrated): ({crosshair_x_display}, {crosshair_y_display})", 
                       (10, info_y_offset + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(display_img, f"Y-Offset Applied: {CROSSHAIR_OFFSET_Y}px", 
                       (10, info_y_offset + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # 显示检测到的目标数量
            cv2.putText(display_img, f"Targets: {len(targets)}", 
                       (10, info_y_offset + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # 显示当前置信度阈值
            cv2.putText(display_img, f"Confidence Threshold: {confidence:.2f}", 
                       (10, info_y_offset + 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
            
            # 显示当前瞄准模式
            cv2.putText(display_img, f"Aiming Mode: {aiming_system.aiming_mode}", 
                       (10, info_y_offset + 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # 显示扳机系统状态
            trigger_status = "ON" if trigger_system.enabled else "OFF"
            cv2.putText(display_img, f"Trigger: {trigger_status}", 
                       (10, info_y_offset + 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if trigger_system.enabled else (0, 0, 255), 2)
        
        # 显示性能信息（FPS计算始终进行）
        current_time = time.time()
        fps = 1.0 / (current_time - sTime) if (current_time - sTime) > 0 else 0
        if showLiveFeed and display_img is not None:
            cv2.putText(display_img, f"FPS: {fps:.1f}", 
                       (10, info_y_offset + 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # 显示帧时间顺序信息（如果使用增强多线程处理器）
            if 'live_display_info' in locals() and live_display_info:
                # 显示最新的帧时间信息
                latest_frame_info = live_display_info[-1]
                cv2.putText(display_img, f"Frame Time: {latest_frame_info}", 
                           (10, info_y_offset + 240), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                
                # 清理旧的帧时间信息（只保留最新的5条）
                if len(live_display_info) > 5:
                    live_display_info = live_display_info[-5:]
        sTime = current_time

        # See visually what the Aimbot sees (仅在启用Live Feed时)
        if visuals and showLiveFeed and display_img is not None:
            
            # 如果有检测到目标，显示目标框和头部标记
            if len(targets) > 0:
                # 根据是否启用增强检测选择不同的缩放策略
                if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
                    # 增强检测模式：从模型输出坐标(320x320)转换到截取区域坐标，再缩放到显示图像
                    model_to_capture_scale = enhanced_config.SCALE_FACTOR  # 720/320 = 2.25
                    capture_to_display_scale_x = display_img.shape[1] / enhanced_config.CAPTURE_SIZE
                    capture_to_display_scale_y = display_img.shape[0] / enhanced_config.CAPTURE_SIZE
                    
                    print(f"[ENHANCED_DEBUG] 缩放参数:")
                    print(f"[ENHANCED_DEBUG] - 模型到截取区域缩放: {model_to_capture_scale}")
                    print(f"[ENHANCED_DEBUG] - 截取区域到显示缩放: {capture_to_display_scale_x}x{capture_to_display_scale_y}")
                else:
                    # 标准模式：从320x320直接缩放到显示图像尺寸
                    scale_x = display_img.shape[1] / 320
                    scale_y = display_img.shape[0] / 320
                
                # 遍历所有目标并绘制
                for idx in range(len(targets)):
                    # 获取目标在模型输出中的坐标（320x320）
                    row = targets.iloc[idx]
                    target_x_320 = row['current_mid_x']
                    target_y_320 = row['current_mid_y']
                    box_height_320 = row.height
                    box_width_320 = row.width
                    target_confidence = row['confidence']
                    
                    # 只显示高置信度目标的头部标记
                    show_head_marker = target_confidence >= confidence
                    
                    # 🎯 关键修复：优先使用锁定的头部位置，确保显示与瞄准一致
                    if target_lock_enabled and locked_target and idx == 0:
                        # 使用锁定的头部位置（已经是320坐标系）
                        head_x_320 = locked_target['head_x']
                        head_y_320 = locked_target['head_y']
                        print(f"[HEAD_LOCK_DISPLAY] 使用锁定的头部位置: ({head_x_320:.1f}, {head_y_320:.1f})")
                    else:
                        # 统一使用320坐标系计算头部位置（与瞄准系统保持一致）
                        if headshot_mode:
                            headshot_offset_320 = box_height_320 * 0.38
                        else:
                            headshot_offset_320 = box_height_320 * 0.2
                        
                        # 使用平滑的头部位置计算
                        head_x_320, head_y_320 = calculate_smoothed_head_position(target_x_320, target_y_320, box_height_320)
                        print(f"[HEAD_CALC_DISPLAY] 计算头部位置: ({head_x_320:.1f}, {head_y_320:.1f})")
                    
                    # 🧠 头部记忆增强：当检测丢失时，使用预测位置补偿（仅用于目标锁定，不影响显示）
                    if show_head_marker and target_confidence < confidence * 0.8:  # 当置信度较低时
                        predicted_pos = get_predicted_or_locked_head_position()
                        if predicted_pos:
                            # 预测功能仅用于目标锁定，不改变显示
                            print(f"[HEAD_MEMORY] 检测到{predicted_pos['source']}头部位置: ({predicted_pos['x']:.1f}, {predicted_pos['y']:.1f}) (仅用于锁定)")
                            # 不修改 head_x_320 和 head_y_320，保持显示的是实际检测位置
                    
                    # 坐标转换：从320坐标系转换到显示坐标系（仅用于绘制）
                    if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
                        # 增强检测模式：先转换到截取区域坐标，再缩放到显示尺寸
                        model_to_capture_scale = enhanced_config.SCALE_FACTOR  # 720/320 = 2.25
                        capture_to_display_scale_x = display_img.shape[1] / enhanced_config.CAPTURE_SIZE
                        capture_to_display_scale_y = display_img.shape[0] / enhanced_config.CAPTURE_SIZE
                        
                        # 目标框坐标转换（用于绘制框）
                        target_x_capture = target_x_320 * model_to_capture_scale
                        target_y_capture = target_y_320 * model_to_capture_scale
                        box_height_capture = box_height_320 * model_to_capture_scale
                        box_width_capture = box_width_320 * model_to_capture_scale
                        
                        target_x = target_x_capture * capture_to_display_scale_x
                        target_y = target_y_capture * capture_to_display_scale_y
                        box_height = box_height_capture * capture_to_display_scale_y
                        box_width = box_width_capture * capture_to_display_scale_x
                        
                        # 头部坐标转换（使用320坐标系的头部位置）
                        head_x_capture = head_x_320 * model_to_capture_scale
                        head_y_capture = head_y_320 * model_to_capture_scale
                        head_x_display = head_x_capture * capture_to_display_scale_x
                        head_y_display = head_y_capture * capture_to_display_scale_y
                        
                        print(f"[COORDINATE_UNIFIED] 目标{idx}: 320坐标({target_x_320:.1f},{target_y_320:.1f}) 头部320坐标({head_x_320:.1f},{head_y_320:.1f}) -> 显示坐标({head_x_display:.1f},{head_y_display:.1f})")
                    else:
                        # 标准模式：直接缩放到显示图像尺寸
                        scale_x = display_img.shape[1] / 320
                        scale_y = display_img.shape[0] / 320
                        
                        # 目标框坐标转换
                        target_x = target_x_320 * scale_x
                        target_y = target_y_320 * scale_y
                        box_height = box_height_320 * scale_y
                        box_width = box_width_320 * scale_x
                        
                        # 头部坐标转换（使用320坐标系的头部位置）
                        head_x_display = head_x_320 * scale_x
                        head_y_display = head_y_320 * scale_y
                    
                    # 计算目标框的四个角点
                    x1 = int(target_x - box_width / 2)
                    y1 = int(target_y - box_height / 2)
                    x2 = int(target_x + box_width / 2)
                    y2 = int(target_y + box_height / 2)
                    
                    # 绘制目标框
                    cv2.rectangle(display_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # 在目标框上方显示置信度
                    confidence_text = f"Conf: {target_confidence:.3f}"
                    confidence_color = (0, 255, 0) if target_confidence >= confidence else (0, 165, 255)  # 绿色表示高置信度，橙色表示低置信度
                    cv2.putText(display_img, confidence_text, (x1, y1 - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, confidence_color, 2)
                    
                    # 显示目标索引
                    index_text = f"#{idx}"
                    cv2.putText(display_img, index_text, (x1, y1 - 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                    
                    # 添加调试输出：监控统一坐标系的头部位置计算
                    if idx == 0:  # 只为第一个目标输出调试信息
                        print(f"[UNIFIED_COORDINATE_DEBUG] 目标{idx}:")
                        print(f"  320坐标系目标位置: ({target_x_320:.3f}, {target_y_320:.3f})")
                        print(f"  320坐标系头部位置: ({head_x_320:.3f}, {head_y_320:.3f})")
                        print(f"  显示坐标系头部位置: ({head_x_display:.3f}, {head_y_display:.3f})")
                        print(f"  头部偏移量(320): {headshot_offset_320:.3f}")
                        print(f"  ✅ 坐标系统一：瞄准和显示都基于320坐标系")
                    
                    # 只为高置信度目标绘制头部标记（使用统一的320坐标系）
                    if show_head_marker:
                        # 正常检测位置使用红色（移除预测功能的显示）
                        cv2.circle(display_img, (int(head_x_display), int(head_y_display)), 5, (0, 0, 255), -1)
                        cv2.putText(display_img, "HEAD", (int(head_x_display) + 10, int(head_y_display)), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        print(f"[UNIFIED_LIVE_FEED] 显示统一坐标系头部标记: 320坐标({head_x_320:.1f},{head_y_320:.1f}) 显示坐标({head_x_display:.1f},{head_y_display:.1f}) 置信度={target_confidence:.3f}")
                    else:
                        print(f"[UNIFIED_LIVE_FEED] 跳过低置信度目标头部标记: 置信度={target_confidence:.3f} < 阈值={confidence:.3f}")
                    
                    # 如果是最近的目标（第一个），显示详细信息
                    if idx == 0:
                        # 计算准星与目标头部的偏移（320坐标系）
                        offset_x_320 = head_x_320 - crosshair_x_320
                        offset_y_320 = head_y_320 - crosshair_y_320
                        distance_320 = (offset_x_320**2 + offset_y_320**2)**0.5
                        
                        # 显示目标头部位置（320坐标系下的真实头部位置）
                        cv2.putText(display_img, f"Target Head 320: ({head_x_320:.1f}, {head_y_320:.1f})", 
                                   (10, info_y_offset + 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        # 显示偏移信息
                        cv2.putText(display_img, f"Offset: ({offset_x_320:.1f}, {offset_y_320:.1f}) Dist: {distance_320:.1f}", 
                                   (10, info_y_offset + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
                        
                        # 显示偏移方向
                        direction_x = "RIGHT" if offset_x_320 > 0 else "LEFT" if offset_x_320 < 0 else "CENTER"
                        direction_y = "DOWN" if offset_y_320 > 0 else "UP" if offset_y_320 < 0 else "CENTER"
                        cv2.putText(display_img, f"Direction: {direction_x}, {direction_y}", 
                                   (10, info_y_offset + 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
                        
                        print(f"[OFFSET_DEBUG] 准星(160,160) -> 目标头部({head_x_320:.1f},{head_y_320:.1f}) 偏移({offset_x_320:.1f},{offset_y_320:.1f}) 距离{distance_320:.1f}")
                        print(f"[UNIFIED_DISPLAY_DEBUG] 统一320坐标系头部位置: ({head_x_320:.1f}, {head_y_320:.1f})")
                        print(f"[UNIFIED_DISPLAY_DEBUG] 显示坐标系头部位置: ({head_x_display:.1f}, {head_y_display:.1f})")
                
                # 计算鼠标移动需要的坐标（不是显示坐标）
                # 获取第一个目标（最近的目标）用于瞄准，或使用预测目标
                current_target = None
                is_predicted_target = False
                
                # 在鼠标移动前过滤掉置信度低的目标
                if len(targets) > 0 and 'current_mid_x' in targets.columns and 'current_mid_y' in targets.columns:
                    # 过滤出高置信度目标用于瞄准
                    high_confidence_targets = targets[targets['confidence'] >= confidence]
                    
                    if len(high_confidence_targets) > 0:
                        # 使用第一个高置信度目标（已按距离排序）
                        first_high_conf_target = high_confidence_targets.iloc[0]
                        current_target = {
                            'x_320': first_high_conf_target['current_mid_x'],
                            'y_320': first_high_conf_target['current_mid_y'],
                            'height_320': first_high_conf_target['height'],
                            'is_predicted': False,
                            'confidence': first_high_conf_target['confidence']
                        }
                        print(f"[CONFIDENCE_FILTER] 选择高置信度目标进行瞄准: 置信度={first_high_conf_target['confidence']:.3f}")
                    else:
                        print(f"[CONFIDENCE_FILTER] 没有高置信度目标可用于瞄准 (阈值={confidence:.3f})")
                        current_target = None
                elif 'predicted_target' in locals() and predicted_target is not None:
                    # 使用预测目标
                    current_target = {
                        'x_320': predicted_target['current_mid_x'],
                        'y_320': predicted_target['current_mid_y'],
                        'height_320': predicted_target['height'],
                        'is_predicted': True
                    }
                    is_predicted_target = True
                    print(f"[CONTINUOUS_TRACKING] 使用预测目标进行瞄准: ({current_target['x_320']:.1f}, {current_target['y_320']:.1f})")
                
                if current_target is not None:
                    # 获取目标在模型输出中的坐标（320x320）
                    target_x_320 = current_target['x_320']
                    target_y_320 = current_target['y_320']
                    box_height_320 = current_target['height_320']
                    
                    # 🎯 关键修复：优先使用锁定的头部位置，确保瞄准与显示一致
                    if target_lock_enabled and locked_target and not is_predicted_target:
                        # 使用锁定的头部位置（已经是320坐标系）
                        head_x_320 = locked_target['head_x']
                        head_y_320 = locked_target['head_y']
                        print(f"[HEAD_LOCK_AIMING] 使用锁定的头部位置进行瞄准: ({head_x_320:.1f}, {head_y_320:.1f})")
                    else:
                        # 计算头部位置（在320x320坐标系下）
                        if headshot_mode:
                            headshot_offset_320 = box_height_320 * 0.38
                        else:
                            headshot_offset_320 = box_height_320 * 0.2
                        
                        # 使用平滑的头部位置计算
                        head_x_320, head_y_320 = calculate_smoothed_head_position(target_x_320, target_y_320, box_height_320)
                        print(f"[HEAD_CALC_AIMING] 计算头部位置进行瞄准: ({head_x_320:.1f}, {head_y_320:.1f})")
                    
                    # 🧠 头部记忆增强：当目标置信度较低时，使用预测位置进行瞄准
                    if 'confidence' in current_target and current_target['confidence'] < confidence * 0.9:
                        predicted_pos = get_predicted_or_locked_head_position()
                        if predicted_pos:
                            head_x_320 = predicted_pos['x']
                            head_y_320 = predicted_pos['y']
                            print(f"[HEAD_MEMORY_AIMING] 使用{predicted_pos['source']}头部位置进行瞄准: ({head_x_320:.1f}, {head_y_320:.1f})")
                    
                    # 鼠标移动计算始终基于320x320坐标系
                    # 准星位置为截图区域中心
                    crosshair_x_320 = 160  # 320坐标系中心X
                    crosshair_y_320 = 160  # 320坐标系中心Y
                    
                    # 用于瞄准的坐标就是320坐标系下的头部位置
                    head_x_for_aiming = head_x_320
                    head_y_for_aiming = head_y_320
                    crosshair_x_for_aiming = crosshair_x_320
                    crosshair_y_for_aiming = crosshair_y_320
                    
                    print(f"[COORDINATE_DEBUG] 320坐标系计算:")
                    print(f"[COORDINATE_DEBUG] - 目标位置: ({target_x_320:.1f}, {target_y_320:.1f})")
                    print(f"[COORDINATE_DEBUG] - 头部位置: ({head_x_320:.1f}, {head_y_320:.1f})")
                    print(f"[COORDINATE_DEBUG] - 准星位置: ({crosshair_x_320}, {crosshair_y_320})")
                    
                    if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
                        # 增强检测模式：将模型坐标转换到截取区域坐标（仅用于显示）
                        target_x_for_display = target_x_320 * enhanced_config.SCALE_FACTOR
                        target_y_for_display = target_y_320 * enhanced_config.SCALE_FACTOR
                        box_height_for_display = box_height_320 * enhanced_config.SCALE_FACTOR
                        
                        print(f"[ENHANCED_DEBUG] 显示坐标转换:")
                        print(f"[ENHANCED_DEBUG] - 截取区域坐标: ({target_x_for_display:.1f}, {target_y_for_display:.1f})")
                    else:
                        # 标准模式：显示坐标与320坐标相同
                        target_x_for_display = target_x_320
                        target_y_for_display = target_y_320
                        box_height_for_display = box_height_320
                    
                    # 计算偏移信息（用于显示）
                    if is_predicted_target:
                        # 对于预测目标，使用320坐标系计算偏移
                        offset_x = head_x_320 - crosshair_x_320
                        offset_y = head_y_320 - crosshair_y_320
                    else:
                        # 对于实际目标，使用320坐标系计算偏移
                        offset_x = head_x_320 - crosshair_x_320
                        offset_y = head_y_320 - crosshair_y_320
                    
                    distance = (offset_x**2 + offset_y**2)**0.5
                else:
                    # 没有目标时，清除相关变量
                    head_x_for_aiming = None
                    head_y_for_aiming = None
                    offset_x = 0
                    offset_y = 0
                    distance = 0
                
                # 检查激活键状态
                caps_lock_pressed = win32api.GetKeyState(0x14) < 0  # Caps Lock - 纯扳机键
                right_mouse_pressed = win32api.GetKeyState(0x02) < 0  # 鼠标右键 - 瞄准+扳机
                
                # 鼠标右键：瞄准+扳机模式
                if right_mouse_pressed and head_x_for_aiming is not None:
                    print(f"[DEBUG] 🖱️ 鼠标右键已按下，激活瞄准系统")
                    
                    if is_predicted_target:
                        print(f"[CONTINUOUS_TRACKING] 使用预测目标进行瞄准移动")
                    
                    # 修复坐标计算错误：鼠标移动方向 = 目标位置 - 准星位置
                    # 如果目标在右侧（head_x > crosshair_x），鼠标应该向右移动（正值）
                    # 如果目标在左侧（head_x < crosshair_x），鼠标应该向左移动（负值）
                    mouseMove = [head_x_for_aiming - crosshair_x_for_aiming, head_y_for_aiming - crosshair_y_for_aiming]
                    
                    print(f"[TRACKING] 目标头部位置(瞄准坐标): ({head_x_for_aiming:.1f}, {head_y_for_aiming:.1f})")
                    print(f"[TRACKING] 准星位置(瞄准坐标): ({crosshair_x_for_aiming}, {crosshair_y_for_aiming})")
                    print(f"[COORDINATE_FIX] 修复后的鼠标移动计算: ({mouseMove[0]:.1f}, {mouseMove[1]:.1f})")
                    print(f"[COORDINATE_FIX] 移动方向解释: X={mouseMove[0]:.1f}({'右' if mouseMove[0] > 0 else '左' if mouseMove[0] < 0 else '无'}), Y={mouseMove[1]:.1f}({'下' if mouseMove[1] > 0 else '上' if mouseMove[1] < 0 else '无'})")
                    
                    movement = mouseMove
                    
                    if movement is not None:
                        move_x, move_y = movement
                        print(f"[TRACKING] 计算完成 - 鼠标移动: ({move_x:.1f}, {move_y:.1f})")
                        print(f"[TRACKING] 瞄准模式: {aiming_system.aiming_mode}")
                        print(f"[TRACKING] 移动幅度系数: {aiming_system.tracker.movement_amp}")
                        
                        # 🔥 关键优化：先检查开火条件，再执行移动
                        # 这样可以在移动过程中随时开火，不会错失开火机会
                        fire_executed = False
                        
                        # 🎯 移动过程中的实时开火检测
                        if trigger_system.enabled and len(targets) > 0:
                            # 计算当前准星位置（320坐标系）
                            current_crosshair_x_320 = crosshair_x_320
                            current_crosshair_y_320 = crosshair_y_320
                            
                            # 检测是否有开火机会
                            realtime_fire_success = check_realtime_fire_opportunity(
                                targets, current_crosshair_x_320, current_crosshair_y_320
                            )
                            
                            if realtime_fire_success:
                                fire_executed = True
                                print("[REALTIME_FIRE] 🔥 移动过程中检测到开火机会并成功开火")
                        
                        # 右键模式的精确扳机系统检查（移动前优先检查）
                        if trigger_system.enabled and not movement_paused and not fire_executed:
                            # 🎯 实时开火检测 - 不等待移动完成
                            should_check_fire = True
                            fire_reason = "移动前实时检测"
                            
                            if should_check_fire:
                                # 🎯 关键修复：确保头部位置和鼠标检测使用同一帧数据
                                current_frame_head_x = head_x_320
                                current_frame_head_y = head_y_320
                                current_frame_crosshair_x = crosshair_x_320
                                current_frame_crosshair_y = crosshair_y_320
                                
                                print(f"[FIRE_FIRST] 🔥 移动前开火检测 ({fire_reason}):")
                                print(f"[FIRE_FIRST] - 头部位置: ({current_frame_head_x:.1f}, {current_frame_head_y:.1f})")
                                print(f"[FIRE_FIRST] - 准星位置: ({current_frame_crosshair_x}, {current_frame_crosshair_y})")
                                
                                # 计算归一化坐标
                                normalized_target_x = current_frame_head_x / DETECTION_SIZE
                                normalized_target_y = current_frame_head_y / DETECTION_SIZE
                                detection_center = (0.5, 0.5)
                                
                                # 立即进行扳机检测
                                trigger_fired = trigger_system.check_and_fire(
                                    normalized_target_x, normalized_target_y, detection_center, 0,
                                    game_fov=GAME_FOV, detection_size=DETECTION_SIZE, 
                                    game_width=ACTUAL_GAME_WIDTH, game_height=ACTUAL_GAME_HEIGHT
                                )
                                
                                if trigger_fired:
                                    print(f"[FIRE_FIRST] 🔥 移动前开火成功！({fire_reason})")
                                    fire_executed = True
                                else:
                                    distance_to_center = ((current_frame_head_x - current_frame_crosshair_x)**2 + (current_frame_head_y - current_frame_crosshair_y)**2)**0.5
                                    print(f"[FIRE_FIRST] 移动前检测 - 距离: {distance_to_center:.1f}px，继续移动")
                        
                        # 检查移动是否被暂停（开火时）或已经开火
                        if not movement_paused and not fire_executed:
                            # 🎯 直接移动 - 使用最新计算的头部位置，不使用平滑移动
                            if abs(move_x) > 0.1 or abs(move_y) > 0.1:  # 避免微小移动
                                print(f"🎯 [DIRECT_MOVE] 直接移动到目标: ({move_x:.1f}, {move_y:.1f})")
                                
                                # 使用直接移动，不使用平滑移动
                                if move_mouse(move_x, move_y, use_smooth=False):
                                    print("[DEBUG] 🎯 直接移动成功")
                                    
                                    # 更新连续跟踪系统的移动向量（用于实时跟踪）
                                    if CONTINUOUS_TRACKING_AVAILABLE and continuous_tracker:
                                        continuous_tracker.update_movement(move_x, move_y)
                                        print(f"[CONTINUOUS_TRACKING] 更新直接移动向量: ({move_x:.1f}, {move_y:.1f})")
                                else:
                                    print("[DEBUG] ❌ 直接移动失败")
                            else:
                                print("[DEBUG] 🎯 目标已对齐，无需移动鼠标")
                            
                            # 移动完成后打印相对于截屏框的位置信息
                            # 计算移动后的准星位置
                            new_crosshair_x = cWidth + int(move_x)
                            new_crosshair_y = cHeight + int(move_y)
                            
                            print(f"[POSITION] 移动完成后位置信息:")
                            print(f"[POSITION] - 目标在截屏框中的位置(320坐标): ({head_x_320:.1f}, {head_y_320:.1f})")
                            print(f"[POSITION] - 移动前准星位置(320坐标): ({crosshair_x_320:.1f}, {crosshair_y_320:.1f})")
                            print(f"[POSITION] - 鼠标移动量: ({int(move_x)}, {int(move_y)}) 像素")
                            print(f"[POSITION] - 移动后准星位置(320坐标): ({crosshair_x_320 + int(move_x):.1f}, {crosshair_y_320 + int(move_y):.1f})")
                            print(f"[POSITION] - 截屏框尺寸: {DETECTION_SIZE}x{DETECTION_SIZE}")
                            print(f"[POSITION] - 移动后目标相对准星偏移(320坐标): ({head_x_320 - (crosshair_x_320 + int(move_x)):.1f}, {head_y_320 - (crosshair_y_320 + int(move_y)):.1f}) 像素")
                            
                            # 计算目标在截屏框中的相对位置（百分比）
                            target_x_percent = (head_x_320 / DETECTION_SIZE) * 100
                            target_y_percent = (head_y_320 / DETECTION_SIZE) * 100
                            new_crosshair_x_320 = crosshair_x_320 + int(move_x)
                            new_crosshair_y_320 = crosshair_y_320 + int(move_y)
                            new_crosshair_x_percent = (new_crosshair_x_320 / DETECTION_SIZE) * 100
                            new_crosshair_y_percent = (new_crosshair_y_320 / DETECTION_SIZE) * 100
                            
                            print(f"[POSITION] - 目标在截屏框中的百分比位置: ({target_x_percent:.1f}%, {target_y_percent:.1f}%)")
                            print(f"[POSITION] - 移动后准星在截屏框中的百分比位置: ({new_crosshair_x_percent:.1f}%, {new_crosshair_y_percent:.1f}%)")
                            
                            # 🎯 移动完成后重置移动状态
                            is_moving_to_target = False
                            print("[MOVEMENT_LOCK] 🏁 移动完成，重置移动状态")
                        else:
                            print("[DEBUG] 鼠标移动已暂停（开火中）或已执行开火")
                        
                        # 🔥 移动后的补充开火检测（仅在移动前未开火时执行）
                        # 这是为了捕获移动后可能出现的新的开火机会
                        if trigger_system.enabled and not movement_paused and not fire_executed:
                            # 🎯 移动后补充检测（仅在移动前未开火时）
                            should_check_fire = True
                            fire_reason = "移动后补充检测"
                            
                            if should_check_fire:
                                # 使用移动后的位置进行检测
                                current_frame_head_x = head_x_320
                                current_frame_head_y = head_y_320
                                # 计算移动后的准星位置
                                current_frame_crosshair_x = crosshair_x_320 + int(move_x) if 'move_x' in locals() else crosshair_x_320
                                current_frame_crosshair_y = crosshair_y_320 + int(move_y) if 'move_y' in locals() else crosshair_y_320
                                
                                print(f"[FIRE_AFTER] 🔥 移动后开火检测 ({fire_reason}):")
                                print(f"[FIRE_AFTER] - 头部位置: ({current_frame_head_x:.1f}, {current_frame_head_y:.1f})")
                                print(f"[FIRE_AFTER] - 移动后准星位置: ({current_frame_crosshair_x}, {current_frame_crosshair_y})")
                                
                                # 计算归一化坐标
                                normalized_target_x = current_frame_head_x / DETECTION_SIZE
                                normalized_target_y = current_frame_head_y / DETECTION_SIZE
                                detection_center = (0.5, 0.5)
                                
                                # 进行扳机检测
                                trigger_fired = trigger_system.check_and_fire(
                                    normalized_target_x, normalized_target_y, detection_center, 0,
                                    game_fov=GAME_FOV, detection_size=DETECTION_SIZE, 
                                    game_width=ACTUAL_GAME_WIDTH, game_height=ACTUAL_GAME_HEIGHT
                                )
                                
                                if trigger_fired:
                                    print(f"[FIRE_AFTER] 🔥 移动后开火成功！({fire_reason})")
                                else:
                                    distance_to_center = ((current_frame_head_x - current_frame_crosshair_x)**2 + (current_frame_head_y - current_frame_crosshair_y)**2)**0.5
                                    print(f"[FIRE_AFTER] 移动后检测 - 距离: {distance_to_center:.1f}px")
                        elif trigger_system.enabled and movement_paused:
                            print("[TRIGGER] 右键模式扳机系统已启用，但移动已暂停（开火中）")
                        elif trigger_system.enabled and fire_executed:
                            print("[TRIGGER] 右键模式扳机系统已启用，但已在移动前开火，跳过移动后检测")
                
                # Caps Lock：纯扳机模式（不瞄准，只在准星对准头部时开火）
                elif caps_lock_pressed and head_x_for_aiming is not None:
                    mode_text = "快速模式" if pureTriggerFastMode else "标准模式"
                    print(f"[DEBUG] ⌨️ Caps Lock已按下，激活纯扳机模式 ({mode_text})")
                    
                    if is_predicted_target:
                        print(f"[CONTINUOUS_TRACKING] 使用预测目标进行扳机检测")
                    
                    # 🔥 使用同帧数据进行扳机检测（与右键模式保持一致）
                    print(f"[FRAME_SYNC] Caps Lock模式使用同帧数据 - 头部位置: ({head_x_for_aiming}, {head_y_for_aiming}), 准星位置: ({crosshair_x_for_aiming}, {crosshair_y_for_aiming})")
                    
                    # 使用当前帧的准星位置（确保使用最新帧数据）
                    current_crosshair_x, current_crosshair_y = crosshair_x_for_aiming, crosshair_y_for_aiming
                    
                    # 计算距离中心的距离（使用同帧数据）
                    distance_to_center = ((head_x_for_aiming - current_crosshair_x)**2 + (head_y_for_aiming - current_crosshair_y)**2)**0.5
                    
                    # 纯扳机模式：只检查是否对准，不进行瞄准移动
                    if distance_to_center < pureTriggerThreshold:  # 使用配置的阈值
                        print("[TRIGGER] 🔥 Caps Lock纯扳机模式已触发！")
                        print(f"[TRIGGER] 距离中心(同帧数据): {distance_to_center:.1f} 像素 (阈值: {pureTriggerThreshold})")
                        
                        # 根据配置选择开火函数
                        if pureTriggerFastMode:
                            print("[TRIGGER] 使用快速开火模式（跳过WASD检测）")
                            auto_fire_fast()
                        else:
                            print("[TRIGGER] 使用标准开火模式（包含WASD检测）")
                            auto_fire()
                    else:
                        print(f"[TRIGGER] Caps Lock纯扳机模式激活，但未对准目标 (距离(同帧数据): {distance_to_center:.1f} 像素，阈值: {pureTriggerThreshold})")
                        
                        # FPS优化：移除延迟以获得最大性能
                        pass
                
                else:
                    print(f"[DEBUG] 目标偏离中心 {distance:.1f}px，无激活键按下")
                
                # 显示偏差信息（仅在启用Live Feed时）
                if showLiveFeed and display_img is not None:
                    # 计算缩放比例（从320x320到原始图像大小）
                    scale_x = display_img.shape[1] / 320.0
                    scale_y = display_img.shape[0] / 320.0
                    
                    cv2.putText(display_img, f"Offset: ({offset_x}, {offset_y}) Dist: {distance}px", 
                               (10, info_y_offset + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                
                # 可视化信息已经在上面的条件块中绘制了
        
        # Live Feed窗口显示（仅在启用时，带帧率限制防止闪烁）
        current_time = time.time()
        if showLiveFeed:
            # 检查是否到了刷新时间（帧率限制）
            if current_time - last_live_feed_time >= live_feed_frame_interval:
                # 🔥 使用与头部位置计算相同的帧（确保完全同步）
                print(f"[FRAME_SYNC] Live Feed使用与头部计算相同的帧")
                live_feed_img = display_img  # 使用已经处理过的同一帧
                
                if live_feed_img is not None:
                    # 创建Live Feed显示图像的副本
                    live_display_img = live_feed_img.copy()
                    
                    # 注意：掩码已经在display_img创建时应用过了，无需重复应用
                    
                    # 在实时截图上绘制所有UI元素和目标标记
                    if len(targets) > 0:
                        # 重新绘制基本信息
                        info_y_offset = 30
                        
                        # 显示鼠标位置（准星位置）
                        cv2.putText(live_display_img, f"Mouse: ({mouse_x}, {mouse_y})", 
                                   (10, info_y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        
                        # 显示准星位置
                        cv2.putText(live_display_img, f"Crosshair: ({crosshair_x}, {crosshair_y})", 
                                   (10, info_y_offset + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                        
                        # 在图像中心画准星标记
                        center_x = live_display_img.shape[1] // 2
                        center_y = live_display_img.shape[0] // 2
                        cv2.circle(live_display_img, (center_x, center_y), 3, (255, 255, 0), -1)
                        cv2.circle(live_display_img, (center_x, center_y), 8, (255, 255, 0), 1)
                        cv2.putText(live_display_img, "DOT", (center_x, center_y), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                        
                        # 显示检测到的目标数量
                        cv2.putText(live_display_img, f"Targets: {len(targets)}", 
                                   (10, info_y_offset + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        
                        # 重新绘制目标框和头部标记（使用实时坐标）
                        for idx in range(len(targets)):
                            row = targets.iloc[idx]
                            target_x_320 = row['current_mid_x']
                            target_y_320 = row['current_mid_y']
                            box_height_320 = row.height
                            box_width_320 = row.width
                            target_confidence = row['confidence']
                            
                            # 坐标转换到实时显示图像
                            if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
                                model_to_capture_scale = enhanced_config.SCALE_FACTOR
                                capture_to_display_scale_x = live_display_img.shape[1] / enhanced_config.CAPTURE_SIZE
                                capture_to_display_scale_y = live_display_img.shape[0] / enhanced_config.CAPTURE_SIZE
                                
                                target_x_capture = target_x_320 * model_to_capture_scale
                                target_y_capture = target_y_320 * model_to_capture_scale
                                box_height_capture = box_height_320 * model_to_capture_scale
                                box_width_capture = box_width_320 * model_to_capture_scale
                                
                                target_x = target_x_capture * capture_to_display_scale_x
                                target_y = target_y_capture * capture_to_display_scale_y
                                box_height = box_height_capture * capture_to_display_scale_y
                                box_width = box_width_capture * capture_to_display_scale_x
                            else:
                                scale_x = live_display_img.shape[1] / 320
                                scale_y = live_display_img.shape[0] / 320
                                target_x = target_x_320 * scale_x
                                target_y = target_y_320 * scale_y
                                box_height = box_height_320 * scale_y
                                box_width = box_width_320 * scale_x
                            
                            # 绘制目标框
                            x1 = int(target_x - box_width / 2)
                            y1 = int(target_y - box_height / 2)
                            x2 = int(target_x + box_width / 2)
                            y2 = int(target_y + box_height / 2)
                            cv2.rectangle(live_display_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            
                            # 显示置信度
                            confidence_text = f"Conf: {target_confidence:.3f}"
                            confidence_color = (0, 255, 0) if target_confidence >= confidence else (0, 165, 255)
                            cv2.putText(live_display_img, confidence_text, (x1, y1 - 10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, confidence_color, 2)
                            
                            # 显示目标索引
                            index_text = f"#{idx}"
                            cv2.putText(live_display_img, index_text, (x1, y1 - 30), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                            
                            # 计算并绘制头部标记（实时同步）- 修复坐标转换
                            # 🔥 关键修复：头部位置计算应该基于320坐标系，然后转换到显示坐标系
                            if headshot_mode:
                                headshot_offset_320 = box_height_320 * 0.38
                            else:
                                headshot_offset_320 = box_height_320 * 0.2
                            
                            # 使用平滑的头部位置计算
                            head_x_320, head_y_320 = calculate_smoothed_head_position(target_x_320, target_y_320, box_height_320)
                            
                            # 转换到显示坐标系
                            if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
                                model_to_capture_scale = enhanced_config.SCALE_FACTOR
                                capture_to_display_scale_x = live_display_img.shape[1] / enhanced_config.CAPTURE_SIZE
                                capture_to_display_scale_y = live_display_img.shape[0] / enhanced_config.CAPTURE_SIZE
                                
                                head_x_capture = head_x_320 * model_to_capture_scale
                                head_y_capture = head_y_320 * model_to_capture_scale
                                
                                head_x = head_x_capture * capture_to_display_scale_x
                                head_y = head_y_capture * capture_to_display_scale_y
                            else:
                                scale_x = live_display_img.shape[1] / 320
                                scale_y = live_display_img.shape[0] / 320
                                head_x = head_x_320 * scale_x
                                head_y = head_y_320 * scale_y
                            
                            # 只为高置信度目标绘制头部标记
                            if target_confidence >= confidence:
                                cv2.circle(live_display_img, (int(head_x), int(head_y)), 5, (0, 0, 255), -1)
                                cv2.putText(live_display_img, "HEAD", (int(head_x) + 10, int(head_y)), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                print(f"[LIVE_FEED_COORDINATE_FIX] 目标{idx} 坐标转换:")
                                print(f"  320坐标系: 目标({target_x_320:.1f}, {target_y_320:.1f}) 头部({head_x_320:.1f}, {head_y_320:.1f})")
                                print(f"  显示坐标系: 目标({target_x:.1f}, {target_y:.1f}) 头部({head_x:.1f}, {head_y:.1f})")
                                print(f"  置信度: {target_confidence:.3f}")
                    
                    # 显示实时Live Feed
                    display_height, display_width = live_display_img.shape[:2]
                    print(f"[LIVE_FEED_DEBUG] 原始图像尺寸: {display_width}x{display_height}")
                    
                    # 🔥 修复：直接显示原始尺寸，不进行缩放以保持最佳清晰度
                    cv2.imshow('Live Feed', live_display_img)
                    print(f"[LIVE_FEED_REALTIME] 高清显示: {display_width}x{display_height} (无缩放)")
                
                last_live_feed_time = current_time
            
            # 检查退出键（每帧都检查，但窗口刷新有限制）
            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                exit()
        elif not showLiveFeed:
            # 即使不显示Live Feed，也要检查退出键
            if cv2.waitKey(1) & 0xFF == ord('q'):
                exit()
        
        # 记录检测时间
        # 记录总体FPS和性能监控数据
        if performance_monitor is not None:
            performance_monitor.increment_counter('total_frames')
        
        detection_time = time.time() - processing_start_time
    camera.stop()
    
    # 清理统一内存GPU加速资源
    if unified_gpu_processor is not None:
        try:
            cleanup_unified_gpu_processor()
            print("[INFO] 🌐 统一内存GPU处理器已清理")
        except Exception as e:
            print(f"[WARNING] 统一内存GPU处理器清理失败: {e}")
    
    if unified_memory_manager is not None:
        try:
            cleanup_unified_memory_manager()
            print("[INFO] 🌐 统一内存管理器已清理")
        except Exception as e:
            print(f"[WARNING] 统一内存管理器清理失败: {e}")
    
    # 清理传统GPU加速资源
    if gpu_processor is not None:
        try:
            cleanup_gpu_processor()
            print("[INFO] 🧹 传统GPU加速处理器已清理")
        except Exception as e:
            print(f"[WARNING] 传统GPU处理器清理失败: {e}")
    
    if gpu_memory_manager is not None:
        try:
            cleanup_gpu_memory_manager()
            print("[INFO] 🧹 传统GPU内存管理器已清理")
        except Exception as e:
            print(f"[WARNING] 传统GPU内存管理器清理失败: {e}")
    
    # 清理双GPU资源
    if DUAL_GPU_AVAILABLE:
        try:
            stop_gpu_monitoring()
            print("[INFO] 🔄 GPU监控已停止")
        except:
            pass
    
    # 清理高性能截图系统
    if HIGH_PERFORMANCE_SCREENSHOT_AVAILABLE and 'high_perf_screenshot' in locals():
        try:
            high_perf_screenshot.stop()
            print("[INFO] 📸 高性能截图系统已停止")
        except Exception as e:
            print(f"[WARNING] 高性能截图系统停止失败: {e}")
    
    # 清理多线程AI处理系统
    if MULTI_THREADED_AI_AVAILABLE and 'multi_threaded_ai' in locals():
        try:
            multi_threaded_ai.stop()
            print("[INFO] 🧠 多线程AI处理系统已停止")
        except Exception as e:
            print(f"[WARNING] 多线程AI处理系统停止失败: {e}")
    
    # 清理性能监控系统
    if PERFORMANCE_MONITOR_AVAILABLE and 'performance_monitor' in locals():
        try:
            performance_monitor.stop()
            print("[INFO] 📊 性能监控系统已停止")
        except Exception as e:
            print(f"[WARNING] 性能监控系统停止失败: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exception(e)
        print("ERROR: " + str(e))
        print("Ask @Wonder for help in our Discord in the #ai-aimbot channel ONLY: https://discord.gg/rootkitorg")
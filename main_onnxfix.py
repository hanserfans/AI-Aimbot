#!/usr/bin/env python3
"""
AI-Aimbot ONNX 简化版本 - 纯320坐标系
- 完全使用320坐标系，无任何缩放处理
- 集成硬件驱动移动鼠标方式（Arduino + G-Hub + Win32 API）
- 简化的目标选择逻辑
- 优化的性能和精度
"""

import onnxruntime as ort
import numpy as np
import gc
import cv2
import time
import win32api
import win32con

# ==================== “多点重合”开火方案配置 ====================
# 在 FIRE_EVENT_WINDOW 秒内，需要检测到 FIRE_EVENT_THRESHOLD 次重合才会开火# 开火事件检测配置
FIRE_EVENT_WINDOW = 1 # 时间窗口（秒）- 增加到0.5秒，更宽松的检测
FIRE_EVENT_THRESHOLD = 2 # 开火阈值（次数）- 降低到1次，更容易触发
alignment_events = []       # 存储重合事件时间戳的列表

# 全局变量用于开火回调
current_targets = None      # 当前帧的目标数据
current_crosshair_x = 159   # 当前准星X位置（320坐标系中心）
current_crosshair_y = 186  # 当前准星Y位置（320坐标系中心）

# 鼠标移动限制配置
MAX_SINGLE_MOVE_PIXELS = 240#移动像素限制 - 平衡流畅度与精确度
# =================================================================
import pandas as pd
from utils.general import (cv2, non_max_suppression, xyxy2xywh)
import torch

# 配置导入
from config import (
    aaMovementAmp, useMask, maskHeight, maskWidth, aaQuitKey, 
    confidence, headshot_mode, cpsDisplay, visuals, onnxChoice, centerOfScreen,
    screenShotWidth, screenShotHeight, autoFire, autoFireShots, autoFireDelay, 
    autoFireKey, pureTriggerFastMode, pureTriggerThreshold, showLiveFeed, 
    maxTargets, targetSelectionStrategy, DEBUG_LOG
)

# ==================== 平滑移动配置 ====================
# 平滑移动开关（True=平滑移动，False=机械移动）
USE_SMOOTH_MOVEMENT = True
# 非阻塞移动开关（True=非阻塞，False=阻塞）
USE_NON_BLOCKING_MOVEMENT = True

print(f"[CONFIG] 🎯 移动模式: {'平滑移动' if USE_SMOOTH_MOVEMENT else '机械移动'}")
print(f"[CONFIG] 🔄 移动类型: {'非阻塞' if USE_NON_BLOCKING_MOVEMENT else '阻塞'}")
print(f"[CONFIG] 📏 最大单次移动: {MAX_SINGLE_MOVE_PIXELS}px (多步瞄准)")
print(f"[CONFIG] 🕹️ 鼠标移动放大器: {aaMovementAmp}")
# 轻量级调试开关由全局配置控制（config.DEBUG_LOG）

# 轻量级调试日志函数（支持可选节流）
LOG_THROTTLE_MS_DEFAULT = 200
_last_debug_log_times = {}

def debug_log(message, tag=None, throttle_ms=None):
    """
    轻量调试输出函数
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
        # 若节流出错，直接打印以免影响调试
        print(message)

# ==================== 轻量FPS计数器 ====================
# 说明：每秒输出一次FPS，默认不打印，仅在DEBUG_LOG=True时启用。
_fps_last_ts = 0.0
_fps_count = 0

def fps_tick(label: str = "MAIN"):
    """
    轻量级FPS计数器（每秒一次）
    - 仅在 DEBUG_LOG 为 True 时统计并打印
    - 开销极小：一次整数自增 + 简单时间比较

    参数:
      label: 文本标签，用于区分不同循环来源
    """
    if not DEBUG_LOG:
        return
    global _fps_last_ts, _fps_count
    # 首次调用初始化时间戳
    if _fps_last_ts == 0.0:
        _fps_last_ts = time.time()
        _fps_count = 0
        return
    _fps_count += 1
    now = time.time()
    if now - _fps_last_ts >= 1.0:
        debug_log(f"[FPS] {label} 循环 {_fps_count} fps", tag="FPS")
        _fps_last_ts = now
        _fps_count = 0

# ==================== 自适应移动放大器 ====================
# 说明：根据本次瞄准距离动态调整鼠标移动放大器，提升近距离的细腻度、远距离的响应速度
ADAPTIVE_AMP_MIN = 3
ADAPTIVE_AMP_MAX = 5

def compute_adaptive_amp(distance):
    """
    计算自适应鼠标移动放大器（范围 [0.8, 2.0]）

    参数:
      distance (float): 本次准星到目标头部的像素距离（320坐标系）

    返回:
      float: 当前帧使用的移动放大器

    原理:
      - 将距离按 MAX_SINGLE_MOVE_PIXELS 归一化到 [0,1]
      - 线性插值到 [ADAPTIVE_AMP_MIN, ADAPTIVE_AMP_MAX]
      - 距离越大移动越快，距离越小移动越细腻
    """
    # 距离归一化（限制在 [0, MAX_SINGLE_MOVE_PIXELS]）
    clamped = min(max(distance, 0.0), float(MAX_SINGLE_MOVE_PIXELS))
    norm = clamped / float(MAX_SINGLE_MOVE_PIXELS)
    # 线性映射到目标范围
    amp = ADAPTIVE_AMP_MIN + (ADAPTIVE_AMP_MAX - ADAPTIVE_AMP_MIN) * norm
    return amp

import gameSelection

# 扳机系统导入
from auto_trigger_system import get_trigger_system

# 平滑移动系统导入
from smooth_mouse_movement import create_smooth_movement_system
from non_blocking_smooth_movement import create_non_blocking_smooth_movement_system

# ==================== 硬件驱动导入 ====================

# 1. Arduino 硬件驱动导入
ARDUINO_AVAILABLE = False
arduino_driver = None
try:
    from arduino_mouse_driver import ArduinoMouseDriver
    arduino_driver = ArduinoMouseDriver()
    arduino_driver.connect()  # 尝试连接
    
    if arduino_driver.is_arduino_connected:
        ARDUINO_AVAILABLE = True
        print("[SUCCESS] Arduino 硬件驱动连接成功")
    else:
        arduino_driver = None
        print("[INFO] Arduino 硬件驱动连接失败")
except ImportError as e:
    arduino_driver = None
    print(f"[INFO] Arduino 驱动不可用: {e}")

# 2. G-Hub 驱动导入
GHUB_AVAILABLE = False
try:
    from mouse_driver.MouseMove import ghub_move, ghub_click
    print("[SUCCESS] G-Hub 驱动导入成功")
    GHUB_AVAILABLE = True
except ImportError as e:
    print(f"[INFO] G-Hub 驱动不可用: {e}")
    GHUB_AVAILABLE = False

# 打印当前使用的鼠标控制方法
if ARDUINO_AVAILABLE:
    print("[INFO] 当前鼠标控制方法: Arduino 硬件驱动")
elif GHUB_AVAILABLE:
    print("[INFO] 当前鼠标控制方法: G-Hub 驱动")
else:
    print("[INFO] 当前鼠标控制方法: Win32 API")

# 将已连接的 Arduino 驱动注入到自动扳机系统以复用串口
try:
    trigger_system = get_trigger_system()
    if ARDUINO_AVAILABLE and arduino_driver:
        trigger_system.attach_arduino_driver(arduino_driver)
except Exception as e:
    print(f"[WARN] 无法将 Arduino 驱动注入扳机系统: {e}")

# ==================== 鼠标移动函数 ====================

# 创建直接移动函数（用于平滑移动系统的底层调用）
def move_mouse_direct(x, y):
    """
    直接鼠标移动函数，不使用平滑算法
    用作平滑移动系统的底层移动函数
    """
    try:
        if ARDUINO_AVAILABLE and arduino_driver:
            # 优先使用Arduino驱动
            success = arduino_driver.move_mouse(x, y)
            if success:
                return True
            else:
                print("[WARNING] Arduino移动失败，切换到G-Hub")
        
        if GHUB_AVAILABLE:
            # 备选方案1: G-Hub驱动
            ghub_move(int(x), int(y))
            return True
        else:
            # 备选方案2: Win32 API
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)
            return True
            
    except Exception as e:
        print(f"[ERROR] 直接鼠标移动失败: {e}")
        # 最后的备选方案：Win32 API
        try:
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)
            return True
        except Exception as e2:
            print(f"[ERROR] 所有鼠标移动方法都失败: {e2}")
            return False

# 创建平滑移动系统
try:
    # 创建非阻塞平滑移动系统（推荐）
    non_blocking_smooth_movement_system = create_non_blocking_smooth_movement_system(move_mouse_direct)
    
    # 保留原有平滑移动系统作为备选
    smooth_movement_system = create_smooth_movement_system(move_mouse_direct)
    
    print("[INFO] ✅ 平滑移动系统初始化成功")
except Exception as e:
    print(f"[ERROR] 平滑移动系统初始化失败: {e}")
    non_blocking_smooth_movement_system = None
    smooth_movement_system = None

def move_mouse(x, y, use_smooth=True, use_non_blocking=True):
    """
    统一的鼠标移动函数，支持平滑移动和非阻塞移动
    
    Args:
        x: X轴移动距离
        y: Y轴移动距离
        use_smooth: 是否使用平滑移动（默认True）
        use_non_blocking: 是否使用非阻塞移动（默认True）
    
    Returns:
        bool: 移动是否成功
    """
    # 获取扳机系统实例
    trigger_system = get_trigger_system()
    
    # 如果扳机系统处于精确重合状态，则不移动鼠标
    if trigger_system.is_precisely_aligned():
        print("[MOVE_MOUSE] 🎯 精确重合，移动已暂停")
        return True
        
    if use_smooth and non_blocking_smooth_movement_system and use_non_blocking:
        # 使用非阻塞平滑移动算法（推荐，包含指数函数）
        return non_blocking_smooth_movement_system.move_to_target(x, y)
    elif use_smooth and smooth_movement_system:
        # 使用传统阻塞平滑移动算法
        return smooth_movement_system.smooth_move_to_target(x, y)
    else:
        # 使用直接移动（原来的机械移动）
        return move_mouse_direct(x, y)

# ==================== 开火函数 ====================

def auto_fire():
    """
    自动开火函数 - 标准模式
    现在与AutoTriggerSystem共享冷却时间机制；优化按下/抬起间隔为1ms以减少阻塞
    """
    try:
        trigger_system = get_trigger_system()
        
        # 冷却检查：冷却期内禁止开火
        if trigger_system.is_on_cooldown():
            remaining = max(0.0, trigger_system.cooldown_duration - (time.time() - trigger_system.last_fire_time))
            if DEBUG_LOG:
                print(f"[AUTO_FIRE] ⏱️ 冷却中，剩余时间: {remaining:.2f}秒")
            return
        
        if DEBUG_LOG:
            print("[AUTO_FIRE] 🔥 直接开火（遵守冷却），无WASD检测")
        
        # 优先使用Arduino驱动
        if ARDUINO_AVAILABLE and arduino_driver and arduino_driver.is_arduino_connected:
            try:
                result = arduino_driver.click_mouse('L')
                if result['success']:
                    if DEBUG_LOG:
                        print("[AUTO_FIRE] Arduino开火成功")
                    trigger_system.last_fire_time = time.time()
                    return
            except Exception as e:
                print(f"[AUTO_FIRE] Arduino开火失败: {e}")
        
        # 备选方案：Win32 API
        try:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            # 减少按下-抬起间隔为1ms，降低对主循环的影响
            time.sleep(0.001)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            if DEBUG_LOG:
                print("[AUTO_FIRE] Win32 API开火成功")
            trigger_system.last_fire_time = time.time()
        except Exception as e:
            print(f"[AUTO_FIRE] Win32 API开火失败: {e}")
            
    except Exception as e:
        print(f"[AUTO_FIRE] 开火函数异常: {e}")

def auto_fire_fast():
    """
    快速开火函数 - 跳过WASD检测
    专为纯扳机模式设计，提供最快的响应速度
    优化Win32按下/抬起间隔为1ms以减少阻塞
    """
    try:
        trigger_system = get_trigger_system()
        
        # 冷却检查：冷却期内禁止开火
        if trigger_system.is_on_cooldown():
            remaining = max(0.0, trigger_system.cooldown_duration - (time.time() - trigger_system.last_fire_time))
            print(f"[FAST_FIRE] ⏱️ 冷却中，剩余时间: {remaining:.2f}秒")
            return
        
        print("[AUTO_FIRE_FAST] 🚀 启动快速纯扳机模式（遵守冷却）")
        
        # 确定使用的驱动类型
        driver_type = "Arduino" if (ARDUINO_AVAILABLE and arduino_driver and arduino_driver.is_arduino_connected) else "Win32"
        print(f"[AUTO_FIRE_FAST] 🔥 开始连续开火，共{autoFireShots}发，间隔{autoFireDelay}ms")
        
        for i in range(autoFireShots):
            # 优先使用Arduino驱动
            if ARDUINO_AVAILABLE and arduino_driver and arduino_driver.is_arduino_connected:
                try:
                    result = arduino_driver.click_mouse('L')
                    if result['success']:
                        if DEBUG_LOG:
                            print(f"[AUTO_FIRE_FAST] 🔥 第{i+1}发开火 (Arduino-CL)")
                    else:
                        print(f"[AUTO_FIRE_FAST] ⚠️ Arduino开火失败: {result.get('error', 'Unknown error')}")
                        # 备选方案：Win32 API
                        try:
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                            # 减少按下-抬起间隔为1ms，降低对主循环的影响
                            time.sleep(0.001)
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                            if DEBUG_LOG:
                                print(f"[AUTO_FIRE_FAST] 🔥 第{i+1}发开火 (备用方案-左键)")
                        except Exception as e:
                            print(f"[AUTO_FIRE_FAST] ❌ 第{i+1}发开火失败: {e}")
                except Exception as e:
                    print(f"[AUTO_FIRE_FAST] ❌ Arduino开火异常: {e}")
                    # 备选方案：Win32 API
                    try:
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        # 减少按下-抬起间隔为1ms，降低对主循环的影响
                        time.sleep(0.001)
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                        if DEBUG_LOG:
                            print(f"[AUTO_FIRE_FAST] 🔥 第{i+1}发开火 (备用方案-左键)")
                    except Exception as e2:
                        print(f"[AUTO_FIRE_FAST] ❌ 第{i+1}发开火失败: {e2}")
            else:
                # 使用Win32 API
                try:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    # 减少按下-抬起间隔为1ms，降低对主循环的影响
                    time.sleep(0.001)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    if DEBUG_LOG:
                        print(f"[AUTO_FIRE_FAST] 🔥 第{i+1}发开火 (Win32)")
                except:
                    print(f"[AUTO_FIRE_FAST] ❌ 第{i+1}发开火失败")
            
            # 连发间隔
            if i < autoFireShots - 1:
                time.sleep(autoFireDelay / 1000.0)
        
        if DEBUG_LOG:
            print(f"[AUTO_FIRE_FAST] ✅ 快速开火完成，共{autoFireShots}发 (使用{driver_type})")
        
        # 更新冷却时间
        trigger_system.last_fire_time = time.time()
        if DEBUG_LOG:
            print(f"[AUTO_FIRE_FAST] ⏱️ 冷却时间已启动，持续{trigger_system.cooldown_duration}秒")
        
    except Exception as e:
        print(f"[AUTO_FIRE_FAST] 快速开火函数异常: {e}")

def check_realtime_fire_opportunity(targets, crosshair_x, crosshair_y):
    """
    实时检测鼠标与任意头部的重合，用于移动过程中的开火检测
    
    Args:
        targets: 当前帧检测到的所有目标
        crosshair_x: 当前准星在320坐标系中的X位置
        crosshair_y: 当前准星在320坐标系中的Y位置
    
    Returns:
        bool: 是否检测到开火机会并成功开火
    """
    # 获取扳机系统实例
    trigger_system = get_trigger_system()
    
    print(f"[FIRE_DEBUG] 🔍 开火检测开始 - 扳机启用: {trigger_system.enabled}, 目标数量: {len(targets)}")
    
    if not trigger_system.enabled or len(targets) == 0:
        print(f"[FIRE_DEBUG] ❌ 开火检测跳过 - 扳机启用: {trigger_system.enabled}, 目标数量: {len(targets)}")
        return False
    
    print(f"[FIRE_DEBUG] 📍 准星位置: ({crosshair_x}, {crosshair_y}), 距离阈值: {trigger_system.angle_threshold}")
    
    # 遍历所有目标，检测是否有任何头部与准星重合
    for idx, target in targets.iterrows():
        # 获取目标的头部位置（假设头部在目标中心偏上）
        target_x = target['current_mid_x']
        target_y = target['current_mid_y']
        target_height = target['height']
        
        # 计算头部位置（在目标上方0.38处）
        head_x_320 = target_x
        head_y_320 = target_y - target_height * 0.38  # 使用固定0.38偏移
        
        # 计算准星与头部的距离
        distance = ((head_x_320 - crosshair_x)**2 + (head_y_320 - crosshair_y)**2)**0.5
        
        print(f"[FIRE_DEBUG] 🎯 目标{idx}: 中心({target_x:.1f}, {target_y:.1f}), 高度{target_height:.1f}, 头部({head_x_320:.1f}, {head_y_320:.1f}), 距离{distance:.1f}")
        
        # 如果距离在开火阈值内
        if distance <= trigger_system.angle_threshold:
            # 记录当前重合事件的时间戳
            now = time.time()
            alignment_events.append(now)
            
            # 清理时间窗口之外的旧事件
            alignment_events[:] = [event for event in alignment_events if now - event <= FIRE_EVENT_WINDOW]
            
            # 打印当前事件数量
            print(f"[REALTIME_FIRE] ⏳ 当前重合事件: {len(alignment_events)} / {FIRE_EVENT_THRESHOLD} (窗口: {FIRE_EVENT_WINDOW}s)")

            # 检查在时间窗口内是否达到了开火阈值
            if len(alignment_events) >= FIRE_EVENT_THRESHOLD:
                print(f"[REALTIME_FIRE] 🔥 达到开火阈值！准备开火！")
                
                # 冷却 gating：只有非冷却期才开火
                if not trigger_system.is_on_cooldown():
                    trigger_system.fire_shots()  # 不需要参数
                    print(f"[REALTIME_FIRE] ✅ 开火成功！")
                else:
                    remaining = max(0.0, trigger_system.cooldown_duration - (now - trigger_system.last_fire_time))
                    if DEBUG_LOG:
                        print(f"[REALTIME_FIRE] ⏱️ 冷却中，跳过开火，剩余{remaining:.2f}秒")
                
                # 仅在实际开火后更新最后开火时间
                if not trigger_system.is_on_cooldown():
                    trigger_system.last_fire_time = now
                
                # 清空事件列表，防止连续开火
                alignment_events.clear()
                if DEBUG_LOG:
                    print(f"[REALTIME_FIRE] 🔄 事件列表已清空，重新开始计数。")
                
                return True # 表示成功开火
    
    return False


def fire_callback_adapter():
    """
    开火回调适配器函数 - 用于非阻塞移动系统
    使用全局变量获取当前目标和准星位置
    """
    global current_targets, current_crosshair_x, current_crosshair_y
    
    print(f"[FIRE_CALLBACK] 🔍 开火回调被调用")
    print(f"[FIRE_CALLBACK] - 目标数据: {len(current_targets) if current_targets is not None else 0} 个目标")
    print(f"[FIRE_CALLBACK] - 准星位置: ({current_crosshair_x}, {current_crosshair_y})")
    
    if current_targets is not None and len(current_targets) > 0:
        result = check_realtime_fire_opportunity(current_targets, current_crosshair_x, current_crosshair_y)
        print(f"[FIRE_CALLBACK] - 开火检测结果: {result}")
        return result
    else:
        print(f"[FIRE_CALLBACK] - 无目标数据，跳过开火检测")
        return False


# ==================== 主函数 ====================

def main():
    """主函数 - 纯320坐标系ONNX自瞄"""
    print("=== AI-Aimbot ONNX 纯320坐标系版本启动 ===")
    print(f"- 截图尺寸: {screenShotWidth}x{screenShotHeight}")
    print("- 无缩放处理，直接使用320坐标系")
    print("- 集成硬件驱动移动鼠标")
    
    # 游戏选择和摄像头初始化
    result = gameSelection.gameSelection()
    if result is None:
        print("[ERROR] 游戏选择失败，退出程序")
        return
    
    # 修复返回值解包问题 - 只解包前5个值
    camera, cWidth, cHeight, camera_type, videoGameWindow = result[:5]
    region = result[5] if len(result) > 5 else None
    print(f"[INFO] 截图区域: {screenShotWidth}x{screenShotHeight}")
    print(f"[INFO] 屏幕中心: ({cWidth}, {cHeight})")
    print(f"[INFO] 使用摄像头类型: {camera_type}")
    print(f"[INFO] 游戏窗口: {videoGameWindow.title}")
    
    # 垃圾回收计数器
    count = 0
    sTime = time.time()

    # ONNX 提供者选择
    onnxProvider = ""
    if onnxChoice == 1:
        onnxProvider = "CPUExecutionProvider"
    elif onnxChoice == 2:
        onnxProvider = "DmlExecutionProvider"
    elif onnxChoice == 3:
        import cupy as cp
        onnxProvider = "CUDAExecutionProvider"

    # ONNX 会话初始化
    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    ort_sess = ort.InferenceSession('yolov5s320Half.onnx', sess_options=so, providers=[onnxProvider])

    # 设置非阻塞平滑移动系统的开火检测回调
    if non_blocking_smooth_movement_system:
        trigger_system = get_trigger_system()
        non_blocking_smooth_movement_system.set_fire_check_callback(fire_callback_adapter)
        print("[INFO] ✅ 非阻塞平滑移动系统开火回调已设置（使用适配器函数）")

    # 绘制颜色
    COLORS = np.random.uniform(0, 255, size=(1500, 3))

    # 目标跟踪变量
    last_mid_coord = None

    print("[INFO] 开始主循环，按 Q 键退出")
    
    # ==================== 主循环 ====================
    while win32api.GetAsyncKeyState(ord(aaQuitKey)) == 0:
        
        # 获取帧（直接320x320，无需任何缩放）
        npImg = np.array(camera.get_latest_frame())
        
        # 确保图像是320x320（如果不是则调整）
        if npImg.shape[:2] != (320, 320):
            npImg = cv2.resize(npImg, (320, 320))
        
        # 应用遮罩（如果启用）
        from config import maskSide
        if useMask:
            maskSide = maskSide.lower()
            if maskSide == "right":
                npImg[-maskHeight:, -maskWidth:, :] = 0
            elif maskSide == "left":
                npImg[-maskHeight:, :maskWidth, :] = 0
            else:
                raise Exception('ERROR: Invalid maskSide! Please use "left" or "right"')

        # 图像预处理（统一为轻量级 numpy 管线，避免跨框架搬运）
        im = np.array([npImg], dtype=np.float16)
        if im.shape[3] == 4:
            im = im[:, :, :, :3]  # 移除alpha通道
        im /= 255.0
        im = np.moveaxis(im, 3, 1)

        # ONNX 推理（提供者自行处理设备传输）
        outputs = ort_sess.run(None, {'images': im})

        # 后处理
        im = torch.from_numpy(outputs[0]).to('cpu').float()
        pred = non_max_suppression(im, confidence, confidence, 0, False, max_det=10)

        # 目标提取
        targets = []
        for i, det in enumerate(pred):
            if len(det):
                for *xyxy, conf, cls in reversed(det):
                    # 直接使用320像素坐标系，无需归一化/回放
                    coords = xyxy2xywh(torch.tensor(xyxy).view(1, 4)).view(-1).tolist()
                    targets.append([coords[0], coords[1], coords[2], coords[3], float(conf)])

        # 转换为DataFrame
        targets = pd.DataFrame(targets, columns=['current_mid_x', 'current_mid_y', 'width', "height", "confidence"])
        
        # 坐标已为像素值，无需额外转换

        # 更新全局变量供开火回调使用
        global current_targets, current_crosshair_x, current_crosshair_y
        current_targets = targets
        current_crosshair_x = 160  # 准星X位置（320坐标系中心）
        current_crosshair_y = 160  # 准星Y位置（320坐标系中心）

        # 屏幕中心（320坐标系）
        center_screen = [cWidth, cHeight]  # 160, 160

        # ==================== 目标选择逻辑 ====================
        selected_target = None
        if len(targets) > 0:
            if centerOfScreen:
                # 基于距离选择最近目标（避免整表排序，直接取最小索引）
                targets["dist_from_center"] = np.sqrt(
                    (targets.current_mid_x - center_screen[0])**2 + 
                    (targets.current_mid_y - center_screen[1])**2
                )
                idx = targets["dist_from_center"].idxmin()
                selected_target = targets.loc[idx]
                debug_log(
                    f"[TARGET_SELECT] 选择距离最近的目标，距离: {selected_target['dist_from_center']:.1f}",
                    tag="target_select",
                    throttle_ms=1000,
                )
            else:
                # 基于置信度选择最高置信度目标（避免整表排序）
                idx = targets["confidence"].idxmax()
                selected_target = targets.loc[idx]
                debug_log(
                    f"[TARGET_SELECT] 选择置信度最高的目标，置信度: {selected_target['confidence']:.2f}",
                    tag="target_select",
                    throttle_ms=1000,
                )
            xMid = selected_target.current_mid_x
            yMid = selected_target.current_mid_y
            box_height = selected_target.height

            # 计算头部偏移（320坐标系）
            if headshot_mode:
                headshot_offset = box_height * 0.38
            else:
                headshot_offset = box_height * 0.2

            # 计算鼠标移动量（320坐标系）
            head_x = xMid
            head_y = yMid - headshot_offset
            mouseMove = [head_x - cWidth, head_y - cHeight]

            debug_log(
                f"[COORDINATE] 目标中心: ({xMid:.1f}, {yMid:.1f}), 头部: ({head_x:.1f}, {head_y:.1f}), 移动: ({mouseMove[0]:.1f}, {mouseMove[1]:.1f})",
                tag="coords",
                throttle_ms=500,
            )
            
            # 更新跟踪坐标
            last_mid_coord = [xMid, yMid]
        else:
            last_mid_coord = None
            debug_log("[TARGET_SELECT] 未检测到目标", tag="target_select_none", throttle_ms=1000)
            # 重置扳机系统的精确对齐状态
            trigger_system = get_trigger_system()
            trigger_system.reset_alignment_status()

        # ==================== 按键驱动逻辑 ====================
        
        # 检测按键状态
        caps_lock_pressed = win32api.GetKeyState(0x14) & 0x0001  # Caps Lock - 纯扳机键
        right_mouse_down = win32api.GetKeyState(0x02) & 0x8000  # 鼠标右键 - 瞄准+扳机
        
        # 初始化默认值，防止 UnboundLocalError
        normalized_head_x, normalized_head_y = 0.5, 0.5  # 默认为屏幕中心
        normalized_detection_center = (0.5, 0.5)
        
        # 按键驱动模式处理
        if selected_target is not None:
            head_x = selected_target.current_mid_x
            head_y = selected_target.current_mid_y - (selected_target.height * (0.38 if headshot_mode else 0.2))
            crosshair_x, crosshair_y = 160, 180  # 准星位置设置为 (170, 170)
            
            # 计算鼠标移动量（用于所有模式）
            mouseMove = [head_x - crosshair_x, head_y - crosshair_y]
            
            # 计算准星到目标头部的距离
            distance_to_target = ((head_x - crosshair_x)**2 + (head_y - crosshair_y)**2)**0.5
            
            # 1像素阈值检测 - 允许更精细的移动调整（降低阈值以改善近距离瞄准）
            movement_threshold = 1.0
            should_move = distance_to_target > movement_threshold

            # 将320像素坐标转换为归一化坐标（0-1范围），供所有模式使用
            normalized_head_x = head_x / 320.0
            normalized_head_y = head_y / 320.0
            
            # Caps Lock 纯扳机模式（只开火，不瞄准）
            if caps_lock_pressed and autoFire:
                print("[KEY_DRIVER] 🔒 Caps Lock 纯扳机模式激活（仅扳机，不瞄准）")
                
                # 获取扳机系统实例
                trigger_system = get_trigger_system()
                
                # 检查对齐状态并开火
                normalized_detection_center = (0.5, 0.5)  # 320像素坐标系中心(160,160)对应归一化坐标(0.5,0.5)
                
                # 🔍 详细调试信息
                print(f"[DEBUG] 目标头部坐标: ({head_x:.1f}, {head_y:.1f}) -> 归一化: ({normalized_head_x:.4f}, {normalized_head_y:.4f})")
                print(f"[DEBUG] 准星中心: (160, 160) -> 归一化: (0.5000, 0.5000)")
                print(f"[DEBUG] 扳机系统阈值: 角度={trigger_system.precise_angle_threshold:.3f}°, 像素={trigger_system.precise_alignment_threshold}px")
                
                # 优先使用精确扳机检测（针对选中目标）
                fired = trigger_system.check_and_fire(
                    normalized_head_x, normalized_head_y, normalized_detection_center, 0.38,
                    game_fov=103.0, detection_size=320, 
                    game_width=2560, game_height=1600
                )
                
                if fired:
                    print(f"[CAPS_TRIGGER] 🔥 精确扳机开火成功！")
                else:
                    # 如果精确扳机未开火，使用实时扫描检测所有目标
                    realtime_fire_success = check_realtime_fire_opportunity(
                        targets, crosshair_x, crosshair_y
                    )
                    if realtime_fire_success:
                        print("[CAPS_TRIGGER] 🔥 实时扫描开火成功！")
                    else:
                        print(f"[CAPS_TRIGGER] ❌ 未开火 - 目标未对齐或在冷却期")
                        print(f"[CAPS_TRIGGER] 阈值要求: 角度≤{trigger_system.precise_angle_threshold:.3f}°, 像素≤{trigger_system.precise_alignment_threshold}px")
            
            # 右键瞄准+扳机模式
            elif right_mouse_down:
                print("[KEY_DRIVER] 🖱️ 右键瞄准+扳机模式激活")
                
                # 获取扳机系统实例
                trigger_system = get_trigger_system()
                
                # 优先进行扳机检测 (调用新的实时开火检测函数)
                fire_result = check_realtime_fire_opportunity(targets, crosshair_x, crosshair_y)
                
                if fire_result:
                    print(f"[RIGHT_TRIGGER] 🔥 扳机开火成功")
                else:
                    # 如果没有开火，执行平滑鼠标移动（允许微小移动以改善精度）
                    if should_move and (abs(mouseMove[0]) > 0.5 or abs(mouseMove[1]) > 0.5):  # 降低阈值允许更精细移动
                        # 计算自适应放大器并应用
                        adaptive_amp = compute_adaptive_amp(distance_to_target)
                        move_x = int(mouseMove[0] * adaptive_amp)
                        move_y = int(mouseMove[1] * adaptive_amp)
                        
                        # 应用最大移动像素限制 - 实现多步瞄准
                        move_distance = (move_x**2 + move_y**2)**0.5
                        if move_distance > MAX_SINGLE_MOVE_PIXELS:
                            # 按比例缩放到最大限制
                            scale_factor = MAX_SINGLE_MOVE_PIXELS / move_distance
                            move_x = int(move_x * scale_factor)
                            move_y = int(move_y * scale_factor)
                            print(f"[MOVE_LIMIT] 🎯 移动距离限制: {move_distance:.1f}px -> {MAX_SINGLE_MOVE_PIXELS}px (缩放: {scale_factor:.2f})")
                        
                        # 使用配置化的平滑移动算法
                        success = move_mouse(move_x, move_y, 
                                           use_smooth=USE_SMOOTH_MOVEMENT, 
                                           use_non_blocking=USE_NON_BLOCKING_MOVEMENT)
                        
                        if success:
                            movement_type = "平滑" if USE_SMOOTH_MOVEMENT else "机械"
                            blocking_type = "非阻塞" if USE_NON_BLOCKING_MOVEMENT else "阻塞"
                            debug_log(
                                f"[RIGHT_AIM] 🎯 {movement_type}{blocking_type}瞄准移动: ({move_x:.1f}, {move_y:.1f}) 距离:{distance_to_target:.1f}px 放大器:{adaptive_amp:.2f}",
                                tag="RIGHT_AIM", throttle_ms=100
                            )
                            
                            # 🎯 目标范围内停止增强功能 - 非阻塞版本
                            if non_blocking_smooth_movement_system:
                                # 显示距离检查信息（调试）
                                debug_log(
                                    f"[TARGET_RANGE] 📏 距离检查: {distance_to_target:.1f}px (阈值: 15px)",
                                    tag="TARGET_RANGE", throttle_ms=100
                                )
                                
                                # 检查是否应该阻止移动
                                if non_blocking_smooth_movement_system.is_movement_blocked():
                                    stop_status = non_blocking_smooth_movement_system.get_stop_status()
                                    remaining = stop_status['remaining_stop_time']
                                    debug_log(
                                        f"[TARGET_RANGE] ⏸️ 停止期间，剩余{remaining:.2f}s - 跳过移动",
                                        tag="TARGET_RANGE", throttle_ms=200
                                    )
                                    continue  # 跳过移动，但不延误主函数
                                
                                # 检查是否需要触发停止（15像素范围内）
                                if distance_to_target <= 15:
                                    debug_log(
                                        f"[TARGET_RANGE] 🎯 进入头部范围({distance_to_target:.1f}px≤15px)，尝试触发停止",
                                        tag="TARGET_RANGE", throttle_ms=200
                                    )
                                    # 传递目标相对于准星的坐标，而不是移动偏移量
                                    target_relative_x = head_x - crosshair_x
                                    target_relative_y = head_y - crosshair_y
                                    debug_log(
                                        f"[TARGET_RANGE] 📍 目标相对坐标: ({target_relative_x:.1f}, {target_relative_y:.1f})",
                                        tag="TARGET_RANGE", throttle_ms=200
                                    )
                                    stop_triggered = non_blocking_smooth_movement_system.enhanced_target_stop(
                                        target_relative_x, target_relative_y, False
                                    )
                                    if stop_triggered:
                                        debug_log(
                                            f"[TARGET_RANGE] ✅ 成功触发头部停止（停止时间已取消）",
                                            tag="TARGET_RANGE", throttle_ms=200
                                        )
                                        continue  # 触发停止后跳过本次移动
                                    else:
                                        debug_log(
                                            f"[TARGET_RANGE] ❌ 停止触发失败",
                                            tag="TARGET_RANGE", throttle_ms=200
                                        )
                                else:
                                    debug_log(
                                        f"[TARGET_RANGE] ➡️ 距离({distance_to_target:.1f}px)超出15px范围，继续移动",
                                        tag="TARGET_RANGE", throttle_ms=200
                                    )
                            
                            # 移动过程中进行重合扳机检测
                            if len(targets) > 0:
                                realtime_fire_success = check_realtime_fire_opportunity(
                                    targets, crosshair_x, crosshair_y
                                )
                                if realtime_fire_success:
                                    debug_log(
                                        "[OVERLAP_TRIGGER] 🔥 移动过程中重合扳机开火成功",
                                        tag="OVERLAP_TRIGGER", throttle_ms=300
                                    )
                            
                            # 移动后进行补充开火检测（仅阻塞平滑时短暂等待）
                            if USE_SMOOTH_MOVEMENT and not USE_NON_BLOCKING_MOVEMENT:
                                time.sleep(0.001)
                            supplementary_fire = trigger_system.check_and_fire(
                                normalized_head_x, normalized_head_y, normalized_detection_center, 0.38,
                                game_fov=103.0, detection_size=320, 
                                game_width=2560, game_height=1600
                            )
                            if supplementary_fire:
                                debug_log(
                                    "[RIGHT_TRIGGER] 🔥 移动后补充开火",
                                    tag="RIGHT_TRIGGER", throttle_ms=300
                                )
                        else:
                            movement_type = "平滑" if USE_SMOOTH_MOVEMENT else "机械"
                            debug_log(
                                f"[RIGHT_AIM] ❌ {movement_type}瞄准移动失败",
                                tag="RIGHT_AIM", throttle_ms=200
                            )
                    elif not should_move:
                        debug_log(
                            f"[RIGHT_AIM] 🚫 距离过近，跳过移动: 距离{distance_to_target:.1f}px < 阈值{movement_threshold}px",
                            tag="RIGHT_AIM", throttle_ms=200
                        )
                    else:
                        debug_log(
                            "[RIGHT_AIM] 📍 目标已对齐，无需移动",
                            tag="RIGHT_AIM", throttle_ms=300
                        )
        else:
            # 无目标时的按键状态显示
            if caps_lock_pressed:
                debug_log("[KEY_DRIVER] 🔒 Caps Lock 纯扳机模式等待目标...", tag="KEY_DRIVER", throttle_ms=500)
            elif right_mouse_down:
                debug_log("[KEY_DRIVER] 🖱️ 右键瞄准模式等待目标...", tag="KEY_DRIVER", throttle_ms=500)

        # ==================== 可视化显示 ====================
        if visuals:
            # 绘制检测框
            for i in range(len(targets)):
                halfW = round(targets.iloc[i]["width"] / 2)
                halfH = round(targets.iloc[i]["height"] / 2)
                midX = int(targets.iloc[i]['current_mid_x'])
                midY = int(targets.iloc[i]['current_mid_y'])
                
                startX, startY = midX - halfW, midY - halfH
                endX, endY = midX + halfW, midY + halfH

                # 绘制边界框
                label = f"Human: {targets.iloc[i]['confidence'] * 100:.1f}%"
                cv2.rectangle(npImg, (startX, startY), (endX, endY), COLORS[0], 2)
                
                # 绘制标签
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(npImg, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[0], 2)
                
                # 如果是选中目标，绘制头部位置
                if selected_target is not None and i == 0:
                    head_x = int(midX)
                    head_y = int(midY - (targets.iloc[i]["height"] * (0.38 if headshot_mode else 0.2)))
                    cv2.circle(npImg, (head_x, head_y), 5, (0, 255, 0), -1)  # 绿色圆点标记头部
            
            # 绘制准星
            cv2.line(npImg, (cWidth-10, cHeight), (cWidth+10, cHeight), (255, 255, 255), 2)
            cv2.line(npImg, (cWidth, cHeight-10), (cWidth, cHeight+10), (255, 255, 255), 2)
            
            # 显示按键驱动状态
            caps_lock_pressed = win32api.GetKeyState(0x14) & 0x0001  # Caps Lock - 纯扳机键
            right_mouse_down = win32api.GetAsyncKeyState(0x02) & 0x8000  # 鼠标右键 - 瞄准+扳机（修复检测方法）
            
            if caps_lock_pressed and autoFire:
                cv2.putText(npImg, "CAPS TRIGGER", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)  # 黄色
            elif right_mouse_down:
                cv2.putText(npImg, "RIGHT AIM+TRIGGER", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)  # 绿色
                # 显示重合扳机状态
                if len(targets) > 0:
                    cv2.putText(npImg, "OVERLAP DETECTION", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)  # 青色
            else:
                cv2.putText(npImg, "STANDBY", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (128, 128, 128), 2)  # 灰色
            
            # 显示坐标系信息
            cv2.putText(npImg, f"Pure {screenShotWidth}x{screenShotHeight}", (10, npImg.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # ==================== 性能监控 ====================
        count += 1
        if (time.time() - sTime) > 1:
            if cpsDisplay:
                debug_log(f"CPS: {count}", tag="cps", throttle_ms=1000)
            count = 0
            sTime = time.time()
            
            # 可选的垃圾回收
            # gc.collect(generation=0)

        # 轻量FPS计数（只在 DEBUG_LOG 为 True 时输出，每秒一次）
        fps_tick("MAIN")

        # 显示实时画面
        if visuals:
            cv2.imshow(f'AI-Aimbot Pure {screenShotWidth}x{screenShotHeight}', npImg)
            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                break

    # 清理资源
    camera.stop()
    if arduino_driver:
        arduino_driver.close()
    cv2.destroyAllWindows()
    print("[INFO] AI-Aimbot 已退出")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exception(e)
        print("ERROR: " + str(e))
        print("Ask @Wonder for help in our Discord in the #ai-aimbot channel ONLY: https://discord.gg/rootkitorg")
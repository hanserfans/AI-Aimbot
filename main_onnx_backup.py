import onnxruntime as ort
import numpy as np
import gc
import numpy as np
import cv2
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
from config import aaMovementAmp, useMask, maskHeight, maskWidth, aaQuitKey, confidence, headshot_mode, cpsDisplay, visuals, onnxChoice, centerOfScreen, autoFire, autoFireShots, autoFireDelay, autoFireKey, screenShotWidth, screenShotHeight
import gameSelection
from precision_aiming_optimizer import optimize_aiming_parameters, get_precision_report, save_aiming_data, load_aiming_data
from dynamic_tracking_system import get_aiming_system
from auto_trigger_system import get_trigger_system
from performance_optimizer import get_performance_optimizer
from threshold_config import ThresholdConfig

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
                "game_fov": 103  # 默认FOV
            }
    except Exception as e:
        print(f"[ERROR] 加载配置失败: {str(e)}")
        # 返回默认配置
        return {
            "control_method": "arduino",  # 默认使用Arduino
            "confidence": 0.4,
            "movement_amp": 0.4,
            "headshot_mode": True,
            "game_fov": 103  # 默认FOV
        }

# 加载配置
GUI_CONFIG = load_gui_config()
GAME_FOV = GUI_CONFIG.get("game_fov", 103)  # 获取用户配置的FOV，默认103

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

# 2. 尝试导入G-Hub驱动（如果Arduino不可用）
if not ARDUINO_AVAILABLE:
    try:
        from mouse_driver.MouseMove import ghub_move, ghub_click
        print("[SUCCESS] G-Hub 驱动导入成功")
        GHUB_AVAILABLE = True
    except ImportError as e:
        print(f"[WARNING] G-Hub 驱动导入失败: {e}")
        print("[INFO] 将使用 Win32 API 作为备用方案")
        GHUB_AVAILABLE = False

# 打印当前使用的鼠标控制方法
if ARDUINO_AVAILABLE:
    print("[INFO] 当前鼠标控制方法: Arduino 硬件驱动")
elif GHUB_AVAILABLE:
    print("[INFO] 当前鼠标控制方法: G-Hub 驱动")
else:
    print("[INFO] 当前鼠标控制方法: Win32 API")

def move_mouse(x, y):
    """统一的鼠标移动函数，支持三层备选"""
    try:
        if ARDUINO_AVAILABLE and arduino_driver:
            # 优先使用Arduino驱动
            success = arduino_driver.move_mouse(x, y)
            if success:
                print(f"[DEBUG] Arduino移动: ({x}, {y})")
                return True
            else:
                print("[WARNING] Arduino移动失败，切换到G-Hub")
        
        if GHUB_AVAILABLE:
            # 备选方案1: G-Hub驱动
            ghub_move(int(x), int(y))
            print(f"[DEBUG] G-Hub移动: ({x}, {y})")
            return True
        else:
            # 备选方案2: Win32 API
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

def click_mouse(button='left'):
    """统一的鼠标点击函数，支持三层备选"""
    try:
        if ARDUINO_AVAILABLE and arduino_driver:
            # 优先使用Arduino驱动
            success = arduino_driver.click_mouse(button)
            if success:
                print(f"[DEBUG] Arduino点击: {button}")
                return True
            else:
                print("[WARNING] Arduino点击失败，切换到G-Hub")
        
        if GHUB_AVAILABLE:
            # 备选方案1: G-Hub驱动
            ghub_click()
            print(f"[DEBUG] G-Hub点击: {button}")
            return True
        else:
            # 备选方案2: Win32 API
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
    """
    if not autoFire:
        return
    
    # 获取自动扳机系统实例来检查冷却时间
    trigger_system = get_trigger_system()
    
    # 检查是否在冷却时间内
    if trigger_system.is_on_cooldown():
        print(f"[AUTO_FIRE] ⏱️ 冷却中，剩余时间: {trigger_system.cooldown_duration - (time.time() - trigger_system.last_fire_time):.1f}秒")
        return
    
    try:
        for i in range(autoFireShots):
            if autoFireKey == "left_click":
                # 使用统一的鼠标点击函数
                if click_mouse("left"):
                    print(f"[AUTO_FIRE] 🔥 第{i+1}发开火 (左键)")
                else:
                    print(f"[AUTO_FIRE] ❌ 第{i+1}发开火失败")
            elif autoFireKey == "right_click":
                # 使用统一的鼠标点击函数
                if click_mouse("right"):
                    print(f"[AUTO_FIRE] 🔥 第{i+1}发开火 (右键)")
                else:
                    print(f"[AUTO_FIRE] ❌ 第{i+1}发开火失败")
            elif autoFireKey == "space":
                # 键盘按键仍使用Win32 API
                win32api.keybd_event(0x20, 0, 0, 0)  # 按下空格
                time.sleep(0.001)  # 高性能模式：1ms延迟
                win32api.keybd_event(0x20, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放空格
                print(f"[AUTO_FIRE] 🔥 第{i+1}发开火 (空格)")
            elif autoFireKey == "f":
                # 键盘按键仍使用Win32 API
                win32api.keybd_event(0x46, 0, 0, 0)  # 按下F键
                time.sleep(0.001)  # 高性能模式：1ms延迟
                win32api.keybd_event(0x46, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放F键
                print(f"[AUTO_FIRE] 🔥 第{i+1}发开火 (F键)")
            elif autoFireKey == "r":
                # 键盘按键仍使用Win32 API
                win32api.keybd_event(0x52, 0, 0, 0)  # 按下R键
                time.sleep(0.001)  # 高性能模式：1ms延迟
                win32api.keybd_event(0x52, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放R键
                print(f"[AUTO_FIRE] 🔥 第{i+1}发开火 (R键)")
            
            # 如果不是最后一发，等待指定延迟
            if i < autoFireShots - 1:
                time.sleep(autoFireDelay / 1000.0)  # 转换毫秒为秒
                
        # 确定当前使用的驱动类型
        driver_type = "Arduino" if ARDUINO_AVAILABLE else ("G-Hub" if GHUB_AVAILABLE else "Win32 API")
        print(f"[AUTO_FIRE] ✅ 自动开火完成，共{autoFireShots}发 (使用{driver_type})")
        
        # 更新冷却时间
        trigger_system.last_fire_time = time.time()
        print(f"[AUTO_FIRE] ⏱️ 冷却时间已启动，持续{trigger_system.cooldown_duration}秒")
        
    except Exception as e:
        print(f"[ERROR] 自动开火失败: {e}")

def main():
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
    print("   • Caps Lock - 仅激活瞄准功能（按住瞄准，不开火）")
    print("   • 鼠标侧键2 - 切换扳机功能开关（可选）")
    print("   • R键 - 显示扳机系统状态")
    print("   • M键 - 切换瞄准模式")
    print("   • P键 - 显示精度报告")
    print("="*60 + "\n")
    
    # External Function for running the game selection menu (gameSelection.py)
    result = gameSelection.gameSelection()
    if result is None:
        print("[ERROR] 游戏选择失败，程序退出")
        return
    
    camera, cWidth, cHeight, camera_type, videoGameWindow = result
    print("[INFO] 使用屏幕捕获方案: {}".format(camera_type))

    # Used for forcing garbage collection
    count = 0
    sTime = time.time()
    
    # 初始化性能优化器
    perf_optimizer = get_performance_optimizer()
    print("[INFO] 🚀 性能优化器已初始化")
    
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
    print("[INFO] 🎯 扳机系统已就绪 - 按鼠标侧键2启用/禁用")
    
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
    
    # 移动控制状态管理
    movement_paused = False
    
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

    # Choosing the correct ONNX Provider based on config.py
    onnxProvider = ""
    if onnxChoice == 1:
        onnxProvider = "CPUExecutionProvider"
    elif onnxChoice == 2:
        onnxProvider = "DmlExecutionProvider"
    elif onnxChoice == 3:
        import cupy as cp
        onnxProvider = "CUDAExecutionProvider"

    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    ort_sess = ort.InferenceSession('yolov5s320Half.onnx', sess_options=so, providers=[
                                    onnxProvider])

    # Used for colors drawn on bounding boxes
    COLORS = np.random.uniform(0, 255, size=(1500, 3))

    # 系统就绪提示
    print("\n🚀 系统已就绪，开始运行...")
    print("💡 提示: 按鼠标右键激活瞄准+扳机，按Caps Lock仅瞄准，按 R 键查看状态")
    print("⚠️  注意: 按 Q 键退出程序\n")
    
    # Main loop Quit if Q is pressed
    last_mid_coord = None
    last_report_time = time.time()
    last_mode_switch_time = time.time()
    
    while win32api.GetAsyncKeyState(ord(aaQuitKey)) == 0:
        # 开始帧计时
        frame_start_time = perf_optimizer.start_frame()
        
        # 检查是否需要跳帧以维持目标FPS
        if perf_optimizer.should_skip_frame():
            time.sleep(0.001)  # 短暂延迟
            continue
        
        # 检测P键显示精度报告和性能报告
        if win32api.GetAsyncKeyState(ord('P')) & 0x8000:
            current_time = time.time()
            if current_time - last_report_time > 2:  # 防止重复触发
                print("\n" + "="*50)
                print(get_precision_report())
                print(perf_optimizer.get_performance_report())
                print("="*50 + "\n")
                last_report_time = current_time
        
        # M键功能已移除 - 现在只使用静态瞄准模式
        
        # 检测鼠标第二个侧键切换扳机系统
        if win32api.GetAsyncKeyState(0x06) & 0x8000:  # 0x06 是鼠标第二个侧键的虚拟键码
            current_time = time.time()
            if current_time - last_mode_switch_time > 1:  # 防止重复触发
                trigger_system.toggle_trigger()
                last_mode_switch_time = current_time
        
        # 检测R键显示扳机系统状态
        if win32api.GetAsyncKeyState(ord('R')) & 0x8000:
            current_time = time.time()
            if current_time - last_report_time > 2:  # 防止重复触发
                trigger_system.print_status()
                last_report_time = current_time
        
        # 检查跟踪超时
        aiming_system.check_timeout()

        # Getting Frame (different API for different camera types)
        if camera_type == "bettercam":
            npImg = torch.tensor(camera.get_latest_frame(, device='cuda').cpu().numpy())
        elif camera_type == "dxcam":
            frame = camera.get_latest_frame()
            if frame is None:
                continue
            npImg = torch.tensor(frame, device='cuda').cpu().numpy()
        else:
            print("[ERROR] 未知的相机类型: {}".format(camera_type))
            break

        from config import maskSide # "temporary" workaround for bad syntax
        if useMask:
            maskSide = maskSide.lower()
            if maskSide == "right":
                npImg[-maskHeight:, -maskWidth:, :] = 0
            elif maskSide == "left":
                npImg[-maskHeight:, :maskWidth, :] = 0
            else:
                raise Exception('ERROR: Invalid maskSide! Please use "left" or "right"')

        # Store original image for coordinate calculations
        original_img = npImg.copy()
        
        # Scale image to 320x320 for model input (if needed)
        if npImg.shape[0] != 320 or npImg.shape[1] != 320:
            npImg = cv2.resize(npImg, (320, 320), interpolation=cv2.INTER_LINEAR)
            print(f"[DEBUG] 图像缩放: {original_img.shape[:2]} -> {npImg.shape[:2]}")

        # If Nvidia, do this
        if onnxChoice == 3:
            # Normalizing Data
            im = torch.from_numpy(npImg).to('cuda')
            if im.shape[2] == 4:
                # If the image has an alpha channel, remove it
                im = im[:, :, :3,]

            im = torch.movedim(im, 2, 0)
            im = im.half()
            im /= 255
            if len(im.shape) == 3:
                im = im[None]
        # If AMD or CPU, do this
        else:
            # Normalizing Data
            im = torch.tensor([npImg], device='cuda').cpu().numpy()
            if im.shape[3] == 4:
                # If the image has an alpha channel, remove it
                im = im[:, :, :, :3]
            im = im / 255
            im = im.astype(np.half)
            im = np.moveaxis(im, 3, 1)

        # 开始检测计时
        detection_start = time.time()
        
        # If Nvidia, do this
        if onnxChoice == 3:
            outputs = ort_sess.run(None, {'images': cp.asnumpy(im)})
        # If AMD or CPU, do this
        else:
            outputs = ort_sess.run(None, {'images': torch.tensor(im, device='cuda').cpu().numpy()})

        im = torch.from_numpy(outputs[0]).to('cpu')

        # 使用动态置信度进行检测
        dynamic_confidence = perf_optimizer.get_optimized_confidence()
        pred = non_max_suppression(
            im, dynamic_confidence, dynamic_confidence, 0, False, max_det=10)

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
            
            # 显示第一个目标的原始归一化坐标
            first_target = targets.iloc[0]
            print(f"[DEBUG] 第一个目标原始归一化坐标: x={first_target['current_mid_x']:.3f}, y={first_target['current_mid_y']:.3f}")
            
            # 将归一化坐标转换为检测图像内的像素坐标
            targets['current_mid_x'] = targets['current_mid_x'] * npImg.shape[1]  # 宽度
            targets['current_mid_y'] = targets['current_mid_y'] * npImg.shape[0]  # 高度
            targets['height'] = targets['height'] * npImg.shape[0]  # 高度
            
            # 计算距离检测图像中心的距离（用于排序）
            targets['distance_from_center'] = ((targets['current_mid_x'] - detection_center[0])**2 + (targets['current_mid_y'] - detection_center[1])**2)**0.5
        
        # If there are people in the center bounding box
        if len(targets) > 0:
            if (centerOfScreen):
                # Sort the data frame by distance from center
                targets = targets.sort_values("distance_from_center")

            # Get the last persons mid coordinate if it exists
            if last_mid_coord:
                targets['last_mid_x'] = last_mid_coord[0]
                targets['last_mid_y'] = last_mid_coord[1]
                # Take distance between current person mid coordinate and last person mid coordinate
                targets['dist'] = np.linalg.norm(
                    targets.iloc[:, [0, 1]].values - targets.iloc[:, [4, 5]], axis=1)
                targets.sort_values(by="dist", ascending=False)

            # Take the first person that shows up in the dataframe (Recall that we sort based on Euclidean distance)
            # ===== 使用统一坐标系统 =====
            from coordinate_system import get_coordinate_system
            
            # 初始化坐标系统
            coord_system = get_coordinate_system(
                detection_size=DETECTION_SIZE,
                game_width=ACTUAL_GAME_WIDTH,
                game_height=ACTUAL_GAME_HEIGHT,
                game_fov=GAME_FOV
            )
            
            # 获取目标在检测图像中的原始坐标
            raw_x = targets.iloc[0].current_mid_x
            raw_y = targets.iloc[0].current_mid_y
            box_height = targets.iloc[0].height
            
            # 计算目标头部位置（统一计算）
            head_x, head_y = coord_system.calculate_target_head_position(
                raw_x, raw_y, box_height, headshot_mode
            )
            
            # 计算准星到目标的完整偏移信息
            offset_info = coord_system.calculate_crosshair_to_target_offset(head_x, head_y)
            
            # 计算目标距离系数（基于目标大小）
            normalized_box_height = box_height / DETECTION_SIZE
            reference_normalized_height = 80.0 / DETECTION_SIZE
            target_distance_factor = max(0.3, min(1.5, normalized_box_height / reference_normalized_height))
            
            # 使用直接像素移动方法 - 简单高效
            mouse_move_x, mouse_move_y = coord_system.calculate_mouse_movement_direct(
                offset_info['pixel']['x'],
                offset_info['pixel']['y'], 
                target_distance_factor,
                base_scaling=1.0  # 基础缩放系数，可根据游戏调整
            )
            
            mouseMove = [mouse_move_x, mouse_move_y]

            # 输出统一坐标系统的调试信息
            print(coord_system.debug_info(raw_x, raw_y, box_height, headshot_mode))
            print(f"[COORD] 距离系数: {target_distance_factor:.3f}")
            print(f"[COORD] 鼠标移动: ({mouse_move_x}, {mouse_move_y})")

            # 保存坐标用于跟踪
            last_mid_coord = [raw_x, raw_y]

        else:
            last_mid_coord = None

        # See what the bot sees
        if visuals:
            # Loops over every item identified and draws a bounding box
            for i in range(0, len(targets)):
                halfW = round(targets["width"][i] / 2)
                halfH = round(targets["height"][i] / 2)
                midX = targets['current_mid_x'][i]
                midY = targets['current_mid_y'][i]
                (startX, startY, endX, endY) = int(midX + halfW), int(midY +
                                                                      halfH), int(midX - halfW), int(midY - halfH)

                idx = 0
                # draw the bounding box and label on the frame
                label = "{}: {:.2f}%".format(
                    "Human", targets["confidence"][i] * 100)
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
            count = 0
            sTime = time.time()
            
            # 每秒保存一次瞄准数据
            save_aiming_data()

            # Uncomment if you keep running into memory issues
            # gc.collect(generation=0)

        # See visually what the Aimbot sees
        if visuals:
            # 在FPS游戏中，鼠标指针就是准星，始终位于屏幕中心
            # 鼠标坐标 = 准星坐标 = 截图区域中心坐标
            mouse_x = cWidth  # 160
            mouse_y = cHeight  # 160
            
            # 准星位置（与鼠标位置相同）
            crosshair_x = cWidth
            crosshair_y = cHeight
            
            # 在图像上显示位置信息
            info_y_offset = 30
            
            # 显示鼠标位置
            cv2.putText(npImg, f"Mouse: ({mouse_x}, {mouse_y})", 
                       (10, info_y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # 显示准星位置
            cv2.putText(npImg, f"Crosshair: ({crosshair_x}, {crosshair_y})", 
                       (10, info_y_offset + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # 如果有检测到目标，显示目标头部位置和偏差
            if len(targets) > 0:
                # 获取最近的目标（使用targets数据结构）
                closest_idx = 0  # 假设第一个目标是最近的
                
                # 使用统一坐标系统计算头部位置
                target_x = targets['current_mid_x'][closest_idx]
                target_y = targets['current_mid_y'][closest_idx]
                box_height = targets.iloc[closest_idx].height
                box_width = targets.iloc[closest_idx].width
                
                # 使用统一坐标系统计算头部位置
                head_x, head_y = coord_system.calculate_target_head_position(
                    target_x, target_y, box_height, headshot_mode
                )
                
                # 显示目标头部位置
                cv2.putText(npImg, f"Target Head: ({head_x:.1f}, {head_y:.1f})", 
                           (10, info_y_offset + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # 使用统一坐标系统计算偏移信息
                offset_info = coord_system.calculate_crosshair_to_target_offset(head_x, head_y)
                offset_x = offset_info['pixel']['x']
                offset_y = offset_info['pixel']['y']
                distance = int(offset_info['pixel']['distance'])
                
                # 检查激活键状态
                caps_lock_pressed = win32api.GetKeyState(0x14) < 0  # Caps Lock
                right_mouse_pressed = win32api.GetKeyState(0x02) < 0  # 鼠标右键
                
                # 使用动态跟踪系统进行瞄准（鼠标右键激活瞄准和扳机）
                if right_mouse_pressed:
                    print(f"[DEBUG] 🖱️ 鼠标右键已按下，激活瞄准系统")
                    
                    # 更新目标信息
                    target_info = {
                        'x': head_x,
                        'y': head_y,
                        'confidence': targets.iloc[closest_idx].confidence,
                        'box_width': box_width,
                        'box_height': box_height
                    }
                    
                    # 使用统一坐标系统计算屏幕坐标
                    screen_x, screen_y = coord_system.pixel_to_screen(head_x, head_y)
                    
                    # 使用动态跟踪系统计算移动（传递检测图像坐标和游戏参数）
                    movement = aiming_system.aim_at_target(
                        head_x, head_y, target_info['confidence'], 
                        cWidth, cHeight,
                        game_fov=GAME_FOV, detection_size=DETECTION_SIZE,
                        game_width=ACTUAL_GAME_WIDTH, game_height=ACTUAL_GAME_HEIGHT
                    )
                    
                    if movement is not None:
                        move_x, move_y = movement
                        print(f"[DEBUG] 动态跟踪移动: ({move_x:.1f}, {move_y:.1f}), 模式: {aiming_system.aiming_mode}")
                        
                        # 检查移动是否被暂停（开火时）
                        if not movement_paused:
                            # 执行鼠标移动
                            if move_mouse(move_x, move_y):
                                print("[DEBUG] 鼠标移动成功")
                            else:
                                print("[DEBUG] 鼠标移动失败")
                            
                            # 移动完成后打印相对于截屏框的位置信息
                            # 计算移动后的准星位置
                            new_crosshair_x = cWidth + int(move_x)
                            new_crosshair_y = cHeight + int(move_y)
                            
                            print(f"[POSITION] 移动完成后位置信息:")
                            print(f"[POSITION] - 目标在截屏框中的位置: ({head_x:.1f}, {head_y:.1f})")
                            print(f"[POSITION] - 移动前准星位置: ({cWidth:.1f}, {cHeight:.1f})")
                            print(f"[POSITION] - 鼠标移动量: ({int(move_x)}, {int(move_y)}) 像素")
                            print(f"[POSITION] - 移动后准星位置: ({new_crosshair_x:.1f}, {new_crosshair_y:.1f})")
                            print(f"[POSITION] - 截屏框尺寸: {DETECTION_SIZE}x{DETECTION_SIZE}")
                            print(f"[POSITION] - 移动后目标相对准星偏移: ({head_x - new_crosshair_x:.1f}, {head_y - new_crosshair_y:.1f}) 像素")
                            
                            # 计算目标在截屏框中的相对位置（百分比）
                            target_x_percent = (head_x / DETECTION_SIZE) * 100
                            target_y_percent = (head_y / DETECTION_SIZE) * 100
                            new_crosshair_x_percent = (new_crosshair_x / DETECTION_SIZE) * 100
                            new_crosshair_y_percent = (new_crosshair_y / DETECTION_SIZE) * 100
                            
                            print(f"[POSITION] - 目标在截屏框中的百分比位置: ({target_x_percent:.1f}%, {target_y_percent:.1f}%)")
                            print(f"[POSITION] - 移动后准星在截屏框中的百分比位置: ({new_crosshair_x_percent:.1f}%, {new_crosshair_y_percent:.1f}%)")
                            
                            # 右键激活扳机系统检查（移动完成后）
                            if trigger_system.enabled:
                                # 使用统一坐标系统计算归一化坐标
                                normalized_coords = coord_system.pixel_to_normalized(head_x, head_y)
                                detection_center = (0.5, 0.5)
                                
                                # 检测并执行扳机 - 传递游戏配置参数支持角度阈值
                                trigger_fired = trigger_system.check_and_fire(
                                    normalized_coords[0], normalized_coords[1], detection_center, 0,  # 头部偏移已在head_x, head_y中计算
                                    game_fov=GAME_FOV, detection_size=DETECTION_SIZE, 
                                    game_width=ACTUAL_GAME_WIDTH, game_height=ACTUAL_GAME_HEIGHT
                                )
                                
                                if trigger_fired:
                                    print("[TRIGGER] 🔥 右键扳机系统已触发！")
                        else:
                            print("[DEBUG] 鼠标移动已暂停（开火中）")
                        
                        time.sleep(0.001)  # 高性能模式：1ms延迟
                
                elif caps_lock_pressed:
                    # Caps Lock只激活瞄准，不开火
                    print(f"[DEBUG] Caps Lock已按下，仅激活瞄准功能（不开火）")
                    
                    # 更新目标信息
                    target_info = {
                        'x': head_x,
                        'y': head_y,
                        'confidence': targets.iloc[closest_idx].confidence,
                        'box_width': box_width,
                        'box_height': box_height
                    }
                    
                    # 使用统一坐标系统计算屏幕坐标
                    screen_x, screen_y = coord_system.pixel_to_screen(head_x, head_y)
                    
                    # 使用动态跟踪系统计算移动（传递检测图像坐标和游戏参数）
                    movement = aiming_system.aim_at_target(
                        head_x, head_y, target_info['confidence'], 
                        cWidth, cHeight,
                        game_fov=GAME_FOV, detection_size=DETECTION_SIZE,
                        game_width=ACTUAL_GAME_WIDTH, game_height=ACTUAL_GAME_HEIGHT
                    )
                    
                    if movement is not None:
                        move_x, move_y = movement
                        print(f"[DEBUG] 动态跟踪移动: ({move_x:.1f}, {move_y:.1f}), 模式: {aiming_system.aiming_mode}")
                        
                        # 检查移动是否被暂停（开火时）
                        if not movement_paused:
                            # 执行鼠标移动
                            if move_mouse(move_x, move_y):
                                print("[DEBUG] 鼠标移动成功")
                            else:
                                print("[DEBUG] 鼠标移动失败")
                            
                            # 移动完成后打印相对于截屏框的位置信息
                            # 计算移动后的准星位置
                            new_crosshair_x = cWidth + int(move_x)
                            new_crosshair_y = cHeight + int(move_y)
                            
                            print(f"[POSITION] 移动完成后位置信息:")
                            print(f"[POSITION] - 目标在截屏框中的位置: ({head_x:.1f}, {head_y:.1f})")
                            print(f"[POSITION] - 移动前准星位置: ({cWidth:.1f}, {cHeight:.1f})")
                            print(f"[POSITION] - 鼠标移动量: ({int(move_x)}, {int(move_y)}) 像素")
                            print(f"[POSITION] - 移动后准星位置: ({new_crosshair_x:.1f}, {new_crosshair_y:.1f})")
                            print(f"[POSITION] - 截屏框尺寸: {DETECTION_SIZE}x{DETECTION_SIZE}")
                            print(f"[POSITION] - 移动后目标相对准星偏移: ({head_x - new_crosshair_x:.1f}, {head_y - new_crosshair_y:.1f}) 像素")
                            
                            # 计算目标在截屏框中的相对位置（百分比）
                            target_x_percent = (head_x / DETECTION_SIZE) * 100
                            target_y_percent = (head_y / DETECTION_SIZE) * 100
                            new_crosshair_x_percent = (new_crosshair_x / DETECTION_SIZE) * 100
                            new_crosshair_y_percent = (new_crosshair_y / DETECTION_SIZE) * 100
                            
                            print(f"[POSITION] - 目标在截屏框中的百分比位置: ({target_x_percent:.1f}%, {target_y_percent:.1f}%)")
                            print(f"[POSITION] - 移动后准星在截屏框中的百分比位置: ({new_crosshair_x_percent:.1f}%, {new_crosshair_y_percent:.1f}%)")
                        else:
                            print("[DEBUG] 鼠标移动已暂停（开火中）")
                        
                        time.sleep(0.001)  # 高性能模式：1ms延迟
                    else:
                        print(f"[DEBUG] 目标已接近中心 ({distance:.1f}px)，但Caps Lock不开火")
                
                else:
                    print(f"[DEBUG] 目标偏离中心 {distance:.1f}px，无激活键按下")
                
                # 显示偏差信息
                cv2.putText(npImg, f"Offset: ({offset_x}, {offset_y}) Dist: {distance}px", 
                           (10, info_y_offset + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                
                # 在图像上画出目标头部位置的标记（相对于截图区域）
                target_img_x = int(targets['current_mid_x'][closest_idx])
                # 计算头部偏移量
                current_box_height = targets.iloc[closest_idx].height
                if headshot_mode:
                    current_headshot_offset = current_box_height * 0.38
                else:
                    current_headshot_offset = current_box_height * 0.2
                target_img_y = int(targets['current_mid_y'][closest_idx] - current_headshot_offset)  # 头部在目标中心上方，所以是减法
                cv2.circle(npImg, (target_img_x, target_img_y), 5, (0, 255, 0), -1)
                cv2.putText(npImg, "HEAD", (target_img_x + 10, target_img_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # 在图像中心画准星标记（点状）
            center_x = npImg.shape[1] // 2
            center_y = npImg.shape[0] // 2
            # 绘制点状准星：中心实心圆点 + 外围圆环
            cv2.circle(npImg, (center_x, center_y), 3, (255, 255, 0), -1)  # 实心圆点
            cv2.circle(npImg, (center_x, center_y), 8, (255, 255, 0), 1)   # 外围圆环
            cv2.putText(npImg, "DOT", (center_x , center_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # 显示检测到的目标数量
            cv2.putText(npImg, f"Targets: {len(targets)}", 
                       (10, info_y_offset + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # 显示当前瞄准模式
            cv2.putText(npImg, f"Aiming Mode: {aiming_system.aiming_mode}", 
                       (10, info_y_offset + 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # 显示扳机系统状态
            trigger_status = "ON" if trigger_system.enabled else "OFF"
            cv2.putText(npImg, f"Trigger: {trigger_status}", 
                       (10, info_y_offset + 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if trigger_system.enabled else (0, 0, 255), 2)
            
            # 显示性能信息
            fps = perf_optimizer.get_current_fps()
            cv2.putText(npImg, f"FPS: {fps:.1f}", 
                       (10, info_y_offset + 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            cv2.imshow('Live Feed', npImg)
            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                exit()
        
        # 记录检测时间和结果
        detection_time = time.time() - detection_start
        perf_optimizer.record_detection(detection_time, len(targets))
        
        # 结束帧计时
        perf_optimizer.end_frame()
    camera.stop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exception(e)
        print("ERROR: " + str(e))
        print("Ask @Wonder for help in our Discord in the #ai-aimbot channel ONLY: https://discord.gg/rootkitorg")
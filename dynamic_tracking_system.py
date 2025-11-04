"""
动态跟踪瞄准系统
解决瞄准过程中目标移动的时序问题
"""

import time
import threading
import numpy as np
import math
from typing import Tuple, Optional, List
import win32api
import win32con

class DynamicTracker:
    """简化的动态跟踪器 - 仅用于状态管理"""
    
    def __init__(self, movement_amp: float = 0.05):
        self.movement_amp = movement_amp
        self.is_tracking = False
        self.target_lock = threading.Lock()
        self.current_target = None
        self.crosshair_pos = (160, 160)  # 准星位置
        
        # 跟踪参数
        self.max_tracking_time = 2.0  # 最大跟踪时间（秒）
        self.min_movement_threshold = 1.5  # 最小移动阈值（像素）
        self.update_interval = 0.016  # 更新间隔（约60FPS）
        
    def start_tracking(self, target_x: float, target_y: float, confidence: float):
        """开始动态跟踪 - 简化版本"""
        with self.target_lock:
            self.current_target = {
                'x': target_x,
                'y': target_y,
                'confidence': confidence,
                'start_time': time.time()
            }
            
        self.is_tracking = True
        print(f"[TRACKER] 开始动态跟踪目标: ({target_x:.1f}, {target_y:.1f}), 置信度: {confidence:.2f}")
    
    def update_target(self, target_x: float, target_y: float, confidence: float):
        """更新目标位置 - 简化版本"""
        if not self.is_tracking:
            return
            
        with self.target_lock:
            if self.current_target:
                self.current_target.update({
                    'x': target_x,
                    'y': target_y,
                    'confidence': confidence
                })
        
        print(f"[TRACKER] 更新目标: ({target_x:.1f}, {target_y:.1f})")
    
    def stop_tracking(self):
        """停止跟踪"""
        self.is_tracking = False
        print("[TRACKER] 停止动态跟踪")

class AdaptiveAimingSystem:
    """自适应瞄准系统"""
    
    def __init__(self, movement_amp: float = 0.5):
        self.tracker = DynamicTracker(movement_amp)
        self.last_detection_time = 0
        self.detection_timeout = 0.5  # 检测超时时间
        
        # 瞄准模式状态
        self.aiming_mode = "adaptive"  # 瞄准模式: adaptive, static, dynamic
        
        # 角度阈值配置（与自动扳机系统保持一致）
        self.angle_threshold = 0.5  # 角度阈值（度）
        self.precise_angle_threshold = 0.3  # 精确角度阈值（度）
        self.use_angle_threshold = True  # 是否使用角度阈值
        
        # 优化的头部跟踪
        self.optimized_tracking = True  # 是否启用优化跟踪
        self.frame_processing = False   # 当前是否在处理帧
        self.pending_target = None      # 待处理的目标
        self.frame_lock = threading.Lock()
        
        # 边界和移动限制 - 进一步优化版本
        self.boundary_margin = 20       # 边界边距（像素）
        self.max_single_move = 300   # 单次最大移动距离（像素）- 进一步增加以支持更快移动
        self.tracking_smoothness = 1.0# 跟踪平滑度 (0-1) - 保持最大精度
    
    def update_threshold_config(self, angle_threshold: float = None, 
                               precise_angle_threshold: float = None,
                               use_angle_threshold: bool = None):
        """
        更新角度阈值配置
        
        Args:
            angle_threshold: 角度阈值（度）
            precise_angle_threshold: 精确角度阈值（度）
            use_angle_threshold: 是否使用角度阈值
        """
        if angle_threshold is not None:
            self.angle_threshold = angle_threshold
        if precise_angle_threshold is not None:
            self.precise_angle_threshold = precise_angle_threshold
        if use_angle_threshold is not None:
            self.use_angle_threshold = use_angle_threshold
            
        print(f"[DYNAMIC] 角度阈值配置更新: 阈值={self.angle_threshold}°, 精确阈值={self.precise_angle_threshold}°, 启用={self.use_angle_threshold}")
    
    def start_frame_processing(self):
        """开始处理当前帧（优化跟踪）"""
        if self.optimized_tracking:
            with self.frame_lock:
                self.frame_processing = True
                self.pending_target = None
                print("[DYNAMIC] 🎬 开始帧处理")
    
    def end_frame_processing(self):
        """结束当前帧处理（优化跟踪）"""
        if self.optimized_tracking:
            with self.frame_lock:
                self.frame_processing = False
                # 如果有待处理的目标，现在处理它
                if self.pending_target:
                    print("[DYNAMIC] 📋 处理待处理目标")
                    self._process_pending_target()
                    self.pending_target = None
                print("[DYNAMIC] 🎬 结束帧处理")
    
    def _process_pending_target(self):
        """处理待处理的目标"""
        if not self.pending_target:
            return
            
        target_data = self.pending_target
        print(f"[DYNAMIC] 🎯 处理待处理目标: ({target_data['x']:.1f}, {target_data['y']:.1f})")
    
    def _is_within_safe_bounds(self, target_x: float, target_y: float) -> bool:
        """检查目标是否在安全边界内"""
        margin = self.boundary_margin
        detection_size = 320  # 假设检测尺寸为320
        return (margin <= target_x <= detection_size - margin and 
                margin <= target_y <= detection_size - margin)
    
    def calculate_angle_offset(self, target_x: float, target_y: float, 
                              crosshair_x: float, crosshair_y: float,
                              game_fov: float = 103.0, detection_size: int = 320,
                              game_width: int = 2560, game_height: int = 1600) -> float:
        """
        计算目标与准星的角度偏移
        
        Args:
            target_x: 目标X坐标（像素）
            target_y: 目标Y坐标（像素）
            crosshair_x: 准星X坐标（像素）
            crosshair_y: 准星Y坐标（像素）
            game_fov: 游戏水平FOV（度）
            detection_size: 检测图像尺寸
            game_width: 游戏窗口宽度
            game_height: 游戏窗口高度
            
        Returns:
            总角度偏移（度）
        """
        # 计算像素偏移
        dx_pixels = target_x - crosshair_x
        dy_pixels = target_y - crosshair_y
        
        # 计算角度偏移
        fov_per_pixel = game_fov / game_width
        angle_x = abs(dx_pixels * fov_per_pixel * (detection_size / game_width))
        angle_y = abs(dy_pixels * fov_per_pixel * (detection_size / game_width) * (game_width / game_height))
        
        return math.sqrt(angle_x**2 + angle_y**2)
    
    def is_target_aligned(self, target_x: float, target_y: float, 
                         crosshair_x: float, crosshair_y: float,
                         game_fov: float = 103.0, detection_size: int = 320,
                         game_width: int = 2560, game_height: int = 1600) -> bool:
        """
        检查目标是否与准星对齐
        
        Returns:
            是否精确对齐
        """
        if self.use_angle_threshold:
            angle_offset = self.calculate_angle_offset(
                target_x, target_y, crosshair_x, crosshair_y,
                game_fov, detection_size, game_width, game_height
            )
            
            is_aligned = angle_offset <= self.precise_angle_threshold
            
            if is_aligned:
                print(f"[DYNAMIC] 🎯 目标已对齐！角度偏移: {angle_offset:.3f}° (阈值: {self.precise_angle_threshold:.3f}°)")
            
            return is_aligned
        else:
            # 使用像素距离作为备用方案
            distance = np.sqrt((target_x - crosshair_x)**2 + (target_y - crosshair_y)**2)
            is_aligned = distance <= 5  # 5像素阈值
            
            if is_aligned:
                print(f"[DYNAMIC] 🎯 目标已对齐！像素距离: {distance:.1f}px")
            
            return is_aligned
        
    def aim_at_target(self, target_x: float, target_y: float, confidence: float, 
                     crosshair_x: float = 160, crosshair_y: float = 160,
                     game_fov: float = 103.0, detection_size: int = 320, 
                     game_width: int = 2560, game_height: int = 1600):
        """
        瞄准目标（支持优化跟踪）
        
        Args:
            target_x: 目标X坐标（检测图像像素坐标）
            target_y: 目标Y坐标（检测图像像素坐标）
            confidence: 检测置信度
            crosshair_x: 准星X坐标（检测图像像素坐标）
            crosshair_y: 准星Y坐标（检测图像像素坐标）
            game_fov: 游戏水平FOV（度）
            detection_size: 检测图像尺寸
            game_width: 游戏窗口宽度
            game_height: 游戏窗口高度
            
        Returns:
            移动值元组 (move_x, move_y) 或 None
        """
        # 打印详细的输入信息
        print(f"\n🎯 [AIM_DEBUG] 开始瞄准目标")
        print(f"[AIM_DEBUG] 输入参数:")
        print(f"  - 目标位置: ({target_x:.1f}, {target_y:.1f})")
        print(f"  - 准星位置: ({crosshair_x:.1f}, {crosshair_y:.1f})")
        print(f"  - 置信度: {confidence:.2f}")
        print(f"  - 游戏FOV: {game_fov}°")
        print(f"  - 检测尺寸: {detection_size}x{detection_size}")
        print(f"  - 游戏分辨率: {game_width}x{game_height}")
        
        # 检查输入参数
        if target_x is None or target_y is None:
            print(f"[AIM_DEBUG] ❌ 目标坐标无效，返回None")
            return None
        
        # 优化跟踪：时序控制
        if self.optimized_tracking:
            print(f"[AIM_DEBUG] 🔧 优化跟踪已启用")
            target_data = {
                'x': target_x,
                'y': target_y,
                'confidence': confidence,
                'crosshair_x': crosshair_x,
                'crosshair_y': crosshair_y,
                'timestamp': time.time()
            }
            
            with self.frame_lock:
                if self.frame_processing:
                    # 当前正在处理帧，暂存目标数据
                    self.pending_target = target_data
                    print(f"[AIM_DEBUG] 🔄 帧处理中，暂存目标: ({target_x:.1f}, {target_y:.1f})")
                    return None
        
        # 边界检查
        if self.optimized_tracking and not self._is_within_safe_bounds(target_x, target_y):
            print(f"[AIM_DEBUG] ⚠️ 目标超出安全边界: ({target_x:.1f}, {target_y:.1f})")
            print(f"[AIM_DEBUG] 安全边界: 边距={self.boundary_margin}px, 范围=[{self.boundary_margin}, {320-self.boundary_margin}]")
            return None
        else:
            print(f"[AIM_DEBUG] ✅ 目标在安全边界内: ({target_x:.1f}, {target_y:.1f})")
            
        current_time = time.time()
        self.last_detection_time = current_time
        print(f"[AIM_DEBUG] ⏰ 更新检测时间: {current_time:.3f}")
        
        # 检查目标是否已对齐
        print(f"[AIM_DEBUG] 🎯 检查目标对齐状态...")
        is_aligned = self.is_target_aligned(target_x, target_y, crosshair_x, crosshair_y,
                                           game_fov, detection_size, game_width, game_height)
        if is_aligned:
            # 目标已对齐，停止移动
            print(f"[AIM_DEBUG] ✅ 目标已对齐，返回 (0, 0)")
            return (0, 0)
        else:
            print(f"[AIM_DEBUG] ❌ 目标未对齐，需要移动")
        
        # 更新准星位置
        self.tracker.crosshair_pos = (crosshair_x, crosshair_y)
        print(f"[AIM_DEBUG] 🎯 更新准星位置: ({crosshair_x:.1f}, {crosshair_y:.1f})")
        
        # 计算移动 - 只使用静态瞄准
        self.aiming_mode = "static"  # 设置当前瞄准模式
        print(f"[AIM_DEBUG] 🧮 开始计算静态瞄准移动...")
        move_result = self._static_aim(target_x, target_y, crosshair_x, crosshair_y)
        print(f"[AIM_DEBUG] 📊 静态瞄准计算结果: {move_result}")
        
        # 优化跟踪：应用移动限制
        if self.optimized_tracking and move_result:
            print(f"[AIM_DEBUG] 🔧 应用移动优化...")
            move_x, move_y = move_result
            print(f"[AIM_DEBUG] 原始移动: ({move_x}, {move_y})")
            
            # 应用平滑度
            original_move_x, original_move_y = move_x, move_y
            # 增加跟踪平滑度以提高移动速度
            self.tracking_smoothness = 1.0  # 设置为1.0以获得最快的响应速度
            move_x = int(move_x * self.tracking_smoothness)
            move_y = int(move_y * self.tracking_smoothness)
            print(f"[AIM_DEBUG] 平滑度处理 (smoothness={self.tracking_smoothness}): ({original_move_x}, {original_move_y}) -> ({move_x}, {move_y})")
            
            # 限制单次移动距离
            before_limit_x, before_limit_y = move_x, move_y
            move_x = max(-self.max_single_move, min(self.max_single_move, move_x))
            move_y = max(-self.max_single_move, min(self.max_single_move, move_y))
            print(f"[AIM_DEBUG] 距离限制 (max={self.max_single_move}px): ({before_limit_x}, {before_limit_y}) -> ({move_x}, {move_y})")
            
            print(f"[AIM_DEBUG] 🎯 最终优化移动: ({move_x}, {move_y})")
            print(f"[AIM_DEBUG] 📍 移动终点: 准星({crosshair_x:.1f}, {crosshair_y:.1f}) + 移动({move_x}, {move_y}) = 新位置({crosshair_x + move_x:.1f}, {crosshair_y + move_y:.1f})")
            print(f"[AIM_DEBUG] 🎯 目标位置: ({target_x:.1f}, {target_y:.1f})")
            print(f"[AIM_DEBUG] 📏 移动后距离目标: X差={abs(target_x - (crosshair_x + move_x)):.1f}px, Y差={abs(target_y - (crosshair_y + move_y)):.1f}px")
            return (move_x, move_y)
        
        print(f"[AIM_DEBUG] 🎯 返回原始移动结果: {move_result}")
        if move_result:
            move_x, move_y = move_result
            print(f"[AIM_DEBUG] 📍 移动终点: 准星({crosshair_x:.1f}, {crosshair_y:.1f}) + 移动({move_x}, {move_y}) = 新位置({crosshair_x + move_x:.1f}, {crosshair_y + move_y:.1f})")
            print(f"[AIM_DEBUG] 🎯 目标位置: ({target_x:.1f}, {target_y:.1f})")
            print(f"[AIM_DEBUG] 📏 移动后距离目标: X差={abs(target_x - (crosshair_x + move_x)):.1f}px, Y差={abs(target_y - (crosshair_y + move_y)):.1f}px")
        return move_result
    
    def _static_aim(self, target_x: float, target_y: float, crosshair_x: float, crosshair_y: float):
        """传统静态瞄准，返回移动值 - 修复版本"""
        
        print(f"[STATIC_DEBUG] 🎯 开始静态瞄准计算")
        print(f"[STATIC_DEBUG] 输入: 目标({target_x:.1f}, {target_y:.1f}), 准星({crosshair_x:.1f}, {crosshair_y:.1f})")
        
        # 使用统一坐标系统计算移动
        from coordinate_system import CoordinateSystem
        
        # 初始化坐标系统（使用与main_onnx.py相同的参数）
        coord_system = CoordinateSystem(
            detection_size=320,
            game_width=2560,  # 或使用实际游戏窗口宽度
            game_height=1600, # 或使用实际游戏窗口高度
            game_fov=103.0
        )
        print(f"[STATIC_DEBUG] 坐标系统初始化完成")
        
        # 计算目标到准星的偏移信息
        print(f"[STATIC_DEBUG] 计算偏移信息...")
        offset_info = coord_system.calculate_crosshair_to_target_offset(target_x, target_y, crosshair_x, crosshair_y)
        print(f"[STATIC_DEBUG] 偏移信息: {offset_info}")
        
        # 使用角度偏移计算鼠标移动 - 精确版本
        print(f"[STATIC_DEBUG] 计算鼠标移动...")
        print(f"[STATIC_DEBUG] 角度偏移: H={offset_info['angle']['h']:.3f}°, V={offset_info['angle']['v']:.3f}°")
        move_x, move_y = coord_system.calculate_mouse_movement(
            offset_info['angle']['h'], 
            offset_info['angle']['v'],
            target_distance_factor=1.0,  # 可以根据需要调整
            base_sensitivity=24.85  # 使用精确的转换系数
        )
        
        print(f"[STATIC_DEBUG] 🎯 静态瞄准结果:")
        print(f"[STATIC_DEBUG]   目标: ({target_x:.1f}, {target_y:.1f})")
        print(f"[STATIC_DEBUG]   准星: ({crosshair_x:.1f}, {crosshair_y:.1f})")
        print(f"[STATIC_DEBUG]   像素差: X={target_x - crosshair_x:.1f}px, Y={target_y - crosshair_y:.1f}px")
        print(f"[STATIC_DEBUG]   角度偏移: H={offset_info['angle']['h']:.3f}°, V={offset_info['angle']['v']:.3f}°")
        print(f"[STATIC_DEBUG]   鼠标移动: ({move_x}, {move_y})")
        
        # 保持原有的简化输出
        print(f"[STATIC-FIXED] 目标: ({target_x:.1f}, {target_y:.1f}), 准星: ({crosshair_x:.1f}, {crosshair_y:.1f})")
        print(f"[STATIC-FIXED] 角度偏移: H={offset_info['angle']['h']:.3f}°, V={offset_info['angle']['v']:.3f}°")
        print(f"[STATIC-FIXED] 计算移动: ({move_x}, {move_y})")
        
        return (int(move_x), int(move_y))
    

    
    def update_detection(self, target_x: float, target_y: float, confidence: float):
        """更新检测结果"""
        if self.tracker.is_tracking:
            self.tracker.update_target(target_x, target_y, confidence)
        self.last_detection_time = time.time()
    
    def check_timeout(self):
        """检查检测超时"""
        if self.tracker.is_tracking and time.time() - self.last_detection_time > self.detection_timeout:
            print("[ADAPTIVE] 检测超时，停止跟踪")
            self.tracker.stop_tracking()
    


# 全局实例
adaptive_aiming = AdaptiveAimingSystem()

def get_aiming_system():
    """获取瞄准系统实例"""
    return adaptive_aiming
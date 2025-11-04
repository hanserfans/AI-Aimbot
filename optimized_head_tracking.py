"""
优化的头部跟踪系统
解决时序问题和边界限制问题
"""

import time
import threading
import numpy as np
from typing import Tuple, Optional, Dict, Any
from coordinate_system import CoordinateSystem

class OptimizedHeadTracker:
    """优化的头部跟踪器"""
    
    def __init__(self, movement_amp: float = 0.5, detection_size: int = 320):
        self.movement_amp = movement_amp
        self.detection_size = detection_size
        self.detection_center = detection_size / 2.0
        
        # 跟踪状态
        self.is_tracking = False
        self.current_target = None
        self.target_lock = threading.Lock()
        self.crosshair_pos = (self.detection_center, self.detection_center)
        
        # 时序控制
        self.frame_processing = False  # 当前是否在处理帧
        self.pending_target = None     # 待处理的目标
        self.frame_lock = threading.Lock()
        
        # 边界限制 - 优化版本
        self.boundary_margin = 20  # 边界边距（像素）
        self.max_single_move = 120  # 单次最大移动距离（像素）- 增加以支持精确瞄准
        
        # 跟踪参数 - 优化版本
        self.min_movement_threshold = 1.0
        self.tracking_smoothness = 0.95  # 跟踪平滑度 (0-1) - 提高精度
        
        # 坐标系统
        self.coord_system = None
        
        print("[OPTIMIZED_TRACKER] 优化头部跟踪器初始化完成")
    
    def initialize_coordinate_system(self, game_width: int = 2560, game_height: int = 1600, game_fov: float = 103.0):
        """初始化坐标系统"""
        self.coord_system = CoordinateSystem(
            detection_size=self.detection_size,
            game_width=game_width,
            game_height=game_height,
            game_fov=game_fov
        )
        print("[OPTIMIZED_TRACKER] 坐标系统初始化完成")
    
    def start_frame_processing(self):
        """开始处理当前帧"""
        with self.frame_lock:
            self.frame_processing = True
            self.pending_target = None
    
    def end_frame_processing(self):
        """结束当前帧处理"""
        with self.frame_lock:
            self.frame_processing = False
            # 如果有待处理的目标，现在处理它
            if self.pending_target:
                self._process_target_update(self.pending_target)
                self.pending_target = None
    
    def update_target(self, target_x: float, target_y: float, confidence: float) -> Optional[Tuple[int, int]]:
        """
        更新目标位置（带时序控制）
        
        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            confidence: 检测置信度
            
        Returns:
            移动值 (move_x, move_y) 或 None
        """
        target_data = {
            'x': target_x,
            'y': target_y,
            'confidence': confidence,
            'timestamp': time.time()
        }
        
        with self.frame_lock:
            if self.frame_processing:
                # 当前正在处理帧，暂存目标数据
                self.pending_target = target_data
                print(f"[OPTIMIZED_TRACKER] 帧处理中，暂存目标: ({target_x:.1f}, {target_y:.1f})")
                return None
            else:
                # 立即处理目标更新
                return self._process_target_update(target_data)
    
    def _process_target_update(self, target_data: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """处理目标更新"""
        target_x = target_data['x']
        target_y = target_data['y']
        confidence = target_data['confidence']
        
        # 边界检查
        if not self._is_within_safe_bounds(target_x, target_y):
            print(f"[OPTIMIZED_TRACKER] ⚠️ 目标超出安全边界: ({target_x:.1f}, {target_y:.1f})")
            return None
        
        # 更新当前目标
        with self.target_lock:
            self.current_target = target_data
        
        # 计算移动
        return self._calculate_movement(target_x, target_y)
    
    def _is_within_safe_bounds(self, target_x: float, target_y: float) -> bool:
        """检查目标是否在安全边界内"""
        margin = self.boundary_margin
        return (margin <= target_x <= self.detection_size - margin and 
                margin <= target_y <= self.detection_size - margin)
    
    def _calculate_movement(self, target_x: float, target_y: float) -> Optional[Tuple[int, int]]:
        """计算鼠标移动量"""
        if not self.coord_system:
            print("[OPTIMIZED_TRACKER] ⚠️ 坐标系统未初始化")
            return None
        
        # 计算当前偏移
        offset_x = target_x - self.crosshair_pos[0]
        offset_y = target_y - self.crosshair_pos[1]
        
        # 检查是否需要移动
        distance = np.sqrt(offset_x**2 + offset_y**2)
        if distance < self.min_movement_threshold:
            return None
        
        # 使用坐标系统计算角度偏移
        norm_x, norm_y = self.coord_system.pixel_to_normalized(target_x, target_y)
        crosshair_norm_x, crosshair_norm_y = self.coord_system.pixel_to_normalized(
            self.crosshair_pos[0], self.crosshair_pos[1]
        )
        
        # 计算角度偏移
        angle_offset_h = (norm_x - crosshair_norm_x) * (self.coord_system.effective_fov_h / 2)
        angle_offset_v = (norm_y - crosshair_norm_y) * (self.coord_system.effective_fov_v / 2)
        
        # 使用坐标系统计算鼠标移动 - 精确版本
        move_x, move_y = self.coord_system.calculate_mouse_movement(
            angle_offset_h, angle_offset_v,
            target_distance_factor=1.0,
            base_sensitivity=24.85  # 使用精确的转换系数
        )
        
        # 应用平滑度和限制
        move_x = int(move_x * self.tracking_smoothness * self.movement_amp)
        move_y = int(move_y * self.tracking_smoothness * self.movement_amp)
        
        # 限制单次移动距离
        move_x = max(-self.max_single_move, min(self.max_single_move, move_x))
        move_y = max(-self.max_single_move, min(self.max_single_move, move_y))
        
        # 边界预测检查
        predicted_x = self.crosshair_pos[0] + move_x / self.movement_amp
        predicted_y = self.crosshair_pos[1] + move_y / self.movement_amp
        
        if not self._is_within_safe_bounds(predicted_x, predicted_y):
            print(f"[OPTIMIZED_TRACKER] ⚠️ 移动会超出边界，取消移动")
            return None
        
        # 更新准星位置
        self.crosshair_pos = (predicted_x, predicted_y)
        
        print(f"[OPTIMIZED_TRACKER] 🎯 计算移动: ({move_x}, {move_y}), 距离: {distance:.1f}px")
        print(f"[OPTIMIZED_TRACKER] 📍 准星位置: ({self.crosshair_pos[0]:.1f}, {self.crosshair_pos[1]:.1f})")
        
        return (move_x, move_y)
    
    def is_target_locked(self, target_x: float, target_y: float, threshold: float = 3.0) -> bool:
        """检查目标是否已锁定"""
        distance = np.sqrt((target_x - self.crosshair_pos[0])**2 + 
                          (target_y - self.crosshair_pos[1])**2)
        is_locked = distance <= threshold
        
        if is_locked:
            print(f"[OPTIMIZED_TRACKER] 🔒 目标已锁定！距离: {distance:.1f}px")
        
        return is_locked
    
    def reset_crosshair_position(self):
        """重置准星位置到中心"""
        self.crosshair_pos = (self.detection_center, self.detection_center)
        print("[OPTIMIZED_TRACKER] 🎯 准星位置已重置到中心")
    
    def get_tracking_info(self) -> Dict[str, Any]:
        """获取跟踪信息"""
        with self.target_lock:
            return {
                'is_tracking': self.is_tracking,
                'current_target': self.current_target.copy() if self.current_target else None,
                'crosshair_pos': self.crosshair_pos,
                'frame_processing': self.frame_processing,
                'has_pending_target': self.pending_target is not None
            }


class FrameBasedTrackingManager:
    """基于帧的跟踪管理器"""
    
    def __init__(self, tracker: OptimizedHeadTracker):
        self.tracker = tracker
        self.frame_count = 0
        
    def process_frame(self, detections: list) -> Optional[Tuple[int, int]]:
        """
        处理一帧检测结果
        
        Args:
            detections: 检测结果列表 [{'x': x, 'y': y, 'confidence': conf}, ...]
            
        Returns:
            移动值 (move_x, move_y) 或 None
        """
        self.frame_count += 1
        
        # 开始帧处理
        self.tracker.start_frame_processing()
        
        try:
            # 选择最佳目标
            best_target = self._select_best_target(detections)
            
            if best_target:
                # 更新目标（此时会暂存，不会立即处理）
                self.tracker.update_target(
                    best_target['x'], 
                    best_target['y'], 
                    best_target['confidence']
                )
            
            # 结束帧处理（此时会处理暂存的目标）
            self.tracker.end_frame_processing()
            
            # 获取移动结果
            if best_target:
                return self.tracker._calculate_movement(best_target['x'], best_target['y'])
            
        except Exception as e:
            print(f"[FRAME_MANAGER] ❌ 处理帧时出错: {e}")
            self.tracker.end_frame_processing()
            
        return None
    
    def _select_best_target(self, detections: list) -> Optional[Dict[str, Any]]:
        """选择最佳目标"""
        if not detections:
            return None
        
        # 按置信度排序
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 选择置信度最高且在安全边界内的目标
        for detection in detections:
            if self.tracker._is_within_safe_bounds(detection['x'], detection['y']):
                return detection
        
        return None


# 使用示例
def create_optimized_tracking_system():
    """创建优化的跟踪系统"""
    tracker = OptimizedHeadTracker(movement_amp=0.5, detection_size=320)
    tracker.initialize_coordinate_system(game_width=2560, game_height=1600, game_fov=103.0)
    
    manager = FrameBasedTrackingManager(tracker)
    
    return tracker, manager

if __name__ == "__main__":
    # 测试代码
    tracker, manager = create_optimized_tracking_system()
    
    # 模拟检测结果
    test_detections = [
        {'x': 170, 'y': 150, 'confidence': 0.9},
        {'x': 180, 'y': 160, 'confidence': 0.8}
    ]
    
    # 处理帧
    result = manager.process_frame(test_detections)
    print(f"移动结果: {result}")
    
    # 获取跟踪信息
    info = tracker.get_tracking_info()
    print(f"跟踪信息: {info}")
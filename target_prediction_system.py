"""
目标位置预测和惯性跟踪系统
解决目标跟踪中断问题，在未检测到目标时继续移动
"""

import time
import numpy as np
from typing import Optional, Tuple, List, Dict
from collections import deque
import threading

class TargetPredictionSystem:
    """目标位置预测系统"""
    
    def __init__(self, max_history: int = 10, prediction_time: float = 0.1):
        """
        初始化目标预测系统
        
        Args:
            max_history: 最大历史位置记录数
            prediction_time: 预测时间（秒）
        """
        self.max_history = max_history
        self.prediction_time = prediction_time
        self.position_history = deque(maxlen=max_history)
        self.last_update_time = None
        
    def add_position(self, x: float, y: float, timestamp: Optional[float] = None):
        """
        添加目标位置到历史记录
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            timestamp: 时间戳，如果为None则使用当前时间
        """
        if timestamp is None:
            timestamp = time.time()
            
        self.position_history.append({
            'x': x,
            'y': y,
            'timestamp': timestamp
        })
        self.last_update_time = timestamp
        
    def predict_position(self, future_time: Optional[float] = None) -> Tuple[float, float]:
        """
        预测目标在未来时间的位置
        
        Args:
            future_time: 预测的未来时间戳，如果为None则使用当前时间+prediction_time
            
        Returns:
            预测的(x, y)坐标
        """
        if len(self.position_history) < 2:
            # 历史数据不足，返回最后已知位置
            if len(self.position_history) == 1:
                pos = self.position_history[-1]
                return pos['x'], pos['y']
            return 0.0, 0.0
            
        if future_time is None:
            future_time = time.time() + self.prediction_time
            
        # 使用线性回归预测位置
        positions = list(self.position_history)
        
        # 提取时间和坐标数据
        times = np.array([pos['timestamp'] for pos in positions])
        x_coords = np.array([pos['x'] for pos in positions])
        y_coords = np.array([pos['y'] for pos in positions])
        
        # 计算速度（使用最近的几个点）
        if len(positions) >= 3:
            # 使用最近3个点计算平均速度
            recent_positions = positions[-3:]
            dt = recent_positions[-1]['timestamp'] - recent_positions[0]['timestamp']
            if dt > 0:
                vx = (recent_positions[-1]['x'] - recent_positions[0]['x']) / dt
                vy = (recent_positions[-1]['y'] - recent_positions[0]['y']) / dt
            else:
                vx = vy = 0
        else:
            # 使用最近2个点计算速度
            dt = positions[-1]['timestamp'] - positions[-2]['timestamp']
            if dt > 0:
                vx = (positions[-1]['x'] - positions[-2]['x']) / dt
                vy = (positions[-1]['y'] - positions[-2]['y']) / dt
            else:
                vx = vy = 0
        
        # 预测未来位置
        last_pos = positions[-1]
        time_diff = future_time - last_pos['timestamp']
        
        predicted_x = last_pos['x'] + vx * time_diff
        predicted_y = last_pos['y'] + vy * time_diff
        
        return predicted_x, predicted_y
        
    def get_velocity(self) -> Tuple[float, float]:
        """
        获取目标当前速度
        
        Returns:
            (vx, vy) 速度向量
        """
        if len(self.position_history) < 2:
            return 0.0, 0.0
            
        positions = list(self.position_history)
        
        # 使用最近的几个点计算平均速度
        if len(positions) >= 3:
            recent_positions = positions[-3:]
            dt = recent_positions[-1]['timestamp'] - recent_positions[0]['timestamp']
            if dt > 0:
                vx = (recent_positions[-1]['x'] - recent_positions[0]['x']) / dt
                vy = (recent_positions[-1]['y'] - recent_positions[0]['y']) / dt
                return vx, vy
        
        # 使用最近2个点计算速度
        dt = positions[-1]['timestamp'] - positions[-2]['timestamp']
        if dt > 0:
            vx = (positions[-1]['x'] - positions[-2]['x']) / dt
            vy = (positions[-1]['y'] - positions[-2]['y']) / dt
            return vx, vy
            
        return 0.0, 0.0
        
    def is_moving(self, threshold: float = 1.0) -> bool:
        """
        判断目标是否在移动
        
        Args:
            threshold: 速度阈值（像素/秒）
            
        Returns:
            True如果目标在移动
        """
        vx, vy = self.get_velocity()
        speed = np.sqrt(vx**2 + vy**2)
        return speed > threshold
        
    def clear_history(self):
        """清除历史记录"""
        self.position_history.clear()
        self.last_update_time = None


class InertialTrackingSystem:
    """惯性跟踪系统"""
    
    def __init__(self, decay_rate: float = 0.95, min_movement: float = 0.5):
        """
        初始化惯性跟踪系统
        
        Args:
            decay_rate: 惯性衰减率（0-1之间）
            min_movement: 最小移动阈值
        """
        self.decay_rate = decay_rate
        self.min_movement = min_movement
        self.last_movement = [0.0, 0.0]
        self.last_update_time = None
        self.is_tracking = False
        
    def update_movement(self, move_x: float, move_y: float):
        """
        更新移动向量
        
        Args:
            move_x: X方向移动量
            move_y: Y方向移动量
        """
        self.last_movement = [move_x, move_y]
        self.last_update_time = time.time()
        self.is_tracking = True
        
    def get_inertial_movement(self) -> Tuple[float, float]:
        """
        获取惯性移动量
        
        Returns:
            (move_x, move_y) 惯性移动向量
        """
        if not self.is_tracking or self.last_update_time is None:
            return 0.0, 0.0
            
        # 计算时间衰减
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        
        # 应用时间衰减和惯性衰减
        # 使用更激进的衰减：每秒衰减到原来的decay_rate，每0.1秒额外衰减
        time_decay_factor = self.decay_rate ** (time_diff * 10)  # 每0.1秒应用一次衰减
        
        inertial_x = self.last_movement[0] * time_decay_factor
        inertial_y = self.last_movement[1] * time_decay_factor
        
        # 检查是否低于最小移动阈值
        movement_magnitude = np.sqrt(inertial_x**2 + inertial_y**2)
        if movement_magnitude < self.min_movement:
            self.is_tracking = False
            return 0.0, 0.0
            
        return inertial_x, inertial_y
        
    def stop_tracking(self):
        """停止惯性跟踪"""
        self.is_tracking = False
        self.last_movement = [0.0, 0.0]


class ContinuousTrackingSystem:
    """连续跟踪系统 - 整合预测和惯性跟踪"""
    
    def __init__(self, 
                 max_prediction_time: float = 0.5,
                 inertial_decay_rate: float = 0.9,
                 confidence_threshold: float = 0.3):
        """
        初始化连续跟踪系统
        
        Args:
            max_prediction_time: 最大预测时间（秒）
            inertial_decay_rate: 惯性衰减率
            confidence_threshold: 置信度阈值
        """
        self.predictor = TargetPredictionSystem()
        self.inertial_tracker = InertialTrackingSystem(decay_rate=inertial_decay_rate)
        
        self.max_prediction_time = max_prediction_time
        self.confidence_threshold = confidence_threshold
        
        self.last_target_time = None
        self.tracking_mode = "none"  # none, prediction, inertial
        self.lock = threading.Lock()
        
    def update_target(self, x: float, y: float, confidence: float = 1.0):
        """
        更新目标位置
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            confidence: 检测置信度
        """
        with self.lock:
            current_time = time.time()
            
            # 只有置信度足够高才更新预测器
            if confidence >= self.confidence_threshold:
                self.predictor.add_position(x, y, current_time)
                self.last_target_time = current_time
                self.tracking_mode = "target"
                
                print(f"[CONTINUOUS_TRACKING] 更新目标位置: ({x:.1f}, {y:.1f}), 置信度: {confidence:.3f}")
            
    def get_tracking_position(self, crosshair_x: float, crosshair_y: float) -> Optional[Tuple[float, float, str]]:
        """
        获取跟踪位置（目标位置或预测位置）
        
        Args:
            crosshair_x: 准星X坐标
            crosshair_y: 准星Y坐标
            
        Returns:
            (target_x, target_y, mode) 或 None
        """
        with self.lock:
            current_time = time.time()
            
            # 检查是否有最近的目标数据
            if self.last_target_time is None:
                return None
                
            time_since_last_target = current_time - self.last_target_time
            
            # 如果目标数据太旧，停止跟踪
            if time_since_last_target > self.max_prediction_time:
                self.tracking_mode = "none"
                self.inertial_tracker.stop_tracking()
                print(f"[CONTINUOUS_TRACKING] 目标数据过旧 ({time_since_last_target:.3f}s)，停止跟踪")
                return None
            
            # 使用预测位置
            if time_since_last_target > 0.05:  # 50ms后开始使用预测
                predicted_x, predicted_y = self.predictor.predict_position()
                self.tracking_mode = "prediction"
                
                print(f"[CONTINUOUS_TRACKING] 使用预测位置: ({predicted_x:.1f}, {predicted_y:.1f})")
                return predicted_x, predicted_y, "prediction"
            else:
                # 使用最新的实际目标位置
                if len(self.predictor.position_history) > 0:
                    last_pos = self.predictor.position_history[-1]
                    return last_pos['x'], last_pos['y'], "target"
                    
            return None
            
    def update_movement(self, move_x: float, move_y: float):
        """
        更新移动向量（用于惯性跟踪）
        
        Args:
            move_x: X方向移动量
            move_y: Y方向移动量
        """
        with self.lock:
            self.inertial_tracker.update_movement(move_x, move_y)
            
    def get_inertial_movement(self) -> Tuple[float, float]:
        """
        获取惯性移动量
        
        Returns:
            (move_x, move_y) 惯性移动向量
        """
        with self.lock:
            return self.inertial_tracker.get_inertial_movement()
            
    def clear_tracking(self):
        """清除所有跟踪数据"""
        with self.lock:
            self.predictor.clear_history()
            self.inertial_tracker.stop_tracking()
            self.last_target_time = None
            self.tracking_mode = "none"
            print("[CONTINUOUS_TRACKING] 清除所有跟踪数据")
            
    def get_status(self) -> Dict:
        """
        获取跟踪系统状态
        
        Returns:
            状态字典
        """
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_target_time if self.last_target_time else None
            
            return {
                'mode': self.tracking_mode,
                'history_count': len(self.predictor.position_history),
                'time_since_last_target': time_since_last,
                'is_inertial_tracking': self.inertial_tracker.is_tracking,
                'velocity': self.predictor.get_velocity() if len(self.predictor.position_history) >= 2 else (0, 0)
            }
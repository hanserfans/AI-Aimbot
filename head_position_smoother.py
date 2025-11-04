"""
头部位置平滑系统
专门用于减少头部位置计算中的抖动和不稳定性
"""

import numpy as np
from collections import deque
from typing import Tuple, Optional
import time


class HeadPositionSmoother:
    """头部位置平滑器"""
    
    def __init__(self, 
                 smoothing_factor: float = 0.7,
                 history_size: int = 8,
                 velocity_smoothing: float = 0.5,
                 min_movement_threshold: float = 1.5):
        """
        初始化头部位置平滑器
        
        Args:
            smoothing_factor: 位置平滑系数 (0-1)，越大越平滑
            history_size: 保持的历史位置数量
            velocity_smoothing: 速度平滑系数
            min_movement_threshold: 最小移动阈值，小于此值的移动将被忽略
        """
        self.smoothing_factor = smoothing_factor
        self.history_size = history_size
        self.velocity_smoothing = velocity_smoothing
        self.min_movement_threshold = min_movement_threshold
        
        # 位置历史
        self.position_history = deque(maxlen=history_size)
        self.time_history = deque(maxlen=history_size)
        
        # 当前平滑位置
        self.current_smoothed_x = None
        self.current_smoothed_y = None
        
        # 速度信息
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        
        # 统计信息
        self.total_updates = 0
        self.smoothed_updates = 0
        
        print("[HEAD_SMOOTHER] 头部位置平滑器已初始化")
        print(f"   • 平滑系数: {smoothing_factor}")
        print(f"   • 历史大小: {history_size}")
        print(f"   • 速度平滑: {velocity_smoothing}")
        print(f"   • 移动阈值: {min_movement_threshold}")
    
    def update_position(self, head_x: float, head_y: float) -> Tuple[float, float]:
        """
        更新头部位置并返回平滑后的位置
        
        Args:
            head_x: 原始头部X坐标
            head_y: 原始头部Y坐标
            
        Returns:
            平滑后的头部位置 (smoothed_x, smoothed_y)
        """
        current_time = time.time()
        self.total_updates += 1
        
        # 如果是第一次更新，直接使用原始位置
        if self.current_smoothed_x is None:
            self.current_smoothed_x = head_x
            self.current_smoothed_y = head_y
            self._add_to_history(head_x, head_y, current_time)
            return head_x, head_y
        
        # 计算与当前平滑位置的距离
        distance = np.sqrt((head_x - self.current_smoothed_x)**2 + 
                          (head_y - self.current_smoothed_y)**2)
        
        # 如果移动距离太小，保持当前位置
        if distance < self.min_movement_threshold:
            return self.current_smoothed_x, self.current_smoothed_y
        
        # 计算速度
        if len(self.time_history) > 0:
            dt = current_time - self.time_history[-1]
            if dt > 0:
                new_velocity_x = (head_x - self.position_history[-1][0]) / dt
                new_velocity_y = (head_y - self.position_history[-1][1]) / dt
                
                # 平滑速度
                self.velocity_x = (1 - self.velocity_smoothing) * self.velocity_x + \
                                 self.velocity_smoothing * new_velocity_x
                self.velocity_y = (1 - self.velocity_smoothing) * self.velocity_y + \
                                 self.velocity_smoothing * new_velocity_y
        
        # 应用位置平滑
        alpha = self.smoothing_factor
        
        # 基于速度调整平滑系数
        speed = np.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if speed > 100:  # 快速移动时减少平滑
            alpha *= 0.7
        elif speed < 10:  # 慢速移动时增加平滑
            alpha *= 1.2
            alpha = min(alpha, 0.9)  # 限制最大平滑系数
        
        # 计算平滑位置
        self.current_smoothed_x = (1 - alpha) * self.current_smoothed_x + alpha * head_x
        self.current_smoothed_y = (1 - alpha) * self.current_smoothed_y + alpha * head_y
        
        # 添加到历史记录
        self._add_to_history(head_x, head_y, current_time)
        
        self.smoothed_updates += 1
        
        return self.current_smoothed_x, self.current_smoothed_y
    
    def _add_to_history(self, x: float, y: float, timestamp: float):
        """添加位置到历史记录"""
        self.position_history.append((x, y))
        self.time_history.append(timestamp)
    
    def get_predicted_position(self, prediction_time: float = 0.016) -> Optional[Tuple[float, float]]:
        """
        基于当前速度预测未来位置
        
        Args:
            prediction_time: 预测时间（秒），默认为一帧时间
            
        Returns:
            预测的头部位置，如果无法预测则返回None
        """
        if self.current_smoothed_x is None:
            return None
        
        # 基于当前速度预测
        predicted_x = self.current_smoothed_x + self.velocity_x * prediction_time
        predicted_y = self.current_smoothed_y + self.velocity_y * prediction_time
        
        return predicted_x, predicted_y
    
    def get_average_position(self) -> Optional[Tuple[float, float]]:
        """
        获取历史位置的平均值
        
        Returns:
            平均位置，如果没有历史数据则返回None
        """
        if len(self.position_history) == 0:
            return None
        
        positions = np.array(self.position_history)
        avg_x = np.mean(positions[:, 0])
        avg_y = np.mean(positions[:, 1])
        
        return avg_x, avg_y
    
    def reset(self):
        """重置平滑器状态"""
        self.position_history.clear()
        self.time_history.clear()
        self.current_smoothed_x = None
        self.current_smoothed_y = None
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        print("[HEAD_SMOOTHER] 平滑器状态已重置")
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        smoothing_rate = self.smoothed_updates / self.total_updates if self.total_updates > 0 else 0
        
        return {
            'total_updates': self.total_updates,
            'smoothed_updates': self.smoothed_updates,
            'smoothing_rate': smoothing_rate,
            'current_velocity': np.sqrt(self.velocity_x**2 + self.velocity_y**2),
            'history_size': len(self.position_history),
            'current_position': (self.current_smoothed_x, self.current_smoothed_y) if self.current_smoothed_x is not None else None
        }


# 全局实例
_head_smoother = None

def get_head_position_smoother() -> HeadPositionSmoother:
    """获取头部位置平滑器实例"""
    global _head_smoother
    if _head_smoother is None:
        _head_smoother = HeadPositionSmoother()
    return _head_smoother

def create_head_position_smoother(**kwargs) -> HeadPositionSmoother:
    """创建新的头部位置平滑器实例"""
    global _head_smoother
    _head_smoother = HeadPositionSmoother(**kwargs)
    return _head_smoother

def reset_head_position_smoother():
    """重置头部位置平滑器"""
    global _head_smoother
    if _head_smoother is not None:
        _head_smoother.reset()
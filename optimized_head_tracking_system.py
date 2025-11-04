"""
优化的头部跟踪系统
减少历史记忆影响，提供更实时的头部位置跟踪
"""

import time
import threading
import numpy as np
from typing import Optional, Dict, List, Tuple
from collections import deque
import math

class OptimizedHeadTracker:
    """优化的头部跟踪器"""
    
    def __init__(self, 
                 max_history_size: int = 3,  # 减少历史记录大小
                 position_threshold: float = 5.0,  # 位置变化阈值
                 velocity_smoothing: float = 0.3,  # 速度平滑系数
                 max_prediction_time: float = 0.05):  # 最大预测时间（50ms）
        """
        初始化优化的头部跟踪器
        
        Args:
            max_history_size: 最大历史记录大小（减少到3个）
            position_threshold: 位置变化阈值，小于此值的变化被忽略
            velocity_smoothing: 速度平滑系数，越小越平滑
            max_prediction_time: 最大预测时间
        """
        self.max_history_size = max_history_size
        self.position_threshold = position_threshold
        self.velocity_smoothing = velocity_smoothing
        self.max_prediction_time = max_prediction_time
        
        # 头部位置历史记录（使用deque提高性能）
        self.position_history = deque(maxlen=max_history_size)
        self.velocity_history = deque(maxlen=2)  # 只保留2个速度记录
        
        # 当前状态
        self.current_velocity = {'x': 0.0, 'y': 0.0}
        self.last_update_time = 0
        self.tracking_confidence = 0.0
        
        # 线程锁
        self.lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            'updates_count': 0,
            'predictions_count': 0,
            'position_changes': 0,
            'avg_velocity': 0.0,
            'max_velocity': 0.0
        }
        
        print(f"[INFO] 优化头部跟踪器初始化完成，历史大小: {max_history_size}")
    
    def update_position(self, head_x: float, head_y: float, timestamp: float = None) -> bool:
        """
        更新头部位置
        
        Args:
            head_x: 头部X坐标
            head_y: 头部Y坐标
            timestamp: 时间戳，如果为None则使用当前时间
            
        Returns:
            bool: 是否成功更新位置
        """
        if timestamp is None:
            timestamp = time.time()
        
        try:
            with self.lock:
                # 检查位置变化是否足够大
                if self.position_history:
                    last_pos = self.position_history[-1]
                    distance = math.sqrt((head_x - last_pos['x'])**2 + (head_y - last_pos['y'])**2)
                    
                    # 如果位置变化太小，忽略此次更新（减少噪声）
                    if distance < self.position_threshold:
                        return False
                    
                    self.stats['position_changes'] += 1
                
                # 添加新位置到历史记录
                new_position = {
                    'x': head_x,
                    'y': head_y,
                    'timestamp': timestamp
                }
                self.position_history.append(new_position)
                
                # 计算速度
                self._calculate_velocity()
                
                # 更新统计信息
                self.stats['updates_count'] += 1
                self.last_update_time = timestamp
                
                # 计算跟踪置信度
                self._update_tracking_confidence()
                
                return True
                
        except Exception as e:
            print(f"[ERROR] 更新头部位置失败: {e}")
            return False
    
    def _calculate_velocity(self):
        """计算头部移动速度"""
        if len(self.position_history) < 2:
            return
        
        try:
            # 使用最近两个位置计算速度
            current_pos = self.position_history[-1]
            prev_pos = self.position_history[-2]
            
            time_diff = current_pos['timestamp'] - prev_pos['timestamp']
            if time_diff <= 0:
                return
            
            # 计算瞬时速度
            velocity_x = (current_pos['x'] - prev_pos['x']) / time_diff
            velocity_y = (current_pos['y'] - prev_pos['y']) / time_diff
            
            # 平滑速度（减少抖动）
            self.current_velocity['x'] = (
                self.current_velocity['x'] * (1 - self.velocity_smoothing) + 
                velocity_x * self.velocity_smoothing
            )
            self.current_velocity['y'] = (
                self.current_velocity['y'] * (1 - self.velocity_smoothing) + 
                velocity_y * self.velocity_smoothing
            )
            
            # 记录速度历史
            velocity_magnitude = math.sqrt(velocity_x**2 + velocity_y**2)
            self.velocity_history.append(velocity_magnitude)
            
            # 更新统计信息
            self.stats['avg_velocity'] = (
                self.stats['avg_velocity'] * 0.9 + velocity_magnitude * 0.1
            )
            self.stats['max_velocity'] = max(self.stats['max_velocity'], velocity_magnitude)
            
        except Exception as e:
            print(f"[ERROR] 计算速度失败: {e}")
    
    def _update_tracking_confidence(self):
        """更新跟踪置信度"""
        if len(self.position_history) < 2:
            self.tracking_confidence = 0.5
            return
        
        try:
            # 基于位置历史的一致性计算置信度
            if len(self.position_history) >= 3:
                # 计算位置变化的一致性
                recent_positions = list(self.position_history)[-3:]
                distances = []
                
                for i in range(1, len(recent_positions)):
                    dist = math.sqrt(
                        (recent_positions[i]['x'] - recent_positions[i-1]['x'])**2 + 
                        (recent_positions[i]['y'] - recent_positions[i-1]['y'])**2
                    )
                    distances.append(dist)
                
                if distances:
                    # 距离变化越小，置信度越高
                    avg_distance = sum(distances) / len(distances)
                    consistency = 1.0 / (1.0 + avg_distance / 50.0)  # 归一化
                    self.tracking_confidence = min(1.0, consistency)
                else:
                    self.tracking_confidence = 0.8
            else:
                self.tracking_confidence = 0.7
                
        except Exception as e:
            print(f"[ERROR] 更新跟踪置信度失败: {e}")
            self.tracking_confidence = 0.5
    
    def get_current_position(self, predict_future: bool = False) -> Optional[Dict[str, float]]:
        """
        获取当前头部位置
        
        Args:
            predict_future: 是否预测未来位置
            
        Returns:
            包含位置信息的字典
        """
        try:
            with self.lock:
                if not self.position_history:
                    return None
                
                current_pos = self.position_history[-1]
                current_time = time.time()
                
                # 检查位置是否过时
                position_age = current_time - current_pos['timestamp']
                if position_age > 0.1:  # 100ms
                    print(f"[DEBUG] 头部位置过时，年龄: {position_age*1000:.1f}ms")
                    return None
                
                result = {
                    'x': current_pos['x'],
                    'y': current_pos['y'],
                    'timestamp': current_pos['timestamp'],
                    'age_ms': position_age * 1000,
                    'confidence': self.tracking_confidence,
                    'velocity_x': self.current_velocity['x'],
                    'velocity_y': self.current_velocity['y']
                }
                
                # 如果需要预测未来位置
                if predict_future and len(self.position_history) >= 2:
                    prediction_time = min(position_age, self.max_prediction_time)
                    if prediction_time > 0:
                        predicted_x = current_pos['x'] + self.current_velocity['x'] * prediction_time
                        predicted_y = current_pos['y'] + self.current_velocity['y'] * prediction_time
                        
                        result.update({
                            'predicted_x': predicted_x,
                            'predicted_y': predicted_y,
                            'prediction_time': prediction_time
                        })
                        
                        self.stats['predictions_count'] += 1
                
                return result
                
        except Exception as e:
            print(f"[ERROR] 获取当前位置失败: {e}")
            return None
    
    def get_stable_position(self) -> Optional[Dict[str, float]]:
        """
        获取稳定的头部位置（基于历史平均）
        
        Returns:
            稳定位置信息
        """
        try:
            with self.lock:
                if len(self.position_history) < 2:
                    return self.get_current_position()
                
                # 计算加权平均位置（最新的权重更大）
                total_weight = 0
                weighted_x = 0
                weighted_y = 0
                
                positions = list(self.position_history)
                for i, pos in enumerate(positions):
                    weight = (i + 1) / len(positions)  # 线性权重
                    weighted_x += pos['x'] * weight
                    weighted_y += pos['y'] * weight
                    total_weight += weight
                
                if total_weight > 0:
                    stable_x = weighted_x / total_weight
                    stable_y = weighted_y / total_weight
                    
                    return {
                        'x': stable_x,
                        'y': stable_y,
                        'timestamp': positions[-1]['timestamp'],
                        'confidence': self.tracking_confidence,
                        'is_stable': True,
                        'history_size': len(positions)
                    }
                
                return None
                
        except Exception as e:
            print(f"[ERROR] 获取稳定位置失败: {e}")
            return None
    
    def clear_history(self):
        """清除历史记录"""
        try:
            with self.lock:
                self.position_history.clear()
                self.velocity_history.clear()
                self.current_velocity = {'x': 0.0, 'y': 0.0}
                self.tracking_confidence = 0.0
                self.last_update_time = 0
                print("[DEBUG] 头部跟踪历史已清除")
        except Exception as e:
            print(f"[ERROR] 清除历史记录失败: {e}")
    
    def is_tracking_stable(self) -> bool:
        """检查跟踪是否稳定"""
        return (
            len(self.position_history) >= 2 and 
            self.tracking_confidence > 0.6 and
            time.time() - self.last_update_time < 0.1
        )
    
    def get_stats(self) -> Dict[str, any]:
        """获取统计信息"""
        with self.lock:
            stats = self.stats.copy()
            stats.update({
                'history_size': len(self.position_history),
                'tracking_confidence': self.tracking_confidence,
                'current_velocity': self.current_velocity.copy(),
                'is_stable': self.is_tracking_stable()
            })
            return stats
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()
        print(f"\n📊 优化头部跟踪器统计:")
        print(f"   • 更新次数: {stats['updates_count']}")
        print(f"   • 预测次数: {stats['predictions_count']}")
        print(f"   • 位置变化: {stats['position_changes']}")
        print(f"   • 历史大小: {stats['history_size']}")
        print(f"   • 跟踪置信度: {stats['tracking_confidence']:.2f}")
        print(f"   • 平均速度: {stats['avg_velocity']:.2f} px/s")
        print(f"   • 最大速度: {stats['max_velocity']:.2f} px/s")
        print(f"   • 跟踪稳定: {'是' if stats['is_stable'] else '否'}")


class HeadTrackingOptimizer:
    """头部跟踪优化器"""
    
    def __init__(self):
        """初始化头部跟踪优化器"""
        self.tracker = OptimizedHeadTracker()
        self.smoothing_enabled = True
        self.prediction_enabled = True
        
        # 平滑参数
        self.position_smoothing = 0.7  # 位置平滑系数
        self.last_smooth_position = None
        
        print("[INFO] 头部跟踪优化器初始化完成")
    
    def update_head_position(self, head_x: float, head_y: float, timestamp: float = None) -> bool:
        """
        更新头部位置（优化版本）
        
        Args:
            head_x: 头部X坐标
            head_y: 头部Y坐标
            timestamp: 时间戳
            
        Returns:
            bool: 是否成功更新
        """
        return self.tracker.update_position(head_x, head_y, timestamp)
    
    def get_optimized_head_position(self, use_prediction: bool = None) -> Optional[Dict[str, float]]:
        """
        获取优化的头部位置
        
        Args:
            use_prediction: 是否使用预测，如果为None则使用默认设置
            
        Returns:
            优化的头部位置信息
        """
        if use_prediction is None:
            use_prediction = self.prediction_enabled
        
        # 获取当前位置
        position = self.tracker.get_current_position(predict_future=use_prediction)
        if not position:
            return None
        
        # 应用位置平滑
        if self.smoothing_enabled and self.last_smooth_position:
            smoothed_x = (
                self.last_smooth_position['x'] * (1 - self.position_smoothing) + 
                position['x'] * self.position_smoothing
            )
            smoothed_y = (
                self.last_smooth_position['y'] * (1 - self.position_smoothing) + 
                position['y'] * self.position_smoothing
            )
            
            position['x'] = smoothed_x
            position['y'] = smoothed_y
            position['is_smoothed'] = True
        
        # 更新最后平滑位置
        self.last_smooth_position = {'x': position['x'], 'y': position['y']}
        
        return position
    
    def get_stable_head_position(self) -> Optional[Dict[str, float]]:
        """获取稳定的头部位置"""
        return self.tracker.get_stable_position()
    
    def clear_head_memory(self):
        """清除头部记忆"""
        self.tracker.clear_history()
        self.last_smooth_position = None
        print("[DEBUG] 头部记忆已清除")
    
    def configure_optimization(self, 
                             smoothing_enabled: bool = True,
                             prediction_enabled: bool = True,
                             position_smoothing: float = 0.7):
        """
        配置优化参数
        
        Args:
            smoothing_enabled: 是否启用平滑
            prediction_enabled: 是否启用预测
            position_smoothing: 位置平滑系数
        """
        self.smoothing_enabled = smoothing_enabled
        self.prediction_enabled = prediction_enabled
        self.position_smoothing = position_smoothing
        
        print(f"[INFO] 头部跟踪优化配置更新:")
        print(f"   • 平滑: {'启用' if smoothing_enabled else '禁用'}")
        print(f"   • 预测: {'启用' if prediction_enabled else '禁用'}")
        print(f"   • 平滑系数: {position_smoothing}")
    
    def get_performance_stats(self) -> Dict[str, any]:
        """获取性能统计"""
        return self.tracker.get_stats()
    
    def print_performance_stats(self):
        """打印性能统计"""
        self.tracker.print_stats()


# 全局头部跟踪优化器实例
_head_tracking_optimizer = None

def get_head_tracking_optimizer() -> HeadTrackingOptimizer:
    """获取全局头部跟踪优化器实例"""
    global _head_tracking_optimizer
    if _head_tracking_optimizer is None:
        _head_tracking_optimizer = HeadTrackingOptimizer()
    return _head_tracking_optimizer

def optimize_head_tracking_parameters():
    """优化头部跟踪参数"""
    optimizer = get_head_tracking_optimizer()
    
    # 配置为更实时的参数
    optimizer.configure_optimization(
        smoothing_enabled=True,
        prediction_enabled=True,
        position_smoothing=0.5  # 减少平滑，提高响应性
    )
    
    print("[INFO] 头部跟踪参数已优化为实时模式")


if __name__ == "__main__":
    # 测试代码
    print("测试优化的头部跟踪系统...")
    
    tracker = OptimizedHeadTracker()
    
    # 模拟头部位置更新
    import random
    base_x, base_y = 160, 160
    
    for i in range(10):
        # 模拟头部移动
        x = base_x + random.uniform(-10, 10)
        y = base_y + random.uniform(-10, 10)
        
        success = tracker.update_position(x, y)
        if success:
            position = tracker.get_current_position(predict_future=True)
            if position:
                print(f"位置 {i+1}: ({position['x']:.1f}, {position['y']:.1f}), "
                      f"置信度: {position['confidence']:.2f}")
        
        time.sleep(0.01)
    
    # 打印统计
    tracker.print_stats()
    
    print("测试完成！")
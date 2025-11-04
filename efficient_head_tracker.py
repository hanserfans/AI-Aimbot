"""
高效头部跟踪系统 - 优化版本
实现市面上锁头系统的核心算法
"""

import numpy as np
import time
from collections import deque
import cv2

class EfficientHeadTracker:
    """
    高效头部跟踪系统
    
    核心特性：
    1. 卡尔曼滤波预测
    2. 多帧融合
    3. 延迟补偿
    4. 平滑移动
    """
    
    def __init__(self, history_size=5, prediction_frames=2):
        """
        初始化跟踪器
        
        Args:
            history_size: 历史帧数量
            prediction_frames: 预测帧数
        """
        self.history_size = history_size
        self.prediction_frames = prediction_frames
        
        # 头部位置历史记录
        self.position_history = deque(maxlen=history_size)
        self.time_history = deque(maxlen=history_size)
        
        # 卡尔曼滤波器参数
        self.kalman_filter = None
        self.init_kalman_filter()
        
        # 移动状态
        self.is_locked = False
        self.locked_position = None
        self.lock_start_time = None
        self.lock_duration = 0.3  # 锁定持续时间（秒）
        
        # 性能统计
        self.frame_count = 0
        self.last_update_time = time.time()
        
    def init_kalman_filter(self):
        """初始化卡尔曼滤波器"""
        # 状态向量: [x, y, vx, vy] (位置和速度)
        self.kalman_filter = cv2.KalmanFilter(4, 2)
        
        # 状态转移矩阵
        dt = 1.0 / 60.0  # 假设60FPS
        self.kalman_filter.transitionMatrix = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # 测量矩阵
        self.kalman_filter.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=np.float32)
        
        # 过程噪声协方差
        self.kalman_filter.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
        
        # 测量噪声协方差
        self.kalman_filter.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.1
        
        # 后验误差协方差
        self.kalman_filter.errorCovPost = np.eye(4, dtype=np.float32)
        
        # 初始状态
        self.kalman_filter.statePre = np.zeros((4, 1), dtype=np.float32)
        self.kalman_filter.statePost = np.zeros((4, 1), dtype=np.float32)
        
    def update_head_position(self, x, y, confidence=1.0, timestamp=None):
        """
        更新头部位置
        
        Args:
            x, y: 头部坐标
            confidence: 检测置信度
            timestamp: 时间戳
        
        Returns:
            dict: 跟踪结果
        """
        if timestamp is None:
            timestamp = time.time()
            
        self.frame_count += 1
        
        # 如果处于锁定状态，检查是否应该解锁
        if self.is_locked:
            if timestamp - self.lock_start_time > self.lock_duration:
                self.unlock_position()
            else:
                # 返回锁定的位置
                return {
                    'x': self.locked_position[0],
                    'y': self.locked_position[1],
                    'predicted_x': self.locked_position[0],
                    'predicted_y': self.locked_position[1],
                    'is_locked': True,
                    'confidence': confidence
                }
        
        # 添加到历史记录
        self.position_history.append((x, y, confidence))
        self.time_history.append(timestamp)
        
        # 更新卡尔曼滤波器
        measurement = np.array([[x], [y]], dtype=np.float32)
        
        if len(self.position_history) == 1:
            # 第一帧，初始化状态
            self.kalman_filter.statePost = np.array([[x], [y], [0], [0]], dtype=np.float32)
        
        # 预测步骤
        predicted_state = self.kalman_filter.predict()
        
        # 更新步骤
        self.kalman_filter.correct(measurement)
        
        # 获取当前状态
        current_state = self.kalman_filter.statePost
        current_x, current_y = current_state[0, 0], current_state[1, 0]
        velocity_x, velocity_y = current_state[2, 0], current_state[3, 0]
        
        # 预测未来位置（补偿延迟）
        delay_compensation = 0.05  # 50ms延迟补偿
        predicted_x = current_x + velocity_x * delay_compensation
        predicted_y = current_y + velocity_y * delay_compensation
        
        return {
            'x': current_x,
            'y': current_y,
            'predicted_x': predicted_x,
            'predicted_y': predicted_y,
            'velocity_x': velocity_x,
            'velocity_y': velocity_y,
            'is_locked': False,
            'confidence': confidence
        }
    
    def lock_position(self, x=None, y=None):
        """
        锁定头部位置
        
        Args:
            x, y: 锁定的坐标，如果为None则使用当前预测位置
        """
        if x is None or y is None:
            if len(self.position_history) > 0:
                # 使用最新的预测位置
                state = self.kalman_filter.statePost
                x, y = state[0, 0], state[1, 0]
            else:
                return False
        
        self.is_locked = True
        self.locked_position = (x, y)
        self.lock_start_time = time.time()
        return True
    
    def unlock_position(self):
        """解锁头部位置"""
        self.is_locked = False
        self.locked_position = None
        self.lock_start_time = None
    
    def get_smooth_movement_path(self, target_x, target_y, current_x, current_y, steps=5):
        """
        生成平滑移动路径
        
        Args:
            target_x, target_y: 目标位置
            current_x, current_y: 当前位置
            steps: 移动步数
        
        Returns:
            list: 移动路径点列表
        """
        path = []
        
        # 计算距离和方向
        dx = target_x - current_x
        dy = target_y - current_y
        distance = np.sqrt(dx*dx + dy*dy)
        
        if distance < 1:
            return [(target_x, target_y)]
        
        # 使用贝塞尔曲线生成平滑路径
        for i in range(1, steps + 1):
            t = i / steps
            # 应用缓动函数（ease-out）
            t = 1 - (1 - t) ** 2
            
            x = current_x + dx * t
            y = current_y + dy * t
            path.append((x, y))
        
        return path
    
    def get_performance_stats(self):
        """获取性能统计信息"""
        current_time = time.time()
        elapsed = current_time - self.last_update_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        return {
            'fps': fps,
            'frame_count': self.frame_count,
            'history_size': len(self.position_history),
            'is_locked': self.is_locked,
            'lock_remaining': max(0, self.lock_duration - (current_time - self.lock_start_time)) if self.is_locked else 0
        }
    
    def draw_tracking_info(self, img, scale_factor=1.0):
        """
        在图像上绘制跟踪信息
        
        Args:
            img: 输入图像
            scale_factor: 缩放因子
        
        Returns:
            处理后的图像
        """
        if len(self.position_history) == 0:
            return img
        
        # 绘制历史轨迹
        if len(self.position_history) > 1:
            points = []
            for pos in self.position_history:
                x, y = int(pos[0] * scale_factor), int(pos[1] * scale_factor)
                points.append((x, y))
            
            # 绘制轨迹线
            for i in range(1, len(points)):
                alpha = i / len(points)  # 透明度渐变
                color = (0, int(255 * alpha), 0)
                cv2.line(img, points[i-1], points[i], color, 2)
        
        # 绘制当前位置
        if len(self.position_history) > 0:
            current_pos = self.position_history[-1]
            x, y = int(current_pos[0] * scale_factor), int(current_pos[1] * scale_factor)
            
            if self.is_locked:
                # 锁定状态 - 红色圆圈
                cv2.circle(img, (x, y), 8, (0, 0, 255), 3)
                cv2.putText(img, "LOCKED", (x + 10, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            else:
                # 正常状态 - 绿色圆圈
                cv2.circle(img, (x, y), 6, (0, 255, 0), 2)
        
        # 绘制预测位置
        if self.kalman_filter is not None and len(self.position_history) > 0:
            state = self.kalman_filter.statePost
            pred_x = int(state[0, 0] * scale_factor)
            pred_y = int(state[1, 0] * scale_factor)
            
            # 预测位置 - 蓝色十字
            cv2.line(img, (pred_x - 5, pred_y), (pred_x + 5, pred_y), (255, 0, 0), 2)
            cv2.line(img, (pred_x, pred_y - 5), (pred_x, pred_y + 5), (255, 0, 0), 2)
        
        # 绘制性能信息
        stats = self.get_performance_stats()
        info_text = f"FPS: {stats['fps']:.1f} | Frames: {stats['frame_count']}"
        cv2.putText(img, info_text, (10, img.shape[0] - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        if self.is_locked:
            lock_text = f"Lock: {stats['lock_remaining']:.1f}s"
            cv2.putText(img, lock_text, (10, img.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        return img

def create_efficient_head_tracker(history_size=5, prediction_frames=2):
    """
    创建高效头部跟踪器实例
    
    Args:
        history_size: 历史帧数量
        prediction_frames: 预测帧数
    
    Returns:
        EfficientHeadTracker: 跟踪器实例
    """
    return EfficientHeadTracker(history_size, prediction_frames)

# 使用示例
if __name__ == "__main__":
    # 创建跟踪器
    tracker = create_efficient_head_tracker()
    
    # 模拟头部位置更新
    import random
    
    for i in range(100):
        # 模拟头部移动
        x = 160 + 50 * np.sin(i * 0.1) + random.uniform(-5, 5)
        y = 160 + 30 * np.cos(i * 0.1) + random.uniform(-5, 5)
        
        # 更新位置
        result = tracker.update_head_position(x, y, confidence=0.9)
        
        print(f"Frame {i}: Current({result['x']:.1f}, {result['y']:.1f}) "
              f"Predicted({result['predicted_x']:.1f}, {result['predicted_y']:.1f})")
        
        # 模拟锁定
        if i == 50:
            tracker.lock_position()
            print("Position locked!")
        
        time.sleep(0.016)  # 模拟60FPS
    
    # 显示性能统计
    stats = tracker.get_performance_stats()
    print(f"\nPerformance Stats: {stats}")
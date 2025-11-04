#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时头部位置跟踪系统
实现移动锁定机制，确保一次移动期间不被新的目标打断
同时提供头部位置变化的实时绘制和可视化
"""

import time
import threading
import numpy as np
import cv2
from typing import Optional, Dict, List, Tuple, Any
from collections import deque
import math

class RealtimeHeadPositionTracker:
    """实时头部位置跟踪系统"""
    
    def __init__(self, 
                 movement_lock_duration: float = 0.3,  # 移动锁定持续时间（秒）
                 position_history_size: int = 50,      # 位置历史记录大小
                 visualization_enabled: bool = True):   # 是否启用可视化
        """
        初始化实时头部位置跟踪系统
        
        Args:
            movement_lock_duration: 移动锁定持续时间（秒）
            position_history_size: 位置历史记录大小
            visualization_enabled: 是否启用可视化
        """
        self.movement_lock_duration = movement_lock_duration
        self.position_history_size = position_history_size
        self.visualization_enabled = visualization_enabled
        
        # 移动锁定状态
        self.is_movement_locked = False
        self.movement_start_time = 0.0
        self.locked_target_position = None
        self.movement_lock = threading.Lock()
        
        # 头部位置历史记录
        self.position_history = deque(maxlen=position_history_size)
        self.current_head_position = None
        self.target_head_position = None
        
        # 移动轨迹记录
        self.movement_trajectory = deque(maxlen=100)
        self.is_moving = False
        self.movement_progress = 0.0
        
        # 统计信息
        self.stats = {
            'total_movements': 0,
            'locked_movements': 0,
            'interrupted_movements': 0,
            'avg_movement_duration': 0.0,
            'position_updates': 0
        }
        
        print(f"[INFO] 🎯 实时头部位置跟踪系统初始化完成")
        print(f"   • 移动锁定持续时间: {movement_lock_duration*1000:.0f}ms")
        print(f"   • 位置历史记录大小: {position_history_size}")
        print(f"   • 可视化功能: {'启用' if visualization_enabled else '禁用'}")
    
    def update_head_position(self, x: float, y: float, confidence: float = 1.0, 
                           frame_timestamp: float = None) -> bool:
        """
        更新头部位置
        
        Args:
            x: 头部X坐标
            y: 头部Y坐标
            confidence: 检测置信度
            frame_timestamp: 帧时间戳
            
        Returns:
            bool: 是否接受了位置更新
        """
        current_time = time.time()
        if frame_timestamp is None:
            frame_timestamp = current_time
        
        # 检查移动锁定状态
        with self.movement_lock:
            if self.is_movement_locked:
                # 检查锁定是否过期
                if current_time - self.movement_start_time > self.movement_lock_duration:
                    self._unlock_movement()
                    print(f"[MOVEMENT_LOCK] 🔓 移动锁定已过期，解除锁定")
                else:
                    # 移动仍在锁定期间，拒绝位置更新
                    remaining_time = self.movement_lock_duration - (current_time - self.movement_start_time)
                    print(f"[MOVEMENT_LOCK] 🔒 移动锁定中，拒绝位置更新 (剩余: {remaining_time*1000:.0f}ms)")
                    return False
        
        # 记录位置历史
        position_data = {
            'x': x,
            'y': y,
            'confidence': confidence,
            'timestamp': frame_timestamp,
            'system_time': current_time
        }
        
        self.position_history.append(position_data)
        self.current_head_position = position_data
        self.stats['position_updates'] += 1
        
        print(f"[HEAD_TRACKER] 📍 头部位置更新: ({x:.1f}, {y:.1f}), 置信度: {confidence:.2f}")
        
        return True
    
    def start_movement_to_target(self, target_x: float, target_y: float) -> Dict[str, Any]:
        """
        开始移动到目标位置，启动移动锁定
        
        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            
        Returns:
            Dict: 移动信息
        """
        current_time = time.time()
        
        with self.movement_lock:
            # 如果已经在移动中，记录为中断
            if self.is_movement_locked:
                self.stats['interrupted_movements'] += 1
                print(f"[MOVEMENT_LOCK] ⚠️ 中断当前移动，开始新的移动")
            
            # 启动移动锁定
            self.is_movement_locked = True
            self.movement_start_time = current_time
            self.locked_target_position = {'x': target_x, 'y': target_y}
            self.target_head_position = self.locked_target_position.copy()
            
            # 记录移动轨迹起点
            if self.current_head_position:
                start_pos = {
                    'x': self.current_head_position['x'],
                    'y': self.current_head_position['y'],
                    'timestamp': current_time,
                    'type': 'movement_start'
                }
                self.movement_trajectory.append(start_pos)
            
            # 记录目标位置
            target_pos = {
                'x': target_x,
                'y': target_y,
                'timestamp': current_time,
                'type': 'movement_target'
            }
            self.movement_trajectory.append(target_pos)
            
            self.is_moving = True
            self.movement_progress = 0.0
            self.stats['total_movements'] += 1
            self.stats['locked_movements'] += 1
        
        print(f"[MOVEMENT_LOCK] 🔒 开始移动锁定: 目标({target_x:.1f}, {target_y:.1f}), 持续时间: {self.movement_lock_duration*1000:.0f}ms")
        
        return {
            'locked_target': self.locked_target_position.copy(),
            'lock_duration': self.movement_lock_duration,
            'movement_id': self.stats['total_movements']
        }
    
    def on_movement_start(self):
        """移动开始时的回调函数"""
        if self.locked_target_position:
            print(f"[MOVEMENT_LOCK] 🚀 移动开始执行: 目标({self.locked_target_position['x']:.1f}, {self.locked_target_position['y']:.1f})")
    
    def on_movement_complete(self):
        """移动完成时的回调函数"""
        current_time = time.time()
        
        with self.movement_lock:
            if self.is_movement_locked:
                movement_duration = current_time - self.movement_start_time
                
                # 更新平均移动持续时间
                if self.stats['total_movements'] > 0:
                    self.stats['avg_movement_duration'] = (
                        (self.stats['avg_movement_duration'] * (self.stats['total_movements'] - 1) + movement_duration) 
                        / self.stats['total_movements']
                    )
                
                # 记录移动完成
                if self.locked_target_position:
                    complete_pos = {
                        'x': self.locked_target_position['x'],
                        'y': self.locked_target_position['y'],
                        'timestamp': current_time,
                        'type': 'movement_complete',
                        'duration': movement_duration
                    }
                    self.movement_trajectory.append(complete_pos)
                
                print(f"[MOVEMENT_LOCK] ✅ 移动完成: 持续时间 {movement_duration*1000:.0f}ms")
                
                # 延迟解锁，确保移动完全完成
                threading.Timer(0.05, self._unlock_movement).start()
            
            self.is_moving = False
            self.movement_progress = 1.0
    
    def _unlock_movement(self):
        """解除移动锁定"""
        with self.movement_lock:
            self.is_movement_locked = False
            self.locked_target_position = None
            self.target_head_position = None
            self.movement_start_time = 0.0
            
        print(f"[MOVEMENT_LOCK] 🔓 移动锁定已解除")
    
    def get_current_target_position(self) -> Optional[Dict[str, float]]:
        """
        获取当前目标位置
        
        Returns:
            Dict: 当前目标位置，如果锁定则返回锁定的位置，否则返回最新位置
        """
        with self.movement_lock:
            if self.is_movement_locked and self.locked_target_position:
                return self.locked_target_position.copy()
            elif self.current_head_position:
                return {
                    'x': self.current_head_position['x'],
                    'y': self.current_head_position['y']
                }
            else:
                return None
    
    def is_locked(self) -> bool:
        """检查是否处于移动锁定状态"""
        with self.movement_lock:
            return self.is_movement_locked
    
    def get_position_history(self, count: int = None) -> List[Dict]:
        """
        获取位置历史记录
        
        Args:
            count: 返回的记录数量，None表示返回所有
            
        Returns:
            List: 位置历史记录
        """
        if count is None:
            return list(self.position_history)
        else:
            return list(self.position_history)[-count:]
    
    def get_movement_trajectory(self) -> List[Dict]:
        """获取移动轨迹"""
        return list(self.movement_trajectory)
    
    def draw_position_visualization(self, img: np.ndarray, 
                                  scale_factor: float = 1.0) -> np.ndarray:
        """
        在图像上绘制头部位置可视化
        
        Args:
            img: 输入图像
            scale_factor: 缩放因子
            
        Returns:
            np.ndarray: 绘制后的图像
        """
        if not self.visualization_enabled:
            return img
        
        img_vis = img.copy()
        
        # 绘制位置历史轨迹
        if len(self.position_history) > 1:
            points = []
            for pos in self.position_history:
                x = int(pos['x'] * scale_factor)
                y = int(pos['y'] * scale_factor)
                points.append((x, y))
            
            # 绘制轨迹线（渐变色）
            for i in range(1, len(points)):
                alpha = i / len(points)  # 透明度渐变
                color = (0, int(255 * alpha), int(255 * (1 - alpha)))  # 蓝到红渐变
                thickness = max(1, int(3 * alpha))  # 线条粗细渐变
                cv2.line(img_vis, points[i-1], points[i], color, thickness)
        
        # 绘制当前头部位置
        if self.current_head_position:
            x = int(self.current_head_position['x'] * scale_factor)
            y = int(self.current_head_position['y'] * scale_factor)
            
            # 当前位置圆圈（绿色）
            cv2.circle(img_vis, (x, y), 8, (0, 255, 0), 2)
            cv2.circle(img_vis, (x, y), 3, (0, 255, 0), -1)
            
            # 添加位置标签
            cv2.putText(img_vis, f"Current ({x}, {y})", 
                       (x + 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (0, 255, 0), 1)
        
        # 绘制目标头部位置（如果正在移动）
        if self.target_head_position and self.is_moving:
            x = int(self.target_head_position['x'] * scale_factor)
            y = int(self.target_head_position['y'] * scale_factor)
            
            # 目标位置圆圈（红色）
            cv2.circle(img_vis, (x, y), 10, (0, 0, 255), 2)
            cv2.circle(img_vis, (x, y), 4, (0, 0, 255), -1)
            
            # 添加目标标签
            cv2.putText(img_vis, f"Target ({x}, {y})", 
                       (x + 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (0, 0, 255), 1)
            
            # 绘制移动方向箭头
            if self.current_head_position:
                start_x = int(self.current_head_position['x'] * scale_factor)
                start_y = int(self.current_head_position['y'] * scale_factor)
                cv2.arrowedLine(img_vis, (start_x, start_y), (x, y), 
                               (255, 255, 0), 2, tipLength=0.3)
        
        # 绘制锁定状态指示器
        if self.is_movement_locked:
            # 在左上角绘制锁定状态
            lock_text = "MOVEMENT LOCKED"
            remaining_time = self.movement_lock_duration - (time.time() - self.movement_start_time)
            if remaining_time > 0:
                lock_text += f" ({remaining_time:.1f}s)"
            
            cv2.rectangle(img_vis, (10, 10), (300, 50), (0, 0, 255), -1)
            cv2.putText(img_vis, lock_text, (15, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # 绘制移动轨迹（如果有）
        if len(self.movement_trajectory) > 1:
            traj_points = []
            for traj in self.movement_trajectory:
                x = int(traj['x'] * scale_factor)
                y = int(traj['y'] * scale_factor)
                traj_points.append((x, y))
            
            # 绘制移动轨迹（黄色虚线）
            for i in range(1, len(traj_points)):
                if i % 2 == 0:  # 虚线效果
                    cv2.line(img_vis, traj_points[i-1], traj_points[i], 
                            (0, 255, 255), 2)
        
        # 绘制统计信息
        stats_y = img_vis.shape[0] - 100
        cv2.putText(img_vis, f"Total Movements: {self.stats['total_movements']}", 
                   (10, stats_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img_vis, f"Locked Movements: {self.stats['locked_movements']}", 
                   (10, stats_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img_vis, f"Position History: {len(self.position_history)}", 
                   (10, stats_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return img_vis
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.movement_lock:
            stats = self.stats.copy()
            stats['is_locked'] = self.is_movement_locked
            stats['position_history_size'] = len(self.position_history)
            stats['movement_trajectory_size'] = len(self.movement_trajectory)
            
            if self.is_movement_locked:
                stats['current_lock_duration'] = time.time() - self.movement_start_time
                stats['lock_remaining'] = max(0, self.movement_lock_duration - stats['current_lock_duration'])
            
            return stats
    
    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()
        print(f"\n🎯 实时头部位置跟踪系统统计:")
        print(f"   • 总移动次数: {stats['total_movements']}")
        print(f"   • 锁定移动次数: {stats['locked_movements']}")
        print(f"   • 中断移动次数: {stats['interrupted_movements']}")
        print(f"   • 平均移动持续时间: {stats['avg_movement_duration']*1000:.0f}ms")
        print(f"   • 位置更新次数: {stats['position_updates']}")
        print(f"   • 当前锁定状态: {'是' if stats['is_locked'] else '否'}")
        
        if stats['is_locked']:
            print(f"   • 当前锁定持续时间: {stats['current_lock_duration']*1000:.0f}ms")
            print(f"   • 锁定剩余时间: {stats['lock_remaining']*1000:.0f}ms")


def create_realtime_head_position_tracker(**kwargs):
    """创建实时头部位置跟踪系统"""
    return RealtimeHeadPositionTracker(**kwargs)


if __name__ == "__main__":
    # 测试实时头部位置跟踪系统
    tracker = create_realtime_head_position_tracker(
        movement_lock_duration=0.5,
        position_history_size=30,
        visualization_enabled=True
    )
    
    print("[INFO] 测试实时头部位置跟踪系统...")
    
    # 模拟头部位置更新
    test_positions = [
        (100, 100), (105, 102), (110, 105), (115, 108), (120, 110)
    ]
    
    for i, (x, y) in enumerate(test_positions):
        print(f"\n--- 测试位置 {i+1} ---")
        
        # 更新头部位置
        accepted = tracker.update_head_position(x, y, confidence=0.9)
        print(f"位置更新 ({x}, {y}): {'接受' if accepted else '拒绝'}")
        
        # 第一个位置时开始移动
        if i == 0:
            movement_info = tracker.start_movement_to_target(x + 50, y + 30)
            print(f"开始移动到目标: {movement_info}")
            
            # 模拟移动开始
            tracker.on_movement_start()
        
        # 模拟时间间隔
        time.sleep(0.1)
        
        # 获取当前目标位置
        target_pos = tracker.get_current_target_position()
        if target_pos:
            print(f"当前目标位置: ({target_pos['x']:.1f}, {target_pos['y']:.1f})")
    
    # 模拟移动完成
    time.sleep(0.2)
    tracker.on_movement_complete()
    
    # 继续测试位置更新
    time.sleep(0.1)
    final_accepted = tracker.update_head_position(130, 115, confidence=0.95)
    print(f"\n最终位置更新: {'接受' if final_accepted else '拒绝'}")
    
    # 打印统计信息
    tracker.print_statistics()
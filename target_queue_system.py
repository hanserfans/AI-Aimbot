"""
目标点队列系统 - 实现稳定的鼠标移动策略
解决实时跟踪导致的频繁方向改变和移动抖动问题
"""

import time
import math
from collections import deque
from typing import Tuple, Optional, List


class TargetQueueSystem:
    """
    目标点队列系统
    
    核心思想：
    1. 鼠标移动到固定的目标点，而不是实时跟随最新检测位置
    2. 只有到达当前目标点后，才会更新到下一个目标点
    3. 维护一个目标点历史队列，确保移动轨迹稳定
    """
    
    def __init__(self, 
                 arrival_threshold: float = 3.0,      # 到达阈值（像素）
                 max_queue_size: int = 5,             # 最大队列长度
                 min_distance_threshold: float = 5.0,  # 最小距离阈值，避免微小移动
                 target_update_interval: float = 0.1,  # 目标更新间隔（秒）
                 movement_timeout: float = 2.0):       # 移动超时时间（秒）
        
        self.arrival_threshold = arrival_threshold
        self.max_queue_size = max_queue_size
        self.min_distance_threshold = min_distance_threshold
        self.target_update_interval = target_update_interval
        self.movement_timeout = movement_timeout
        
        # 目标点队列
        self.target_queue = deque(maxlen=max_queue_size)
        
        # 当前状态
        self.current_target: Optional[Tuple[float, float]] = None
        self.current_mouse_pos: Tuple[float, float] = (0, 0)
        self.is_moving: bool = False
        self.movement_start_time: float = 0
        self.last_target_update_time: float = 0
        
        # 统计信息
        self.targets_reached: int = 0
        self.total_movements: int = 0
        self.average_arrival_time: float = 0
        
        print("🎯 目标点队列系统已初始化")
        print(f"   - 到达阈值: {arrival_threshold}px")
        print(f"   - 队列大小: {max_queue_size}")
        print(f"   - 最小移动距离: {min_distance_threshold}px")
    
    def add_target_position(self, x: float, y: float) -> bool:
        """
        添加新的目标位置到队列
        
        Args:
            x, y: 目标位置坐标
            
        Returns:
            bool: 是否成功添加目标
        """
        current_time = time.time()
        
        # 检查更新间隔，避免过于频繁的目标更新
        if current_time - self.last_target_update_time < self.target_update_interval:
            return False
        
        # 如果当前有目标，检查距离是否足够大
        if self.current_target:
            distance = self._calculate_distance(self.current_target, (x, y))
            if distance < self.min_distance_threshold:
                return False
        
        # 检查与队列中最后一个目标的距离
        if self.target_queue:
            last_target = self.target_queue[-1]
            distance = self._calculate_distance(last_target, (x, y))
            if distance < self.min_distance_threshold:
                return False
        
        # 添加到队列
        self.target_queue.append((x, y))
        self.last_target_update_time = current_time
        
        print(f"🎯 添加新目标: ({x:.1f}, {y:.1f}), 队列长度: {len(self.target_queue)}")
        return True
    
    def update_mouse_position(self, x: float, y: float):
        """
        更新当前鼠标位置
        
        Args:
            x, y: 当前鼠标位置
        """
        self.current_mouse_pos = (x, y)
    
    def get_next_target(self) -> Optional[Tuple[float, float]]:
        """
        获取下一个移动目标
        
        Returns:
            Optional[Tuple[float, float]]: 目标坐标，如果没有目标则返回None
        """
        current_time = time.time()
        
        # 检查当前移动是否超时
        if self.is_moving and (current_time - self.movement_start_time) > self.movement_timeout:
            print(f"⚠️ 移动超时，强制切换到下一个目标")
            self._complete_current_movement()
        
        # 如果当前没有目标，从队列中获取
        if not self.current_target and self.target_queue:
            self.current_target = self.target_queue.popleft()
            self.is_moving = True
            self.movement_start_time = current_time
            self.total_movements += 1
            print(f"🎯 开始移动到新目标: {self.current_target}")
        
        # 检查是否已到达当前目标
        if self.current_target and self._has_arrived():
            print(f"✅ 已到达目标: {self.current_target}")
            self._complete_current_movement()
            
            # 立即获取下一个目标
            if self.target_queue:
                self.current_target = self.target_queue.popleft()
                self.is_moving = True
                self.movement_start_time = current_time
                self.total_movements += 1
                print(f"🎯 立即移动到下一个目标: {self.current_target}")
        
        return self.current_target
    
    def _has_arrived(self) -> bool:
        """
        检查是否已到达当前目标
        
        Returns:
            bool: 是否已到达
        """
        if not self.current_target:
            return False
        
        distance = self._calculate_distance(self.current_mouse_pos, self.current_target)
        return distance <= self.arrival_threshold
    
    def _complete_current_movement(self):
        """
        完成当前移动
        """
        if self.is_moving:
            movement_time = time.time() - self.movement_start_time
            self.targets_reached += 1
            
            # 更新平均到达时间
            if self.targets_reached == 1:
                self.average_arrival_time = movement_time
            else:
                self.average_arrival_time = (self.average_arrival_time * (self.targets_reached - 1) + movement_time) / self.targets_reached
        
        self.current_target = None
        self.is_moving = False
        self.movement_start_time = 0
    
    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """
        计算两点之间的距离
        
        Args:
            pos1, pos2: 两个位置坐标
            
        Returns:
            float: 距离
        """
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def is_ready_to_fire(self) -> bool:
        """
        检查是否准备好开火
        
        当鼠标到达目标点时，是最佳的开火时机
        
        Returns:
            bool: 是否准备好开火
        """
        return self.current_target is not None and self._has_arrived()
    
    def get_movement_direction(self) -> Optional[Tuple[float, float]]:
        """
        获取移动方向向量（单位向量）
        
        Returns:
            Optional[Tuple[float, float]]: 移动方向，如果没有目标则返回None
        """
        if not self.current_target:
            return None
        
        dx = self.current_target[0] - self.current_mouse_pos[0]
        dy = self.current_target[1] - self.current_mouse_pos[1]
        
        distance = math.sqrt(dx*dx + dy*dy)
        if distance == 0:
            return (0, 0)
        
        return (dx / distance, dy / distance)
    
    def get_remaining_distance(self) -> float:
        """
        获取到当前目标的剩余距离
        
        Returns:
            float: 剩余距离
        """
        if not self.current_target:
            return 0
        
        return self._calculate_distance(self.current_mouse_pos, self.current_target)
    
    def clear_queue(self):
        """
        清空目标队列
        """
        self.target_queue.clear()
        self.current_target = None
        self.is_moving = False
        print("🗑️ 目标队列已清空")
    
    def get_status_info(self) -> dict:
        """
        获取系统状态信息
        
        Returns:
            dict: 状态信息
        """
        return {
            'current_target': self.current_target,
            'queue_size': len(self.target_queue),
            'is_moving': self.is_moving,
            'targets_reached': self.targets_reached,
            'total_movements': self.total_movements,
            'average_arrival_time': self.average_arrival_time,
            'remaining_distance': self.get_remaining_distance(),
            'ready_to_fire': self.is_ready_to_fire()
        }
    
    def print_status(self):
        """
        打印当前状态
        """
        status = self.get_status_info()
        print(f"🎯 目标队列系统状态:")
        print(f"   当前目标: {status['current_target']}")
        print(f"   队列长度: {status['queue_size']}")
        print(f"   正在移动: {status['is_moving']}")
        print(f"   已到达目标数: {status['targets_reached']}")
        print(f"   平均到达时间: {status['average_arrival_time']:.2f}s")
        print(f"   剩余距离: {status['remaining_distance']:.1f}px")
        print(f"   准备开火: {status['ready_to_fire']}")


def create_target_queue_system(arrival_threshold: float = 3.0,
                              max_queue_size: int = 5,
                              min_distance_threshold: float = 5.0,
                              target_update_interval: float = 0.1,
                              movement_timeout: float = 2.0) -> TargetQueueSystem:
    """
    创建目标点队列系统实例
    
    Args:
        arrival_threshold: 到达阈值（像素）
        max_queue_size: 最大队列长度
        min_distance_threshold: 最小距离阈值
        target_update_interval: 目标更新间隔（秒）
        movement_timeout: 移动超时时间（秒）
        
    Returns:
        TargetQueueSystem: 目标队列系统实例
    """
    return TargetQueueSystem(
        arrival_threshold=arrival_threshold,
        max_queue_size=max_queue_size,
        min_distance_threshold=min_distance_threshold,
        target_update_interval=target_update_interval,
        movement_timeout=movement_timeout
    )


def get_target_queue_system():
    """
    获取目标队列系统模块
    
    Returns:
        module: 目标队列系统模块
    """
    import sys
    return sys.modules[__name__]


# 全局变量，用于模块级别的可用性检查
TARGET_QUEUE_SYSTEM_AVAILABLE = True

if __name__ == "__main__":
    # 测试代码
    print("🧪 测试目标点队列系统")
    
    # 创建系统实例
    target_system = create_target_queue_system(
        arrival_threshold=2.0,
        max_queue_size=3,
        min_distance_threshold=3.0
    )
    
    # 模拟鼠标位置和目标添加
    target_system.update_mouse_position(100, 100)
    
    # 添加一些目标
    target_system.add_target_position(120, 110)
    target_system.add_target_position(140, 120)
    target_system.add_target_position(160, 130)
    
    # 模拟移动过程
    for i in range(10):
        target = target_system.get_next_target()
        if target:
            print(f"步骤 {i+1}: 移动到 {target}")
            # 模拟鼠标逐渐接近目标
            current_x, current_y = target_system.current_mouse_pos
            target_x, target_y = target
            new_x = current_x + (target_x - current_x) * 0.3
            new_y = current_y + (target_y - current_y) * 0.3
            target_system.update_mouse_position(new_x, new_y)
            
            if target_system.is_ready_to_fire():
                print("🔥 准备开火！")
        else:
            print(f"步骤 {i+1}: 没有目标")
        
        time.sleep(0.1)
    
    target_system.print_status()
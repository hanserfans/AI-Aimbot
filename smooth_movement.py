"""
平滑移动算法模块
模拟人手操作，减少移动误差
"""

import time
import math
import random
from typing import Tuple, List


class SmoothMovement:
    """平滑移动算法类"""
    
    def __init__(self):
        # 移动参数
        self.min_step_size = 1  # 最小步长
        self.max_step_size = 2  # 最大步长（进一步减小以避免锁头感, 从3改为2）
        self.base_delay = 0.1# 基础延迟(增加延迟, 从5ms改为8ms)
        self.max_delay = 0.025   # 最大延迟(增加延迟, 从15ms改为25ms)
        
        # 人手模拟参数
        self.acceleration_ratio = 0.2 # 加速阶段比例 (从0.3改为0.2)
        self.deceleration_ratio = 0.7# 减速阶段比例 (从0.4改为0.5)
        self.steady_ratio = 0.1     # 匀速阶段比例
        
        # 随机性参数（大幅减少以提高精度）
        self.path_randomness = 0.02    # 路径随机性（从0.15减少到0.02）
        self.timing_randomness = 0.05  # 时间随机性（从0.2减少到0.05）
    
    def calculate_movement_path(self, dx: int, dy: int) -> List[Tuple[int, int, float]]:
        """
        计算平滑移动路径
        
        Args:
            dx, dy: 目标移动距离
            
        Returns:
            List[Tuple[int, int, float]]: 移动步骤列表 (step_x, step_y, delay)
        """
        total_distance = math.sqrt(dx*dx + dy*dy)
        
        # 如果距离太小，直接移动
        if total_distance <= self.min_step_size:
            return [(dx, dy, self.base_delay)]
        
        # 计算步数（增加步数以提高平滑度）
        steps = max(3, min(int(total_distance / 1.5), 15))  # 3-15步, 增加步数使移动更平滑
        
        # 生成移动路径
        path = []
        accumulated_x = 0.0
        accumulated_y = 0.0
        
        for i in range(steps):
            # 计算进度比例
            progress = (i + 1) / steps
            
            # 计算速度因子（模拟加速-匀速-减速）
            speed_factor = self._calculate_speed_factor(progress)
            
            # 计算目标位置（使用浮点数保持精度）
            target_x = dx * progress
            target_y = dy * progress
            
            # 只在中间步骤添加极小的随机性
            if i > 0 and i < steps - 1 and total_distance > 10:  # 只对较长距离添加随机性
                randomness = self.path_randomness * min(2, total_distance / steps)
                target_x += random.uniform(-randomness, randomness)
                target_y += random.uniform(-randomness, randomness)
            
            # 计算当前步骤的移动量
            step_x = target_x - accumulated_x
            step_y = target_y - accumulated_y
            
            # 限制步长
            step_distance = math.sqrt(step_x*step_x + step_y*step_y)
            if step_distance > self.max_step_size:
                scale = self.max_step_size / step_distance
                step_x = step_x * scale
                step_y = step_y * scale
            
            # 转换为整数
            step_x_int = int(round(step_x))
            step_y_int = int(round(step_y))
            
            # 计算延迟（基于速度因子）
            base_delay = self.base_delay + (self.max_delay - self.base_delay) / speed_factor
            delay = base_delay * (1 + random.uniform(-self.timing_randomness, self.timing_randomness))
            delay = max(0.003, min(delay, self.max_delay))  # 限制延迟范围
            
            if step_x_int != 0 or step_y_int != 0:  # 只添加有效移动
                path.append((step_x_int, step_y_int, delay))
                accumulated_x += step_x_int
                accumulated_y += step_y_int
        
        # 确保最终精确到达目标位置
        final_x = dx - int(accumulated_x)
        final_y = dy - int(accumulated_y)
        if final_x != 0 or final_y != 0:
            path.append((final_x, final_y, self.base_delay))
        
        return path
    
    def _calculate_speed_factor(self, progress: float) -> float:
        """
        计算速度因子（模拟人手加速-匀速-减速）
        
        Args:
            progress: 移动进度 (0-1)
            
        Returns:
            float: 速度因子
        """
        if progress <= self.acceleration_ratio:
            # 加速阶段：从0.2到1.0 (降低初始速度)
            t = progress / self.acceleration_ratio
            return 0.2 + 0.8 * (t * t)  # 二次加速 (从0.3 + 0.7*t*t 改为 0.2 + 0.8*t*t)
        elif progress <= (self.acceleration_ratio + self.steady_ratio):
            # 匀速阶段：保持1.0
            return 1.0
        else:
            # 减速阶段：从1.0到0.5
            t = (progress - self.acceleration_ratio - self.steady_ratio) / self.deceleration_ratio
            return 1.0 - 0.5 * (t * t)  # 二次减速
    
    def calculate_total_time(self, dx: int, dy: int) -> float:
        """
        计算移动总时间
        
        Args:
            dx, dy: 移动距离
            
        Returns:
            float: 预计移动时间（秒）
        """
        path = self.calculate_movement_path(dx, dy)
        return sum(delay for _, _, delay in path)
    
    def get_movement_stats(self, dx: int, dy: int) -> dict:
        """
        获取移动统计信息
        
        Args:
            dx, dy: 移动距离
            
        Returns:
            dict: 移动统计信息
        """
        path = self.calculate_movement_path(dx, dy)
        total_distance = math.sqrt(dx*dx + dy*dy)
        total_time = sum(delay for _, _, delay in path)
        
        return {
            'total_distance': total_distance,
            'total_steps': len(path),
            'total_time': total_time,
            'average_speed': total_distance / total_time if total_time > 0 else 0,
            'path_preview': path[:5]  # 前5步预览
        }


# 全局实例
smooth_movement = SmoothMovement()


def get_smooth_movement_path(dx: int, dy: int) -> List[Tuple[int, int, float]]:
    """
    获取平滑移动路径的便捷函数
    
    Args:
        dx, dy: 移动距离
        
    Returns:
        List[Tuple[int, int, float]]: 移动路径
    """
    return smooth_movement.calculate_movement_path(dx, dy)


if __name__ == "__main__":
    # 测试平滑移动算法
    print("平滑移动算法测试")
    print("=" * 50)
    
    test_movements = [
        (10, 0),   # 水平移动
        (0, 15),   # 垂直移动
        (20, 20),  # 对角移动
        (50, 30),  # 长距离移动
        (3, 2),    # 短距离移动
    ]
    
    for dx, dy in test_movements:
        print(f"\n测试移动: ({dx}, {dy})")
        stats = smooth_movement.get_movement_stats(dx, dy)
        print(f"总距离: {stats['total_distance']:.1f}")
        print(f"步数: {stats['total_steps']}")
        print(f"总时间: {stats['total_time']:.3f}秒")
        print(f"平均速度: {stats['average_speed']:.1f} 像素/秒")
        print(f"路径预览: {stats['path_preview']}")
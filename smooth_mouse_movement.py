"""
平滑鼠标移动算法
模拟人手移动：先大幅度移动到目标附近，再进行微调
"""

import time
import math
import random
from typing import Tuple, List, Callable


class SmoothMouseMovement:
    """人性化鼠标移动算法"""
    
    def __init__(self, move_function: Callable[[float, float], bool]):
        """
        初始化平滑移动系统
        
        Args:
            move_function: 底层鼠标移动函数，接受(x, y)参数，返回bool表示成功/失败
        """
        self.move_function = move_function
        
        # 移动参数配置 - 优化速度和平滑度
        self.initial_move_ratio = 0.75  # 初始大幅度移动占总距离的比例（从0.95降低到0.75）
        self.micro_adjustment_steps = 3  # 微调步数（从1增加到3）
        self.step_delay_base = 0.008    # 基础延迟时间(秒)（从0增加到0.008）
        self.step_delay_variance = 0.005 # 延迟时间随机变化范围（从0增加到0.005）
        
        # 距离阈值 - 调整阈值以增加平滑度
        self.large_movement_threshold = 50 # 降低阈值（从80降低到50），增加分步移动
        self.micro_adjustment_threshold = 5 # 提高阈值（从1增加到3），减少直接移动
        
    def calculate_distance(self, x: float, y: float) -> float:
        """计算移动距离"""
        return math.sqrt(x * x + y * y)
    
    def add_human_variance(self, value: float, variance_ratio: float = 0.05) -> float:
        """添加人性化的随机变化"""
        variance = value * variance_ratio
        return value + random.uniform(-variance, variance)
    
    def calculate_movement_steps(self, target_x: float, target_y: float) -> List[Tuple[float, float]]:
        """
        计算移动步骤
        
        Args:
            target_x: 目标X坐标偏移
            target_y: 目标Y坐标偏移
            
        Returns:
            移动步骤列表，每个元素为(x, y)偏移
        """
        total_distance = self.calculate_distance(target_x, target_y)
        
        # 如果距离很小，直接移动
        if total_distance <= self.micro_adjustment_threshold:
            return [(target_x, target_y)]
        
        # 如果距离不大，使用简单的两步移动
        if total_distance <= self.large_movement_threshold:
            # 第一步移动80%
            first_ratio = 0.8
            first_x = target_x * first_ratio
            first_y = target_y * first_ratio
            
            # 第二步移动剩余部分
            second_x = target_x - first_x
            second_y = target_y - first_y
            
            return [(first_x, first_y), (second_x, second_y)]
        
        # 大距离移动：使用多步移动模拟人手行为
        steps = []
        
        # 第一步：大幅度移动到目标附近
        initial_x = target_x * self.initial_move_ratio
        initial_y = target_y * self.initial_move_ratio
        
        # 添加轻微的人性化偏差
        initial_x = self.add_human_variance(initial_x, 0.03)
        initial_y = self.add_human_variance(initial_y, 0.03)
        
        steps.append((initial_x, initial_y))
        
        # 计算剩余距离
        remaining_x = target_x - initial_x
        remaining_y = target_y - initial_y
        
        # 微调步骤：将剩余距离分成几个小步骤
        for i in range(self.micro_adjustment_steps):
            if i == self.micro_adjustment_steps - 1:
                # 最后一步：移动到精确位置
                step_x = remaining_x
                step_y = remaining_y
            else:
                # 中间步骤：逐步接近目标
                progress = (i + 1) / self.micro_adjustment_steps
                step_x = remaining_x * progress - sum(step[0] for step in steps[1:])
                step_y = remaining_y * progress - sum(step[1] for step in steps[1:])
                
                # 添加微小的人性化变化
                step_x = self.add_human_variance(step_x, 0.08)
                step_y = self.add_human_variance(step_y, 0.08)
            
            steps.append((step_x, step_y))
            
            # 更新剩余距离
            remaining_x -= step_x
            remaining_y -= step_y
        
        return steps
    
    def get_step_delay(self, step_index: int, total_steps: int, distance: float) -> float:
        """
        计算步骤间的延迟时间
        
        Args:
            step_index: 当前步骤索引
            total_steps: 总步骤数
            distance: 当前步骤的移动距离
            
        Returns:
            延迟时间(秒)
        """
        # 基础延迟
        base_delay = self.step_delay_base
        
        # 根据移动距离调整延迟
        distance_factor = min(distance / 100, 1.0)  # 距离越大延迟越长
        
        # 第一步（大幅度移动）后需要稍长的延迟
        if step_index == 0 and total_steps > 1:
            base_delay *= 1.5
        
        # 微调步骤使用较短延迟
        if step_index > 0:
            base_delay *= 0.7
        
        # 添加随机变化，模拟人手的不规律性
        delay = base_delay * (1 + distance_factor * 0.3)
        delay += random.uniform(-self.step_delay_variance, self.step_delay_variance)
        
        return max(delay, 0.001)  # 确保延迟不为负数
    
    def smooth_move_to_target(self, target_x: float, target_y: float) -> bool:
        """
        平滑移动到目标位置
        
        Args:
            target_x: 目标X坐标偏移
            target_y: 目标Y坐标偏移
            
        Returns:
            是否成功完成移动
        """
        # 计算移动步骤
        steps = self.calculate_movement_steps(target_x, target_y)
        
        print(f"[SMOOTH_MOVE] 目标距离: {self.calculate_distance(target_x, target_y):.1f}, 分解为 {len(steps)} 步")
        
        # 执行每个移动步骤
        for i, (step_x, step_y) in enumerate(steps):
            step_distance = self.calculate_distance(step_x, step_y)
            
            # 跳过过小的移动
            if step_distance < 0.1:
                continue
            
            print(f"[SMOOTH_MOVE] 步骤 {i+1}/{len(steps)}: ({step_x:.1f}, {step_y:.1f}), 距离: {step_distance:.1f}")
            
            # 执行移动
            success = self.move_function(step_x, step_y)
            if not success:
                print(f"[SMOOTH_MOVE] 步骤 {i+1} 移动失败")
                return False
            
            # 步骤间延迟（除了最后一步）
            if i < len(steps) - 1:
                delay = self.get_step_delay(i, len(steps), step_distance)
                time.sleep(delay)
        
        print(f"[SMOOTH_MOVE] 平滑移动完成")
        return True


def create_smooth_movement_system(move_function: Callable[[float, float], bool]) -> SmoothMouseMovement:
    """
    创建平滑移动系统的工厂函数
    
    Args:
        move_function: 底层鼠标移动函数
        
    Returns:
        配置好的平滑移动系统实例
    """
    return SmoothMouseMovement(move_function)


# 测试函数
def test_smooth_movement():
    """测试平滑移动算法"""
    
    def mock_move_function(x: float, y: float) -> bool:
        """模拟移动函数"""
        print(f"  -> 执行移动: ({x:.1f}, {y:.1f})")
        return True
    
    # 创建平滑移动系统
    smooth_mover = create_smooth_movement_system(mock_move_function)
    
    # 测试不同距离的移动
    test_cases = [
        (5, 3),      # 小距离
        (25, 15),    # 中等距离
        (80, -60),   # 大距离
        (120, 90),   # 很大距离
    ]
    
    for target_x, target_y in test_cases:
        print(f"\n=== 测试移动到 ({target_x}, {target_y}) ===")
        smooth_mover.smooth_move_to_target(target_x, target_y)


if __name__ == "__main__":
    test_smooth_movement()
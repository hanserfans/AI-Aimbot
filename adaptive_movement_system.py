"""
智能自适应移动系统
根据距离远近自动调整移动策略：
- 远距离：80%粗调 + 20%精调
- 中距离：60%粗调 + 40%精调  
- 近距离：直接微调锁定
"""

import math
import time
from typing import Tuple, List, Callable, Optional
from dataclasses import dataclass


@dataclass
class MovementConfig:
    """移动配置参数"""
    # 距离阈值（像素）
    micro_adjustment_threshold: float = 15.0    # 微调阈值：小于此距离直接微调
    medium_distance_threshold: float = 60.0     # 中距离阈值
    large_distance_threshold: float = 120.0     # 大距离阈值
    
    # 移动策略参数
    large_distance_first_ratio: float = 0.80    # 大距离第一步移动比例
    medium_distance_first_ratio: float = 0.60   # 中距离第一步移动比例
    micro_adjustment_ratio: float = 1.0         # 微调直接移动比例
    
    # 精度控制
    final_precision_threshold: float = 3.0      # 最终精度阈值
    max_adjustment_steps: int = 3               # 最大微调步数
    
    # 延迟控制
    step_delay_base: float = 0.008              # 基础延迟（8ms）
    step_delay_variance: float = 0.003          # 延迟随机变化（±3ms）


class AdaptiveMovementSystem:
    """智能自适应移动系统"""
    
    def __init__(self, move_function: Callable[[float, float], bool], config: Optional[MovementConfig] = None):
        """
        初始化自适应移动系统
        
        Args:
            move_function: 底层鼠标移动函数
            config: 移动配置参数
        """
        self.move_function = move_function
        self.config = config or MovementConfig()
        
        # 统计信息
        self.stats = {
            'total_movements': 0,
            'micro_adjustments': 0,
            'medium_movements': 0,
            'large_movements': 0,
            'successful_movements': 0,
            'failed_movements': 0
        }
        
        print(f"[ADAPTIVE_MOVE] 智能自适应移动系统已初始化")
        print(f"[ADAPTIVE_MOVE] 微调阈值: {self.config.micro_adjustment_threshold}px")
        print(f"[ADAPTIVE_MOVE] 中距离阈值: {self.config.medium_distance_threshold}px")
        print(f"[ADAPTIVE_MOVE] 大距离阈值: {self.config.large_distance_threshold}px")
    
    def calculate_distance(self, x: float, y: float) -> float:
        """计算移动距离"""
        return math.sqrt(x * x + y * y)
    
    def classify_movement_type(self, distance: float) -> str:
        """
        根据距离分类移动类型
        
        Args:
            distance: 移动距离
            
        Returns:
            移动类型：'micro', 'medium', 'large'
        """
        if distance <= self.config.micro_adjustment_threshold:
            return 'micro'
        elif distance <= self.config.medium_distance_threshold:
            return 'medium'
        elif distance <= self.config.large_distance_threshold:
            return 'large'
        else:
            return 'extra_large'
    
    def calculate_adaptive_steps(self, target_x: float, target_y: float) -> List[Tuple[float, float]]:
        """
        计算自适应移动步骤
        
        Args:
            target_x: 目标X坐标偏移
            target_y: 目标Y坐标偏移
            
        Returns:
            移动步骤列表
        """
        distance = self.calculate_distance(target_x, target_y)
        movement_type = self.classify_movement_type(distance)
        
        print(f"[ADAPTIVE_MOVE] 距离: {distance:.1f}px, 类型: {movement_type}")
        
        if movement_type == 'micro':
            # 微调：直接移动到目标
            return [(target_x, target_y)]
        
        elif movement_type == 'medium':
            # 中距离：60%粗调 + 40%精调
            first_ratio = self.config.medium_distance_first_ratio
            first_x = target_x * first_ratio
            first_y = target_y * first_ratio
            
            second_x = target_x - first_x
            second_y = target_y - first_y
            
            return [(first_x, first_y), (second_x, second_y)]
        
        elif movement_type in ['large', 'extra_large']:
            # 大距离：80%粗调 + 20%精调（可能需要多步微调）
            first_ratio = self.config.large_distance_first_ratio
            first_x = target_x * first_ratio
            first_y = target_y * first_ratio
            
            # 计算剩余距离
            remaining_x = target_x - first_x
            remaining_y = target_y - first_y
            remaining_distance = self.calculate_distance(remaining_x, remaining_y)
            
            steps = [(first_x, first_y)]
            
            # 如果剩余距离仍然较大，分步精调
            if remaining_distance > self.config.final_precision_threshold:
                # 将剩余距离分成2-3步
                num_fine_steps = min(3, max(2, int(remaining_distance / 20)))
                
                accumulated_x = 0.0
                accumulated_y = 0.0
                
                for i in range(num_fine_steps):
                    # 使用线性插值进行精调
                    progress = (i + 1) / num_fine_steps
                    target_fine_x = remaining_x * progress
                    target_fine_y = remaining_y * progress
                    
                    step_x = target_fine_x - accumulated_x
                    step_y = target_fine_y - accumulated_y
                    
                    accumulated_x = target_fine_x
                    accumulated_y = target_fine_y
                    
                    steps.append((step_x, step_y))
            else:
                # 剩余距离较小，一步到位
                steps.append((remaining_x, remaining_y))
            
            return steps
        
        return [(target_x, target_y)]
    
    def get_step_delay(self, step_index: int, total_steps: int, movement_type: str) -> float:
        """
        计算步骤延迟时间
        
        Args:
            step_index: 当前步骤索引
            total_steps: 总步骤数
            movement_type: 移动类型
            
        Returns:
            延迟时间（秒）
        """
        if movement_type == 'micro':
            return 0.0  # 微调无延迟
        
        # 基础延迟
        base_delay = self.config.step_delay_base
        
        # 第一步（粗调）延迟稍长，后续步骤（精调）延迟较短
        if step_index == 0 and total_steps > 1:
            delay = base_delay * 1.5  # 粗调延迟
        else:
            delay = base_delay * 0.8  # 精调延迟
        
        # 添加随机变化，模拟人手操作
        import random
        variance = random.uniform(-self.config.step_delay_variance, self.config.step_delay_variance)
        delay = max(0.0, delay + variance)
        
        return delay
    
    def adaptive_move_to_target(self, target_x: float, target_y: float) -> bool:
        """
        自适应移动到目标位置
        
        Args:
            target_x: 目标X坐标偏移
            target_y: 目标Y坐标偏移
            
        Returns:
            是否成功完成移动
        """
        self.stats['total_movements'] += 1
        
        # 计算移动距离和类型
        distance = self.calculate_distance(target_x, target_y)
        movement_type = self.classify_movement_type(distance)
        
        # 更新统计
        if movement_type == 'micro':
            self.stats['micro_adjustments'] += 1
        elif movement_type == 'medium':
            self.stats['medium_movements'] += 1
        else:
            self.stats['large_movements'] += 1
        
        # 计算移动步骤
        steps = self.calculate_adaptive_steps(target_x, target_y)
        
        print(f"[ADAPTIVE_MOVE] 🎯 开始自适应移动")
        print(f"[ADAPTIVE_MOVE] 目标: ({target_x:.1f}, {target_y:.1f}), 距离: {distance:.1f}px")
        print(f"[ADAPTIVE_MOVE] 移动类型: {movement_type}, 步数: {len(steps)}")
        
        # 执行移动步骤
        success = True
        for i, (step_x, step_y) in enumerate(steps):
            step_distance = self.calculate_distance(step_x, step_y)
            
            # 跳过过小的移动
            if step_distance < 0.5:
                print(f"[ADAPTIVE_MOVE] 步骤 {i+1}: 跳过微小移动 ({step_x:.1f}, {step_y:.1f})")
                continue
            
            step_type = "粗调" if i == 0 and len(steps) > 1 else "精调"
            print(f"[ADAPTIVE_MOVE] 步骤 {i+1}/{len(steps)} ({step_type}): ({step_x:.1f}, {step_y:.1f}), 距离: {step_distance:.1f}px")
            
            # 执行移动
            move_success = self.move_function(step_x, step_y)
            if not move_success:
                print(f"[ADAPTIVE_MOVE] ❌ 步骤 {i+1} 移动失败")
                success = False
                break
            
            # 步骤间延迟
            if i < len(steps) - 1:
                delay = self.get_step_delay(i, len(steps), movement_type)
                if delay > 0:
                    time.sleep(delay)
        
        # 更新统计
        if success:
            self.stats['successful_movements'] += 1
            print(f"[ADAPTIVE_MOVE] ✅ 自适应移动完成")
        else:
            self.stats['failed_movements'] += 1
            print(f"[ADAPTIVE_MOVE] ❌ 自适应移动失败")
        
        return success
    
    def get_movement_stats(self) -> dict:
        """获取移动统计信息"""
        total = self.stats['total_movements']
        if total == 0:
            return self.stats.copy()
        
        stats = self.stats.copy()
        stats['success_rate'] = (self.stats['successful_movements'] / total) * 100
        stats['micro_percentage'] = (self.stats['micro_adjustments'] / total) * 100
        stats['medium_percentage'] = (self.stats['medium_movements'] / total) * 100
        stats['large_percentage'] = (self.stats['large_movements'] / total) * 100
        
        return stats
    
    def print_stats(self):
        """打印移动统计信息"""
        stats = self.get_movement_stats()
        print(f"\n[ADAPTIVE_MOVE] 📊 移动统计:")
        print(f"  总移动次数: {stats['total_movements']}")
        print(f"  成功率: {stats.get('success_rate', 0):.1f}%")
        print(f"  微调移动: {stats['micro_adjustments']} ({stats.get('micro_percentage', 0):.1f}%)")
        print(f"  中距离移动: {stats['medium_movements']} ({stats.get('medium_percentage', 0):.1f}%)")
        print(f"  大距离移动: {stats['large_movements']} ({stats.get('large_percentage', 0):.1f}%)")


def create_adaptive_movement_system(move_function: Callable[[float, float], bool], 
                                  config: Optional[MovementConfig] = None) -> AdaptiveMovementSystem:
    """
    创建自适应移动系统
    
    Args:
        move_function: 底层鼠标移动函数
        config: 移动配置参数
        
    Returns:
        自适应移动系统实例
    """
    return AdaptiveMovementSystem(move_function, config)


if __name__ == "__main__":
    # 测试代码
    def mock_move_function(x: float, y: float) -> bool:
        print(f"    执行移动: ({x:.1f}, {y:.1f})")
        return True
    
    print("🎯 智能自适应移动系统测试")
    
    # 创建系统
    adaptive_system = create_adaptive_movement_system(mock_move_function)
    
    # 测试不同距离的移动
    test_cases = [
        (10, 5, "微调测试"),
        (40, 30, "中距离测试"),
        (100, 80, "大距离测试"),
        (200, 150, "超大距离测试"),
    ]
    
    for target_x, target_y, description in test_cases:
        print(f"\n=== {description} ===")
        adaptive_system.adaptive_move_to_target(target_x, target_y)
        time.sleep(0.1)
    
    # 打印统计信息
    adaptive_system.print_stats()
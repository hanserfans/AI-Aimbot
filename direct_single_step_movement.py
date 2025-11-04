"""
直接一步移动系统 - 专为Arduino Leonardo优化
针对用户要求的"直接一步移动到头上"功能设计

特点：
1. 无多步分解，直接移动到目标
2. 针对Arduino Leonardo的-127到127像素限制优化
3. 适合1600 DPI x 0.19灵敏度（304 eDPI）设置
4. 最大化移动效率，减少延迟
"""

import math
import time
from typing import Tuple, Optional

class DirectSingleStepMovement:
    """直接一步移动系统"""
    
    def __init__(self, move_function, arduino_limit=127):
        """
        初始化一步移动系统
        
        Args:
            move_function: 底层移动函数（如move_mouse_direct）
            arduino_limit: Arduino移动限制（默认127像素）
        """
        self.move_function = move_function
        self.arduino_limit = arduino_limit
        self.total_moves = 0
        self.successful_moves = 0
        self.large_distance_moves = 0  # 超出Arduino限制的移动次数
        
        print(f"[DIRECT_MOVE] 一步移动系统已初始化，Arduino限制: ±{arduino_limit}像素")
    
    def calculate_distance(self, x: float, y: float) -> float:
        """计算移动距离"""
        return math.sqrt(x*x + y*y)
    
    def is_within_arduino_limit(self, x: float, y: float) -> bool:
        """检查移动是否在Arduino限制范围内"""
        return abs(x) <= self.arduino_limit and abs(y) <= self.arduino_limit
    
    def clamp_to_arduino_limit(self, x: float, y: float) -> Tuple[int, int]:
        """
        将移动限制在Arduino范围内
        如果超出限制，按比例缩放到最大可移动距离
        """
        # 直接限制在Arduino范围内
        clamped_x = max(-self.arduino_limit, min(self.arduino_limit, x))
        clamped_y = max(-self.arduino_limit, min(self.arduino_limit, y))
        
        return int(clamped_x), int(clamped_y)
    
    def move_direct_to_target(self, target_x: float, target_y: float) -> bool:
        """
        直接一步移动到目标位置
        
        Args:
            target_x: 目标X坐标偏移
            target_y: 目标Y坐标偏移
            
        Returns:
            是否成功移动
        """
        self.total_moves += 1
        
        # 计算移动距离
        distance = self.calculate_distance(target_x, target_y)
        
        # 检查是否在Arduino限制范围内
        within_limit = self.is_within_arduino_limit(target_x, target_y)
        
        if not within_limit:
            self.large_distance_moves += 1
            print(f"[DIRECT_MOVE] ⚠️  大距离移动: {distance:.1f}像素，超出Arduino限制({self.arduino_limit})")
        
        # 限制移动到Arduino范围内
        move_x, move_y = self.clamp_to_arduino_limit(target_x, target_y)
        
        print(f"[DIRECT_MOVE] 🎯 一步移动: 目标({target_x:.1f}, {target_y:.1f}) -> 实际({move_x}, {move_y})")
        print(f"[DIRECT_MOVE] 📏 移动距离: {distance:.1f}像素，在限制内: {'✅' if within_limit else '❌'}")
        
        # 执行移动
        try:
            success = self.move_function(move_x, move_y)
            if success:
                self.successful_moves += 1
                print(f"[DIRECT_MOVE] ✅ 移动成功")
            else:
                print(f"[DIRECT_MOVE] ❌ 移动失败")
            return success
        except Exception as e:
            print(f"[DIRECT_MOVE] ❌ 移动异常: {e}")
            return False
    
    def get_statistics(self) -> dict:
        """获取移动统计信息"""
        success_rate = (self.successful_moves / self.total_moves * 100) if self.total_moves > 0 else 0
        large_distance_rate = (self.large_distance_moves / self.total_moves * 100) if self.total_moves > 0 else 0
        
        return {
            "total_moves": self.total_moves,
            "successful_moves": self.successful_moves,
            "success_rate": success_rate,
            "large_distance_moves": self.large_distance_moves,
            "large_distance_rate": large_distance_rate,
            "arduino_limit": self.arduino_limit
        }
    
    def print_statistics(self):
        """打印移动统计信息"""
        stats = self.get_statistics()
        print(f"\n[DIRECT_MOVE] 📊 移动统计:")
        print(f"  总移动次数: {stats['total_moves']}")
        print(f"  成功移动: {stats['successful_moves']}")
        print(f"  成功率: {stats['success_rate']:.1f}%")
        print(f"  大距离移动: {stats['large_distance_moves']} ({stats['large_distance_rate']:.1f}%)")
        print(f"  Arduino限制: ±{stats['arduino_limit']}像素")

def create_direct_single_step_movement(move_function, arduino_limit=127):
    """
    创建直接一步移动系统
    
    Args:
        move_function: 底层移动函数
        arduino_limit: Arduino移动限制（默认127像素）
        
    Returns:
        DirectSingleStepMovement实例
    """
    return DirectSingleStepMovement(move_function, arduino_limit)

# 使用示例
if __name__ == "__main__":
    def mock_move_function(x, y):
        """模拟移动函数"""
        print(f"模拟移动: ({x}, {y})")
        return True
    
    # 创建一步移动系统
    direct_movement = create_direct_single_step_movement(mock_move_function)
    
    # 测试不同距离的移动
    test_cases = [
        (50, 30),    # 小距离移动
        (100, 80),   # 中距离移动
        (150, 120),  # 大距离移动（超出Arduino限制）
        (-80, -60),  # 负方向移动
        (200, -150), # 超大距离移动
    ]
    
    print("🧪 测试一步移动系统:")
    for i, (x, y) in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}: 移动到 ({x}, {y}) ---")
        direct_movement.move_direct_to_target(x, y)
    
    # 打印统计信息
    direct_movement.print_statistics()
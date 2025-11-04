"""
智能移动状态管理系统
解决移动过程中的检测丢失、移动过头等问题
"""

import time
import threading
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class MovementState:
    """移动状态数据类"""
    is_moving: bool = False
    start_time: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    locked_target: Optional[Dict[str, Any]] = None
    movement_id: str = ""
    expected_duration: float = 0.0
    
class IntelligentMovementManager:
    """
    智能移动状态管理器
    
    功能：
    1. 管理移动状态，防止移动期间被新检测中断
    2. 处理移动期间的检测丢失问题
    3. 优化移动逻辑，避免移动过头
    4. 提供移动状态查询和控制接口
    """
    
    def __init__(self, arduino_limit: int = 127):
        self.arduino_limit = arduino_limit
        self.movement_state = MovementState()
        self.lock = threading.Lock()
        
        # 移动配置
        self.movement_timeout = 0.5  # 移动超时时间（秒）
        self.detection_loss_tolerance = 0.2  # 检测丢失容忍时间（秒）
        self.movement_precision_threshold = 2.0  # 移动精度阈值（像素）
        
        # 统计信息
        self.stats = {
            'total_movements': 0,
            'successful_movements': 0,
            'interrupted_movements': 0,
            'timeout_movements': 0,
            'detection_loss_during_movement': 0
        }
        
        print("[INFO] ✅ 智能移动状态管理器已初始化")
        print(f"[INFO] - Arduino限制: ±{self.arduino_limit}像素")
        print(f"[INFO] - 移动超时: {self.movement_timeout}秒")
        print(f"[INFO] - 检测丢失容忍: {self.detection_loss_tolerance}秒")
    
    def is_currently_moving(self) -> bool:
        """检查是否正在移动"""
        with self.lock:
            if not self.movement_state.is_moving:
                return False
            
            # 检查移动是否超时
            current_time = time.time()
            if (current_time - self.movement_state.start_time) > self.movement_timeout:
                print(f"[MOVEMENT_MANAGER] ⏰ 移动超时，自动结束移动状态")
                self._end_movement_internal("timeout")
                return False
            
            return True
    
    def start_movement(self, target_x: float, target_y: float, 
                      locked_target: Optional[Dict[str, Any]] = None) -> str:
        """
        开始移动
        
        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            locked_target: 锁定的目标信息
            
        Returns:
            movement_id: 移动ID
        """
        with self.lock:
            # 如果已经在移动，先结束当前移动
            if self.movement_state.is_moving:
                print(f"[MOVEMENT_MANAGER] 🔄 中断当前移动，开始新移动")
                self._end_movement_internal("interrupted")
            
            # 生成移动ID
            movement_id = f"move_{int(time.time() * 1000)}"
            
            # 计算预期移动时间
            distance = (target_x**2 + target_y**2)**0.5
            expected_duration = min(0.1 + distance * 0.001, self.movement_timeout)
            
            # 设置移动状态
            self.movement_state = MovementState(
                is_moving=True,
                start_time=time.time(),
                target_x=target_x,
                target_y=target_y,
                locked_target=locked_target,
                movement_id=movement_id,
                expected_duration=expected_duration
            )
            
            self.stats['total_movements'] += 1
            
            print(f"[MOVEMENT_MANAGER] 🎯 开始移动: ID={movement_id}")
            print(f"[MOVEMENT_MANAGER] - 目标: ({target_x:.1f}, {target_y:.1f})")
            print(f"[MOVEMENT_MANAGER] - 距离: {distance:.1f}px")
            print(f"[MOVEMENT_MANAGER] - 预期时长: {expected_duration:.3f}s")
            
            return movement_id
    
    def end_movement(self, movement_id: str, success: bool = True) -> bool:
        """
        结束移动
        
        Args:
            movement_id: 移动ID
            success: 是否成功
            
        Returns:
            是否成功结束
        """
        with self.lock:
            if not self.movement_state.is_moving:
                return False
            
            if self.movement_state.movement_id != movement_id:
                print(f"[MOVEMENT_MANAGER] ⚠️ 移动ID不匹配: 期望={movement_id}, 当前={self.movement_state.movement_id}")
                return False
            
            return self._end_movement_internal("success" if success else "failed")
    
    def _end_movement_internal(self, reason: str) -> bool:
        """内部结束移动方法"""
        if not self.movement_state.is_moving:
            return False
        
        duration = time.time() - self.movement_state.start_time
        
        print(f"[MOVEMENT_MANAGER] 🏁 移动结束: 原因={reason}, 时长={duration:.3f}s")
        
        # 更新统计
        if reason == "success":
            self.stats['successful_movements'] += 1
        elif reason == "interrupted":
            self.stats['interrupted_movements'] += 1
        elif reason == "timeout":
            self.stats['timeout_movements'] += 1
        
        # 重置移动状态
        self.movement_state = MovementState()
        return True
    
    def should_ignore_detection_loss(self) -> bool:
        """
        判断是否应该忽略检测丢失
        
        在移动期间，短时间的检测丢失是正常的，不应该中断移动
        """
        with self.lock:
            if not self.movement_state.is_moving:
                return False
            
            # 计算移动进行时间
            movement_duration = time.time() - self.movement_state.start_time
            
            # 如果移动时间还很短，忽略检测丢失
            if movement_duration < self.detection_loss_tolerance:
                print(f"[MOVEMENT_MANAGER] 🛡️ 移动期间忽略检测丢失 (时长: {movement_duration:.3f}s)")
                self.stats['detection_loss_during_movement'] += 1
                return True
            
            return False
    
    def get_locked_target(self) -> Optional[Dict[str, Any]]:
        """获取当前锁定的目标"""
        with self.lock:
            if self.movement_state.is_moving and self.movement_state.locked_target:
                return self.movement_state.locked_target.copy()
            return None
    
    def calculate_optimal_movement(self, target_x: float, target_y: float) -> Tuple[float, float, bool]:
        """
        计算最优移动方案
        
        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            
        Returns:
            (move_x, move_y, needs_multiple_steps): 移动量和是否需要多步
        """
        # 计算移动距离
        distance = (target_x**2 + target_y**2)**0.5
        
        # 检查是否超出Arduino限制
        max_single_move = min(abs(target_x), abs(target_y), self.arduino_limit)
        
        if abs(target_x) <= self.arduino_limit and abs(target_y) <= self.arduino_limit:
            # 可以一步到位
            return target_x, target_y, False
        else:
            # 需要分步移动，计算第一步的最优移动
            ratio = self.arduino_limit / max(abs(target_x), abs(target_y))
            move_x = target_x * ratio
            move_y = target_y * ratio
            
            print(f"[MOVEMENT_MANAGER] 📏 分步移动: 总距离={distance:.1f}px, 第一步=({move_x:.1f}, {move_y:.1f})")
            return move_x, move_y, True
    
    def get_movement_stats(self) -> Dict[str, Any]:
        """获取移动统计信息"""
        with self.lock:
            total = self.stats['total_movements']
            if total == 0:
                success_rate = 0.0
            else:
                success_rate = (self.stats['successful_movements'] / total) * 100
            
            return {
                **self.stats,
                'success_rate': success_rate,
                'current_state': {
                    'is_moving': self.movement_state.is_moving,
                    'movement_id': self.movement_state.movement_id,
                    'target': (self.movement_state.target_x, self.movement_state.target_y) if self.movement_state.is_moving else None
                }
            }
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_movement_stats()
        print(f"\n[MOVEMENT_MANAGER] 📊 移动统计:")
        print(f"- 总移动次数: {stats['total_movements']}")
        print(f"- 成功移动: {stats['successful_movements']}")
        print(f"- 成功率: {stats['success_rate']:.1f}%")
        print(f"- 中断移动: {stats['interrupted_movements']}")
        print(f"- 超时移动: {stats['timeout_movements']}")
        print(f"- 移动期间检测丢失: {stats['detection_loss_during_movement']}")
        
        if stats['current_state']['is_moving']:
            print(f"- 当前状态: 正在移动到 {stats['current_state']['target']}")
        else:
            print(f"- 当前状态: 空闲")

def create_intelligent_movement_manager(arduino_limit: int = 127) -> IntelligentMovementManager:
    """创建智能移动状态管理器"""
    return IntelligentMovementManager(arduino_limit=arduino_limit)

# 测试代码
if __name__ == "__main__":
    print("🧪 测试智能移动状态管理器...")
    
    manager = create_intelligent_movement_manager()
    
    # 测试移动状态管理
    print("\n1. 测试移动状态管理:")
    movement_id = manager.start_movement(100, 50)
    print(f"是否正在移动: {manager.is_currently_moving()}")
    print(f"应该忽略检测丢失: {manager.should_ignore_detection_loss()}")
    
    # 模拟移动完成
    time.sleep(0.1)
    manager.end_movement(movement_id, success=True)
    print(f"移动结束后是否还在移动: {manager.is_currently_moving()}")
    
    # 测试最优移动计算
    print("\n2. 测试最优移动计算:")
    test_cases = [
        (50, 30),    # 可以一步到位
        (200, 100),  # 需要分步移动
        (-150, 80),  # 需要分步移动
    ]
    
    for target_x, target_y in test_cases:
        move_x, move_y, needs_multiple = manager.calculate_optimal_movement(target_x, target_y)
        print(f"目标({target_x}, {target_y}) -> 移动({move_x:.1f}, {move_y:.1f}), 需要多步: {needs_multiple}")
    
    # 打印统计信息
    print("\n3. 统计信息:")
    manager.print_stats()
    
    print("\n✅ 智能移动状态管理器测试完成")
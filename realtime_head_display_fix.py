"""
实时头部位置显示修复系统
解决Live Feed中头部位置不实时和鼠标移动冲突的问题

主要功能：
1. 实时头部位置计算和显示
2. 移动状态锁定机制
3. 帧同步优化
4. 移动冲突检测和处理
"""

import time
import threading
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
import numpy as np

@dataclass
class MovementState:
    """移动状态数据类"""
    is_moving: bool = False
    start_time: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    movement_id: str = ""
    lock_reason: str = ""

@dataclass
class HeadPositionData:
    """头部位置数据类"""
    x: float
    y: float
    confidence: float
    timestamp: float
    frame_id: int

class RealtimeHeadDisplaySystem:
    """
    实时头部位置显示系统
    
    解决问题：
    1. Live Feed中头部位置显示延迟
    2. 鼠标移动过程中头部位置变化导致的移动冲突
    3. 帧同步不一致问题
    """
    
    def __init__(self):
        self.movement_state = MovementState()
        self.current_head_position: Optional[HeadPositionData] = None
        self.locked_head_position: Optional[HeadPositionData] = None
        self.frame_counter = 0
        self.lock = threading.Lock()
        
        # 配置参数
        self.movement_timeout = 5.0  # 移动超时时间（秒）
        self.position_update_threshold = 2.0  # 位置更新阈值（像素）
        self.frame_sync_enabled = True
        
        print("[INFO] ✅ 实时头部位置显示系统已初始化")
    
    def on_movement_start(self) -> None:
        """
        通知系统开始移动（由外部调用）
        """
        with self.lock:
            if not self.movement_state.is_moving:
                # 使用当前头部位置作为移动目标
                if self.current_head_position:
                    self.start_movement(
                        self.current_head_position.x, 
                        self.current_head_position.y, 
                        "external_trigger"
                    )
                    print(f"[MOVEMENT_LOCK] 🔒 外部触发移动开始")
                else:
                    print(f"[MOVEMENT_LOCK] ⚠️ 无法开始移动：没有当前头部位置")

    def on_movement_end(self) -> None:
        """
        通知系统移动结束（由外部调用）
        """
        with self.lock:
            if self.movement_state.is_moving:
                self.end_movement()
                print(f"[MOVEMENT_LOCK] 🔓 外部触发移动结束")
    
    def start_movement(self, target_x: float, target_y: float, movement_id: str = None) -> bool:
        """
        开始移动，锁定当前头部位置
        
        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            movement_id: 移动ID（可选）
        
        Returns:
            bool: 是否成功开始移动
        """
        with self.lock:
            if self.movement_state.is_moving:
                print(f"[MOVEMENT_LOCK] ⚠️ 移动已在进行中，忽略新的移动请求")
                return False
            
            # 锁定当前头部位置
            if self.current_head_position:
                self.locked_head_position = HeadPositionData(
                    x=self.current_head_position.x,
                    y=self.current_head_position.y,
                    confidence=self.current_head_position.confidence,
                    timestamp=time.time(),
                    frame_id=self.frame_counter
                )
                print(f"[MOVEMENT_LOCK] 🔒 锁定头部位置: ({self.locked_head_position.x:.1f}, {self.locked_head_position.y:.1f})")
            
            # 设置移动状态
            self.movement_state = MovementState(
                is_moving=True,
                start_time=time.time(),
                target_x=target_x,
                target_y=target_y,
                movement_id=movement_id or f"move_{int(time.time() * 1000)}",
                lock_reason="头部位置锁定"
            )
            
            print(f"[MOVEMENT_LOCK] 🚀 开始移动到 ({target_x:.1f}, {target_y:.1f})")
            return True
    
    def end_movement(self, success: bool = True) -> bool:
        """
        结束移动，解锁头部位置
        
        Args:
            success: 移动是否成功
        
        Returns:
            bool: 是否成功结束移动
        """
        with self.lock:
            if not self.movement_state.is_moving:
                return False
            
            movement_duration = time.time() - self.movement_state.start_time
            
            # 重置移动状态
            self.movement_state = MovementState()
            self.locked_head_position = None
            
            status = "成功" if success else "失败"
            print(f"[MOVEMENT_LOCK] 🏁 移动{status}，耗时 {movement_duration:.2f}s，解锁头部位置")
            return True
    
    def update_frame_data(self, targets: List[Dict], timestamp: float) -> bool:
        """
        更新当前帧的目标数据
        
        Args:
            targets: 目标列表，每个目标包含 x, y, width, height, confidence, index
            timestamp: 时间戳
        
Returns:
            bool: 是否更新成功
        """
        with self.lock:
            self.frame_counter += 1
            
            # 检查移动超时
            if self.movement_state.is_moving:
                if time.time() - self.movement_state.start_time > self.movement_timeout:
                    print(f"[MOVEMENT_LOCK] ⏰ 移动超时，自动解锁")
                    self.end_movement(success=False)
            
            # 如果有目标，更新第一个高置信度目标的头部位置
            if targets:
                # 找到置信度最高的目标
                best_target = max(targets, key=lambda t: t.get('confidence', 0))
                
                if best_target.get('confidence', 0) >= 0.5:  # 置信度阈值
                    # 计算头部位置（目标中心上方）
                    target_x = best_target['x']
                    target_y = best_target['y']
                    target_height = best_target.get('height', 50)
                    
                    # 头部位置在目标框上方约1/3处
                    head_x = target_x
                    head_y = target_y - target_height * 0.3
                    
                    return self.update_head_position(head_x, head_y, best_target['confidence'])
            
            return False

    def get_display_head_position(self, target_index: int = 0) -> Optional[Tuple[float, float]]:
        """
        获取用于显示的头部位置
        
        Args:
            target_index: 目标索引（暂时未使用，始终返回第一个目标）
        
        Returns:
            Optional[Tuple[float, float]]: 头部位置坐标，如果没有则返回None
        """
        with self.lock:
            # 如果正在移动且有锁定位置，使用锁定位置
            if self.movement_state.is_moving and self.locked_head_position:
                return (self.locked_head_position.x, self.locked_head_position.y)
            
            # 否则使用当前位置
            if self.current_head_position:
                return (self.current_head_position.x, self.current_head_position.y)
            
            return None

    def get_aiming_head_position(self, target_index: int = 0) -> Optional[Tuple[float, float]]:
        """
        获取用于瞄准的头部位置
        
        Args:
            target_index: 目标索引（暂时未使用，始终返回第一个目标）
        
        Returns:
            Optional[Tuple[float, float]]: 头部位置坐标，如果没有则返回None
        """
        with self.lock:
            # 瞄准系统始终使用最新的头部位置
            if self.current_head_position:
                return (self.current_head_position.x, self.current_head_position.y)
            
            return None

    def update_head_position(self, x: float, y: float, confidence: float) -> bool:
        """
        更新头部位置
        
        Args:
            x: 头部X坐标
            y: 头部Y坐标
            confidence: 置信度
        
        Returns:
            bool: 是否更新成功
        """
        with self.lock:
            self.frame_counter += 1
            
            # 检查移动超时
            if self.movement_state.is_moving:
                if time.time() - self.movement_state.start_time > self.movement_timeout:
                    print(f"[MOVEMENT_LOCK] ⏰ 移动超时，自动解锁")
                    self.end_movement(success=False)
            
            # 如果正在移动，检查是否应该更新位置
            if self.movement_state.is_moving:
                if self.locked_head_position:
                    # 计算位置变化
                    distance = ((x - self.locked_head_position.x)**2 + (y - self.locked_head_position.y)**2)**0.5
                    
                    if distance > self.position_update_threshold:
                        print(f"[MOVEMENT_LOCK] ⚠️ 移动中检测到头部位置大幅变化 (距离: {distance:.1f}px)，但保持锁定")
                        # 可以选择是否更新锁定位置，这里选择保持锁定
                        return False
                    else:
                        print(f"[MOVEMENT_LOCK] 🔒 移动中，保持锁定位置")
                        return False
            
            # 更新当前头部位置
            self.current_head_position = HeadPositionData(
                x=x,
                y=y,
                confidence=confidence,
                timestamp=time.time(),
                frame_id=self.frame_counter
            )
            
            print(f"[HEAD_UPDATE] 📍 更新头部位置: ({x:.1f}, {y:.1f}), 置信度: {confidence:.3f}")
            return True
    
    def get_display_head_position(self, target_index: int = 0) -> Optional[Tuple[float, float]]:
        """
        获取用于显示的头部位置
        
        Args:
            target_index: 目标索引（暂时未使用，始终返回第一个目标）
        
        Returns:
            Optional[Tuple[float, float]]: 头部位置坐标，如果没有则返回None
        """
        with self.lock:
            # 如果正在移动且有锁定位置，使用锁定位置
            if self.movement_state.is_moving and self.locked_head_position:
                return (self.locked_head_position.x, self.locked_head_position.y)
            
            # 否则使用当前位置
            if self.current_head_position:
                return (self.current_head_position.x, self.current_head_position.y)
            
            return None

    def get_aiming_head_position(self, target_index: int = 0) -> Optional[Tuple[float, float]]:
        """
        获取用于瞄准的头部位置
        
        Args:
            target_index: 目标索引（暂时未使用，始终返回第一个目标）
        
        Returns:
            Optional[Tuple[float, float]]: 头部位置坐标，如果没有则返回None
        """
        with self.lock:
            # 瞄准系统始终使用最新的头部位置
            if self.current_head_position:
                return (self.current_head_position.x, self.current_head_position.y)
            
            return None

    def is_movement_locked(self) -> bool:
        """
        检查移动是否被锁定
        
        Returns:
            bool: 是否被锁定
        """
        with self.lock:
            return self.movement_state.is_moving

    def is_movement_in_progress(self) -> bool:
        """
        检查是否有移动正在进行
        
        Returns:
            bool: 是否有移动正在进行
        """
        with self.lock:
            return self.movement_state.is_moving

    def should_start_new_movement(self, new_target_x: float, new_target_y: float) -> bool:
        """
        检查是否应该开始新的移动
        
        Args:
            new_target_x: 新目标X坐标
            new_target_y: 新目标Y坐标
        
        Returns:
            bool: 是否应该开始新移动
        """
        with self.lock:
            if not self.movement_state.is_moving:
                return True
            
            # 如果当前移动的目标与新目标相同，不需要新移动
            current_distance = ((new_target_x - self.movement_state.target_x)**2 + 
                              (new_target_y - self.movement_state.target_y)**2)**0.5
            
            if current_distance < 5.0:  # 5像素内认为是同一目标
                print(f"[MOVEMENT_LOCK] 🎯 目标位置相近，继续当前移动")
                return False
            
            print(f"[MOVEMENT_LOCK] 🔄 检测到新目标，距离当前目标 {current_distance:.1f}px")
            return True

    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态信息
        
        Returns:
            Dict[str, Any]: 系统状态信息
        """
        with self.lock:
            current_pos = None
            locked_pos = None
            display_pos = self.get_display_head_position()
            aiming_pos = self.get_aiming_head_position()
            
            if self.current_head_position:
                current_pos = (self.current_head_position.x, self.current_head_position.y)
            
            if self.locked_head_position:
                locked_pos = (self.locked_head_position.x, self.locked_head_position.y)
            
            return {
                'movement_state': {
                    'is_moving': self.movement_state.is_moving,
                    'start_time': self.movement_state.start_time,
                    'target': (self.movement_state.target_x, self.movement_state.target_y) if self.movement_state.is_moving else None,
                    'movement_id': self.movement_state.movement_id,
                    'lock_reason': self.movement_state.lock_reason
                },
                'head_positions': {
                    'current': current_pos,
                    'locked': locked_pos,
                    'display': display_pos,
                    'aiming': aiming_pos
                },
                'frame_counter': self.frame_counter,
                'movement_timeout': self.movement_timeout,
                'position_update_threshold': self.position_update_threshold
            }

    def print_system_status(self) -> None:
        """
        打印系统状态信息
        """
        status = self.get_system_status()
        
        print(f"\n[REALTIME_HEAD_DISPLAY_STATUS] 实时头部位置显示系统状态:")
        print(f"  移动状态: {'🔒 锁定中' if status['movement_state']['is_moving'] else '🔓 空闲'}")
        
        if status['movement_state']['is_moving']:
            print(f"  移动目标: {status['movement_state']['target']}")
            print(f"  移动ID: {status['movement_state']['movement_id']}")
            print(f"  锁定原因: {status['movement_state']['lock_reason']}")
        
        print(f"  当前头部位置: {status['head_positions']['current']}")
        print(f"  锁定头部位置: {status['head_positions']['locked']}")
        print(f"  显示头部位置: {status['head_positions']['display']}")
        print(f"  瞄准头部位置: {status['head_positions']['aiming']}")
        print(f"  帧计数器: {status['frame_counter']}")
        print(f"  移动超时: {status['movement_timeout']}s")
        print(f"  位置更新阈值: {status['position_update_threshold']}px\n")
        
        print("\n" + "="*50)
        print("🎯 实时头部位置显示系统状态")
        print("="*50)
        
        # 移动状态
        movement = status['movement_state']
        if movement['is_moving']:
            duration = time.time() - movement['start_time']
            print(f"🚀 移动状态: 进行中 (耗时: {duration:.2f}s)")
            print(f"   目标位置: {movement['target']}")
            print(f"   移动ID: {movement['movement_id']}")
            print(f"   锁定原因: {movement['lock_reason']}")
        else:
            print("🛑 移动状态: 空闲")
        
        # 头部位置
        positions = status['head_positions']
        print(f"📍 当前头部位置: {positions['current']}")
        print(f"🔒 锁定头部位置: {positions['locked']}")
        print(f"🖥️ 显示头部位置: {positions['display']}")
        print(f"🎯 瞄准头部位置: {positions['aiming']}")
        
        # 帧信息
        frame_info = status['frame_info']
        print(f"🎬 帧计数器: {frame_info['frame_counter']}")
        print(f"🔄 帧同步: {'启用' if frame_info['sync_enabled'] else '禁用'}")
        
        print("="*50)

def create_realtime_head_display_system() -> RealtimeHeadDisplaySystem:
    """创建实时头部位置显示系统"""
    return RealtimeHeadDisplaySystem()

# 测试代码
if __name__ == "__main__":
    print("🧪 测试实时头部位置显示系统...")
    
    system = create_realtime_head_display_system()
    
    # 测试基本功能
    print("\n1. 测试头部位置更新:")
    system.update_head_position(100, 50, 0.95)
    system.update_head_position(105, 52, 0.93)
    
    print("\n2. 测试移动锁定:")
    system.start_movement(200, 100)
    system.update_head_position(110, 55, 0.92)  # 移动中的位置更新
    
    print("\n3. 测试位置获取:")
    display_pos = system.get_display_head_position()
    aiming_pos = system.get_aiming_head_position()
    print(f"显示位置: {display_pos}")
    print(f"瞄准位置: {aiming_pos}")
    
    print("\n4. 测试移动结束:")
    system.end_movement(success=True)
    
    print("\n5. 系统状态:")
    system.print_system_status()
    
    print("\n✅ 实时头部位置显示系统测试完成")
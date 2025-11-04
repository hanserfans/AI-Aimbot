#!/usr/bin/env python3
"""
增强目标选择系统
- 增加距离权重，距离越近优先级越高
- 改进移动锁定机制，移动过程中不重新选择目标
- 智能目标切换逻辑
"""

import time
import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

class EnhancedTargetSelectionSystem:
    """增强的目标选择系统"""
    
    def __init__(self):
        # 距离权重配置
        self.distance_weight_factor = 2.0  # 距离权重因子，越大距离影响越大
        self.min_distance_threshold = 10.0  # 最小距离阈值（像素）
        self.max_distance_threshold = 200.0  # 最大距离阈值（像素）
        
        # 移动锁定配置
        self.movement_lock_duration = 0.5  # 移动锁定持续时间（秒）
        self.movement_completion_threshold = 5.0  # 移动完成阈值（像素）
        self.target_switch_cooldown = 1  # 目标切换冷却时间（秒）
        
        # 状态变量
        self.locked_target = None
        self.lock_start_time = 0
        self.is_moving_to_target = False
        self.last_target_switch_time = 0
        self.current_mouse_pos = (0, 0)
        
        print("[ENHANCED_TARGET] ✅ 增强目标选择系统已初始化")
        print(f"[ENHANCED_TARGET] 📏 距离权重因子: {self.distance_weight_factor}")
        print(f"[ENHANCED_TARGET] 🔒 移动锁定时长: {self.movement_lock_duration}s")
    
    def calculate_weighted_distance_score(self, target_x: float, target_y: float, 
                                        box_height: float, crosshair_x: float, 
                                        crosshair_y: float, confidence: float = 1.0) -> float:
        """
        计算加权距离评分（距离越近评分越低，优先级越高）
        
        Args:
            target_x: 目标中心X坐标
            target_y: 目标中心Y坐标
            box_height: 目标框高度
            crosshair_x: 准星X坐标
            crosshair_y: 准星Y坐标
            confidence: 目标置信度
            
        Returns:
            float: 加权距离评分（越低越好）
        """
        # 计算头部位置（头部在目标中心上方约1/3处）
        head_offset = box_height * 0.35
        head_x = target_x
        head_y = target_y - head_offset
        
        # 计算欧几里得距离
        raw_distance = math.sqrt((head_x - crosshair_x)**2 + (head_y - crosshair_y)**2)
        
        # 应用距离权重
        # 使用指数函数增强距离影响：距离越远，权重增长越快
        distance_weight = math.pow(raw_distance / self.min_distance_threshold, self.distance_weight_factor)
        
        # 结合置信度（置信度越高，评分越低）
        confidence_factor = 1.0 / max(confidence, 0.1)  # 避免除零
        
        # 最终评分 = 距离权重 * 置信度因子
        final_score = distance_weight * confidence_factor
        
        return final_score
    
    def is_mouse_near_target(self, target_x: float, target_y: float, 
                           box_height: float) -> bool:
        """
        检查鼠标是否接近目标位置
        
        Args:
            target_x: 目标中心X坐标
            target_y: 目标中心Y坐标
            box_height: 目标框高度
            
        Returns:
            bool: 是否接近目标
        """
        # 计算头部位置
        head_offset = box_height * 0.35
        head_x = target_x
        head_y = target_y - head_offset
        
        # 计算鼠标到目标头部的距离
        distance = math.sqrt((self.current_mouse_pos[0] - head_x)**2 + 
                           (self.current_mouse_pos[1] - head_y)**2)
        
        return distance <= self.movement_completion_threshold
    
    def should_allow_target_switch(self, current_time: float) -> bool:
        """
        检查是否允许切换目标
        
        Args:
            current_time: 当前时间
            
        Returns:
            bool: 是否允许切换目标
        """
        # 检查冷却时间
        if (current_time - self.last_target_switch_time) < self.target_switch_cooldown:
            return False
        
        # 如果正在移动到目标，检查是否应该继续锁定
        if self.is_moving_to_target and self.locked_target:
            # 检查锁定是否过期
            if (current_time - self.lock_start_time) < self.movement_lock_duration:
                # 检查是否已经接近目标
                if self.is_mouse_near_target(
                    self.locked_target['x'], 
                    self.locked_target['y'], 
                    self.locked_target['height']
                ):
                    print("[ENHANCED_TARGET] 🎯 已接近锁定目标，允许重新选择")
                    self.is_moving_to_target = False
                    return True
                else:
                    print(f"[ENHANCED_TARGET] 🔒 移动中，继续锁定目标 (剩余: {self.movement_lock_duration - (current_time - self.lock_start_time):.2f}s)")
                    return False
            else:
                print("[ENHANCED_TARGET] ⏰ 移动锁定已过期，允许重新选择")
                self.is_moving_to_target = False
                return True
        
        return True
    
    def select_best_target(self, targets_df, crosshair_x: float, crosshair_y: float, 
                          current_time: float, mouse_pos: Tuple[float, float] = None) -> Optional[Dict]:
        """
        选择最佳目标（考虑距离权重和移动状态）
        
        Args:
            targets_df: 目标数据框
            crosshair_x: 准星X坐标
            crosshair_y: 准星Y坐标
            current_time: 当前时间
            mouse_pos: 当前鼠标位置
            
        Returns:
            Dict: 选中的目标信息，如果没有目标则返回None
        """
        if mouse_pos:
            self.current_mouse_pos = mouse_pos
        
        if len(targets_df) == 0:
            return None
        
        # 检查是否允许切换目标
        if not self.should_allow_target_switch(current_time):
            if self.locked_target:
                print(f"[ENHANCED_TARGET] 🔒 继续使用锁定目标: ({self.locked_target['x']:.1f}, {self.locked_target['y']:.1f})")
                return self.locked_target
        
        # 计算所有目标的加权距离评分
        targets_df = targets_df.copy()
        targets_df['weighted_score'] = targets_df.apply(
            lambda row: self.calculate_weighted_distance_score(
                row['current_mid_x'], 
                row['current_mid_y'], 
                row['height'],
                crosshair_x, 
                crosshair_y,
                row.get('confidence', 1.0)
            ), axis=1
        )
        
        # 按评分排序（评分越低越好）
        targets_df = targets_df.sort_values('weighted_score')
        
        # 选择最佳目标
        best_target = targets_df.iloc[0]
        
        # 创建目标信息
        selected_target = {
            'x': best_target['current_mid_x'],
            'y': best_target['current_mid_y'],
            'height': best_target['height'],
            'confidence': best_target.get('confidence', 1.0),
            'weighted_score': best_target['weighted_score']
        }
        
        # 检查是否需要更新锁定目标
        target_changed = (self.locked_target is None or 
                         abs(self.locked_target['x'] - selected_target['x']) > 5 or
                         abs(self.locked_target['y'] - selected_target['y']) > 5)
        
        if target_changed:
            self.locked_target = selected_target
            self.lock_start_time = current_time
            self.is_moving_to_target = True
            self.last_target_switch_time = current_time
            
            print(f"[ENHANCED_TARGET] 🎯 选择新目标: ({selected_target['x']:.1f}, {selected_target['y']:.1f})")
            print(f"[ENHANCED_TARGET] 📊 目标评分: {selected_target['weighted_score']:.2f}")
            print(f"[ENHANCED_TARGET] 🎯 共检测到 {len(targets_df)} 个目标，评分范围: {targets_df['weighted_score'].min():.2f} - {targets_df['weighted_score'].max():.2f}")
        
        return selected_target
    
    def get_target_priority_info(self, targets_df, crosshair_x: float, crosshair_y: float) -> str:
        """
        获取目标优先级信息（用于调试）
        
        Args:
            targets_df: 目标数据框
            crosshair_x: 准星X坐标
            crosshair_y: 准星Y坐标
            
        Returns:
            str: 优先级信息字符串
        """
        if len(targets_df) == 0:
            return "无目标"
        
        # 计算评分
        targets_df = targets_df.copy()
        targets_df['weighted_score'] = targets_df.apply(
            lambda row: self.calculate_weighted_distance_score(
                row['current_mid_x'], 
                row['current_mid_y'], 
                row['height'],
                crosshair_x, 
                crosshair_y,
                row.get('confidence', 1.0)
            ), axis=1
        )
        
        # 排序
        targets_df = targets_df.sort_values('weighted_score')
        
        # 生成信息
        info_lines = []
        for i, (_, target) in enumerate(targets_df.head(3).iterrows()):
            raw_distance = math.sqrt((target['current_mid_x'] - crosshair_x)**2 + 
                                   (target['current_mid_y'] - crosshair_y)**2)
            info_lines.append(
                f"#{i+1}: 距离={raw_distance:.1f}px, 评分={target['weighted_score']:.2f}, "
                f"置信度={target.get('confidence', 1.0):.2f}"
            )
        
        return " | ".join(info_lines)
    
    def reset_lock(self):
        """重置锁定状态"""
        self.locked_target = None
        self.lock_start_time = 0
        self.is_moving_to_target = False
        print("[ENHANCED_TARGET] 🔓 已重置目标锁定状态")
    
    def get_status_info(self) -> str:
        """获取系统状态信息"""
        if self.locked_target and self.is_moving_to_target:
            remaining_time = max(0, self.movement_lock_duration - (time.time() - self.lock_start_time))
            return f"🔒 锁定目标: ({self.locked_target['x']:.1f}, {self.locked_target['y']:.1f}), 剩余: {remaining_time:.2f}s"
        elif self.locked_target:
            return f"🎯 当前目标: ({self.locked_target['x']:.1f}, {self.locked_target['y']:.1f})"
        else:
            return "🔍 搜索目标中"

# 全局实例
_enhanced_target_system = None

def get_enhanced_target_system() -> EnhancedTargetSelectionSystem:
    """获取增强目标选择系统实例"""
    global _enhanced_target_system
    if _enhanced_target_system is None:
        _enhanced_target_system = EnhancedTargetSelectionSystem()
    return _enhanced_target_system

def create_enhanced_target_system() -> EnhancedTargetSelectionSystem:
    """创建新的增强目标选择系统实例"""
    return EnhancedTargetSelectionSystem()

if __name__ == "__main__":
    # 测试代码
    import pandas as pd
    
    system = EnhancedTargetSelectionSystem()
    
    # 模拟目标数据
    test_targets = pd.DataFrame([
        {'current_mid_x': 160, 'current_mid_y': 120, 'height': 40, 'confidence': 0.9},  # 近距离高置信度
        {'current_mid_x': 200, 'current_mid_y': 150, 'height': 35, 'confidence': 0.7},  # 中距离中置信度
        {'current_mid_x': 100, 'current_mid_y': 100, 'height': 30, 'confidence': 0.6},  # 远距离低置信度
    ])
    
    crosshair_x, crosshair_y = 160, 160  # 准星位置
    current_time = time.time()
    
    print("=== 增强目标选择系统测试 ===")
    print(f"准星位置: ({crosshair_x}, {crosshair_y})")
    print("\n目标优先级信息:")
    print(system.get_target_priority_info(test_targets, crosshair_x, crosshair_y))
    
    print("\n选择最佳目标:")
    best_target = system.select_best_target(test_targets, crosshair_x, crosshair_y, current_time)
    if best_target:
        print(f"最佳目标: ({best_target['x']:.1f}, {best_target['y']:.1f}), 评分: {best_target['weighted_score']:.2f}")
    
    print(f"\n系统状态: {system.get_status_info()}")
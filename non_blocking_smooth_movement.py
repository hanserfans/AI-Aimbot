#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非阻塞平滑移动系统
解决平滑移动阻塞主循环的问题，允许在移动过程中重新选择目标
"""

import time
import threading
import queue
from typing import Callable, Optional, Tuple, List
import math
import random


class NonBlockingSmoothMovement:
    """非阻塞平滑移动系统"""
    
    def __init__(self, move_function: Callable[[float, float], bool], fire_check_callback=None):
        """
        初始化非阻塞平滑移动系统
        
        Args:
            move_function: 移动函数，接受(dx, dy)参数
            fire_check_callback: 开火检测回调函数，返回True表示开火
        """
        self.move_function = move_function
        
        # 移动参数优化 - 增加步数，减少步长，提升平滑度
        self.max_steps = 15  # 增加到15步，提供更平滑的移动
        self.min_step_size = 30  # 减少到30px，允许更精细的移动
        self.base_step_delay = 0.003  # 减少基础延迟，提升速度
        self.step_delay_variance = 0.002  # 减少延迟变化，保持一致性
        
        # 指数衰减配置 - 可调节的衰减策略
        self.decay_presets = {
            "aggressive": 1.5,  # 激进递减 - 第一步77.7%
            "balanced": 1.2,    # 平衡递减 - 第一步70.1% (默认)
            "gentle": 0.9,      # 温和递减 - 第一步60.0%
            "linear": 0.0       # 线性递减 - 第一步33.3%
        }
        self.current_decay_preset = "balanced"  # 默认使用平衡策略
        
        # 人性化移动配置
        self.enable_human_tremor = True  # 启用人手抖动模拟
        self.tremor_intensity = 1.5      # 抖动强度（像素）- 适度减少
        self.enable_parabolic_trajectory = True  # 启用抛物线轨迹
        self.parabolic_height_factor = 0.08      # 抛物线高度因子 - 减少以提高收敛性
        
        # 步长控制配置
        self.min_final_step = 8   # 最后一步最小距离（像素）
        self.max_final_step = 18  # 最后一步最大距离（像素）
        self.min_penultimate_step = 20  # 倒数第二步最小距离（像素）
        
        # 目标范围内停止增强参数 - 从config.py导入
        try:
            import config
            self.target_range_threshold = getattr(config, 'targetRangeThreshold', 15)  # 改为15像素
            self.in_range_stop_duration = getattr(config, 'inRangeStopDuration', 0.0)  # 已取消停止时间
            self.precision_stop_duration = getattr(config, 'precisionStopDuration', 0.0)  # 已取消停止时间
            self.precision_mode_threshold = getattr(config, 'precisionModeThreshold', 15)
            self.stability_check_interval = getattr(config, 'stabilityCheckInterval', 0.005)
            print(f"[NON_BLOCKING_SMOOTH] ✅ 停止增强配置已加载: 范围阈值{self.target_range_threshold}px, 停止时间{self.in_range_stop_duration:.3f}s")
        except ImportError:
            # 使用默认值
            self.target_range_threshold = 15  # 15像素范围
            self.in_range_stop_duration = 0.0  # 已取消停止时间
            self.precision_stop_duration = 0.0  # 已取消停止时间
            self.precision_mode_threshold = 15
            self.stability_check_interval = 0.005
            print(f"[NON_BLOCKING_SMOOTH] ⚠️ 使用默认停止增强配置")
        
        # 非阻塞停止状态
        self.stop_until_time = 0  # 停止到什么时间
        self.is_in_stop_mode = False  # 是否处于停止模式
        
        # 非阻塞移动状态
        self.is_moving = False
        self.current_target = None
        self.movement_thread = None
        self.stop_movement = False
        
        # 目标队列（用于处理快速目标切换）
        self.target_queue = queue.Queue(maxsize=1)  # 只保留最新目标
        
        # 移动锁定机制
        self.movement_locked = False  # 是否锁定移动（禁止目标切换）
        self.pending_target = None    # 暂存的新目标
        self.lock_reason = ""         # 锁定原因（用于调试）
        
        # 🔧 新增：移动收敛检查机制
        self.convergence_check_enabled = True  # 启用收敛检查
        self.max_convergence_attempts = 3      # 最大收敛尝试次数
        self.convergence_threshold = 5.0       # 收敛阈值（像素）
        self.last_target_distance = None       # 上次目标距离
        self.convergence_attempts = 0          # 当前收敛尝试次数
        
        # 开火检测回调函数
        self.fire_check_callback = fire_check_callback
        
        # 性能统计
        self.total_movements = 0
        self.successful_movements = 0
        self.interrupted_movements = 0
        
        print("[NON_BLOCKING_SMOOTH] 非阻塞平滑移动系统初始化完成")
    
    def calculate_movement_steps(self, dx: float, dy: float) -> List[Tuple[float, float]]:
        """
        计算人性化平滑移动步骤
        
        特性：
        1. 确保最后几步>20px，最后一步<20px
        2. 添加人手抖动模拟
        3. 实现抛物线轨迹
        4. 针对300像素范围优化
        
        Args:
            dx: X轴移动距离
            dy: Y轴移动距离
            
        Returns:
            移动步骤列表
        """
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < self.min_step_size:
            return [(dx, dy)]
        
        # 针对300像素范围的优化算法
        if distance <= 300:
            return self._calculate_humanized_steps(dx, dy, distance)
        
        # 超过300像素使用原有的指数递减策略
        elif distance <= 500:
            return self._calculate_exponential_steps(dx, dy, distance)
        
        # 超长距离使用传统分步策略
        else:
            return self._calculate_traditional_steps(dx, dy, distance)
    
    def _calculate_humanized_steps(self, dx: float, dy: float, distance: float) -> List[Tuple[float, float]]:
        """
        计算300像素内的人性化移动步骤
        
        特点：
        - 最后一步约占20/300比例（约6.7%）
        - 确保最后几步>20px，最后一步<20px
        - 添加抛物线轨迹和人手抖动
        """
        # 根据距离动态调整步数
        if distance <= 50:
            num_steps = 3
        elif distance <= 100:
            num_steps = 4
        elif distance <= 200:
            num_steps = 5
        else:  # 200-300px
            num_steps = 6
        
        print(f"[HUMANIZED_MOVE] 300px内{num_steps}步移动，距离{distance:.1f}px")
        
        # 计算步长分配，确保最后一步在指定范围内
        if distance <= 100:
            # 对于较短距离，适当调整最后一步比例
            target_final_step = min(self.max_final_step, max(self.min_final_step, distance * 0.08))  # 8%
        else:
            target_final_step = min(self.max_final_step, max(self.min_final_step, distance * 0.067))  # 约6.7%
        
        # 为倒数第二步预留至少20px
        if num_steps > 2:
            target_penultimate_step = max(self.min_penultimate_step, distance * 0.12)  # 约12%
        else:
            target_penultimate_step = 0
        
        # 计算前面步骤需要覆盖的距离
        front_distance = distance - target_final_step - target_penultimate_step
        front_steps = num_steps - (2 if num_steps > 2 else 1)
        
        # 使用指数递减为前面的步骤分配比例
        decay_factor = self.decay_presets[self.current_decay_preset]
        if decay_factor == 0.0:  # 线性递减
            front_ratios = [front_steps - i for i in range(front_steps)]
        else:  # 指数递减
            front_ratios = [math.exp(-decay_factor * i) for i in range(front_steps)]
        
        # 归一化前面步骤的比例
        total_front_ratio = sum(front_ratios)
        normalized_front_ratios = [ratio / total_front_ratio for ratio in front_ratios]
        
        # 构建完整的步长分配（不包含轨迹和抖动效果）
        steps = []
        accumulated_x, accumulated_y = 0.0, 0.0
        
        # 前面的步骤
        for i in range(front_steps):
            step_distance = front_distance * normalized_front_ratios[i]
            
            # 计算基础方向向量（不加抖动和轨迹）
            base_x = dx * (step_distance / distance)
            base_y = dy * (step_distance / distance)
            
            # 添加轻微的人手抖动（但不影响总体精度）
            if self.enable_human_tremor and i < front_steps - 1:  # 最后几步不加抖动
                tremor_x = random.uniform(-1.0, 1.0)
                tremor_y = random.uniform(-1.0, 1.0)
                tremor_factor = 0.5 * (1.0 - i / front_steps)  # 抖动强度递减
                base_x += tremor_x * tremor_factor
                base_y += tremor_y * tremor_factor
            
            steps.append((base_x, base_y))
            accumulated_x += base_x
            accumulated_y += base_y
            
            actual_distance = math.sqrt(base_x**2 + base_y**2)
            cumulative_distance = math.sqrt(accumulated_x**2 + accumulated_y**2)
            print(f"   步骤{i+1}: 距离{actual_distance:.1f}px, 累积{cumulative_distance:.1f}px ({cumulative_distance/distance*100:.1f}%)")
        
        # 倒数第二步（如果存在）
        if num_steps > 2:
            penult_x = dx * (target_penultimate_step / distance)
            penult_y = dy * (target_penultimate_step / distance)
            
            steps.append((penult_x, penult_y))
            accumulated_x += penult_x
            accumulated_y += penult_y
            
            penult_distance = math.sqrt(penult_x**2 + penult_y**2)
            cumulative_distance = math.sqrt(accumulated_x**2 + accumulated_y**2)
            print(f"   步骤{num_steps-1}: 距离{penult_distance:.1f}px, 累积{cumulative_distance:.1f}px ({cumulative_distance/distance*100:.1f}%)")
        
        # 最后一步：精确到达目标
        final_x = dx - accumulated_x
        final_y = dy - accumulated_y
        
        steps.append((final_x, final_y))
        final_distance = math.sqrt(final_x**2 + final_y**2)
        print(f"   步骤{num_steps}: 距离{final_distance:.1f}px (最终步骤)")
        
        return steps
    
    def _calculate_step_with_trajectory(self, dx: float, dy: float, progress: float, 
                                      step_distance: float, step_index: int, total_steps: int) -> Tuple[float, float]:
        """
        计算带有完全对称抛物线轨迹和人手抖动的单步移动
        
        🎯 新算法：完全对称的抛物线轨迹，确保收敛性
        """
        # 基础方向向量
        total_distance = math.sqrt(dx * dx + dy * dy)
        base_x = dx * (step_distance / total_distance)
        base_y = dy * (step_distance / total_distance)
        
        # ✅ 启用完全对称的抛物线轨迹
        if self.enable_parabolic_trajectory and total_steps > 3:
            # 计算垂直于移动方向的单位向量
            perpendicular_x = -dy / total_distance
            perpendicular_y = dx / total_distance
            
            # 🎯 完全对称的抛物线函数：y = 4h * x * (1-x)
            # 其中 x 是进度 (0到1)，h 是最大高度系数
            # 这确保了在 x=0 和 x=1 时偏移为0，在 x=0.5 时达到最大偏移
            symmetric_progress = progress  # 0 到 1 的进度
            parabolic_height = 4 * symmetric_progress * (1 - symmetric_progress)  # 完全对称的抛物线
            
            # 动态调整抛物线高度：短距离移动使用较小的偏移
            adaptive_height_factor = min(self.parabolic_height_factor, total_distance * 0.01)
            parabolic_offset = total_distance * adaptive_height_factor * parabolic_height
            
            # 只在中间步骤添加抛物线偏移，确保首尾步骤完全对称
            if 0.1 < progress < 0.9:  # 只在10%-90%的进度范围内添加偏移
                base_x += perpendicular_x * parabolic_offset
                base_y += perpendicular_y * parabolic_offset
        
        # 🔧 优化人手抖动：保持适度抖动但确保收敛
        if self.enable_human_tremor and step_index < total_steps - 3:  # 最后三步不加抖动，确保精确收敛
            # 抖动强度随进度递减，后期步骤抖动更小
            tremor_factor = (1.0 - progress) * 0.5  # 从50%递减到0%
            tremor_intensity = self.tremor_intensity * tremor_factor
            
            tremor_x = random.uniform(-tremor_intensity, tremor_intensity)
            tremor_y = random.uniform(-tremor_intensity, tremor_intensity)
            
            base_x += tremor_x
            base_y += tremor_y
        
        return (base_x, base_y)
    
    def _calculate_final_step(self, dx: float, dy: float, previous_steps: List[Tuple[float, float]]) -> Tuple[float, float]:
        """
        计算最终步骤，确保精确到达目标
        
        🎯 优化：考虑抛物线轨迹的累积偏移，确保完美收敛
        """
        # 计算已移动的总距离
        accumulated_x = sum(step[0] for step in previous_steps)
        accumulated_y = sum(step[1] for step in previous_steps)
        
        # 计算剩余距离（这是真正需要到达目标的距离）
        remaining_x = dx - accumulated_x
        remaining_y = dy - accumulated_y
        
        # 🎯 抛物线轨迹补偿：由于抛物线轨迹是完全对称的，
        # 理论上累积偏移应该为0，但实际计算中可能有微小误差
        # 最终步骤直接使用剩余距离，确保精确到达目标
        
        # 计算最终步骤的距离，用于调试
        final_distance = math.sqrt(remaining_x**2 + remaining_y**2)
        
        # 如果最终步骤距离过大，可能是抛物线计算有问题，进行限制
        max_final_step = 10.0  # 最大最终步骤距离
        if final_distance > max_final_step:
            # 按比例缩放到合理范围
            scale_factor = max_final_step / final_distance
            remaining_x *= scale_factor
            remaining_y *= scale_factor
            print(f"   ⚠️ 最终步骤距离过大({final_distance:.1f}px)，已缩放到{max_final_step}px")
        
        return (remaining_x, remaining_y)
    
    def _calculate_exponential_steps(self, dx: float, dy: float, distance: float) -> List[Tuple[float, float]]:
        """
        计算指数递减移动步骤（300-500像素）
        """
        num_steps = 5  # 固定5步完成
        
        # 获取当前衰减系数
        decay_factor = self.decay_presets[self.current_decay_preset]
        
        # 计算移动比例
        if decay_factor == 0.0:  # 线性递减
            step_ratios = [num_steps - i for i in range(num_steps)]
        else:  # 指数递减
            step_ratios = [math.exp(-decay_factor * i) for i in range(num_steps)]
        
        # 归一化比例，确保总和为1
        total_ratio = sum(step_ratios)
        normalized_ratios = [ratio / total_ratio for ratio in step_ratios]
        
        print(f"[EXPONENTIAL_MOVE] 500px内5步移动 ({self.current_decay_preset}策略)")
        print(f"   衰减系数: {decay_factor}, 递减比例: {[f'{r:.3f}' for r in normalized_ratios]}")
        
        # 计算每步的累积位置和移动量
        steps = []
        accumulated_x, accumulated_y = 0, 0
        for i in range(num_steps):
            # 计算当前步骤应到达的目标位置
            cumulative_ratio = sum(normalized_ratios[:i+1])
            target_x_step = dx * cumulative_ratio
            target_y_step = dy * cumulative_ratio
            
            # 计算实际移动量
            step_x = target_x_step - accumulated_x
            step_y = target_y_step - accumulated_y
            
            # 添加轻微的人手抖动
            if self.enable_human_tremor and i < num_steps - 1:  # 最后一步不加抖动
                tremor_x = random.uniform(-1.0, 1.0)
                tremor_y = random.uniform(-1.0, 1.0)
                step_x += tremor_x
                step_y += tremor_y
            
            steps.append((step_x, step_y))
            accumulated_x = target_x_step
            accumulated_y = target_y_step
            
            # 调试输出每步信息
            step_distance = math.sqrt(step_x**2 + step_y**2)
            print(f"   步骤{i+1}: 比例{normalized_ratios[i]:.3f}, 距离{step_distance:.1f}px")
        
        return steps
    
    def _calculate_traditional_steps(self, dx: float, dy: float, distance: float) -> List[Tuple[float, float]]:
        """
        计算传统分步移动（超过500像素）
        """
        # 超长距离：6-8步，确保充分的微调阶段
        num_steps = max(6, min(self.max_steps, int(distance / 50) + 3))
        
        steps = []
        accumulated_x = 0.0
        accumulated_y = 0.0
        
        for i in range(num_steps):
            # 优化缓动函数：前期大步移动，后期精细微调
            t = (i + 1) / num_steps
            
            # 新的缓动策略：前三步达到80%，第一步就移动50%+
            if i == 0:  # 第一步：移动50%
                eased_t = 0.5
            elif i == 1:  # 第二步：累积到70%
                eased_t = 0.7
            elif i == 2:  # 第三步：累积到85%
                eased_t = 0.85
            else:
                # 后续步骤使用平滑过渡到100%
                remaining_progress = (t - 0.6) / 0.4  # 将剩余40%的进度重新映射
                eased_t = 0.85 + 0.15 * (1 - (1 - remaining_progress) ** 2)  # 从85%平滑到100%
            
            # 计算目标位置
            target_x = dx * eased_t
            target_y = dy * eased_t
            
            # 计算当前步骤的移动量
            step_x = target_x - accumulated_x
            step_y = target_y - accumulated_y
            
            steps.append((step_x, step_y))
            accumulated_x = target_x
            accumulated_y = target_y
            
            # 调试输出
            step_distance = math.sqrt(step_x**2 + step_y**2)
            cumulative_distance = math.sqrt(accumulated_x**2 + accumulated_y**2)
            cumulative_percentage = (cumulative_distance / distance) * 100
            print(f"   步骤{i+1}: 距离{step_distance:.1f}px, 累积{cumulative_percentage:.1f}%")
        
        return steps
    
    def get_step_delay(self, step_index: int, total_steps: int, step_distance: float) -> float:
        """
        计算步骤延迟时间（优化为高速移动）
        
        Args:
            step_index: 当前步骤索引
            total_steps: 总步骤数
            step_distance: 当前步骤距离
            
        Returns:
            延迟时间（秒）
        """
        # 如果基础延迟为0，直接返回0，跳过所有延迟计算
        if self.base_step_delay == 0:
            return 0.0
        
        # 基础延迟
        base_delay = self.base_step_delay
        
        # 距离因子：距离越远，延迟越短（快速移动）
        distance_factor = min(1.0, step_distance / 50.0)
        
        # 步骤因子：最后几步稍微慢一点，提高精度
        step_factor = 1.0
        if step_index >= total_steps - 2:
            step_factor = 1.2
        
        delay = base_delay * step_factor * (1 + distance_factor * 0.2)
        
        # 添加微小随机变化（仅在有基础延迟时）
        if self.step_delay_variance > 0:
            import random
            delay += random.uniform(-self.step_delay_variance, self.step_delay_variance)
        
        return max(0.0, delay)
    
    def _movement_worker(self):
        """移动工作线程"""
        while True:
            try:
                # 等待新的移动目标
                target_data = self.target_queue.get(timeout=0.1)
                if target_data is None:  # 停止信号
                    break
                
                # 解析目标数据
                if len(target_data) == 2:
                    # 兼容旧格式
                    target_x, target_y = target_data
                    is_locked_movement = False
                    lock_reason = ""
                else:
                    target_x, target_y, is_locked_movement, lock_reason = target_data
                
                self.current_target = (target_x, target_y)
                self.is_moving = True
                self.stop_movement = False
                self.total_movements += 1
                
                if is_locked_movement:
                    print(f"[NON_BLOCKING_SMOOTH] 开始锁定移动到: ({target_x:.1f}, {target_y:.1f}) - {lock_reason}")
                else:
                    print(f"[NON_BLOCKING_SMOOTH] 开始移动到: ({target_x:.1f}, {target_y:.1f})")
                
                # 计算移动步骤
                steps = self.calculate_movement_steps(target_x, target_y)
                
                # 添加调试输出显示移动步骤分配
                if len(steps) > 1:
                    total_distance = math.sqrt(target_x**2 + target_y**2)
                    cumulative_distance = 0
                    print(f"[SMOOTH_MOVE] 总距离: {total_distance:.1f}px, 分{len(steps)}步移动:")
                    for i, (step_x, step_y) in enumerate(steps):
                        step_distance = math.sqrt(step_x**2 + step_y**2)
                        cumulative_distance += step_distance
                        percentage = (cumulative_distance / total_distance) * 100 if total_distance > 0 else 0
                        print(f"  步骤{i+1}: ({step_x:.1f}, {step_y:.1f}) 距离:{step_distance:.1f}px 累积:{percentage:.1f}%")
                
                # 执行移动步骤
                movement_successful = True
                fire_executed = False  # 新增：跟踪是否已开火
                for i, (step_x, step_y) in enumerate(steps):
                    # 检查是否需要停止当前移动（锁定移动不能被中断）
                    if self.stop_movement and not is_locked_movement:
                        print(f"[NON_BLOCKING_SMOOTH] 普通移动被中断，切换到新目标")
                        self.interrupted_movements += 1
                        movement_successful = False
                        break
                    elif self.stop_movement and is_locked_movement:
                        print(f"[NON_BLOCKING_SMOOTH] 锁定移动不能被中断，继续执行: {lock_reason}")
                        self.stop_movement = False  # 重置中断标志
                    
                    # 跳过过小的移动
                    step_distance = math.sqrt(step_x * step_x + step_y * step_y)
                    if step_distance < 0.1:
                        continue
                    
                    # 执行移动
                    success = self.move_function(step_x, step_y)
                    if not success:
                        print(f"[NON_BLOCKING_SMOOTH] 步骤 {i+1} 移动失败")
                        movement_successful = False
                        break
                    
                    # 🎯 新增：移动步骤执行后立即进行扳机检测
                    if self.fire_check_callback and not fire_executed:
                        if self.fire_check_callback():
                            print(f"[NON_BLOCKING_SMOOTH] 🔥 步骤 {i+1} 执行后检测到开火！跳过剩余 {len(steps)-i-1} 步移动")
                            fire_executed = True
                            break  # 开火成功，立即跳出移动循环
                    
                    # 步骤间延迟（除了最后一步）
                    if i < len(steps) - 1:
                        delay = self.get_step_delay(i, len(steps), step_distance)
                        
                        # 在延迟期间检测开火机会（优化检测间隔提升速度）
                        if self.fire_check_callback and delay > 0 and not fire_executed:
                            start_time = time.time()
                            while time.time() - start_time < delay:
                                if self.fire_check_callback():
                                    print(f"[NON_BLOCKING_SMOOTH] 🔥 步骤 {i+1} 延迟期间检测到开火！跳过剩余 {len(steps)-i-1} 步移动")
                                    fire_executed = True
                                    break
                                time.sleep(0.0005)  # 减少到0.5ms检测间隔，提升响应速度
                            if fire_executed:
                                break  # 延迟期间开火成功，跳出移动循环
                        elif delay > 0:
                            time.sleep(delay)
                
                if movement_successful or fire_executed:
                    self.successful_movements += 1
                    if fire_executed:
                        print(f"[NON_BLOCKING_SMOOTH] 🔥 移动中开火成功，提前完成")
                    elif is_locked_movement:
                        print(f"[NON_BLOCKING_SMOOTH] 锁定移动完成: {lock_reason}")
                    else:
                        print(f"[NON_BLOCKING_SMOOTH] 移动完成")
                
                # 如果是锁定移动，解除锁定并处理缓存目标
                if is_locked_movement:
                    self.movement_locked = False
                    self.lock_reason = ""
                    print(f"[NON_BLOCKING_SMOOTH] 解除移动锁定")
                    
                    # 处理缓存的目标
                    if self.pending_target:
                        pending_x, pending_y, pending_lock, pending_reason = self.pending_target
                        self.pending_target = None
                        print(f"[NON_BLOCKING_SMOOTH] 处理缓存目标: ({pending_x:.1f}, {pending_y:.1f})")
                        
                        # 将缓存目标添加到队列
                        try:
                            self.target_queue.put_nowait((pending_x, pending_y, pending_lock, pending_reason))
                        except queue.Full:
                            print(f"[NON_BLOCKING_SMOOTH] 队列已满，丢弃缓存目标")
                
                # 清理当前移动状态
                self.is_moving = False
                self.current_target = None
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[NON_BLOCKING_SMOOTH] 移动线程错误: {e}")
                self.is_moving = False
                self.current_target = None
                # 确保解除锁定
                if self.movement_locked:
                    self.movement_locked = False
                    self.lock_reason = ""
                    print(f"[NON_BLOCKING_SMOOTH] 错误后解除移动锁定")
    
    def set_decay_strategy(self, strategy: str) -> bool:
        """
        设置指数衰减策略
        
        Args:
            strategy: 策略名称 ("aggressive", "balanced", "gentle", "linear")
            
        Returns:
            bool: 设置是否成功
        """
        if strategy in self.decay_presets:
            old_strategy = self.current_decay_preset
            self.current_decay_preset = strategy
            decay_factor = self.decay_presets[strategy]
            
            # 计算策略特性
            step_ratios = []
            if decay_factor == 0.0:  # 线性递减
                step_ratios = [5 - i for i in range(5)]
            else:  # 指数递减
                step_ratios = [math.exp(-decay_factor * i) for i in range(5)]
            
            total_ratio = sum(step_ratios)
            normalized_ratios = [ratio / total_ratio for ratio in step_ratios]
            first_step_percent = normalized_ratios[0] * 100
            
            print(f"[DECAY_STRATEGY] 切换策略: {old_strategy} → {strategy}")
            print(f"   衰减系数: {decay_factor}")
            print(f"   第一步移动: {first_step_percent:.1f}%")
            print(f"   移动比例: {[f'{r:.3f}' for r in normalized_ratios]}")
            
            return True
        else:
            available = list(self.decay_presets.keys())
            print(f"[DECAY_STRATEGY] ❌ 未知策略: {strategy}")
            print(f"   可用策略: {available}")
            return False
    
    def get_decay_info(self) -> dict:
        """获取当前衰减策略信息"""
        decay_factor = self.decay_presets[self.current_decay_preset]
        
        # 计算策略特性
        step_ratios = []
        if decay_factor == 0.0:  # 线性递减
            step_ratios = [5 - i for i in range(5)]
        else:  # 指数递减
            step_ratios = [math.exp(-decay_factor * i) for i in range(5)]
        
        total_ratio = sum(step_ratios)
        normalized_ratios = [ratio / total_ratio for ratio in step_ratios]
        
        return {
            "current_strategy": self.current_decay_preset,
            "decay_factor": decay_factor,
            "ratios": normalized_ratios,
            "first_step_percentage": normalized_ratios[0] * 100,
            "first_three_steps_percentage": sum(normalized_ratios[:3]) * 100,
            "available_strategies": list(self.decay_presets.keys())
        }

    def set_fire_check_callback(self, callback: Optional[Callable[[], bool]]):
        """
        设置开火检测回调函数
        
        Args:
            callback: 开火检测函数，返回True表示需要开火，会中断当前延迟
        """
        self.fire_check_callback = callback
        print(f"[NON_BLOCKING_SMOOTH] 开火检测回调已{'设置' if callback else '清除'}")
    
    def move_to_target(self, target_x: float, target_y: float, lock_movement: bool = False, lock_reason: str = "") -> bool:
        """
        非阻塞移动到目标位置
        
        Args:
            target_x: 目标X坐标偏移
            target_y: 目标Y坐标偏移
            lock_movement: 是否锁定移动（禁止目标切换）
            lock_reason: 锁定原因（用于调试）
            
        Returns:
            是否成功启动移动（非阻塞，不等待完成）
        """
        try:
            # 🔧 新增：收敛检查机制
            current_distance = math.sqrt(target_x**2 + target_y**2)
            
            if self.convergence_check_enabled:
                # 检查是否距离过小，无需移动
                if current_distance < self.convergence_threshold:
                    print(f"[NON_BLOCKING_SMOOTH] 🎯 目标距离{current_distance:.1f}px < 收敛阈值{self.convergence_threshold}px，跳过移动")
                    self.convergence_attempts = 0  # 重置收敛尝试次数
                    return True
                
                # 检查收敛性：如果距离没有显著减小，增加尝试次数
                if self.last_target_distance is not None:
                    distance_reduction = self.last_target_distance - current_distance
                    if distance_reduction < 2.0:  # 距离减小不足2像素
                        self.convergence_attempts += 1
                        print(f"[NON_BLOCKING_SMOOTH] ⚠️ 收敛缓慢：距离减小{distance_reduction:.1f}px，尝试次数{self.convergence_attempts}/{self.max_convergence_attempts}")
                        
                        if self.convergence_attempts >= self.max_convergence_attempts:
                            print(f"[NON_BLOCKING_SMOOTH] 🚫 收敛失败，跳过移动避免无限循环")
                            self.convergence_attempts = 0
                            self.last_target_distance = None
                            return False
                    else:
                        # 距离有显著减小，重置尝试次数
                        self.convergence_attempts = 0
                
                # 更新上次距离
                self.last_target_distance = current_distance
            
            # 检查是否正在锁定移动
            if self.movement_locked:
                # 如果移动被锁定，暂存新目标
                self.pending_target = (target_x, target_y, lock_movement, lock_reason)
                print(f"[NON_BLOCKING_SMOOTH] 移动已锁定({self.lock_reason})，暂存新目标: ({target_x:.1f}, {target_y:.1f})")
                return False
            
            # 如果正在移动且不是锁定移动，中断当前移动
            if self.is_moving and not lock_movement:
                self.stop_movement = True
                print(f"[NON_BLOCKING_SMOOTH] 中断当前移动，切换到新目标")
            elif self.is_moving and lock_movement:
                # 如果当前移动也是锁定的，暂存新目标
                self.pending_target = (target_x, target_y, lock_movement, lock_reason)
                print(f"[NON_BLOCKING_SMOOTH] 当前移动已锁定，暂存新目标: ({target_x:.1f}, {target_y:.1f})")
                return False
            
            # 设置移动锁定状态
            if lock_movement:
                self.movement_locked = True
                self.lock_reason = lock_reason
                print(f"[NON_BLOCKING_SMOOTH] 启用移动锁定: {lock_reason}")
            
            # 清空队列并添加新目标
            try:
                self.target_queue.get_nowait()  # 移除旧目标
            except queue.Empty:
                pass
            
            self.target_queue.put_nowait((target_x, target_y, lock_movement, lock_reason))
            
            # 启动移动线程（如果尚未启动）
            if self.movement_thread is None or not self.movement_thread.is_alive():
                self.movement_thread = threading.Thread(target=self._movement_worker, daemon=True)
                self.movement_thread.start()
                print(f"[NON_BLOCKING_SMOOTH] 移动线程已启动")
            
            return True
            
        except queue.Full:
            print(f"[NON_BLOCKING_SMOOTH] 目标队列已满，跳过移动")
            return False
        except Exception as e:
            print(f"[NON_BLOCKING_SMOOTH] 启动移动失败: {e}")
            return False
    
    def move_to_head_position(self, target_x: float, target_y: float) -> bool:
        """
        移动到头部位置（锁定移动，不可中断）
        
        Args:
            target_x: 目标X坐标偏移
            target_y: 目标Y坐标偏移
            
        Returns:
            是否成功启动移动
        """
        return self.move_to_target(target_x, target_y, lock_movement=True, lock_reason="头部瞄准")
    
    def move_to_target_normal(self, target_x: float, target_y: float) -> bool:
        """
        普通移动到目标位置（可中断）
        
        Args:
            target_x: 目标X坐标偏移
            target_y: 目标Y坐标偏移
            
        Returns:
            是否成功启动移动
        """
        return self.move_to_target(target_x, target_y, lock_movement=False, lock_reason="")
    
    def is_movement_locked(self) -> bool:
        """
        检查移动是否被锁定
        
        Returns:
            是否锁定
        """
        return self.movement_locked
    
    def get_lock_info(self) -> dict:
        """
        获取锁定信息
        
        Returns:
            锁定信息字典
        """
        return {
            'locked': self.movement_locked,
            'reason': self.lock_reason,
            'has_pending': self.pending_target is not None,
            'pending_target': self.pending_target
        }
    
    def force_unlock_movement(self):
        """
        强制解除移动锁定（紧急情况使用）
        """
        if self.movement_locked:
            print(f"[NON_BLOCKING_SMOOTH] 强制解除移动锁定: {self.lock_reason}")
            self.movement_locked = False
            self.lock_reason = ""
            
            # 处理缓存目标
            if self.pending_target:
                pending_x, pending_y, pending_lock, pending_reason = self.pending_target
                self.pending_target = None
                print(f"[NON_BLOCKING_SMOOTH] 强制解锁后处理缓存目标: ({pending_x:.1f}, {pending_y:.1f})")
                self.move_to_target(pending_x, pending_y, pending_lock, pending_reason)

    def enhanced_target_stop(self, target_x: float, target_y: float, is_precision_mode: bool = False):
        """
        非阻塞的目标范围内停止功能
        当检测到头部目标在15像素范围内时，根据配置设置停止状态，不延误主函数执行
        
        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标  
            is_precision_mode: 是否为精确模式（距离很近时）
        """
        try:
            # 计算距离
            distance = math.sqrt(target_x**2 + target_y**2)
            
            # 只有在15像素范围内才触发停止
            if distance <= 15:
                # 根据配置决定停止时间
                stop_duration = self.precision_stop_duration if is_precision_mode else self.in_range_stop_duration
                
                # 如果停止时间为0，则不触发停止
                if stop_duration <= 0:
                    print(f"[ENHANCED_STOP] ➡️ 头部范围内({distance:.1f}px≤15px)，但停止时间已取消，继续移动")
                    return False
                
                # 设置非阻塞停止状态
                current_time = time.time()
                self.stop_until_time = current_time + stop_duration
                self.is_in_stop_mode = True
                
                print(f"[ENHANCED_STOP] 🎯 头部范围内({distance:.1f}px≤15px)，设置停止{stop_duration:.1f}s - 目标:({target_x:.1f}, {target_y:.1f})")
                
                # 立即停止当前移动
                if self.is_moving:
                    self.stop_movement = True
                    print(f"[ENHANCED_STOP] ⏸️ 立即停止当前移动")
                
                return True  # 表示已触发停止
            else:
                print(f"[ENHANCED_STOP] ➡️ 目标距离({distance:.1f}px)超出15px范围，继续移动")
                return False  # 表示未触发停止
                
        except Exception as e:
            print(f"[ENHANCED_STOP] ❌ 停止功能异常: {e}")
            return False

    def is_movement_blocked(self) -> bool:
        """
        检查当前是否应该阻止移动（非阻塞检查）
        
        Returns:
            True: 应该阻止移动, False: 可以移动
        """
        current_time = time.time()
        
        if self.is_in_stop_mode:
            if current_time < self.stop_until_time:
                # 仍在停止期间
                remaining_time = self.stop_until_time - current_time
                return True
            else:
                # 停止期间结束
                self.is_in_stop_mode = False
                self.stop_until_time = 0
                print(f"[ENHANCED_STOP] ✅ 停止期间结束，恢复移动")
                return False
        
        return False

    def get_stop_status(self) -> dict:
        """
        获取停止状态信息
        
        Returns:
            停止状态信息字典
        """
        current_time = time.time()
        remaining_time = max(0, self.stop_until_time - current_time) if self.is_in_stop_mode else 0
        
        return {
            'is_in_stop_mode': self.is_in_stop_mode,
            'stop_until_time': self.stop_until_time,
            'remaining_stop_time': remaining_time,
            'current_time': current_time
        }

    def check_target_range(self, target_x: float, target_y: float) -> tuple[bool, bool]:
        """
        检查目标是否在范围内
        
        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            
        Returns:
            (是否在目标范围内, 是否为精确模式)
        """
        distance = math.sqrt(target_x**2 + target_y**2)
        in_range = distance <= self.target_range_threshold
        is_precision = distance <= self.precision_mode_threshold
        
        return in_range, is_precision

    def get_movement_status(self) -> dict:
        """
        获取移动状态信息
        
        Returns:
            状态信息字典
        """
        return {
            'is_moving': self.is_moving,
            'current_target': self.current_target,
            'movement_locked': self.movement_locked,
            'lock_reason': self.lock_reason,
            'has_pending_target': self.pending_target is not None,
            'pending_target': self.pending_target,
            'total_movements': self.total_movements,
            'successful_movements': self.successful_movements,
            'interrupted_movements': self.interrupted_movements,
            'success_rate': self.successful_movements / max(1, self.total_movements) * 100,
            'thread_alive': self.movement_thread is not None and self.movement_thread.is_alive()
        }
    
    def stop(self):
        """停止移动系统"""
        self.stop_movement = True
        
        # 发送停止信号
        try:
            self.target_queue.put_nowait(None)
        except queue.Full:
            pass
        
        # 等待线程结束
        if self.movement_thread and self.movement_thread.is_alive():
            self.movement_thread.join(timeout=1.0)
        
        print("[NON_BLOCKING_SMOOTH] 非阻塞平滑移动系统已停止")


def create_non_blocking_smooth_movement_system(move_function: Callable[[float, float], bool]) -> NonBlockingSmoothMovement:
    """
    创建非阻塞平滑移动系统的工厂函数
    
    Args:
        move_function: 底层鼠标移动函数
        
    Returns:
        配置好的非阻塞平滑移动系统实例
    """
    return NonBlockingSmoothMovement(move_function)


if __name__ == "__main__":
    def mock_move_function(x: float, y: float) -> bool:
        """模拟鼠标移动函数"""
        print(f"移动鼠标: ({x:.1f}, {y:.1f})")
        return True
    
    # 测试非阻塞平滑移动
    print("🎯 非阻塞平滑移动系统测试")
    
    # 创建移动系统
    smooth_mover = create_non_blocking_smooth_movement_system(mock_move_function)
    
    # 测试快速目标切换
    print("\n测试快速目标切换:")
    smooth_mover.move_to_target(100, 50)
    time.sleep(0.02)  # 20ms后切换目标
    smooth_mover.move_to_target(200, 100)
    time.sleep(0.02)  # 再次切换
    smooth_mover.move_to_target(50, 150)
    
    # 等待移动完成
    time.sleep(2)
    
    # 显示统计信息
    status = smooth_mover.get_movement_status()
    print(f"\n移动统计:")
    print(f"  总移动次数: {status['total_movements']}")
    print(f"  成功移动: {status['successful_movements']}")
    print(f"  中断移动: {status['interrupted_movements']}")
    print(f"  成功率: {status['success_rate']:.1f}%")
    
    # 停止系统
    smooth_mover.stop()
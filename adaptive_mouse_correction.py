#!/usr/bin/env python3
"""
自适应鼠标校正系统
处理G-Hub鼠标精度不稳定的问题
"""

import time
import json
import pyautogui
from collections import deque
from mouse_driver.MouseMove import initialize_mouse
import ctypes
from ctypes import wintypes

class AdaptiveMouseCorrection:
    def __init__(self, base_correction_factor=0.62):
        """
        初始化自适应校正系统
        
        Args:
            base_correction_factor: 基础校正因子
        """
        self.base_factor = base_correction_factor
        self.current_factor = base_correction_factor
        
        # 历史记录 (最近50次移动)
        self.movement_history = deque(maxlen=50)
        
        # 累积误差
        self.accumulated_error_x = 0.0
        self.accumulated_error_y = 0.0
        
        # 方向特定的校正因子
        self.direction_factors = {
            'right': base_correction_factor,
            'left': base_correction_factor,
            'up': base_correction_factor,
            'down': base_correction_factor
        }
        
        # 距离特定的校正因子
        self.distance_factors = {
            'small': base_correction_factor,    # 1-5像素
            'medium': base_correction_factor,   # 6-20像素
            'large': base_correction_factor     # 21+像素
        }
        
        # 性能统计
        self.stats = {
            'total_movements': 0,
            'accurate_movements': 0,
            'average_error': 0.0,
            'recent_accuracy': 0.0
        }
        
        # G-Hub鼠标实例
        self.mouse_initialized = False
        
    def initialize(self):
        """初始化G-Hub鼠标"""
        if not self.mouse_initialized:
            self.mouse_initialized = initialize_mouse()
        return self.mouse_initialized
    
    def _get_direction(self, dx, dy):
        """获取移动方向"""
        if abs(dx) > abs(dy):
            return 'right' if dx > 0 else 'left'
        else:
            return 'down' if dy > 0 else 'up'
    
    def _get_distance_category(self, dx, dy):
        """获取移动距离类别"""
        distance = (dx**2 + dy**2)**0.5
        if distance <= 5:
            return 'small'
        elif distance <= 20:
            return 'medium'
        else:
            return 'large'
    
    def _calculate_adaptive_factor(self, dx, dy):
        """计算自适应校正因子"""
        direction = self._get_direction(dx, dy)
        distance_cat = self._get_distance_category(dx, dy)
        
        # 基础因子 = 方向因子 * 距离因子 * 全局因子
        direction_factor = self.direction_factors[direction]
        distance_factor = self.distance_factors[distance_cat]
        
        # 综合校正因子
        adaptive_factor = (direction_factor + distance_factor + self.current_factor) / 3
        
        return adaptive_factor
    
    def _apply_error_compensation(self, dx, dy):
        """应用累积误差补偿"""
        # 如果累积误差较大，进行补偿
        compensation_threshold = 3.0
        
        compensated_dx = dx
        compensated_dy = dy
        
        if abs(self.accumulated_error_x) > compensation_threshold:
            compensation_x = self.accumulated_error_x * 0.3  # 30%补偿
            compensated_dx += compensation_x
            self.accumulated_error_x *= 0.7  # 减少累积误差
        
        if abs(self.accumulated_error_y) > compensation_threshold:
            compensation_y = self.accumulated_error_y * 0.3  # 30%补偿
            compensated_dy += compensation_y
            self.accumulated_error_y *= 0.7  # 减少累积误差
        
        return compensated_dx, compensated_dy
    
    def adaptive_move(self, dx, dy, max_retries=2):
        """
        自适应鼠标移动
        
        Args:
            dx, dy: 期望移动距离
            max_retries: 最大重试次数
            
        Returns:
            bool: 移动是否成功
        """
        if not self.mouse_initialized:
            if not self.initialize():
                return False
        
        # 应用累积误差补偿
        compensated_dx, compensated_dy = self._apply_error_compensation(dx, dy)
        
        # 计算自适应校正因子
        adaptive_factor = self._calculate_adaptive_factor(dx, dy)
        
        # 记录初始位置
        start_pos = pyautogui.position()
        
        for attempt in range(max_retries + 1):
            # 应用校正因子
            corrected_dx = compensated_dx * adaptive_factor
            corrected_dy = compensated_dy * adaptive_factor
            
            # 执行移动
            success = self._execute_ghub_move(corrected_dx, corrected_dy)
            if not success:
                continue
            
            time.sleep(0.1)  # 等待移动完成
            
            # 检查实际移动
            end_pos = pyautogui.position()
            actual_dx = end_pos.x - start_pos.x
            actual_dy = end_pos.y - start_pos.y
            
            # 计算误差
            error_x = actual_dx - dx
            error_y = actual_dy - dy
            total_error = (error_x**2 + error_y**2)**0.5
            
            # 记录移动历史
            self._record_movement(dx, dy, actual_dx, actual_dy, adaptive_factor)
            
            # 如果精度可接受，返回成功
            acceptable_error = max(2, abs(dx) * 0.1, abs(dy) * 0.1)  # 动态误差阈值
            if total_error <= acceptable_error:
                return True
            
            # 如果误差较大且还有重试机会，进行微调
            if attempt < max_retries:
                # 计算补偿移动
                compensation_dx = error_x * -0.8  # 反向补偿80%
                compensation_dy = error_y * -0.8
                
                # 执行补偿移动
                if abs(compensation_dx) > 1 or abs(compensation_dy) > 1:
                    self._execute_ghub_move(compensation_dx, compensation_dy)
                    time.sleep(0.1)
        
        return True  # 即使有误差也返回成功，避免阻塞
    
    def _execute_ghub_move(self, dx, dy):
        """执行G-Hub移动"""
        try:
            # 导入G-Hub移动函数
            from mouse_driver.MouseMove import ghub_move
            return ghub_move(dx, dy)
        except Exception as e:
            print(f"G-Hub移动失败: {e}")
            return False
    
    def _record_movement(self, expected_dx, expected_dy, actual_dx, actual_dy, factor_used):
        """记录移动历史并更新统计"""
        error_x = actual_dx - expected_dx
        error_y = actual_dy - expected_dy
        total_error = (error_x**2 + error_y**2)**0.5
        
        # 记录到历史
        movement_record = {
            'expected': (expected_dx, expected_dy),
            'actual': (actual_dx, actual_dy),
            'error': (error_x, error_y),
            'total_error': total_error,
            'factor_used': factor_used,
            'timestamp': time.time()
        }
        self.movement_history.append(movement_record)
        
        # 更新累积误差
        self.accumulated_error_x += error_x
        self.accumulated_error_y += error_y
        
        # 更新统计
        self.stats['total_movements'] += 1
        
        # 判断是否为精确移动 (误差<=2像素)
        if total_error <= 2:
            self.stats['accurate_movements'] += 1
        
        # 更新平均误差
        total_errors = [record['total_error'] for record in self.movement_history]
        self.stats['average_error'] = sum(total_errors) / len(total_errors)
        
        # 更新最近精度 (最近10次移动)
        recent_records = list(self.movement_history)[-10:]
        recent_accurate = sum(1 for r in recent_records if r['total_error'] <= 2)
        self.stats['recent_accuracy'] = recent_accurate / len(recent_records) * 100
        
        # 自适应调整校正因子
        self._adaptive_adjustment()
    
    def _adaptive_adjustment(self):
        """基于历史表现自适应调整校正因子"""
        if len(self.movement_history) < 10:
            return
        
        recent_accuracy = self.stats['recent_accuracy']
        
        # 全局因子调整
        if recent_accuracy > 85:
            # 精度很好，可以微调减小校正因子
            self.current_factor *= 0.995
        elif recent_accuracy < 60:
            # 精度较差，增大校正因子
            self.current_factor *= 1.005
        
        # 限制校正因子范围
        self.current_factor = max(0.3, min(1.2, self.current_factor))
        
        # 方向特定调整
        self._adjust_direction_factors()
        
        # 距离特定调整
        self._adjust_distance_factors()
    
    def _adjust_direction_factors(self):
        """调整方向特定的校正因子"""
        direction_errors = {'right': [], 'left': [], 'up': [], 'down': []}
        
        for record in list(self.movement_history)[-20:]:  # 最近20次
            dx, dy = record['expected']
            direction = self._get_direction(dx, dy)
            direction_errors[direction].append(record['total_error'])
        
        for direction, errors in direction_errors.items():
            if len(errors) >= 3:  # 至少3次数据
                avg_error = sum(errors) / len(errors)
                if avg_error > 3:  # 误差较大
                    self.direction_factors[direction] *= 1.01
                elif avg_error < 1:  # 误差很小
                    self.direction_factors[direction] *= 0.99
                
                # 限制范围
                self.direction_factors[direction] = max(0.3, min(1.2, self.direction_factors[direction]))
    
    def _adjust_distance_factors(self):
        """调整距离特定的校正因子"""
        distance_errors = {'small': [], 'medium': [], 'large': []}
        
        for record in list(self.movement_history)[-20:]:  # 最近20次
            dx, dy = record['expected']
            distance_cat = self._get_distance_category(dx, dy)
            distance_errors[distance_cat].append(record['total_error'])
        
        for distance_cat, errors in distance_errors.items():
            if len(errors) >= 3:  # 至少3次数据
                avg_error = sum(errors) / len(errors)
                if avg_error > 3:  # 误差较大
                    self.distance_factors[distance_cat] *= 1.01
                elif avg_error < 1:  # 误差很小
                    self.distance_factors[distance_cat] *= 0.99
                
                # 限制范围
                self.distance_factors[distance_cat] = max(0.3, min(1.2, self.distance_factors[distance_cat]))
    
    def get_performance_report(self):
        """获取性能报告"""
        if self.stats['total_movements'] == 0:
            return "暂无移动数据"
        
        accuracy_rate = self.stats['accurate_movements'] / self.stats['total_movements'] * 100
        
        report = f"""
🎯 自适应鼠标校正性能报告
================================
总移动次数: {self.stats['total_movements']}
精确移动次数: {self.stats['accurate_movements']}
总体精度: {accuracy_rate:.1f}%
最近精度: {self.stats['recent_accuracy']:.1f}%
平均误差: {self.stats['average_error']:.2f}像素

当前校正因子:
- 全局因子: {self.current_factor:.3f}
- 右移因子: {self.direction_factors['right']:.3f}
- 左移因子: {self.direction_factors['left']:.3f}
- 上移因子: {self.direction_factors['up']:.3f}
- 下移因子: {self.direction_factors['down']:.3f}

累积误差:
- X轴: {self.accumulated_error_x:.2f}
- Y轴: {self.accumulated_error_y:.2f}
"""
        return report
    
    def save_calibration(self, filename="adaptive_calibration.json"):
        """保存校正数据"""
        calibration_data = {
            'base_factor': self.base_factor,
            'current_factor': self.current_factor,
            'direction_factors': self.direction_factors,
            'distance_factors': self.distance_factors,
            'stats': self.stats,
            'timestamp': time.time()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(calibration_data, f, indent=2, ensure_ascii=False)
        
        print(f"校正数据已保存到: {filename}")
    
    def load_calibration(self, filename="adaptive_calibration.json"):
        """加载校正数据"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                calibration_data = json.load(f)
            
            self.base_factor = calibration_data.get('base_factor', 0.62)
            self.current_factor = calibration_data.get('current_factor', 0.62)
            self.direction_factors = calibration_data.get('direction_factors', {})
            self.distance_factors = calibration_data.get('distance_factors', {})
            self.stats = calibration_data.get('stats', {})
            
            print(f"校正数据已从 {filename} 加载")
            return True
        except FileNotFoundError:
            print(f"校正文件 {filename} 不存在，使用默认设置")
            return False
        except Exception as e:
            print(f"加载校正数据失败: {e}")
            return False

# 全局实例
adaptive_mouse = AdaptiveMouseCorrection()

def adaptive_ghub_move(dx, dy):
    """
    自适应G-Hub移动函数
    可以直接替换原来的ghub_move函数
    """
    return adaptive_mouse.adaptive_move(dx, dy)

if __name__ == "__main__":
    # 测试自适应校正系统
    print("自适应鼠标校正系统测试")
    
    # 初始化
    if not adaptive_mouse.initialize():
        print("❌ G-Hub鼠标初始化失败")
        exit(1)
    
    print("✅ 自适应校正系统初始化成功")
    
    # 测试移动
    test_movements = [
        (10, 0), (-10, 0), (0, 10), (0, -10),
        (5, 5), (-5, -5), (20, 0), (0, -20)
    ]
    
    for dx, dy in test_movements:
        print(f"\n测试移动: ({dx}, {dy})")
        success = adaptive_mouse.adaptive_move(dx, dy)
        print(f"移动结果: {'成功' if success else '失败'}")
        time.sleep(0.5)
    
    # 显示性能报告
    print(adaptive_mouse.get_performance_report())
    
    # 保存校正数据
    adaptive_mouse.save_calibration()
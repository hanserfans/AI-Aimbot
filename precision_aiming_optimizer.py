#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确瞄准优化器
基于实时像素偏移数据动态调整瞄准参数
"""

import json
import time
from typing import Dict, List, Tuple

class PrecisionAimingOptimizer:
    def __init__(self):
        self.offset_history = []  # 存储历史偏移数据
        self.max_history = 50     # 最大历史记录数
        self.target_precision = 3  # 目标精度（像素）
        
        # 动态调整参数
        self.dynamic_headshot_ratio = 0.38
        self.learning_rate = 0.01
        
        # 统计数据
        self.stats = {
            'total_shots': 0,
            'accurate_shots': 0,  # 偏移 <= 3px
            'average_offset': 0.0,
            'best_offset': float('inf'),
            'worst_offset': 0.0
        }
    
    def add_offset_data(self, offset_x: float, offset_y: float, box_height: float, confidence: float):
        """添加新的偏移数据"""
        distance = (offset_x**2 + offset_y**2)**0.5
        
        data_point = {
            'timestamp': time.time(),
            'offset_x': offset_x,
            'offset_y': offset_y,
            'distance': distance,
            'box_height': box_height,
            'confidence': confidence,
            'headshot_ratio': self.dynamic_headshot_ratio
        }
        
        self.offset_history.append(data_point)
        
        # 保持历史记录在限制范围内
        if len(self.offset_history) > self.max_history:
            self.offset_history.pop(0)
        
        # 更新统计数据
        self.update_stats(distance)
        
        # 动态调整头部偏移比例
        self.adjust_headshot_ratio(offset_y, box_height)
        
        return self.get_optimized_parameters()
    
    def update_stats(self, distance: float):
        """更新统计数据"""
        self.stats['total_shots'] += 1
        
        if distance <= self.target_precision:
            self.stats['accurate_shots'] += 1
        
        # 更新平均偏移
        total_distance = sum(point['distance'] for point in self.offset_history)
        self.stats['average_offset'] = total_distance / len(self.offset_history)
        
        # 更新最佳和最差偏移
        self.stats['best_offset'] = min(self.stats['best_offset'], distance)
        self.stats['worst_offset'] = max(self.stats['worst_offset'], distance)
    
    def adjust_headshot_ratio(self, offset_y: float, box_height: float):
        """动态调整头部偏移比例"""
        if len(self.offset_history) < 5:  # 需要足够的数据才开始调整
            return
        
        # 计算最近几次的Y轴偏移趋势
        recent_y_offsets = [point['offset_y'] for point in self.offset_history[-5:]]
        avg_y_offset = sum(recent_y_offsets) / len(recent_y_offsets)
        
        # 如果持续向上偏移，增加头部偏移比例
        if avg_y_offset < -2:  # 持续偏上
            self.dynamic_headshot_ratio += self.learning_rate
        # 如果持续向下偏移，减少头部偏移比例
        elif avg_y_offset > 2:  # 持续偏下
            self.dynamic_headshot_ratio -= self.learning_rate
        
        # 限制调整范围
        self.dynamic_headshot_ratio = max(0.2, min(0.5, self.dynamic_headshot_ratio))
    
    def get_optimized_parameters(self) -> Dict:
        """获取优化后的参数"""
        if len(self.offset_history) < 3:
            return {
                'headshot_ratio': 0.38,
                'movement_amp_multiplier': 1.0,
                'confidence_threshold': 0.4
            }
        
        # 基于历史数据计算优化参数
        avg_distance = self.stats['average_offset']
        accuracy_rate = self.stats['accurate_shots'] / self.stats['total_shots']
        
        # 动态调整移动幅度乘数
        if avg_distance > 8:  # 偏移太大，减少移动幅度
            movement_multiplier = 0.8
        elif avg_distance < 3:  # 偏移很小，可以稍微增加移动幅度
            movement_multiplier = 1.1
        else:
            movement_multiplier = 1.0
        
        # 动态调整置信度阈值
        if accuracy_rate > 0.8:  # 准确率高，可以降低置信度阈值
            confidence_threshold = 0.35
        elif accuracy_rate < 0.5:  # 准确率低，提高置信度阈值
            confidence_threshold = 0.5
        else:
            confidence_threshold = 0.4
        
        return {
            'headshot_ratio': self.dynamic_headshot_ratio,
            'movement_amp_multiplier': movement_multiplier,
            'confidence_threshold': confidence_threshold,
            'stats': self.stats.copy()
        }
    
    def get_precision_report(self) -> str:
        """生成精度报告"""
        if self.stats['total_shots'] == 0:
            return "暂无数据"
        
        accuracy_rate = (self.stats['accurate_shots'] / self.stats['total_shots']) * 100
        
        report = f"""
=== 精确瞄准报告 ===
总射击次数: {self.stats['total_shots']}
精确射击次数: {self.stats['accurate_shots']} (≤{self.target_precision}px)
准确率: {accuracy_rate:.1f}%
平均偏移: {self.stats['average_offset']:.1f}px
最佳偏移: {self.stats['best_offset']:.1f}px
最差偏移: {self.stats['worst_offset']:.1f}px
当前头部偏移比例: {self.dynamic_headshot_ratio:.3f}

=== 优化建议 ===
"""
        
        if accuracy_rate >= 80:
            report += "✅ 瞄准精度优秀！"
        elif accuracy_rate >= 60:
            report += "⚠️ 瞄准精度良好，可继续优化"
        else:
            report += "❌ 瞄准精度需要改进"
        
        return report
    
    def save_data(self, filename: str = "aiming_data.json"):
        """保存数据到文件"""
        data = {
            'offset_history': self.offset_history,
            'stats': self.stats,
            'dynamic_headshot_ratio': self.dynamic_headshot_ratio
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_data(self, filename: str = "aiming_data.json"):
        """从文件加载数据"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.offset_history = data.get('offset_history', [])
            self.stats = data.get('stats', self.stats)
            self.dynamic_headshot_ratio = data.get('dynamic_headshot_ratio', 0.38)
            
            print(f"✅ 成功加载历史数据: {len(self.offset_history)} 条记录")
        except FileNotFoundError:
            print("📝 未找到历史数据文件，将创建新的记录")
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")

# 全局优化器实例
precision_optimizer = PrecisionAimingOptimizer()

def optimize_aiming_parameters(offset_x: float, offset_y: float, box_height: float, confidence: float) -> Dict:
    """
    优化瞄准参数的主函数
    
    Args:
        offset_x: X轴偏移（像素）
        offset_y: Y轴偏移（像素）
        box_height: 检测框高度
        confidence: 检测置信度
    
    Returns:
        优化后的参数字典
    """
    return precision_optimizer.add_offset_data(offset_x, offset_y, box_height, confidence)

def get_precision_report() -> str:
    """获取精度报告"""
    return precision_optimizer.get_precision_report()

def save_aiming_data():
    """保存瞄准数据"""
    precision_optimizer.save_data()

def load_aiming_data():
    """加载瞄准数据"""
    precision_optimizer.load_data()

if __name__ == "__main__":
    # 测试示例
    optimizer = PrecisionAimingOptimizer()
    
    # 模拟一些偏移数据
    test_data = [
        (-4, -9, 50, 0.75),  # 你当前的数据
        (-2, -5, 48, 0.68),
        (-6, -8, 52, 0.82),
        (-3, -4, 49, 0.71),
        (-1, -6, 51, 0.79)
    ]
    
    print("=== 测试精确瞄准优化器 ===")
    for i, (x, y, h, c) in enumerate(test_data):
        print(f"\n第 {i+1} 次测试:")
        print(f"输入偏移: ({x}, {y}), 距离: {(x**2 + y**2)**0.5:.1f}px")
        
        params = optimizer.add_offset_data(x, y, h, c)
        print(f"优化参数: {params}")
    
    print("\n" + optimizer.get_precision_report())
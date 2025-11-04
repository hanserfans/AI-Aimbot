#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
防抖检测阈值分析工具
用于分析和确定最佳的防抖检测阈值
"""

import numpy as np
import matplotlib.pyplot as plt
import time
import json
from typing import List, Tuple, Dict
import statistics

class JitterThresholdAnalyzer:
    """防抖检测阈值分析器"""
    
    def __init__(self):
        self.position_history = []
        self.movement_data = []
        self.time_stamps = []
        
    def add_position(self, x: float, y: float):
        """添加位置数据"""
        current_time = time.time()
        
        if len(self.position_history) > 0:
            # 计算移动距离
            prev_x, prev_y = self.position_history[-1]
            distance = np.sqrt((x - prev_x)**2 + (y - prev_y)**2)
            
            # 计算移动速度
            dt = current_time - self.time_stamps[-1]
            velocity = distance / dt if dt > 0 else 0
            
            self.movement_data.append({
                'distance': distance,
                'velocity': velocity,
                'dt': dt,
                'x': x,
                'y': y,
                'prev_x': prev_x,
                'prev_y': prev_y
            })
        
        self.position_history.append((x, y))
        self.time_stamps.append(current_time)
    
    def analyze_movement_patterns(self) -> Dict:
        """分析移动模式"""
        if len(self.movement_data) < 10:
            return {"error": "数据不足，需要至少10个数据点"}
        
        distances = [data['distance'] for data in self.movement_data]
        velocities = [data['velocity'] for data in self.movement_data]
        
        # 统计分析
        stats = {
            'distance_stats': {
                'mean': statistics.mean(distances),
                'median': statistics.median(distances),
                'std': statistics.stdev(distances) if len(distances) > 1 else 0,
                'min': min(distances),
                'max': max(distances),
                'percentile_25': np.percentile(distances, 25),
                'percentile_75': np.percentile(distances, 75),
                'percentile_90': np.percentile(distances, 90),
                'percentile_95': np.percentile(distances, 95)
            },
            'velocity_stats': {
                'mean': statistics.mean(velocities),
                'median': statistics.median(velocities),
                'std': statistics.stdev(velocities) if len(velocities) > 1 else 0,
                'min': min(velocities),
                'max': max(velocities)
            }
        }
        
        return stats
    
    def suggest_thresholds(self) -> Dict:
        """建议防抖阈值"""
        stats = self.analyze_movement_patterns()
        
        if 'error' in stats:
            return stats
        
        distance_stats = stats['distance_stats']
        
        # 基于统计数据建议阈值
        suggestions = {
            'conservative': {
                'threshold': distance_stats['percentile_25'],
                'description': '保守阈值 - 过滤25%的最小移动'
            },
            'balanced': {
                'threshold': distance_stats['median'],
                'description': '平衡阈值 - 过滤50%的移动'
            },
            'aggressive': {
                'threshold': distance_stats['percentile_75'],
                'description': '激进阈值 - 只保留25%的最大移动'
            },
            'ultra_conservative': {
                'threshold': distance_stats['mean'] - distance_stats['std'],
                'description': '超保守阈值 - 基于均值减一个标准差'
            },
            'ultra_aggressive': {
                'threshold': distance_stats['mean'] + distance_stats['std'],
                'description': '超激进阈值 - 基于均值加一个标准差'
            }
        }
        
        # 确保阈值不为负数
        for key in suggestions:
            suggestions[key]['threshold'] = max(0.1, suggestions[key]['threshold'])
        
        return {
            'statistics': stats,
            'suggestions': suggestions,
            'current_system_thresholds': {
                'main_program': 10.0,  # main_onnxfix.py 中的阈值
                'dynamic_tracking': 1.0,  # dynamic_tracking_system.py 中的阈值
                'head_smoother': 1.0  # head_position_smoother.py 中的阈值
            }
        }
    
    def test_threshold_effectiveness(self, threshold: float) -> Dict:
        """测试特定阈值的有效性"""
        if len(self.movement_data) < 10:
            return {"error": "数据不足"}
        
        filtered_movements = []
        total_movements = len(self.movement_data)
        
        for data in self.movement_data:
            if data['distance'] > threshold:
                filtered_movements.append(data)
        
        filtered_count = len(filtered_movements)
        filter_rate = (total_movements - filtered_count) / total_movements * 100
        
        if filtered_count > 0:
            filtered_distances = [data['distance'] for data in filtered_movements]
            avg_filtered_distance = statistics.mean(filtered_distances)
        else:
            avg_filtered_distance = 0
        
        return {
            'threshold': threshold,
            'total_movements': total_movements,
            'filtered_movements': filtered_count,
            'filter_rate_percent': filter_rate,
            'avg_filtered_distance': avg_filtered_distance,
            'effectiveness': 'good' if 10 <= filter_rate <= 50 else 'poor'
        }
    
    def generate_report(self) -> str:
        """生成分析报告"""
        analysis = self.suggest_thresholds()
        
        if 'error' in analysis:
            return f"分析失败: {analysis['error']}"
        
        report = []
        report.append("=" * 60)
        report.append("防抖检测阈值分析报告")
        report.append("=" * 60)
        
        # 统计信息
        stats = analysis['statistics']['distance_stats']
        report.append("\n📊 移动距离统计:")
        report.append(f"  • 平均值: {stats['mean']:.2f} 像素")
        report.append(f"  • 中位数: {stats['median']:.2f} 像素")
        report.append(f"  • 标准差: {stats['std']:.2f} 像素")
        report.append(f"  • 最小值: {stats['min']:.2f} 像素")
        report.append(f"  • 最大值: {stats['max']:.2f} 像素")
        report.append(f"  • 25%分位: {stats['percentile_25']:.2f} 像素")
        report.append(f"  • 75%分位: {stats['percentile_75']:.2f} 像素")
        report.append(f"  • 95%分位: {stats['percentile_95']:.2f} 像素")
        
        # 当前系统阈值
        current = analysis['current_system_thresholds']
        report.append("\n🔧 当前系统阈值:")
        report.append(f"  • 主程序阈值: {current['main_program']:.1f} 像素")
        report.append(f"  • 动态跟踪阈值: {current['dynamic_tracking']:.1f} 像素")
        report.append(f"  • 头部平滑器阈值: {current['head_smoother']:.1f} 像素")
        
        # 建议阈值
        suggestions = analysis['suggestions']
        report.append("\n💡 建议阈值:")
        for name, suggestion in suggestions.items():
            report.append(f"  • {suggestion['description']}: {suggestion['threshold']:.2f} 像素")
        
        # 阈值测试
        report.append("\n🧪 阈值有效性测试:")
        test_thresholds = [1.0, 2.0, 5.0, 10.0, 15.0, 20.0]
        for threshold in test_thresholds:
            result = self.test_threshold_effectiveness(threshold)
            if 'error' not in result:
                report.append(f"  • {threshold:.1f}px: 过滤{result['filter_rate_percent']:.1f}%的移动 ({result['effectiveness']})")
        
        # 推荐配置
        report.append("\n🎯 推荐配置:")
        balanced_threshold = suggestions['balanced']['threshold']
        conservative_threshold = suggestions['conservative']['threshold']
        
        if balanced_threshold < 5:
            report.append(f"  • 建议使用平衡阈值: {balanced_threshold:.1f} 像素")
            report.append("  • 当前系统阈值可能过高，建议降低")
        elif balanced_threshold > 15:
            report.append(f"  • 建议使用保守阈值: {conservative_threshold:.1f} 像素")
            report.append("  • 检测到较大的移动，可能需要更高的阈值")
        else:
            report.append(f"  • 建议使用平衡阈值: {balanced_threshold:.1f} 像素")
            report.append("  • 当前系统阈值基本合理")
        
        return "\n".join(report)

def simulate_mouse_movement_data():
    """模拟鼠标移动数据进行测试"""
    analyzer = JitterThresholdAnalyzer()
    
    print("🔄 模拟鼠标移动数据...")
    
    # 模拟正常移动
    base_x, base_y = 160, 160
    
    # 添加一些正常移动
    for i in range(50):
        # 正常移动 (5-20像素)
        if i % 10 == 0:
            base_x += np.random.uniform(10, 30)
            base_y += np.random.uniform(10, 30)
        
        # 添加小幅抖动 (0.1-3像素)
        jitter_x = np.random.uniform(-3, 3)
        jitter_y = np.random.uniform(-3, 3)
        
        analyzer.add_position(base_x + jitter_x, base_y + jitter_y)
        time.sleep(0.01)  # 模拟时间间隔
    
    return analyzer

def main():
    """主函数"""
    print("防抖检测阈值分析工具")
    print("=" * 40)
    
    # 使用模拟数据进行分析
    analyzer = simulate_mouse_movement_data()
    
    # 生成报告
    report = analyzer.generate_report()
    print(report)
    
    # 保存报告到文件
    with open('jitter_threshold_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 报告已保存到: jitter_threshold_analysis_report.txt")
    
    # 保存详细数据
    analysis_data = analyzer.suggest_thresholds()
    with open('jitter_threshold_analysis_data.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    print(f"📊 详细数据已保存到: jitter_threshold_analysis_data.json")

if __name__ == "__main__":
    main()
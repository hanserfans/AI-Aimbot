#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时防抖检测分析工具
用于在实际运行中分析鼠标移动模式并动态调整阈值
"""

import time
import numpy as np
import threading
from typing import Dict, List, Tuple, Optional
import json
import statistics
from collections import deque

class RealTimeJitterAnalyzer:
    """实时防抖检测分析器"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.position_history = deque(maxlen=window_size)
        self.movement_history = deque(maxlen=window_size)
        self.time_history = deque(maxlen=window_size)
        
        self.lock = threading.Lock()
        self.analysis_cache = {}
        self.cache_time = 0
        self.cache_duration = 1.0  # 缓存1秒
        
        # 动态阈值
        self.current_threshold = 10.0
        self.adaptive_mode = True
        
        # 统计计数器
        self.total_movements = 0
        self.filtered_movements = 0
        
    def add_movement(self, x: float, y: float, timestamp: Optional[float] = None) -> Dict:
        """添加移动数据并返回实时分析结果"""
        if timestamp is None:
            timestamp = time.time()
        
        with self.lock:
            # 计算移动距离
            if len(self.position_history) > 0:
                prev_x, prev_y = self.position_history[-1]
                distance = np.sqrt((x - prev_x)**2 + (y - prev_y)**2)
                
                # 计算时间间隔
                dt = timestamp - self.time_history[-1] if len(self.time_history) > 0 else 0.016
                
                # 添加到历史记录
                self.movement_history.append(distance)
                self.total_movements += 1
                
                # 判断是否应该过滤
                should_filter = distance <= self.current_threshold
                if should_filter:
                    self.filtered_movements += 1
                
                # 更新自适应阈值
                if self.adaptive_mode and len(self.movement_history) >= 10:
                    self._update_adaptive_threshold()
                
            else:
                distance = 0
                should_filter = True
            
            # 添加位置和时间
            self.position_history.append((x, y))
            self.time_history.append(timestamp)
            
            # 返回实时分析结果
            return {
                'distance': distance,
                'should_filter': should_filter,
                'current_threshold': self.current_threshold,
                'filter_rate': self.get_filter_rate(),
                'analysis': self.get_current_analysis()
            }
    
    def _update_adaptive_threshold(self):
        """更新自适应阈值"""
        if len(self.movement_history) < 10:
            return
        
        # 获取最近的移动数据
        recent_movements = list(self.movement_history)[-20:]  # 最近20次移动
        
        # 计算统计值
        median_distance = np.median(recent_movements)
        mean_distance = np.mean(recent_movements)
        std_distance = np.std(recent_movements)
        
        # 计算当前过滤率
        current_filter_rate = self.get_filter_rate()
        
        # 自适应调整策略
        target_filter_rate = 0.3  # 目标过滤率30%
        
        if current_filter_rate < 0.1:  # 过滤太少，提高阈值
            self.current_threshold = min(self.current_threshold * 1.1, median_distance * 1.5)
        elif current_filter_rate > 0.5:  # 过滤太多，降低阈值
            self.current_threshold = max(self.current_threshold * 0.9, median_distance * 0.5)
        
        # 限制阈值范围
        self.current_threshold = max(0.5, min(self.current_threshold, 20.0))
    
    def get_filter_rate(self) -> float:
        """获取当前过滤率"""
        if self.total_movements == 0:
            return 0.0
        return self.filtered_movements / self.total_movements
    
    def get_current_analysis(self) -> Dict:
        """获取当前分析结果（带缓存）"""
        current_time = time.time()
        
        # 检查缓存
        if (current_time - self.cache_time) < self.cache_duration and self.analysis_cache:
            return self.analysis_cache
        
        with self.lock:
            if len(self.movement_history) < 5:
                return {"status": "insufficient_data"}
            
            movements = list(self.movement_history)
            
            analysis = {
                'sample_count': len(movements),
                'distance_stats': {
                    'mean': np.mean(movements),
                    'median': np.median(movements),
                    'std': np.std(movements),
                    'min': np.min(movements),
                    'max': np.max(movements),
                    'percentile_25': np.percentile(movements, 25),
                    'percentile_75': np.percentile(movements, 75)
                },
                'threshold_info': {
                    'current': self.current_threshold,
                    'adaptive_mode': self.adaptive_mode,
                    'filter_rate': self.get_filter_rate()
                },
                'recommendations': self._generate_recommendations(movements)
            }
            
            # 更新缓存
            self.analysis_cache = analysis
            self.cache_time = current_time
            
            return analysis
    
    def _generate_recommendations(self, movements: List[float]) -> Dict:
        """生成阈值建议"""
        if len(movements) < 10:
            return {"status": "need_more_data"}
        
        median = np.median(movements)
        mean = np.mean(movements)
        std = np.std(movements)
        
        recommendations = {
            'conservative': max(0.5, median * 0.5),
            'balanced': max(1.0, median),
            'aggressive': max(1.5, median * 1.5),
            'current_assessment': 'unknown'
        }
        
        # 评估当前阈值
        if self.current_threshold < recommendations['conservative']:
            recommendations['current_assessment'] = 'too_low'
        elif self.current_threshold > recommendations['aggressive']:
            recommendations['current_assessment'] = 'too_high'
        else:
            recommendations['current_assessment'] = 'reasonable'
        
        return recommendations
    
    def set_threshold(self, threshold: float):
        """手动设置阈值"""
        with self.lock:
            self.current_threshold = max(0.1, min(threshold, 50.0))
            self.adaptive_mode = False
    
    def enable_adaptive_mode(self):
        """启用自适应模式"""
        with self.lock:
            self.adaptive_mode = True
    
    def disable_adaptive_mode(self):
        """禁用自适应模式"""
        with self.lock:
            self.adaptive_mode = False
    
    def reset_statistics(self):
        """重置统计数据"""
        with self.lock:
            self.total_movements = 0
            self.filtered_movements = 0
            self.position_history.clear()
            self.movement_history.clear()
            self.time_history.clear()
            self.analysis_cache.clear()
    
    def get_detailed_report(self) -> str:
        """获取详细报告"""
        analysis = self.get_current_analysis()
        
        if analysis.get('status') == 'insufficient_data':
            return "数据不足，无法生成报告"
        
        stats = analysis['distance_stats']
        threshold_info = analysis['threshold_info']
        recommendations = analysis['recommendations']
        
        report = []
        report.append("=" * 50)
        report.append("实时防抖检测分析报告")
        report.append("=" * 50)
        
        report.append(f"\n📊 当前统计 (样本数: {analysis['sample_count']}):")
        report.append(f"  • 平均移动距离: {stats['mean']:.2f} 像素")
        report.append(f"  • 中位移动距离: {stats['median']:.2f} 像素")
        report.append(f"  • 标准差: {stats['std']:.2f} 像素")
        report.append(f"  • 最小/最大: {stats['min']:.2f} / {stats['max']:.2f} 像素")
        
        report.append(f"\n🔧 当前阈值配置:")
        report.append(f"  • 当前阈值: {threshold_info['current']:.2f} 像素")
        report.append(f"  • 自适应模式: {'开启' if threshold_info['adaptive_mode'] else '关闭'}")
        report.append(f"  • 过滤率: {threshold_info['filter_rate']:.1%}")
        
        if recommendations.get('status') != 'need_more_data':
            report.append(f"\n💡 阈值建议:")
            report.append(f"  • 保守阈值: {recommendations['conservative']:.2f} 像素")
            report.append(f"  • 平衡阈值: {recommendations['balanced']:.2f} 像素")
            report.append(f"  • 激进阈值: {recommendations['aggressive']:.2f} 像素")
            
            assessment = recommendations['current_assessment']
            if assessment == 'too_low':
                report.append(f"  • 当前阈值评估: 过低 ⚠️")
            elif assessment == 'too_high':
                report.append(f"  • 当前阈值评估: 过高 ⚠️")
            else:
                report.append(f"  • 当前阈值评估: 合理 ✅")
        
        return "\n".join(report)

def test_real_time_analyzer():
    """测试实时分析器"""
    analyzer = RealTimeJitterAnalyzer(window_size=50)
    
    print("🔄 开始实时防抖检测分析测试...")
    print("模拟鼠标移动数据...")
    
    # 模拟鼠标移动
    base_x, base_y = 160, 160
    
    for i in range(100):
        # 模拟不同类型的移动
        if i % 20 == 0:
            # 大幅移动
            base_x += np.random.uniform(15, 30)
            base_y += np.random.uniform(15, 30)
        elif i % 5 == 0:
            # 中等移动
            base_x += np.random.uniform(3, 8)
            base_y += np.random.uniform(3, 8)
        
        # 添加随机抖动
        jitter_x = np.random.uniform(-2, 2)
        jitter_y = np.random.uniform(-2, 2)
        
        current_x = base_x + jitter_x
        current_y = base_y + jitter_y
        
        # 添加到分析器
        result = analyzer.add_movement(current_x, current_y)
        
        # 每10次移动打印一次状态
        if i % 10 == 0 and i > 0:
            print(f"\n步骤 {i}: 距离={result['distance']:.2f}px, "
                  f"阈值={result['current_threshold']:.2f}px, "
                  f"过滤率={result['filter_rate']:.1%}")
        
        time.sleep(0.01)  # 模拟实时间隔
    
    # 生成最终报告
    print("\n" + analyzer.get_detailed_report())
    
    # 测试手动阈值设置
    print("\n🔧 测试手动阈值设置...")
    analyzer.set_threshold(5.0)
    print(f"设置阈值为 5.0px，当前过滤率: {analyzer.get_filter_rate():.1%}")
    
    # 重新启用自适应模式
    analyzer.enable_adaptive_mode()
    print("重新启用自适应模式")

def main():
    """主函数"""
    print("实时防抖检测分析工具")
    print("=" * 40)
    
    test_real_time_analyzer()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能分析器 - 详细监控各环节耗时
用于诊断CPS低的问题
"""

import time
import statistics
from collections import deque
from typing import Dict, List, Optional
import psutil
import GPUtil

class PerformanceAnalyzer:
    def __init__(self, history_size=100):
        """
        初始化性能分析器
        
        Args:
            history_size: 历史记录保存数量
        """
        self.history_size = history_size
        
        # 各环节耗时记录
        self.timings = {
            'screenshot': deque(maxlen=history_size),
            'preprocessing': deque(maxlen=history_size),
            'inference': deque(maxlen=history_size),
            'postprocessing': deque(maxlen=history_size),
            'stability_processing': deque(maxlen=history_size),
            'total_frame': deque(maxlen=history_size),
            'aiming': deque(maxlen=history_size),
            'trigger': deque(maxlen=history_size)
        }
        
        # 系统资源监控
        self.system_stats = {
            'cpu_usage': deque(maxlen=history_size),
            'memory_usage': deque(maxlen=history_size),
            'gpu_usage': deque(maxlen=history_size),
            'gpu_memory': deque(maxlen=history_size)
        }
        
        # 当前帧的计时器
        self.current_timers = {}
        
        # 统计信息
        self.frame_count = 0
        self.start_time = time.time()
        
    def start_timer(self, name: str):
        """开始计时"""
        self.current_timers[name] = time.time()
        
    def end_timer(self, name: str) -> float:
        """结束计时并记录"""
        if name not in self.current_timers:
            return 0.0
            
        duration = time.time() - self.current_timers[name]
        self.timings[name].append(duration)
        del self.current_timers[name]
        return duration
        
    def record_system_stats(self):
        """记录系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=None)
            self.system_stats['cpu_usage'].append(cpu_percent)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            self.system_stats['memory_usage'].append(memory.percent)
            
            # GPU使用率（如果有GPU）
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # 使用第一个GPU
                    self.system_stats['gpu_usage'].append(gpu.load * 100)
                    self.system_stats['gpu_memory'].append(gpu.memoryUtil * 100)
                else:
                    self.system_stats['gpu_usage'].append(0)
                    self.system_stats['gpu_memory'].append(0)
            except:
                self.system_stats['gpu_usage'].append(0)
                self.system_stats['gpu_memory'].append(0)
                
        except Exception as e:
            print(f"[WARNING] 系统资源监控失败: {e}")
            
    def get_timing_stats(self, name: str) -> Dict:
        """获取指定环节的统计信息"""
        if name not in self.timings or not self.timings[name]:
            return {'avg': 0, 'min': 0, 'max': 0, 'std': 0, 'count': 0}
            
        times = list(self.timings[name])
        return {
            'avg': statistics.mean(times),
            'min': min(times),
            'max': max(times),
            'std': statistics.stdev(times) if len(times) > 1 else 0,
            'count': len(times)
        }
        
    def get_system_stats(self, name: str) -> Dict:
        """获取系统资源统计信息"""
        if name not in self.system_stats or not self.system_stats[name]:
            return {'avg': 0, 'min': 0, 'max': 0, 'current': 0}
            
        stats = list(self.system_stats[name])
        return {
            'avg': statistics.mean(stats),
            'min': min(stats),
            'max': max(stats),
            'current': stats[-1] if stats else 0
        }
        
    def calculate_cps(self) -> float:
        """计算当前CPS"""
        if not self.timings['total_frame']:
            return 0.0
            
        # 使用最近10帧的平均时间计算CPS
        recent_frames = list(self.timings['total_frame'])[-10:]
        if not recent_frames:
            return 0.0
            
        avg_frame_time = statistics.mean(recent_frames)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
        
    def get_bottleneck_analysis(self) -> Dict:
        """分析性能瓶颈"""
        analysis = {}
        
        # 计算各环节平均耗时
        for name in ['screenshot', 'preprocessing', 'inference', 'postprocessing']:
            stats = self.get_timing_stats(name)
            analysis[name] = {
                'avg_ms': stats['avg'] * 1000,
                'percentage': 0  # 稍后计算
            }
            
        # 计算总耗时
        total_time = sum(analysis[name]['avg_ms'] for name in analysis)
        
        # 计算各环节占比
        if total_time > 0:
            for name in analysis:
                analysis[name]['percentage'] = (analysis[name]['avg_ms'] / total_time) * 100
                
        # 找出最大瓶颈
        bottleneck = max(analysis.items(), key=lambda x: x[1]['avg_ms'])
        analysis['bottleneck'] = {
            'name': bottleneck[0],
            'time_ms': bottleneck[1]['avg_ms'],
            'percentage': bottleneck[1]['percentage']
        }
        
        return analysis
        
    def print_performance_report(self):
        """打印详细的性能报告"""
        print("\n" + "="*80)
        print("🔍 详细性能分析报告")
        print("="*80)
        
        # 基本统计
        current_cps = self.calculate_cps()
        total_time = time.time() - self.start_time
        avg_cps = self.frame_count / total_time if total_time > 0 else 0
        
        print(f"📊 基本统计:")
        print(f"   当前CPS: {current_cps:.1f}")
        print(f"   平均CPS: {avg_cps:.1f}")
        print(f"   总帧数: {self.frame_count}")
        print(f"   运行时间: {total_time:.1f}s")
        
        # 各环节耗时分析
        print(f"\n⏱️ 各环节耗时分析:")
        for name in ['screenshot', 'preprocessing', 'inference', 'postprocessing', 'aiming', 'trigger']:
            stats = self.get_timing_stats(name)
            if stats['count'] > 0:
                print(f"   {name:15}: 平均 {stats['avg']*1000:6.2f}ms | "
                      f"最小 {stats['min']*1000:6.2f}ms | "
                      f"最大 {stats['max']*1000:6.2f}ms | "
                      f"标准差 {stats['std']*1000:6.2f}ms")
                      
        # 瓶颈分析
        bottleneck_analysis = self.get_bottleneck_analysis()
        if 'bottleneck' in bottleneck_analysis:
            bottleneck = bottleneck_analysis['bottleneck']
            print(f"\n🚨 性能瓶颈:")
            print(f"   最大瓶颈: {bottleneck['name']}")
            print(f"   耗时: {bottleneck['time_ms']:.2f}ms ({bottleneck['percentage']:.1f}%)")
            
        # 系统资源使用
        print(f"\n💻 系统资源使用:")
        for name in ['cpu_usage', 'memory_usage', 'gpu_usage', 'gpu_memory']:
            stats = self.get_system_stats(name)
            unit = '%'
            print(f"   {name:15}: 当前 {stats['current']:6.1f}{unit} | "
                  f"平均 {stats['avg']:6.1f}{unit} | "
                  f"最大 {stats['max']:6.1f}{unit}")
                  
        # 性能建议
        self._print_performance_suggestions(bottleneck_analysis)
        
        print("="*80)
        
    def _print_performance_suggestions(self, analysis: Dict):
        """打印性能优化建议"""
        print(f"\n💡 性能优化建议:")
        
        if 'bottleneck' not in analysis:
            return
            
        bottleneck_name = analysis['bottleneck']['name']
        bottleneck_time = analysis['bottleneck']['time_ms']
        
        if bottleneck_name == 'screenshot':
            print("   📸 截图捕获是主要瓶颈:")
            print("     • 尝试使用更快的截图方案 (dxcam vs bettercam)")
            print("     • 减少截图区域大小")
            print("     • 检查是否有其他程序占用显卡")
            
        elif bottleneck_name == 'inference':
            print("   🧠 模型推理是主要瓶颈:")
            print("     • 检查GPU使用率是否过高")
            print("     • 考虑降低模型精度或使用更小的模型")
            print("     • 确保CUDA版本和驱动程序是最新的")
            
        elif bottleneck_name == 'preprocessing':
            print("   🔄 图像预处理是主要瓶颈:")
            print("     • 优化图像缩放和格式转换")
            print("     • 减少不必要的图像拷贝操作")
            
        elif bottleneck_name == 'postprocessing':
            print("   📋 后处理是主要瓶颈:")
            print("     • 优化目标检测结果处理逻辑")
            print("     • 减少不必要的计算")
            
        # 通用建议
        cpu_stats = self.get_system_stats('cpu_usage')
        gpu_stats = self.get_system_stats('gpu_usage')
        memory_stats = self.get_system_stats('memory_usage')
        
        if cpu_stats['avg'] > 80:
            print("   ⚠️ CPU使用率过高，考虑关闭其他程序")
            
        if gpu_stats['avg'] > 90:
            print("   ⚠️ GPU使用率过高，可能存在显卡瓶颈")
            
        if memory_stats['avg'] > 85:
            print("   ⚠️ 内存使用率过高，可能影响性能")
            
    def frame_complete(self):
        """标记一帧完成"""
        self.frame_count += 1
        self.record_system_stats()

# 全局性能分析器实例
_performance_analyzer = None

def get_performance_analyzer() -> PerformanceAnalyzer:
    """获取全局性能分析器实例"""
    global _performance_analyzer
    if _performance_analyzer is None:
        _performance_analyzer = PerformanceAnalyzer()
    return _performance_analyzer

def reset_performance_analyzer():
    """重置性能分析器"""
    global _performance_analyzer
    _performance_analyzer = PerformanceAnalyzer()
    return _performance_analyzer
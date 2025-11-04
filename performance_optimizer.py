"""
性能优化器模块
提供系统性能监控和优化功能
"""

import time
import psutil
import threading
from typing import Dict, Any, Optional

class PerformanceOptimizer:
    """性能优化器类"""
    
    def __init__(self):
        """初始化性能优化器"""
        self.start_time = time.time()
        self.frame_count = 0
        self.fps_history = []
        self.cpu_usage_history = []
        self.memory_usage_history = []
        self.gpu_usage_history = []
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """开始性能监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self.cpu_usage_history.append(cpu_percent)
                
                # 内存使用率
                memory = psutil.virtual_memory()
                self.memory_usage_history.append(memory.percent)
                
                # 保持历史记录在合理范围内
                if len(self.cpu_usage_history) > 100:
                    self.cpu_usage_history.pop(0)
                if len(self.memory_usage_history) > 100:
                    self.memory_usage_history.pop(0)
                    
                time.sleep(0.5)  # 每0.5秒监控一次
            except Exception as e:
                print(f"[WARNING] 性能监控错误: {e}")
                time.sleep(1.0)
                
    def update_fps(self, fps: float):
        """更新FPS数据"""
        self.fps_history.append(fps)
        if len(self.fps_history) > 100:
            self.fps_history.pop(0)
            
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        stats = {
            'uptime': time.time() - self.start_time,
            'frame_count': self.frame_count,
            'avg_fps': sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0,
            'current_fps': self.fps_history[-1] if self.fps_history else 0,
            'avg_cpu': sum(self.cpu_usage_history) / len(self.cpu_usage_history) if self.cpu_usage_history else 0,
            'current_cpu': self.cpu_usage_history[-1] if self.cpu_usage_history else 0,
            'avg_memory': sum(self.memory_usage_history) / len(self.memory_usage_history) if self.memory_usage_history else 0,
            'current_memory': self.memory_usage_history[-1] if self.memory_usage_history else 0,
        }
        return stats
        
    def print_performance_report(self):
        """打印性能报告"""
        stats = self.get_performance_stats()
        print("\n" + "="*50)
        print("📊 性能监控报告")
        print("="*50)
        print(f"⏱️  运行时间: {stats['uptime']:.1f}秒")
        print(f"🎯 处理帧数: {stats['frame_count']}")
        print(f"📈 平均FPS: {stats['avg_fps']:.1f}")
        print(f"📊 当前FPS: {stats['current_fps']:.1f}")
        print(f"🖥️  平均CPU: {stats['avg_cpu']:.1f}%")
        print(f"💾 平均内存: {stats['avg_memory']:.1f}%")
        print("="*50)
        
    def increment_frame_count(self):
        """增加帧计数"""
        self.frame_count += 1
        
    def optimize_system(self):
        """系统优化建议"""
        stats = self.get_performance_stats()
        
        suggestions = []
        
        if stats['avg_cpu'] > 80:
            suggestions.append("CPU使用率过高，建议降低检测频率或优化算法")
            
        if stats['avg_memory'] > 80:
            suggestions.append("内存使用率过高，建议清理缓存或减少缓冲区大小")
            
        if stats['avg_fps'] < 30:
            suggestions.append("FPS过低，建议优化图像处理或降低分辨率")
            
        return suggestions

# 全局性能优化器实例
_performance_optimizer = None

def get_performance_optimizer() -> PerformanceOptimizer:
    """获取性能优化器实例（单例模式）"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
        _performance_optimizer.start_monitoring()
    return _performance_optimizer

def cleanup_performance_optimizer():
    """清理性能优化器"""
    global _performance_optimizer
    if _performance_optimizer:
        _performance_optimizer.stop_monitoring()
        _performance_optimizer = None

# 导出主要函数
__all__ = ['PerformanceOptimizer', 'get_performance_optimizer', 'cleanup_performance_optimizer']
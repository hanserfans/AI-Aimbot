"""
性能监控和FPS显示系统
实时监控截图、AI处理、总体FPS等性能指标
"""

import time
import threading
import psutil
import numpy as np
from collections import deque
from typing import Dict, Optional, List
import GPUtil

class PerformanceMonitorSystem:
    """性能监控和FPS显示系统"""
    
    def __init__(self, 
                 update_interval: float = 1.0,
                 history_size: int = 60,
                 enable_gpu_monitoring: bool = True,
                 enable_detailed_stats: bool = True):
        """
        初始化性能监控系统
        
        Args:
            update_interval: 更新间隔（秒）
            history_size: 历史数据保存数量
            enable_gpu_monitoring: 启用GPU监控
            enable_detailed_stats: 启用详细统计
        """
        self.update_interval = update_interval
        self.history_size = history_size
        self.enable_gpu_monitoring = enable_gpu_monitoring
        self.enable_detailed_stats = enable_detailed_stats
        
        # 性能计数器
        self.counters = {
            'screenshot_count': 0,
            'ai_inference_count': 0,
            'detection_count': 0,
            'frame_processed_count': 0,
            'mouse_move_count': 0,
            'trigger_count': 0
        }
        
        # FPS历史记录
        self.fps_history = {
            'screenshot_fps': deque(maxlen=history_size),
            'ai_fps': deque(maxlen=history_size),
            'detection_fps': deque(maxlen=history_size),
            'overall_fps': deque(maxlen=history_size)
        }
        
        # 时间记录
        self.timing_history = {
            'screenshot_time': deque(maxlen=history_size),
            'ai_inference_time': deque(maxlen=history_size),
            'postprocess_time': deque(maxlen=history_size),
            'total_frame_time': deque(maxlen=history_size)
        }
        
        # 系统资源监控
        self.system_stats = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_used_gb': 0.0,
            'memory_total_gb': 0.0,
            'gpu_percent': 0.0,
            'gpu_memory_percent': 0.0,
            'gpu_memory_used_gb': 0.0,
            'gpu_memory_total_gb': 0.0,
            'gpu_temperature': 0.0
        }
        
        # 性能统计
        self.performance_stats = {
            'avg_screenshot_fps': 0.0,
            'avg_ai_fps': 0.0,
            'avg_detection_fps': 0.0,
            'avg_overall_fps': 0.0,
            'peak_fps': 0.0,
            'min_fps': 0.0,
            'avg_frame_time': 0.0,
            'frame_time_std': 0.0
        }
        
        # 控制变量
        self.running = False
        self.monitor_thread = None
        self.last_update_time = time.time()
        self.last_counters = self.counters.copy()
        
        # 锁
        self.stats_lock = threading.Lock()
        
        print(f"[INFO] 🔍 性能监控系统初始化完成")
        print(f"   • 更新间隔: {update_interval}秒")
        print(f"   • 历史记录: {history_size}个数据点")
        print(f"   • GPU监控: {'启用' if enable_gpu_monitoring else '禁用'}")
        print(f"   • 详细统计: {'启用' if enable_detailed_stats else '禁用'}")
    
    def start(self):
        """启动性能监控"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_worker,
            daemon=True,
            name="PerformanceMonitor"
        )
        self.monitor_thread.start()
        
        print("[INFO] 🚀 性能监控系统已启动")
    
    def stop(self):
        """停止性能监控"""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        print("[INFO] 🛑 性能监控系统已停止")
    
    def increment_counter(self, counter_name: str, count: int = 1):
        """增加计数器"""
        if counter_name in self.counters:
            with self.stats_lock:
                self.counters[counter_name] += count
    
    def record_timing(self, timing_name: str, duration: float):
        """记录时间"""
        if timing_name in self.timing_history:
            with self.stats_lock:
                self.timing_history[timing_name].append(duration)
    
    def _monitor_worker(self):
        """监控工作线程"""
        while self.running:
            try:
                current_time = time.time()
                time_diff = current_time - self.last_update_time
                
                if time_diff >= self.update_interval:
                    self._update_fps_stats(time_diff)
                    self._update_system_stats()
                    self._update_performance_stats()
                    
                    self.last_update_time = current_time
                    self.last_counters = self.counters.copy()
                
                time.sleep(0.1)  # 100ms检查间隔
                
            except Exception as e:
                print(f"[ERROR] 性能监控线程错误: {e}")
                time.sleep(1.0)
    
    def _update_fps_stats(self, time_diff: float):
        """更新FPS统计"""
        with self.stats_lock:
            # 计算各种FPS
            screenshot_fps = (self.counters['screenshot_count'] - self.last_counters['screenshot_count']) / time_diff
            ai_fps = (self.counters['ai_inference_count'] - self.last_counters['ai_inference_count']) / time_diff
            detection_fps = (self.counters['detection_count'] - self.last_counters['detection_count']) / time_diff
            overall_fps = (self.counters['frame_processed_count'] - self.last_counters['frame_processed_count']) / time_diff
            
            # 添加到历史记录
            self.fps_history['screenshot_fps'].append(screenshot_fps)
            self.fps_history['ai_fps'].append(ai_fps)
            self.fps_history['detection_fps'].append(detection_fps)
            self.fps_history['overall_fps'].append(overall_fps)
    
    def _update_system_stats(self):
        """更新系统资源统计"""
        try:
            # CPU和内存
            self.system_stats['cpu_percent'] = psutil.cpu_percent(interval=None)
            
            memory = psutil.virtual_memory()
            self.system_stats['memory_percent'] = memory.percent
            self.system_stats['memory_used_gb'] = memory.used / (1024**3)
            self.system_stats['memory_total_gb'] = memory.total / (1024**3)
            
            # GPU监控
            if self.enable_gpu_monitoring:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]  # 使用第一个GPU
                        self.system_stats['gpu_percent'] = gpu.load * 100
                        self.system_stats['gpu_memory_percent'] = gpu.memoryUtil * 100
                        self.system_stats['gpu_memory_used_gb'] = gpu.memoryUsed / 1024
                        self.system_stats['gpu_memory_total_gb'] = gpu.memoryTotal / 1024
                        self.system_stats['gpu_temperature'] = gpu.temperature
                except Exception as e:
                    # GPU监控失败时静默处理
                    pass
                    
        except Exception as e:
            print(f"[ERROR] 系统资源监控失败: {e}")
    
    def _update_performance_stats(self):
        """更新性能统计"""
        with self.stats_lock:
            # 计算平均FPS
            if self.fps_history['screenshot_fps']:
                self.performance_stats['avg_screenshot_fps'] = np.mean(self.fps_history['screenshot_fps'])
            if self.fps_history['ai_fps']:
                self.performance_stats['avg_ai_fps'] = np.mean(self.fps_history['ai_fps'])
            if self.fps_history['detection_fps']:
                self.performance_stats['avg_detection_fps'] = np.mean(self.fps_history['detection_fps'])
            if self.fps_history['overall_fps']:
                overall_fps_array = np.array(self.fps_history['overall_fps'])
                self.performance_stats['avg_overall_fps'] = np.mean(overall_fps_array)
                self.performance_stats['peak_fps'] = np.max(overall_fps_array)
                self.performance_stats['min_fps'] = np.min(overall_fps_array)
            
            # 计算平均帧时间
            if self.timing_history['total_frame_time']:
                frame_times = np.array(self.timing_history['total_frame_time'])
                self.performance_stats['avg_frame_time'] = np.mean(frame_times) * 1000  # 转换为毫秒
                self.performance_stats['frame_time_std'] = np.std(frame_times) * 1000
    
    def get_current_fps(self) -> Dict[str, float]:
        """获取当前FPS"""
        with self.stats_lock:
            return {
                'screenshot_fps': self.fps_history['screenshot_fps'][-1] if self.fps_history['screenshot_fps'] else 0.0,
                'ai_fps': self.fps_history['ai_fps'][-1] if self.fps_history['ai_fps'] else 0.0,
                'detection_fps': self.fps_history['detection_fps'][-1] if self.fps_history['detection_fps'] else 0.0,
                'overall_fps': self.fps_history['overall_fps'][-1] if self.fps_history['overall_fps'] else 0.0
            }
    
    def get_system_stats(self) -> Dict[str, float]:
        """获取系统资源统计"""
        return self.system_stats.copy()
    
    def get_performance_stats(self) -> Dict[str, float]:
        """获取性能统计"""
        return self.performance_stats.copy()
    
    def get_detailed_stats(self) -> Dict:
        """获取详细统计信息"""
        current_fps = self.get_current_fps()
        system_stats = self.get_system_stats()
        performance_stats = self.get_performance_stats()
        
        return {
            'current_fps': current_fps,
            'system_stats': system_stats,
            'performance_stats': performance_stats,
            'counters': self.counters.copy(),
            'timing_stats': {
                'avg_screenshot_time': np.mean(self.timing_history['screenshot_time']) * 1000 if self.timing_history['screenshot_time'] else 0.0,
                'avg_ai_time': np.mean(self.timing_history['ai_inference_time']) * 1000 if self.timing_history['ai_inference_time'] else 0.0,
                'avg_postprocess_time': np.mean(self.timing_history['postprocess_time']) * 1000 if self.timing_history['postprocess_time'] else 0.0
            }
        }
    
    def print_performance_summary(self):
        """打印性能摘要"""
        stats = self.get_detailed_stats()
        
        print(f"\n📊 性能监控摘要:")
        print(f"   🖼️  截图FPS: {stats['current_fps']['screenshot_fps']:.1f} (平均: {stats['performance_stats']['avg_screenshot_fps']:.1f})")
        print(f"   🧠 AI推理FPS: {stats['current_fps']['ai_fps']:.1f} (平均: {stats['performance_stats']['avg_ai_fps']:.1f})")
        print(f"   🎯 检测FPS: {stats['current_fps']['detection_fps']:.1f} (平均: {stats['performance_stats']['avg_detection_fps']:.1f})")
        print(f"   ⚡ 总体FPS: {stats['current_fps']['overall_fps']:.1f} (平均: {stats['performance_stats']['avg_overall_fps']:.1f})")
        print(f"   🏆 峰值FPS: {stats['performance_stats']['peak_fps']:.1f}")
        print(f"   📉 最低FPS: {stats['performance_stats']['min_fps']:.1f}")
        
        print(f"\n💻 系统资源:")
        print(f"   CPU使用率: {stats['system_stats']['cpu_percent']:.1f}%")
        print(f"   内存使用: {stats['system_stats']['memory_used_gb']:.1f}GB / {stats['system_stats']['memory_total_gb']:.1f}GB ({stats['system_stats']['memory_percent']:.1f}%)")
        
        if self.enable_gpu_monitoring and stats['system_stats']['gpu_percent'] > 0:
            print(f"   GPU使用率: {stats['system_stats']['gpu_percent']:.1f}%")
            print(f"   GPU内存: {stats['system_stats']['gpu_memory_used_gb']:.1f}GB / {stats['system_stats']['gpu_memory_total_gb']:.1f}GB ({stats['system_stats']['gpu_memory_percent']:.1f}%)")
            if stats['system_stats']['gpu_temperature'] > 0:
                print(f"   GPU温度: {stats['system_stats']['gpu_temperature']:.1f}°C")
        
        print(f"\n⏱️  平均处理时间:")
        print(f"   截图时间: {stats['timing_stats']['avg_screenshot_time']:.2f}ms")
        print(f"   AI推理时间: {stats['timing_stats']['avg_ai_time']:.2f}ms")
        print(f"   后处理时间: {stats['timing_stats']['avg_postprocess_time']:.2f}ms")
        print(f"   总帧时间: {stats['performance_stats']['avg_frame_time']:.2f}±{stats['performance_stats']['frame_time_std']:.2f}ms")
        
        print(f"\n📈 处理计数:")
        print(f"   截图次数: {stats['counters']['screenshot_count']}")
        print(f"   AI推理次数: {stats['counters']['ai_inference_count']}")
        print(f"   检测次数: {stats['counters']['detection_count']}")
        print(f"   处理帧数: {stats['counters']['frame_processed_count']}")
        print(f"   鼠标移动次数: {stats['counters']['mouse_move_count']}")
        print(f"   扳机触发次数: {stats['counters']['trigger_count']}")
    
    def print_realtime_fps(self):
        """打印实时FPS（单行显示）"""
        current_fps = self.get_current_fps()
        system_stats = self.get_system_stats()
        
        fps_text = f"📊 FPS: 截图{current_fps['screenshot_fps']:.0f} | AI{current_fps['ai_fps']:.0f} | 检测{current_fps['detection_fps']:.0f} | 总体{current_fps['overall_fps']:.0f}"
        resource_text = f"💻 CPU{system_stats['cpu_percent']:.0f}% | 内存{system_stats['memory_percent']:.0f}%"
        
        if self.enable_gpu_monitoring and system_stats['gpu_percent'] > 0:
            resource_text += f" | GPU{system_stats['gpu_percent']:.0f}%"
        
        print(f"\r{fps_text} | {resource_text}", end="", flush=True)
    
    def reset_counters(self):
        """重置计数器"""
        with self.stats_lock:
            for key in self.counters:
                self.counters[key] = 0
            self.last_counters = self.counters.copy()
        
        print("[INFO] 📊 性能计数器已重置")
    
    def cleanup(self):
        """清理资源"""
        self.stop()
        print("[INFO] ✅ 性能监控系统资源已清理")

def create_performance_monitor(**kwargs):
    """创建性能监控系统"""
    return PerformanceMonitorSystem(**kwargs)

if __name__ == "__main__":
    # 测试性能监控系统
    monitor = create_performance_monitor(
        update_interval=1.0,
        enable_gpu_monitoring=True,
        enable_detailed_stats=True
    )
    
    try:
        monitor.start()
        
        print("[INFO] 测试运行30秒...")
        start_time = time.time()
        
        # 模拟性能数据
        while time.time() - start_time < 30:
            # 模拟计数器增加
            monitor.increment_counter('screenshot_count')
            monitor.increment_counter('ai_inference_count')
            monitor.increment_counter('detection_count')
            monitor.increment_counter('frame_processed_count')
            
            # 模拟时间记录
            monitor.record_timing('screenshot_time', 0.003)  # 3ms
            monitor.record_timing('ai_inference_time', 0.008)  # 8ms
            monitor.record_timing('postprocess_time', 0.002)  # 2ms
            monitor.record_timing('total_frame_time', 0.013)  # 13ms
            
            # 每5秒打印一次详细统计
            if int(time.time() - start_time) % 5 == 0:
                monitor.print_performance_summary()
            else:
                monitor.print_realtime_fps()
            
            time.sleep(0.01)  # 100FPS模拟
        
        print("\n")
        monitor.print_performance_summary()
        
    finally:
        monitor.cleanup()
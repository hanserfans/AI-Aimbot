
# GPU利用率监控脚本
import time
import threading
import psutil
import os

class GPUMonitor:
    """GPU监控器"""
    
    def __init__(self, monitor_interval=5.0, enable_monitoring=True):
        """
        初始化GPU监控器
        
        Args:
            monitor_interval (float): 监控间隔时间（秒），默认5秒
            enable_monitoring (bool): 是否启用监控，默认True
        """
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = monitor_interval
        self.enable_monitoring = enable_monitoring
        
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("[INFO] 🔍 GPU监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("[INFO] 🔍 GPU监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 检查是否启用监控
                if not self.enable_monitoring:
                    time.sleep(self.monitor_interval)
                    continue
                
                # 获取GPU信息
                handle = nvmlDeviceGetHandleByIndex(0)
                
                # GPU负载
                utilization = nvmlDeviceGetUtilizationRates(handle)
                gpu_load = utilization.gpu
                
                # 显存使用
                memory_info = nvmlDeviceGetMemoryInfo(handle)
                memory_used_gb = memory_info.used / (1024**3)
                memory_total_gb = memory_info.total / (1024**3)
                memory_usage_percent = (memory_info.used / memory_info.total) * 100
                
                # 系统内存使用
                memory = psutil.virtual_memory()
                system_memory_used_gb = memory.used / (1024**3)
                system_memory_total_gb = memory.total / (1024**3)
                system_memory_usage_percent = memory.percent
                
                print(f"[MONITOR] GPU负载: {gpu_load}% | 显存: {memory_used_gb:.1f}GB/{memory_total_gb:.1f}GB ({memory_usage_percent:.1f}%) | 系统内存: {system_memory_used_gb:.1f}GB/{system_memory_total_gb:.1f}GB ({system_memory_usage_percent:.1f}%)")
                
            except Exception as e:
                print(f"[MONITOR] 监控错误: {e}")
            
            time.sleep(self.monitor_interval)  # 使用可配置的监控间隔

# 全局监控器
_gpu_monitor = None

def start_gpu_monitoring(monitor_interval=10.0, enable_monitoring=True):
    """
    启动GPU监控
    
    Args:
        monitor_interval (float): 监控间隔时间（秒），默认10秒（降低频率）
        enable_monitoring (bool): 是否启用监控，默认True
    """
    global _gpu_monitor
    if _gpu_monitor is None:
        _gpu_monitor = GPUMonitor(monitor_interval, enable_monitoring)
    _gpu_monitor.start_monitoring()

def stop_gpu_monitoring():
    """停止GPU监控"""
    global _gpu_monitor
    if _gpu_monitor:
        _gpu_monitor.stop_monitoring()

def disable_gpu_monitoring():
    """完全禁用GPU监控（用于高性能模式）"""
    global _gpu_monitor
    if _gpu_monitor:
        _gpu_monitor.enable_monitoring = False
        print("[INFO] GPU监控已禁用以提升性能")

def enable_gpu_monitoring():
    """重新启用GPU监控"""
    global _gpu_monitor
    if _gpu_monitor:
        _gpu_monitor.enable_monitoring = True
        print("[INFO] GPU监控已重新启用")

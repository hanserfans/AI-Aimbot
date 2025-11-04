#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU实时监控器
监控GPU使用率、显存使用、系统内存等关键指标
"""

import time
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any
import psutil
import GPUtil
import torch

class GPURealtimeMonitor:
    """GPU实时监控器"""
    
    def __init__(self, monitor_interval: float = 2.0):
        self.monitor_interval = monitor_interval
        self.monitoring = False
        self.data_history = []
        self.start_time = None
        
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'gpu_available': torch.cuda.is_available(),
            'gpu_info': [],
            'system_memory': {},
            'cpu_usage': psutil.cpu_percent(interval=0.1)
        }
        
        # GPU信息
        if torch.cuda.is_available():
            try:
                gpus = GPUtil.getGPUs()
                for i, gpu in enumerate(gpus):
                    gpu_info = {
                        'id': i,
                        'name': gpu.name,
                        'utilization': gpu.load * 100,
                        'memory_used': gpu.memoryUsed,
                        'memory_total': gpu.memoryTotal,
                        'memory_util': gpu.memoryUtil * 100,
                        'temperature': gpu.temperature
                    }
                    stats['gpu_info'].append(gpu_info)
            except Exception as e:
                stats['gpu_error'] = str(e)
        
        # 系统内存
        memory = psutil.virtual_memory()
        stats['system_memory'] = {
            'total_gb': memory.total / 1024**3,
            'available_gb': memory.available / 1024**3,
            'used_percent': memory.percent,
            'used_gb': memory.used / 1024**3
        }
        
        return stats
    
    def format_progress_bar(self, value: float, max_value: float = 100, width: int = 30) -> str:
        """格式化进度条"""
        percentage = min(value / max_value, 1.0)
        filled = int(width * percentage)
        bar = '█' * filled + '░' * (width - filled)
        
        # 颜色编码
        if percentage < 0.3:
            color = '\033[92m'  # 绿色
        elif percentage < 0.7:
            color = '\033[93m'  # 黄色
        else:
            color = '\033[91m'  # 红色
        
        reset = '\033[0m'
        return f"{color}[{bar}]{reset} {value:.1f}%"
    
    def calculate_trends(self) -> Dict[str, str]:
        """计算趋势"""
        if len(self.data_history) < 2:
            return {}
        
        current = self.data_history[-1]
        previous = self.data_history[-2]
        trends = {}
        
        if current['gpu_info'] and previous['gpu_info']:
            gpu_util_diff = current['gpu_info'][0]['utilization'] - previous['gpu_info'][0]['utilization']
            if gpu_util_diff > 1:
                trends['gpu_util'] = '📈 ↗️'
            elif gpu_util_diff < -1:
                trends['gpu_util'] = '📉 ↘️'
            else:
                trends['gpu_util'] = '➡️'
        
        memory_diff = current['system_memory']['used_percent'] - previous['system_memory']['used_percent']
        if memory_diff > 1:
            trends['memory'] = '📈 ↗️'
        elif memory_diff < -1:
            trends['memory'] = '📉 ↘️'
        else:
            trends['memory'] = '➡️'
        
        return trends
    
    def display_monitor_screen(self, stats: Dict[str, Any]):
        """显示监控界面"""
        self.clear_screen()
        
        # 标题
        print("🎯 GPU实时监控器")
        print("=" * 80)
        
        # 运行时间
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"⏱️ 运行时间: {int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}")
        
        print(f"🕒 当前时间: {stats['timestamp']}")
        print(f"🔄 更新间隔: {self.monitor_interval}秒")
        print()
        
        # GPU信息
        if stats['gpu_info']:
            gpu = stats['gpu_info'][0]
            trends = self.calculate_trends()
            
            print("🎮 GPU状态:")
            print(f"  📱 设备: {gpu['name']}")
            print(f"  🔥 温度: {gpu['temperature']:.0f}°C")
            print()
            
            # GPU使用率
            gpu_trend = trends.get('gpu_util', '')
            print(f"  ⚡ GPU使用率: {gpu_trend}")
            print(f"     {self.format_progress_bar(gpu['utilization'])}")
            print()
            
            # 显存使用
            memory_used_gb = gpu['memory_used'] / 1024
            memory_total_gb = gpu['memory_total'] / 1024
            print(f"  💾 显存使用:")
            print(f"     {self.format_progress_bar(gpu['memory_util'])}")
            print(f"     {memory_used_gb:.1f}GB / {memory_total_gb:.1f}GB")
            print()
        
        # 系统内存
        memory = stats['system_memory']
        memory_trend = self.calculate_trends().get('memory', '')
        print("🖥️ 系统内存:")
        print(f"  📊 内存使用: {memory_trend}")
        print(f"     {self.format_progress_bar(memory['used_percent'])}")
        print(f"     {memory['used_gb']:.1f}GB / {memory['total_gb']:.1f}GB")
        print(f"  💚 可用内存: {memory['available_gb']:.1f}GB")
        print()
        
        # CPU使用率
        print(f"🔧 CPU使用率:")
        print(f"     {self.format_progress_bar(stats['cpu_usage'])}")
        print()
        
        # 性能分析
        self.display_performance_analysis(stats)
        
        # 控制提示
        print("=" * 80)
        print("💡 控制: Ctrl+C 停止监控")
        print("=" * 80)
    
    def display_performance_analysis(self, stats: Dict[str, Any]):
        """显示性能分析"""
        print("📈 性能分析:")
        
        if stats['gpu_info']:
            gpu = stats['gpu_info'][0]
            memory = stats['system_memory']
            
            # GPU利用率分析
            if gpu['utilization'] < 30:
                print("  ⚠️ GPU使用率偏低 - 可能存在CPU瓶颈或任务未充分利用GPU")
            elif gpu['utilization'] > 90:
                print("  🔥 GPU使用率很高 - 性能良好，注意散热")
            else:
                print("  ✅ GPU使用率正常")
            
            # 显存分析
            if gpu['memory_util'] < 30:
                print("  💾 显存使用率偏低 - 可以增加批处理大小或模型复杂度")
            elif gpu['memory_util'] > 90:
                print("  ⚠️ 显存使用率很高 - 注意避免显存溢出")
            else:
                print("  ✅ 显存使用率正常")
            
            # 系统内存分析
            if memory['used_percent'] > 90:
                print("  🚨 系统内存严重不足 - 建议关闭其他程序或增加内存")
            elif memory['used_percent'] > 80:
                print("  ⚠️ 系统内存使用率较高 - 建议优化内存使用")
            else:
                print("  ✅ 系统内存使用正常")
            
            # 温度分析
            if gpu['temperature'] > 80:
                print("  🌡️ GPU温度较高 - 注意散热，可能需要降低性能")
            elif gpu['temperature'] > 70:
                print("  🌡️ GPU温度正常偏高 - 注意散热")
            else:
                print("  ❄️ GPU温度正常")
        
        print()
    
    def save_monitoring_data(self):
        """保存监控数据"""
        if not self.data_history:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"gpu_monitor_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.data_history, f, indent=2, ensure_ascii=False)
            print(f"\n💾 监控数据已保存到: {filename}")
        except Exception as e:
            print(f"\n❌ 数据保存失败: {e}")
    
    def start_monitoring(self):
        """开始监控"""
        print("🚀 启动GPU实时监控...")
        print("按 Ctrl+C 停止监控")
        time.sleep(2)
        
        self.monitoring = True
        self.start_time = time.time()
        
        try:
            while self.monitoring:
                # 获取系统状态
                stats = self.get_system_stats()
                self.data_history.append(stats)
                
                # 限制历史数据长度
                if len(self.data_history) > 1000:
                    self.data_history = self.data_history[-500:]
                
                # 显示监控界面
                self.display_monitor_screen(stats)
                
                # 等待下次更新
                time.sleep(self.monitor_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ 监控已停止")
            self.monitoring = False
            
            # 保存数据
            if len(self.data_history) > 10:
                save_choice = input("\n💾 是否保存监控数据? (y/n): ").lower().strip()
                if save_choice in ['y', 'yes', '是']:
                    self.save_monitoring_data()
            
            print("👋 感谢使用GPU监控器！")
        
        except Exception as e:
            print(f"\n❌ 监控异常: {e}")
            self.monitoring = False

def main():
    """主函数"""
    print("🎯 GPU实时监控器")
    print("=" * 50)
    
    # 检查GPU可用性
    if not torch.cuda.is_available():
        print("❌ 未检测到可用的CUDA GPU")
        return False
    
    try:
        # 设置监控间隔
        interval = 2.0
        try:
            user_interval = input(f"⏱️ 设置监控间隔 (默认{interval}秒): ").strip()
            if user_interval:
                interval = float(user_interval)
                if interval < 0.5:
                    interval = 0.5
                    print("⚠️ 最小间隔为0.5秒")
        except ValueError:
            print("⚠️ 输入无效，使用默认间隔")
        
        # 创建监控器
        monitor = GPURealtimeMonitor(monitor_interval=interval)
        
        # 开始监控
        monitor.start_monitoring()
        
        return True
        
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        return False

if __name__ == "__main__":
    main()
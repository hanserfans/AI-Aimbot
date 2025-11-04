#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一内存性能对比测试
对比传统GPU内存管理与CUDA统一内存的性能差异
测试内存使用效率、处理速度和系统稳定性
"""

import numpy as np
import cv2
import time
import gc
import psutil
import os
import sys
from typing import Dict, List, Tuple, Any
import torch
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

# 导入测试模块
try:
    from gpu_accelerated_processor import get_gpu_processor
    from unified_memory_gpu_processor import get_unified_gpu_processor
    from gpu_memory_manager import get_gpu_memory_manager
    GPU_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] GPU模块导入失败: {e}")
    GPU_MODULES_AVAILABLE = False

class UnifiedMemoryPerformanceTest:
    """统一内存性能测试器"""
    
    def __init__(self, test_duration_minutes: int = 5, save_results: bool = True):
        """
        初始化性能测试器
        
        Args:
            test_duration_minutes: 测试持续时间(分钟)
            save_results: 是否保存测试结果
        """
        self.test_duration = test_duration_minutes * 60  # 转换为秒
        self.save_results = save_results
        
        # 测试结果存储
        self.results = {
            'traditional_gpu': {
                'processing_times': [],
                'memory_usage': [],
                'gpu_memory_usage': [],
                'cpu_usage': [],
                'errors': 0,
                'total_processed': 0
            },
            'unified_memory': {
                'processing_times': [],
                'memory_usage': [],
                'gpu_memory_usage': [],
                'cpu_usage': [],
                'errors': 0,
                'total_processed': 0
            }
        }
        
        # 测试配置
        self.test_configs = [
            # (image_size, batch_size, description)
            ((320, 320), 1, "小图像单张处理"),
            ((640, 640), 1, "中等图像单张处理"),
            ((1920, 1080), 1, "大图像单张处理"),
            ((320, 320), 4, "小图像批处理"),
            ((640, 640), 2, "中等图像批处理"),
        ]
        
        print(f"[INFO] 🧪 统一内存性能测试器初始化完成")
        print(f"[INFO] 测试时长: {test_duration_minutes}分钟")
        print(f"[INFO] 测试配置: {len(self.test_configs)}种场景")
        
    def generate_test_images(self, size: Tuple[int, int], batch_size: int) -> List[np.ndarray]:
        """生成测试图像"""
        images = []
        for i in range(batch_size):
            # 生成随机图像，模拟真实场景
            img = np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)
            
            # 添加一些图像特征，模拟目标检测场景
            # 添加矩形框
            cv2.rectangle(img, (50, 50), (size[0]-50, size[1]-50), (255, 0, 0), 2)
            # 添加圆形
            cv2.circle(img, (size[0]//2, size[1]//2), min(size)//4, (0, 255, 0), -1)
            
            images.append(img)
            
        return images
        
    def get_system_metrics(self) -> Dict[str, float]:
        """获取系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            
            # GPU内存使用情况
            gpu_memory_used = 0
            gpu_memory_total = 0
            
            if torch.cuda.is_available():
                gpu_memory_used = torch.cuda.memory_allocated() / (1024**3)
                gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_used_gb': memory_used_gb,
                'gpu_memory_used_gb': gpu_memory_used,
                'gpu_memory_total_gb': gpu_memory_total,
                'gpu_memory_percent': (gpu_memory_used / gpu_memory_total * 100) if gpu_memory_total > 0 else 0
            }
            
        except Exception as e:
            print(f"[WARNING] 获取系统指标失败: {e}")
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'memory_used_gb': 0,
                'gpu_memory_used_gb': 0,
                'gpu_memory_total_gb': 0,
                'gpu_memory_percent': 0
            }
            
    def test_traditional_gpu_processing(self, images: List[np.ndarray], 
                                      target_size: Tuple[int, int]) -> Dict[str, Any]:
        """测试传统GPU处理性能"""
        try:
            # 获取传统GPU处理器
            gpu_processor = get_gpu_processor(device_id=0)
            
            start_time = time.time()
            processed_images = []
            
            # 处理所有图像
            for img in images:
                processed = gpu_processor.preprocess_image_gpu(img, target_size)
                processed_images.append(processed)
                
            processing_time = time.time() - start_time
            
            # 获取系统指标
            metrics = self.get_system_metrics()
            
            return {
                'processing_time': processing_time,
                'processed_count': len(images),
                'avg_time_per_image': processing_time / len(images),
                'metrics': metrics,
                'success': True
            }
            
        except Exception as e:
            print(f"[ERROR] 传统GPU处理测试失败: {e}")
            return {
                'processing_time': float('inf'),
                'processed_count': 0,
                'avg_time_per_image': float('inf'),
                'metrics': self.get_system_metrics(),
                'success': False,
                'error': str(e)
            }
            
    def test_unified_memory_processing(self, images: List[np.ndarray], 
                                     target_size: Tuple[int, int],
                                     access_pattern: str = 'mixed') -> Dict[str, Any]:
        """测试统一内存处理性能"""
        try:
            # 获取统一内存GPU处理器
            unified_processor = get_unified_gpu_processor(device_id=0, unified_memory_size_gb=2.0)
            
            start_time = time.time()
            processed_images = []
            
            # 处理所有图像
            for img in images:
                processed = unified_processor.preprocess_image_unified(
                    img, target_size, access_pattern=access_pattern
                )
                processed_images.append(processed)
                
            processing_time = time.time() - start_time
            
            # 获取系统指标
            metrics = self.get_system_metrics()
            
            # 获取统一内存特定指标
            unified_stats = unified_processor.get_unified_memory_stats()
            
            return {
                'processing_time': processing_time,
                'processed_count': len(images),
                'avg_time_per_image': processing_time / len(images),
                'metrics': metrics,
                'unified_stats': unified_stats,
                'success': True
            }
            
        except Exception as e:
            print(f"[ERROR] 统一内存处理测试失败: {e}")
            return {
                'processing_time': float('inf'),
                'processed_count': 0,
                'avg_time_per_image': float('inf'),
                'metrics': self.get_system_metrics(),
                'unified_stats': {},
                'success': False,
                'error': str(e)
            }
            
    def run_single_test_scenario(self, config: Tuple) -> Dict[str, Any]:
        """运行单个测试场景"""
        image_size, batch_size, description = config
        
        print(f"\n[TEST] 🔄 测试场景: {description}")
        print(f"  图像尺寸: {image_size}")
        print(f"  批处理大小: {batch_size}")
        
        # 生成测试图像
        test_images = self.generate_test_images(image_size, batch_size)
        
        # 测试传统GPU处理
        print("  [1/3] 测试传统GPU处理...")
        traditional_result = self.test_traditional_gpu_processing(test_images, image_size)
        
        # 清理GPU内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
        time.sleep(1)  # 等待内存清理
        
        # 测试统一内存处理 - 混合模式
        print("  [2/3] 测试统一内存处理(混合模式)...")
        unified_mixed_result = self.test_unified_memory_processing(test_images, image_size, 'mixed')
        
        # 清理GPU内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
        time.sleep(1)
        
        # 测试统一内存处理 - GPU重度模式
        print("  [3/3] 测试统一内存处理(GPU重度模式)...")
        unified_gpu_result = self.test_unified_memory_processing(test_images, image_size, 'gpu_heavy')
        
        # 清理GPU内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
        
        return {
            'config': config,
            'traditional_gpu': traditional_result,
            'unified_mixed': unified_mixed_result,
            'unified_gpu_heavy': unified_gpu_result
        }
        
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行综合性能测试"""
        print(f"\n[INFO] 🚀 开始综合性能测试...")
        print(f"[INFO] 预计测试时间: {self.test_duration/60:.1f}分钟")
        
        if not GPU_MODULES_AVAILABLE:
            print("[ERROR] GPU模块不可用，无法进行测试")
            return {}
            
        test_start_time = time.time()
        scenario_results = []
        
        # 运行每个测试场景
        for i, config in enumerate(self.test_configs):
            print(f"\n[PROGRESS] 测试进度: {i+1}/{len(self.test_configs)}")
            
            scenario_result = self.run_single_test_scenario(config)
            scenario_results.append(scenario_result)
            
            # 检查是否超时
            elapsed_time = time.time() - test_start_time
            if elapsed_time > self.test_duration:
                print(f"[INFO] ⏰ 达到测试时间限制，停止测试")
                break
                
        total_test_time = time.time() - test_start_time
        
        # 汇总结果
        summary = self.analyze_test_results(scenario_results, total_test_time)
        
        # 保存结果
        if self.save_results:
            self.save_test_results(scenario_results, summary)
            
        return {
            'scenario_results': scenario_results,
            'summary': summary,
            'total_test_time': total_test_time
        }
        
    def analyze_test_results(self, scenario_results: List[Dict], 
                           total_test_time: float) -> Dict[str, Any]:
        """分析测试结果"""
        print(f"\n[INFO] 📊 分析测试结果...")
        
        # 收集性能数据
        traditional_times = []
        unified_mixed_times = []
        unified_gpu_times = []
        
        traditional_memory = []
        unified_mixed_memory = []
        unified_gpu_memory = []
        
        success_rates = {
            'traditional': 0,
            'unified_mixed': 0,
            'unified_gpu': 0
        }
        
        for result in scenario_results:
            # 处理时间
            if result['traditional_gpu']['success']:
                traditional_times.append(result['traditional_gpu']['avg_time_per_image'])
                traditional_memory.append(result['traditional_gpu']['metrics']['memory_percent'])
                success_rates['traditional'] += 1
                
            if result['unified_mixed']['success']:
                unified_mixed_times.append(result['unified_mixed']['avg_time_per_image'])
                unified_mixed_memory.append(result['unified_mixed']['metrics']['memory_percent'])
                success_rates['unified_mixed'] += 1
                
            if result['unified_gpu_heavy']['success']:
                unified_gpu_times.append(result['unified_gpu_heavy']['avg_time_per_image'])
                unified_gpu_memory.append(result['unified_gpu_heavy']['metrics']['memory_percent'])
                success_rates['unified_gpu'] += 1
                
        # 计算平均性能
        def safe_mean(data):
            return np.mean(data) if data else float('inf')
            
        avg_traditional_time = safe_mean(traditional_times)
        avg_unified_mixed_time = safe_mean(unified_mixed_times)
        avg_unified_gpu_time = safe_mean(unified_gpu_times)
        
        avg_traditional_memory = safe_mean(traditional_memory)
        avg_unified_mixed_memory = safe_mean(unified_mixed_memory)
        avg_unified_gpu_memory = safe_mean(unified_gpu_memory)
        
        # 计算性能提升
        def calculate_improvement(baseline, optimized):
            if baseline == 0 or baseline == float('inf') or optimized == float('inf'):
                return 0
            return ((baseline - optimized) / baseline) * 100
            
        mixed_speed_improvement = calculate_improvement(avg_traditional_time, avg_unified_mixed_time)
        gpu_speed_improvement = calculate_improvement(avg_traditional_time, avg_unified_gpu_time)
        
        mixed_memory_improvement = calculate_improvement(avg_traditional_memory, avg_unified_mixed_memory)
        gpu_memory_improvement = calculate_improvement(avg_traditional_memory, avg_unified_gpu_memory)
        
        summary = {
            'test_scenarios': len(scenario_results),
            'total_test_time_minutes': total_test_time / 60,
            
            # 平均处理时间 (毫秒)
            'avg_processing_time_ms': {
                'traditional_gpu': avg_traditional_time * 1000,
                'unified_mixed': avg_unified_mixed_time * 1000,
                'unified_gpu_heavy': avg_unified_gpu_time * 1000
            },
            
            # 平均内存使用率 (%)
            'avg_memory_usage_percent': {
                'traditional_gpu': avg_traditional_memory,
                'unified_mixed': avg_unified_mixed_memory,
                'unified_gpu_heavy': avg_unified_gpu_memory
            },
            
            # 性能提升 (%)
            'performance_improvement_percent': {
                'unified_mixed_speed': mixed_speed_improvement,
                'unified_gpu_speed': gpu_speed_improvement,
                'unified_mixed_memory': mixed_memory_improvement,
                'unified_gpu_memory': gpu_memory_improvement
            },
            
            # 成功率
            'success_rates': {
                'traditional_gpu': success_rates['traditional'] / len(scenario_results) * 100,
                'unified_mixed': success_rates['unified_mixed'] / len(scenario_results) * 100,
                'unified_gpu_heavy': success_rates['unified_gpu'] / len(scenario_results) * 100
            }
        }
        
        return summary
        
    def print_test_summary(self, summary: Dict[str, Any]):
        """打印测试摘要"""
        print(f"\n" + "="*60)
        print(f"📊 统一内存性能测试报告")
        print(f"="*60)
        
        print(f"\n🔍 测试概况:")
        print(f"  测试场景数量: {summary['test_scenarios']}")
        print(f"  总测试时间: {summary['total_test_time_minutes']:.1f}分钟")
        
        print(f"\n⚡ 平均处理时间 (每张图像):")
        times = summary['avg_processing_time_ms']
        print(f"  传统GPU处理: {times['traditional_gpu']:.2f}ms")
        print(f"  统一内存(混合): {times['unified_mixed']:.2f}ms")
        print(f"  统一内存(GPU重度): {times['unified_gpu_heavy']:.2f}ms")
        
        print(f"\n💾 平均内存使用率:")
        memory = summary['avg_memory_usage_percent']
        print(f"  传统GPU处理: {memory['traditional_gpu']:.1f}%")
        print(f"  统一内存(混合): {memory['unified_mixed']:.1f}%")
        print(f"  统一内存(GPU重度): {memory['unified_gpu_heavy']:.1f}%")
        
        print(f"\n📈 性能提升:")
        improvements = summary['performance_improvement_percent']
        print(f"  统一内存(混合)速度提升: {improvements['unified_mixed_speed']:+.1f}%")
        print(f"  统一内存(GPU重度)速度提升: {improvements['unified_gpu_speed']:+.1f}%")
        print(f"  统一内存(混合)内存优化: {improvements['unified_mixed_memory']:+.1f}%")
        print(f"  统一内存(GPU重度)内存优化: {improvements['unified_gpu_memory']:+.1f}%")
        
        print(f"\n✅ 成功率:")
        success = summary['success_rates']
        print(f"  传统GPU处理: {success['traditional_gpu']:.1f}%")
        print(f"  统一内存(混合): {success['unified_mixed']:.1f}%")
        print(f"  统一内存(GPU重度): {success['unified_gpu_heavy']:.1f}%")
        
        # 推荐建议
        print(f"\n💡 优化建议:")
        
        best_speed = max(improvements['unified_mixed_speed'], improvements['unified_gpu_speed'])
        best_memory = max(improvements['unified_mixed_memory'], improvements['unified_gpu_memory'])
        
        if best_speed > 10:
            print(f"  ✅ 统一内存显著提升处理速度 ({best_speed:.1f}%)")
        elif best_speed > 0:
            print(f"  ⚠️ 统一内存轻微提升处理速度 ({best_speed:.1f}%)")
        else:
            print(f"  ❌ 统一内存未能提升处理速度")
            
        if best_memory > 5:
            print(f"  ✅ 统一内存显著优化内存使用 ({best_memory:.1f}%)")
        elif best_memory > 0:
            print(f"  ⚠️ 统一内存轻微优化内存使用 ({best_memory:.1f}%)")
        else:
            print(f"  ❌ 统一内存未能优化内存使用")
            
        if improvements['unified_gpu_speed'] > improvements['unified_mixed_speed']:
            print(f"  🎯 推荐使用GPU重度访问模式")
        else:
            print(f"  🎯 推荐使用混合访问模式")
            
        print(f"\n" + "="*60)
        
    def save_test_results(self, scenario_results: List[Dict], summary: Dict[str, Any]):
        """保存测试结果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存详细结果
            results_file = f"unified_memory_test_results_{timestamp}.json"
            import json
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'scenario_results': scenario_results,
                    'summary': summary,
                    'timestamp': timestamp
                }, f, indent=2, ensure_ascii=False, default=str)
                
            print(f"[INFO] 💾 测试结果已保存到: {results_file}")
            
            # 生成性能图表
            self.generate_performance_charts(scenario_results, summary, timestamp)
            
        except Exception as e:
            print(f"[WARNING] 保存测试结果失败: {e}")
            
    def generate_performance_charts(self, scenario_results: List[Dict], 
                                  summary: Dict[str, Any], timestamp: str):
        """生成性能对比图表"""
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # 图1: 处理时间对比
            methods = ['传统GPU', '统一内存(混合)', '统一内存(GPU重度)']
            times = [
                summary['avg_processing_time_ms']['traditional_gpu'],
                summary['avg_processing_time_ms']['unified_mixed'],
                summary['avg_processing_time_ms']['unified_gpu_heavy']
            ]
            
            bars1 = ax1.bar(methods, times, color=['#ff7f0e', '#2ca02c', '#1f77b4'])
            ax1.set_title('平均处理时间对比', fontsize=14, fontweight='bold')
            ax1.set_ylabel('处理时间 (毫秒)')
            ax1.grid(True, alpha=0.3)
            
            # 添加数值标签
            for bar, time in zip(bars1, times):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{time:.1f}ms', ha='center', va='bottom')
            
            # 图2: 内存使用率对比
            memory_usage = [
                summary['avg_memory_usage_percent']['traditional_gpu'],
                summary['avg_memory_usage_percent']['unified_mixed'],
                summary['avg_memory_usage_percent']['unified_gpu_heavy']
            ]
            
            bars2 = ax2.bar(methods, memory_usage, color=['#ff7f0e', '#2ca02c', '#1f77b4'])
            ax2.set_title('平均内存使用率对比', fontsize=14, fontweight='bold')
            ax2.set_ylabel('内存使用率 (%)')
            ax2.grid(True, alpha=0.3)
            
            for bar, usage in zip(bars2, memory_usage):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{usage:.1f}%', ha='center', va='bottom')
            
            # 图3: 性能提升百分比
            improvements = [
                summary['performance_improvement_percent']['unified_mixed_speed'],
                summary['performance_improvement_percent']['unified_gpu_speed'],
                summary['performance_improvement_percent']['unified_mixed_memory'],
                summary['performance_improvement_percent']['unified_gpu_memory']
            ]
            
            improvement_labels = ['混合模式\n速度提升', 'GPU重度\n速度提升', '混合模式\n内存优化', 'GPU重度\n内存优化']
            colors = ['#2ca02c' if x > 0 else '#d62728' for x in improvements]
            
            bars3 = ax3.bar(improvement_labels, improvements, color=colors)
            ax3.set_title('性能提升百分比', fontsize=14, fontweight='bold')
            ax3.set_ylabel('提升百分比 (%)')
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax3.grid(True, alpha=0.3)
            
            for bar, improvement in zip(bars3, improvements):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., 
                        height + (1 if height >= 0 else -3),
                        f'{improvement:+.1f}%', ha='center', 
                        va='bottom' if height >= 0 else 'top')
            
            # 图4: 成功率对比
            success_rates = [
                summary['success_rates']['traditional_gpu'],
                summary['success_rates']['unified_mixed'],
                summary['success_rates']['unified_gpu_heavy']
            ]
            
            bars4 = ax4.bar(methods, success_rates, color=['#ff7f0e', '#2ca02c', '#1f77b4'])
            ax4.set_title('测试成功率对比', fontsize=14, fontweight='bold')
            ax4.set_ylabel('成功率 (%)')
            ax4.set_ylim(0, 105)
            ax4.grid(True, alpha=0.3)
            
            for bar, rate in zip(bars4, success_rates):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{rate:.1f}%', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # 保存图表
            chart_file = f"unified_memory_performance_chart_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"[INFO] 📊 性能图表已保存到: {chart_file}")
            
        except Exception as e:
            print(f"[WARNING] 生成性能图表失败: {e}")

def main():
    """主函数"""
    print("[INFO] 🚀 启动统一内存性能测试...")
    
    # 检查GPU可用性
    if not torch.cuda.is_available():
        print("[ERROR] CUDA不可用，无法进行GPU测试")
        return
        
    print(f"[INFO] GPU设备: {torch.cuda.get_device_name()}")
    print(f"[INFO] GPU内存: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.1f}GB")
    
    # 创建测试器
    tester = UnifiedMemoryPerformanceTest(test_duration_minutes=3, save_results=True)
    
    # 运行测试
    results = tester.run_comprehensive_test()
    
    if results:
        # 打印摘要
        tester.print_test_summary(results['summary'])
        
        print(f"\n[INFO] ✅ 性能测试完成!")
        print(f"[INFO] 总测试时间: {results['total_test_time']:.1f}秒")
    else:
        print(f"[ERROR] 性能测试失败")

if __name__ == "__main__":
    main()
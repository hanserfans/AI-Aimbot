#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存和GPU优化器
解决内存不足、显存过量和双GPU利用率问题
"""

import gc
import os
import sys
import psutil
import time
import onnxruntime as ort
import numpy as np
from typing import List, Dict, Any

class MemoryGPUOptimizer:
    """内存和GPU优化器"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage()
        self.gpu_providers = []
        self.optimized_session_options = None
        
    def get_memory_usage(self) -> Dict[str, float]:
        """获取当前内存使用情况"""
        memory_info = self.process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            'process_memory_mb': memory_info.rss / 1024 / 1024,
            'system_memory_percent': system_memory.percent,
            'system_available_gb': system_memory.available / 1024 / 1024 / 1024
        }
    
    def analyze_gpu_providers(self) -> List[str]:
        """分析可用的GPU提供者"""
        available_providers = ort.get_available_providers()
        print(f"[INFO] 可用的ONNX提供者: {available_providers}")
        
        # 优先级排序的提供者列表
        priority_providers = [
            'CUDAExecutionProvider',    # NVIDIA GPU
            'DmlExecutionProvider',     # DirectML (AMD/Intel GPU)
            'CPUExecutionProvider'      # CPU备用
        ]
        
        # 筛选可用的提供者
        self.gpu_providers = [p for p in priority_providers if p in available_providers]
        print(f"[INFO] 优先使用的提供者: {self.gpu_providers}")
        
        return self.gpu_providers
    
    def optimize_memory_usage(self):
        """优化内存使用"""
        print("[INFO] 🧹 开始内存优化...")
        
        # 强制垃圾回收
        collected = gc.collect()
        print(f"[INFO] 垃圾回收释放了 {collected} 个对象")
        
        # 设置环境变量优化内存
        os.environ['OMP_NUM_THREADS'] = '16'  # 优化OpenMP线程数（32核CPU）
os.environ['MKL_NUM_THREADS'] = '16'  # 优化MKL线程数
os.environ['NUMEXPR_NUM_THREADS'] = '16'  # 优化NumExpr线程数
        
        # 优化NumPy内存使用
        np.seterr(all='ignore')  # 忽略数值警告以减少内存开销
        
        print("[INFO] ✅ 内存优化完成")
    
    def create_optimized_session_options(self) -> ort.SessionOptions:
        """创建优化的ONNX会话选项"""
        print("[INFO] ⚙️ 创建优化的ONNX会话选项...")
        
        so = ort.SessionOptions()
        
        # 图优化设置
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        # 内存优化设置
        so.enable_mem_pattern = True
        so.enable_cpu_mem_arena = True
        
        # 线程设置（减少内存占用）
        so.intra_op_num_threads = 16  # 优化线程数以充分利用32核CPU
        so.inter_op_num_threads = 8   # 增加并行操作线程数
        
        # 执行模式设置
        so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL  # 顺序执行以节省内存
        
        self.optimized_session_options = so
        print("[INFO] ✅ ONNX会话选项优化完成")
        
        return so
    
    def create_dual_gpu_sessions(self, model_path: str) -> Dict[str, Any]:
        """创建双GPU会话配置"""
        print("[INFO] 🔄 配置双GPU负载均衡...")
        
        sessions = {}
        
        try:
            # 获取优化的会话选项
            so = self.create_optimized_session_options()
            
            # 尝试创建NVIDIA GPU会话
            if 'CUDAExecutionProvider' in self.gpu_providers:
                cuda_options = {
                    'device_id': 0,  # 使用第一个NVIDIA GPU
                    'arena_extend_strategy': 'kNextPowerOfTwo',  # 更激进的内存策略
                    'gpu_mem_limit': 6 * 1024 * 1024 * 1024,  # 限制GPU内存为6GB（RTX 4060适配）
                    'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    'do_copy_in_default_stream': True,  # 启用默认流复制
                    'cudnn_conv_use_max_workspace': True,  # 使用最大工作空间
                }
                
                sessions['nvidia'] = ort.InferenceSession(
                    model_path,
                    sess_options=so,
                    providers=[('CUDAExecutionProvider', cuda_options)]
                )
                print("[INFO] ✅ NVIDIA GPU会话创建成功")
            
            # 尝试创建AMD GPU会话
            if 'DmlExecutionProvider' in self.gpu_providers:
                dml_options = {
                    'device_id': 1,  # 尝试使用第二个GPU
                }
                
                sessions['amd'] = ort.InferenceSession(
                    model_path,
                    sess_options=so,
                    providers=[('DmlExecutionProvider', dml_options)]
                )
                print("[INFO] ✅ AMD GPU会话创建成功")
            
            # CPU备用会话
            sessions['cpu'] = ort.InferenceSession(
                model_path,
                sess_options=so,
                providers=['CPUExecutionProvider']
            )
            print("[INFO] ✅ CPU备用会话创建成功")
            
        except Exception as e:
            print(f"[ERROR] 创建GPU会话失败: {e}")
            # 创建CPU备用会话
            sessions['cpu'] = ort.InferenceSession(
                model_path,
                sess_options=self.create_optimized_session_options(),
                providers=['CPUExecutionProvider']
            )
        
        return sessions
    
    def optimize_vram_usage(self) -> Dict[str, Any]:
        """优化显存使用配置"""
        print("[INFO] 💾 优化显存使用配置...")
        
        vram_config = {
            # CUDA配置
            'cuda_options': {
                'arena_extend_strategy': 'kNextPowerOfTwo',  # 更激进的内存分配
                'gpu_mem_limit': 6 * 1024 * 1024 * 1024,  # 限制为6GB（RTX 4060适配）
                'cudnn_conv_algo_search': 'EXHAUSTIVE',  # 使用最优算法
                'do_copy_in_default_stream': True,
                'cudnn_conv_use_max_workspace': True,  # 使用最大工作空间
            },
            
            # DirectML配置
            'dml_options': {
                'device_id': 1,  # 使用第二个GPU
            },
            
            # 会话配置
            'session_options': {
                'enable_mem_pattern': True,
                'enable_cpu_mem_arena': True,
                'execution_mode': 'sequential',
                'intra_op_num_threads': 4,
                'inter_op_num_threads': 2,
            }
        }
        
        print("[INFO] ✅ 显存优化配置完成")
        return vram_config
    
    def monitor_performance(self, duration: int = 10):
        """监控性能指标"""
        print(f"[INFO] 📊 开始监控性能 ({duration}秒)...")
        
        start_time = time.time()
        memory_samples = []
        
        while time.time() - start_time < duration:
            memory_info = self.get_memory_usage()
            memory_samples.append(memory_info)
            time.sleep(1)
        
        # 计算平均值
        avg_memory = {
            'process_memory_mb': sum(s['process_memory_mb'] for s in memory_samples) / len(memory_samples),
            'system_memory_percent': sum(s['system_memory_percent'] for s in memory_samples) / len(memory_samples),
            'system_available_gb': sum(s['system_available_gb'] for s in memory_samples) / len(memory_samples)
        }
        
        print(f"[INFO] 📈 平均内存使用:")
        print(f"  - 进程内存: {avg_memory['process_memory_mb']:.1f} MB")
        print(f"  - 系统内存: {avg_memory['system_memory_percent']:.1f}%")
        print(f"  - 可用内存: {avg_memory['system_available_gb']:.1f} GB")
        
        return avg_memory
    
    def generate_optimized_config(self) -> str:
        """生成优化配置代码"""
        config_code = '''
# 优化的ONNX配置
import onnxruntime as ort
import os

# 设置环境变量优化内存
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['MKL_NUM_THREADS'] = '4'
os.environ['NUMEXPR_NUM_THREADS'] = '4'

def create_optimized_onnx_session(model_path, use_dual_gpu=True):
    """创建优化的ONNX会话"""
    
    # 优化的会话选项
    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    so.enable_mem_pattern = True
    so.enable_cpu_mem_arena = True
    so.intra_op_num_threads = 4
    so.inter_op_num_threads = 2
    so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    
    # 提供者配置
    providers = []
    
    # NVIDIA GPU配置（优化显存使用）
    cuda_options = {
        'device_id': 0,
        'arena_extend_strategy': 'kNextPowerOfTwo',  # 更激进的内存分配
        'gpu_mem_limit': 6 * 1024 * 1024 * 1024,  # 6GB限制（RTX 4060适配）
        'cudnn_conv_algo_search': 'EXHAUSTIVE',  # 使用最优算法
        'do_copy_in_default_stream': True,  # 启用默认流复制
        'cudnn_conv_use_max_workspace': True,  # 使用最大工作空间
    }
    providers.append(('CUDAExecutionProvider', cuda_options))
    
    # AMD GPU配置（如果需要双GPU）
    if use_dual_gpu:
        dml_options = {'device_id': 1}
        providers.append(('DmlExecutionProvider', dml_options))
    
    # CPU备用
    providers.append('CPUExecutionProvider')
    
    try:
        session = ort.InferenceSession(model_path, sess_options=so, providers=providers)
        print(f"[INFO] ONNX会话创建成功，使用提供者: {session.get_providers()}")
        return session
    except Exception as e:
        print(f"[ERROR] ONNX会话创建失败: {e}")
        # 备用CPU会话
        return ort.InferenceSession(model_path, sess_options=so, providers=['CPUExecutionProvider'])
'''
        return config_code
    
    def run_optimization(self, model_path: str = 'yolov5s320Half.onnx'):
        """运行完整优化流程"""
        print("=" * 60)
        print("🚀 AI-Aimbot 内存和GPU优化器")
        print("=" * 60)
        
        # 1. 分析初始状态
        print("\n📊 初始状态分析:")
        initial_memory = self.get_memory_usage()
        print(f"  - 进程内存: {initial_memory['process_memory_mb']:.1f} MB")
        print(f"  - 系统内存: {initial_memory['system_memory_percent']:.1f}%")
        print(f"  - 可用内存: {initial_memory['system_available_gb']:.1f} GB")
        
        # 2. 分析GPU提供者
        print("\n🔍 GPU提供者分析:")
        self.analyze_gpu_providers()
        
        # 3. 优化内存使用
        print("\n🧹 内存优化:")
        self.optimize_memory_usage()
        
        # 4. 优化显存配置
        print("\n💾 显存优化:")
        vram_config = self.optimize_vram_usage()
        
        # 5. 创建优化配置
        print("\n⚙️ 生成优化配置:")
        config_code = self.generate_optimized_config()
        
        # 保存优化配置到文件
        with open('optimized_onnx_config.py', 'w', encoding='utf-8') as f:
            f.write(config_code)
        print("[INFO] ✅ 优化配置已保存到 optimized_onnx_config.py")
        
        # 6. 最终状态检查
        print("\n📈 优化后状态:")
        final_memory = self.get_memory_usage()
        print(f"  - 进程内存: {final_memory['process_memory_mb']:.1f} MB")
        print(f"  - 系统内存: {final_memory['system_memory_percent']:.1f}%")
        print(f"  - 可用内存: {final_memory['system_available_gb']:.1f} GB")
        
        # 计算改善情况
        memory_improvement = initial_memory['system_memory_percent'] - final_memory['system_memory_percent']
        print(f"\n✨ 内存使用改善: {memory_improvement:.1f}%")
        
        print("\n" + "=" * 60)
        print("🎯 优化建议:")
        print("1. 使用生成的 optimized_onnx_config.py 替换现有ONNX配置")
        print("2. 重启AI-Aimbot以应用优化设置")
        print("3. 监控GPU利用率确认双GPU工作状态")
        print("4. 如果内存仍然不足，考虑降低截图分辨率")
        print("=" * 60)

def main():
    """主函数"""
    optimizer = MemoryGPUOptimizer()
    optimizer.run_optimization()

if __name__ == "__main__":
    main()
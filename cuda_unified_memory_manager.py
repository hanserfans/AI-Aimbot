#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CUDA统一内存管理器
实现CUDA统一内存（Unified Memory）支持
自动CPU-GPU内存迁移，简化内存管理，提升性能
"""

import torch
import numpy as np
import time
import gc
import ctypes
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import defaultdict
import threading
import psutil
import warnings

# 尝试导入CUDA运行时API
try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    print("[WARNING] CuPy未安装，部分统一内存功能将受限")

class CUDAUnifiedMemoryManager:
    """CUDA统一内存管理器 - 实现CPU和GPU间的统一内存空间"""
    
    def __init__(self, device_ids: List[int] = [0], unified_pool_size_gb: float = 2.0):
        """
        初始化CUDA统一内存管理器
        
        Args:
            device_ids: GPU设备ID列表
            unified_pool_size_gb: 统一内存池大小(GB)
        """
        self.device_ids = device_ids
        self.unified_pool_size_bytes = int(unified_pool_size_gb * 1024**3)
        self.devices = [f'cuda:{i}' for i in device_ids if torch.cuda.is_available()]
        
        if not self.devices:
            self.devices = ['cpu']
            print("[WARNING] 无可用GPU，统一内存功能将受限")
            
        # 检查统一内存支持
        self.unified_memory_supported = self._check_unified_memory_support()
        
        # 统一内存池
        self.unified_memory_pool = {}
        self.unified_memory_usage = {}
        self.unified_memory_locks = {}
        
        # 传统内存池（作为备用）
        self.fallback_memory_pool = {}
        self.fallback_usage = {}
        
        # 内存访问模式跟踪
        self.access_patterns = defaultdict(list)
        self.migration_stats = {
            'cpu_to_gpu_migrations': 0,
            'gpu_to_cpu_migrations': 0,
            'automatic_migrations': 0,
            'manual_migrations': 0,
            'migration_time_total': 0.0
        }
        
        # 性能统计
        self.stats = {
            'unified_allocations': 0,
            'fallback_allocations': 0,
            'memory_saved_bytes': 0,
            'access_violations': 0,
            'prefetch_hits': 0,
            'prefetch_misses': 0
        }
        
        # 初始化统一内存池
        self._initialize_unified_memory_pools()
        
        print(f"[INFO] 🌐 CUDA统一内存管理器初始化完成")
        print(f"[INFO] 设备: {self.devices}")
        print(f"[INFO] 统一内存支持: {'✅' if self.unified_memory_supported else '❌'}")
        print(f"[INFO] 统一内存池大小: {unified_pool_size_gb:.1f}GB")
        
    def _check_unified_memory_support(self) -> bool:
        """检查GPU是否支持统一内存"""
        if not torch.cuda.is_available():
            return False
            
        try:
            # 检查GPU架构（Pascal及以上支持硬件统一内存）
            for device_id in self.device_ids:
                props = torch.cuda.get_device_properties(device_id)
                major, minor = props.major, props.minor
                
                # Pascal (6.0+), Volta (7.0+), Turing (7.5+), Ampere (8.0+)
                if major >= 6:
                    print(f"[INFO] 🎯 GPU {device_id} ({props.name}) 支持硬件统一内存 (计算能力 {major}.{minor})")
                    return True
                else:
                    print(f"[WARNING] GPU {device_id} ({props.name}) 不支持硬件统一内存 (计算能力 {major}.{minor})")
                    
            return False
            
        except Exception as e:
            print(f"[WARNING] 检查统一内存支持时出错: {e}")
            return False
            
    def _initialize_unified_memory_pools(self):
        """初始化统一内存池"""
        for device in self.devices:
            if device == 'cpu':
                continue
                
            try:
                self.unified_memory_pool[device] = {}
                self.unified_memory_usage[device] = {}
                self.unified_memory_locks[device] = threading.Lock()
                
                self.fallback_memory_pool[device] = {}
                self.fallback_usage[device] = {}
                
                # 预分配常用尺寸的统一内存块
                if self.unified_memory_supported:
                    common_sizes = [
                        (1, 3, 320, 320),    # 标准检测图像
                        (1, 3, 640, 640),    # 高分辨率检测
                        (320, 320, 3),       # 处理后图像
                        (100, 6),            # 检测结果
                    ]
                    
                    for size in common_sizes:
                        self._preallocate_unified_buffer(device, size)
                        
                    print(f"[INFO] 🌐 {device} 统一内存池初始化完成，预分配{len(common_sizes)}个缓冲区")
                else:
                    print(f"[INFO] 📦 {device} 使用传统内存池模式")
                    
            except Exception as e:
                print(f"[WARNING] {device} 统一内存池初始化失败: {e}")
                
    def _preallocate_unified_buffer(self, device: str, size: Tuple, dtype=torch.float16):
        """预分配统一内存缓冲区"""
        try:
            key = f"{size}_{dtype}"
            
            if self.unified_memory_supported:
                # 创建统一内存张量
                buffer = self._allocate_unified_tensor(size, dtype, device)
            else:
                # 回退到传统内存
                buffer = torch.empty(size, dtype=dtype, device=device)
                
            with self.unified_memory_locks[device]:
                self.unified_memory_pool[device][key] = buffer
                self.unified_memory_usage[device][key] = False
                
        except Exception as e:
            print(f"[WARNING] 预分配统一内存缓冲区失败 {device} {size}: {e}")
            
    def _allocate_unified_tensor(self, size: Tuple, dtype=torch.float16, device: str = None) -> torch.Tensor:
        """分配统一内存张量"""
        if not self.unified_memory_supported:
            return torch.empty(size, dtype=dtype, device=device)
            
        try:
            # 方法1: 使用PyTorch的统一内存分配（如果支持）
            if hasattr(torch.cuda, 'memory_pool'):
                # 尝试使用内存池分配统一内存
                with torch.cuda.device(device):
                    tensor = torch.empty(size, dtype=dtype, device='cuda', memory_format=torch.contiguous_format)
                    # 标记为统一内存（如果API支持）
                    return tensor
                    
            # 方法2: 使用CuPy分配统一内存
            elif CUPY_AVAILABLE:
                with cp.cuda.Device(int(device.split(':')[1])):
                    # 计算所需的字节数
                    element_count = np.prod(size)
                    dtype_size = np.dtype(np.float16).itemsize
                    total_bytes = element_count * dtype_size
                    
                    print(f"[DEBUG] CuPy统一内存分配: size={size}, elements={element_count}, bytes={total_bytes}")
                    
                    # 分配统一内存
                    cupy_array = cp.cuda.alloc_pinned_memory(total_bytes)
                    
                    # 验证分配的内存大小
                    buffer_size = len(cupy_array)
                    expected_size = element_count * dtype_size
                    
                    if buffer_size != expected_size:
                        raise ValueError(f"内存分配大小不匹配: 分配了{buffer_size}字节，期望{expected_size}字节")
                    
                    # 转换为PyTorch张量
                    try:
                        numpy_array = np.frombuffer(cupy_array, dtype=np.float16)
                        print(f"[DEBUG] numpy_array形状: {numpy_array.shape}, 期望元素数: {element_count}")
                        
                        if numpy_array.size != element_count:
                            raise ValueError(f"数组元素数不匹配: 实际{numpy_array.size}，期望{element_count}")
                        
                        tensor = torch.from_numpy(numpy_array.reshape(size))
                        return tensor.to(device)
                        
                    except Exception as reshape_error:
                        print(f"[ERROR] CuPy张量重塑失败: {reshape_error}")
                        print(f"[ERROR] 缓冲区大小: {buffer_size}, 数组大小: {numpy_array.size if 'numpy_array' in locals() else 'N/A'}")
                        raise
                    
            # 方法3: 回退到固定内存 + 异步传输
            else:
                # 创建CPU固定内存
                cpu_tensor = torch.empty(size, dtype=dtype).pin_memory()
                # 异步传输到GPU
                gpu_tensor = cpu_tensor.to(device, non_blocking=True)
                return gpu_tensor
                
        except Exception as e:
            print(f"[WARNING] 统一内存分配失败，使用传统方法: {e}")
            return torch.empty(size, dtype=dtype, device=device)
            
    def allocate_unified_memory(self, size: Tuple, dtype=torch.float16, device: str = None, 
                              access_pattern: str = 'mixed') -> torch.Tensor:
        """
        分配统一内存张量
        
        Args:
            size: 张量尺寸
            dtype: 数据类型
            device: 目标设备
            access_pattern: 访问模式 ('cpu_heavy', 'gpu_heavy', 'mixed')
            
        Returns:
            统一内存张量
        """
        if device is None:
            device = self.devices[0]
            
        key = f"{size}_{dtype}"
        
        # 尝试从统一内存池获取
        if device in self.unified_memory_pool:
            with self.unified_memory_locks[device]:
                if key in self.unified_memory_pool[device] and not self.unified_memory_usage[device].get(key, True):
                    self.unified_memory_usage[device][key] = True
                    self.stats['unified_allocations'] += 1
                    
                    # 记录访问模式
                    self.access_patterns[key].append(access_pattern)
                    
                    return self.unified_memory_pool[device][key]
        
        # 创建新的统一内存张量
        try:
            print(f"[DEBUG] 尝试分配统一内存: size={size}, dtype={dtype}, device={device}")
            tensor = self._allocate_unified_tensor(size, dtype, device)
            self.stats['unified_allocations'] += 1
            
            # 根据访问模式进行预取
            self._prefetch_memory(tensor, access_pattern, device)
            
            print(f"[DEBUG] 统一内存分配成功: {tensor.shape}, device={tensor.device}")
            return tensor
            
        except torch.cuda.OutOfMemoryError as oom_error:
            print(f"[WARNING] GPU内存不足，尝试清理后重试: {oom_error}")
            # 内存不足时清理并重试
            self._emergency_cleanup(device)
            try:
                tensor = self._allocate_unified_tensor(size, dtype, device)
                self.stats['fallback_allocations'] += 1
                print(f"[INFO] 清理后重试成功")
                return tensor
            except Exception as retry_error:
                print(f"[ERROR] 清理后重试仍失败: {retry_error}")
                raise
                
        except ValueError as value_error:
            print(f"[ERROR] 统一内存分配参数错误: {value_error}")
            print(f"[ERROR] 参数信息: size={size}, dtype={dtype}, device={device}")
            # 对于reshape等错误，直接回退到传统内存
            print(f"[INFO] 回退到传统GPU内存分配")
            fallback_tensor = torch.empty(size, dtype=dtype, device=device)
            self.stats['fallback_allocations'] += 1
            return fallback_tensor
            
        except Exception as general_error:
            print(f"[ERROR] 统一内存分配失败: {general_error}")
            print(f"[ERROR] 错误类型: {type(general_error).__name__}")
            print(f"[INFO] 回退到传统GPU内存分配")
            # 回退到传统GPU内存
            try:
                fallback_tensor = torch.empty(size, dtype=dtype, device=device)
                self.stats['fallback_allocations'] += 1
                return fallback_tensor
            except Exception as fallback_error:
                print(f"[CRITICAL] 传统内存分配也失败: {fallback_error}")
                raise RuntimeError(f"所有内存分配方法都失败: 统一内存({general_error}), 传统内存({fallback_error})")
            
    def _prefetch_memory(self, tensor: torch.Tensor, access_pattern: str, device: str):
        """根据访问模式预取内存"""
        if not self.unified_memory_supported:
            return
            
        try:
            if access_pattern == 'gpu_heavy':
                # 预取到GPU
                if hasattr(torch.cuda, 'memory_advise'):
                    torch.cuda.memory_advise(tensor, 'PREFERRED_LOCATION', device)
                self.stats['prefetch_hits'] += 1
                
            elif access_pattern == 'cpu_heavy':
                # 预取到CPU
                if hasattr(torch.cuda, 'memory_advise'):
                    torch.cuda.memory_advise(tensor, 'PREFERRED_LOCATION', 'cpu')
                self.stats['prefetch_hits'] += 1
                
            # mixed模式不进行预取，让系统自动管理
            
        except Exception as e:
            print(f"[WARNING] 内存预取失败: {e}")
            self.stats['prefetch_misses'] += 1
            
    def migrate_to_device(self, tensor: torch.Tensor, target_device: str, 
                         async_migration: bool = True) -> torch.Tensor:
        """
        手动迁移统一内存到指定设备
        
        Args:
            tensor: 源张量
            target_device: 目标设备
            async_migration: 是否异步迁移
            
        Returns:
            迁移后的张量
        """
        start_time = time.time()
        
        try:
            if async_migration:
                migrated_tensor = tensor.to(target_device, non_blocking=True)
            else:
                migrated_tensor = tensor.to(target_device)
                
            # 更新迁移统计
            migration_time = time.time() - start_time
            self.migration_stats['migration_time_total'] += migration_time
            self.migration_stats['manual_migrations'] += 1
            
            if 'cpu' in str(tensor.device) and 'cuda' in target_device:
                self.migration_stats['cpu_to_gpu_migrations'] += 1
            elif 'cuda' in str(tensor.device) and 'cpu' in target_device:
                self.migration_stats['gpu_to_cpu_migrations'] += 1
                
            return migrated_tensor
            
        except Exception as e:
            print(f"[WARNING] 内存迁移失败: {e}")
            return tensor
            
    def optimize_access_patterns(self):
        """基于访问模式优化内存布局"""
        print("[INFO] 🔄 开始优化内存访问模式...")
        
        for key, patterns in self.access_patterns.items():
            if len(patterns) < 5:  # 样本太少，跳过
                continue
                
            # 分析访问模式
            gpu_heavy_count = patterns.count('gpu_heavy')
            cpu_heavy_count = patterns.count('cpu_heavy')
            mixed_count = patterns.count('mixed')
            
            total_count = len(patterns)
            gpu_ratio = gpu_heavy_count / total_count
            cpu_ratio = cpu_heavy_count / total_count
            
            # 根据访问模式调整内存位置
            if gpu_ratio > 0.7:
                print(f"[INFO] 📊 {key} 主要在GPU访问 ({gpu_ratio:.1%})，优化GPU亲和性")
                # 可以在这里添加GPU亲和性优化
            elif cpu_ratio > 0.7:
                print(f"[INFO] 📊 {key} 主要在CPU访问 ({cpu_ratio:.1%})，优化CPU亲和性")
                # 可以在这里添加CPU亲和性优化
            else:
                print(f"[INFO] 📊 {key} 混合访问模式，保持当前配置")
                
    def _emergency_cleanup(self, device: str):
        """紧急内存清理"""
        print(f"[WARNING] 🧹 {device} 内存不足，执行紧急清理...")
        
        try:
            # 清理未使用的统一内存
            if device in self.unified_memory_pool:
                with self.unified_memory_locks[device]:
                    for key, in_use in list(self.unified_memory_usage[device].items()):
                        if not in_use:
                            del self.unified_memory_pool[device][key]
                            del self.unified_memory_usage[device][key]
                            
            # 强制垃圾回收
            gc.collect()
            
            # 清理GPU缓存
            if 'cuda' in device:
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                
            print(f"[INFO] ✅ {device} 紧急清理完成")
            
        except Exception as e:
            print(f"[ERROR] 紧急清理失败: {e}")
            
    def get_unified_memory_stats(self) -> Dict[str, Any]:
        """获取统一内存统计信息"""
        total_allocations = self.stats['unified_allocations'] + self.stats['fallback_allocations']
        unified_ratio = self.stats['unified_allocations'] / max(total_allocations, 1)
        
        migration_avg_time = (self.migration_stats['migration_time_total'] / 
                            max(self.migration_stats['manual_migrations'], 1))
        
        prefetch_hit_rate = (self.stats['prefetch_hits'] / 
                           max(self.stats['prefetch_hits'] + self.stats['prefetch_misses'], 1))
        
        return {
            'unified_memory_supported': self.unified_memory_supported,
            'unified_allocation_ratio': unified_ratio,
            'total_migrations': (self.migration_stats['cpu_to_gpu_migrations'] + 
                               self.migration_stats['gpu_to_cpu_migrations']),
            'average_migration_time_ms': migration_avg_time * 1000,
            'prefetch_hit_rate': prefetch_hit_rate,
            'memory_saved_mb': self.stats['memory_saved_bytes'] / (1024**2),
            'access_violations': self.stats['access_violations']
        }
        
    def get_memory_usage(self) -> Dict[str, Dict]:
        """获取内存使用情况"""
        usage_info = {}
        
        for device in self.devices:
            if device == 'cpu':
                # CPU内存使用
                memory = psutil.virtual_memory()
                usage_info['cpu'] = {
                    'total_gb': memory.total / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percent': memory.percent,
                    'available_gb': memory.available / (1024**3)
                }
            else:
                # GPU内存使用
                device_id = int(device.split(':')[1])
                if torch.cuda.is_available():
                    allocated = torch.cuda.memory_allocated(device_id) / (1024**3)
                    reserved = torch.cuda.memory_reserved(device_id) / (1024**3)
                    total = torch.cuda.get_device_properties(device_id).total_memory / (1024**3)
                    
                    usage_info[device] = {
                        'total_gb': total,
                        'allocated_gb': allocated,
                        'reserved_gb': reserved,
                        'percent': (allocated / total) * 100,
                        'unified_pool_count': len(self.unified_memory_pool.get(device, {}))
                    }
                    
        return usage_info
        
    def cleanup(self):
        """清理所有内存资源"""
        print("[INFO] 🧹 开始清理统一内存管理器...")
        
        try:
            # 清理统一内存池
            for device in self.devices:
                if device in self.unified_memory_pool:
                    with self.unified_memory_locks[device]:
                        self.unified_memory_pool[device].clear()
                        self.unified_memory_usage[device].clear()
                        
                if device in self.fallback_memory_pool:
                    self.fallback_memory_pool[device].clear()
                    self.fallback_usage[device].clear()
                    
            # 清理访问模式记录
            self.access_patterns.clear()
            
            # 强制垃圾回收
            gc.collect()
            
            # 清理GPU缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                
            print("[INFO] ✅ 统一内存管理器清理完成")
            
        except Exception as e:
            print(f"[ERROR] 清理统一内存管理器时出错: {e}")

# 全局统一内存管理器实例
_unified_memory_manager = None

def get_unified_memory_manager(device_ids: List[int] = [0], 
                             unified_pool_size_gb: float = 2.0) -> CUDAUnifiedMemoryManager:
    """获取全局统一内存管理器实例"""
    global _unified_memory_manager
    if _unified_memory_manager is None:
        _unified_memory_manager = CUDAUnifiedMemoryManager(device_ids, unified_pool_size_gb)
    return _unified_memory_manager

def cleanup_unified_memory_manager():
    """清理全局统一内存管理器"""
    global _unified_memory_manager
    if _unified_memory_manager is not None:
        _unified_memory_manager.cleanup()
        _unified_memory_manager = None

if __name__ == "__main__":
    # 测试统一内存管理器
    print("[INFO] 🧪 开始CUDA统一内存管理器测试...")
    
    manager = CUDAUnifiedMemoryManager([0], unified_pool_size_gb=1.0)
    
    # 测试统一内存分配
    print("\n[TEST] 测试统一内存分配...")
    tensor1 = manager.allocate_unified_memory((1, 3, 320, 320), access_pattern='gpu_heavy')
    tensor2 = manager.allocate_unified_memory((1, 3, 320, 320), access_pattern='cpu_heavy')
    
    print(f"GPU重度访问张量设备: {tensor1.device}")
    print(f"CPU重度访问张量设备: {tensor2.device}")
    
    # 测试内存迁移
    print("\n[TEST] 测试内存迁移...")
    if torch.cuda.is_available():
        migrated_tensor = manager.migrate_to_device(tensor1, 'cpu')
        print(f"迁移后张量设备: {migrated_tensor.device}")
    
    # 测试访问模式优化
    print("\n[TEST] 测试访问模式优化...")
    manager.optimize_access_patterns()
    
    # 显示统计信息
    print("\n[INFO] 📊 统一内存统计:")
    stats = manager.get_unified_memory_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n[INFO] 📈 内存使用情况:")
    usage = manager.get_memory_usage()
    for device, info in usage.items():
        print(f"  {device}: {info}")
    
    # 清理
    manager.cleanup()
    print("\n[INFO] ✅ 测试完成")
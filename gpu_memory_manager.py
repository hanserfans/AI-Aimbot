#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU内存管理器
实现共享GPU内存、内存池、零拷贝技术
解决内存不足问题，提高GPU利用率
"""

import torch
import numpy as np
import time
import gc
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import threading
import psutil

class GPUMemoryManager:
    """GPU内存管理器 - 实现共享GPU内存和内存池"""
    
    def __init__(self, device_ids: List[int] = [0], pool_size_gb: float = 4.0):
        """
        初始化GPU内存管理器
        
        Args:
            device_ids: GPU设备ID列表
            pool_size_gb: 内存池大小(GB)
        """
        self.device_ids = device_ids
        self.pool_size_bytes = int(pool_size_gb * 1024**3)
        self.devices = [f'cuda:{i}' for i in device_ids if torch.cuda.is_available()]
        
        if not self.devices:
            self.devices = ['cpu']
            print("[WARNING] 无可用GPU，使用CPU模式")
        
        # 内存池 - 每个设备一个池
        self.memory_pools = {}
        self.pool_usage = {}
        self.pool_locks = {}
        
        # 共享内存区域
        self.shared_memory = {}
        self.shared_locks = {}
        
        # 统计信息
        self.stats = {
            'allocations': 0,
            'deallocations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'memory_saved_bytes': 0,
            'peak_memory_usage': 0
        }
        
        # 初始化内存池
        self._initialize_memory_pools()
        
        print(f"[INFO] 🏊 GPU内存管理器初始化完成")
        print(f"[INFO] 设备: {self.devices}")
        print(f"[INFO] 内存池大小: {pool_size_gb:.1f}GB")
        
    def _initialize_memory_pools(self):
        """初始化内存池"""
        for device in self.devices:
            if device == 'cpu':
                continue
                
            try:
                self.memory_pools[device] = {}
                self.pool_usage[device] = {}
                self.pool_locks[device] = threading.Lock()
                self.shared_memory[device] = {}
                self.shared_locks[device] = threading.Lock()
                
                # 预分配常用尺寸的内存块
                common_sizes = [
                    (1, 3, 320, 320),    # 标准检测图像
                    (1, 3, 640, 640),    # 高分辨率检测
                    (1920, 1080, 3),     # 全屏截图
                    (320, 320, 3),       # 处理后图像
                    (100, 6),            # 检测结果
                ]
                
                for size in common_sizes:
                    self._preallocate_buffer(device, size)
                    
                print(f"[INFO] 📦 {device} 内存池初始化完成，预分配{len(common_sizes)}个缓冲区")
                
            except Exception as e:
                print(f"[WARNING] {device} 内存池初始化失败: {e}")
                
    def _preallocate_buffer(self, device: str, size: Tuple, dtype=torch.float16):
        """预分配内存缓冲区"""
        try:
            key = f"{size}_{dtype}"
            buffer = torch.empty(size, dtype=dtype, device=device)
            
            with self.pool_locks[device]:
                self.memory_pools[device][key] = buffer
                self.pool_usage[device][key] = False
                
        except Exception as e:
            print(f"[WARNING] 预分配缓冲区失败 {device} {size}: {e}")
            
    def allocate_tensor(self, size: Tuple, dtype=torch.float16, device: str = None) -> torch.Tensor:
        """
        分配GPU张量（支持内存池复用）
        
        Args:
            size: 张量尺寸
            dtype: 数据类型
            device: 目标设备
            
        Returns:
            GPU张量
        """
        if device is None:
            device = self.devices[0]
            
        key = f"{size}_{dtype}"
        
        # 尝试从内存池获取
        if device in self.memory_pools:
            with self.pool_locks[device]:
                if key in self.memory_pools[device] and not self.pool_usage[device].get(key, True):
                    self.pool_usage[device][key] = True
                    self.stats['cache_hits'] += 1
                    self.stats['memory_saved_bytes'] += torch.tensor(size).prod().item() * dtype.itemsize if hasattr(dtype, 'itemsize') else 4
                    return self.memory_pools[device][key]
        
        # 创建新张量
        try:
            tensor = torch.empty(size, dtype=dtype, device=device)
            self.stats['allocations'] += 1
            self.stats['cache_misses'] += 1
            return tensor
        except torch.cuda.OutOfMemoryError:
            # 内存不足时清理并重试
            self._emergency_cleanup(device)
            return torch.empty(size, dtype=dtype, device=device)
            
    def deallocate_tensor(self, tensor: torch.Tensor):
        """释放张量（返回内存池）"""
        if not tensor.is_cuda:
            return
            
        device = str(tensor.device)
        size = tuple(tensor.shape)
        dtype = tensor.dtype
        key = f"{size}_{dtype}"
        
        # 返回内存池
        if device in self.pool_usage and key in self.pool_usage[device]:
            with self.pool_locks[device]:
                self.pool_usage[device][key] = False
                self.stats['deallocations'] += 1
                
    def create_shared_memory(self, name: str, size: Tuple, dtype=torch.float16, device: str = None) -> torch.Tensor:
        """
        创建共享GPU内存区域
        
        Args:
            name: 共享内存名称
            size: 内存大小
            dtype: 数据类型
            device: 目标设备
            
        Returns:
            共享内存张量
        """
        if device is None:
            device = self.devices[0]
            
        if device not in self.shared_memory:
            return self.allocate_tensor(size, dtype, device)
            
        with self.shared_locks[device]:
            if name not in self.shared_memory[device]:
                self.shared_memory[device][name] = torch.empty(size, dtype=dtype, device=device)
                print(f"[INFO] 🔗 创建共享内存区域: {name} on {device}")
                
            return self.shared_memory[device][name]
            
    def get_shared_memory(self, name: str, device: str = None) -> Optional[torch.Tensor]:
        """获取共享内存区域"""
        if device is None:
            device = self.devices[0]
            
        if device in self.shared_memory:
            with self.shared_locks[device]:
                return self.shared_memory[device].get(name)
        return None
        
    def zero_copy_transfer(self, data: np.ndarray, target_device: str = None) -> torch.Tensor:
        """
        零拷贝数据传输（尽可能避免内存拷贝）
        
        Args:
            data: 源数据
            target_device: 目标设备
            
        Returns:
            GPU张量
        """
        if target_device is None:
            target_device = self.devices[0]
            
        try:
            # 使用pin_memory加速CPU到GPU传输
            if isinstance(data, np.ndarray):
                # 创建pinned memory
                tensor_cpu = torch.from_numpy(data).pin_memory()
                # 异步传输到GPU
                tensor_gpu = tensor_cpu.to(target_device, non_blocking=True)
                return tensor_gpu
            else:
                return torch.as_tensor(data, device=target_device)
                
        except Exception as e:
            print(f"[WARNING] 零拷贝传输失败: {e}")
            return torch.tensor(data, device=target_device)
            
    def batch_allocate(self, sizes: List[Tuple], dtype=torch.float16, device: str = None) -> List[torch.Tensor]:
        """批量分配张量（提高效率）"""
        if device is None:
            device = self.devices[0]
            
        tensors = []
        for size in sizes:
            tensor = self.allocate_tensor(size, dtype, device)
            tensors.append(tensor)
            
        return tensors
        
    def _emergency_cleanup(self, device: str):
        """紧急内存清理"""
        print(f"[WARNING] {device} 内存不足，执行紧急清理...")
        
        try:
            # 清理未使用的内存池
            if device in self.memory_pools:
                with self.pool_locks[device]:
                    unused_keys = [k for k, used in self.pool_usage[device].items() if not used]
                    for key in unused_keys:
                        if key in self.memory_pools[device]:
                            del self.memory_pools[device][key]
                            del self.pool_usage[device][key]
                            
            # 强制GPU垃圾回收
            if device != 'cpu':
                torch.cuda.empty_cache()
                
            # 系统垃圾回收
            gc.collect()
            
            print(f"[INFO] {device} 紧急清理完成")
            
        except Exception as e:
            print(f"[ERROR] 紧急清理失败: {e}")
            
    def get_memory_usage(self) -> Dict[str, Dict]:
        """获取内存使用情况"""
        usage = {}
        
        for device in self.devices:
            if device == 'cpu':
                # CPU内存使用
                memory = psutil.virtual_memory()
                usage[device] = {
                    'used_gb': (memory.total - memory.available) / 1024**3,
                    'total_gb': memory.total / 1024**3,
                    'percent': memory.percent
                }
            else:
                # GPU内存使用
                try:
                    device_id = int(device.split(':')[1])
                    allocated = torch.cuda.memory_allocated(device_id) / 1024**3
                    reserved = torch.cuda.memory_reserved(device_id) / 1024**3
                    total = torch.cuda.get_device_properties(device_id).total_memory / 1024**3
                    
                    usage[device] = {
                        'allocated_gb': allocated,
                        'reserved_gb': reserved,
                        'total_gb': total,
                        'percent': (allocated / total) * 100
                    }
                except:
                    usage[device] = {'error': 'Unable to get GPU memory info'}
                    
        return usage
        
    def get_pool_statistics(self) -> Dict:
        """获取内存池统计信息"""
        stats = self.stats.copy()
        
        # 计算内存池使用率
        total_buffers = 0
        used_buffers = 0
        
        for device in self.memory_pools:
            device_total = len(self.memory_pools[device])
            device_used = sum(1 for used in self.pool_usage[device].values() if used)
            
            total_buffers += device_total
            used_buffers += device_used
            
        if total_buffers > 0:
            stats['pool_usage_percent'] = (used_buffers / total_buffers) * 100
        else:
            stats['pool_usage_percent'] = 0
            
        # 缓存命中率
        total_requests = stats['cache_hits'] + stats['cache_misses']
        if total_requests > 0:
            stats['cache_hit_rate'] = (stats['cache_hits'] / total_requests) * 100
        else:
            stats['cache_hit_rate'] = 0
            
        # 内存节省
        stats['memory_saved_mb'] = stats['memory_saved_bytes'] / 1024**2
        
        return stats
        
    def optimize_memory_layout(self):
        """优化内存布局"""
        print("[INFO] 🔧 开始内存布局优化...")
        
        for device in self.devices:
            if device == 'cpu':
                continue
                
            try:
                # 清理碎片化内存
                if device.startswith('cuda'):
                    torch.cuda.empty_cache()
                    
                # 重新整理内存池
                self._reorganize_memory_pool(device)
                
            except Exception as e:
                print(f"[WARNING] {device} 内存优化失败: {e}")
                
        print("[INFO] ✅ 内存布局优化完成")
        
    def _reorganize_memory_pool(self, device: str):
        """重新整理内存池"""
        if device not in self.memory_pools:
            return
            
        with self.pool_locks[device]:
            # 释放未使用的缓冲区
            unused_keys = [k for k, used in self.pool_usage[device].items() if not used]
            for key in unused_keys[:len(unused_keys)//2]:  # 只释放一半，保留一些缓存
                if key in self.memory_pools[device]:
                    del self.memory_pools[device][key]
                    del self.pool_usage[device][key]
                    
    def cleanup(self):
        """清理所有GPU资源"""
        print("[INFO] 🧹 开始GPU内存管理器清理...")
        
        try:
            # 清理内存池
            for device in self.memory_pools:
                with self.pool_locks[device]:
                    self.memory_pools[device].clear()
                    self.pool_usage[device].clear()
                    
            # 清理共享内存
            for device in self.shared_memory:
                with self.shared_locks[device]:
                    self.shared_memory[device].clear()
                    
            # 清理GPU缓存
            for device in self.devices:
                if device.startswith('cuda'):
                    torch.cuda.empty_cache()
                    
            # 重置统计
            for key in self.stats:
                self.stats[key] = 0
                
            print("[INFO] ✅ GPU内存管理器清理完成")
            
        except Exception as e:
            print(f"[WARNING] GPU内存管理器清理失败: {e}")

# 全局内存管理器实例
_memory_manager = None

def get_gpu_memory_manager(device_ids: List[int] = [0], pool_size_gb: float = 4.0) -> GPUMemoryManager:
    """获取GPU内存管理器单例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = GPUMemoryManager(device_ids, pool_size_gb)
    return _memory_manager

def cleanup_gpu_memory_manager():
    """清理GPU内存管理器"""
    global _memory_manager
    if _memory_manager is not None:
        _memory_manager.cleanup()
        _memory_manager = None

if __name__ == "__main__":
    # 测试GPU内存管理器
    print("[INFO] 🧪 开始GPU内存管理器测试...")
    
    manager = GPUMemoryManager([0], pool_size_gb=1.0)
    
    # 测试内存分配
    print("\n[TEST] 测试内存分配...")
    tensor1 = manager.allocate_tensor((1, 3, 320, 320))
    tensor2 = manager.allocate_tensor((1, 3, 320, 320))  # 应该复用内存池
    
    print(f"张量1设备: {tensor1.device}")
    print(f"张量2设备: {tensor2.device}")
    
    # 测试共享内存
    print("\n[TEST] 测试共享内存...")
    shared_tensor = manager.create_shared_memory("test_shared", (100, 100))
    retrieved_tensor = manager.get_shared_memory("test_shared")
    print(f"共享内存创建成功: {shared_tensor is not None}")
    print(f"共享内存检索成功: {retrieved_tensor is not None}")
    
    # 测试零拷贝传输
    print("\n[TEST] 测试零拷贝传输...")
    test_data = np.random.rand(320, 320, 3).astype(np.float32)
    gpu_tensor = manager.zero_copy_transfer(test_data)
    print(f"零拷贝传输成功: {gpu_tensor.device}")
    
    # 获取统计信息
    print("\n[INFO] 📊 内存使用统计:")
    usage = manager.get_memory_usage()
    for device, info in usage.items():
        print(f"  {device}: {info}")
        
    stats = manager.get_pool_statistics()
    print(f"\n[INFO] 📈 内存池统计:")
    print(f"  缓存命中率: {stats['cache_hit_rate']:.1f}%")
    print(f"  内存池使用率: {stats['pool_usage_percent']:.1f}%")
    print(f"  节省内存: {stats['memory_saved_mb']:.1f}MB")
    
    # 清理资源
    manager.cleanup()
    print("\n[INFO] ✅ 测试完成")
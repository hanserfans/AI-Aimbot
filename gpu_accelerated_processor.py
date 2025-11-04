#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速图像处理器
将CPU密集型的图像预处理和后处理操作迁移到GPU
解决内存不足问题，充分利用GPU资源
"""

import numpy as np
import cv2
import time
import gc
from typing import Tuple, Optional, Any
import torch
import torch.nn.functional as F

try:
    import cupy as cp
    CUPY_AVAILABLE = True
    print("[INFO] ✅ CuPy可用，启用CUDA加速")
except ImportError:
    CUPY_AVAILABLE = False
    print("[WARNING] CuPy不可用，使用PyTorch CUDA")

class GPUAcceleratedProcessor:
    """GPU加速图像处理器"""
    
    def __init__(self, device_id: int = 0, enable_memory_pool: bool = True):
        """
        初始化GPU加速处理器
        
        Args:
            device_id: GPU设备ID
            enable_memory_pool: 是否启用GPU内存池
        """
        self.device_id = device_id
        self.device = f'cuda:{device_id}' if torch.cuda.is_available() else 'cpu'
        self.enable_memory_pool = enable_memory_pool
        
        # GPU内存池
        self.memory_pool = {}
        self.pool_usage = {}
        
        # 预分配常用尺寸的GPU内存
        self._preallocate_memory()
        
        # 性能统计
        self.stats = {
            'gpu_preprocessing_time': [],
            'gpu_postprocessing_time': [],
            'memory_transfers': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        print(f"[INFO] 🚀 GPU加速处理器初始化完成")
        print(f"[INFO] 设备: {self.device}")
        print(f"[INFO] 内存池: {'启用' if enable_memory_pool else '禁用'}")
        
    def _preallocate_memory(self):
        """预分配GPU内存池"""
        if not torch.cuda.is_available():
            return
            
        try:
            # 预分配常用尺寸的内存
            common_sizes = [
                (320, 320, 3),    # AI检测图像
                (640, 640, 3),    # 高分辨率检测
                (1920, 1080, 3),  # 全屏截图
                (1, 3, 320, 320), # NCHW格式
                (1, 3, 640, 640), # 高分辨率NCHW
            ]
            
            for size in common_sizes:
                key = f"buffer_{size}"
                if self.enable_memory_pool:
                    buffer = torch.empty(size, dtype=torch.float16, device=self.device)
                    self.memory_pool[key] = buffer
                    self.pool_usage[key] = False
                    
            print(f"[INFO] 📦 预分配了{len(common_sizes)}个GPU内存缓冲区")
            
        except Exception as e:
            print(f"[WARNING] GPU内存预分配失败: {e}")
            
    def get_gpu_buffer(self, shape: Tuple, dtype=torch.float16) -> torch.Tensor:
        """
        获取GPU内存缓冲区（支持内存池复用）
        
        Args:
            shape: 张量形状
            dtype: 数据类型
            
        Returns:
            GPU张量缓冲区
        """
        key = f"buffer_{shape}"
        
        # 尝试从内存池获取
        if self.enable_memory_pool and key in self.memory_pool:
            if not self.pool_usage[key]:
                self.pool_usage[key] = True
                self.stats['cache_hits'] += 1
                return self.memory_pool[key]
        
        # 创建新的缓冲区
        self.stats['cache_misses'] += 1
        return torch.empty(shape, dtype=dtype, device=self.device)
        
    def release_gpu_buffer(self, shape: Tuple):
        """释放GPU内存缓冲区"""
        key = f"buffer_{shape}"
        if key in self.pool_usage:
            self.pool_usage[key] = False
            
    def preprocess_image_gpu(self, img: np.ndarray, target_size: Tuple[int, int] = (320, 320)) -> torch.Tensor:
        """
        GPU加速图像预处理
        
        Args:
            img: 输入图像 (numpy数组)
            target_size: 目标尺寸
            
        Returns:
            预处理后的GPU张量 (NCHW格式)
        """
        start_time = time.time()
        
        try:
            if CUPY_AVAILABLE:
                # 使用CuPy进行GPU加速
                return self._preprocess_with_cupy(img, target_size)
            else:
                # 使用PyTorch CUDA进行加速
                return self._preprocess_with_torch(img, target_size)
                
        except Exception as e:
            print(f"[WARNING] GPU预处理失败，回退到CPU: {e}")
            return self._preprocess_cpu_fallback(img, target_size)
        finally:
            processing_time = time.time() - start_time
            self.stats['gpu_preprocessing_time'].append(processing_time)
            
    def _preprocess_with_cupy(self, img: np.ndarray, target_size: Tuple[int, int]) -> torch.Tensor:
        """使用CuPy进行GPU加速预处理"""
        # 将numpy数组转换为CuPy数组（GPU）
        gpu_img = cp.asarray(img)
        
        # 移除alpha通道（如果存在）
        if gpu_img.shape[2] == 4:
            gpu_img = gpu_img[:, :, :3]
        
        # GPU上进行图像缩放
        if gpu_img.shape[:2] != target_size:
            # CuPy没有直接的resize，使用PyTorch
            torch_img = torch.from_numpy(cp.asnumpy(gpu_img)).to(self.device)
            torch_img = torch_img.permute(2, 0, 1).unsqueeze(0).float()  # HWC -> NCHW
            torch_img = F.interpolate(torch_img, size=target_size, mode='bilinear', align_corners=False)
        else:
            torch_img = torch.from_numpy(cp.asnumpy(gpu_img)).to(self.device)
            torch_img = torch_img.permute(2, 0, 1).unsqueeze(0).float()
        
        # 归一化和类型转换
        torch_img = torch_img / 255.0
        torch_img = torch_img.half()  # 转换为float16
        
        self.stats['memory_transfers'] += 1
        return torch_img
        
    def _preprocess_with_torch(self, img: np.ndarray, target_size: Tuple[int, int]) -> torch.Tensor:
        """使用PyTorch CUDA进行加速预处理"""
        # 转换为PyTorch张量并移到GPU
        torch_img = torch.from_numpy(img).to(self.device)
        
        # 移除alpha通道（如果存在）
        if torch_img.shape[2] == 4:
            torch_img = torch_img[:, :, :3]
            
        # 转换为NCHW格式
        torch_img = torch_img.permute(2, 0, 1).unsqueeze(0).float()
        
        # GPU上进行图像缩放
        if torch_img.shape[2:] != target_size:
            torch_img = F.interpolate(torch_img, size=target_size, mode='bilinear', align_corners=False)
        
        # 归一化和类型转换
        torch_img = torch_img / 255.0
        torch_img = torch_img.half()  # 转换为float16节省显存
        
        self.stats['memory_transfers'] += 1
        return torch_img
        
    def _preprocess_cpu_fallback(self, img: np.ndarray, target_size: Tuple[int, int]) -> torch.Tensor:
        """CPU回退预处理"""
        # 传统的CPU预处理
        if img.shape[:2] != target_size:
            img = cv2.resize(img, target_size)
            
        if img.shape[2] == 4:
            img = img[:, :, :3]
            
        img = img.astype(np.float16) / 255.0
        img = np.moveaxis(img, 2, 0)  # HWC -> CHW
        img = np.expand_dims(img, 0)  # CHW -> NCHW
        
        return torch.from_numpy(img).to(self.device)
        
    def postprocess_detections_gpu(self, outputs: torch.Tensor, conf_threshold: float = 0.5) -> torch.Tensor:
        """
        GPU加速后处理
        
        Args:
            outputs: 模型输出张量
            conf_threshold: 置信度阈值
            
        Returns:
            处理后的检测结果
        """
        start_time = time.time()
        
        try:
            # 确保张量在GPU上
            if not outputs.is_cuda:
                outputs = outputs.to(self.device)
            
            # GPU上进行置信度筛选
            conf_mask = outputs[..., 4] > conf_threshold
            filtered_outputs = outputs[conf_mask]
            
            # GPU上进行坐标转换等计算
            # 这里可以添加更多GPU加速的后处理操作
            
            return filtered_outputs
            
        except Exception as e:
            print(f"[WARNING] GPU后处理失败: {e}")
            return outputs
        finally:
            processing_time = time.time() - start_time
            self.stats['gpu_postprocessing_time'].append(processing_time)
            
    def apply_mask_gpu(self, img: torch.Tensor, mask_config: dict) -> torch.Tensor:
        """GPU加速掩码应用"""
        if not mask_config.get('enabled', False):
            return img
            
        try:
            # 在GPU上应用掩码
            mask_side = mask_config.get('side', 'right').lower()
            mask_width = mask_config.get('width', 100)
            mask_height = mask_config.get('height', 100)
            
            if mask_side == 'right':
                img[:, :, -mask_height:, -mask_width:] = 0
            elif mask_side == 'left':
                img[:, :, -mask_height:, :mask_width] = 0
                
            return img
            
        except Exception as e:
            print(f"[WARNING] GPU掩码应用失败: {e}")
            return img
            
    def get_memory_usage(self) -> dict:
        """获取GPU内存使用情况"""
        if not torch.cuda.is_available():
            return {'gpu_memory_used': 0, 'gpu_memory_total': 0}
            
        try:
            memory_used = torch.cuda.memory_allocated(self.device_id) / 1024**3  # GB
            memory_total = torch.cuda.get_device_properties(self.device_id).total_memory / 1024**3  # GB
            
            return {
                'gpu_memory_used': memory_used,
                'gpu_memory_total': memory_total,
                'gpu_memory_percent': (memory_used / memory_total) * 100
            }
        except:
            return {'gpu_memory_used': 0, 'gpu_memory_total': 0}
            
    def get_performance_stats(self) -> dict:
        """获取性能统计"""
        stats = self.stats.copy()
        
        # 计算平均时间
        if stats['gpu_preprocessing_time']:
            stats['avg_preprocessing_time'] = np.mean(stats['gpu_preprocessing_time'])
            stats['max_preprocessing_time'] = np.max(stats['gpu_preprocessing_time'])
            
        if stats['gpu_postprocessing_time']:
            stats['avg_postprocessing_time'] = np.mean(stats['gpu_postprocessing_time'])
            stats['max_postprocessing_time'] = np.max(stats['gpu_postprocessing_time'])
            
        # 缓存命中率
        total_requests = stats['cache_hits'] + stats['cache_misses']
        if total_requests > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / total_requests * 100
        else:
            stats['cache_hit_rate'] = 0
            
        return stats
        
    def cleanup(self):
        """清理GPU资源"""
        try:
            # 清空内存池
            for key in self.memory_pool:
                del self.memory_pool[key]
            self.memory_pool.clear()
            self.pool_usage.clear()
            
            # 强制GPU垃圾回收
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            # 清空统计信息
            for key in self.stats:
                if isinstance(self.stats[key], list):
                    self.stats[key].clear()
                else:
                    self.stats[key] = 0
                    
            print("[INFO] 🧹 GPU资源清理完成")
            
        except Exception as e:
            print(f"[WARNING] GPU资源清理失败: {e}")

# 全局GPU处理器实例
_gpu_processor = None

def get_gpu_processor(device_id: int = 0) -> GPUAcceleratedProcessor:
    """获取GPU处理器单例"""
    global _gpu_processor
    if _gpu_processor is None:
        _gpu_processor = GPUAcceleratedProcessor(device_id)
    return _gpu_processor

def cleanup_gpu_processor():
    """清理GPU处理器"""
    global _gpu_processor
    if _gpu_processor is not None:
        _gpu_processor.cleanup()
        _gpu_processor = None

if __name__ == "__main__":
    # 测试GPU加速处理器
    processor = GPUAcceleratedProcessor()
    
    # 创建测试图像
    test_img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    print("[INFO] 🧪 开始GPU加速测试...")
    
    # 测试预处理
    start_time = time.time()
    processed = processor.preprocess_image_gpu(test_img)
    gpu_time = time.time() - start_time
    
    print(f"[INFO] GPU预处理时间: {gpu_time*1000:.2f}ms")
    print(f"[INFO] 输出形状: {processed.shape}")
    print(f"[INFO] 输出设备: {processed.device}")
    
    # 获取性能统计
    stats = processor.get_performance_stats()
    print(f"[INFO] 缓存命中率: {stats['cache_hit_rate']:.1f}%")
    
    # 获取内存使用
    memory = processor.get_memory_usage()
    print(f"[INFO] GPU内存使用: {memory['gpu_memory_used']:.2f}GB / {memory['gpu_memory_total']:.2f}GB")
    
    # 清理资源
    processor.cleanup()
    print("[INFO] ✅ 测试完成")
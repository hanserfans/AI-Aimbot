#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一内存GPU加速处理器
集成CUDA统一内存管理，实现高效的CPU-GPU协同处理
自动内存迁移，优化图像处理性能
"""

import numpy as np
import cv2
import time
import gc
from typing import Tuple, Optional, Any, Dict
import torch
import torch.nn.functional as F
from cuda_unified_memory_manager import get_unified_memory_manager, CUDAUnifiedMemoryManager

try:
    import cupy as cp
    CUPY_AVAILABLE = True
    print("[INFO] ✅ CuPy可用，启用CUDA加速")
except ImportError:
    CUPY_AVAILABLE = False
    print("[WARNING] CuPy不可用，使用PyTorch CUDA")

class UnifiedMemoryGPUProcessor:
    """统一内存GPU加速处理器 - 集成CUDA统一内存管理"""
    
    def __init__(self, device_id: int = 0, unified_memory_size_gb: float = 2.0, 
                 enable_auto_migration: bool = True):
        """
        初始化统一内存GPU处理器
        
        Args:
            device_id: GPU设备ID
            unified_memory_size_gb: 统一内存池大小(GB)
            enable_auto_migration: 是否启用自动内存迁移
        """
        self.device_id = device_id
        self.device = f'cuda:{device_id}' if torch.cuda.is_available() else 'cpu'
        self.enable_auto_migration = enable_auto_migration
        
        # 初始化统一内存管理器
        self.unified_memory_manager = get_unified_memory_manager([device_id], unified_memory_size_gb)
        
        # 预分配统一内存缓冲区
        self.unified_buffers = {}
        self.buffer_access_patterns = {}
        
        # 性能统计
        self.stats = {
            'gpu_preprocessing_time': [],
            'gpu_postprocessing_time': [],
            'unified_memory_hits': 0,
            'unified_memory_misses': 0,
            'auto_migrations': 0,
            'manual_migrations': 0,
            'total_processing_time': 0.0,
            'memory_efficiency_score': 0.0
        }
        
        # 预分配常用的统一内存缓冲区
        self._preallocate_unified_memory()
        
        print(f"[INFO] 🌐 统一内存GPU处理器初始化完成")
        print(f"[INFO] 设备: {self.device}")
        print(f"[INFO] 统一内存: {unified_memory_size_gb:.1f}GB")
        print(f"[INFO] 自动迁移: {'启用' if enable_auto_migration else '禁用'}")
        
    def _preallocate_unified_memory(self):
        """预分配统一内存缓冲区"""
        try:
            # 预分配常用尺寸的统一内存
            buffer_configs = [
                # (shape, access_pattern, description)
                ((320, 320, 3), 'mixed', 'AI检测图像'),
                ((640, 640, 3), 'gpu_heavy', '高分辨率检测'),
                ((1920, 1080, 3), 'cpu_heavy', '全屏截图'),
                ((1, 3, 320, 320), 'gpu_heavy', 'NCHW格式检测'),
                ((1, 3, 640, 640), 'gpu_heavy', '高分辨率NCHW'),
                ((100, 6), 'mixed', '检测结果'),
                ((1000, 6), 'mixed', '大批量检测结果'),
            ]
            
            for shape, access_pattern, description in buffer_configs:
                key = f"unified_buffer_{shape}"
                buffer = self.unified_memory_manager.allocate_unified_memory(
                    shape, dtype=torch.float16, device=self.device, access_pattern=access_pattern
                )
                self.unified_buffers[key] = buffer
                self.buffer_access_patterns[key] = access_pattern
                
            print(f"[INFO] 🌐 预分配了{len(buffer_configs)}个统一内存缓冲区")
            
        except Exception as e:
            print(f"[WARNING] 统一内存预分配失败: {e}")
            
    def get_unified_buffer(self, shape: Tuple, access_pattern: str = 'mixed', 
                          dtype=torch.float16) -> torch.Tensor:
        """
        获取统一内存缓冲区
        
        Args:
            shape: 张量形状
            access_pattern: 访问模式 ('cpu_heavy', 'gpu_heavy', 'mixed')
            dtype: 数据类型
            
        Returns:
            统一内存张量
        """
        key = f"unified_buffer_{shape}"
        
        # 尝试从预分配的缓冲区获取
        if key in self.unified_buffers:
            self.stats['unified_memory_hits'] += 1
            return self.unified_buffers[key]
        
        # 动态分配新的统一内存
        try:
            buffer = self.unified_memory_manager.allocate_unified_memory(
                shape, dtype=dtype, device=self.device, access_pattern=access_pattern
            )
            self.stats['unified_memory_misses'] += 1
            return buffer
            
        except Exception as e:
            print(f"[WARNING] 统一内存分配失败: {e}")
            # 回退到传统GPU内存
            return torch.empty(shape, dtype=dtype, device=self.device)
            
    def preprocess_image_unified(self, img: np.ndarray, target_size: Tuple[int, int] = (320, 320),
                               access_pattern: str = 'gpu_heavy') -> torch.Tensor:
        """
        使用统一内存进行图像预处理
        
        Args:
            img: 输入图像 (numpy数组)
            target_size: 目标尺寸
            access_pattern: 访问模式
            
        Returns:
            预处理后的GPU张量
        """
        start_time = time.time()
        
        try:
            # 步骤1: 将图像数据加载到统一内存
            if access_pattern == 'cpu_heavy':
                # CPU重度访问，优先在CPU处理
                processed_img = self._preprocess_cpu_optimized(img, target_size)
                # 然后迁移到GPU（如果需要）
                if self.enable_auto_migration:
                    processed_img = self.unified_memory_manager.migrate_to_device(
                        processed_img, self.device, async_migration=True
                    )
                    self.stats['auto_migrations'] += 1
                    
            elif access_pattern == 'gpu_heavy':
                # GPU重度访问，直接在GPU处理
                processed_img = self._preprocess_gpu_optimized(img, target_size)
                
            else:  # mixed
                # 混合访问，使用最优策略
                if img.size > 1920 * 1080 * 3:  # 大图像用CPU预处理
                    processed_img = self._preprocess_cpu_optimized(img, target_size)
                    if self.enable_auto_migration:
                        processed_img = self.unified_memory_manager.migrate_to_device(
                            processed_img, self.device, async_migration=True
                        )
                        self.stats['auto_migrations'] += 1
                else:  # 小图像直接GPU处理
                    processed_img = self._preprocess_gpu_optimized(img, target_size)
                    
            processing_time = time.time() - start_time
            self.stats['gpu_preprocessing_time'].append(processing_time)
            self.stats['total_processing_time'] += processing_time
            
            return processed_img
            
        except Exception as e:
            print(f"[WARNING] 统一内存预处理失败: {e}")
            # 回退到传统方法
            return self._preprocess_fallback(img, target_size)
    
    def preprocess_image_gpu(self, img: np.ndarray, target_size: Tuple[int, int] = (320, 320)) -> torch.Tensor:
        """
        GPU图像预处理接口（兼容性方法）
        
        Args:
            img: 输入图像 (numpy数组)
            target_size: 目标尺寸，默认(320, 320)
            
        Returns:
            预处理后的GPU张量
        """
        try:
            # 验证输入图像
            if img is None:
                raise ValueError("输入图像为None")
            
            if len(img.shape) != 3:
                raise ValueError(f"输入图像维度错误，期望3维，实际{len(img.shape)}维")
            
            if img.shape[2] not in [3, 4]:  # RGB或RGBA
                raise ValueError(f"输入图像通道数错误，期望3或4通道，实际{img.shape[2]}通道")
            
            # 如果是RGBA，转换为RGB
            if img.shape[2] == 4:
                img = img[:, :, :3]
            
            print(f"[DEBUG] 统一内存GPU预处理开始，输入形状: {img.shape}")
            
            # 使用统一内存预处理，默认GPU重度访问模式
            return self.preprocess_image_unified(img, target_size, access_pattern='gpu_heavy')
            
        except Exception as e:
            print(f"[ERROR] 统一内存GPU预处理接口失败: {e}")
            print(f"[ERROR] 输入图像信息: shape={img.shape if img is not None else 'None'}, dtype={img.dtype if img is not None else 'None'}")
            print(f"[ERROR] 目标尺寸: {target_size}")
            raise
            
    def _preprocess_cpu_optimized(self, img: np.ndarray, target_size: Tuple[int, int]) -> torch.Tensor:
        """CPU优化的预处理"""
        try:
            print(f"[DEBUG] CPU优化预处理输入图像形状: {img.shape}")
            
            # 使用OpenCV进行CPU预处理
            resized = cv2.resize(img, target_size, interpolation=cv2.INTER_LINEAR)
            print(f"[DEBUG] CPU缩放后图像形状: {resized.shape}")
            
            # 转换为PyTorch张量并归一化
            tensor = torch.from_numpy(resized).float() / 255.0
            
            # 转换为NCHW格式
            if len(tensor.shape) == 3:  # HWC -> NCHW
                tensor = tensor.permute(2, 0, 1).unsqueeze(0)
            
            print(f"[DEBUG] CPU预处理最终张量形状: {tensor.shape}")
            
            # 尝试分配统一内存
            try:
                # 分配统一内存张量
                unified_tensor = self.unified_memory_manager.allocate_unified_memory(
                    tensor.shape, dtype=torch.float32, access_pattern='cpu_heavy'
                )
                
                # 将数据复制到统一内存
                unified_tensor.copy_(tensor)
                
                return unified_tensor.half()  # 转换为float16节省内存
                
            except Exception as unified_error:
                print(f"[WARNING] 统一内存分配失败，使用普通GPU内存: {unified_error}")
                # 回退到普通GPU内存
                return tensor.half().to(self.device)
            
        except Exception as e:
            print(f"[WARNING] CPU优化预处理失败: {e}")
            print(f"[ERROR] 输入图像形状: {img.shape if img is not None else 'None'}")
            print(f"[ERROR] 目标尺寸: {target_size}")
            raise
            
    def _preprocess_gpu_optimized(self, img: np.ndarray, target_size: Tuple[int, int]) -> torch.Tensor:
        """GPU优化的预处理"""
        try:
            # 方法1: 使用CuPy加速（如果可用）
            if CUPY_AVAILABLE:
                return self._preprocess_with_cupy_unified(img, target_size)
            
            # 方法2: 使用PyTorch GPU加速
            else:
                return self._preprocess_with_torch_unified(img, target_size)
                
        except Exception as e:
            print(f"[WARNING] GPU优化预处理失败: {e}")
            raise
            
    def _preprocess_with_cupy_unified(self, img: np.ndarray, target_size: Tuple[int, int]) -> torch.Tensor:
        """使用CuPy和统一内存的预处理"""
        try:
            # 将图像数据传输到GPU
            gpu_img = cp.asarray(img)
            
            # GPU上进行resize和归一化
            resized = cp.array(cv2.resize(cp.asnumpy(gpu_img), target_size))
            normalized = resized.astype(cp.float32) / 255.0
            
            # 转换为PyTorch统一内存张量
            tensor = torch.as_tensor(normalized, device=self.device)
            
            # 转换为NCHW格式
            if len(tensor.shape) == 3:
                tensor = tensor.permute(2, 0, 1).unsqueeze(0)
                
            return tensor.half()
            
        except Exception as e:
            print(f"[WARNING] CuPy统一内存预处理失败: {e}")
            raise
            
    def _preprocess_with_torch_unified(self, img: np.ndarray, target_size: Tuple[int, int]) -> torch.Tensor:
        """使用PyTorch和统一内存的预处理"""
        try:
            # 获取统一内存缓冲区
            buffer_shape = (target_size[1], target_size[0], 3)  # HWC
            tensor = self.get_unified_buffer(buffer_shape, 'gpu_heavy', torch.float32)
            
            # 将numpy数组转换为tensor并传输到GPU
            img_tensor = torch.from_numpy(img).float()
            img_tensor = self.unified_memory_manager.migrate_to_device(
                img_tensor, self.device, async_migration=True
            )
            
            # 使用PyTorch进行resize和归一化
            img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0)  # HWC -> NCHW
            resized = F.interpolate(img_tensor, size=target_size, mode='bilinear', align_corners=False)
            normalized = resized / 255.0
            
            return normalized.half()
            
        except Exception as e:
            print(f"[WARNING] PyTorch统一内存预处理失败: {e}")
            raise
            
    def _preprocess_fallback(self, img: np.ndarray, target_size: Tuple[int, int]) -> torch.Tensor:
        """回退预处理方法"""
        try:
            # 确保输入图像尺寸正确
            print(f"[DEBUG] 回退预处理输入图像形状: {img.shape}")
            
            # 使用OpenCV进行图像缩放
            resized = cv2.resize(img, target_size, interpolation=cv2.INTER_LINEAR)
            print(f"[DEBUG] 缩放后图像形状: {resized.shape}")
            
            # 转换为PyTorch张量并归一化
            tensor = torch.from_numpy(resized).float()
            tensor = tensor / 255.0
            
            # 转换为NCHW格式 (HWC -> NCHW)
            if len(tensor.shape) == 3:  # HWC格式
                tensor = tensor.permute(2, 0, 1).unsqueeze(0)  # HWC -> NCHW
            elif len(tensor.shape) == 4:  # 已经是NCHW格式
                pass
            else:
                raise ValueError(f"不支持的图像维度: {tensor.shape}")
            
            print(f"[DEBUG] 最终张量形状: {tensor.shape}")
            
            # 转换为half精度并移动到GPU
            return tensor.half().to(self.device)
            
        except Exception as e:
            print(f"[ERROR] 回退预处理失败: {e}")
            print(f"[ERROR] 输入图像形状: {img.shape if img is not None else 'None'}")
            print(f"[ERROR] 目标尺寸: {target_size}")
            raise
            
    def postprocess_detections_unified(self, outputs: torch.Tensor, 
                                     conf_threshold: float = 0.5,
                                     access_pattern: str = 'mixed') -> torch.Tensor:
        """
        使用统一内存进行检测后处理
        
        Args:
            outputs: 模型输出张量
            conf_threshold: 置信度阈值
            access_pattern: 访问模式
            
        Returns:
            后处理结果
        """
        start_time = time.time()
        
        try:
            # 确保输出在正确的设备上
            if access_pattern == 'cpu_heavy':
                # CPU重度访问，迁移到CPU处理
                if outputs.is_cuda:
                    outputs = self.unified_memory_manager.migrate_to_device(
                        outputs, 'cpu', async_migration=False
                    )
                    self.stats['manual_migrations'] += 1
                    
            # 应用置信度阈值
            mask = outputs[..., 4] > conf_threshold
            filtered_outputs = outputs[mask]
            
            # 如果需要，迁移回GPU
            if access_pattern == 'gpu_heavy' and not filtered_outputs.is_cuda:
                filtered_outputs = self.unified_memory_manager.migrate_to_device(
                    filtered_outputs, self.device, async_migration=True
                )
                self.stats['auto_migrations'] += 1
                
            processing_time = time.time() - start_time
            self.stats['gpu_postprocessing_time'].append(processing_time)
            self.stats['total_processing_time'] += processing_time
            
            return filtered_outputs
            
        except Exception as e:
            print(f"[WARNING] 统一内存后处理失败: {e}")
            # 回退到传统方法
            mask = outputs[..., 4] > conf_threshold
            return outputs[mask]
            
    def optimize_memory_access_patterns(self):
        """优化内存访问模式"""
        print("[INFO] 🔄 开始优化统一内存访问模式...")
        
        # 让统一内存管理器分析访问模式
        self.unified_memory_manager.optimize_access_patterns()
        
        # 计算内存效率分数
        total_hits = self.stats['unified_memory_hits']
        total_accesses = total_hits + self.stats['unified_memory_misses']
        
        if total_accesses > 0:
            hit_rate = total_hits / total_accesses
            migration_efficiency = 1.0 - (self.stats['auto_migrations'] / max(total_accesses, 1))
            self.stats['memory_efficiency_score'] = (hit_rate + migration_efficiency) / 2
            
        print(f"[INFO] 📊 内存效率分数: {self.stats['memory_efficiency_score']:.3f}")
        
    def get_unified_memory_stats(self) -> Dict[str, Any]:
        """获取统一内存统计信息"""
        base_stats = self.unified_memory_manager.get_unified_memory_stats()
        
        # 添加处理器特定的统计
        processor_stats = {
            'preprocessing_avg_time_ms': np.mean(self.stats['gpu_preprocessing_time']) * 1000 if self.stats['gpu_preprocessing_time'] else 0,
            'postprocessing_avg_time_ms': np.mean(self.stats['gpu_postprocessing_time']) * 1000 if self.stats['gpu_postprocessing_time'] else 0,
            'unified_memory_hit_rate': self.stats['unified_memory_hits'] / max(self.stats['unified_memory_hits'] + self.stats['unified_memory_misses'], 1),
            'auto_migration_count': self.stats['auto_migrations'],
            'manual_migration_count': self.stats['manual_migrations'],
            'memory_efficiency_score': self.stats['memory_efficiency_score'],
            'total_processing_time_s': self.stats['total_processing_time']
        }
        
        return {**base_stats, **processor_stats}
        
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        base_usage = self.unified_memory_manager.get_memory_usage()
        
        # 添加处理器特定的内存信息
        processor_usage = {
            'unified_buffers_count': len(self.unified_buffers),
            'buffer_access_patterns': self.buffer_access_patterns,
        }
        
        return {**base_usage, **processor_usage}
        
    def cleanup(self):
        """清理所有资源"""
        print("[INFO] 🧹 开始清理统一内存GPU处理器...")
        
        try:
            # 清理预分配的缓冲区
            self.unified_buffers.clear()
            self.buffer_access_patterns.clear()
            
            # 清理统一内存管理器
            self.unified_memory_manager.cleanup()
            
            # 强制垃圾回收
            gc.collect()
            
            # 清理GPU缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                
            print("[INFO] ✅ 统一内存GPU处理器清理完成")
            
        except Exception as e:
            print(f"[ERROR] 清理统一内存GPU处理器时出错: {e}")

# 全局统一内存GPU处理器实例
_unified_gpu_processor = None

def get_unified_gpu_processor(device_id: int = 0, unified_memory_size_gb: float = 2.0) -> UnifiedMemoryGPUProcessor:
    """获取全局统一内存GPU处理器实例"""
    global _unified_gpu_processor
    if _unified_gpu_processor is None:
        _unified_gpu_processor = UnifiedMemoryGPUProcessor(device_id, unified_memory_size_gb)
    return _unified_gpu_processor

def cleanup_unified_gpu_processor():
    """清理全局统一内存GPU处理器"""
    global _unified_gpu_processor
    if _unified_gpu_processor is not None:
        _unified_gpu_processor.cleanup()
        _unified_gpu_processor = None

if __name__ == "__main__":
    # 测试统一内存GPU处理器
    print("[INFO] 🧪 开始统一内存GPU处理器测试...")
    
    processor = UnifiedMemoryGPUProcessor(device_id=0, unified_memory_size_gb=1.0)
    
    # 测试图像预处理
    print("\n[TEST] 测试统一内存图像预处理...")
    test_img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    # 测试不同访问模式
    access_patterns = ['cpu_heavy', 'gpu_heavy', 'mixed']
    
    for pattern in access_patterns:
        print(f"\n[TEST] 测试访问模式: {pattern}")
        start_time = time.time()
        processed = processor.preprocess_image_unified(test_img, access_pattern=pattern)
        processing_time = time.time() - start_time
        
        print(f"  处理时间: {processing_time*1000:.2f}ms")
        print(f"  输出形状: {processed.shape}")
        print(f"  输出设备: {processed.device}")
        
    # 测试后处理
    print("\n[TEST] 测试统一内存后处理...")
    dummy_outputs = torch.rand(100, 6, device=processor.device)
    dummy_outputs[:, 4] = torch.rand(100) * 0.8 + 0.2  # 置信度
    
    filtered = processor.postprocess_detections_unified(dummy_outputs, conf_threshold=0.5)
    print(f"  过滤前: {dummy_outputs.shape[0]} 个检测")
    print(f"  过滤后: {filtered.shape[0]} 个检测")
    
    # 优化访问模式
    print("\n[TEST] 测试访问模式优化...")
    processor.optimize_memory_access_patterns()
    
    # 显示统计信息
    print("\n[INFO] 📊 统一内存统计:")
    stats = processor.get_unified_memory_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n[INFO] 📈 内存使用情况:")
    usage = processor.get_memory_usage()
    for device, info in usage.items():
        if isinstance(info, dict):
            print(f"  {device}:")
            for k, v in info.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {device}: {info}")
    
    # 清理
    processor.cleanup()
    print("\n[INFO] ✅ 测试完成")
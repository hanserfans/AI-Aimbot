#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU利用率优化器
解决GPU使用率低（21%）和内存使用率高（87.7%）的问题
"""

import torch
import numpy as np
import cv2
import time
import json
import os
import gc
from typing import Tuple, Optional
import mss

class GPUUtilizationOptimizer:
    """GPU利用率优化器"""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.stream = torch.cuda.Stream() if torch.cuda.is_available() else None
        
        # GPU内存池
        self.gpu_memory_pool = {}
        self.prealloc_tensors = {}
        
        # 性能统计
        self.stats = {
            'gpu_preprocess_time': [],
            'gpu_inference_time': [],
            'gpu_postprocess_time': [],
            'total_gpu_time': [],
            'memory_usage': []
        }
        
        print(f"[INFO] 🚀 GPU利用率优化器初始化完成")
        print(f"[INFO] 📱 使用设备: {self.device}")
        
        if torch.cuda.is_available():
            print(f"[INFO] 💾 GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
            self.setup_gpu_memory_pool()
    
    def setup_gpu_memory_pool(self):
        """设置GPU内存池，预分配常用尺寸的张量"""
        try:
            # 预分配常用尺寸的张量
            common_sizes = [
                (320, 320, 3),    # 检测图像
                (640, 640, 3),    # 高分辨率图像
                (1920, 1080, 3),  # 全屏截图
                (1, 3, 320, 320), # 模型输入
                (1, 3, 640, 640)  # 高分辨率模型输入
            ]
            
            for size in common_sizes:
                key = f"tensor_{size}"
                if len(size) == 3:  # HWC格式
                    self.prealloc_tensors[key] = torch.zeros(size, dtype=torch.uint8, device=self.device)
                else:  # NCHW格式
                    self.prealloc_tensors[key] = torch.zeros(size, dtype=torch.float32, device=self.device)
            
            print(f"[INFO] 🏊 GPU内存池设置完成，预分配 {len(common_sizes)} 个张量")
            
        except Exception as e:
            print(f"[WARNING] GPU内存池设置失败: {e}")
    
    def get_gpu_tensor(self, shape: Tuple, dtype=torch.uint8) -> torch.Tensor:
        """从内存池获取GPU张量"""
        key = f"tensor_{shape}"
        
        if key in self.prealloc_tensors:
            return self.prealloc_tensors[key]
        else:
            # 动态分配
            return torch.zeros(shape, dtype=dtype, device=self.device)
    
    def gpu_screen_capture_optimized(self, region: Tuple[int, int, int, int]) -> Optional[torch.Tensor]:
        """GPU优化的屏幕截图"""
        try:
            start_time = time.time()
            
            # 使用mss进行快速截图
            with mss.mss() as sct:
                monitor = {
                    "top": region[1],
                    "left": region[0], 
                    "width": region[2],
                    "height": region[3]
                }
                screenshot = sct.grab(monitor)
                
                # 转换为numpy数组
                img_np = torch.tensor(screenshot, device='cuda').cpu().numpy()[:, :, :3]  # 移除alpha通道
                
                # 直接在GPU上创建张量
                img_tensor = torch.from_numpy(img_np).to(self.device, non_blocking=True)
                
                capture_time = time.time() - start_time
                print(f"[DEBUG] 📸 GPU屏幕截图: {capture_time*1000:.2f}ms")
                
                return img_tensor
                
        except Exception as e:
            print(f"[ERROR] GPU屏幕截图失败: {e}")
            return None
    
    def gpu_image_preprocessing(self, img_tensor: torch.Tensor, target_size: Tuple[int, int] = (320, 320)) -> torch.Tensor:
        """GPU图像预处理"""
        try:
            start_time = time.time()
            
            with torch.cuda.stream(self.stream) if self.stream else torch.no_grad():
                # 确保张量在GPU上
                if img_tensor.device != self.device:
                    img_tensor = img_tensor.to(self.device, non_blocking=True)
                
                # 转换数据类型
                img_float = img_tensor.float() / 255.0
                
                # 调整尺寸 (使用双线性插值)
                img_resized = torch.nn.functional.interpolate(
                    img_float.permute(2, 0, 1).unsqueeze(0),  # HWC -> NCHW
                    size=target_size,
                    mode='bilinear',
                    align_corners=False
                )
                
                # 归一化 (ImageNet标准)
                mean = torch.tensor([0.485, 0.456, 0.406], device=self.device).view(1, 3, 1, 1)
                std = torch.tensor([0.229, 0.224, 0.225], device=self.device).view(1, 3, 1, 1)
                img_normalized = (img_resized - mean) / std
                
                preprocess_time = time.time() - start_time
                self.stats['gpu_preprocess_time'].append(preprocess_time * 1000)
                
                print(f"[DEBUG] 🔄 GPU图像预处理: {preprocess_time*1000:.2f}ms")
                
                return img_normalized
                
        except Exception as e:
            print(f"[ERROR] GPU图像预处理失败: {e}")
            return None
    
    def gpu_postprocessing(self, model_output: torch.Tensor, conf_threshold: float = 0.4) -> torch.Tensor:
        """GPU后处理"""
        try:
            start_time = time.time()
            
            with torch.cuda.stream(self.stream) if self.stream else torch.no_grad():
                # 确保输出在GPU上
                if model_output.device != self.device:
                    model_output = model_output.to(self.device, non_blocking=True)
                
                # 置信度过滤
                conf_mask = model_output[..., 4] > conf_threshold
                filtered_detections = model_output[conf_mask]
                
                if filtered_detections.numel() == 0:
                    return torch.empty((0, 6), device=self.device)
                
                # NMS (非极大值抑制)
                boxes = filtered_detections[:, :4]
                scores = filtered_detections[:, 4]
                
                # 简化的NMS实现
                keep_indices = torch.ops.torchvision.nms(boxes, scores, 0.45)
                final_detections = filtered_detections[keep_indices]
                
                postprocess_time = time.time() - start_time
                self.stats['gpu_postprocess_time'].append(postprocess_time * 1000)
                
                print(f"[DEBUG] 🎯 GPU后处理: {postprocess_time*1000:.2f}ms, 检测到 {len(final_detections)} 个目标")
                
                return final_detections
                
        except Exception as e:
            print(f"[ERROR] GPU后处理失败: {e}")
            return torch.empty((0, 6), device=self.device)
    
    def optimize_gpu_pipeline(self, region: Tuple[int, int, int, int], model_session) -> Optional[torch.Tensor]:
        """完整的GPU优化管道"""
        try:
            pipeline_start = time.time()
            
            # 1. GPU屏幕截图
            img_tensor = self.gpu_screen_capture_optimized(region)
            if img_tensor is None:
                return None
            
            # 2. GPU图像预处理
            preprocessed = self.gpu_image_preprocessing(img_tensor)
            if preprocessed is None:
                return None
            
            # 3. 模型推理 (在GPU上)
            inference_start = time.time()
            
            # 转换为numpy进行ONNX推理
            input_np = preprocessed.cpu().numpy()
            outputs = model_session.run(None, {"images": input_np})
            
            # 转换回GPU张量
            output_tensor = torch.from_numpy(outputs[0]).to(self.device)
            
            inference_time = time.time() - inference_start
            self.stats['gpu_inference_time'].append(inference_time * 1000)
            
            # 4. GPU后处理
            detections = self.gpu_postprocessing(output_tensor)
            
            total_time = time.time() - pipeline_start
            self.stats['total_gpu_time'].append(total_time * 1000)
            
            # 记录GPU内存使用
            if torch.cuda.is_available():
                memory_used = torch.cuda.memory_allocated() / 1024**2  # MB
                self.stats['memory_usage'].append(memory_used)
            
            print(f"[INFO] ⚡ GPU管道总时间: {total_time*1000:.2f}ms")
            
            return detections
            
        except Exception as e:
            print(f"[ERROR] GPU优化管道失败: {e}")
            return None
    
    def get_performance_stats(self) -> dict:
        """获取性能统计"""
        if not self.stats['total_gpu_time']:
            return {}
        
        def avg(lst):
            return sum(lst) / len(lst) if lst else 0
        
        return {
            'avg_preprocess_time_ms': avg(self.stats['gpu_preprocess_time']),
            'avg_inference_time_ms': avg(self.stats['gpu_inference_time']),
            'avg_postprocess_time_ms': avg(self.stats['gpu_postprocess_time']),
            'avg_total_time_ms': avg(self.stats['total_gpu_time']),
            'avg_memory_usage_mb': avg(self.stats['memory_usage']),
            'total_frames_processed': len(self.stats['total_gpu_time'])
        }
    
    def print_optimization_report(self):
        """打印优化报告"""
        stats = self.get_performance_stats()
        
        if not stats:
            print("[INFO] 📊 暂无性能数据")
            return
        
        print("\n" + "="*50)
        print("🚀 GPU利用率优化报告")
        print("="*50)
        
        print(f"📊 性能统计 (处理了 {stats['total_frames_processed']} 帧):")
        print(f"  • 平均预处理时间: {stats['avg_preprocess_time_ms']:.2f}ms")
        print(f"  • 平均推理时间: {stats['avg_inference_time_ms']:.2f}ms") 
        print(f"  • 平均后处理时间: {stats['avg_postprocess_time_ms']:.2f}ms")
        print(f"  • 平均总处理时间: {stats['avg_total_time_ms']:.2f}ms")
        print(f"  • 平均GPU内存使用: {stats['avg_memory_usage_mb']:.1f}MB")
        
        # 计算理论FPS
        if stats['avg_total_time_ms'] > 0:
            theoretical_fps = 1000 / stats['avg_total_time_ms']
            print(f"  • 理论最大FPS: {theoretical_fps:.1f}")
        
        # GPU利用率估算
        total_compute_time = (stats['avg_preprocess_time_ms'] + 
                            stats['avg_inference_time_ms'] + 
                            stats['avg_postprocess_time_ms'])
        
        if total_compute_time > 0:
            gpu_utilization = (total_compute_time / stats['avg_total_time_ms']) * 100
            print(f"  • 估算GPU利用率: {gpu_utilization:.1f}%")
        
        print("\n💡 优化建议:")
        if stats['avg_total_time_ms'] > 50:
            print("  • 考虑降低图像分辨率以提高处理速度")
        if stats['avg_memory_usage_mb'] < 1000:
            print("  • GPU内存使用较低，可以增加批处理大小")
        if stats['avg_preprocess_time_ms'] > stats['avg_inference_time_ms']:
            print("  • 预处理时间较长，考虑进一步优化图像处理")
        
        print("="*50)
    
    def cleanup(self):
        """清理GPU资源"""
        try:
            # 清理预分配的张量
            for tensor in self.prealloc_tensors.values():
                del tensor
            self.prealloc_tensors.clear()
            
            # 清理GPU缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            gc.collect()
            print("[INFO] 🧹 GPU资源清理完成")
            
        except Exception as e:
            print(f"[WARNING] GPU资源清理失败: {e}")

def test_gpu_optimization():
    """测试GPU优化效果"""
    print("🧪 GPU利用率优化测试")
    print("="*40)
    
    optimizer = GPUUtilizationOptimizer()
    
    if not torch.cuda.is_available():
        print("❌ CUDA不可用，无法进行GPU优化测试")
        return
    
    try:
        # 模拟检测区域 (屏幕中心320x320)
        screen_width = 1920
        screen_height = 1080
        region_size = 320
        
        region = (
            (screen_width - region_size) // 2,
            (screen_height - region_size) // 2,
            region_size,
            region_size
        )
        
        print(f"📍 测试区域: {region}")
        
        # 运行测试
        test_frames = 10
        print(f"🔄 处理 {test_frames} 帧进行测试...")
        
        for i in range(test_frames):
            print(f"处理第 {i+1}/{test_frames} 帧...")
            
            # 模拟GPU优化管道 (不包含实际模型推理)
            img_tensor = optimizer.gpu_screen_capture_optimized(region)
            if img_tensor is not None:
                preprocessed = optimizer.gpu_image_preprocessing(img_tensor)
                if preprocessed is not None:
                    # 模拟后处理
                    fake_output = torch.randn(1, 25200, 85, device=optimizer.device)
                    detections = optimizer.gpu_postprocessing(fake_output)
            
            time.sleep(0.1)  # 模拟实际使用间隔
        
        # 打印优化报告
        optimizer.print_optimization_report()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        optimizer.cleanup()

def main():
    """主函数"""
    print("🎯 GPU利用率优化器")
    print("="*50)
    
    print("当前问题:")
    print("  • GPU使用率: 21% (严重不足)")
    print("  • 系统内存: 87.7% (接近瓶颈)")
    print("  • GPU显存: 39.2% (充足空间)")
    
    print("\n优化策略:")
    print("  1. 将屏幕截图迁移到GPU")
    print("  2. 在GPU上进行图像预处理")
    print("  3. GPU上进行后处理")
    print("  4. 使用GPU内存池减少分配开销")
    print("  5. 异步GPU流水线处理")
    
    print(f"\n是否运行GPU优化测试？(y/n): ", end="")
    choice = input().lower().strip()
    
    if choice == 'y':
        test_gpu_optimization()
    else:
        print("💡 提示: 在main_onnx.py中集成GPUUtilizationOptimizer类以获得最佳效果")

if __name__ == "__main__":
    main()
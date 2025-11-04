#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU优化指南 - 将内存计算迁移到GPU
适用于AI-Aimbot项目的GPU加速优化
"""

import torch
import numpy as np
import cv2
import time
from ultralytics import YOLO
import psutil
import GPUtil

def check_gpu_status():
    """检查GPU状态和可用性"""
    print("=== GPU状态检查 ===")
    
    # 检查CUDA可用性
    print(f"CUDA可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA版本: {torch.version.cuda}")
        print(f"GPU数量: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
            print(f"GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)")
    
    # 检查GPU使用情况
    try:
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            print(f"GPU {gpu.id}: {gpu.name}")
            print(f"  内存使用: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB ({gpu.memoryUtil*100:.1f}%)")
            print(f"  GPU使用率: {gpu.load*100:.1f}%")
    except:
        print("无法获取详细GPU信息")

def optimize_yolov8_gpu():
    """YOLOv8 GPU优化示例"""
    print("\n=== YOLOv8 GPU优化 ===")
    
    # 1. 模型加载优化
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    
    # 加载模型到GPU
    model = YOLO('models/valorant/best.pt')
    model.to(device)
    
    # 2. 预热GPU（重要！）
    print("GPU预热中...")
    dummy_input = torch.randn(1, 3, 416, 416).to(device)
    with torch.no_grad():
        for _ in range(5):
            _ = model.predict(dummy_input.cpu().numpy(), device=device, verbose=False)
    
    print("GPU预热完成")
    return model, device

def gpu_image_processing():
    """图像处理GPU加速示例"""
    print("\n=== 图像处理GPU加速 ===")
    
    # 创建测试图像
    cpu_image = np.random.randint(0, 255, (416, 416, 3), dtype=np.uint8)
    
    # CPU处理时间测试
    start_time = time.time()
    for _ in range(100):
        # CPU图像处理
        resized = torch.nn.functional.interpolate(
    torch.from_numpy(cpu_image).permute(2, 0, 1).float().unsqueeze(0).to('cuda'),
    size=(320, 320), mode='bilinear', align_corners=False
).squeeze(0).permute(1, 2, 0).cpu().numpy().astype(np.uint8)
        normalized = (torch.from_numpy(resized).float().to('cuda') / 255.0).cpu().numpy()
    cpu_time = time.time() - start_time
    
    # GPU处理时间测试
    if torch.cuda.is_available():
        device = torch.device('cuda')
        
        # 将图像转换为GPU张量
        gpu_image = torch.from_numpy(cpu_image).permute(2, 0, 1).float().to(device) / 255.0
        
        start_time = time.time()
        for _ in range(100):
            # GPU图像处理
            resized_gpu = torch.nn.functional.interpolate(
                gpu_image.unsqueeze(0), 
                size=(320, 320), 
                mode='bilinear', 
                align_corners=False
            )
        torch.cuda.synchronize()  # 等待GPU完成
        gpu_time = time.time() - start_time
        
        print(f"CPU处理时间: {cpu_time:.4f}s")
        print(f"GPU处理时间: {gpu_time:.4f}s")
        print(f"GPU加速比: {cpu_time/gpu_time:.2f}x")
    else:
        print("GPU不可用，无法进行GPU加速测试")

def memory_optimization_tips():
    """内存优化建议"""
    print("\n=== 内存优化建议 ===")
    
    # 检查系统内存
    memory = psutil.virtual_memory()
    print(f"系统内存: {memory.total/1024**3:.1f}GB")
    print(f"可用内存: {memory.available/1024**3:.1f}GB")
    print(f"内存使用率: {memory.percent:.1f}%")
    
    print("\n优化建议:")
    print("1. 使用GPU进行模型推理")
    print("2. 将图像预处理移到GPU")
    print("3. 使用torch.no_grad()减少内存占用")
    print("4. 及时清理GPU缓存: torch.cuda.empty_cache()")
    print("5. 使用混合精度训练/推理")
    print("6. 批处理多个图像以提高GPU利用率")

def gpu_memory_management():
    """GPU内存管理示例"""
    print("\n=== GPU内存管理 ===")
    
    if not torch.cuda.is_available():
        print("GPU不可用")
        return
    
    # 显示初始GPU内存
    print(f"初始GPU内存: {torch.cuda.memory_allocated()/1024**2:.1f}MB")
    
    # 创建大张量
    large_tensor = torch.randn(1000, 1000, 1000).cuda()
    print(f"创建大张量后: {torch.cuda.memory_allocated()/1024**2:.1f}MB")
    
    # 删除张量
    del large_tensor
    print(f"删除张量后: {torch.cuda.memory_allocated()/1024**2:.1f}MB")
    
    # 清理GPU缓存
    torch.cuda.empty_cache()
    print(f"清理缓存后: {torch.cuda.memory_allocated()/1024**2:.1f}MB")

def practical_gpu_migration():
    """实际GPU迁移示例"""
    print("\n=== 实际GPU迁移示例 ===")
    
    # 原始CPU代码
    def cpu_processing(image_array):
        # CPU图像处理
        processed = torch.nn.functional.interpolate(
    torch.from_numpy(image_array).permute(2, 0, 1).float().unsqueeze(0).to('cuda'),
    size=(416, 416), mode='bilinear', align_corners=False
).squeeze(0).permute(1, 2, 0).cpu().numpy().astype(np.uint8)
        normalized = (torch.from_numpy(processed).float().to('cuda') / 255.0).cpu().numpy()
        return normalized
    
    # GPU优化版本
    def gpu_processing(image_array, device):
        # 转换为GPU张量
        tensor = torch.from_numpy(image_array).permute(2, 0, 1).float().to(device)
        
        # GPU处理
        with torch.no_grad():
            # 调整大小
            resized = torch.nn.functional.interpolate(
                tensor.unsqueeze(0), 
                size=(416, 416), 
                mode='bilinear'
            )
            # 归一化
            normalized = resized / 255.0
        
        return normalized.squeeze(0).permute(1, 2, 0).cpu().numpy()
    
    # 性能对比
    test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    
    # CPU测试
    start = time.time()
    for _ in range(50):
        cpu_result = cpu_processing(test_image)
    cpu_time = time.time() - start
    
    # GPU测试
    if torch.cuda.is_available():
        device = torch.device('cuda')
        start = time.time()
        for _ in range(50):
            gpu_result = gpu_processing(test_image, device)
        gpu_time = time.time() - start
        
        print(f"CPU处理50次: {cpu_time:.4f}s")
        print(f"GPU处理50次: {gpu_time:.4f}s")
        print(f"性能提升: {cpu_time/gpu_time:.2f}x")
    
def main():
    """主函数"""
    print("AI-Aimbot GPU优化指南")
    print("=" * 50)
    
    # 1. 检查GPU状态
    check_gpu_status()
    
    # 2. YOLOv8优化
    try:
        model, device = optimize_yolov8_gpu()
        print("✅ YOLOv8 GPU优化成功")
    except Exception as e:
        print(f"❌ YOLOv8 GPU优化失败: {e}")
    
    # 3. 图像处理加速
    gpu_image_processing()
    
    # 4. 内存优化建议
    memory_optimization_tips()
    
    # 5. GPU内存管理
    gpu_memory_management()
    
    # 6. 实际迁移示例
    practical_gpu_migration()
    
    print("\n" + "=" * 50)
    print("优化完成！建议根据以上结果调整你的代码。")

if __name__ == "__main__":
    main()
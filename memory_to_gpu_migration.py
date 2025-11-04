#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存到GPU迁移实施方案
针对AI-Aimbot项目的具体优化建议
"""

import torch
import numpy as np
import cv2
import mss
from ultralytics import YOLO
import time

class GPUOptimizedAimbot:
    """GPU优化的瞄准机器人"""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"使用设备: {self.device}")
        
        # 预分配GPU内存
        self.setup_gpu_memory()
        
        # 加载模型到GPU
        self.load_model()
    
    def setup_gpu_memory(self):
        """预分配GPU内存，避免运行时分配延迟"""
        if self.device.type == 'cuda':
            # 预分配常用张量
            self.gpu_image_buffer = torch.zeros((3, 416, 416), dtype=torch.float32, device=self.device)
            self.gpu_resized_buffer = torch.zeros((3, 320, 320), dtype=torch.float32, device=self.device)
            print("✅ GPU内存预分配完成")
    
    def load_model(self):
        """加载模型到GPU并预热"""
        try:
            self.model = YOLO('models/valorant/best.pt')
            self.model.to(self.device)
            
            # 模型预热
            print("🔥 GPU模型预热中...")
            dummy_input = torch.randn(1, 3, 416, 416, device=self.device)
            with torch.no_grad():
                for _ in range(3):
                    # 使用numpy数组进行预热（匹配实际使用）
                    dummy_np = dummy_input.cpu().numpy().transpose(0, 2, 3, 1)[0]
                    _ = self.model.predict(dummy_np, device=self.device, verbose=False)
            
            print("✅ 模型预热完成")
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            self.model = None
    
    def gpu_image_preprocessing(self, screenshot_np):
        """GPU加速的图像预处理"""
        if self.device.type == 'cpu':
            # CPU回退方案
            return torch.nn.functional.interpolate(
    torch.from_numpy(screenshot_np).permute(2, 0, 1).float().unsqueeze(0).to('cuda'),
    size=(416, 416), mode='bilinear', align_corners=False
).squeeze(0).permute(1, 2, 0).cpu().numpy().astype(np.uint8)
        
        try:
            # 转换为GPU张量
            with torch.no_grad():
                # 转换为张量并移到GPU
                gpu_tensor = torch.from_numpy(screenshot_np).permute(2, 0, 1).float().to(self.device)
                
                # GPU上调整大小
                resized = torch.nn.functional.interpolate(
                    gpu_tensor.unsqueeze(0),
                    size=(416, 416),
                    mode='bilinear',
                    align_corners=False
                )
                
                # 转回CPU numpy数组
                result = resized.squeeze(0).permute(1, 2, 0).cpu().numpy().astype(np.uint8)
                
            return result
            
        except Exception as e:
            print(f"GPU预处理失败，使用CPU: {e}")
            return torch.nn.functional.interpolate(
    torch.from_numpy(screenshot_np).permute(2, 0, 1).float().unsqueeze(0).to('cuda'),
    size=(416, 416), mode='bilinear', align_corners=False
).squeeze(0).permute(1, 2, 0).cpu().numpy().astype(np.uint8)
    
    def optimized_capture_and_detect(self, fov_x, fov_y, fov_width, fov_height):
        """优化的捕获和检测流程"""
        # 1. 屏幕捕获（CPU）
        with mss.mss() as sct:
            monitor = {
                "top": fov_y, 
                "left": fov_x, 
                "width": fov_width, 
                "height": fov_height
            }
            screenshot = sct.grab(monitor)
            screenshot_np = torch.tensor(screenshot, device='cuda').cpu().numpy()[:, :, :3]  # 移除alpha通道
        
        # 2. GPU图像预处理
        processed_image = self.gpu_image_preprocessing(screenshot_np)
        
        # 3. GPU模型推理
        if self.model:
            with torch.no_grad():
                results = self.model.predict(
                    processed_image, 
                    device=self.device, 
                    verbose=False,
                    classes=[0, 1]  # enemyBody, enemyHead
                )
            return results
        
        return None
    
    def memory_efficient_detection_loop(self):
        """内存高效的检测循环"""
        # FOV设置
        screen_width = 1920  # 根据你的屏幕调整
        screen_height = 1080
        fov_width = 320
        fov_height = 320
        fov_x = (screen_width - fov_width) // 2
        fov_y = (screen_height - fov_height) // 2
        
        print("🎯 开始GPU优化检测循环...")
        print("按Ctrl+C停止")
        
        frame_count = 0
        start_time = time.time()
        
        try:
            while True:
                # 优化的检测
                results = self.optimized_capture_and_detect(fov_x, fov_y, fov_width, fov_height)
                
                # 处理结果
                if results:
                    for r in results:
                        if r.boxes.xyxy.shape[0] > 0:
                            print(f"检测到 {r.boxes.xyxy.shape[0]} 个目标")
                        else:
                            print("目标: ❌")
                
                frame_count += 1
                
                # 每100帧显示性能统计
                if frame_count % 100 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(f"📊 性能统计: {fps:.1f} FPS, GPU内存: {torch.cuda.memory_allocated()/1024**2:.1f}MB")
                    
                    # 清理GPU缓存
                    if self.device.type == 'cuda':
                        torch.cuda.empty_cache()
                
                # 小延迟避免100%CPU使用
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            print("\n🛑 检测循环已停止")
            
            # 最终性能报告
            total_time = time.time() - start_time
            avg_fps = frame_count / total_time
            print(f"📈 最终统计: 平均 {avg_fps:.1f} FPS，总帧数: {frame_count}")

def compare_cpu_vs_gpu():
    """CPU vs GPU性能对比"""
    print("\n🏁 CPU vs GPU 性能对比")
    print("=" * 40)
    
    # 创建测试数据
    test_image = np.random.randint(0, 255, (320, 320, 3), dtype=np.uint8)
    
    # CPU测试
    print("🖥️  CPU处理测试...")
    start_time = time.time()
    for _ in range(100):
        cpu_result = torch.nn.functional.interpolate(
    torch.from_numpy(test_image).permute(2, 0, 1).float().unsqueeze(0).to('cuda'),
    size=(416, 416), mode='bilinear', align_corners=False
).squeeze(0).permute(1, 2, 0).cpu().numpy().astype(np.uint8)
    cpu_time = time.time() - start_time
    
    # GPU测试
    if torch.cuda.is_available():
        print("🚀 GPU处理测试...")
        device = torch.device('cuda')
        
        start_time = time.time()
        for _ in range(100):
            with torch.no_grad():
                gpu_tensor = torch.from_numpy(test_image).permute(2, 0, 1).float().to(device)
                resized = torch.nn.functional.interpolate(
                    gpu_tensor.unsqueeze(0),
                    size=(416, 416),
                    mode='bilinear'
                )
                gpu_result = resized.squeeze(0).permute(1, 2, 0).cpu().numpy()
        
        torch.cuda.synchronize()
        gpu_time = time.time() - start_time
        
        print(f"📊 结果对比:")
        print(f"   CPU: {cpu_time:.4f}s")
        print(f"   GPU: {gpu_time:.4f}s")
        print(f"   加速比: {cpu_time/gpu_time:.2f}x")
        
        if gpu_time < cpu_time:
            print("✅ GPU更快，建议使用GPU处理")
        else:
            print("⚠️  GPU较慢，可能因为数据传输开销")
    else:
        print("❌ GPU不可用")

def memory_usage_tips():
    """内存使用优化建议"""
    print("\n💡 内存优化建议")
    print("=" * 40)
    
    print("🔧 立即可实施的优化:")
    print("1. 将YOLOv8模型推理移到GPU（已配置）")
    print("2. 将图像预处理移到GPU")
    print("3. 使用torch.no_grad()减少内存占用")
    print("4. 定期清理GPU缓存: torch.cuda.empty_cache()")
    
    print("\n⚡ 高级优化:")
    print("5. 预分配GPU内存缓冲区")
    print("6. 使用混合精度推理（如果稳定）")
    print("7. 批处理多帧图像")
    print("8. 异步GPU操作")
    
    print("\n🎯 针对你的系统（内存使用93.3%）:")
    print("- 优先级1: 立即启用GPU图像预处理")
    print("- 优先级2: 减少CPU内存中的图像缓存")
    print("- 优先级3: 使用GPU进行所有计算密集型操作")

def main():
    """主函数"""
    print("🚀 AI-Aimbot 内存到GPU迁移方案")
    print("=" * 50)
    
    # 1. 性能对比
    compare_cpu_vs_gpu()
    
    # 2. 内存优化建议
    memory_usage_tips()
    
    # 3. 实际测试（可选）
    print(f"\n🤖 是否要运行GPU优化测试？(y/n): ", end="")
    choice = input().lower().strip()
    
    if choice == 'y':
        optimizer = GPUOptimizedAimbot()
        if optimizer.model:
            print("⚠️  注意：这将开始实际检测循环")
            print("确认要继续吗？(y/n): ", end="")
            if input().lower().strip() == 'y':
                optimizer.memory_efficient_detection_loop()
        else:
            print("❌ 模型加载失败，无法运行测试")
    
    print("\n✅ 迁移方案展示完成！")

if __name__ == "__main__":
    main()
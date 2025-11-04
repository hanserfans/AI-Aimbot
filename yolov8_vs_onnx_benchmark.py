#!/usr/bin/env python3
"""
YOLOv8 vs ONNX 模型性能对比测试
对比YOLOv8 PT模型与当前ONNX模型的性能差异
"""

import time
import numpy as np
import cv2
import torch
import onnxruntime as ort
import psutil
import gc
import os
from pathlib import Path
import json
from datetime import datetime

# 尝试导入YOLOv8
try:
    from ultralytics import YOLO
    YOLOV8_AVAILABLE = True
except ImportError:
    YOLOV8_AVAILABLE = False
    print("⚠️ YOLOv8 (ultralytics) 未安装，请运行: pip install ultralytics")

class ModelBenchmark:
    """模型性能基准测试类"""
    
    def __init__(self):
        self.results = {
            'onnx': {},
            'yolov8': {},
            'comparison': {}
        }
        
        # 测试配置
        self.test_config = {
            'num_warmup': 10,      # 预热次数
            'num_iterations': 100,  # 测试迭代次数
            'input_size': (320, 320),  # 输入尺寸
            'batch_size': 1,
            'confidence': 0.3,
            'device': 'cuda' if torch.cuda.is_available() else 'cpu'
        }
        
        print(f"🔧 测试配置: {self.test_config}")
    
    def create_test_input(self, size=(320, 320), use_fp16=False):
        """创建测试输入数据"""
        # 创建随机图像数据
        img = np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)
        
        # 转换为模型输入格式
        img_tensor = (torch.from_numpy(img).float().to('cuda') / 255.0).cpu().numpy()
        img_tensor = np.transpose(img_tensor, (2, 0, 1))  # HWC -> CHW
        img_tensor = np.expand_dims(img_tensor, axis=0)   # 添加batch维度
        
        if use_fp16:
            img_tensor = img_tensor.astype(np.float16)
        
        return img, img_tensor
    
    def get_system_info(self):
        """获取系统信息"""
        info = {
            'cpu': psutil.cpu_count(),
            'memory_gb': psutil.virtual_memory().total / (1024**3),
            'gpu_available': torch.cuda.is_available(),
        }
        
        if torch.cuda.is_available():
            info['gpu_name'] = torch.cuda.get_device_name(0)
            info['gpu_memory_gb'] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        
        return info
    
    def benchmark_onnx_model(self, model_path):
        """测试ONNX模型性能"""
        print(f"\n🔄 测试ONNX模型: {model_path}")
        
        if not os.path.exists(model_path):
            print(f"❌ ONNX模型文件不存在: {model_path}")
            return None
        
        try:
            # 创建ONNX会话
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if torch.cuda.is_available() else ['CPUExecutionProvider']
            session = ort.InferenceSession(model_path, providers=providers)
            
            # 获取输入输出信息
            input_name = session.get_inputs()[0].name
            output_names = [output.name for output in session.get_outputs()]
            
            print(f"✅ ONNX会话创建成功")
            print(f"📊 输入: {input_name}, 输出: {output_names}")
            
            # 创建测试数据
            test_img, test_input = self.create_test_input(
                self.test_config['input_size'], 
                use_fp16=True  # ONNX模型使用半精度
            )
            
            # 预热
            print("🔥 预热ONNX模型...")
            for _ in range(self.test_config['num_warmup']):
                _ = session.run(output_names, {input_name: test_input})
            
            # 性能测试
            print("📊 开始ONNX性能测试...")
            start_memory = psutil.virtual_memory().used / (1024**2)
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
                start_gpu_memory = torch.cuda.memory_allocated() / (1024**2)
            
            inference_times = []
            start_time = time.time()
            
            for i in range(self.test_config['num_iterations']):
                iter_start = time.time()
                outputs = session.run(output_names, {input_name: test_input})
                iter_end = time.time()
                inference_times.append((iter_end - iter_start) * 1000)  # 转换为毫秒
                
                if (i + 1) % 20 == 0:
                    print(f"  进度: {i+1}/{self.test_config['num_iterations']}")
            
            total_time = time.time() - start_time
            
            # 计算内存使用
            end_memory = psutil.virtual_memory().used / (1024**2)
            memory_increase = end_memory - start_memory
            
            gpu_memory_increase = 0
            if torch.cuda.is_available():
                end_gpu_memory = torch.cuda.memory_allocated() / (1024**2)
                gpu_memory_increase = end_gpu_memory - start_gpu_memory
            
            # 统计结果
            results = {
                'model_path': model_path,
                'avg_inference_time_ms': np.mean(inference_times),
                'min_inference_time_ms': np.min(inference_times),
                'max_inference_time_ms': np.max(inference_times),
                'std_inference_time_ms': np.std(inference_times),
                'fps': 1000 / np.mean(inference_times),
                'total_time_s': total_time,
                'memory_increase_mb': memory_increase,
                'gpu_memory_increase_mb': gpu_memory_increase,
                'iterations': self.test_config['num_iterations']
            }
            
            print(f"✅ ONNX测试完成")
            print(f"📊 平均推理时间: {results['avg_inference_time_ms']:.2f}ms")
            print(f"📊 FPS: {results['fps']:.1f}")
            
            return results
            
        except Exception as e:
            print(f"❌ ONNX测试失败: {e}")
            return None
    
    def benchmark_yolov8_model(self, model_path):
        """测试YOLOv8模型性能"""
        print(f"\n🔄 测试YOLOv8模型: {model_path}")
        
        if not YOLOV8_AVAILABLE:
            print("❌ YOLOv8不可用")
            return None
        
        if not os.path.exists(model_path):
            print(f"❌ YOLOv8模型文件不存在: {model_path}")
            return None
        
        try:
            # 加载YOLOv8模型
            model = YOLO(model_path)
            
            # 移动到GPU
            if self.test_config['device'] == 'cuda' and torch.cuda.is_available():
                model = model.cuda()
                if hasattr(model.model, 'half'):
                    model = model.half()
            
            print(f"✅ YOLOv8模型加载成功")
            
            # 创建测试数据
            test_img, _ = self.create_test_input(self.test_config['input_size'])
            
            # 预热
            print("🔥 预热YOLOv8模型...")
            for _ in range(self.test_config['num_warmup']):
                _ = model.predict(
                    test_img,
                    device=self.test_config['device'],
                    verbose=False,
                    conf=self.test_config['confidence']
                )
            
            # 性能测试
            print("📊 开始YOLOv8性能测试...")
            start_memory = psutil.virtual_memory().used / (1024**2)
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
                start_gpu_memory = torch.cuda.memory_allocated() / (1024**2)
            
            inference_times = []
            start_time = time.time()
            
            for i in range(self.test_config['num_iterations']):
                iter_start = time.time()
                results = model.predict(
                    test_img,
                    device=self.test_config['device'],
                    verbose=False,
                    conf=self.test_config['confidence'],
                    classes=[0]  # 只检测人物
                )
                iter_end = time.time()
                inference_times.append((iter_end - iter_start) * 1000)  # 转换为毫秒
                
                if (i + 1) % 20 == 0:
                    print(f"  进度: {i+1}/{self.test_config['num_iterations']}")
            
            total_time = time.time() - start_time
            
            # 计算内存使用
            end_memory = psutil.virtual_memory().used / (1024**2)
            memory_increase = end_memory - start_memory
            
            gpu_memory_increase = 0
            if torch.cuda.is_available():
                end_gpu_memory = torch.cuda.memory_allocated() / (1024**2)
                gpu_memory_increase = end_gpu_memory - start_gpu_memory
            
            # 统计结果
            results = {
                'model_path': model_path,
                'avg_inference_time_ms': np.mean(inference_times),
                'min_inference_time_ms': np.min(inference_times),
                'max_inference_time_ms': np.max(inference_times),
                'std_inference_time_ms': np.std(inference_times),
                'fps': 1000 / np.mean(inference_times),
                'total_time_s': total_time,
                'memory_increase_mb': memory_increase,
                'gpu_memory_increase_mb': gpu_memory_increase,
                'iterations': self.test_config['num_iterations']
            }
            
            print(f"✅ YOLOv8测试完成")
            print(f"📊 平均推理时间: {results['avg_inference_time_ms']:.2f}ms")
            print(f"📊 FPS: {results['fps']:.1f}")
            
            return results
            
        except Exception as e:
            print(f"❌ YOLOv8测试失败: {e}")
            return None
    
    def compare_results(self, onnx_results, yolov8_results):
        """对比测试结果"""
        if not onnx_results or not yolov8_results:
            print("❌ 无法进行对比，缺少测试结果")
            return None
        
        print("\n" + "="*60)
        print("📊 YOLOv8 vs ONNX 性能对比报告")
        print("="*60)
        
        # 速度对比
        onnx_fps = onnx_results['fps']
        yolov8_fps = yolov8_results['fps']
        speed_diff = ((yolov8_fps - onnx_fps) / onnx_fps) * 100
        
        print(f"\n🚀 推理速度对比:")
        print(f"  ONNX模型:    {onnx_fps:.1f} FPS ({onnx_results['avg_inference_time_ms']:.2f}ms)")
        print(f"  YOLOv8模型:  {yolov8_fps:.1f} FPS ({yolov8_results['avg_inference_time_ms']:.2f}ms)")
        print(f"  速度差异:    {speed_diff:+.1f}% ({'YOLOv8更快' if speed_diff > 0 else 'ONNX更快'})")
        
        # 内存对比
        onnx_mem = onnx_results['memory_increase_mb']
        yolov8_mem = yolov8_results['memory_increase_mb']
        mem_diff = yolov8_mem - onnx_mem
        
        print(f"\n💾 内存使用对比:")
        print(f"  ONNX模型:    {onnx_mem:+.1f} MB")
        print(f"  YOLOv8模型:  {yolov8_mem:+.1f} MB")
        print(f"  内存差异:    {mem_diff:+.1f} MB")
        
        # GPU内存对比
        if torch.cuda.is_available():
            onnx_gpu_mem = onnx_results['gpu_memory_increase_mb']
            yolov8_gpu_mem = yolov8_results['gpu_memory_increase_mb']
            gpu_mem_diff = yolov8_gpu_mem - onnx_gpu_mem
            
            print(f"\n🎮 GPU内存使用对比:")
            print(f"  ONNX模型:    {onnx_gpu_mem:+.1f} MB")
            print(f"  YOLOv8模型:  {yolov8_gpu_mem:+.1f} MB")
            print(f"  GPU内存差异: {gpu_mem_diff:+.1f} MB")
        
        # 稳定性对比
        onnx_std = onnx_results['std_inference_time_ms']
        yolov8_std = yolov8_results['std_inference_time_ms']
        
        print(f"\n📈 推理稳定性对比:")
        print(f"  ONNX模型:    标准差 {onnx_std:.2f}ms")
        print(f"  YOLOv8模型:  标准差 {yolov8_std:.2f}ms")
        print(f"  稳定性:      {'YOLOv8更稳定' if yolov8_std < onnx_std else 'ONNX更稳定'}")
        
        # 建议
        print(f"\n💡 使用建议:")
        if speed_diff > 10:
            print("  ✅ 推荐使用YOLOv8模型 - 速度优势明显")
        elif speed_diff < -10:
            print("  ✅ 推荐使用ONNX模型 - 速度优势明显")
        else:
            print("  ⚖️ 两个模型性能相近，可根据其他因素选择")
        
        if abs(mem_diff) > 100:
            print(f"  ⚠️ 注意内存差异较大: {abs(mem_diff):.1f}MB")
        
        # 保存对比结果
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'onnx_results': onnx_results,
            'yolov8_results': yolov8_results,
            'speed_difference_percent': speed_diff,
            'memory_difference_mb': mem_diff,
            'recommendation': 'yolov8' if speed_diff > 5 else 'onnx' if speed_diff < -5 else 'similar'
        }
        
        return comparison
    
    def save_results(self, results, filename='benchmark_results.json'):
        """保存测试结果"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 测试结果已保存到: {filename}")
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")
    
    def run_full_benchmark(self):
        """运行完整的基准测试"""
        print("🎯 YOLOv8 vs ONNX 模型性能基准测试")
        print("="*50)
        
        # 系统信息
        system_info = self.get_system_info()
        print(f"\n💻 系统信息:")
        for key, value in system_info.items():
            print(f"  {key}: {value}")
        
        # 清理GPU内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        
        # 测试ONNX模型
        onnx_models = ['yolov5s320Half.onnx', 'yolov5m320Half.onnx']
        onnx_results = None
        
        for model_path in onnx_models:
            if os.path.exists(model_path):
                onnx_results = self.benchmark_onnx_model(model_path)
                break
        
        # 清理内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        
        # 测试YOLOv8模型
        yolov8_models = ['best.pt', 'models/valorant/best.pt', 'yolov8s.pt']
        yolov8_results = None
        
        for model_path in yolov8_models:
            if os.path.exists(model_path):
                yolov8_results = self.benchmark_yolov8_model(model_path)
                break
        
        # 对比结果
        comparison = self.compare_results(onnx_results, yolov8_results)
        
        # 保存结果
        all_results = {
            'system_info': system_info,
            'test_config': self.test_config,
            'onnx_results': onnx_results,
            'yolov8_results': yolov8_results,
            'comparison': comparison
        }
        
        self.save_results(all_results)
        
        print("\n" + "="*60)
        print("✅ 基准测试完成！")
        print("="*60)

def main():
    """主函数"""
    benchmark = ModelBenchmark()
    benchmark.run_full_benchmark()

if __name__ == "__main__":
    main()
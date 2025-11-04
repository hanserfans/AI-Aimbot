#!/usr/bin/env python3
"""
模型性能对比测试脚本
比较 yolov5s320Half.onnx 和 yolov5m320Half.onnx 的性能差异
"""

import time
import numpy as np
import torch
import torch.nn.functional as F
import onnxruntime as ort
import psutil
import GPUtil
from typing import Dict, List, Tuple

class ModelPerformanceComparator:
    def __init__(self):
        self.models = {
            'yolov5s': 'yolov5s320Half.onnx',
            'yolov5m': 'yolov5m320Half.onnx'
        }
        self.test_results = {}
        
    def create_test_input(self, use_fp16: bool = True) -> np.ndarray:
        """创建测试输入数据 (320x320x3)"""
        data = np.random.rand(1, 3, 320, 320)
        if use_fp16:
            return data.astype(np.float16)
        else:
            return data.astype(np.float32)
    
    def create_onnx_session(self, model_path: str) -> ort.InferenceSession:
        """创建优化的ONNX推理会话"""
        try:
            # 会话选项
            so = ort.SessionOptions()
            so.log_severity_level = 3  # 减少日志输出
            
            # 提供者配置
            providers = [
                ('CUDAExecutionProvider', {
                    'device_id': 0,
                    'arena_extend_strategy': 'kNextPowerOfTwo',
                    'gpu_mem_limit': 4 * 1024 * 1024 * 1024,  # 4GB
                    'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    'do_copy_in_default_stream': True,
                }),
                'CPUExecutionProvider'
            ]
            
            session = ort.InferenceSession(model_path, sess_options=so, providers=providers)
            print(f"✅ {model_path} 加载成功")
            return session
            
        except Exception as e:
            print(f"❌ {model_path} 加载失败: {e}")
            return None
    
    def get_system_info(self) -> Dict:
        """获取系统资源使用情况"""
        # CPU和内存信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # GPU信息
        gpu_info = {}
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_info = {
                    'name': gpu.name,
                    'memory_total': gpu.memoryTotal,
                    'memory_used': gpu.memoryUsed,
                    'memory_free': gpu.memoryFree,
                    'load': gpu.load * 100,
                    'temperature': gpu.temperature
                }
        except:
            gpu_info = {'error': 'GPU信息获取失败'}
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_mb': memory.used / 1024 / 1024,
            'gpu': gpu_info
        }
    
    def benchmark_model(self, model_name: str, model_path: str, num_runs: int = 100) -> Dict:
        """对单个模型进行性能测试"""
        print(f"\n🔄 开始测试 {model_name} ({model_path})")
        
        # 检查文件是否存在
        import os
        if not os.path.exists(model_path):
            return {'error': f'模型文件不存在: {model_path}'}
        
        # 创建会话
        session = self.create_onnx_session(model_path)
        if session is None:
            return {'error': f'无法创建推理会话: {model_path}'}
        
        # 获取输入输出信息
        input_name = session.get_inputs()[0].name
        output_names = [output.name for output in session.get_outputs()]
        
        # 创建测试数据 (半精度模型需要FP16输入)
        test_input = self.create_test_input(use_fp16=True)
        
        # 预热
        print("🔥 预热模型...")
        for _ in range(10):
            _ = session.run(output_names, {input_name: test_input})
        
        # 获取测试前的系统状态
        before_info = self.get_system_info()
        
        # 性能测试
        print(f"⏱️ 开始 {num_runs} 次推理测试...")
        inference_times = []
        
        start_time = time.time()
        for i in range(num_runs):
            inference_start = time.perf_counter()
            outputs = session.run(output_names, {input_name: test_input})
            inference_end = time.perf_counter()
            
            inference_times.append((inference_end - inference_start) * 1000)  # 转换为毫秒
            
            if (i + 1) % 20 == 0:
                print(f"  完成 {i + 1}/{num_runs} 次推理")
        
        total_time = time.time() - start_time
        
        # 获取测试后的系统状态
        after_info = self.get_system_info()
        
        # 计算统计信息
        inference_times = torch.tensor(inference_times, device='cuda').cpu().numpy()
        
        results = {
            'model_name': model_name,
            'model_path': model_path,
            'num_runs': num_runs,
            'total_time_sec': total_time,
            'avg_inference_ms': np.mean(inference_times),
            'min_inference_ms': np.min(inference_times),
            'max_inference_ms': np.max(inference_times),
            'std_inference_ms': np.std(inference_times),
            'fps': 1000 / np.mean(inference_times),
            'system_before': before_info,
            'system_after': after_info,
            'memory_increase_mb': after_info['memory_used_mb'] - before_info['memory_used_mb']
        }
        
        if 'gpu' in after_info and 'gpu' in before_info:
            if 'memory_used' in after_info['gpu'] and 'memory_used' in before_info['gpu']:
                results['gpu_memory_increase_mb'] = after_info['gpu']['memory_used'] - before_info['gpu']['memory_used']
        
        return results
    
    def run_comparison(self) -> Dict:
        """运行完整的模型对比测试"""
        print("🚀 开始模型性能对比测试")
        print("=" * 60)
        
        results = {}
        
        for model_name, model_path in self.models.items():
            try:
                results[model_name] = self.benchmark_model(model_name, model_path)
            except Exception as e:
                results[model_name] = {'error': str(e)}
        
        return results
    
    def print_comparison_report(self, results: Dict):
        """打印对比报告"""
        print("\n" + "=" * 80)
        print("📊 模型性能对比报告")
        print("=" * 80)
        
        # 检查是否有有效结果
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        
        if len(valid_results) < 2:
            print("❌ 无法进行对比，缺少有效的测试结果")
            for model_name, result in results.items():
                if 'error' in result:
                    print(f"  {model_name}: {result['error']}")
            return
        
        # 基本性能对比
        print("\n🎯 推理性能对比:")
        print(f"{'模型':<15} {'平均延迟(ms)':<15} {'FPS':<10} {'最小延迟(ms)':<15} {'最大延迟(ms)':<15}")
        print("-" * 80)
        
        for model_name, result in valid_results.items():
            print(f"{model_name:<15} {result['avg_inference_ms']:<15.2f} {result['fps']:<10.1f} "
                  f"{result['min_inference_ms']:<15.2f} {result['max_inference_ms']:<15.2f}")
        
        # 内存使用对比
        print("\n💾 内存使用对比:")
        print(f"{'模型':<15} {'系统内存增加(MB)':<20} {'GPU内存增加(MB)':<20}")
        print("-" * 60)
        
        for model_name, result in valid_results.items():
            gpu_mem = result.get('gpu_memory_increase_mb', 'N/A')
            print(f"{model_name:<15} {result['memory_increase_mb']:<20.1f} {gpu_mem}")
        
        # 性能差异分析
        if 'yolov5s' in valid_results and 'yolov5m' in valid_results:
            s_result = valid_results['yolov5s']
            m_result = valid_results['yolov5m']
            
            print("\n📈 性能差异分析:")
            
            # 速度差异
            speed_diff = ((m_result['avg_inference_ms'] - s_result['avg_inference_ms']) / s_result['avg_inference_ms']) * 100
            fps_diff = ((s_result['fps'] - m_result['fps']) / m_result['fps']) * 100
            
            print(f"  推理延迟差异: yolov5m 比 yolov5s 慢 {speed_diff:.1f}%")
            print(f"  FPS差异: yolov5s 比 yolov5m 快 {fps_diff:.1f}%")
            
            # 内存差异
            mem_diff = m_result['memory_increase_mb'] - s_result['memory_increase_mb']
            print(f"  系统内存差异: yolov5m 多使用 {mem_diff:.1f} MB")
            
            if 'gpu_memory_increase_mb' in m_result and 'gpu_memory_increase_mb' in s_result:
                gpu_mem_diff = m_result['gpu_memory_increase_mb'] - s_result['gpu_memory_increase_mb']
                print(f"  GPU内存差异: yolov5m 多使用 {gpu_mem_diff:.1f} MB")
        
        # 建议
        print("\n💡 使用建议:")
        if 'yolov5s' in valid_results and 'yolov5m' in valid_results:
            s_fps = valid_results['yolov5s']['fps']
            m_fps = valid_results['yolov5m']['fps']
            
            if s_fps > 60 and m_fps > 30:
                print("  ✅ 两个模型的FPS都足够高，可以考虑使用yolov5m获得更好的精度")
            elif s_fps > 60 and m_fps < 30:
                print("  ⚠️ yolov5m的FPS较低，建议继续使用yolov5s保证实时性")
            else:
                print("  ❌ 两个模型的FPS都不够理想，建议检查系统配置")
        
        print("\n" + "=" * 80)

def main():
    """主函数"""
    comparator = ModelPerformanceComparator()
    
    # 运行对比测试
    results = comparator.run_comparison()
    
    # 打印报告
    comparator.print_comparison_report(results)
    
    # 保存结果到文件
    import json
    with open('model_performance_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 详细结果已保存到: model_performance_comparison.json")

if __name__ == "__main__":
    main()
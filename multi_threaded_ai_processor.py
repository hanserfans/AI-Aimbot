"""
多线程AI处理系统
充分利用多核CPU和GPU，实现并行AI推理和后处理
"""

import numpy as np
import torch
import onnxruntime as ort
import time
import threading
import queue
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Optional, Dict, List, Tuple, Any
import psutil
import pandas as pd
from utils.general import non_max_suppression, xyxy2xywh
import cv2

class MultiThreadedAIProcessor:
    """多线程AI处理系统"""
    
    def __init__(self,
                 model_path: str,
                 num_inference_threads: int = None,
                 num_postprocess_threads: int = None,
                 batch_size: int = 4,
                 enable_gpu_inference: bool = True,
                 enable_parallel_postprocess: bool = True):
        """
        初始化多线程AI处理系统
        
        Args:
            model_path: 模型路径
            num_inference_threads: 推理线程数
            num_postprocess_threads: 后处理线程数
            batch_size: 批处理大小
            enable_gpu_inference: 启用GPU推理
            enable_parallel_postprocess: 启用并行后处理
        """
        self.model_path = model_path
        self.batch_size = batch_size
        self.enable_gpu_inference = enable_gpu_inference
        self.enable_parallel_postprocess = enable_parallel_postprocess
        
        # 自动检测最优线程数
        cpu_count = psutil.cpu_count(logical=True)
        self.num_inference_threads = num_inference_threads or min(4, max(2, cpu_count // 4))
        self.num_postprocess_threads = num_postprocess_threads or min(8, max(4, cpu_count // 2))
        
        print(f"[INFO] 🧠 多线程AI处理系统初始化")
        print(f"   • 推理线程数: {self.num_inference_threads}")
        print(f"   • 后处理线程数: {self.num_postprocess_threads}")
        print(f"   • 批处理大小: {batch_size}")
        print(f"   • GPU推理: {enable_gpu_inference}")
        print(f"   • 并行后处理: {enable_parallel_postprocess}")
        
        # 初始化模型会话池
        self.model_sessions = []
        self._initialize_model_sessions()
        
        # 线程池
        self.inference_executor = ThreadPoolExecutor(max_workers=self.num_inference_threads)
        self.postprocess_executor = ThreadPoolExecutor(max_workers=self.num_postprocess_threads)
        
        # 队列系统
        self.input_queue = queue.Queue(maxsize=20)
        self.inference_queue = queue.Queue(maxsize=10)
        self.postprocess_queue = queue.Queue(maxsize=10)  # 添加缺失的后处理队列
        self.output_queue = queue.Queue(maxsize=10)
        
        # 批处理缓冲区
        self.batch_buffer = []
        self.batch_lock = threading.Lock()
        
        # 控制变量
        self.running = False
        self.worker_threads = []
        
        # 性能统计
        self.stats = {
            'frames_received': 0,
            'frames_processed': 0,
            'inference_count': 0,
            'postprocess_count': 0,
            'avg_inference_time': 0.0,
            'avg_postprocess_time': 0.0,
            'throughput_fps': 0.0,
            'batch_efficiency': 0.0
        }
        
        print(f"[SUCCESS] ✅ 多线程AI处理系统初始化完成")
    
    def _initialize_model_sessions(self):
        """初始化模型会话池"""
        try:
            # 配置ONNX Runtime
            providers = []
            if self.enable_gpu_inference and ort.get_available_providers():
                if 'CUDAExecutionProvider' in ort.get_available_providers():
                    providers.append(('CUDAExecutionProvider', {
                        'device_id': 0,
                        'arena_extend_strategy': 'kNextPowerOfTwo',
                        'gpu_mem_limit': 2 * 1024 * 1024 * 1024,  # 2GB
                        'cudnn_conv_algo_search': 'EXHAUSTIVE',
                        'do_copy_in_default_stream': True,
                    }))
                elif 'DmlExecutionProvider' in ort.get_available_providers():
                    providers.append('DmlExecutionProvider')
            
            providers.append('CPUExecutionProvider')
            
            # 创建多个会话实例
            for i in range(self.num_inference_threads):
                session_options = ort.SessionOptions()
                session_options.inter_op_num_threads = 2
                session_options.intra_op_num_threads = 4
                session_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
                session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                
                session = ort.InferenceSession(
                    self.model_path,
                    sess_options=session_options,
                    providers=providers
                )
                
                self.model_sessions.append({
                    'session': session,
                    'input_name': session.get_inputs()[0].name,
                    'output_names': [output.name for output in session.get_outputs()],
                    'lock': threading.Lock(),
                    'usage_count': 0
                })
            
            print(f"[INFO] ✅ 创建了 {len(self.model_sessions)} 个模型会话")
            
        except Exception as e:
            print(f"[ERROR] 模型会话初始化失败: {e}")
            raise
    
    def start(self):
        """启动AI处理系统"""
        if self.running:
            return
        
        self.running = True
        
        print(f"[INFO] 🚀 启动多线程AI处理系统")
        
        # 启动批处理收集线程
        batch_thread = threading.Thread(
            target=self._batch_collector_worker,
            daemon=True,
            name="BatchCollector"
        )
        batch_thread.start()
        self.worker_threads.append(batch_thread)
        
        # 启动推理工作线程
        for i in range(self.num_inference_threads):
            thread = threading.Thread(
                target=self._inference_worker,
                args=(i,),
                daemon=True,
                name=f"InferenceWorker-{i}"
            )
            thread.start()
            self.worker_threads.append(thread)
        
        # 启动后处理工作线程
        for i in range(self.num_postprocess_threads):
            thread = threading.Thread(
                target=self._postprocess_worker,
                args=(i,),
                daemon=True,
                name=f"PostprocessWorker-{i}"
            )
            thread.start()
            self.worker_threads.append(thread)
        
        # 启动统计线程
        stats_thread = threading.Thread(
            target=self._stats_worker,
            daemon=True,
            name="StatsWorker"
        )
        stats_thread.start()
        self.worker_threads.append(stats_thread)
        
        print(f"[SUCCESS] ✅ 多线程AI处理系统已启动")
    
    def stop(self):
        """停止AI处理系统"""
        if not self.running:
            return
        
        print("[INFO] 🛑 停止多线程AI处理系统...")
        self.running = False
        
        # 等待线程结束
        for thread in self.worker_threads:
            thread.join(timeout=1.0)
        
        # 清空队列
        for q in [self.input_queue, self.inference_queue, self.output_queue]:
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break
        
        print("[SUCCESS] ✅ 多线程AI处理系统已停止")
    
    def process_frame_async(self, frame: np.ndarray, metadata: Dict = None) -> bool:
        """异步处理帧"""
        try:
            frame_data = {
                'frame': frame,
                'metadata': metadata or {},
                'timestamp': time.time(),
                'frame_id': self.stats['frames_received']
            }
            
            self.input_queue.put_nowait(frame_data)
            self.stats['frames_received'] += 1
            return True
            
        except queue.Full:
            return False
    
    def get_result(self, timeout: float = 0.001) -> Optional[Dict]:
        """获取处理结果"""
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def _batch_collector_worker(self):
        """批处理收集工作线程"""
        while self.running:
            try:
                # 收集批处理数据
                batch_frames = []
                batch_metadata = []
                
                # 尝试填满批次
                for _ in range(self.batch_size):
                    try:
                        frame_data = self.input_queue.get(timeout=0.001)
                        batch_frames.append(frame_data['frame'])
                        batch_metadata.append(frame_data)
                    except queue.Empty:
                        break
                
                # 如果有数据就处理
                if batch_frames:
                    # 准备批处理输入
                    if len(batch_frames) == 1:
                        # 单帧处理
                        batch_input = np.expand_dims(batch_frames[0], 0)
                    else:
                        # 多帧批处理
                        batch_input = np.stack(batch_frames, axis=0)
                    
                    # 转换为模型输入格式 (NCHW)
                    if batch_input.ndim == 4:
                        # 批处理情况
                        if batch_input.shape[-1] == 4:
                            # 移除alpha通道 (RGBA -> RGB)
                            batch_input = batch_input[:, :, :, :3]
                        if batch_input.shape[-1] == 3:
                            # 从 (batch, H, W, C) 转换为 (batch, C, H, W)
                            batch_input = np.transpose(batch_input, (0, 3, 1, 2))
                    elif batch_input.ndim == 3:
                        # 单帧情况
                        if batch_input.shape[-1] == 4:
                            # 移除alpha通道 (RGBA -> RGB)
                            batch_input = batch_input[:, :, :3]
                        if batch_input.shape[-1] == 3:
                            # 从 (H, W, C) 转换为 (C, H, W)
                            batch_input = np.transpose(batch_input, (2, 0, 1))
                        # 添加批次维度 (C, H, W) -> (1, C, H, W)
                        batch_input = np.expand_dims(batch_input, axis=0)
                    
                    # 确保数据类型和数值范围正确
                    if batch_input.dtype == np.uint8:
                        batch_input = batch_input.astype(np.float32) / 255.0
                    elif batch_input.dtype != np.float32:
                        batch_input = batch_input.astype(np.float32)
                    
                    # 转换为模型期望的float16类型
                    batch_input = batch_input.astype(np.float16)
                    
                    print(f"[DEBUG] 批处理输入形状: {batch_input.shape}, 数据类型: {batch_input.dtype}")
                    
                    batch_data = {
                        'input': batch_input,  # 使用float16匹配模型期望
                        'metadata': batch_metadata,
                        'batch_size': len(batch_frames),
                        'timestamp': time.time()
                    }
                    
                    # 放入推理队列
                    try:
                        self.inference_queue.put_nowait(batch_data)
                    except queue.Full:
                        # 队列满时丢弃最旧的批次
                        try:
                            self.inference_queue.get_nowait()
                            self.inference_queue.put_nowait(batch_data)
                        except queue.Empty:
                            pass
                
                else:
                    time.sleep(0.0001)  # 0.1ms微延迟
                    
            except Exception as e:
                print(f"[ERROR] 批处理收集线程错误: {e}")
                time.sleep(0.001)
    
    def _inference_worker(self, worker_id: int):
        """推理工作线程"""
        session_info = self.model_sessions[worker_id % len(self.model_sessions)]
        
        while self.running:
            try:
                # 获取批处理数据
                batch_data = self.inference_queue.get(timeout=0.1)
                
                inference_start = time.time()
                
                # 执行推理
                with session_info['lock']:
                    session_info['usage_count'] += 1
                    
                    outputs = session_info['session'].run(
                        session_info['output_names'],
                        {session_info['input_name']: batch_data['input']}
                    )
                
                inference_time = time.time() - inference_start
                
                # 准备推理结果
                inference_result = {
                    'outputs': outputs,
                    'metadata': batch_data['metadata'],
                    'batch_size': batch_data['batch_size'],
                    'inference_time': inference_time,
                    'worker_id': worker_id,
                    'timestamp': batch_data['timestamp']
                }
                
                # 放入后处理队列
                try:
                    self.postprocess_queue.put_nowait(inference_result)  # 修复：应该放入后处理队列
                    self.stats['inference_count'] += 1
                except queue.Full:
                    pass
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] 推理线程 {worker_id} 错误: {e}")
                time.sleep(0.001)
    
    def _postprocess_worker(self, worker_id: int):
        """后处理工作线程"""
        while self.running:
            try:
                # 获取推理结果
                inference_result = self.postprocess_queue.get(timeout=0.1)  # 修复：从后处理队列获取数据
                
                postprocess_start = time.time()
                
                # 执行后处理
                processed_results = self._postprocess_batch(
                    inference_result['outputs'],
                    inference_result['metadata'],
                    inference_result['batch_size']
                )
                
                postprocess_time = time.time() - postprocess_start
                
                # 为每个结果创建输出
                for i, result in enumerate(processed_results):
                    output_data = {
                        'detections': result,
                        'metadata': inference_result['metadata'][i],
                        'inference_time': inference_result['inference_time'],
                        'postprocess_time': postprocess_time,
                        'total_time': inference_result['inference_time'] + postprocess_time,
                        'worker_id': worker_id,
                        'timestamp': inference_result['timestamp']
                    }
                    
                    # 放入输出队列
                    try:
                        self.output_queue.put_nowait(output_data)
                        self.stats['postprocess_count'] += 1
                        self.stats['frames_processed'] += 1
                    except queue.Full:
                        # 队列满时丢弃最旧的结果
                        try:
                            self.output_queue.get_nowait()
                            self.output_queue.put_nowait(output_data)
                        except queue.Empty:
                            pass
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] 后处理线程 {worker_id} 错误: {e}")
                time.sleep(0.001)
    
    def _postprocess_batch(self, outputs: List[np.ndarray], metadata: List[Dict], batch_size: int) -> List[pd.DataFrame]:
        """批处理后处理"""
        results = []
        
        try:
            # 检查outputs是否有效
            if not outputs or len(outputs) == 0:
                print("[WARNING] 后处理收到空的outputs")
                for _ in range(batch_size):
                    results.append(pd.DataFrame(columns=['x1', 'y1', 'x2', 'y2', 'confidence', 'class', 'center_x', 'center_y', 'width', 'height']))
                return results
            
            # 假设输出是 [batch_size, num_detections, 6] 格式
            predictions = outputs[0]  # 主要输出
            
            for i in range(batch_size):
                # 提取单个样本的预测
                pred = predictions[i:i+1]  # 保持批次维度
                
                # 应用NMS
                pred_nms = non_max_suppression(
                    torch.from_numpy(pred),
                    conf_thres=0.45,
                    iou_thres=0.45,
                    classes=None,
                    agnostic=False,
                    max_det=10
                )
                
                # 转换为DataFrame
                if pred_nms[0] is not None and len(pred_nms[0]) > 0:
                    detections = pred_nms[0].cpu().numpy()
                    
                    df = pd.DataFrame(detections, columns=['x1', 'y1', 'x2', 'y2', 'confidence', 'class'])
                    
                    # 计算中心点和尺寸
                    df['center_x'] = (df['x1'] + df['x2']) / 2
                    df['center_y'] = (df['y1'] + df['y2']) / 2
                    df['width'] = df['x2'] - df['x1']
                    df['height'] = df['y2'] - df['y1']
                    
                    results.append(df)
                else:
                    # 空检测结果
                    results.append(pd.DataFrame(columns=['x1', 'y1', 'x2', 'y2', 'confidence', 'class', 'center_x', 'center_y', 'width', 'height']))
            
        except Exception as e:
            print(f"[ERROR] 批处理后处理失败: {e}")
            # 返回空结果
            for _ in range(batch_size):
                results.append(pd.DataFrame(columns=['x1', 'y1', 'x2', 'y2', 'confidence', 'class', 'center_x', 'center_y', 'width', 'height']))
        
        return results
    
    def _stats_worker(self):
        """统计工作线程"""
        last_stats_time = time.time()
        last_processed = 0
        
        while self.running:
            try:
                time.sleep(1.0)  # 每秒更新统计
                
                current_time = time.time()
                time_diff = current_time - last_stats_time
                
                # 计算吞吐量
                processed_diff = self.stats['frames_processed'] - last_processed
                self.stats['throughput_fps'] = processed_diff / time_diff
                
                # 计算批处理效率
                if self.stats['inference_count'] > 0:
                    self.stats['batch_efficiency'] = self.stats['frames_processed'] / (self.stats['inference_count'] * self.batch_size)
                
                # 更新记录
                last_stats_time = current_time
                last_processed = self.stats['frames_processed']
                
            except Exception as e:
                print(f"[ERROR] 统计线程错误: {e}")
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        stats = self.stats.copy()
        
        # 添加队列状态
        stats['queue_sizes'] = {
            'input': self.input_queue.qsize(),
            'inference': self.inference_queue.qsize(),
            'output': self.output_queue.qsize()
        }
        
        # 添加会话使用情况
        stats['session_usage'] = [session['usage_count'] for session in self.model_sessions]
        
        return stats
    
    def print_performance_stats(self):
        """打印性能统计"""
        stats = self.get_performance_stats()
        print(f"\n🧠 多线程AI处理系统统计:")
        print(f"   • 吞吐量FPS: {stats['throughput_fps']:.1f}")
        print(f"   • 总接收帧数: {stats['frames_received']}")
        print(f"   • 总处理帧数: {stats['frames_processed']}")
        print(f"   • 推理次数: {stats['inference_count']}")
        print(f"   • 后处理次数: {stats['postprocess_count']}")
        print(f"   • 批处理效率: {stats['batch_efficiency']:.2%}")
        print(f"   • 队列大小: {stats['queue_sizes']}")
    
    def cleanup(self):
        """清理资源"""
        self.stop()
        
        if hasattr(self, 'inference_executor'):
            self.inference_executor.shutdown(wait=False)
        
        if hasattr(self, 'postprocess_executor'):
            self.postprocess_executor.shutdown(wait=False)
        
        # 清理模型会话
        for session_info in self.model_sessions:
            try:
                del session_info['session']
            except:
                pass
        
        print("[INFO] ✅ 多线程AI处理系统资源已清理")

def create_multi_threaded_ai_processor(model_path: str, **kwargs):
    """创建多线程AI处理系统"""
    return MultiThreadedAIProcessor(model_path=model_path, **kwargs)

if __name__ == "__main__":
    # 测试多线程AI处理系统
    processor = create_multi_threaded_ai_processor(
        model_path="yolov5s320Half.onnx",
        batch_size=4,
        num_inference_threads=2,
        num_postprocess_threads=4
    )
    
    try:
        processor.start()
        
        print("[INFO] 测试运行30秒...")
        start_time = time.time()
        
        # 模拟输入帧
        test_frame = np.random.randint(0, 255, (320, 320, 3), dtype=np.uint8).astype(np.float16) / 255.0
        
        while time.time() - start_time < 30:
            # 提交处理任务
            processor.process_frame_async(test_frame)
            
            # 获取结果
            result = processor.get_result()
            if result:
                print(f"处理完成: {result['timestamp']:.3f}, 检测数: {len(result['detections'])}")
            
            time.sleep(0.01)  # 100FPS输入
        
        processor.print_performance_stats()
        
    finally:
        processor.cleanup()
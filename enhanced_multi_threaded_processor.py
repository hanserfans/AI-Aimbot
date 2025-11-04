#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的多线程AI处理器
集成帧时间顺序管理，确保处理最新帧
"""

import numpy as np
import torch
import onnxruntime as ort
import time
import threading
import queue
import heapq
from typing import Optional, Dict, List, Tuple, Any
import psutil
import pandas as pd
from utils.general import non_max_suppression, xyxy2xywh
import cv2

class FrameOrderingManager:
    """帧时间顺序管理器（简化版）"""
    
    def __init__(self, max_frame_age: float = 0.05, buffer_size: int = 10):
        self.max_frame_age = max_frame_age
        self.buffer_size = buffer_size
        self.frame_heap = []  # 存储 (-timestamp, frame_id, frame_data)
        self.heap_lock = threading.Lock()
        self.frame_counter = 0
        self.counter_lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            'frames_received': 0,
            'frames_processed': 0,
            'frames_discarded_old': 0,
            'frames_discarded_overflow': 0,
            'avg_frame_age': 0.0
        }
    
    def add_frame(self, frame_data: Dict) -> bool:
        """添加帧到有序缓冲区"""
        current_time = time.time()
        frame_timestamp = frame_data.get('timestamp', current_time)
        
        # 检查帧是否过时
        frame_age = current_time - frame_timestamp
        if frame_age > self.max_frame_age:
            self.stats['frames_discarded_old'] += 1
            return False
        
        with self.counter_lock:
            frame_id = self.frame_counter
            self.frame_counter += 1
        
        with self.heap_lock:
            # 检查缓冲区是否已满
            if len(self.frame_heap) >= self.buffer_size:
                if self.frame_heap:
                    heapq.heappop(self.frame_heap)
                    self.stats['frames_discarded_overflow'] += 1
            
            # 添加新帧（使用负时间戳使最新帧在堆顶）
            heapq.heappush(self.frame_heap, (-frame_timestamp, frame_id, frame_data))
            self.stats['frames_received'] += 1
        
        return True
    
    def get_latest_frame(self) -> Optional[Dict]:
        """获取最新的帧"""
        with self.heap_lock:
            if not self.frame_heap:
                return None
            
            # 获取最新帧（堆顶）
            neg_timestamp, frame_id, frame_data = heapq.heappop(self.frame_heap)
            timestamp = -neg_timestamp
            
            # 检查帧是否仍然有效
            current_time = time.time()
            frame_age = current_time - timestamp
            
            if frame_age > self.max_frame_age:
                self.stats['frames_discarded_old'] += 1
                return self.get_latest_frame()  # 递归获取下一个帧
            
            self.stats['frames_processed'] += 1
            self.stats['avg_frame_age'] = (
                self.stats['avg_frame_age'] * (self.stats['frames_processed'] - 1) + frame_age
            ) / self.stats['frames_processed']
            
            # 添加处理时间信息
            frame_data['processing_timestamp'] = current_time
            frame_data['frame_age'] = frame_age
            frame_data['frame_id'] = frame_id
            
            return frame_data
    
    def get_batch_frames(self, batch_size: int) -> List[Dict]:
        """获取一批最新帧"""
        frames = []
        for _ in range(batch_size):
            frame = self.get_latest_frame()
            if frame is None:
                break
            frames.append(frame)
        return frames
    
    def clear_old_frames(self):
        """清理过时帧"""
        current_time = time.time()
        
        with self.heap_lock:
            valid_frames = []
            
            while self.frame_heap:
                neg_timestamp, frame_id, frame_data = heapq.heappop(self.frame_heap)
                timestamp = -neg_timestamp
                frame_age = current_time - timestamp
                
                if frame_age <= self.max_frame_age:
                    valid_frames.append((neg_timestamp, frame_id, frame_data))
                else:
                    self.stats['frames_discarded_old'] += 1
            
            # 重建堆
            self.frame_heap = valid_frames
            heapq.heapify(self.frame_heap)
    
    def get_buffer_size(self) -> int:
        """获取当前缓冲区大小"""
        with self.heap_lock:
            return len(self.frame_heap)


class EnhancedMultiThreadedAIProcessor:
    """增强的多线程AI处理器，集成帧时间顺序管理"""
    
    def __init__(self,
                 model_path: str,
                 num_inference_threads: int = None,
                 num_postprocess_threads: int = None,
                 batch_size: int = 4,
                 enable_gpu_inference: bool = True,
                 max_frame_age: float = 0.05):
        """
        初始化增强多线程AI处理系统
        
        Args:
            model_path: 模型路径
            num_inference_threads: 推理线程数
            num_postprocess_threads: 后处理线程数
            batch_size: 批处理大小
            enable_gpu_inference: 启用GPU推理
            max_frame_age: 最大帧年龄（秒）
        """
        self.model_path = model_path
        self.batch_size = batch_size
        self.enable_gpu_inference = enable_gpu_inference
        self.max_frame_age = max_frame_age
        
        # 自动检测最优线程数
        cpu_count = psutil.cpu_count(logical=True)
        self.num_inference_threads = num_inference_threads or min(4, max(2, cpu_count // 4))
        self.num_postprocess_threads = num_postprocess_threads or min(8, max(4, cpu_count // 2))
        
        print(f"[INFO] 🚀 增强多线程AI处理系统初始化")
        print(f"   • 推理线程数: {self.num_inference_threads}")
        print(f"   • 后处理线程数: {self.num_postprocess_threads}")
        print(f"   • 批处理大小: {batch_size}")
        print(f"   • GPU推理: {enable_gpu_inference}")
        print(f"   • 最大帧年龄: {max_frame_age*1000:.1f}ms")
        
        # 帧时间顺序管理器
        self.frame_manager = FrameOrderingManager(
            max_frame_age=max_frame_age,
            buffer_size=batch_size * 3  # 缓冲区大小为批处理大小的3倍
        )
        
        # 初始化模型会话
        self.model_session = None
        self._initialize_model_session()
        
        # 队列系统
        self.inference_queue = queue.Queue(maxsize=10)
        self.postprocess_queue = queue.Queue(maxsize=10)  # 🔧 添加后处理队列
        self.output_queue = queue.Queue(maxsize=10)  # 最终输出队列
        
        # 控制变量
        self.running = False
        self.worker_threads = []
        
        # 性能统计
        self.stats = {
            'frames_received': 0,
            'frames_processed': 0,
            'inference_count': 0,
            'avg_inference_time': 0.0,
            'avg_postprocess_time': 0.0,
            'throughput_fps': 0.0,
            'frame_ordering_stats': {}
        }
        
        print(f"[SUCCESS] ✅ 增强多线程AI处理系统初始化完成")
    
    def _initialize_model_session(self):
        """初始化模型会话"""
        try:
            # 配置ONNX Runtime
            providers = []
            if self.enable_gpu_inference:
                if 'CUDAExecutionProvider' in ort.get_available_providers():
                    providers.append('CUDAExecutionProvider')
                    print("[INFO] 🎮 使用CUDA GPU推理")
                elif 'DmlExecutionProvider' in ort.get_available_providers():
                    providers.append('DmlExecutionProvider')
                    print("[INFO] 🎮 使用DirectML GPU推理")
            
            providers.append('CPUExecutionProvider')
            
            # 创建会话选项
            sess_options = ort.SessionOptions()
            sess_options.inter_op_num_threads = self.num_inference_threads
            sess_options.intra_op_num_threads = self.num_inference_threads
            sess_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # 创建推理会话
            self.model_session = ort.InferenceSession(
                self.model_path,
                sess_options=sess_options,
                providers=providers
            )
            
            print(f"[SUCCESS] ✅ 模型会话初始化完成")
            print(f"   • 提供者: {self.model_session.get_providers()}")
            
        except Exception as e:
            print(f"[ERROR] ❌ 模型会话初始化失败: {e}")
            raise
    
    def start(self):
        """启动处理系统"""
        if self.running:
            return
        
        self.running = True
        
        # 启动工作线程
        threads = [
            ('BatchCollector', self._batch_collector_worker),
            ('InferenceWorker', self._inference_worker),
            ('PostprocessWorker', self._postprocess_worker),
            ('FrameCleanup', self._frame_cleanup_worker),
            ('StatsWorker', self._stats_worker)
        ]
        
        for name, target in threads:
            thread = threading.Thread(target=target, daemon=True, name=name)
            thread.start()
            self.worker_threads.append(thread)
        
        print("[INFO] ✅ 增强多线程AI处理系统已启动")
    
    def stop(self):
        """停止处理系统"""
        self.running = False
        
        # 等待线程结束
        for thread in self.worker_threads:
            thread.join(timeout=1.0)
        
        self.worker_threads.clear()
        print("[INFO] 🛑 增强多线程AI处理系统已停止")
    
    def process_frame_async(self, frame: np.ndarray, metadata: Dict = None) -> bool:
        """
        异步处理帧（集成帧时间顺序管理）
        
        Args:
            frame: 输入帧
            metadata: 元数据
            
        Returns:
            是否成功提交处理
        """
        try:
            frame_data = {
                'frame': frame,
                'metadata': metadata or {},
                'timestamp': time.time(),
                'original_frame_id': self.stats['frames_received']
            }
            
            # 使用帧时间顺序管理器
            success = self.frame_manager.add_frame(frame_data)
            if success:
                self.stats['frames_received'] += 1
            
            return success
            
        except Exception as e:
            print(f"[ERROR] 帧提交失败: {e}")
            return False
    
    def get_result(self, timeout: float = 0.001) -> Optional[Dict]:
        """获取处理结果"""
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def _batch_collector_worker(self):
        """批处理收集工作线程（使用帧时间顺序管理）"""
        while self.running:
            try:
                # 从帧管理器获取最新帧
                batch_frames_data = self.frame_manager.get_batch_frames(self.batch_size)
                
                if not batch_frames_data:
                    time.sleep(0.001)
                    continue
                
                # 准备批处理数据
                batch_frames = []
                batch_metadata = []
                
                for frame_data in batch_frames_data:
                    batch_frames.append(frame_data['frame'])
                    batch_metadata.append(frame_data)
                
                # 准备批处理输入
                if len(batch_frames) == 1:
                    batch_input = np.expand_dims(batch_frames[0], 0)
                else:
                    batch_input = np.stack(batch_frames, axis=0)
                
                # 转换为模型输入格式 (NCHW)
                batch_input = self._prepare_model_input(batch_input)
                
                # 提交到推理队列
                inference_data = {
                    'input': batch_input,
                    'metadata': batch_metadata,
                    'batch_size': len(batch_frames),
                    'timestamp': time.time()
                }
                
                try:
                    self.inference_queue.put_nowait(inference_data)
                except queue.Full:
                    # 队列满时丢弃最旧的推理任务
                    try:
                        self.inference_queue.get_nowait()
                        self.inference_queue.put_nowait(inference_data)
                    except queue.Empty:
                        pass
                
            except Exception as e:
                print(f"[ERROR] 批处理收集线程错误: {e}")
                time.sleep(0.001)
    
    def _prepare_model_input(self, batch_input: np.ndarray) -> np.ndarray:
        """准备模型输入格式"""
        try:
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
                    batch_input = batch_input[:, :, :3]
                if batch_input.shape[-1] == 3:
                    batch_input = np.transpose(batch_input, (2, 0, 1))
                batch_input = np.expand_dims(batch_input, 0)
            
            # 归一化到 [0, 1]
            if batch_input.dtype == np.uint8:
                batch_input = batch_input.astype(np.float32) / 255.0
            elif batch_input.dtype != np.float32:
                batch_input = batch_input.astype(np.float32)
            
            # 🔧 关键修复：转换为模型期望的float16类型
            batch_input = batch_input.astype(np.float16)
            
            print(f"[DEBUG] 模型输入准备完成 - 形状: {batch_input.shape}, 数据类型: {batch_input.dtype}")
            
            return batch_input
            
        except Exception as e:
            print(f"[ERROR] 模型输入准备失败: {e}")
            print(f"[ERROR] 输入形状: {batch_input.shape if batch_input is not None else 'None'}")
            print(f"[ERROR] 输入数据类型: {batch_input.dtype if batch_input is not None else 'None'}")
            return batch_input
    
    def _inference_worker(self):
        """推理工作线程"""
        while self.running:
            try:
                # 获取推理任务
                inference_data = self.inference_queue.get(timeout=0.1)
                
                start_time = time.time()
                
                # 执行推理
                input_name = self.model_session.get_inputs()[0].name
                outputs = self.model_session.run(None, {input_name: inference_data['input']})
                
                inference_time = time.time() - start_time
                
                # 更新统计
                self.stats['inference_count'] += 1
                self.stats['avg_inference_time'] = (
                    self.stats['avg_inference_time'] * (self.stats['inference_count'] - 1) + inference_time
                ) / self.stats['inference_count']
                
                # 提交到后处理
                postprocess_data = {
                    'outputs': outputs,
                    'metadata': inference_data['metadata'],
                    'batch_size': inference_data['batch_size'],
                    'inference_time': inference_time,
                    'timestamp': time.time()
                }
                
                try:
                    self.postprocess_queue.put_nowait(postprocess_data)  # 🔧 修复：放入后处理队列
                except queue.Full:
                    # 队列满时丢弃最旧的结果
                    try:
                        self.postprocess_queue.get_nowait()
                        self.postprocess_queue.put_nowait(postprocess_data)
                    except queue.Empty:
                        pass
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] 推理线程错误: {e}")
                time.sleep(0.001)
    
    def _postprocess_worker(self):
        """后处理工作线程"""
        while self.running:
            try:
                # 获取推理结果进行后处理
                postprocess_data = self.postprocess_queue.get(timeout=0.1)  # 🔧 修复：从后处理队列获取
                
                # 执行后处理
                processed_results = self._postprocess_batch(
                    postprocess_data['outputs'],
                    postprocess_data['metadata'],
                    postprocess_data['batch_size']
                )
                
                # 为每个结果创建最终输出
                for i, result in enumerate(processed_results):
                    # 获取对应的元数据
                    frame_metadata = postprocess_data['metadata'][i] if i < len(postprocess_data['metadata']) else {}
                    
                    # 计算帧年龄（如果有时间戳信息）
                    frame_age = 0
                    if 'timestamp' in frame_metadata:
                        frame_age = time.time() - frame_metadata['timestamp']
                    
                    final_output = {
                        'detections': result,  # 🔧 修复：使用正确的键名
                        'metadata': frame_metadata,
                        'inference_time': postprocess_data['inference_time'],
                        'frame_age': frame_age,
                        'frame_id': frame_metadata.get('frame_id', 'unknown'),
                        'timestamp': postprocess_data['timestamp']
                    }
                    
                    # 放入最终输出队列
                    try:
                        self.output_queue.put_nowait(final_output)  # 🔧 修复：放入输出队列
                        self.stats['frames_processed'] += 1
                        
                    except queue.Full:
                        # 队列满时丢弃最旧的结果
                        try:
                            self.output_queue.get_nowait()
                            self.output_queue.put_nowait(final_output)
                        except queue.Empty:
                            pass
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] 后处理线程错误: {e}")
                time.sleep(0.001)
    
    def _frame_cleanup_worker(self):
        """帧清理工作线程"""
        while self.running:
            try:
                self.frame_manager.clear_old_frames()
                time.sleep(0.01)  # 每10ms清理一次
            except Exception as e:
                print(f"[ERROR] 帧清理线程错误: {e}")
                time.sleep(0.1)
    
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
                
                # 更新帧管理器统计
                self.stats['frame_ordering_stats'] = self.frame_manager.stats.copy()
                
                # 更新记录
                last_stats_time = current_time
                last_processed = self.stats['frames_processed']
                
            except Exception as e:
                print(f"[ERROR] 统计线程错误: {e}")
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        stats = self.stats.copy()
        
        # 添加队列状态
        stats['queue_status'] = {
            'inference_queue_size': self.inference_queue.qsize(),
            'postprocess_queue_size': self.postprocess_queue.qsize(),  # 🔧 添加后处理队列状态
            'output_queue_size': self.output_queue.qsize(),
            'frame_buffer_size': self.frame_manager.get_buffer_size()
        }
        
        return stats
    
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
    
    def print_performance_stats(self):
        """打印性能统计"""
        stats = self.get_performance_stats()
        frame_stats = stats['frame_ordering_stats']
        queue_status = stats['queue_status']
        
        print(f"\n🚀 增强多线程AI处理器统计:")
        print(f"   • 接收帧数: {stats['frames_received']}")
        print(f"   • 处理帧数: {stats['frames_processed']}")
        print(f"   • 推理次数: {stats['inference_count']}")
        print(f"   • 平均推理时间: {stats['avg_inference_time']*1000:.1f}ms")
        print(f"   • 吞吐量: {stats['throughput_fps']:.1f} FPS")
        
        print(f"\n🕒 帧时间顺序管理统计:")
        print(f"   • 帧管理器接收: {frame_stats.get('frames_received', 0)}")
        print(f"   • 帧管理器处理: {frame_stats.get('frames_processed', 0)}")
        print(f"   • 丢弃过时帧: {frame_stats.get('frames_discarded_old', 0)}")
        print(f"   • 丢弃溢出帧: {frame_stats.get('frames_discarded_overflow', 0)}")
        print(f"   • 平均帧年龄: {frame_stats.get('avg_frame_age', 0)*1000:.1f}ms")
        
        print(f"\n📊 队列状态:")
        print(f"   • 推理队列: {queue_status['inference_queue_size']}")
        print(f"   • 后处理队列: {queue_status['postprocess_queue_size']}")  # 🔧 添加后处理队列显示
        print(f"   • 输出队列: {queue_status['output_queue_size']}")
        print(f"   • 帧缓冲区: {queue_status['frame_buffer_size']}")


def test_enhanced_processor():
    """测试增强处理器"""
    print("🧪 测试增强多线程AI处理器")
    print("=" * 60)
    
    # 注意：这里需要实际的模型路径
    # processor = EnhancedMultiThreadedAIProcessor(
    #     model_path="path/to/your/model.onnx",
    #     batch_size=2,
    #     max_frame_age=0.1
    # )
    
    print("✅ 增强处理器测试框架准备完成")
    print("💡 需要实际模型路径才能完整测试")


if __name__ == "__main__":
    test_enhanced_processor()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帧时间顺序修复系统
解决多线程截图中的时间顺序问题，确保始终处理最新帧
"""

import time
import threading
import queue
import heapq
from typing import Dict, List, Optional, Tuple
import numpy as np

class FrameOrderingManager:
    """帧时间顺序管理器"""
    
    def __init__(self, max_frame_age: float = 0.05, buffer_size: int = 10):
        """
        初始化帧顺序管理器
        
        Args:
            max_frame_age: 最大帧年龄（秒），超过此时间的帧将被丢弃
            buffer_size: 缓冲区大小
        """
        self.max_frame_age = max_frame_age
        self.buffer_size = buffer_size
        
        # 使用优先队列（最小堆）按时间戳排序
        self.frame_heap = []  # 存储 (-timestamp, frame_id, frame_data)
        self.heap_lock = threading.Lock()
        
        # 帧ID计数器
        self.frame_counter = 0
        self.counter_lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            'frames_received': 0,
            'frames_processed': 0,
            'frames_discarded_old': 0,
            'frames_discarded_overflow': 0,
            'avg_frame_age': 0.0,
            'latest_timestamp': 0.0
        }
        
        print("[INFO] 🕒 帧时间顺序管理器初始化完成")
        print(f"   • 最大帧年龄: {max_frame_age*1000:.1f}ms")
        print(f"   • 缓冲区大小: {buffer_size}")
    
    def add_frame(self, frame_data: Dict) -> bool:
        """
        添加帧到有序缓冲区
        
        Args:
            frame_data: 包含frame和timestamp的字典
            
        Returns:
            是否成功添加
        """
        current_time = time.time()
        frame_timestamp = frame_data.get('timestamp', current_time)
        
        # 检查帧是否过时
        frame_age = current_time - frame_timestamp
        if frame_age > self.max_frame_age:
            self.stats['frames_discarded_old'] += 1
            print(f"[WARNING] 丢弃过时帧: 年龄 {frame_age*1000:.1f}ms > {self.max_frame_age*1000:.1f}ms")
            return False
        
        with self.counter_lock:
            frame_id = self.frame_counter
            self.frame_counter += 1
        
        with self.heap_lock:
            # 检查缓冲区是否已满
            if len(self.frame_heap) >= self.buffer_size:
                # 移除最旧的帧（堆顶）
                if self.frame_heap:
                    removed_frame = heapq.heappop(self.frame_heap)
                    self.stats['frames_discarded_overflow'] += 1
                    print(f"[INFO] 缓冲区满，丢弃旧帧: ID {removed_frame[1]}")
            
            # 添加新帧（使用负时间戳使最新帧在堆顶）
            heapq.heappush(self.frame_heap, (-frame_timestamp, frame_id, frame_data))
            self.stats['frames_received'] += 1
            self.stats['latest_timestamp'] = max(self.stats['latest_timestamp'], frame_timestamp)
        
        return True
    
    def get_latest_frame(self) -> Optional[Dict]:
        """
        获取最新的帧
        
        Returns:
            最新帧数据或None
        """
        with self.heap_lock:
            if not self.frame_heap:
                return None
            
            # 获取最新帧（堆顶，负时间戳最大的）
            neg_timestamp, frame_id, frame_data = heapq.heappop(self.frame_heap)
            timestamp = -neg_timestamp
            
            # 检查帧是否仍然有效
            current_time = time.time()
            frame_age = current_time - timestamp
            
            if frame_age > self.max_frame_age:
                self.stats['frames_discarded_old'] += 1
                print(f"[WARNING] 获取时发现过时帧: 年龄 {frame_age*1000:.1f}ms")
                return self.get_latest_frame()  # 递归获取下一个帧
            
            self.stats['frames_processed'] += 1
            self.stats['avg_frame_age'] = (self.stats['avg_frame_age'] * (self.stats['frames_processed'] - 1) + frame_age) / self.stats['frames_processed']
            
            # 添加处理时间信息
            frame_data['processing_timestamp'] = current_time
            frame_data['frame_age'] = frame_age
            frame_data['frame_id'] = frame_id
            
            return frame_data
    
    def get_all_valid_frames(self) -> List[Dict]:
        """
        获取所有有效帧，按时间戳排序（最新在前）
        
        Returns:
            有效帧列表
        """
        valid_frames = []
        current_time = time.time()
        
        with self.heap_lock:
            # 创建临时列表存储有效帧
            temp_frames = []
            
            while self.frame_heap:
                neg_timestamp, frame_id, frame_data = heapq.heappop(self.frame_heap)
                timestamp = -neg_timestamp
                frame_age = current_time - timestamp
                
                if frame_age <= self.max_frame_age:
                    temp_frames.append((neg_timestamp, frame_id, frame_data))
                else:
                    self.stats['frames_discarded_old'] += 1
            
            # 按时间戳排序（最新在前）
            temp_frames.sort(key=lambda x: x[0])  # 负时间戳排序
            
            # 重建堆并准备返回数据
            for neg_timestamp, frame_id, frame_data in temp_frames:
                heapq.heappush(self.frame_heap, (neg_timestamp, frame_id, frame_data))
                
                frame_data_copy = frame_data.copy()
                frame_data_copy['processing_timestamp'] = current_time
                frame_data_copy['frame_age'] = current_time - (-neg_timestamp)
                frame_data_copy['frame_id'] = frame_id
                valid_frames.append(frame_data_copy)
        
        return valid_frames
    
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
    
    def get_buffer_status(self) -> Dict:
        """获取缓冲区状态"""
        with self.heap_lock:
            buffer_size = len(self.frame_heap)
            
            if buffer_size > 0:
                # 计算时间范围
                timestamps = [-item[0] for item in self.frame_heap]
                oldest_timestamp = min(timestamps)
                newest_timestamp = max(timestamps)
                time_span = newest_timestamp - oldest_timestamp
            else:
                time_span = 0.0
        
        return {
            'buffer_size': buffer_size,
            'max_buffer_size': self.buffer_size,
            'time_span_ms': time_span * 1000,
            'utilization': buffer_size / self.buffer_size
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        stats['buffer_status'] = self.get_buffer_status()
        return stats
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()
        buffer_status = stats['buffer_status']
        
        print(f"\n🕒 帧时间顺序管理器统计:")
        print(f"   • 接收帧数: {stats['frames_received']}")
        print(f"   • 处理帧数: {stats['frames_processed']}")
        print(f"   • 丢弃过时帧: {stats['frames_discarded_old']}")
        print(f"   • 丢弃溢出帧: {stats['frames_discarded_overflow']}")
        print(f"   • 平均帧年龄: {stats['avg_frame_age']*1000:.1f}ms")
        print(f"   • 缓冲区使用率: {buffer_status['utilization']:.1%}")
        print(f"   • 缓冲区时间跨度: {buffer_status['time_span_ms']:.1f}ms")


class EnhancedMultiThreadProcessor:
    """增强的多线程处理器，集成帧时间顺序管理"""
    
    def __init__(self, max_frame_age: float = 0.05):
        """
        初始化增强处理器
        
        Args:
            max_frame_age: 最大帧年龄（秒）
        """
        self.frame_manager = FrameOrderingManager(max_frame_age=max_frame_age)
        self.running = False
        self.cleanup_thread = None
        
        print("[INFO] 🚀 增强多线程处理器初始化完成")
    
    def start(self):
        """启动处理器"""
        if self.running:
            return
        
        self.running = True
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True,
            name="FrameCleanupThread"
        )
        self.cleanup_thread.start()
        
        print("[INFO] ✅ 增强多线程处理器已启动")
    
    def stop(self):
        """停止处理器"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=1.0)
        print("[INFO] 🛑 增强多线程处理器已停止")
    
    def _cleanup_worker(self):
        """清理工作线程"""
        while self.running:
            try:
                self.frame_manager.clear_old_frames()
                time.sleep(0.01)  # 每10ms清理一次
            except Exception as e:
                print(f"[ERROR] 帧清理线程错误: {e}")
                time.sleep(0.1)
    
    def process_frame(self, frame_data: Dict) -> bool:
        """
        处理帧
        
        Args:
            frame_data: 帧数据
            
        Returns:
            是否成功处理
        """
        return self.frame_manager.add_frame(frame_data)
    
    def get_latest_frame(self) -> Optional[Dict]:
        """获取最新帧"""
        return self.frame_manager.get_latest_frame()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.frame_manager.get_stats()
    
    def print_stats(self):
        """打印统计信息"""
        self.frame_manager.print_stats()


def test_frame_ordering():
    """测试帧时间顺序管理"""
    print("🧪 测试帧时间顺序管理")
    print("=" * 60)
    
    # 创建管理器
    manager = FrameOrderingManager(max_frame_age=0.1, buffer_size=5)
    
    # 模拟多线程添加帧（时间顺序混乱）
    test_frames = [
        {'frame': np.zeros((100, 100, 3)), 'timestamp': time.time() + 0.01, 'source': 'thread_1'},
        {'frame': np.zeros((100, 100, 3)), 'timestamp': time.time() + 0.005, 'source': 'thread_2'},  # 较早
        {'frame': np.zeros((100, 100, 3)), 'timestamp': time.time() + 0.015, 'source': 'thread_3'},  # 最新
        {'frame': np.zeros((100, 100, 3)), 'timestamp': time.time() - 0.2, 'source': 'thread_4'},   # 过时
    ]
    
    print("添加测试帧...")
    for i, frame_data in enumerate(test_frames):
        success = manager.add_frame(frame_data)
        print(f"帧 {i+1} ({frame_data['source']}): {'成功' if success else '失败'}")
    
    print("\n获取帧（按时间顺序）...")
    frame_count = 0
    while True:
        frame = manager.get_latest_frame()
        if frame is None:
            break
        frame_count += 1
        print(f"帧 {frame_count}: {frame['source']}, 年龄: {frame['frame_age']*1000:.1f}ms")
    
    print("\n统计信息:")
    manager.print_stats()


if __name__ == "__main__":
    test_frame_ordering()
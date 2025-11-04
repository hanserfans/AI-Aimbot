"""
增强的最新帧获取系统
解决头部位置历史记忆问题，确保获取真正的最新数据帧
"""

import time
import threading
import queue
import numpy as np
from typing import Optional, Dict, Any
from collections import deque
import cv2

class EnhancedLatestFrameSystem:
    """增强的最新帧获取系统"""
    
    def __init__(self, max_frame_age_ms: float = 16.67):  # 约60fps的帧间隔
        """
        初始化增强的最新帧系统
        
        Args:
            max_frame_age_ms: 最大帧年龄（毫秒），超过此时间的帧被认为过时
        """
        self.max_frame_age_ms = max_frame_age_ms
        self.frame_lock = threading.RLock()
        self.latest_frame = None
        self.latest_timestamp = 0
        self.frame_counter = 0
        
        # 统计信息
        self.stats = {
            'frames_received': 0,
            'frames_discarded': 0,
            'avg_frame_age': 0,
            'max_frame_age': 0,
            'fresh_frame_rate': 0
        }
        
        print(f"[INFO] 增强最新帧系统初始化完成，最大帧年龄: {max_frame_age_ms:.2f}ms")
    
    def add_frame(self, frame: np.ndarray, timestamp: float = None) -> bool:
        """
        添加新帧到系统
        
        Args:
            frame: 图像帧
            timestamp: 帧时间戳，如果为None则使用当前时间
            
        Returns:
            bool: 是否成功添加帧
        """
        if timestamp is None:
            timestamp = time.time() * 1000  # 转换为毫秒
        
        try:
            with self.frame_lock:
                # 检查帧是否过时
                current_time = time.time() * 1000
                frame_age = current_time - timestamp
                
                # 更新统计信息
                self.stats['frames_received'] += 1
                self.stats['avg_frame_age'] = (self.stats['avg_frame_age'] * 0.9 + frame_age * 0.1)
                self.stats['max_frame_age'] = max(self.stats['max_frame_age'], frame_age)
                
                # 如果帧过时，丢弃它
                if frame_age > self.max_frame_age_ms:
                    self.stats['frames_discarded'] += 1
                    print(f"[DEBUG] 丢弃过时帧，年龄: {frame_age:.2f}ms")
                    return False
                
                # 如果新帧比当前帧更新，替换它
                if timestamp > self.latest_timestamp:
                    self.latest_frame = frame.copy()
                    self.latest_timestamp = timestamp
                    self.frame_counter += 1
                    
                    # 计算新鲜帧率
                    if self.stats['frames_received'] > 0:
                        self.stats['fresh_frame_rate'] = (
                            (self.stats['frames_received'] - self.stats['frames_discarded']) / 
                            self.stats['frames_received'] * 100
                        )
                    
                    return True
                else:
                    # 帧时间戳较旧，丢弃
                    self.stats['frames_discarded'] += 1
                    return False
                    
        except Exception as e:
            print(f"[ERROR] 添加帧失败: {e}")
            return False
    
    def get_latest_frame(self, max_age_ms: float = None) -> Optional[Dict[str, Any]]:
        """
        获取最新的有效帧
        
        Args:
            max_age_ms: 最大允许的帧年龄，如果为None则使用默认值
            
        Returns:
            Dict包含frame和metadata，如果没有有效帧则返回None
        """
        if max_age_ms is None:
            max_age_ms = self.max_frame_age_ms
        
        try:
            with self.frame_lock:
                if self.latest_frame is None:
                    return None
                
                current_time = time.time() * 1000
                frame_age = current_time - self.latest_timestamp
                
                # 检查帧是否仍然新鲜
                if frame_age > max_age_ms:
                    print(f"[DEBUG] 最新帧已过时，年龄: {frame_age:.2f}ms > {max_age_ms:.2f}ms")
                    return None
                
                return {
                    'frame': self.latest_frame.copy(),
                    'timestamp': self.latest_timestamp,
                    'age_ms': frame_age,
                    'frame_id': self.frame_counter,
                    'is_fresh': frame_age <= self.max_frame_age_ms
                }
                
        except Exception as e:
            print(f"[ERROR] 获取最新帧失败: {e}")
            return None
    
    def clear_frame_buffer(self):
        """清空帧缓冲区"""
        try:
            with self.frame_lock:
                self.latest_frame = None
                self.latest_timestamp = 0
                self.frame_counter = 0
                print("[DEBUG] 帧缓冲区已清空")
        except Exception as e:
            print(f"[ERROR] 清空帧缓冲区失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        with self.frame_lock:
            return self.stats.copy()
    
    def print_stats(self):
        """打印系统统计信息"""
        stats = self.get_stats()
        print(f"\n📊 增强最新帧系统统计:")
        print(f"   • 接收帧数: {stats['frames_received']}")
        print(f"   • 丢弃帧数: {stats['frames_discarded']}")
        print(f"   • 新鲜帧率: {stats['fresh_frame_rate']:.1f}%")
        print(f"   • 平均帧年龄: {stats['avg_frame_age']:.2f}ms")
        print(f"   • 最大帧年龄: {stats['max_frame_age']:.2f}ms")


class EnhancedMultiThreadedCamera:
    """增强的多线程相机系统"""
    
    def __init__(self, camera_system, max_frame_age_ms: float = 16.67):
        """
        初始化增强的多线程相机系统
        
        Args:
            camera_system: 底层相机系统（high_perf_screenshot或screenshot_optimizer）
            max_frame_age_ms: 最大帧年龄（毫秒）
        """
        self.camera_system = camera_system
        self.frame_system = EnhancedLatestFrameSystem(max_frame_age_ms)
        
        # 线程控制
        self.running = False
        self.capture_thread = None
        self.capture_interval = 1.0 / 120  # 120fps捕获频率
        
        # 性能监控
        self.last_capture_time = 0
        self.capture_fps = 0
        
        print(f"[INFO] 增强多线程相机系统初始化完成")
    
    def start(self):
        """启动相机捕获线程"""
        if self.running:
            print("[WARNING] 相机系统已在运行")
            return
        
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        print("[INFO] 相机捕获线程已启动")
    
    def stop(self):
        """停止相机捕获线程"""
        self.running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        print("[INFO] 相机捕获线程已停止")
    
    def _capture_loop(self):
        """相机捕获循环"""
        print("[INFO] 开始相机捕获循环")
        frame_count = 0
        last_fps_time = time.time()
        
        while self.running:
            try:
                start_time = time.time()
                
                # 从底层系统获取帧
                frame_data = None
                if hasattr(self.camera_system, 'get_latest_frame'):
                    frame_data = self.camera_system.get_latest_frame()
                elif hasattr(self.camera_system, 'get_optimized_frame'):
                    frame = self.camera_system.get_optimized_frame(use_cache=False)
                    if frame is not None:
                        frame_data = {'frame': frame, 'timestamp': time.time() * 1000}
                
                if frame_data and 'frame' in frame_data:
                    # 添加帧到增强系统
                    timestamp = frame_data.get('timestamp', time.time() * 1000)
                    success = self.frame_system.add_frame(frame_data['frame'], timestamp)
                    
                    if success:
                        frame_count += 1
                
                # 计算FPS
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    self.capture_fps = frame_count / (current_time - last_fps_time)
                    frame_count = 0
                    last_fps_time = current_time
                
                # 控制捕获频率
                elapsed = time.time() - start_time
                sleep_time = max(0, self.capture_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                print(f"[ERROR] 相机捕获循环错误: {e}")
                time.sleep(0.01)  # 短暂延迟避免错误循环
    
    def get_latest_frame(self, max_age_ms: float = None) -> Optional[Dict[str, Any]]:
        """
        获取最新的有效帧
        
        Args:
            max_age_ms: 最大允许的帧年龄
            
        Returns:
            包含帧数据和元信息的字典
        """
        return self.frame_system.get_latest_frame(max_age_ms)
    
    def clear_frame_buffer(self):
        """清空帧缓冲区"""
        self.frame_system.clear_frame_buffer()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        frame_stats = self.frame_system.get_stats()
        return {
            'capture_fps': self.capture_fps,
            'frame_stats': frame_stats,
            'is_running': self.running
        }
    
    def print_performance_stats(self):
        """打印性能统计"""
        stats = self.get_performance_stats()
        print(f"\n📊 增强多线程相机系统统计:")
        print(f"   • 捕获FPS: {stats['capture_fps']:.1f}")
        print(f"   • 运行状态: {'运行中' if stats['is_running'] else '已停止'}")
        self.frame_system.print_stats()


def create_enhanced_camera_system(camera_system, max_frame_age_ms: float = 16.67):
    """
    创建增强的相机系统
    
    Args:
        camera_system: 底层相机系统
        max_frame_age_ms: 最大帧年龄（毫秒）
        
    Returns:
        EnhancedMultiThreadedCamera实例
    """
    return EnhancedMultiThreadedCamera(camera_system, max_frame_age_ms)


if __name__ == "__main__":
    # 测试代码
    print("测试增强的最新帧系统...")
    
    # 创建测试帧系统
    frame_system = EnhancedLatestFrameSystem(max_frame_age_ms=50)
    
    # 模拟添加帧
    test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # 添加新鲜帧
    current_time = time.time() * 1000
    frame_system.add_frame(test_frame, current_time)
    
    # 获取最新帧
    latest = frame_system.get_latest_frame()
    if latest:
        print(f"获取到最新帧，年龄: {latest['age_ms']:.2f}ms")
    
    # 添加过时帧
    old_time = current_time - 100  # 100ms前的帧
    frame_system.add_frame(test_frame, old_time)
    
    # 打印统计
    frame_system.print_stats()
    
    print("测试完成！")
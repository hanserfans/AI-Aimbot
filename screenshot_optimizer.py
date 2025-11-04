"""
截图捕获性能优化器
优化截图捕获过程，减少内存拷贝和格式转换开销
"""

import numpy as np
import torch
import torch.nn.functional as F
import cv2
import time
from typing import Optional, Tuple, Any
import threading
import queue

class ScreenshotOptimizer:
    """截图性能优化器"""
    
    def __init__(self, camera, camera_type: str, capture_region=None):
        self.camera = camera
        self.camera_type = camera_type
        self.capture_region = capture_region  # 添加截图区域参数
        self.last_frame = None
        self.frame_cache = None
        self.cache_timestamp = 0
        self.cache_duration = 0.001  # 减少缓存时间到1ms，确保更频繁更新
        
        # 预分配内存缓冲区
        self.buffer_320 = np.empty((320, 320, 3), dtype=np.uint8)
        self.buffer_original = None
        
        # 异步截图相关 - 减小队列大小确保最新帧
        self.async_enabled = False
        self.frame_queue = queue.Queue(maxsize=1)  # 减小队列大小到1，确保最新帧
        self.capture_thread = None
        self.stop_capture = False
        
        # 打印截图区域信息用于调试
        if self.capture_region:
            print(f"[DEBUG] ScreenshotOptimizer 使用截图区域: {self.capture_region}")
        else:
            print("[DEBUG] ScreenshotOptimizer 使用默认截图区域")
        
    def enable_async_capture(self):
        """启用异步截图捕获"""
        if not self.async_enabled:
            self.async_enabled = True
            self.stop_capture = False
            self.capture_thread = threading.Thread(target=self._async_capture_loop, daemon=True)
            self.capture_thread.start()
            print("[INFO] 🚀 异步截图捕获已启用")
    
    def disable_async_capture(self):
        """禁用异步截图捕获"""
        if self.async_enabled:
            self.stop_capture = True
            if self.capture_thread:
                self.capture_thread.join(timeout=1.0)
            self.async_enabled = False
            print("[INFO] ⏹️ 异步截图捕获已禁用")
    
    def _async_capture_loop(self):
        """异步截图捕获循环 - 积极丢弃旧帧确保最新"""
        while not self.stop_capture:
            try:
                frame = self._capture_frame_direct()
                if frame is not None:
                    # 积极清空队列，确保只保留最新帧
                    while not self.frame_queue.empty():
                        try:
                            self.frame_queue.get_nowait()
                        except queue.Empty:
                            break
                    
                    # 放入最新帧
                    try:
                        self.frame_queue.put_nowait((frame, time.time()))
                    except queue.Full:
                        # 如果还是满的，强制清空再放入
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait((frame, time.time()))
                        except (queue.Empty, queue.Full):
                            pass
                
                time.sleep(0.001)  # 1ms延迟，避免CPU占用过高
            except Exception as e:
                print(f"[ERROR] 异步截图捕获错误: {e}")
                time.sleep(0.01)
    
    def _capture_frame_direct(self) -> Optional[np.ndarray]:
        """直接捕获帧，不进行额外处理"""
        try:
            if self.camera_type == "bettercam":
                frame = self.camera.get_latest_frame()
                if frame is not None:
                    # 避免直接GPU分配，先在CPU处理
                    if isinstance(frame, np.ndarray):
                        return frame
                    else:
                        return np.array(frame)
            elif self.camera_type == "dxcam":
                frame = self.camera.get_latest_frame()
                if frame is not None:
                    # 避免直接GPU分配，先在CPU处理
                    if isinstance(frame, np.ndarray):
                        return frame
                    else:
                        return np.array(frame)
            elif self.camera_type == "mss":
                frame = self.camera.get_latest_frame()
                if frame is not None:
                    # mss返回的是numpy数组，直接返回
                    if isinstance(frame, np.ndarray):
                        return frame
                    else:
                        return np.array(frame)
            return None
        except Exception as e:
            print(f"[ERROR] 截图捕获失败: {e}")
            return None
    
    def get_optimized_frame(self, use_cache: bool = True) -> Optional[np.ndarray]:
        """获取优化的帧 - 确保获取最新帧"""
        current_time = time.time()
        
        # 如果启用异步捕获，从队列获取最新帧
        if self.async_enabled:
            latest_frame = None
            frames_discarded = 0
            
            try:
                # 清空队列中的旧帧，只保留最新的一帧
                while True:
                    try:
                        frame, timestamp = self.frame_queue.get_nowait()
                        if latest_frame is not None:
                            frames_discarded += 1
                        latest_frame = frame
                    except queue.Empty:
                        break
                
                # 如果获取到最新帧，返回它
                if latest_frame is not None:
                    if frames_discarded > 0:
                        print(f"[DEBUG] 异步截图：丢弃了 {frames_discarded} 个旧帧，使用最新帧")
                    return latest_frame
                    
            except Exception as e:
                print(f"[ERROR] 异步截图获取最新帧失败: {e}")
            
            # 队列为空，使用缓存或直接捕获
            if use_cache and self.frame_cache is not None:
                cache_age = current_time - self.cache_timestamp
                if cache_age < self.cache_duration:
                    return self.frame_cache
            
            # 缓存过期或无缓存，直接捕获
            frame = self._capture_frame_direct()
            if frame is not None:
                self.frame_cache = frame
                self.cache_timestamp = current_time
            return frame
        
        # 同步模式：检查缓存
        if use_cache and self.frame_cache is not None:
            cache_age = current_time - self.cache_timestamp
            if cache_age < self.cache_duration:
                return self.frame_cache
        
        # 捕获新帧
        frame = self._capture_frame_direct()
        if frame is not None and use_cache:
            self.frame_cache = frame
            self.cache_timestamp = current_time
        
        return frame
    
    def resize_frame_optimized(self, frame: np.ndarray, target_size: Tuple[int, int] = (320, 320)) -> np.ndarray:
        """优化的帧缩放"""
        if frame.shape[:2] == target_size:
            return frame
        
        # 使用预分配的缓冲区
        if target_size == (320, 320):
            cv2.resize(frame, target_size, dst=self.buffer_320, interpolation=cv2.INTER_LINEAR)
            return self.buffer_320.copy()  # 返回副本以避免覆盖
        else:
            return cv2.resize(frame, target_size, interpolation=cv2.INTER_LINEAR)
    
    def apply_mask_optimized(self, frame: np.ndarray, mask_config: dict) -> np.ndarray:
        """优化的掩码应用"""
        if not mask_config.get('enabled', False):
            return frame
        
        mask_side = mask_config.get('side', 'right').lower()
        mask_width = mask_config.get('width', 0)
        mask_height = mask_config.get('height', 0)
        
        if mask_width <= 0 or mask_height <= 0:
            return frame
        
        # 直接在原数组上操作，避免复制
        if mask_side == "right":
            frame[-mask_height:, -mask_width:, :] = 0
        elif mask_side == "left":
            frame[-mask_height:, :mask_width, :] = 0
        
        return frame
    
    def get_performance_stats(self) -> dict:
        """获取性能统计"""
        stats = {
            'camera_type': self.camera_type,
            'async_enabled': self.async_enabled,
            'cache_enabled': self.frame_cache is not None,
            'cache_age': time.time() - self.cache_timestamp if self.frame_cache is not None else 0,
            'queue_size': self.frame_queue.qsize() if self.async_enabled else 0
        }
        return stats
    
    def cleanup(self):
        """清理资源"""
        self.disable_async_capture()
        self.frame_cache = None
        self.buffer_320 = None
        self.buffer_original = None

# 全局实例
_screenshot_optimizer = None

def get_screenshot_optimizer(camera=None, camera_type: str = None, capture_region=None) -> ScreenshotOptimizer:
    """获取截图优化器实例"""
    global _screenshot_optimizer
    if _screenshot_optimizer is None and camera is not None:
        _screenshot_optimizer = ScreenshotOptimizer(camera, camera_type, capture_region)
    return _screenshot_optimizer

def optimize_screenshot_performance():
    """优化截图性能的建议"""
    recommendations = [
        "1. 启用异步截图捕获以减少主线程阻塞",
        "2. 使用帧缓存减少重复截图",
        "3. 预分配内存缓冲区避免动态分配",
        "4. 优化图像缩放和掩码操作",
        "5. 考虑降低截图分辨率或帧率"
    ]
    
    print("[INFO] 📊 截图性能优化建议:")
    for rec in recommendations:
        print(f"  {rec}")
    
    return recommendations
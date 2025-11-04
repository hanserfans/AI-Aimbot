"""
高性能多线程截图系统
充分利用高性能CPU和GPU，实现超高帧率截图和处理
"""

import numpy as np
import torch
import cv2
import time
import threading
import queue
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Optional, Tuple, Dict, List
import psutil
import GPUtil

try:
    import dxcam
    DXCAM_AVAILABLE = True
except ImportError:
    DXCAM_AVAILABLE = False

try:
    import bettercam
    BETTERCAM_AVAILABLE = True
except ImportError:
    BETTERCAM_AVAILABLE = False

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

class HighPerformanceScreenshotSystem:
    """高性能多线程截图系统"""
    
    def __init__(self, 
                 target_fps: int = 500,
                 num_capture_threads: int = None,
                 num_processing_threads: int = None,
                 enable_gpu_acceleration: bool = True,
                 capture_method: str = "auto"):
        """
        初始化高性能截图系统
        
        Args:
            target_fps: 目标FPS
            num_capture_threads: 截图线程数（None=自动检测）
            num_processing_threads: 处理线程数（None=自动检测）
            enable_gpu_acceleration: 启用GPU加速
            capture_method: 截图方法 ("dxcam", "bettercam", "mss", "auto")
        """
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.enable_gpu_acceleration = enable_gpu_acceleration and torch.cuda.is_available()
        
        # 自动检测最优线程数
        cpu_count = psutil.cpu_count(logical=True)
        self.num_capture_threads = num_capture_threads or min(4, max(2, cpu_count // 2))
        self.num_processing_threads = num_processing_threads or min(8, max(4, cpu_count - 2))
        
        print(f"[INFO] 🚀 高性能截图系统初始化")
        print(f"   • 目标FPS: {target_fps}")
        print(f"   • 截图线程数: {self.num_capture_threads}")
        print(f"   • 处理线程数: {self.num_processing_threads}")
        print(f"   • GPU加速: {self.enable_gpu_acceleration}")
        
        # 固定使用MSS方法，避免多线程切换问题
        self.capture_method = "mss"
        print(f"   • 截图方法: {self.capture_method} (固定使用，避免多线程切换)")
        
        # 初始化MSS截图器
        self.camera = self._initialize_mss_camera()
        
        # 线程池和队列
        self.capture_executor = ThreadPoolExecutor(max_workers=self.num_capture_threads)
        self.processing_executor = ThreadPoolExecutor(max_workers=self.num_processing_threads)
        
        # 帧队列（减小队列大小以确保最新帧）
        self.frame_queues = [queue.Queue(maxsize=1) for _ in range(self.num_capture_threads)]
        self.processed_queue = queue.Queue(maxsize=2)  # 减小处理队列大小
        
        # 控制变量
        self.running = False
        self.capture_threads = []
        self.processing_threads = []
        
        # 性能统计
        self.stats = {
            'frames_captured': 0,
            'frames_processed': 0,
            'capture_fps': 0.0,
            'processing_fps': 0.0,
            'avg_capture_time': 0.0,
            'avg_processing_time': 0.0,
            'queue_sizes': []
        }
        
        # GPU相关
        if self.enable_gpu_acceleration:
            self.device = torch.device('cuda')
            self.stream = torch.cuda.Stream()
            # 预分配GPU内存
            self._preallocate_gpu_memory()
        
        print(f"[SUCCESS] ✅ 高性能截图系统初始化完成")
    
    def _select_capture_method(self, method: str) -> str:
        """选择最佳截图方法"""
        if method != "auto":
            return method
        
        # 按性能优先级选择
        if DXCAM_AVAILABLE:
            return "dxcam"
        elif BETTERCAM_AVAILABLE:
            return "bettercam"
        elif MSS_AVAILABLE:
            return "mss"
        else:
            raise RuntimeError("没有可用的截图库")
    
    def _initialize_camera(self):
        """初始化截图器"""
        try:
            if self.capture_method == "dxcam":
                camera = dxcam.create(output_color="BGR")
                if camera:
                    print("[INFO] ✅ DXCam 截图器初始化成功")
                    return camera
            
            elif self.capture_method == "bettercam":
                # 使用BetterCam包装器来解决is_capturing属性缺失问题
                class BetterCamWrapper:
                    def __init__(self):
                        self.is_capturing = False
                        self._camera = None
                    
                    def start(self, fps=60, video_mode=True):
                        try:
                            self._camera = bettercam.create(output_color="BGR")
                            if self._camera is not None:
                                self._camera.start(fps, video_mode=video_mode)
                                self.is_capturing = True
                                return True
                            return False
                        except Exception as e:
                            print(f"[ERROR] BetterCam启动失败: {e}")
                            self.is_capturing = False
                            return False
                    
                    def get_latest_frame(self):
                        if not self.is_capturing or self._camera is None:
                            return None
                        try:
                            return self._camera.get_latest_frame()
                        except Exception as e:
                            return None
                    
                    def grab(self, region=None):
                        if not self.is_capturing or self._camera is None:
                            return None
                        try:
                            if region:
                                return self._camera.grab(region)
                            else:
                                return self._camera.grab()
                        except Exception as e:
                            return None
                    
                    def stop(self):
                        self.is_capturing = False
                        if self._camera is not None:
                            try:
                                # 避免调用有问题的stop方法，直接设置为None
                                self._camera = None
                            except Exception as e:
                                self._camera = None
                    
                    def release(self):
                        self.stop()
                
                camera = BetterCamWrapper()
                if camera.start():
                    print("[INFO] ✅ BetterCam 截图器初始化成功")
                    return camera
            
            elif self.capture_method == "mss":
                camera = mss.mss()
                print("[INFO] ✅ MSS 截图器初始化成功")
                return camera
            
        except Exception as e:
            print(f"[ERROR] 截图器初始化失败: {e}")
        
        return None
    
    def _initialize_mss_camera(self):
        """初始化MSS截图器"""
        try:
            import mss
            camera = mss.mss()
            print("[INFO] ✅ MSS 截图器初始化成功")
            return camera
        except Exception as e:
            print(f"[ERROR] MSS截图器初始化失败: {e}")
            return None
    
    def _preallocate_gpu_memory(self):
        """预分配GPU内存"""
        try:
            # 预分配常用尺寸的GPU张量
            self.gpu_buffers = {
                (640, 640): torch.empty((640, 640, 3), dtype=torch.uint8, device=self.device),
                (320, 320): torch.empty((320, 320, 3), dtype=torch.uint8, device=self.device),
                (1920, 1080): torch.empty((1920, 1080, 3), dtype=torch.uint8, device=self.device),
            }
            print("[INFO] ✅ GPU内存预分配完成")
        except Exception as e:
            print(f"[WARNING] GPU内存预分配失败: {e}")
            self.gpu_buffers = {}
    
    def start(self, region: Tuple[int, int, int, int] = None):
        """启动高性能截图系统"""
        if self.running:
            return
        
        self.running = True
        self.capture_region = region
        
        print(f"[INFO] 🚀 启动高性能截图系统")
        print(f"   • 截图区域: {region}")
        
        # 启动截图线程
        for i in range(self.num_capture_threads):
            thread = threading.Thread(
                target=self._capture_worker,
                args=(i,),
                daemon=True,
                name=f"CaptureThread-{i}"
            )
            thread.start()
            self.capture_threads.append(thread)
        
        # 启动处理线程
        for i in range(self.num_processing_threads):
            thread = threading.Thread(
                target=self._processing_worker,
                args=(i,),
                daemon=True,
                name=f"ProcessingThread-{i}"
            )
            thread.start()
            self.processing_threads.append(thread)
        
        # 启动统计线程
        stats_thread = threading.Thread(
            target=self._stats_worker,
            daemon=True,
            name="StatsThread"
        )
        stats_thread.start()
        
        print(f"[SUCCESS] ✅ 高性能截图系统已启动")
    
    def stop(self):
        """停止截图系统"""
        if not self.running:
            return
        
        print("[INFO] 🛑 停止高性能截图系统...")
        self.running = False
        
        # 等待线程结束
        for thread in self.capture_threads + self.processing_threads:
            thread.join(timeout=1.0)
        
        # 安全清理截图器
        if hasattr(self, 'camera') and self.camera is not None:
            try:
                if self.capture_method == "bettercam":
                    # 安全清理 bettercam - 避免调用有问题的stop方法
                    if hasattr(self.camera, 'release'):
                        self.camera.release()
                    # 直接设置为None，避免调用stop方法
                    self.camera = None
                elif self.capture_method == "dxcam":
                    # 清理 dxcam
                    if hasattr(self.camera, 'release'):
                        self.camera.release()
                elif self.capture_method == "mss":
                    # MSS 不需要特殊清理
                    pass
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 截图器清理时出现错误: {e}")
                # 强制设置为None
                self.camera = None
        
        # 清空队列
        for q in self.frame_queues:
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break
        
        while not self.processed_queue.empty():
            try:
                self.processed_queue.get_nowait()
            except queue.Empty:
                break
        
        print("[SUCCESS] ✅ 高性能截图系统已停止")
    
    def _capture_worker(self, worker_id: int):
        """截图工作线程"""
        frame_queue = self.frame_queues[worker_id]
        last_capture_time = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # 控制截图频率
                if current_time - last_capture_time < self.frame_interval:
                    time.sleep(0.0001)  # 0.1ms微延迟
                    continue
                
                capture_start = time.time()
                
                # 执行截图
                frame = self._capture_frame()
                
                if frame is not None:
                    capture_time = time.time() - capture_start
                    
                    # 非阻塞放入队列
                    try:
                        frame_queue.put_nowait({
                            'frame': frame,
                            'timestamp': current_time,
                            'capture_time': capture_time,
                            'worker_id': worker_id
                        })
                        self.stats['frames_captured'] += 1
                    except queue.Full:
                        # 队列满时丢弃最旧的帧
                        try:
                            frame_queue.get_nowait()
                            frame_queue.put_nowait({
                                'frame': frame,
                                'timestamp': current_time,
                                'capture_time': capture_time,
                                'worker_id': worker_id
                            })
                        except queue.Empty:
                            pass
                
                last_capture_time = current_time
                
            except Exception as e:
                print(f"[ERROR] 截图线程 {worker_id} 错误: {e}")
                time.sleep(0.001)
    
    def _processing_worker(self, worker_id: int):
        """处理工作线程"""
        queue_index = 0
        
        while self.running:
            try:
                # 轮询所有截图队列
                frame_data = None
                for i in range(len(self.frame_queues)):
                    queue_idx = (queue_index + i) % len(self.frame_queues)
                    try:
                        frame_data = self.frame_queues[queue_idx].get_nowait()
                        queue_index = (queue_idx + 1) % len(self.frame_queues)
                        break
                    except queue.Empty:
                        continue
                
                if frame_data is None:
                    time.sleep(0.0001)  # 0.1ms微延迟
                    continue
                
                processing_start = time.time()
                
                # 处理帧
                processed_frame = self._process_frame(frame_data['frame'])
                
                if processed_frame is not None:
                    processing_time = time.time() - processing_start
                    
                    # 放入处理完成队列
                    try:
                        self.processed_queue.put_nowait({
                            'frame': processed_frame,
                            'original_frame': frame_data['frame'],
                            'timestamp': frame_data['timestamp'],
                            'capture_time': frame_data['capture_time'],
                            'processing_time': processing_time,
                            'worker_id': worker_id
                        })
                        self.stats['frames_processed'] += 1
                    except queue.Full:
                        # 队列满时丢弃最旧的帧
                        try:
                            self.processed_queue.get_nowait()
                            self.processed_queue.put_nowait({
                                'frame': processed_frame,
                                'original_frame': frame_data['frame'],
                                'timestamp': frame_data['timestamp'],
                                'capture_time': frame_data['capture_time'],
                                'processing_time': processing_time,
                                'worker_id': worker_id
                            })
                        except queue.Empty:
                            pass
                
            except Exception as e:
                print(f"[ERROR] 处理线程 {worker_id} 错误: {e}")
                time.sleep(0.001)
    
    def _capture_frame(self) -> Optional[np.ndarray]:
        """捕获单帧图像，固定使用MSS方法确保线程安全"""
        try:
            return self._try_capture_with_mss()
        except Exception as e:
            print(f"[ERROR] 截图失败: {e}")
            return None
    
    def _try_capture_with_mss(self) -> Optional[np.ndarray]:
        """固定使用MSS方法截图，避免频繁切换和区域转换"""
        try:
            import mss
            if not hasattr(self, '_mss_camera'):
                self._mss_camera = mss.mss()
            
            if self.capture_region:
                # 预计算MSS格式的截图区域，避免重复转换
                if not hasattr(self, '_mss_monitor_cache'):
                    left, top, right, bottom = self.capture_region
                    self._mss_monitor_cache = {
                        "left": left,
                        "top": top,
                        "width": right - left,
                        "height": bottom - top
                    }
                    print(f"[MSS_INIT] 预计算截图区域: {self._mss_monitor_cache}")
                
                monitor = self._mss_monitor_cache
            else:
                monitor = self._mss_camera.monitors[1]  # 主显示器
            
            screenshot = self._mss_camera.grab(monitor)
            return np.array(screenshot)[:, :, :3]  # 移除alpha通道
        except ImportError:
            print("[ERROR] MSS库未安装")
            return None
        except Exception as e:
            print(f"[ERROR] MSS截图失败: {e}")
            return None
    
    def _try_capture_with_method(self, method: str) -> Optional[np.ndarray]:
        """尝试使用指定方法截图"""
        try:
            if method == "dxcam" and hasattr(self, 'camera') and self.camera:
                if self.capture_region:
                    frame = self.camera.grab(self.capture_region)
                else:
                    frame = self.camera.grab()
                return np.array(frame) if frame is not None else None
            
            elif method == "bettercam":
                # 使用BetterCam包装器
                try:
                    if not hasattr(self, '_bettercam_camera'):
                        # 创建BetterCam包装器
                        class BetterCamWrapper:
                            def __init__(self):
                                self.is_capturing = False
                                self._camera = None
                            
                            def start(self, fps=60, video_mode=True):
                                try:
                                    import bettercam
                                    self._camera = bettercam.create(output_color="BGR")
                                    if self._camera is not None:
                                        self._camera.start(fps, video_mode=video_mode)
                                        self.is_capturing = True
                                        return True
                                    return False
                                except Exception as e:
                                    self.is_capturing = False
                                    return False
                            
                            def grab(self, region=None):
                                if not self.is_capturing or self._camera is None:
                                    return None
                                try:
                                    if region:
                                        return self._camera.grab(region)
                                    else:
                                        return self._camera.grab()
                                except Exception as e:
                                    return None
                        
                        self._bettercam_camera = BetterCamWrapper()
                        self._bettercam_camera.start()
                    
                    if self.capture_region:
                        frame = self._bettercam_camera.grab(self.capture_region)
                    else:
                        frame = self._bettercam_camera.grab()
                    return np.array(frame) if frame is not None else None
                except ImportError:
                    pass
            
        except Exception as e:
            print(f"[ERROR] {method} 截图失败: {e}")
        
        return None
            
    def _try_capture_with_mss(self):
        """使用MSS进行截图，确保线程安全"""
        try:
            import mss
            import threading
            
            # 为每个线程创建独立的MSS实例
            thread_id = threading.current_thread().ident
            mss_attr_name = f'_mss_camera_{thread_id}'
            
            if not hasattr(self, mss_attr_name):
                # 为当前线程创建新的MSS实例
                setattr(self, mss_attr_name, mss.mss())
                print(f"[MSS_THREAD] 为线程 {thread_id} 创建MSS实例")
            
            mss_camera = getattr(self, mss_attr_name)
            
            if self.capture_region:
                # 预计算截图区域，避免重复转换
                if not hasattr(self, '_mss_monitor_cache'):
                    left, top, right, bottom = self.capture_region
                    self._mss_monitor_cache = {
                        "left": left,
                        "top": top,
                        "width": right - left,
                        "height": bottom - top
                    }
                monitor = self._mss_monitor_cache
            else:
                monitor = mss_camera.monitors[1]  # 主显示器
            
            screenshot = mss_camera.grab(monitor)
            return np.array(screenshot)[:, :, :3]  # 移除alpha通道
            
        except Exception as e:
            print(f"[ERROR] MSS截图失败: {e}")
            return None
    
    def _switch_capture_method(self, new_method: str):
        """切换截图方法"""
        try:
            old_method = self.capture_method
            self.capture_method = new_method
            
            # 重新初始化相机
            if new_method == "dxcam":
                import dxcam
                self.camera = dxcam.create()
            elif new_method == "bettercam":
                import bettercam
                self.camera = bettercam.create()
            elif new_method == "mss":
                import mss
                self.camera = mss.mss()
            
            print(f"[SUCCESS] 截图方法已从 {old_method} 切换到 {new_method}")
        except Exception as e:
            print(f"[ERROR] 切换截图方法失败: {e}")
            self.capture_method = old_method  # 恢复原方法
    
    def _process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """处理帧（缩放、格式转换等）"""
        try:
            if self.enable_gpu_acceleration:
                return self._process_frame_gpu(frame)
            else:
                return self._process_frame_cpu(frame)
        except Exception as e:
            print(f"[ERROR] 帧处理失败: {e}")
            return None
    
    def _process_frame_gpu(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """GPU加速帧处理"""
        try:
            with torch.cuda.stream(self.stream):
                # 转换为GPU张量
                frame_tensor = torch.from_numpy(frame).to(self.device, non_blocking=True)
                
                # 缩放到320x320
                if frame.shape[:2] != (320, 320):
                    frame_tensor = frame_tensor.permute(2, 0, 1).float()  # HWC -> CHW
                    frame_tensor = torch.nn.functional.interpolate(
                        frame_tensor.unsqueeze(0),
                        size=(320, 320),
                        mode='bilinear',
                        align_corners=False
                    )
                    frame_tensor = frame_tensor.squeeze(0).permute(1, 2, 0)  # CHW -> HWC
                
                # 归一化
                frame_tensor = frame_tensor / 255.0
                
                # 同步并返回CPU数组
                torch.cuda.synchronize()
                return frame_tensor.cpu().numpy().astype(np.float32)
        
        except Exception as e:
            print(f"[ERROR] GPU帧处理失败: {e}")
            return self._process_frame_cpu(frame)
    
    def _process_frame_cpu(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """CPU帧处理"""
        try:
            # 缩放到320x320
            if frame.shape[:2] != (320, 320):
                frame = cv2.resize(frame, (320, 320))
            
            # 归一化
            frame = frame.astype(np.float32) / 255.0
            
            return frame
        
        except Exception as e:
            print(f"[ERROR] CPU帧处理失败: {e}")
            return None
    
    def _stats_worker(self):
        """统计工作线程"""
        last_stats_time = time.time()
        last_captured = 0
        last_processed = 0
        
        while self.running:
            try:
                time.sleep(1.0)  # 每秒更新统计
                
                current_time = time.time()
                time_diff = current_time - last_stats_time
                
                # 计算FPS
                captured_diff = self.stats['frames_captured'] - last_captured
                processed_diff = self.stats['frames_processed'] - last_processed
                
                self.stats['capture_fps'] = captured_diff / time_diff
                self.stats['processing_fps'] = processed_diff / time_diff
                
                # 更新队列大小
                self.stats['queue_sizes'] = [q.qsize() for q in self.frame_queues]
                self.stats['processed_queue_size'] = self.processed_queue.qsize()
                
                # 更新记录
                last_stats_time = current_time
                last_captured = self.stats['frames_captured']
                last_processed = self.stats['frames_processed']
                
            except Exception as e:
                print(f"[ERROR] 统计线程错误: {e}")
    
    def get_latest_frame(self) -> Optional[Dict]:
        """获取下一个待处理的帧 - 顺序处理每一帧，不丢弃"""
        try:
            # 获取队列中的下一帧，不丢弃任何帧
            frame = self.processed_queue.get_nowait()
            return frame
        except queue.Empty:
            # 队列为空，返回None
            return None
        except Exception as e:
            print(f"[ERROR] 获取帧失败: {e}")
            return None
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        return self.stats.copy()
    
    def print_performance_stats(self):
        """打印性能统计"""
        stats = self.get_performance_stats()
        print(f"\n📊 高性能截图系统统计:")
        print(f"   • 截图FPS: {stats['capture_fps']:.1f}")
        print(f"   • 处理FPS: {stats['processing_fps']:.1f}")
        print(f"   • 总截图数: {stats['frames_captured']}")
        print(f"   • 总处理数: {stats['frames_processed']}")
        print(f"   • 队列大小: {stats.get('queue_sizes', [])}")
        print(f"   • 处理队列: {stats.get('processed_queue_size', 0)}")
    
    def cleanup(self):
        """清理资源"""
        self.stop()
        
        if hasattr(self, 'capture_executor'):
            self.capture_executor.shutdown(wait=False)
        
        if hasattr(self, 'processing_executor'):
            self.processing_executor.shutdown(wait=False)
        
        if self.enable_gpu_acceleration:
            try:
                torch.cuda.empty_cache()
            except:
                pass
        
        print("[INFO] ✅ 高性能截图系统资源已清理")

def create_high_performance_screenshot_system(target_fps: int = 500, **kwargs):
    """创建高性能截图系统"""
    return HighPerformanceScreenshotSystem(target_fps=target_fps, **kwargs)

def optimize_system_for_high_fps():
    """优化系统以支持高FPS"""
    recommendations = []
    
    # 检查CPU
    cpu_count = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    recommendations.append(f"CPU核心数: {cpu_count}")
    if cpu_freq:
        recommendations.append(f"CPU频率: {cpu_freq.current:.0f}MHz")
    
    # 检查内存
    memory = psutil.virtual_memory()
    recommendations.append(f"可用内存: {memory.available / (1024**3):.1f}GB")
    
    # 检查GPU
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        for i in range(gpu_count):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            recommendations.append(f"GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)")
    
    print("[INFO] 🔧 系统性能分析:")
    for rec in recommendations:
        print(f"   • {rec}")
    
    return recommendations

if __name__ == "__main__":
    # 测试高性能截图系统
    optimize_system_for_high_fps()
    
    system = create_high_performance_screenshot_system(target_fps=500)
    
    try:
        system.start()
        
        print("[INFO] 测试运行30秒...")
        start_time = time.time()
        
        while time.time() - start_time < 30:
            frame_data = system.get_latest_frame()
            if frame_data:
                print(f"获取到帧: {frame_data['timestamp']:.3f}")
            
            time.sleep(0.1)
        
        system.print_performance_stats()
        
    finally:
        system.cleanup()
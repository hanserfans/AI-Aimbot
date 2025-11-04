"""
增强高性能截图系统 - 集成游戏窗口选择功能
基于 gameSelection.py 的窗口选择逻辑，提供完整的游戏窗口检测和截图功能
"""

import numpy as np
import torch
import cv2
import time
import threading
import queue
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple, Dict, List, Union
import psutil
import pygetwindow
import sys
import os

# 截图库导入
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

# 配置导入
try:
    from config import screenShotHeight, screenShotWidth, autoSelectWindow, preferredWindowTitle, customGameKeywords
    CONFIG_AVAILABLE = True
except ImportError:
    # 默认配置
    screenShotHeight = 320
    screenShotWidth = 320
    autoSelectWindow = True
    preferredWindowTitle = ""
    customGameKeywords = []
    CONFIG_AVAILABLE = False
    print("[WARNING] config.py 不可用，使用默认配置")

# 增强检测配置
try:
    from enhanced_detection_config import get_enhanced_detection_config
    ENHANCED_DETECTION_AVAILABLE = True
except ImportError:
    ENHANCED_DETECTION_AVAILABLE = False

class BetterCamWrapper:
    """BetterCam 包装器，解决接口兼容性问题"""
    
    def __init__(self, region):
        self.region = region
        self.is_capturing = False
        self._camera = None
    
    def start(self, fps=60, video_mode=True):
        try:
            self._camera = bettercam.create(region=self.region, output_color="BGRA", max_buffer_len=512)
            if self._camera is not None:
                self._camera.start(fps, video_mode=video_mode)
                self.is_capturing = True
                return True
            else:
                raise Exception("bettercam.create() 返回 None")
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
            print(f"[ERROR] BetterCam获取帧失败: {e}")
            return None
    
    def stop(self):
        self.is_capturing = False
        if self._camera is not None:
            try:
                self._camera = None
            except Exception as e:
                print(f"[DEBUG] BetterCam停止时出现错误: {e}")
                self._camera = None
    
    def release(self):
        self.stop()

class MSSCamera:
    """MSS 相机包装器"""
    
    def __init__(self, region):
        self.region = {"top": region[1], "left": region[0], 
                      "width": region[2] - region[0], "height": region[3] - region[1]}
        self.is_capturing = False
        import threading
        self._local = threading.local()
    
    def _get_sct(self):
        """获取线程本地的mss实例"""
        if not hasattr(self._local, 'sct'):
            self._local.sct = mss.mss()
        return self._local.sct
    
    def start(self, fps=60, video_mode=True):
        self.is_capturing = True
        return True
    
    def get_latest_frame(self):
        if not self.is_capturing:
            return None
        try:
            sct = self._get_sct()
            screenshot = sct.grab(self.region)
            frame = np.array(screenshot)
            return frame
        except Exception as e:
            print(f"[ERROR] mss截图失败: {e}")
            return None
    
    def stop(self):
        self.is_capturing = False
        if hasattr(self._local, 'sct'):
            try:
                self._local.sct.close()
            except:
                pass
            delattr(self._local, 'sct')
    
    def release(self):
        self.stop()

class EnhancedScreenshotSystemWithWindowSelection:
    """增强高性能截图系统 - 集成游戏窗口选择"""
    
    def __init__(self, 
                 target_fps: int = 300,
                 num_capture_threads: int = None,
                 num_processing_threads: int = None,
                 enable_gpu_acceleration: bool = True,
                 capture_method: str = "auto",
                 auto_select_window: bool = True,
                 preferred_window_title: str = ""):
        """
        初始化增强截图系统
        
        Args:
            target_fps: 目标FPS
            num_capture_threads: 截图线程数
            num_processing_threads: 处理线程数
            enable_gpu_acceleration: 启用GPU加速
            capture_method: 截图方法 ("dxcam", "bettercam", "mss", "auto")
            auto_select_window: 自动选择游戏窗口
            preferred_window_title: 首选窗口标题
        """
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.enable_gpu_acceleration = enable_gpu_acceleration and torch.cuda.is_available()
        self.auto_select_window = auto_select_window
        self.preferred_window_title = preferred_window_title or preferredWindowTitle
        
        # 自动检测最优线程数
        cpu_count = psutil.cpu_count(logical=True)
        self.num_capture_threads = num_capture_threads or min(4, max(2, cpu_count // 2))
        self.num_processing_threads = num_processing_threads or min(8, max(4, cpu_count - 2))
        
        print(f"[INFO] 🚀 增强高性能截图系统初始化")
        print(f"   • 目标FPS: {target_fps}")
        print(f"   • 截图线程数: {self.num_capture_threads}")
        print(f"   • 处理线程数: {self.num_processing_threads}")
        print(f"   • GPU加速: {self.enable_gpu_acceleration}")
        print(f"   • 自动窗口选择: {self.auto_select_window}")
        
        # 游戏窗口选择和截图区域初始化
        self.game_window = None
        self.capture_region = None
        self.center_x = 0
        self.center_y = 0
        self.camera = None
        self.camera_type = None
        
        # 选择截图方法
        self.capture_method = self._select_capture_method(capture_method)
        print(f"   • 截图方法: {self.capture_method}")
        
        # 线程池和队列
        self.capture_executor = ThreadPoolExecutor(max_workers=self.num_capture_threads)
        self.processing_executor = ThreadPoolExecutor(max_workers=self.num_processing_threads)
        
        # 帧队列
        self.frame_queues = [queue.Queue(maxsize=3) for _ in range(self.num_capture_threads)]
        self.processed_queue = queue.Queue(maxsize=5)
        
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
        
        # GPU内存预分配
        if self.enable_gpu_acceleration:
            self._preallocate_gpu_memory()
        
        print(f"[SUCCESS] ✅ 增强高性能截图系统初始化完成")
    
    def _select_capture_method(self, method: str) -> str:
        """选择最佳截图方法"""
        if method != "auto":
            return method
        
        # 自动选择优先级: dxcam > bettercam > mss
        if DXCAM_AVAILABLE:
            return "dxcam"
        elif BETTERCAM_AVAILABLE:
            return "bettercam"
        elif MSS_AVAILABLE:
            return "mss"
        else:
            raise RuntimeError("没有可用的截图库")
    
    def select_game_window(self) -> bool:
        """选择游戏窗口并初始化截图区域"""
        print(f"\n[INFO] 🎮 开始游戏窗口选择...")
        
        try:
            # 获取所有窗口
            video_game_windows = pygetwindow.getAllWindows()
            print("=== 所有窗口 ===")
            for index, window in enumerate(video_game_windows):
                if window.title != "":
                    print(f"[{index}]: {window.title}")
            
            # 检查是否为GUI模式
            is_gui_mode = (
                os.environ.get('AIMBOT_GUI_MODE') == '1' or
                not sys.stdin.isatty() or
                self.auto_select_window
            )
            
            if is_gui_mode and self.auto_select_window:
                # 自动选择游戏窗口
                print("[AUTO] GUI模式检测到，正在自动选择游戏窗口...")
                self.game_window = self._auto_select_game_window(video_game_windows)
                if self.game_window is None:
                    print("[ERROR] 无法自动选择游戏窗口，请手动启动游戏后重试")
                    return False
                print(f"[SUCCESS] 自动选择窗口: {self.game_window.title}")
            else:
                # 手动选择
                try:
                    user_input = int(input("请输入要选择的窗口编号: "))
                    self.game_window = video_game_windows[user_input]
                except (ValueError, IndexError):
                    print("[ERROR] 无效的窗口编号")
                    return False
            
            # 激活窗口
            if not self._activate_game_window():
                return False
            
            # 计算截图区域
            self._calculate_capture_region()
            
            # 初始化相机
            return self._initialize_camera()
            
        except Exception as e:
            print(f"[ERROR] 游戏窗口选择失败: {e}")
            return False
    
    def _auto_select_game_window(self, windows):
        """自动选择游戏窗口"""
        # 首先检查是否有指定的首选窗口
        if self.preferred_window_title:
            print(f"[INFO] 搜索指定窗口: {self.preferred_window_title}")
            for window in windows:
                if self.preferred_window_title.lower() in window.title.lower():
                    print(f"[SUCCESS] 找到指定窗口: {window.title}")
                    return window
            print("[WARNING] 未找到指定窗口，使用自动检测...")
        
        # 常见游戏窗口关键词（按优先级排序）
        game_keywords = [
            # FPS游戏
            "VALORANT", "Counter-Strike", "CS:GO", "CS2", "Apex Legends", 
            "Call of Duty", "Overwatch", "Rainbow Six", "Battlefield",
            # 其他游戏
            "Fortnite", "PUBG", "Warzone", "Destiny", "Halo", "Titanfall",
            "Rust", "Escape from Tarkov", "Hunt: Showdown", "Paladins",
            # 中文游戏
            "无畏契约", "穿越火线", "和平精英", "绝地求生"
        ]
        
        # 添加自定义游戏关键词
        if customGameKeywords:
            game_keywords = customGameKeywords + game_keywords
        
        # 排除的窗口关键词
        exclude_keywords = [
            "AI-Aimbot", "Trae", "Visual Studio", "PyCharm", "Notepad",
            "Explorer", "Chrome", "Firefox", "Edge", "Discord", "QQ", "WeChat",
            "Steam", "Epic Games", "Battle.net", "Origin", "Uplay", "WeGame",
            "Task Manager", "Control Panel", "Settings", "Program Manager",
            "Windows", "Microsoft", "输入体验"
        ]
        
        valid_windows = []
        
        # 过滤有效窗口
        for window in windows:
            if window.title == "":
                continue
                
            # 检查是否包含排除关键词
            should_exclude = False
            for exclude in exclude_keywords:
                if exclude.lower() in window.title.lower():
                    should_exclude = True
                    break
            
            if not should_exclude:
                valid_windows.append(window)
        
        # 优先选择包含游戏关键词的窗口
        for keyword in game_keywords:
            for window in valid_windows:
                if keyword.lower() in window.title.lower():
                    return window
        
        # 如果没有找到游戏窗口，选择第一个有效窗口
        for window in valid_windows:
            if (window.width > 800 and window.height > 600 and 
                window.left >= 0 and window.top >= 0):
                return window
        
        return None
    
    def _activate_game_window(self) -> bool:
        """激活游戏窗口"""
        activation_retries = 30
        activation_success = False
        
        while activation_retries > 0:
            try:
                self.game_window.activate()
                activation_success = True
                break
            except pygetwindow.PyGetWindowException as we:
                print(f"[WARNING] 窗口激活失败: {we}")
                print("[INFO] 正在重试... (请手动切换到游戏窗口)")
            except Exception as e:
                print(f"[ERROR] 窗口激活失败: {e}")
                print("[INFO] 相关限制说明: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow")
                activation_success = False
                activation_retries = 0
                break
            
            time.sleep(3.0)
            activation_retries -= 1
        
        if activation_success:
            print("[SUCCESS] ✅ 游戏窗口激活成功")
            return True
        else:
            print("[ERROR] ❌ 游戏窗口激活失败")
            return False
    
    def _calculate_capture_region(self):
        """计算截图区域"""
        # 使用增强检测配置计算截取区域
        if ENHANCED_DETECTION_AVAILABLE:
            enhanced_config = get_enhanced_detection_config()
            left, top, right, bottom = enhanced_config.get_capture_region(
                self.game_window.left, 
                self.game_window.top, 
                self.game_window.width, 
                self.game_window.height
            )
            
            # 更新截取区域尺寸
            actual_capture_width = enhanced_config.CAPTURE_SIZE
            actual_capture_height = enhanced_config.CAPTURE_SIZE
            
            print(f"[ENHANCED_DETECTION] 使用增强检测模式")
            print(f"[ENHANCED_DETECTION] 截取区域: {actual_capture_width}x{actual_capture_height}")
            print(f"[ENHANCED_DETECTION] 模型输入: {enhanced_config.MODEL_INPUT_SIZE}x{enhanced_config.MODEL_INPUT_SIZE}")
        else:
            # 原始截取逻辑（备用）
            left = ((self.game_window.left + self.game_window.right) // 2) - (screenShotWidth // 2)
            top = self.game_window.top + (self.game_window.height - screenShotHeight) // 2 + 18
            right, bottom = left + screenShotWidth, top + screenShotHeight
            actual_capture_width = screenShotWidth
            actual_capture_height = screenShotHeight
            print(f"[STANDARD_DETECTION] 使用标准检测模式: {actual_capture_width}x{actual_capture_height}")

        self.capture_region = (left, top, right, bottom)
        
        # 计算中心点
        self.center_x = actual_capture_width // 2
        self.center_y = actual_capture_height // 2
        
        print(f"[INFO] 截图区域: {self.capture_region}")
        print(f"[INFO] 中心点: ({self.center_x}, {self.center_y})")
    
    def _initialize_camera(self) -> bool:
        """初始化相机"""
        print(f"[INFO] 🎥 初始化相机 ({self.capture_method})...")
        
        try:
            if self.capture_method == "bettercam" and BETTERCAM_AVAILABLE:
                self.camera = self._init_bettercam()
                self.camera_type = "bettercam"
            elif self.capture_method == "dxcam" and DXCAM_AVAILABLE:
                self.camera = self._init_dxcam()
                self.camera_type = "dxcam"
            elif self.capture_method == "mss" and MSS_AVAILABLE:
                self.camera = self._init_mss()
                self.camera_type = "mss"
            else:
                # 自动回退
                return self._init_fallback_camera()
            
            if self.camera is not None:
                print(f"[SUCCESS] ✅ {self.camera_type} 相机初始化成功")
                return True
            else:
                return self._init_fallback_camera()
                
        except Exception as e:
            print(f"[ERROR] 相机初始化失败: {e}")
            return self._init_fallback_camera()
    
    def _init_bettercam(self):
        """初始化 BetterCam"""
        try:
            # 清理默认实例
            try:
                temp_camera = bettercam.create()
                if temp_camera:
                    del temp_camera
            except:
                pass
            
            camera = BetterCamWrapper(self.capture_region)
            if camera.start(self.target_fps, video_mode=True):
                return camera
            else:
                return None
        except Exception as e:
            print(f"[ERROR] BetterCam初始化失败: {e}")
            return None
    
    def _init_dxcam(self):
        """初始化 DXCam"""
        try:
            # 清理默认实例
            try:
                temp_camera = dxcam.create()
                if temp_camera:
                    temp_camera.release()
                    del temp_camera
            except:
                pass
            
            camera = dxcam.create(device_idx=0, region=self.capture_region, max_buffer_len=512)
            if camera is not None:
                camera.start(self.target_fps, video_mode=True)
                return camera
            else:
                return None
        except Exception as e:
            print(f"[ERROR] DXCam初始化失败: {e}")
            return None
    
    def _init_mss(self):
        """初始化 MSS"""
        try:
            camera = MSSCamera(self.capture_region)
            camera.start(self.target_fps, video_mode=True)
            return camera
        except Exception as e:
            print(f"[ERROR] MSS初始化失败: {e}")
            return None
    
    def _init_fallback_camera(self) -> bool:
        """初始化备选相机"""
        print("[INFO] 尝试备选相机方案...")
        
        # 尝试顺序: dxcam -> bettercam -> mss
        fallback_methods = []
        if DXCAM_AVAILABLE and self.capture_method != "dxcam":
            fallback_methods.append("dxcam")
        if BETTERCAM_AVAILABLE and self.capture_method != "bettercam":
            fallback_methods.append("bettercam")
        if MSS_AVAILABLE and self.capture_method != "mss":
            fallback_methods.append("mss")
        
        for method in fallback_methods:
            try:
                print(f"[INFO] 尝试 {method}...")
                if method == "dxcam":
                    self.camera = self._init_dxcam()
                elif method == "bettercam":
                    self.camera = self._init_bettercam()
                elif method == "mss":
                    self.camera = self._init_mss()
                
                if self.camera is not None:
                    self.camera_type = method
                    print(f"[SUCCESS] ✅ 备选相机 {method} 初始化成功")
                    return True
            except Exception as e:
                print(f"[ERROR] {method} 初始化失败: {e}")
                continue
        
        print("[ERROR] ❌ 所有相机初始化都失败了")
        return False
    
    def _preallocate_gpu_memory(self):
        """预分配GPU内存"""
        if not self.enable_gpu_acceleration:
            return
        
        try:
            # 预分配一些GPU内存用于图像处理
            dummy_tensor = torch.zeros((1, 3, 320, 320), device='cuda', dtype=torch.float16)
            del dummy_tensor
            torch.cuda.empty_cache()
            print(f"[INFO] ✅ GPU内存预分配完成")
        except Exception as e:
            print(f"[WARNING] GPU内存预分配失败: {e}")
    
    def start(self):
        """启动截图系统"""
        if not self.camera:
            print("[ERROR] 相机未初始化，请先调用 select_game_window()")
            return False
        
        self.running = True
        
        # 启动截图线程
        for i in range(self.num_capture_threads):
            thread = threading.Thread(target=self._capture_worker, args=(i,))
            thread.daemon = True
            thread.start()
            self.capture_threads.append(thread)
        
        # 启动处理线程
        for i in range(self.num_processing_threads):
            thread = threading.Thread(target=self._processing_worker, args=(i,))
            thread.daemon = True
            thread.start()
            self.processing_threads.append(thread)
        
        print(f"[SUCCESS] ✅ 增强截图系统已启动")
        print(f"   • 截图线程: {len(self.capture_threads)}")
        print(f"   • 处理线程: {len(self.processing_threads)}")
        return True
    
    def _capture_worker(self, worker_id: int):
        """截图工作线程"""
        last_capture_time = 0
        frame_queue = self.frame_queues[worker_id]
        
        while self.running:
            try:
                current_time = time.time()
                
                # FPS限制
                if current_time - last_capture_time < self.frame_interval:
                    time.sleep(0.001)  # 1ms
                    continue
                
                # 截图
                start_time = time.time()
                frame = self.camera.get_latest_frame()
                capture_time = time.time() - start_time
                
                if frame is not None:
                    # 添加到队列
                    try:
                        frame_data = {
                            'frame': frame,
                            'timestamp': current_time,
                            'capture_time': capture_time,
                            'worker_id': worker_id
                        }
                        frame_queue.put_nowait(frame_data)
                        self.stats['frames_captured'] += 1
                    except queue.Full:
                        # 队列满，丢弃旧帧
                        try:
                            frame_queue.get_nowait()
                            frame_queue.put_nowait(frame_data)
                        except queue.Empty:
                            pass
                
                last_capture_time = current_time
                
            except Exception as e:
                print(f"[ERROR] 截图线程 {worker_id} 错误: {e}")
                time.sleep(0.01)
    
    def _processing_worker(self, worker_id: int):
        """处理工作线程"""
        while self.running:
            try:
                # 从所有队列中获取帧
                frame_data = None
                for frame_queue in self.frame_queues:
                    try:
                        frame_data = frame_queue.get_nowait()
                        break
                    except queue.Empty:
                        continue
                
                if frame_data is None:
                    time.sleep(0.001)
                    continue
                
                # 处理帧
                start_time = time.time()
                processed_frame = self._process_frame(frame_data['frame'])
                processing_time = time.time() - start_time
                
                if processed_frame is not None:
                    result_data = {
                        'frame': processed_frame,
                        'timestamp': frame_data['timestamp'],
                        'capture_time': frame_data['capture_time'],
                        'processing_time': processing_time,
                        'worker_id': worker_id
                    }
                    
                    try:
                        self.processed_queue.put_nowait(result_data)
                        self.stats['frames_processed'] += 1
                    except queue.Full:
                        # 队列满，丢弃旧帧
                        try:
                            self.processed_queue.get_nowait()
                            self.processed_queue.put_nowait(result_data)
                        except queue.Empty:
                            pass
                
            except Exception as e:
                print(f"[ERROR] 处理线程 {worker_id} 错误: {e}")
                time.sleep(0.01)
    
    def _process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """处理单帧"""
        try:
            if frame is None:
                return None
            
            # 移除alpha通道（如果存在）
            if frame.shape[2] == 4:
                frame = frame[:, :, :3]
            
            # GPU加速处理
            if self.enable_gpu_acceleration:
                return self._gpu_process_frame(frame)
            else:
                return self._cpu_process_frame(frame)
                
        except Exception as e:
            print(f"[ERROR] 帧处理失败: {e}")
            return None
    
    def _gpu_process_frame(self, frame: np.ndarray) -> np.ndarray:
        """GPU加速帧处理"""
        try:
            # 转换为GPU张量
            tensor = torch.from_numpy(frame).cuda().float()
            
            # 基本处理（可以根据需要扩展）
            # 这里只是示例，实际可以添加更多GPU加速的图像处理
            
            # 转换回CPU numpy数组
            processed_frame = tensor.cpu().numpy().astype(np.uint8)
            return processed_frame
            
        except Exception as e:
            print(f"[ERROR] GPU帧处理失败: {e}")
            return self._cpu_process_frame(frame)
    
    def _cpu_process_frame(self, frame: np.ndarray) -> np.ndarray:
        """CPU帧处理"""
        # 基本的CPU处理
        return frame
    
    def get_latest_frame(self) -> Optional[Dict]:
        """获取最新处理的帧"""
        try:
            return self.processed_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_stats(self) -> Dict:
        """获取性能统计"""
        # 计算队列大小
        queue_sizes = [q.qsize() for q in self.frame_queues] + [self.processed_queue.qsize()]
        self.stats['queue_sizes'] = queue_sizes
        
        return self.stats.copy()
    
    def stop(self):
        """停止截图系统"""
        print(f"[INFO] 🛑 正在停止增强截图系统...")
        
        self.running = False
        
        # 等待线程结束
        for thread in self.capture_threads + self.processing_threads:
            thread.join(timeout=1.0)
        
        # 清理相机
        if self.camera:
            try:
                self.camera.stop()
                self.camera.release()
            except:
                pass
        
        # 清理线程池
        self.capture_executor.shutdown(wait=False)
        self.processing_executor.shutdown(wait=False)
        
        print(f"[SUCCESS] ✅ 增强截图系统已停止")

# 便捷函数
def create_enhanced_screenshot_system(**kwargs) -> EnhancedScreenshotSystemWithWindowSelection:
    """创建增强截图系统的便捷函数"""
    return EnhancedScreenshotSystemWithWindowSelection(**kwargs)

def quick_start_with_window_selection(target_fps: int = 300, 
                                    capture_method: str = "auto") -> Optional[EnhancedScreenshotSystemWithWindowSelection]:
    """快速启动带窗口选择的截图系统"""
    system = create_enhanced_screenshot_system(
        target_fps=target_fps,
        capture_method=capture_method,
        auto_select_window=True
    )
    
    if system.select_game_window():
        if system.start():
            return system
    
    return None
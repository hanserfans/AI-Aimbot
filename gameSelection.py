import pygetwindow
import time
import bettercam
import sys
import os
from typing import Union

# Could be do with
# from config import *
# But we are writing it out for clarity for new devs
from config import screenShotHeight, screenShotWidth, autoSelectWindow, preferredWindowTitle, customGameKeywords

# 导入增强检测配置
try:
    from enhanced_detection_config import get_enhanced_detection_config
    ENHANCED_DETECTION_AVAILABLE = True
    print("[INFO] ✅ 增强检测配置已加载")
except ImportError as e:
    print(f"[WARNING] 增强检测配置加载失败: {e}")
    ENHANCED_DETECTION_AVAILABLE = False

# Try to import dxcam as fallback
try:
    import dxcam
    DXCAM_AVAILABLE = True
except ImportError:
    DXCAM_AVAILABLE = False
    print("[WARNING] dxcam 不可用，如果 bettercam 失败将无法使用备选方案")

def gameSelection() -> Union[tuple, None]:
    # Selecting the correct game window
    try:
        videoGameWindows = pygetwindow.getAllWindows()
        print("=== All Windows ===")
        for index, window in enumerate(videoGameWindows):
            # only output the window if it has a meaningful title
            if window.title != "":
                print("[{}]: {}".format(index, window.title))
        
        # Check if running in GUI mode
        # Multiple ways to detect GUI mode:
        # 1. Environment variable set by GUI
        # 2. Check if stdin is not a tty
        # 3. Check if autoSelectWindow is enabled (fallback)
        is_gui_mode = (
            os.environ.get('AIMBOT_GUI_MODE') == '1' or
            not sys.stdin.isatty() or
            autoSelectWindow
        )
        
        if is_gui_mode and autoSelectWindow:
            # Auto-select game window in GUI mode
            print("[AUTO] GUI模式检测到，正在自动选择游戏窗口...")
            videoGameWindow = auto_select_game_window(videoGameWindows)
            if videoGameWindow is None:
                print("[ERROR] 无法自动选择游戏窗口，请手动启动游戏后重试")
                print("[INFO] 提示：可以在config.py中设置preferredWindowTitle来指定目标窗口")
                return None
            print("[SUCCESS] 自动选择窗口: {}".format(videoGameWindow.title))
        else:
            # Manual selection in console mode
            try:
                userInput = int(input(
                    "Please enter the number corresponding to the window you'd like to select: "))
                videoGameWindow = videoGameWindows[userInput]
            except ValueError:
                print("You didn't enter a valid number. Please try again.")
                return None
            except IndexError:
                print("Invalid window index. Please try again.")
                return None
    except Exception as e:
        print("Failed to select game window: {}".format(e))
        return None

    # Activate that Window
    activationRetries = 30
    activationSuccess = False
    while (activationRetries > 0):
        try:
            videoGameWindow.activate()
            activationSuccess = True
            break
        except pygetwindow.PyGetWindowException as we:
            print("Failed to activate game window: {}".format(str(we)))
            print("Trying again... (you should switch to the game now)")
        except Exception as e:
            print("Failed to activate game window: {}".format(str(e)))
            print("Read the relevant restrictions here: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow")
            activationSuccess = False
            activationRetries = 0
            break
        # wait a little bit before the next try
        time.sleep(3.0)
        activationRetries = activationRetries - 1
    # if we failed to activate the window then we'll be unable to send input to it
    # so just exit the script now
    if activationSuccess == False:
        return None
    print("Successfully activated the game window...")

    # 使用增强检测配置计算截取区域
    if ENHANCED_DETECTION_AVAILABLE:
        enhanced_config = get_enhanced_detection_config()
        left, top, right, bottom = enhanced_config.get_capture_region(
            videoGameWindow.left, 
            videoGameWindow.top, 
            videoGameWindow.width, 
            videoGameWindow.height
        )
        
        # 更新截取区域尺寸
        actual_capture_width = enhanced_config.CAPTURE_SIZE
        actual_capture_height = enhanced_config.CAPTURE_SIZE
        
        print(f"[ENHANCED_DETECTION] 使用增强检测模式")
        print(f"[ENHANCED_DETECTION] 截取区域: {actual_capture_width}x{actual_capture_height}")
        print(f"[ENHANCED_DETECTION] 模型输入: {enhanced_config.MODEL_INPUT_SIZE}x{enhanced_config.MODEL_INPUT_SIZE}")
    else:
        # 原始截取逻辑（备用）
        left = ((videoGameWindow.left + videoGameWindow.right) // 2) - (screenShotWidth // 2)
        top = videoGameWindow.top + (videoGameWindow.height - screenShotHeight) // 2 + 18
        right, bottom = left + screenShotWidth, top + screenShotHeight
        actual_capture_width = screenShotWidth
        actual_capture_height = screenShotHeight
        print(f"[STANDARD_DETECTION] 使用标准检测模式: {actual_capture_width}x{actual_capture_height}")

    region: tuple = (left, top, right, bottom)

    # Calculating the center Autoaim box (基于实际截取尺寸)
    cWidth: int = actual_capture_width // 2
    cHeight: int = actual_capture_height // 2

    print(region)

    # Try bettercam first
    camera = None
    camera_type = "bettercam"
    
    try:
        print(f"[DEBUG] 尝试创建bettercam，region: {region}")
        # 确保region参数正确
        if len(region) == 4 and all(isinstance(x, int) for x in region):
            # 先尝试创建默认实例，然后删除重新创建带region的实例
            try:
                temp_camera = bettercam.create()
                if temp_camera:
                    del temp_camera  # 删除默认实例
                    print("[DEBUG] 已清理默认bettercam实例")
            except:
                pass
            
            # 创建BetterCam包装器来解决is_capturing属性缺失问题（保持在try内部，修正缩进）
            class BetterCamWrapper:
                def __init__(self, region):
                    self.region = region
                    self.is_capturing = False
                    self._camera = None

                def _center_crop_320(self, frame):
                    """
                    将输入帧中心裁剪为 320x320（若帧尺寸更大），避免下游缩放开销。
                    当帧尺寸小于 320x320 时，使用 INTER_AREA 进行一次性缩放。
                    """
                    try:
                        import numpy as np
                        h, w = frame.shape[:2]
                        if h == 320 and w == 320:
                            return frame
                        if h >= 320 and w >= 320:
                            y0 = (h - 320) // 2
                            x0 = (w - 320) // 2
                            return frame[y0:y0+320, x0:x0+320, :]
                        # 小于目标尺寸时降采样到 320x320
                        import cv2
                        return cv2.resize(frame, (320, 320), interpolation=cv2.INTER_AREA)
                    except Exception:
                        return frame

                def start(self, fps=60, video_mode=True):
                    try:
                        self._camera = bettercam.create(region=self.region, output_color="BGRA", max_buffer_len=512)
                        if self._camera is not None:
                            self._camera.start(fps, video_mode=video_mode)
                            self.is_capturing = True
                            print("[SUCCESS] 使用 bettercam 进行屏幕捕获")
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
                        frame = self._camera.get_latest_frame()
                        if frame is None:
                            return None
                        return self._center_crop_320(frame)
                    except Exception as e:
                        print(f"[ERROR] BetterCam获取帧失败: {e}")
                        return None

                def stop(self):
                    self.is_capturing = False
                    if self._camera is not None:
                        try:
                            # 避免调用有问题的stop方法，直接设置为None
                            self._camera = None
                        except Exception as e:
                            print(f"[DEBUG] BetterCam停止时出现错误: {e}")
                            self._camera = None

                def release(self):
                    self.stop()

            camera = BetterCamWrapper(region)
            if not camera.start(351, video_mode=True):
                raise Exception("BetterCam包装器启动失败")
        else:
            raise Exception(f"region参数格式错误: {region}")
    except Exception as e:
        print("[ERROR] bettercam 初始化失败: {}".format(str(e)))
        print(f"[DEBUG] region类型: {type(region)}, 内容: {region}")
        camera = None
        
        # Try dxcam as fallback
        if DXCAM_AVAILABLE:
            try:
                print("[INFO] 尝试使用 dxcam 作为备选方案...")
                print(f"[DEBUG] dxcam region: {region}")
                
                # 检查GPU内存状态
                try:
                    import torch
                    if torch.cuda.is_available():
                        gpu_memory_free = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)
                        print(f"[DEBUG] GPU可用内存: {gpu_memory_free / (1024**3):.1f}GB")
                except:
                    print("[DEBUG] 无法检查GPU内存状态")
                
                # 先尝试创建默认实例，然后删除重新创建带region的实例
                try:
                    temp_camera = dxcam.create()
                    if temp_camera:
                        temp_camera.release()
                        del temp_camera
                        print("[DEBUG] 已清理默认dxcam实例")
                except:
                    pass
                
                inner_cam = dxcam.create(device_idx=0, region=region, max_buffer_len=512)
                if inner_cam is not None:
                    inner_cam.start(351, video_mode=True)
                    # 包装 dxcam，确保输出统一为 320x320
                    class DXCamWrapper:
                        def __init__(self, cam):
                            self._camera = cam
                            self.is_capturing = True
                        
                        def _center_crop_320(self, frame):
                            """
                            将输入帧中心裁剪为 320x320（若帧尺寸更大），不足则一次性缩放。
                            """
                            try:
                                h, w = frame.shape[:2]
                                if h == 320 and w == 320:
                                    return frame
                                if h >= 320 and w >= 320:
                                    y0 = (h - 320) // 2
                                    x0 = (w - 320) // 2
                                    return frame[y0:y0+320, x0:x0+320, :]
                                import cv2
                                return cv2.resize(frame, (320, 320), interpolation=cv2.INTER_AREA)
                            except Exception:
                                return frame
                        
                        def start(self, fps=351, video_mode=True):
                            # 已在内部相机启动
                            self.is_capturing = True
                            return True
                        
                        def get_latest_frame(self):
                            if not self.is_capturing or self._camera is None:
                                return None
                            try:
                                frame = self._camera.get_latest_frame()
                                if frame is None:
                                    return None
                                return self._center_crop_320(frame)
                            except Exception as e:
                                print(f"[ERROR] dxcam获取帧失败: {e}")
                                return None
                        
                        def stop(self):
                            self.is_capturing = False
                            try:
                                self._camera.stop()
                            except:
                                pass
                        
                        def release(self):
                            self.stop()
                    camera = DXCamWrapper(inner_cam)
                    camera_type = "dxcam"
                    print("[SUCCESS] 使用 dxcam 进行屏幕捕获（统一输出 320x320）")
                else:
                    raise Exception("dxcam.create() 返回 None")
            except Exception as dxcam_error:
                print("[ERROR] dxcam 也初始化失败: {}".format(str(dxcam_error)))
                print(f"[DEBUG] dxcam错误详情: {type(dxcam_error).__name__}: {dxcam_error}")
                camera = None
        else:
            print("[ERROR] dxcam 不可用，无法使用备选方案")
    
    # 如果bettercam和dxcam都失败，尝试mss作为最终备选方案
    if camera is None:
        print("[INFO] 尝试使用 mss 作为最终备选方案...")
        try:
            import mss
            # 创建一个简单的mss包装器来模拟camera接口
            class MSSCamera:
                def __init__(self, region):
                    # 将 mss 捕获区域直接约束为中心 320x320（源头定幅）
                    src_left, src_top, src_right, src_bottom = region
                    src_w = max(0, src_right - src_left)
                    src_h = max(0, src_bottom - src_top)
                    cap_w = 320
                    cap_h = 320
                    # 居中取 320x320，如果源区域小于 320 则取源实际尺寸，后续再做一次性缩放
                    left = src_left + max((src_w - cap_w) // 2, 0)
                    top = src_top + max((src_h - cap_h) // 2, 0)
                    actual_w = cap_w if src_w >= cap_w else src_w
                    actual_h = cap_h if src_h >= cap_h else src_h
                    self.region = {"top": top, "left": left, "width": actual_w, "height": actual_h}
                    self.is_capturing = False
                    # 使用线程本地存储来避免线程安全问题
                    import threading
                    self._local = threading.local()
                
                def _get_sct(self):
                    """获取线程本地的mss实例"""
                    if not hasattr(self._local, 'sct'):
                        self._local.sct = mss.mss()
                    return self._local.sct
                
                def start(self, fps=60, video_mode=True):
                    self.is_capturing = True
                    print(f"[SUCCESS] 使用 mss 进行屏幕捕获，区域: {self.region}")
                
                def get_latest_frame(self):
                    if not self.is_capturing:
                        return None
                    try:
                        # 每次都获取线程本地的mss实例
                        sct = self._get_sct()
                        screenshot = sct.grab(self.region)
                        # 转换为numpy数组，格式为BGRA
                        import numpy as np
                        frame = np.array(screenshot)
                        # 若源区域不足 320，则做一次性缩放到 320x320；否则直接返回
                        try:
                            h, w = frame.shape[:2]
                            if h == 320 and w == 320:
                                return frame
                            import cv2
                            return cv2.resize(frame, (320, 320), interpolation=cv2.INTER_AREA)
                        except Exception:
                            return frame
                    except Exception as e:
                        print(f"[ERROR] mss截图失败: {e}")
                        return None
                
                def stop(self):
                    self.is_capturing = False
                    # 清理线程本地的mss实例
                    if hasattr(self._local, 'sct'):
                        try:
                            self._local.sct.close()
                        except:
                            pass
                        delattr(self._local, 'sct')
                
                def release(self):
                    self.stop()
            
            camera = MSSCamera(region)
            camera.start(351, video_mode=True)
            camera_type = "mss"
            
        except Exception as mss_error:
            print(f"[ERROR] mss 也初始化失败: {mss_error}")
            camera = None
    
    if camera is None:
        print("[ERROR] 所有屏幕捕获方案都失败了！")
        print("[INFO] 可能的解决方案:")
        print("  1. 以管理员权限运行程序")
        print("  2. 确保游戏运行在窗口模式而非全屏模式")
        print("  3. 检查 Windows 图形设置，将 python.exe 设置为节能模式")
        print("  4. 联系 @Wonder 寻求帮助: https://discord.gg/rootkitorg")
        return None

    return camera, cWidth, cHeight, camera_type, videoGameWindow, region

def auto_select_game_window(windows):
    """自动选择游戏窗口"""
    # 首先检查是否有指定的首选窗口
    if preferredWindowTitle:
        print("[INFO] 搜索指定窗口: {}".format(preferredWindowTitle))
        for window in windows:
            if preferredWindowTitle.lower() in window.title.lower():
                print("[SUCCESS] 找到指定窗口: {}".format(window.title))
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
    
    # 如果没有找到游戏窗口，选择第一个有效窗口（排除系统窗口）
    for window in valid_windows:
        # 进一步过滤系统窗口
        if (window.width > 800 and window.height > 600 and 
            window.left >= 0 and window.top >= 0):
            return window
    
    return None
#!/usr/bin/env python3
"""
YOLOv8 PT模型集成版本 - 支持Ultralytics YOLOv8 .pt格式模型
基于原有项目架构，集成YOLOv8模型支持
"""

import numpy as np
import cv2
import time
import win32api
import win32con
import pandas as pd
import json
import os
import asyncio
import gc
import torch
from ultralytics import YOLO
import mss
from PIL import Image
import ctypes

# 导入项目配置
from config import (
    aaMovementAmp, useMask, maskHeight, maskWidth, aaQuitKey, confidence, 
    headshot_mode, cpsDisplay, visuals, centerOfScreen, autoFire, autoFireShots, 
    autoFireDelay, autoFireKey, screenShotWidth, screenShotHeight, 
    pureTriggerFastMode, pureTriggerThreshold, showLiveFeed
)

import gameSelection
from precision_aiming_optimizer import optimize_aiming_parameters, get_precision_report, save_aiming_data, load_aiming_data
from dynamic_tracking_system import get_aiming_system
from auto_trigger_system import get_trigger_system
from threshold_config import ThresholdConfig
from smooth_mouse_movement import create_smooth_movement_system

# YOLOv8模型配置
class YOLOv8Config:
    """YOLOv8模型配置类"""
    
    def __init__(self):
        # 默认模型路径
        self.default_models = {
            'valorant': 'models/valorant/best.pt',
            'general': 'yolov8s.pt',
            'custom': 'best.pt'
        }
        
        # 模型设置
        self.model_settings = {
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'half': True,  # 使用半精度
            'verbose': False,
            'conf': confidence,
            'iou': 0.45,
            'classes': [0],  # 只检测人物 (person class)
            'max_det': 10,   # 最大检测数量
            'agnostic_nms': False
        }
        
        # 屏幕捕获设置
        self.capture_settings = {
            'width': 416,
            'height': 416,
            'fov_width': 150,
            'fov_height': 150,
            'speed': 1.25
        }
        
        # 获取屏幕尺寸
        self.screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        self.screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        
        # 计算FOV位置
        self.fov_x = (self.screen_width - self.capture_settings['fov_width']) // 2
        self.fov_y = (self.screen_height - self.capture_settings['fov_height']) // 2

class YOLOv8ModelManager:
    """YOLOv8模型管理器"""
    
    def __init__(self, config: YOLOv8Config):
        self.config = config
        self.model = None
        self.model_path = None
        self.is_loaded = False
        
    def load_model(self, model_path: str = None):
        """加载YOLOv8模型"""
        if model_path is None:
            # 尝试按优先级加载模型
            for model_type, path in self.config.default_models.items():
                if os.path.exists(path):
                    model_path = path
                    print(f"[INFO] 🎯 找到{model_type}模型: {path}")
                    break
            
            if model_path is None:
                raise FileNotFoundError("❌ 未找到可用的YOLOv8模型文件")
        
        try:
            print(f"[INFO] 🔄 加载YOLOv8模型: {model_path}")
            
            # 加载模型
            self.model = YOLO(model_path)
            
            # 移动到GPU（如果可用）
            if self.config.model_settings['device'] == 'cuda':
                self.model = self.model.cuda()
                print(f"[INFO] ✅ 模型已加载到GPU")
            
            # 启用半精度（如果支持）
            if self.config.model_settings['half'] and torch.cuda.is_available():
                self.model = self.model.half()
                print(f"[INFO] ✅ 启用半精度模式")
            
            self.model_path = model_path
            self.is_loaded = True
            
            # 预热模型
            self._warmup_model()
            
            print(f"[INFO] ✅ YOLOv8模型加载成功")
            return True
            
        except Exception as e:
            print(f"[ERROR] ❌ 模型加载失败: {e}")
            return False
    
    def _warmup_model(self):
        """预热模型以提高首次推理速度"""
        try:
            print("[INFO] 🔥 预热模型...")
            dummy_input = np.random.randint(0, 255, 
                (self.config.capture_settings['height'], 
                 self.config.capture_settings['width'], 3), 
                dtype=np.uint8)
            
            # 执行一次推理
            _ = self.model.predict(
                dummy_input,
                device=self.config.model_settings['device'],
                verbose=False,
                conf=self.config.model_settings['conf'],
                classes=self.config.model_settings['classes']
            )
            print("[INFO] ✅ 模型预热完成")
            
        except Exception as e:
            print(f"[WARNING] ⚠️ 模型预热失败: {e}")
    
    def predict(self, image: np.ndarray):
        """执行模型推理"""
        if not self.is_loaded:
            raise RuntimeError("模型未加载")
        
        try:
            results = self.model.predict(
                image,
                device=self.config.model_settings['device'],
                verbose=self.config.model_settings['verbose'],
                conf=self.config.model_settings['conf'],
                iou=self.config.model_settings['iou'],
                classes=self.config.model_settings['classes'],
                max_det=self.config.model_settings['max_det'],
                agnostic_nms=self.config.model_settings['agnostic_nms'],
                stream=True
            )
            
            return results
            
        except Exception as e:
            print(f"[ERROR] ❌ 推理失败: {e}")
            return None

class YOLOv8ScreenCapture:
    """YOLOv8屏幕捕获类"""
    
    def __init__(self, config: YOLOv8Config):
        self.config = config
        self.sct = mss.mss()
        
        # 定义捕获区域
        self.monitor = {
            "top": config.fov_y,
            "left": config.fov_x,
            "width": config.capture_settings['fov_width'],
            "height": config.capture_settings['fov_height']
        }
    
    def capture_frame(self):
        """捕获屏幕帧"""
        try:
            # 捕获FOV区域
            screenshot = self.sct.grab(self.monitor)
            
            # 转换为numpy数组
            screenshot_np = torch.tensor(screenshot, device='cuda').cpu().numpy()
            screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGBA2RGB)
            
            # 调整大小到模型输入尺寸
            screenshot_np = torch.nn.functional.interpolate(
    torch.from_numpy(screenshot_np).permute(2, 0, 1).float().unsqueeze(0).to('cuda'),
    size=(self.config.capture_settings['width'], 
                 self.config.capture_settings['height']), mode='bilinear', align_corners=False
).squeeze(0).permute(1, 2, 0).cpu().numpy().astype(np.uint8)
            
            return screenshot_np
            
        except Exception as e:
            print(f"[ERROR] ❌ 屏幕捕获失败: {e}")
            return None

class YOLOv8TargetProcessor:
    """YOLOv8目标处理器"""
    
    def __init__(self, config: YOLOv8Config):
        self.config = config
    
    def process_detections(self, results):
        """处理检测结果，找到最近的目标"""
        if not results:
            return None
        
        closest_box_distance = float('inf')
        closest_box_center = None
        
        for r in results:
            if r.boxes is None or len(r.boxes.xyxy) == 0:
                continue
            
            # 处理每个检测框
            for i in range(len(r.boxes.xyxy)):
                # 获取边界框坐标
                x1, y1, x2, y2 = r.boxes.xyxy[i].cpu().numpy()
                
                # 计算中心点
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                # 将坐标映射回屏幕坐标
                screen_x = (center_x * self.config.capture_settings['fov_width'] // 
                           self.config.capture_settings['width'] + self.config.fov_x)
                screen_y = (center_y * self.config.capture_settings['fov_height'] // 
                           self.config.capture_settings['height'] + self.config.fov_y)
                
                # 计算到屏幕中心的距离
                distance = np.sqrt(
                    (screen_x - self.config.screen_width / 2) ** 2 + 
                    (screen_y - self.config.screen_height / 2) ** 2
                )
                
                # 更新最近的目标
                if distance < closest_box_distance:
                    closest_box_distance = distance
                    closest_box_center = (screen_x, screen_y)
        
        return closest_box_center

class YOLOv8MouseController:
    """YOLOv8鼠标控制器"""
    
    def __init__(self, config: YOLOv8Config):
        self.config = config
        
        # 导入鼠标控制
        try:
            import interception
            self.interception = interception
            self.interception.auto_capture_devices(keyboard=True, mouse=True)
            self.mouse_available = True
            print("[INFO] ✅ Interception鼠标控制已初始化")
        except ImportError:
            print("[WARNING] ⚠️ Interception不可用，使用win32api")
            self.mouse_available = False
    
    async def move_mouse(self, x, y):
        """异步移动鼠标"""
        if self.mouse_available:
            self.interception.move_relative(int(x), int(y))
        else:
            # 使用win32api作为备选
            win32api.SetCursorPos((int(x), int(y)))
    
    def calculate_movement(self, target_pos):
        """计算鼠标移动量"""
        if target_pos is None:
            return None, None
        
        # 计算相对移动量
        relative_x = target_pos[0] - self.config.screen_width / 2
        relative_y = target_pos[1] - self.config.screen_height / 2
        
        # 应用速度系数
        move_x = relative_x * self.config.capture_settings['speed']
        move_y = relative_y * self.config.capture_settings['speed']
        
        return move_x, move_y

async def main_yolov8_loop():
    """YOLOv8主循环"""
    print("🎯 YOLOv8 AI瞄准系统启动")
    print("=" * 50)
    
    # 初始化组件
    config = YOLOv8Config()
    model_manager = YOLOv8ModelManager(config)
    screen_capture = YOLOv8ScreenCapture(config)
    target_processor = YOLOv8TargetProcessor(config)
    mouse_controller = YOLOv8MouseController(config)
    
    # 加载模型
    if not model_manager.load_model():
        print("❌ 模型加载失败，程序退出")
        return
    
    # 系统就绪提示
    print("\n🚀 YOLOv8系统已就绪，开始运行...")
    print("💡 提示: 按鼠标右键激活瞄准，按 Q 键退出程序")
    print("⚠️  注意: 确保以管理员权限运行\n")
    
    # 性能统计
    frame_count = 0
    start_time = time.time()
    last_fps_time = time.time()
    
    try:
        while win32api.GetAsyncKeyState(ord(aaQuitKey)) == 0:
            loop_start = time.time()
            
            # 检查鼠标右键是否按下
            if not (win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000):
                await asyncio.sleep(0.01)  # 短暂休眠以减少CPU使用
                continue
            
            # 捕获屏幕
            frame = screen_capture.capture_frame()
            if frame is None:
                continue
            
            # 模型推理
            results = model_manager.predict(frame)
            if results is None:
                continue
            
            # 处理检测结果
            target_pos = target_processor.process_detections(results)
            
            # 移动鼠标
            if target_pos is not None:
                move_x, move_y = mouse_controller.calculate_movement(target_pos)
                if move_x is not None and move_y is not None:
                    await mouse_controller.move_mouse(move_x, move_y)
            
            # 性能统计
            frame_count += 1
            current_time = time.time()
            
            if current_time - last_fps_time >= 1.0:
                fps = frame_count / (current_time - start_time)
                print(f"[INFO] 📊 FPS: {fps:.1f} | 目标: {'✅' if target_pos else '❌'}")
                last_fps_time = current_time
                frame_count = 0
                start_time = current_time
            
            # 高性能模式 - 无FPS限制，释放最大性能
            # 原60FPS限制已移除，现在支持351+ FPS
            pass
    
    except KeyboardInterrupt:
        print("\n[INFO] 🛑 用户中断程序")
    except Exception as e:
        print(f"\n[ERROR] ❌ 程序异常: {e}")
    finally:
        print("\n[INFO] 🔄 清理资源...")
        # 清理GPU内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        print("[INFO] ✅ 程序已安全退出")

def run_yolov8_aimbot():
    """运行YOLOv8瞄准机器人"""
    try:
        # 检查管理员权限
        import subprocess
        try:
            subprocess.check_output('net session', shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            print("❌ 请以管理员权限运行程序")
            return
        
        # 播放启动音效
        try:
            import winsound
            winsound.PlaySound("C:\\Windows\\Media\\Speech On.wav", winsound.SND_FILENAME)
        except:
            pass
        
        # 清屏
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # 运行主循环
        asyncio.run(main_yolov8_loop())
        
    except Exception as e:
        print(f"[ERROR] ❌ 启动失败: {e}")

if __name__ == "__main__":
    run_yolov8_aimbot()
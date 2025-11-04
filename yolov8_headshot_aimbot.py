"""
YOLOv8s 头部检测专用瞄准脚本
支持全屏和中心区域截屏模式
"""

import torch
import numpy as np
import cv2
import time
import win32api
import win32con
import pandas as pd
import gc
from ultralytics import YOLO
import mss
import threading
from collections import deque

# 导入现有配置
from config import aaMovementAmp, useMask, maskWidth, maskHeight, aaQuitKey, screenShotHeight, confidence, headshot_mode, cpsDisplay, visuals, centerOfScreen

class YOLOv8HeadshotAimbot:
    def __init__(self, model_path, capture_mode='center', confidence_threshold=0.5):
        """
        初始化YOLOv8头部检测瞄准机器人
        
        Args:
            model_path (str): YOLOv8s模型文件路径 (.pt)
            capture_mode (str): 截屏模式 'fullscreen' 或 'center'
            confidence_threshold (float): 检测置信度阈值
        """
        self.model_path = model_path
        self.capture_mode = capture_mode
        self.confidence_threshold = confidence_threshold
        
        # 加载YOLOv8模型
        print(f"正在加载YOLOv8模型: {model_path}")
        self.model = YOLO(model_path)
        print("模型加载完成")
        
        # 屏幕捕获设置
        self.sct = mss.mss()
        self.setup_capture_area()
        
        # 性能统计
        self.fps_counter = deque(maxlen=30)
        self.detection_history = deque(maxlen=10)
        
        # 瞄准参数
        self.headshot_offset_ratio = 0.1  # 头部专用模型的偏移比例
        self.smoothing_factor = 0.3  # 移动平滑因子
        self.last_target = None
        
        print(f"截屏模式: {capture_mode}")
        print(f"置信度阈值: {confidence_threshold}")
        
    def setup_capture_area(self):
        """设置截屏区域"""
        # 获取屏幕分辨率
        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        
        if self.capture_mode == 'fullscreen':
            # 全屏截图
            self.monitor = {
                "top": 0,
                "left": 0,
                "width": screen_width,
                "height": screen_height
            }
            self.center_x = screen_width // 2
            self.center_y = screen_height // 2
            
        else:  # center mode
            # 中心区域截图
            capture_width = min(screenShotHeight, screen_width)
            capture_height = min(screenShotHeight, screen_height)
            
            self.monitor = {
                "top": (screen_height - capture_height) // 2,
                "left": (screen_width - capture_width) // 2,
                "width": capture_width,
                "height": capture_height
            }
            self.center_x = capture_width // 2
            self.center_y = capture_height // 2
            
        print(f"截屏区域: {self.monitor}")
        
    def capture_screen(self):
        """截取屏幕"""
        screenshot = self.sct.grab(self.monitor)
        img = torch.tensor(screenshot, device='cuda').cpu().numpy()
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img
        
    def detect_heads(self, img):
        """使用YOLOv8检测头部"""
        # 运行推理
        results = self.model(img, conf=self.confidence_threshold, verbose=False)
        
        detections = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
                confidences = result.boxes.conf.cpu().numpy()
                
                for i, (box, conf) in enumerate(zip(boxes, confidences)):
                    x1, y1, x2, y2 = box
                    width = x2 - x1
                    height = y2 - y1
                    center_x = x1 + width / 2
                    center_y = y1 + height / 2
                    
                    detections.append({
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                        'center_x': center_x, 'center_y': center_y,
                        'width': width, 'height': height,
                        'confidence': conf
                    })
                    
        return detections
        
    def select_best_target(self, detections):
        """选择最佳目标"""
        if not detections:
            return None
            
        # 按置信度排序
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 选择距离屏幕中心最近的高置信度目标
        best_target = None
        min_distance = float('inf')
        
        for detection in detections:
            # 计算距离屏幕中心的距离
            dx = detection['center_x'] - self.center_x
            dy = detection['center_y'] - self.center_y
            distance = np.sqrt(dx*dx + dy*dy)
            
            # 优先选择高置信度且距离中心较近的目标
            score = distance / detection['confidence']
            
            if score < min_distance:
                min_distance = score
                best_target = detection
                
        return best_target
        
    def calculate_aim_point(self, target):
        """计算瞄准点"""
        if not target:
            return None
            
        # 头部中心点
        head_center_x = target['center_x']
        head_center_y = target['center_y']
        
        # 对于头部专用模型，瞄准点应该在头部中心或略低
        # 因为模型已经专门检测头部，所以偏移应该很小
        head_height = target['height']
        aim_offset = head_height * self.headshot_offset_ratio
        
        aim_x = head_center_x
        aim_y = head_center_y + aim_offset  # 略微向下偏移
        
        return aim_x, aim_y
        
    def smooth_movement(self, current_target, last_target, smoothing=0.3):
        """平滑鼠标移动"""
        if last_target is None:
            return current_target
            
        smooth_x = last_target[0] + (current_target[0] - last_target[0]) * smoothing
        smooth_y = last_target[1] + (current_target[1] - last_target[1]) * smoothing
        
        return smooth_x, smooth_y
        
    def move_mouse(self, target_x, target_y):
        """移动鼠标"""
        # 计算相对于屏幕中心的偏移
        if self.capture_mode == 'center':
            # 中心模式需要加上截屏区域的偏移
            screen_x = target_x + self.monitor['left'] - self.center_x
            screen_y = target_y + self.monitor['top'] - self.center_y
        else:
            # 全屏模式直接计算偏移
            screen_x = target_x - self.center_x
            screen_y = target_y - self.center_y
            
        # 应用移动幅度
        move_x = int(screen_x * aaMovementAmp)
        move_y = int(screen_y * aaMovementAmp)
        
        # 移动鼠标
        if abs(move_x) > 1 or abs(move_y) > 1:
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, move_x, move_y, 0, 0)
            
    def draw_debug_info(self, img, detections, target, fps):
        """绘制调试信息"""
        if not visuals:
            return img
            
        debug_img = img.copy()
        
        # 绘制所有检测结果
        for detection in detections:
            x1, y1, x2, y2 = int(detection['x1']), int(detection['y1']), int(detection['x2']), int(detection['y2'])
            conf = detection['confidence']
            
            # 绘制边界框
            color = (0, 255, 0) if detection == target else (0, 255, 255)
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, 2)
            
            # 绘制置信度
            cv2.putText(debug_img, f'{conf:.2f}', (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                       
        # 绘制瞄准点
        if target:
            aim_point = self.calculate_aim_point(target)
            if aim_point:
                cv2.circle(debug_img, (int(aim_point[0]), int(aim_point[1])), 5, (0, 0, 255), -1)
                
        # 绘制点状准星
        # 绘制点状准星：中心实心圆点 + 外围圆环
        cv2.circle(debug_img, (self.center_x, self.center_y), 3, (255, 255, 255), -1)  # 实心圆点
        cv2.circle(debug_img, (self.center_x, self.center_y), 8, (255, 255, 255), 1)   # 外围圆环
        
        # 显示FPS和检测信息
        cv2.putText(debug_img, f'FPS: {fps:.1f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(debug_img, f'Detections: {len(detections)}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(debug_img, f'Mode: {self.capture_mode}', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return debug_img
        
    def run(self):
        """主运行循环"""
        print("YOLOv8头部检测瞄准机器人启动")
        print(f"退出键: {aaQuitKey}")
        print("按住右键进行瞄准")
        
        try:
            while True:
                start_time = time.time()
                
                # 检查退出键
                if win32api.GetAsyncKeyState(ord(aaQuitKey.upper())) & 0x8000:
                    break
                    
                # 检查是否按住右键
                if win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000:
                    # 截取屏幕
                    img = self.capture_screen()
                    
                    # 检测头部
                    detections = self.detect_heads(img)
                    
                    # 选择最佳目标
                    target = self.select_best_target(detections)
                    
                    if target:
                        # 计算瞄准点
                        aim_point = self.calculate_aim_point(target)
                        
                        if aim_point:
                            # 平滑移动
                            if self.last_target:
                                aim_point = self.smooth_movement(aim_point, self.last_target, self.smoothing_factor)
                            
                            # 移动鼠标
                            self.move_mouse(aim_point[0], aim_point[1])
                            self.last_target = aim_point
                    else:
                        self.last_target = None
                        
                    # 计算FPS
                    frame_time = time.time() - start_time
                    fps = 1.0 / frame_time if frame_time > 0 else 0
                    self.fps_counter.append(fps)
                    avg_fps = sum(self.fps_counter) / len(self.fps_counter)
                    
                    # 显示调试信息
                    if visuals:
                        debug_img = self.draw_debug_info(img, detections, target, avg_fps)
                        cv2.imshow('YOLOv8 Headshot Aimbot', debug_img)
                        
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                            
                    # 控制帧率
                    if cpsDisplay and frame_time < 1.0/cpsDisplay:
                        time.sleep(1.0/cpsDisplay - frame_time)
                        
                else:
                    # 没有按住右键时稍微休息
                    time.sleep(0.001)  # 高性能模式：1ms延迟
                    
        except KeyboardInterrupt:
            print("用户中断")
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cv2.destroyAllWindows()
            print("YOLOv8头部检测瞄准机器人已停止")

def main():
    """主函数"""
    # 配置参数
    model_path = "customModels/yolov8s_head.pt"  # 你的YOLOv8s头部模型路径
    capture_mode = "center"  # 或 "fullscreen"
    confidence_threshold = 0.5
    
    # 检查模型文件是否存在
    import os
    if not os.path.exists(model_path):
        print(f"错误: 模型文件不存在: {model_path}")
        print("请将你的YOLOv8s头部检测模型放在指定路径")
        return
        
    # 创建并运行瞄准机器人
    aimbot = YOLOv8HeadshotAimbot(
        model_path=model_path,
        capture_mode=capture_mode,
        confidence_threshold=confidence_threshold
    )
    
    aimbot.run()

if __name__ == "__main__":
    main()
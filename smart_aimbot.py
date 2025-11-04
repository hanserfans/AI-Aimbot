"""
智能瞄准机器人
支持多种检测模型的自动切换和优化
"""

import torch
import numpy as np
import cv2
import time
import win32api
import win32con
import pandas as pd
import gc
import os
import sys
from collections import deque

# 导入配置
from config import aaMovementAmp, useMask, maskWidth, maskHeight, aaQuitKey, screenShotHeight, confidence, headshot_mode, cpsDisplay, visuals, centerOfScreen
from model_config import ModelConfig

# 尝试导入不同的模型库
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("警告: ultralytics未安装，无法使用YOLOv8模型")

try:
    from utils.general import non_max_suppression, xyxy2xywh
    from utils.torch_utils import select_device
    YOLOV5_AVAILABLE = True
except ImportError:
    YOLOV5_AVAILABLE = False
    print("警告: YOLOv5工具未找到")

import mss

class SmartAimbot:
    def __init__(self):
        """初始化智能瞄准机器人"""
        self.config = ModelConfig()
        self.model = None
        self.model_type = None
        self.device = None
        
        # 屏幕捕获
        self.sct = mss.mss()
        self.setup_capture_area()
        
        # 性能统计
        self.fps_counter = deque(maxlen=30)
        self.detection_history = deque(maxlen=10)
        
        # 瞄准状态
        self.last_target = None
        self.target_lock_time = 0
        
        # 加载当前模型
        self.load_current_model()
        
    def setup_capture_area(self):
        """设置截屏区域"""
        capture_settings = self.config.get_capture_settings()
        
        # 获取屏幕分辨率
        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        
        if capture_settings["mode"] == "fullscreen":
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
            capture_size = capture_settings.get("center_size", screenShotHeight)
            capture_width = min(capture_size, screen_width)
            capture_height = min(capture_size, screen_height)
            
            self.monitor = {
                "top": (screen_height - capture_height) // 2,
                "left": (screen_width - capture_width) // 2,
                "width": capture_width,
                "height": capture_height
            }
            self.center_x = capture_width // 2
            self.center_y = capture_height // 2
            
        print(f"截屏区域: {self.monitor}")
        
    def load_current_model(self):
        """加载当前配置的模型"""
        current_model_info = self.config.get_current_model()
        model_path = current_model_info["path"]
        model_type = current_model_info["type"]
        
        if not os.path.exists(model_path):
            print(f"错误: 模型文件不存在: {model_path}")
            return False
            
        print(f"正在加载模型: {model_path}")
        print(f"模型类型: {model_type}")
        
        try:
            if model_type == "yolov8":
                if not YOLO_AVAILABLE:
                    print("错误: YOLOv8不可用，请安装ultralytics")
                    return False
                self.model = YOLO(model_path)
                self.model_type = "yolov8"
                
            elif model_type == "yolov5":
                if not YOLOV5_AVAILABLE:
                    print("错误: YOLOv5工具不可用")
                    return False
                    
                # 加载YOLOv5模型
                self.device = select_device('')
                if model_path.endswith('.onnx'):
                    # ONNX模型
                    import onnxruntime as ort
                    self.model = ort.InferenceSession(model_path)
                    self.model_type = "yolov5_onnx"
                else:
                    # PyTorch模型
                    self.model = torch.jit.load(model_path, map_location=self.device)
                    self.model_type = "yolov5_torch"
                    
            print("模型加载成功")
            return True
            
        except Exception as e:
            print(f"模型加载失败: {e}")
            return False
            
    def capture_screen(self):
        """截取屏幕"""
        screenshot = self.sct.grab(self.monitor)
        img = torch.tensor(screenshot, device='cuda').cpu().numpy()
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img
        
    def detect_yolov8(self, img):
        """使用YOLOv8进行检测"""
        current_model_info = self.config.get_current_model()
        conf_threshold = current_model_info.get("confidence", 0.5)
        
        results = self.model(img, conf=conf_threshold, verbose=False)
        
        detections = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()
                
                for box, conf in zip(boxes, confidences):
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
        
    def detect_yolov5_onnx(self, img):
        """使用YOLOv5 ONNX进行检测"""
        # 预处理
        img_resized = torch.nn.functional.interpolate(
    torch.from_numpy(img).permute(2, 0, 1).float().unsqueeze(0).to('cuda'),
    size=(320, 320), mode='bilinear', align_corners=False
).squeeze(0).permute(1, 2, 0).cpu().numpy().astype(np.uint8)
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_normalized = (torch.from_numpy(img_rgb).float().to('cuda') / 255.0).cpu().numpy()
        img_transposed = np.transpose(img_normalized, (2, 0, 1))
        img_batch = np.expand_dims(img_transposed, axis=0)
        
        # 推理
        input_name = self.model.get_inputs()[0].name
        outputs = self.model.run(None, {input_name: img_batch})
        predictions = outputs[0]
        
        # 后处理
        detections = []
        current_model_info = self.config.get_current_model()
        conf_threshold = current_model_info.get("confidence", 0.4)
        
        # 缩放因子
        scale_x = img.shape[1] / 320
        scale_y = img.shape[0] / 320
        
        for detection in predictions[0]:
            confidence = detection[4]
            if confidence > conf_threshold:
                x_center, y_center, width, height = detection[:4]
                
                # 转换到原始图像坐标
                x_center *= scale_x
                y_center *= scale_y
                width *= scale_x
                height *= scale_y
                
                x1 = x_center - width / 2
                y1 = y_center - height / 2
                x2 = x_center + width / 2
                y2 = y_center + height / 2
                
                detections.append({
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'center_x': x_center, 'center_y': y_center,
                    'width': width, 'height': height,
                    'confidence': confidence
                })
                
        return detections
        
    def detect_targets(self, img):
        """根据模型类型进行目标检测"""
        if self.model is None:
            return []
            
        if self.model_type == "yolov8":
            return self.detect_yolov8(img)
        elif self.model_type == "yolov5_onnx":
            return self.detect_yolov5_onnx(img)
        else:
            print(f"不支持的模型类型: {self.model_type}")
            return []
            
    def select_best_target(self, detections):
        """选择最佳目标"""
        if not detections:
            return None
            
        aiming_settings = self.config.get_aiming_settings()
        selection_method = aiming_settings.get("target_selection", "closest")
        max_distance = aiming_settings.get("max_distance", 200)
        
        # 过滤距离过远的目标
        valid_targets = []
        for detection in detections:
            dx = detection['center_x'] - self.center_x
            dy = detection['center_y'] - self.center_y
            distance = np.sqrt(dx*dx + dy*dy)
            
            if distance <= max_distance:
                detection['distance'] = distance
                valid_targets.append(detection)
                
        if not valid_targets:
            return None
            
        # 根据选择方法排序
        if selection_method == "closest":
            valid_targets.sort(key=lambda x: x['distance'])
        elif selection_method == "highest_conf":
            valid_targets.sort(key=lambda x: x['confidence'], reverse=True)
        elif selection_method == "largest":
            valid_targets.sort(key=lambda x: x['width'] * x['height'], reverse=True)
            
        return valid_targets[0]
        
    def calculate_aim_point(self, target):
        """计算瞄准点"""
        if not target:
            return None
            
        current_model_info = self.config.get_current_model()
        
        # 根据headshot_mode选择偏移
        if headshot_mode:
            offset_ratio = current_model_info.get("headshot_offset", 0.38)
        else:
            offset_ratio = current_model_info.get("body_offset", 0.2)
            
        # 计算瞄准点
        center_x = target['center_x']
        center_y = target['center_y']
        height = target['height']
        
        # 应用偏移
        aim_offset = height * offset_ratio
        aim_x = center_x
        aim_y = center_y - aim_offset  # 向上偏移（头部方向）
        
        return aim_x, aim_y
        
    def smooth_movement(self, current_target, last_target):
        """平滑鼠标移动"""
        if last_target is None:
            return current_target
            
        aiming_settings = self.config.get_aiming_settings()
        smoothing = aiming_settings.get("smoothing_factor", 0.3)
        
        smooth_x = last_target[0] + (current_target[0] - last_target[0]) * smoothing
        smooth_y = last_target[1] + (current_target[1] - last_target[1]) * smoothing
        
        return smooth_x, smooth_y
        
    def move_mouse(self, target_x, target_y):
        """移动鼠标"""
        capture_settings = self.config.get_capture_settings()
        aiming_settings = self.config.get_aiming_settings()
        
        # 计算相对于屏幕中心的偏移
        if capture_settings["mode"] == "center":
            screen_x = target_x + self.monitor['left'] - self.center_x
            screen_y = target_y + self.monitor['top'] - self.center_y
        else:
            screen_x = target_x - self.center_x
            screen_y = target_y - self.center_y
            
        # 应用移动幅度
        movement_amp = aiming_settings.get("movement_amp", aaMovementAmp)
        move_x = int(screen_x * movement_amp)
        move_y = int(screen_y * movement_amp)
        
        # 移动鼠标
        if abs(move_x) > 1 or abs(move_y) > 1:
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, move_x, move_y, 0, 0)
            
    def draw_debug_info(self, img, detections, target, fps):
        """绘制调试信息"""
        if not visuals:
            return img
            
        debug_img = img.copy()
        current_model_info = self.config.get_current_model()
        
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
        
        # 显示信息
        info_y = 30
        cv2.putText(debug_img, f'FPS: {fps:.1f}', (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        info_y += 30
        cv2.putText(debug_img, f'Targets: {len(detections)}', (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        info_y += 30
        cv2.putText(debug_img, f'Model: {self.config.config["current_model"]}', (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        info_y += 30
        cv2.putText(debug_img, f'Mode: {headshot_mode and "HEAD" or "BODY"}', (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return debug_img
        
    def run(self):
        """主运行循环"""
        if self.model is None:
            print("错误: 没有可用的模型")
            return
            
        print("智能瞄准机器人启动")
        print(f"当前模型: {self.config.config['current_model']}")
        print(f"退出键: {aaQuitKey}")
        print("按住右键进行瞄准")
        print("按 'M' 键切换模型")
        
        try:
            while True:
                start_time = time.time()
                
                # 检查退出键
                if win32api.GetAsyncKeyState(ord(aaQuitKey.upper())) & 0x8000:
                    break
                    
                # 检查模型切换键
                if win32api.GetAsyncKeyState(ord('M')) & 0x8000:
                    self.switch_model_menu()
                    time.sleep(0.5)  # 防止重复触发
                    
                # 检查是否按住右键
                if win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000:
                    # 截取屏幕
                    img = self.capture_screen()
                    
                    # 检测目标
                    detections = self.detect_targets(img)
                    
                    # 选择最佳目标
                    target = self.select_best_target(detections)
                    
                    if target:
                        # 计算瞄准点
                        aim_point = self.calculate_aim_point(target)
                        
                        if aim_point:
                            # 平滑移动
                            if self.last_target:
                                aim_point = self.smooth_movement(aim_point, self.last_target)
                            
                            # 移动鼠标
                            self.move_mouse(aim_point[0], aim_point[1])
                            self.last_target = aim_point
                            self.target_lock_time = time.time()
                    else:
                        # 如果超过一定时间没有目标，清除last_target
                        if time.time() - self.target_lock_time > 0.5:
                            self.last_target = None
                        
                    # 计算FPS
                    frame_time = time.time() - start_time
                    fps = 1.0 / frame_time if frame_time > 0 else 0
                    self.fps_counter.append(fps)
                    avg_fps = sum(self.fps_counter) / len(self.fps_counter)
                    
                    # 显示调试信息
                    if visuals:
                        debug_img = self.draw_debug_info(img, detections, target, avg_fps)
                        cv2.imshow('Smart Aimbot', debug_img)
                        
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord('q'):
                            break
                        elif key == ord('m'):
                            self.switch_model_menu()
                            
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
            print("智能瞄准机器人已停止")
            
    def switch_model_menu(self):
        """模型切换菜单"""
        available_models = self.config.get_available_models()
        
        if len(available_models) <= 1:
            print("没有其他可用模型")
            return
            
        print("\n可用模型:")
        for i, name in enumerate(available_models, 1):
            info = self.config.get_model_info(name)
            current_mark = " (当前)" if name == self.config.config["current_model"] else ""
            print(f"{i}. {name}{current_mark} - {info['description']}")
            
        print("0. 取消")
        
        try:
            choice = int(input("请选择模型 (输入数字): "))
            if choice == 0:
                return
            elif 1 <= choice <= len(available_models):
                selected_model = available_models[choice - 1]
                if self.config.set_current_model(selected_model):
                    print(f"正在切换到模型: {selected_model}")
                    if self.load_current_model():
                        print("模型切换成功")
                    else:
                        print("模型切换失败")
                else:
                    print("模型切换失败")
            else:
                print("无效选择")
        except ValueError:
            print("请输入有效数字")
        except KeyboardInterrupt:
            pass

def main():
    """主函数"""
    print("智能瞄准机器人")
    print("=" * 50)
    
    # 显示当前配置
    config = ModelConfig()
    config.print_model_status()
    
    # 创建并运行瞄准机器人
    aimbot = SmartAimbot()
    aimbot.run()

if __name__ == "__main__":
    main()
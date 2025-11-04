# Arduino Leonardo 串口通信 AI-Aimbot 脚本
import torch
import numpy as np
import cv2
import time
import win32api
import win32con
from PIL import ImageGrab
import serial
import serial.tools.list_ports
from utils.general import non_max_suppression
from models.common import DetectMultiBackend

# Arduino 串口配置
ARDUINO_BAUDRATE = 9600
ARDUINO_PORT = None  # 自动检测

def find_arduino_port():
    """自动查找 Arduino 串口"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # 查找 Arduino 设备
        if 'Arduino' in port.description or 'CH340' in port.description or 'USB Serial' in port.description:
            print(f"找到 Arduino 设备: {port.device} - {port.description}")
            return port.device
    return None

def connect_arduino():
    """连接 Arduino 设备"""
    global arduino_serial
    
    # 自动查找 Arduino 端口
    port = find_arduino_port()
    if not port:
        print("错误: 未找到 Arduino 设备，请检查连接")
        print("可用串口:")
        ports = serial.tools.list_ports.comports()
        for p in ports:
            print(f"  {p.device} - {p.description}")
        return False
    
    try:
        arduino_serial = serial.Serial(port, ARDUINO_BAUDRATE, timeout=1)
        time.sleep(2)  # 等待 Arduino 重启
        
        # 测试连接
        arduino_serial.write(b'STATUS\n')
        response = arduino_serial.readline().decode().strip()
        
        if response == "OK":
            print(f"Arduino 连接成功: {port}")
            return True
        else:
            print(f"Arduino 响应异常: {response}")
            return False
            
    except Exception as e:
        print(f"Arduino 连接失败: {e}")
        return False

def move_arduino_mouse(x, y):
    """通过 Arduino 移动鼠标"""
    global arduino_serial
    
    x = int(np.floor(x))
    y = int(np.floor(y))
    
    if x != 0 or y != 0:
        try:
            command = f'M{x},{y}\n'
            arduino_serial.write(command.encode())
            
            # 读取 Arduino 响应（可选）
            response = arduino_serial.readline().decode().strip()
            if response:
                print(f"Arduino: {response}")
                
        except Exception as e:
            print(f"Arduino 通信错误: {e}")

def click_arduino_mouse(button='L'):
    """通过 Arduino 点击鼠标"""
    global arduino_serial
    
    try:
        command = f'C{button}\n'
        arduino_serial.write(command.encode())
        
        response = arduino_serial.readline().decode().strip()
        if response:
            print(f"Arduino: {response}")
            
    except Exception as e:
        print(f"Arduino 点击错误: {e}")

# 全局变量
arduino_serial = None

# 连接 Arduino
if not connect_arduino():
    print("无法连接 Arduino，程序退出")
    exit(1)

# AI 模型配置
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
half = device.type != 'cpu'

# 加载模型
model = DetectMultiBackend('yolov5s320Half.engine', device=device, dnn=False, data=None, fp16=half)
stride, names, pt = model.stride, model.names, model.pt

# 配置参数
confidence = 0.4
aaMovementAmp = 0.8
aaQuitKey = 0x71  # F2 键退出
headshot_mode = True

# 颜色配置
colors = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [255, 0, 255]]

print("AI-Aimbot Arduino 版本启动成功!")
print("按住 Ctrl+F 激活自动瞄准")
print("按 F2 退出程序")

try:
    while True:
        # 检查退出键
        if win32api.GetAsyncKeyState(aaQuitKey):
            break
        
        # 截取屏幕
        img = np.array(ImageGrab.grab(bbox=(640, 640)))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        # AI 推理
        img_tensor = torch.from_numpy(img).to(device)
        img_tensor = img_tensor.half() if half else img_tensor.float()
        img_tensor /= 255.0
        
        if img_tensor.ndimension() == 3:
            img_tensor = img_tensor.unsqueeze(0)
        
        # 目标检测
        pred = model(img_tensor)
        pred = non_max_suppression(pred, confidence, 0.45, None, False, max_det=10)
        
        # 处理检测结果
        for i, det in enumerate(pred):
            if len(det):
                # 获取最佳目标
                det = det[det[:, 4].argmax()].unsqueeze(0)  # 选择置信度最高的目标
                
                # 计算目标中心点
                x1, y1, x2, y2 = det[0][:4].cpu().numpy()
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # 爆头模式调整
                if headshot_mode:
                    center_y = y1 + (y2 - y1) * 0.25  # 瞄准头部区域
                
                # 计算移动距离
                screen_center_x = 320
                screen_center_y = 320
                
                move_x = (center_x - screen_center_x) * aaMovementAmp
                move_y = (center_y - screen_center_y) * aaMovementAmp
                
                # 检查激活键 (Ctrl+F)
                # Check for Ctrl+F combination (Ctrl=0x11, F=0x46)
                if (win32api.GetAsyncKeyState(0x11) < 0) and (win32api.GetAsyncKeyState(0x46) < 0):
                    move_arduino_mouse(move_x, move_y)
        
        time.sleep(0.01)  # 控制循环频率

except KeyboardInterrupt:
    print("程序被用户中断")

finally:
    # 关闭 Arduino 连接
    if arduino_serial:
        arduino_serial.close()
        print("Arduino 连接已关闭")
    
    print("程序退出")
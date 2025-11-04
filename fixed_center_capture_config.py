#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
固定屏幕中心截图区域配置
确保截图区域始终在屏幕正中心的320x320区域
"""

import win32api
from typing import Tuple

class FixedCenterCaptureConfig:
    """固定屏幕中心截图配置"""
    
    def __init__(self):
        self.CAPTURE_SIZE = 320  # 固定320x320截图区域
        self.MODEL_INPUT_SIZE = 320  # 模型输入尺寸
        self.SCALE_FACTOR = self.CAPTURE_SIZE / self.MODEL_INPUT_SIZE  # 1.0
        
    def get_screen_info(self) -> Tuple[int, int, int, int]:
        """获取屏幕信息"""
        try:
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
        except ImportError:
            # 默认分辨率
            screen_width = 2560
            screen_height = 1600
            print("[WARNING] 无法获取屏幕分辨率，使用默认值 2560x1600")
        
        screen_center_x = screen_width // 2
        screen_center_y = screen_height // 2
        
        return screen_width, screen_height, screen_center_x, screen_center_y
    
    def get_fixed_center_region(self) -> Tuple[int, int, int, int]:
        """
        获取固定的屏幕中心320x320区域
        
        Returns:
            tuple: (left, top, right, bottom) 屏幕正中心的320x320区域坐标
        """
        screen_width, screen_height, screen_center_x, screen_center_y = self.get_screen_info()
        
        # 计算320x320区域的边界（以屏幕中心为基准）
        half_capture = self.CAPTURE_SIZE // 2  # 160
        
        left = screen_center_x - half_capture
        top = screen_center_y - half_capture
        right = left + self.CAPTURE_SIZE
        bottom = top + self.CAPTURE_SIZE
        
        # 确保区域不超出屏幕边界
        if left < 0:
            left = 0
            right = self.CAPTURE_SIZE
        elif right > screen_width:
            right = screen_width
            left = screen_width - self.CAPTURE_SIZE
            
        if top < 0:
            top = 0
            bottom = self.CAPTURE_SIZE
        elif bottom > screen_height:
            bottom = screen_height
            top = screen_height - self.CAPTURE_SIZE
        
        print(f"[FIXED_CENTER] 屏幕分辨率: {screen_width}x{screen_height}")
        print(f"[FIXED_CENTER] 屏幕中心: ({screen_center_x}, {screen_center_y})")
        print(f"[FIXED_CENTER] 截图区域: ({left}, {top}, {right}, {bottom})")
        print(f"[FIXED_CENTER] 区域大小: {self.CAPTURE_SIZE}x{self.CAPTURE_SIZE}")
        
        # 验证区域中心
        region_center_x = left + self.CAPTURE_SIZE // 2
        region_center_y = top + self.CAPTURE_SIZE // 2
        print(f"[FIXED_CENTER] 截图区域中心: ({region_center_x}, {region_center_y})")
        
        # 计算与屏幕中心的偏差
        offset_x = region_center_x - screen_center_x
        offset_y = region_center_y - screen_center_y
        print(f"[FIXED_CENTER] 与屏幕中心偏差: ({offset_x}, {offset_y}) 像素")
        
        if abs(offset_x) <= 1 and abs(offset_y) <= 1:
            print(f"[FIXED_CENTER] ✅ 截图区域完美居中")
        else:
            print(f"[FIXED_CENTER] ⚠️ 截图区域存在偏差")
        
        return (left, top, right, bottom)
    
    def get_capture_region_center(self) -> Tuple[int, int]:
        """
        获取截图区域内坐标系的中心点
        
        Returns:
            tuple: (center_x, center_y) 截图区域内的中心坐标
        """
        center_x = self.CAPTURE_SIZE // 2  # 160
        center_y = self.CAPTURE_SIZE // 2  # 160
        return (center_x, center_y)
    
    def scale_coordinates_to_capture(self, model_x: float, model_y: float) -> Tuple[float, float]:
        """
        将模型输出坐标缩放到截图区域坐标
        
        Args:
            model_x: 模型输出X坐标 (0-320)
            model_y: 模型输出Y坐标 (0-320)
            
        Returns:
            tuple: 截图区域坐标 (0-320)
        """
        scaled_x = model_x * self.SCALE_FACTOR
        scaled_y = model_y * self.SCALE_FACTOR
        return (scaled_x, scaled_y)
    
    def scale_coordinates_to_model(self, capture_x: float, capture_y: float) -> Tuple[float, float]:
        """
        将截图区域坐标缩放到模型输入坐标
        
        Args:
            capture_x: 截图区域X坐标 (0-320)
            capture_y: 截图区域Y坐标 (0-320)
            
        Returns:
            tuple: 模型输入坐标 (0-320)
        """
        model_x = capture_x / self.SCALE_FACTOR
        model_y = capture_y / self.SCALE_FACTOR
        return (model_x, model_y)

def test_fixed_center_config():
    """测试固定中心配置"""
    print("=== 测试固定屏幕中心截图配置 ===")
    
    config = FixedCenterCaptureConfig()
    
    # 获取屏幕信息
    screen_width, screen_height, screen_center_x, screen_center_y = config.get_screen_info()
    
    # 获取截图区域
    left, top, right, bottom = config.get_fixed_center_region()
    
    # 获取区域内中心点
    region_center_x, region_center_y = config.get_capture_region_center()
    
    print(f"\n=== 配置验证 ===")
    print(f"屏幕分辨率: {screen_width}x{screen_height}")
    print(f"屏幕中心: ({screen_center_x}, {screen_center_y})")
    print(f"截图区域: ({left}, {top}) 到 ({right}, {bottom})")
    print(f"截图区域尺寸: {right-left}x{bottom-top}")
    print(f"截图区域内中心: ({region_center_x}, {region_center_y})")
    
    # 测试坐标转换
    print(f"\n=== 坐标转换测试 ===")
    # 模型输出中心点 (160, 160) 应该对应截图区域中心 (320, 320)
    model_center_x, model_center_y = 160, 160
    capture_x, capture_y = config.scale_coordinates_to_capture(model_center_x, model_center_y)
    print(f"模型中心 ({model_center_x}, {model_center_y}) -> 截图区域 ({capture_x}, {capture_y})")
    
    # 反向转换
    back_model_x, back_model_y = config.scale_coordinates_to_model(capture_x, capture_y)
    print(f"截图区域 ({capture_x}, {capture_y}) -> 模型 ({back_model_x}, {back_model_y})")
    
    if abs(back_model_x - model_center_x) < 0.1 and abs(back_model_y - model_center_y) < 0.1:
        print("✅ 坐标转换测试通过")
    else:
        print("❌ 坐标转换测试失败")

if __name__ == "__main__":
    test_fixed_center_config()
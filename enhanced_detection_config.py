#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强检测配置
解决检测框太小导致近战敌人扫描不到的问题
通过增大截取区域但保持模型输入尺寸不变来实现
"""

import cv2
import numpy as np
from typing import Tuple, Optional

class EnhancedDetectionConfig:
    """增强检测配置类"""
    
    def __init__(self, base_capture_size: int = None):
        """
        初始化增强检测配置
        
        Args:
            base_capture_size: 基础截取尺寸，如果为None则从config.py导入
        """
        # 导入config.py中的截图尺寸设置
        if base_capture_size is None:
            try:
                from config import screenShotHeight, screenShotWidth
                # 使用config.py中的设置作为基础尺寸
                self.BASE_CAPTURE_SIZE = max(screenShotHeight, screenShotWidth)
            except ImportError:
                # 如果无法导入config，使用默认值
                self.BASE_CAPTURE_SIZE = 320
        else:
            self.BASE_CAPTURE_SIZE = base_capture_size
        
        # 原始模型输入尺寸（不变）
        self.MODEL_INPUT_SIZE = 320
        
        # 纯320坐标系：不使用增强检测，直接使用320x320
        self.ENHANCEMENT_FACTOR = 1.0  # 320 * 1.0 = 320
        
        # 使用320x320截取区域尺寸（与模型输入尺寸一致）
        self.CAPTURE_SIZE = 320
        
        # 计算缩放比例：320x320模型坐标到320x320截图坐标（无缩放）
        self.SCALE_FACTOR = self.CAPTURE_SIZE / self.MODEL_INPUT_SIZE  # 320 / 320 = 1.0
        
        print(f"[ENHANCED_DETECTION] 配置初始化:")
        print(f"  - 基础截取尺寸: {self.BASE_CAPTURE_SIZE}x{self.BASE_CAPTURE_SIZE}")
        print(f"  - 增强倍数: {self.ENHANCEMENT_FACTOR}")
        print(f"  - 实际截取区域尺寸: {self.CAPTURE_SIZE}x{self.CAPTURE_SIZE}")
        print(f"  - 模型输入尺寸: {self.MODEL_INPUT_SIZE}x{self.MODEL_INPUT_SIZE}")
        print(f"  - 缩放比例: {self.SCALE_FACTOR:.2f}")
    
    def get_capture_region(self, game_window_left: int = None, game_window_top: int = None, 
                          game_window_width: int = None, game_window_height: int = None) -> Tuple[int, int, int, int]:
        """
        计算截取区域 - 基于游戏窗口中心或屏幕中心
        
        Args:
            game_window_left: 游戏窗口左边界
            game_window_top: 游戏窗口上边界
            game_window_width: 游戏窗口宽度
            game_window_height: 游戏窗口高度
            
        Returns:
            tuple: (left, top, right, bottom) 截图区域坐标
        """
        # 如果提供了游戏窗口信息，先验证窗口坐标是否有效
        if all(param is not None for param in [game_window_left, game_window_top, game_window_width, game_window_height]):
            # 验证窗口坐标是否有效（检查是否为最小化窗口的特殊坐标）
            if self._is_valid_window_coordinates(game_window_left, game_window_top, game_window_width, game_window_height):
                print(f"[ENHANCED_DETECTION] 使用有效的游戏窗口坐标")
                return self.get_game_window_center_region(game_window_left, game_window_top, game_window_width, game_window_height)
            else:
                print(f"[ENHANCED_DETECTION] ⚠️ 检测到无效的游戏窗口坐标，回退到屏幕中心")
                print(f"[ENHANCED_DETECTION] 无效坐标: ({game_window_left}, {game_window_top}) {game_window_width}x{game_window_height}")
                # 窗口坐标无效时，回退到屏幕中心
                return self.get_screen_center_region()
        else:
            # 否则使用屏幕中心
            print(f"[ENHANCED_DETECTION] 未提供游戏窗口信息，使用屏幕中心")
            return self.get_screen_center_region()
    
    def get_screen_center_region(self) -> Tuple[int, int, int, int]:
        """
        计算屏幕中央320x320区域 - 改进版，确保精确居中
        
        Returns:
            tuple: (left, top, right, bottom) 屏幕中央320x320区域坐标
        """
        # 获取屏幕分辨率
        try:
            import win32api
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
        except ImportError:
            # 如果win32api不可用，使用默认分辨率
            screen_width = 1920
            screen_height = 1080
            print("[WARNING] 无法获取屏幕分辨率，使用默认值 1920x1080")
        
        # 🔧 改进：精确计算屏幕中心
        screen_center_x = screen_width // 2
        screen_center_y = screen_height // 2
        
        # 🔧 改进：精确计算320x320区域的边界，确保完美居中
        half_capture = self.CAPTURE_SIZE // 2  # 320 // 2 = 160
        
        left = screen_center_x - half_capture
        top = screen_center_y - half_capture
        right = left + self.CAPTURE_SIZE
        bottom = top + self.CAPTURE_SIZE
        
        # 🔧 新增：边界检查，确保不超出屏幕范围
        if left < 0:
            left = 0
            right = self.CAPTURE_SIZE
            print(f"[WARNING] 截图区域左边界调整: left={left}")
        elif right > screen_width:
            right = screen_width
            left = screen_width - self.CAPTURE_SIZE
            print(f"[WARNING] 截图区域右边界调整: right={right}")
            
        if top < 0:
            top = 0
            bottom = self.CAPTURE_SIZE
            print(f"[WARNING] 截图区域上边界调整: top={top}")
        elif bottom > screen_height:
            bottom = screen_height
            top = screen_height - self.CAPTURE_SIZE
            print(f"[WARNING] 截图区域下边界调整: bottom={bottom}")
        
        print(f"[ENHANCED_DETECTION] 屏幕分辨率: {screen_width}x{screen_height}")
        print(f"[ENHANCED_DETECTION] 屏幕中心: ({screen_center_x}, {screen_center_y})")
        print(f"[ENHANCED_DETECTION] 截取区域: ({left}, {top}, {right}, {bottom})")
        print(f"[ENHANCED_DETECTION] 区域大小: {self.CAPTURE_SIZE}x{self.CAPTURE_SIZE}")
        
        # 🔧 新增：验证区域中心是否与屏幕中心一致
        actual_region_center_x = left + self.CAPTURE_SIZE // 2
        actual_region_center_y = top + self.CAPTURE_SIZE // 2
        offset_x = actual_region_center_x - screen_center_x
        offset_y = actual_region_center_y - screen_center_y
        
        print(f"[ENHANCED_DETECTION] 实际区域中心: ({actual_region_center_x}, {actual_region_center_y})")
        print(f"[ENHANCED_DETECTION] 与屏幕中心偏差: ({offset_x}, {offset_y}) 像素")
        
        if abs(offset_x) <= 1 and abs(offset_y) <= 1:
            print(f"[ENHANCED_DETECTION] ✅ 截图区域完美居中")
        else:
            print(f"[ENHANCED_DETECTION] ⚠️ 截图区域存在 {abs(offset_x) + abs(offset_y)} 像素偏差")
        
        return (left, top, right, bottom)
    
    def _is_valid_window_coordinates(self, left: int, top: int, width: int, height: int) -> bool:
        """
        验证窗口坐标是否有效
        
        Args:
            left: 窗口左边界
            top: 窗口上边界
            width: 窗口宽度
            height: 窗口高度
            
        Returns:
            bool: 窗口坐标是否有效
        """
        # Windows 系统中最小化窗口的特殊坐标
        MINIMIZED_WINDOW_COORDS = [-32000, -32768]
        
        # 检查是否为最小化窗口的特殊坐标
        if left in MINIMIZED_WINDOW_COORDS or top in MINIMIZED_WINDOW_COORDS:
            print(f"[ENHANCED_DETECTION] 检测到最小化窗口坐标: ({left}, {top})")
            return False
        
        # 检查窗口尺寸是否合理
        if width <= 0 or height <= 0:
            print(f"[ENHANCED_DETECTION] 检测到无效窗口尺寸: {width}x{height}")
            return False
        
        # 检查窗口尺寸是否过小（可能是隐藏或异常窗口）
        MIN_WINDOW_SIZE = 100
        if width < MIN_WINDOW_SIZE or height < MIN_WINDOW_SIZE:
            print(f"[ENHANCED_DETECTION] 检测到过小窗口尺寸: {width}x{height} (最小: {MIN_WINDOW_SIZE})")
            return False
        
        # 检查窗口坐标是否在合理范围内（考虑多显示器）
        # 允许负坐标（多显示器环境），但不能太极端
        EXTREME_COORD_THRESHOLD = 10000
        if abs(left) > EXTREME_COORD_THRESHOLD or abs(top) > EXTREME_COORD_THRESHOLD:
            print(f"[ENHANCED_DETECTION] 检测到极端窗口坐标: ({left}, {top})")
            return False
        
        print(f"[ENHANCED_DETECTION] 窗口坐标验证通过: ({left}, {top}) {width}x{height}")
        return True

    def get_game_window_center_region(self, game_window_left: int, game_window_top: int, 
                                    game_window_width: int, game_window_height: int) -> Tuple[int, int, int, int]:
        """
        基于游戏窗口中心计算320x320截图区域
        
        Args:
            game_window_left: 游戏窗口左边界
            game_window_top: 游戏窗口上边界
            game_window_width: 游戏窗口宽度
            game_window_height: 游戏窗口高度
            
        Returns:
            tuple: (left, top, right, bottom) 基于游戏窗口中心的320x320区域坐标
        """
        # 计算游戏窗口中心
        game_center_x = game_window_left + game_window_width // 2
        game_center_y = game_window_top + game_window_height // 2
        
        # 计算320x320区域的边界
        half_capture = self.CAPTURE_SIZE // 2  # 320 // 2 = 160
        
        left = game_center_x - half_capture
        top = game_center_y - half_capture
        right = left + self.CAPTURE_SIZE
        bottom = top + self.CAPTURE_SIZE
        
        print(f"[ENHANCED_DETECTION] 游戏窗口: ({game_window_left}, {game_window_top}) {game_window_width}x{game_window_height}")
        print(f"[ENHANCED_DETECTION] 游戏窗口中心: ({game_center_x}, {game_center_y})")
        print(f"[ENHANCED_DETECTION] 截取区域: ({left}, {top}, {right}, {bottom})")
        print(f"[ENHANCED_DETECTION] 区域大小: {self.CAPTURE_SIZE}x{self.CAPTURE_SIZE}")
        
        return (left, top, right, bottom)
    
    def resize_for_model(self, captured_image: np.ndarray) -> np.ndarray:
        """
        将截取的大图像缩放到模型输入尺寸
        
        Args:
            captured_image: 截取的原始图像 (CAPTURE_SIZE x CAPTURE_SIZE)
            
        Returns:
            np.ndarray: 缩放后的图像 (MODEL_INPUT_SIZE x MODEL_INPUT_SIZE)
        """
        if captured_image.shape[:2] == (self.MODEL_INPUT_SIZE, self.MODEL_INPUT_SIZE):
            return captured_image
        
        # 使用高质量的双线性插值进行缩放
        resized = cv2.resize(
            captured_image, 
            (self.MODEL_INPUT_SIZE, self.MODEL_INPUT_SIZE), 
            interpolation=cv2.INTER_LINEAR
        )
        
        return resized
    
    def scale_coordinates_to_capture(self, model_x: float, model_y: float) -> Tuple[float, float]:
        """
        将模型输出的坐标缩放到原始截取区域坐标
        
        Args:
            model_x: 模型输出的X坐标 (0-MODEL_INPUT_SIZE)
            model_y: 模型输出的Y坐标 (0-MODEL_INPUT_SIZE)
            
        Returns:
            tuple: 缩放到截取区域的坐标 (0-CAPTURE_SIZE)
        """
        scaled_x = model_x * self.SCALE_FACTOR
        scaled_y = model_y * self.SCALE_FACTOR
        
        return (scaled_x, scaled_y)
    
    def scale_coordinates_to_model(self, capture_x: float, capture_y: float) -> Tuple[float, float]:
        """
        将截取区域坐标缩放到模型输入坐标
        
        Args:
            capture_x: 截取区域的X坐标 (0-CAPTURE_SIZE)
            capture_y: 截取区域的Y坐标 (0-CAPTURE_SIZE)
            
        Returns:
            tuple: 缩放到模型输入的坐标 (0-MODEL_INPUT_SIZE)
        """
        model_x = capture_x / self.SCALE_FACTOR
        model_y = capture_y / self.SCALE_FACTOR
        
        return (model_x, model_y)
    
    def get_capture_center(self) -> Tuple[float, float]:
        """
        获取截取区域的中心坐标
        
        Returns:
            tuple: 中心坐标 (capture_size/2, capture_size/2)
        """
        center = self.CAPTURE_SIZE / 2
        return (center, center)
    
    def get_model_center(self) -> Tuple[float, float]:
        """
        获取模型输入的中心坐标
        
        Returns:
            tuple: 中心坐标 (model_size/2, model_size/2)
        """
        center = self.MODEL_INPUT_SIZE / 2
        return (center, center)
    
    def calculate_mouse_movement(self, head_x: float, head_y: float, 
                               crosshair_x: float, crosshair_y: float) -> Tuple[float, float]:
        """
        计算鼠标移动量（基于截取区域坐标）
        
        Args:
            head_x: 头部X坐标（截取区域坐标系）
            head_y: 头部Y坐标（截取区域坐标系）
            crosshair_x: 准星X坐标（截取区域坐标系）
            crosshair_y: 准星Y坐标（截取区域坐标系）
            
        Returns:
            tuple: 鼠标移动量 (move_x, move_y)
        """
        move_x = head_x - crosshair_x
        move_y = head_y - crosshair_y
        
        return (move_x, move_y)
    
    def debug_coordinates(self, model_x: float, model_y: float):
        """
        调试坐标转换
        
        Args:
            model_x: 模型输出的X坐标
            model_y: 模型输出的Y坐标
        """
        capture_x, capture_y = self.scale_coordinates_to_capture(model_x, model_y)
        
        print(f"[COORD_DEBUG] 坐标转换:")
        print(f"  - 模型坐标: ({model_x:.1f}, {model_y:.1f})")
        print(f"  - 截取区域坐标: ({capture_x:.1f}, {capture_y:.1f})")
        print(f"  - 缩放比例: {self.SCALE_FACTOR:.2f}")
    
    def update_enhancement_factor(self, new_factor: float):
        """
        动态更新增强倍数
        
        Args:
            new_factor: 新的增强倍数
        """
        self.ENHANCEMENT_FACTOR = new_factor
        self.CAPTURE_SIZE = int(self.BASE_CAPTURE_SIZE * self.ENHANCEMENT_FACTOR)
        self.SCALE_FACTOR = self.CAPTURE_SIZE / self.MODEL_INPUT_SIZE
        
        print(f"[ENHANCED_DETECTION] 配置已更新:")
        print(f"  - 新增强倍数: {self.ENHANCEMENT_FACTOR}")
        print(f"  - 新截取区域尺寸: {self.CAPTURE_SIZE}x{self.CAPTURE_SIZE}")
        print(f"  - 新缩放比例: {self.SCALE_FACTOR:.2f}")
    
    def get_config_info(self) -> dict:
        """
        获取当前配置信息
        
        Returns:
            dict: 配置信息字典
        """
        return {
            'base_capture_size': self.BASE_CAPTURE_SIZE,
            'enhancement_factor': self.ENHANCEMENT_FACTOR,
            'capture_size': self.CAPTURE_SIZE,
            'model_input_size': self.MODEL_INPUT_SIZE,
            'scale_factor': self.SCALE_FACTOR
        }

# 全局实例 - 现在会自动适配config.py中的设置
enhanced_detection = EnhancedDetectionConfig()

def get_enhanced_detection_config():
    """获取增强检测配置实例"""
    return enhanced_detection

if __name__ == "__main__":
    # 测试配置
    config = EnhancedDetectionConfig()
    
    # 测试坐标转换
    print("\n=== 坐标转换测试 ===")
    
    # 模型输出的中心点
    model_center_x, model_center_y = config.get_model_center()
    print(f"模型中心: ({model_center_x}, {model_center_y})")
    
    # 转换到截取区域坐标
    capture_center_x, capture_center_y = config.scale_coordinates_to_capture(model_center_x, model_center_y)
    print(f"截取区域中心: ({capture_center_x}, {capture_center_y})")
    
    # 测试边角坐标
    test_coords = [(0, 0), (320, 0), (0, 320), (320, 320)]
    for mx, my in test_coords:
        cx, cy = config.scale_coordinates_to_capture(mx, my)
        print(f"模型({mx}, {my}) -> 截取区域({cx:.1f}, {cy:.1f})")
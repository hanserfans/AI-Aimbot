#!/usr/bin/env python3
"""
检查display_img实际尺寸的简单脚本
"""

import cv2
import numpy as np
from enhanced_detection_config import EnhancedDetectionConfig
from config import screenShotHeight, screenShotWidth

def check_display_img_size():
    """检查display_img的实际尺寸"""
    print("=== Display Image尺寸检查 ===")
    
    # 初始化增强检测配置
    enhanced_config = EnhancedDetectionConfig()
    print(f"增强检测配置:")
    print(f"  - CAPTURE_SIZE: {enhanced_config.CAPTURE_SIZE}")
    print(f"  - BASE_CAPTURE_SIZE: {enhanced_config.BASE_CAPTURE_SIZE}")
    print(f"  - ENHANCEMENT_FACTOR: {enhanced_config.ENHANCEMENT_FACTOR}")
    
    print(f"\n基础配置:")
    print(f"  - screenShotHeight: {screenShotHeight}")
    print(f"  - screenShotWidth: {screenShotWidth}")
    
    # 获取截图区域
    capture_region = enhanced_config.get_capture_region()
    print(f"\n截图区域: {capture_region}")
    
    # 计算实际截图尺寸
    # capture_region 是 (left, top, right, bottom) 格式
    left, top, right, bottom = capture_region
    actual_width = right - left
    actual_height = bottom - top
    print(f"实际截图尺寸: {actual_width}x{actual_height}")
    
    # 模拟display_img的创建过程
    print(f"\n=== 模拟display_img创建 ===")
    
    # 创建一个模拟的截图（与实际尺寸相同）
    mock_screenshot = np.zeros((actual_height, actual_width, 3), dtype=np.uint8)
    print(f"模拟截图尺寸: {mock_screenshot.shape[1]}x{mock_screenshot.shape[0]}")
    
    # 模拟display_img = npImg.copy()
    display_img = mock_screenshot.copy()
    print(f"display_img尺寸: {display_img.shape[1]}x{display_img.shape[0]}")
    
    # 检查是否与CAPTURE_SIZE匹配
    if display_img.shape[0] == enhanced_config.CAPTURE_SIZE and display_img.shape[1] == enhanced_config.CAPTURE_SIZE:
        print("✅ display_img尺寸与CAPTURE_SIZE匹配！")
    else:
        print("❌ display_img尺寸与CAPTURE_SIZE不匹配！")
        print(f"   display_img: {display_img.shape[1]}x{display_img.shape[0]}")
        print(f"   CAPTURE_SIZE: {enhanced_config.CAPTURE_SIZE}x{enhanced_config.CAPTURE_SIZE}")
    
    # 检查Live Feed应该显示的尺寸
    print(f"\n=== Live Feed显示尺寸分析 ===")
    live_display_img = display_img.copy()
    display_height, display_width = live_display_img.shape[:2]
    print(f"Live Feed显示尺寸: {display_width}x{display_height}")
    
    if display_width == 640 and display_height == 640:
        print("✅ Live Feed应该以640x640显示")
    else:
        print(f"❌ Live Feed显示尺寸异常: {display_width}x{display_height}")

if __name__ == "__main__":
    check_display_img_size()
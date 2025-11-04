#!/usr/bin/env python3
"""
实际Live Feed诊断脚本
检查真实运行时的截图区域和显示问题
"""

import cv2
import numpy as np
import time
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_detection_config import EnhancedDetectionConfig
from screenshot_optimizer import ScreenshotOptimizer

# 尝试导入截图库
try:
    import bettercam
    BETTERCAM_AVAILABLE = True
except ImportError:
    BETTERCAM_AVAILABLE = False

try:
    import dxcam
    DXCAM_AVAILABLE = True
except ImportError:
    DXCAM_AVAILABLE = False

def create_test_camera(region):
    """创建测试用的相机"""
    print(f"📷 创建测试相机，区域: {region}")
    
    # 尝试使用DXCam
    if DXCAM_AVAILABLE:
        try:
            camera = dxcam.create(region=region, output_color="BGR")
            if camera.start():
                print("✅ DXCam相机创建成功")
                return camera, "dxcam"
        except Exception as e:
            print(f"❌ DXCam创建失败: {e}")
    
    # 尝试使用BetterCam
    if BETTERCAM_AVAILABLE:
        try:
            camera = bettercam.create(region=region, output_color="BGR")
            if camera:
                print("✅ BetterCam相机创建成功")
                return camera, "bettercam"
        except Exception as e:
            print(f"❌ BetterCam创建失败: {e}")
    
    print("❌ 无法创建任何相机")
    return None, None

def diagnose_live_feed_real():
    """诊断实际的Live Feed问题"""
    print("🔍 实际Live Feed诊断")
    print("=" * 60)
    
    # 初始化增强检测配置
    enhanced_config = EnhancedDetectionConfig()
    
    # 获取截图区域
    region = enhanced_config.get_capture_region()
    left, top, right, bottom = region
    region_width = right - left
    region_height = bottom - top
    
    print(f"📸 截图区域配置:")
    print(f"  区域坐标: {region}")
    print(f"  区域大小: {region_width}x{region_height}")
    
    # 创建相机
    camera, camera_type = create_test_camera(region)
    if camera is None:
        print("❌ 无法创建相机，诊断终止")
        return
    
    # 创建截图优化器
    screenshot_optimizer = ScreenshotOptimizer(camera, camera_type)
    
    print(f"\n🎯 开始实际截图测试...")
    
    # 捕获几帧进行分析
    for i in range(5):
        print(f"\n--- 第 {i+1} 帧 ---")
        
        # 获取原始帧
        npImg = screenshot_optimizer.get_optimized_frame(use_cache=False)
        if npImg is None:
            print("❌ 无法获取帧")
            continue
        
        print(f"原始帧尺寸: {npImg.shape}")
        
        # 创建显示图像（模拟主程序逻辑）
        display_img = npImg.copy()
        
        # 检查图像内容
        mean_color = np.mean(display_img, axis=(0, 1))
        print(f"平均颜色 (BGR): {mean_color}")
        
        # 检查是否为黑色图像
        if np.all(mean_color < 10):
            print("⚠️ 警告：图像几乎全黑，可能截图区域有问题")
        
        # 保存原始截图用于分析
        cv2.imwrite(f"debug_frame_{i+1}_original.png", display_img)
        print(f"✅ 保存原始截图: debug_frame_{i+1}_original.png")
        
        # 模拟主程序的显示逻辑
        display_height, display_width = display_img.shape[:2]
        target_display_size = enhanced_config.CAPTURE_SIZE  # 640
        
        print(f"显示逻辑:")
        print(f"  原始尺寸: {display_width}x{display_height}")
        print(f"  目标尺寸: {target_display_size}x{target_display_size}")
        
        if display_height != target_display_size or display_width != target_display_size:
            display_img_resized = cv2.resize(display_img, (target_display_size, target_display_size), interpolation=cv2.INTER_LINEAR)
            print(f"  需要缩放: {display_width}x{display_height} -> {target_display_size}x{target_display_size}")
            
            # 保存缩放后的图像
            cv2.imwrite(f"debug_frame_{i+1}_resized.png", display_img_resized)
            print(f"  保存缩放图像: debug_frame_{i+1}_resized.png")
            
            # 显示缩放后的图像
            cv2.imshow('Live Feed - Resized', display_img_resized)
        else:
            print(f"  直接显示: {display_width}x{display_height}")
            cv2.imshow('Live Feed - Direct', display_img)
        
        # 短暂显示
        cv2.waitKey(500)
        
        time.sleep(0.1)
    
    # 清理
    cv2.destroyAllWindows()
    if hasattr(camera, 'stop'):
        camera.stop()
    
    print(f"\n📊 诊断总结:")
    print(f"1. 截图区域: {region_width}x{region_height} at ({left}, {top})")
    print(f"2. 相机类型: {camera_type}")
    print(f"3. 检查生成的debug_frame_*.png文件来验证截图内容")
    print(f"4. 如果图像全黑或显示错误区域，说明截图区域配置有问题")
    print(f"5. 如果图像模糊，可能是缩放导致的")
    
    # 额外的区域验证
    print(f"\n🎯 区域验证:")
    
    # 获取屏幕分辨率
    import tkinter as tk
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    
    # 计算区域中心
    center_x = left + region_width // 2
    center_y = top + region_height // 2
    expected_center_x = screen_width // 2
    expected_center_y = screen_height // 2
    
    print(f"屏幕分辨率: {screen_width}x{screen_height}")
    print(f"屏幕中心: ({expected_center_x}, {expected_center_y})")
    print(f"截图区域中心: ({center_x}, {center_y})")
    print(f"偏移量: ({center_x - expected_center_x}, {center_y - expected_center_y})")
    
    if abs(center_x - expected_center_x) <= 1 and abs(center_y - expected_center_y) <= 1:
        print("✅ 截图区域正确居中")
    else:
        print("❌ 截图区域未正确居中")
        
    # 检查区域是否超出屏幕边界
    if left < 0 or top < 0 or right > screen_width or bottom > screen_height:
        print("❌ 警告：截图区域超出屏幕边界")
        print(f"   区域: ({left}, {top}, {right}, {bottom})")
        print(f"   屏幕: (0, 0, {screen_width}, {screen_height})")
    else:
        print("✅ 截图区域在屏幕边界内")

if __name__ == "__main__":
    diagnose_live_feed_real()
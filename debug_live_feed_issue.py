#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Feed显示问题调试脚本
验证截图区域和Live Feed显示的一致性
"""

import cv2
import numpy as np
import time
import dxcam
import win32api
from enhanced_detection_config import get_enhanced_detection_config

def debug_live_feed_issue():
    """调试Live Feed显示问题"""
    print("🔍 Live Feed显示问题调试")
    print("=" * 60)
    
    # 获取屏幕分辨率
    screen_width = win32api.GetSystemMetrics(0)
    screen_height = win32api.GetSystemMetrics(1)
    print(f"屏幕分辨率: {screen_width}x{screen_height}")
    
    # 获取增强检测配置
    enhanced_config = get_enhanced_detection_config()
    
    # 计算截图区域
    left, top, right, bottom = enhanced_config.get_screen_center_region()
    capture_width = right - left
    capture_height = bottom - top
    
    print(f"\n📸 截图区域配置:")
    print(f"  区域坐标: ({left}, {top}, {right}, {bottom})")
    print(f"  区域大小: {capture_width}x{capture_height}")
    print(f"  屏幕中心: ({screen_width//2}, {screen_height//2})")
    
    # 验证区域是否在屏幕中心
    expected_center_x = screen_width // 2
    expected_center_y = screen_height // 2
    actual_center_x = (left + right) // 2
    actual_center_y = (top + bottom) // 2
    
    center_offset_x = abs(actual_center_x - expected_center_x)
    center_offset_y = abs(actual_center_y - expected_center_y)
    
    print(f"\n🎯 中心点验证:")
    print(f"  预期中心: ({expected_center_x}, {expected_center_y})")
    print(f"  实际中心: ({actual_center_x}, {actual_center_y})")
    print(f"  偏移量: ({center_offset_x}, {center_offset_y})")
    
    if center_offset_x <= 1 and center_offset_y <= 1:
        print("  ✅ 截图区域正确居中")
    else:
        print("  ❌ 截图区域未正确居中")
    
    # 创建DXCam相机
    print(f"\n📷 创建DXCam相机...")
    try:
        camera = dxcam.create(region=(left, top, right, bottom), output_color="BGR")
        if camera is None:
            print("❌ 无法创建DXCam相机")
            return
        
        print("✅ DXCam相机创建成功")
        
        # 启动相机
        if not camera.start():
            print("❌ 无法启动DXCam相机")
            return
        
        print("✅ DXCam相机启动成功")
        
        # 测试截图
        print(f"\n🖼️ 测试截图...")
        
        frame_count = 0
        start_time = time.time()
        
        # 创建窗口
        cv2.namedWindow('Debug Live Feed', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Debug Live Feed', 640, 640)
        
        # 在屏幕上绘制参考线（帮助验证截图区域）
        print(f"\n📐 绘制屏幕参考线...")
        print(f"  请观察Live Feed窗口是否显示屏幕中心区域")
        print(f"  按 'q' 键退出，按 's' 键保存当前帧")
        
        while True:
            # 获取截图
            frame = camera.grab()
            if frame is None:
                print("⚠️ 获取帧失败")
                time.sleep(0.01)
                continue
            
            frame_count += 1
            
            # 检查帧尺寸
            frame_height, frame_width = frame.shape[:2]
            if frame_count == 1:
                print(f"  首帧尺寸: {frame_width}x{frame_height}")
                if frame_width != 640 or frame_height != 640:
                    print(f"  ⚠️ 帧尺寸不是640x640！")
            
            # 在帧上绘制调试信息
            debug_frame = frame.copy()
            
            # 绘制中心十字线
            center_x, center_y = frame_width // 2, frame_height // 2
            cv2.line(debug_frame, (center_x - 50, center_y), (center_x + 50, center_y), (0, 255, 0), 2)
            cv2.line(debug_frame, (center_x, center_y - 50), (center_x, center_y + 50), (0, 255, 0), 2)
            
            # 绘制边框
            cv2.rectangle(debug_frame, (5, 5), (frame_width - 5, frame_height - 5), (255, 0, 0), 2)
            
            # 添加文本信息
            cv2.putText(debug_frame, f"Frame: {frame_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(debug_frame, f"Size: {frame_width}x{frame_height}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(debug_frame, f"Region: ({left},{top},{right},{bottom})", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(debug_frame, "Press 'q' to quit, 's' to save", (10, frame_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # 显示帧
            cv2.imshow('Debug Live Feed', debug_frame)
            
            # 检查按键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # 保存当前帧
                timestamp = int(time.time())
                filename = f"debug_frame_{timestamp}.png"
                cv2.imwrite(filename, debug_frame)
                print(f"  💾 已保存帧: {filename}")
            
            # 计算FPS
            if frame_count % 60 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                print(f"  📊 FPS: {fps:.1f}, 帧数: {frame_count}")
        
        # 清理
        camera.stop()
        cv2.destroyAllWindows()
        
        print(f"\n📊 测试完成:")
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed
        print(f"  总帧数: {frame_count}")
        print(f"  总时间: {elapsed:.1f}秒")
        print(f"  平均FPS: {avg_fps:.1f}")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

def compare_with_full_screen():
    """对比全屏截图和区域截图"""
    print(f"\n🔄 对比全屏截图和区域截图")
    print("=" * 60)
    
    # 获取屏幕分辨率
    screen_width = win32api.GetSystemMetrics(0)
    screen_height = win32api.GetSystemMetrics(1)
    
    # 获取增强检测配置
    enhanced_config = get_enhanced_detection_config()
    left, top, right, bottom = enhanced_config.get_screen_center_region()
    
    try:
        # 创建全屏相机
        full_camera = dxcam.create(output_color="BGR")
        full_camera.start()
        
        # 创建区域相机
        region_camera = dxcam.create(region=(left, top, right, bottom), output_color="BGR")
        region_camera.start()
        
        print("✅ 两个相机创建成功")
        
        # 获取一帧进行对比
        full_frame = full_camera.grab()
        region_frame = region_camera.grab()
        
        if full_frame is not None and region_frame is not None:
            # 从全屏截图中提取对应区域
            extracted_region = full_frame[top:bottom, left:right]
            
            print(f"全屏截图尺寸: {full_frame.shape}")
            print(f"区域截图尺寸: {region_frame.shape}")
            print(f"提取区域尺寸: {extracted_region.shape}")
            
            # 保存对比图像
            timestamp = int(time.time())
            cv2.imwrite(f"full_screen_{timestamp}.png", full_frame)
            cv2.imwrite(f"region_capture_{timestamp}.png", region_frame)
            cv2.imwrite(f"extracted_region_{timestamp}.png", extracted_region)
            
            # 计算差异
            if extracted_region.shape == region_frame.shape:
                diff = cv2.absdiff(extracted_region, region_frame)
                max_diff = np.max(diff)
                mean_diff = np.mean(diff)
                
                print(f"图像差异统计:")
                print(f"  最大差异: {max_diff}")
                print(f"  平均差异: {mean_diff:.2f}")
                
                if max_diff < 5:
                    print("  ✅ 区域截图与全屏提取区域基本一致")
                else:
                    print("  ⚠️ 区域截图与全屏提取区域存在差异")
                
                cv2.imwrite(f"diff_image_{timestamp}.png", diff)
            
        # 清理
        full_camera.stop()
        region_camera.stop()
        
    except Exception as e:
        print(f"❌ 对比测试出错: {e}")

def main():
    """主函数"""
    print("🚀 Live Feed显示问题调试工具")
    print("=" * 60)
    
    try:
        debug_live_feed_issue()
        compare_with_full_screen()
        
        print(f"\n✅ 调试完成！")
        print("请检查生成的图像文件来验证截图区域是否正确")
        
    except Exception as e:
        print(f"❌ 调试过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
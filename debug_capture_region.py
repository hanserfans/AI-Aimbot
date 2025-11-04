#!/usr/bin/env python3
"""
调试截图区域和游戏窗口位置的脚本
"""

import win32api
import pygetwindow
from enhanced_detection_config import get_enhanced_detection_config

def debug_capture_region():
    """调试截图区域计算"""
    print("=== 屏幕和截图区域调试 ===")
    
    # 获取屏幕分辨率
    screen_width = win32api.GetSystemMetrics(0)
    screen_height = win32api.GetSystemMetrics(1)
    print(f"屏幕分辨率: {screen_width}x{screen_height}")
    print(f"屏幕中心: ({screen_width//2}, {screen_height//2})")
    
    # 获取增强检测配置
    enhanced_config = get_enhanced_detection_config()
    
    # 检查游戏窗口
    print(f"\n=== 游戏窗口检测 ===")
    game_window = None
    try:
        windows = pygetwindow.getAllWindows()
        game_windows = []
        
        for window in windows:
            if window.title and any(keyword in window.title.lower() for keyword in 
                                  ['valorant', 'counter-strike', 'cs2', 'csgo', 'apex', 'fortnite']):
                game_windows.append(window)
                game_window = window  # 使用找到的第一个游戏窗口
                print(f"找到游戏窗口: {window.title}")
                print(f"  位置: ({window.left}, {window.top})")
                print(f"  尺寸: {window.width}x{window.height}")
                print(f"  右下角: ({window.right}, {window.bottom})")
                print(f"  窗口中心: ({(window.left + window.right)//2}, {(window.top + window.bottom)//2})")
                
                # 检查窗口是否全屏
                if window.left == 0 and window.top == 0 and window.width == screen_width and window.height == screen_height:
                    print("  ✅ 窗口为全屏模式")
                else:
                    print("  ⚠️ 窗口不是全屏模式")
                break  # 只处理第一个找到的游戏窗口
        
        if not game_windows:
            print("未找到游戏窗口，显示所有窗口:")
            for window in windows[:10]:  # 只显示前10个窗口
                if window.title:
                    print(f"  {window.title}: ({window.left}, {window.top}) {window.width}x{window.height}")
                    
    except Exception as e:
        print(f"检测游戏窗口时出错: {e}")
    
    # 计算截图区域 - 分别测试屏幕中心和游戏窗口中心
    print(f"\n=== 截图区域对比测试 ===")
    
    # 1. 屏幕中心截图区域
    print("1. 屏幕中心截图区域:")
    left_screen, top_screen, right_screen, bottom_screen = enhanced_config.get_screen_center_region()
    print(f"   截图区域: ({left_screen}, {top_screen}, {right_screen}, {bottom_screen})")
    print(f"   区域中心: ({(left_screen + right_screen)//2}, {(top_screen + bottom_screen)//2})")
    
    # 2. 游戏窗口中心截图区域
    if game_window:
        print("2. 游戏窗口中心截图区域:")
        left_game, top_game, right_game, bottom_game = enhanced_config.get_capture_region(
            game_window.left, game_window.top, game_window.width, game_window.height
        )
        print(f"   截图区域: ({left_game}, {top_game}, {right_game}, {bottom_game})")
        print(f"   区域中心: ({(left_game + right_game)//2}, {(top_game + bottom_game)//2})")
        
        # 对比差异
        print("3. 差异分析:")
        diff_x = (left_game + right_game)//2 - (left_screen + right_screen)//2
        diff_y = (top_game + bottom_game)//2 - (top_screen + bottom_screen)//2
        print(f"   中心点差异: X轴 {diff_x} 像素, Y轴 {diff_y} 像素")
        
        if abs(diff_x) > 10 or abs(diff_y) > 10:
            print("   ⚠️ 截图区域中心与游戏窗口中心存在明显偏差！")
            print("   💡 建议：程序应该使用游戏窗口中心而不是屏幕中心")
        else:
            print("   ✅ 截图区域中心与游戏窗口中心基本一致")
    else:
        print("2. 无法测试游戏窗口中心截图区域（未找到游戏窗口）")
    
    # 显示最终使用的截图区域信息
    final_left, final_top, final_right, final_bottom = enhanced_config.get_capture_region(
        game_window.left if game_window else None,
        game_window.top if game_window else None, 
        game_window.width if game_window else None,
        game_window.height if game_window else None
    )
    
    capture_width = final_right - final_left
    capture_height = final_bottom - final_top
    
    print(f"\n=== 最终截图区域信息 ===")
    print(f"截图区域: ({final_left}, {final_top}, {final_right}, {final_bottom})")
    print(f"截图区域尺寸: {capture_width}x{capture_height}")
    print(f"截图区域中心: ({final_left + capture_width//2}, {final_top + capture_height//2})")
    
    # 在截图区域坐标系中的中心
    region_center_x = capture_width // 2
    region_center_y = capture_height // 2
    print(f"截图区域内坐标系中心: ({region_center_x}, {region_center_y})")
    
    print(f"\n=== 坐标系统说明 ===")
    print(f"1. 屏幕坐标系: (0,0) 到 ({screen_width},{screen_height})")
    print(f"2. 截图区域在屏幕中的位置: ({left},{top}) 到 ({right},{bottom})")
    print(f"3. 截图区域内坐标系: (0,0) 到 ({capture_width},{capture_height})")
    print(f"4. 模型输入坐标系: (0,0) 到 (320,320)")
    print(f"5. 准星应该在截图区域内坐标系的中心: ({region_center_x},{region_center_y})")

if __name__ == "__main__":
    debug_capture_region()
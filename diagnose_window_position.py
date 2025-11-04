#!/usr/bin/env python3
"""
窗口位置诊断工具
用于诊断和修复游戏窗口位置异常问题
"""

import pygetwindow
import time
from config import screenShotHeight, screenShotWidth

def diagnose_valorant_window():
    """诊断VALORANT窗口的位置和大小"""
    print("=== 窗口位置诊断工具 ===")
    
    # 获取所有窗口
    windows = pygetwindow.getAllWindows()
    
    # 查找VALORANT窗口
    valorant_windows = []
    for window in windows:
        if "VALORANT" in window.title.upper():
            valorant_windows.append(window)
    
    if not valorant_windows:
        print("[ERROR] 未找到VALORANT窗口！")
        print("请确保VALORANT正在运行")
        return None
    
    print(f"[INFO] 找到 {len(valorant_windows)} 个VALORANT窗口:")
    
    for i, window in enumerate(valorant_windows):
        print(f"\n--- 窗口 {i+1}: {window.title} ---")
        print(f"位置: left={window.left}, top={window.top}")
        print(f"大小: width={window.width}, height={window.height}")
        print(f"右下角: right={window.right}, bottom={window.bottom}")
        print(f"是否最小化: {window.isMinimized}")
        print(f"是否最大化: {window.isMaximized}")
        print(f"是否活动: {window.isActive}")
        
        # 计算截图区域
        left = ((window.left + window.right) // 2) - (screenShotWidth // 2)
        top = window.top + (window.height - screenShotHeight) // 2 + 18
        right = left + screenShotWidth
        bottom = top + screenShotHeight
        
        print(f"计算的截图区域: ({left}, {top}, {right}, {bottom})")
        
        # 检查是否有负坐标
        if left < 0 or top < 0 or right < 0 or bottom < 0:
            print("[WARNING] 检测到负坐标！这会导致屏幕捕获失败")
            
            # 提供修复建议
            print("\n[修复建议]:")
            if window.left < 0 or window.top < 0:
                print("1. 窗口位置异常，请尝试:")
                print("   - 将游戏窗口拖动到主显示器")
                print("   - 按 Win+Shift+左/右箭头 移动窗口到主显示器")
            
            if window.width < screenShotWidth or window.height < screenShotHeight:
                print("2. 窗口太小，请尝试:")
                print(f"   - 将游戏窗口调整为至少 {screenShotWidth}x{screenShotHeight} 像素")
                print("   - 或者在config.py中减小screenShotWidth和screenShotHeight的值")
        else:
            print("[OK] 坐标正常，应该可以正常工作")
    
    return valorant_windows[0] if valorant_windows else None

def fix_window_position(window):
    """尝试修复窗口位置"""
    print(f"\n=== 尝试修复窗口位置 ===")
    
    try:
        # 激活窗口
        print("正在激活窗口...")
        window.activate()
        time.sleep(1)
        
        # 如果窗口最小化，先恢复
        if window.isMinimized:
            print("窗口已最小化，正在恢复...")
            window.restore()
            time.sleep(1)
        
        # 尝试移动窗口到安全位置
        safe_left = max(0, window.left)
        safe_top = max(0, window.top)
        
        if window.left < 0 or window.top < 0:
            print(f"正在移动窗口到安全位置: ({safe_left}, {safe_top})")
            window.moveTo(safe_left, safe_top)
            time.sleep(1)
        
        # 重新检查位置
        print("修复后的窗口信息:")
        print(f"位置: left={window.left}, top={window.top}")
        print(f"大小: width={window.width}, height={window.height}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 修复失败: {e}")
        return False

def main():
    """主函数"""
    window = diagnose_valorant_window()
    
    if window is None:
        return
    
    # 检查是否需要修复
    if window.left < 0 or window.top < 0:
        user_input = input("\n是否尝试自动修复窗口位置? (y/n): ")
        if user_input.lower() == 'y':
            if fix_window_position(window):
                print("[SUCCESS] 窗口位置已修复，请重新运行aimbot")
            else:
                print("[ERROR] 自动修复失败，请手动调整窗口位置")
    
    print("\n=== 诊断完成 ===")
    print("如果问题仍然存在，请尝试:")
    print("1. 将VALORANT设置为窗口模式")
    print("2. 确保游戏窗口完全在主显示器内")
    print("3. 以管理员权限运行aimbot")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
angle_to_mouse_factor 校准工具
用于测试和调整最佳的角度到鼠标移动转换系数
"""

import time
import win32api
import win32con
from mouse_driver.MouseMove import ghub_move

def test_factor(factor_value):
    """测试指定的factor值"""
    print(f"\n=== 测试 angle_to_mouse_factor = {factor_value} ===")
    print("请按照以下步骤测试：")
    print("1. 进入游戏训练场")
    print("2. 将准星对准屏幕中心的目标")
    print("3. 按 Enter 键开始测试移动")
    print("4. 观察鼠标移动是否准确")
    print("5. 按 'q' 退出测试")
    
    input("按 Enter 开始测试...")
    
    # 模拟1度的角度偏移
    test_angle = 1.0  # 1度偏移
    mouse_move = int(test_angle * factor_value)
    
    print(f"模拟1度偏移，鼠标移动: {mouse_move} 像素")
    
    while True:
        key = input("按 Enter 执行移动，输入 'q' 退出: ").lower()
        if key == 'q':
            break
        
        try:
            # 使用G-Hub移动鼠标
            ghub_move(mouse_move, 0)  # 只测试水平移动
            print(f"已移动鼠标 {mouse_move} 像素")
        except Exception as e:
            print(f"移动失败: {e}")

def calculate_optimal_factor():
    """计算最佳factor值"""
    print("\n=== 计算最佳 angle_to_mouse_factor ===")
    
    # 获取用户输入
    try:
        mouse_dpi = float(input("请输入你的鼠标DPI (例如: 1600): "))
        game_sens = float(input("请输入游戏内灵敏度 (例如: 0.2): "))
        game_fov = float(input("请输入游戏FOV (VALORANT默认103): ") or "103")
        
        # 计算有效DPI
        effective_dpi = mouse_dpi * game_sens
        
        # 基于经验公式计算
        # 这个公式基于360度转身需要的鼠标移动距离
        cm_per_360 = 2.54 * (360 / game_fov) * (1600 / effective_dpi)
        
        # 转换为angle_to_mouse_factor
        # 假设显示器DPI为96 (标准值)
        pixels_per_cm = 96 / 2.54  # 约37.8像素/厘米
        pixels_per_360 = cm_per_360 * pixels_per_cm
        factor = pixels_per_360 / 360  # 每度对应的像素数
        
        print(f"\n计算结果:")
        print(f"有效DPI: {effective_dpi}")
        print(f"360度转身距离: {cm_per_360:.2f} cm")
        print(f"建议的 angle_to_mouse_factor: {factor:.1f}")
        
        return factor
        
    except ValueError:
        print("输入错误，请输入有效数字")
        return None

def main():
    """主函数"""
    print("=== angle_to_mouse_factor 校准工具 ===")
    print("此工具帮助你找到最佳的角度转换系数")
    
    while True:
        print("\n选择操作:")
        print("1. 测试当前factor值 (18.0)")
        print("2. 测试自定义factor值")
        print("3. 计算推荐factor值")
        print("4. 退出")
        
        choice = input("请选择 (1-4): ").strip()
        
        if choice == '1':
            test_factor(18.0)
        elif choice == '2':
            try:
                custom_factor = float(input("请输入要测试的factor值: "))
                test_factor(custom_factor)
            except ValueError:
                print("请输入有效数字")
        elif choice == '3':
            optimal_factor = calculate_optimal_factor()
            if optimal_factor:
                test_choice = input(f"是否测试计算出的factor值 {optimal_factor:.1f}? (y/n): ").lower()
                if test_choice == 'y':
                    test_factor(optimal_factor)
        elif choice == '4':
            print("退出校准工具")
            break
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n校准工具已退出")
    except Exception as e:
        print(f"错误: {e}")
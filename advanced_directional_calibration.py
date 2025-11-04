#!/usr/bin/env python3
"""
高级方向校正因子分析工具
分析每个方向的移动特性，计算最优校正因子
"""

import time
import pyautogui
from mouse_driver.MouseMove import ghub_move, initialize_mouse

def analyze_directional_scaling():
    """分析各方向的缩放特性"""
    print("=== 高级方向移动分析 ===\n")
    
    # 初始化鼠标
    if not initialize_mouse():
        print("❌ G-Hub鼠标初始化失败")
        return
    
    print("✅ G-Hub鼠标初始化成功")
    
    # 测试用例：更精细的测试
    test_cases = [
        # 右移测试
        ("右移", [(5, 0), (10, 0), (15, 0), (20, 0), (25, 0), (30, 0)]),
        # 左移测试  
        ("左移", [(-5, 0), (-10, 0), (-15, 0), (-20, 0), (-25, 0), (-30, 0)]),
        # 下移测试
        ("下移", [(0, 5), (0, 10), (0, 15), (0, 20), (0, 25), (0, 30)]),
        # 上移测试
        ("上移", [(0, -5), (0, -10), (0, -15), (0, -20), (0, -25), (0, -30)]),
    ]
    
    direction_results = {}
    
    for direction, movements in test_cases:
        print(f"\n🎯 测试{direction}方向:")
        direction_data = []
        
        for dx, dy in movements:
            print(f"  测试移动: ({dx}, {dy})")
            
            # 记录初始位置
            start_pos = pyautogui.position()
            time.sleep(0.2)
            
            # 执行移动
            success = ghub_move(dx, dy)
            if not success:
                print("    ❌ 移动失败")
                continue
                
            time.sleep(0.2)
            
            # 记录结束位置
            end_pos = pyautogui.position()
            actual_dx = end_pos.x - start_pos.x
            actual_dy = end_pos.y - start_pos.y
            
            print(f"    实际移动: ({actual_dx}, {actual_dy})")
            
            # 计算缩放比例
            if dx != 0:
                scale_x = actual_dx / dx
                print(f"    X轴缩放比例: {scale_x:.3f}")
                direction_data.append(('x', dx, actual_dx, scale_x))
            
            if dy != 0:
                scale_y = actual_dy / dy
                print(f"    Y轴缩放比例: {scale_y:.3f}")
                direction_data.append(('y', dy, actual_dy, scale_y))
            
            # 移动到新位置准备下次测试
            pyautogui.moveTo(start_pos.x + 100, start_pos.y + 50)
            time.sleep(0.3)
        
        direction_results[direction] = direction_data
    
    # 分析结果
    print("\n" + "="*60)
    print("📊 方向缩放分析报告")
    print("="*60)
    
    correction_factors = {}
    
    for direction, data in direction_results.items():
        if not data:
            continue
            
        print(f"\n🎯 {direction}方向分析:")
        
        # 计算平均缩放比例
        scales = [scale for _, _, _, scale in data]
        avg_scale = sum(scales) / len(scales)
        
        # 计算标准差
        variance = sum((scale - avg_scale) ** 2 for scale in scales) / len(scales)
        std_dev = variance ** 0.5
        
        print(f"  平均缩放比例: {avg_scale:.3f}")
        print(f"  标准差: {std_dev:.3f}")
        print(f"  一致性: {'良好' if std_dev < 0.1 else '一般' if std_dev < 0.2 else '较差'}")
        
        # 计算建议的校正因子
        suggested_factor = 1.0 / avg_scale
        correction_factors[direction] = suggested_factor
        
        print(f"  建议校正因子: {suggested_factor:.3f}")
        
        # 显示详细数据
        print("  详细测试数据:")
        for axis, expected, actual, scale in data:
            print(f"    {axis}轴: {expected} → {actual} (比例: {scale:.3f})")
    
    # 计算综合校正因子
    print(f"\n🔧 校正因子建议:")
    
    # 分别计算X轴和Y轴的校正因子
    x_factors = []
    y_factors = []
    
    for direction, factor in correction_factors.items():
        if direction in ["右移", "左移"]:
            x_factors.append(factor)
        else:
            y_factors.append(factor)
    
    if x_factors:
        avg_x_factor = sum(x_factors) / len(x_factors)
        print(f"  X轴平均校正因子: {avg_x_factor:.3f}")
    
    if y_factors:
        avg_y_factor = sum(y_factors) / len(y_factors)
        print(f"  Y轴平均校正因子: {avg_y_factor:.3f}")
    
    # 计算总体校正因子
    all_factors = list(correction_factors.values())
    if all_factors:
        overall_factor = sum(all_factors) / len(all_factors)
        print(f"  总体校正因子: {overall_factor:.3f}")
        
        # 生成代码
        print(f"\n💻 建议的代码更新:")
        print(f"MOVEMENT_CORRECTION_FACTOR = {overall_factor:.2f}")
        
        # 保存到文件
        with open("optimized_correction_factor.py", "w", encoding="utf-8") as f:
            f.write(f"# 优化后的校正因子 - 基于方向移动分析\n")
            f.write(f"# 分析日期: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"MOVEMENT_CORRECTION_FACTOR = {overall_factor:.2f}\n\n")
            f.write(f"# 各方向详细分析:\n")
            for direction, factor in correction_factors.items():
                f.write(f"# {direction}: {factor:.3f}\n")
            if x_factors:
                f.write(f"# X轴平均: {avg_x_factor:.3f}\n")
            if y_factors:
                f.write(f"# Y轴平均: {avg_y_factor:.3f}\n")
        
        print(f"  校正因子已保存到: optimized_correction_factor.py")
        
        return overall_factor
    
    return None

if __name__ == "__main__":
    print("高级方向校正分析")
    print("这将进行更精细的方向移动测试")
    print("\n按Enter开始分析...")
    input()
    
    factor = analyze_directional_scaling()
    if factor:
        print(f"\n✅ 分析完成！建议使用校正因子: {factor:.2f}")
    else:
        print("\n❌ 分析失败，请检查G-Hub连接")
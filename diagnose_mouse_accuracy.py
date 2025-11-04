#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-Hub鼠标移动精度诊断和修复工具
"""

import time
import win32gui
from mouse_driver.MouseMove import ghub_move, initialize_mouse, close_mouse

def get_cursor_position():
    """获取当前鼠标位置"""
    return win32gui.GetCursorPos()

def test_movement_accuracy():
    """测试鼠标移动精度"""
    print("=== G-Hub鼠标移动精度诊断 ===\n")
    
    # 初始化鼠标
    if not initialize_mouse():
        print("❌ G-Hub鼠标初始化失败")
        return False
    
    print("✅ G-Hub鼠标初始化成功")
    time.sleep(0.5)
    
    # 获取初始位置
    initial_pos = get_cursor_position()
    print(f"初始位置: {initial_pos}")
    
    # 测试用例
    test_cases = [
        (1, 0, "向右移动1像素"),
        (0, 1, "向下移动1像素"),
        (-1, 0, "向左移动1像素"),
        (0, -1, "向上移动1像素"),
        (5, 5, "对角移动5像素"),
        (10, 0, "向右移动10像素"),
        (0, 10, "向下移动10像素"),
        (-10, -10, "对角移动-10像素"),
    ]
    
    results = []
    
    for dx, dy, description in test_cases:
        print(f"\n测试: {description}")
        print(f"  期望移动: ({dx}, {dy})")
        
        # 记录移动前位置
        before_pos = get_cursor_position()
        
        # 执行移动
        success = ghub_move(dx, dy)
        time.sleep(0.1)  # 等待移动完成
        
        # 记录移动后位置
        after_pos = get_cursor_position()
        
        # 计算实际移动量
        actual_dx = after_pos[0] - before_pos[0]
        actual_dy = after_pos[1] - before_pos[1]
        
        print(f"  实际移动: ({actual_dx}, {actual_dy})")
        
        # 计算误差
        error_x = abs(actual_dx - dx)
        error_y = abs(actual_dy - dy)
        total_error = error_x + error_y
        
        print(f"  误差: X={error_x}, Y={error_y}, 总计={total_error}")
        
        # 计算放大倍数
        if dx != 0:
            scale_x = actual_dx / dx
            print(f"  X轴放大倍数: {scale_x:.2f}")
        if dy != 0:
            scale_y = actual_dy / dy
            print(f"  Y轴放大倍数: {scale_y:.2f}")
        
        results.append({
            'expected': (dx, dy),
            'actual': (actual_dx, actual_dy),
            'error': total_error,
            'description': description
        })
        
        if not success:
            print("  ❌ 移动失败")
        elif total_error <= 2:  # 允许2像素误差
            print("  ✅ 精度良好")
        else:
            print("  ⚠️ 精度有问题")
    
    # 分析结果
    print("\n=== 诊断结果分析 ===")
    
    total_tests = len(results)
    accurate_tests = sum(1 for r in results if r['error'] <= 2)
    
    print(f"总测试数: {total_tests}")
    print(f"精确测试数: {accurate_tests}")
    print(f"精度率: {accurate_tests/total_tests*100:.1f}%")
    
    # 计算平均放大倍数
    x_scales = []
    y_scales = []
    
    for i, (dx, dy, _) in enumerate(test_cases):
        actual_dx, actual_dy = results[i]['actual']
        if dx != 0:
            x_scales.append(actual_dx / dx)
        if dy != 0:
            y_scales.append(actual_dy / dy)
    
    if x_scales:
        avg_x_scale = sum(x_scales) / len(x_scales)
        print(f"平均X轴放大倍数: {avg_x_scale:.2f}")
    
    if y_scales:
        avg_y_scale = sum(y_scales) / len(y_scales)
        print(f"平均Y轴放大倍数: {avg_y_scale:.2f}")
    
    # 提供修复建议
    print("\n=== 修复建议 ===")
    
    if x_scales and y_scales:
        avg_scale = (sum(x_scales) + sum(y_scales)) / (len(x_scales) + len(y_scales))
        if abs(avg_scale - 1.0) > 0.1:
            correction_factor = 1.0 / avg_scale
            print(f"检测到放大倍数异常: {avg_scale:.2f}")
            print(f"建议校正因子: {correction_factor:.3f}")
            print(f"修复方法: 在移动前将坐标乘以 {correction_factor:.3f}")
            
            # 生成修复代码
            generate_fix_code(correction_factor)
        else:
            print("✅ 移动精度正常，无需修复")
    
    close_mouse()
    return True

def generate_fix_code(correction_factor):
    """生成修复代码"""
    print(f"\n=== 自动生成修复代码 ===")
    
    fix_code = f'''
# 在MouseMove.py中添加校正因子
MOVEMENT_CORRECTION_FACTOR = {correction_factor:.3f}

def move_mouse_corrected(self, x, y):
    """
    修正后的鼠标移动函数
    """
    # 应用校正因子
    corrected_x = int(x * MOVEMENT_CORRECTION_FACTOR)
    corrected_y = int(y * MOVEMENT_CORRECTION_FACTOR)
    
    # 调用原始移动函数
    return self.move_mouse(corrected_x, corrected_y)

# 全局函数版本
def ghub_move_corrected(x, y):
    """修正后的全局移动函数"""
    corrected_x = int(x * {correction_factor:.3f})
    corrected_y = int(y * {correction_factor:.3f})
    return ghub_move(corrected_x, corrected_y)
'''
    
    print(fix_code)
    
    # 保存修复代码到文件
    with open('mouse_movement_fix.py', 'w', encoding='utf-8') as f:
        f.write(fix_code)
    
    print("修复代码已保存到: mouse_movement_fix.py")

def test_dpi_sensitivity():
    """测试DPI和灵敏度设置"""
    print("\n=== DPI和灵敏度测试 ===")
    
    # 测试不同大小的移动
    test_distances = [1, 5, 10, 20, 50]
    
    for distance in test_distances:
        print(f"\n测试距离: {distance}像素")
        
        before_pos = get_cursor_position()
        ghub_move(distance, 0)
        time.sleep(0.1)
        after_pos = get_cursor_position()
        
        actual_distance = after_pos[0] - before_pos[0]
        ratio = actual_distance / distance if distance != 0 else 0
        
        print(f"  期望: {distance}, 实际: {actual_distance}, 比例: {ratio:.2f}")

if __name__ == "__main__":
    print("G-Hub鼠标移动精度诊断工具")
    print("=" * 40)
    
    try:
        test_movement_accuracy()
        test_dpi_sensitivity()
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
    finally:
        close_mouse()
        print("\n测试完成")
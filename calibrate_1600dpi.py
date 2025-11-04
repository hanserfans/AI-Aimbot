#!/usr/bin/env python3
"""
DPI 1600专用校准工具
为1600 DPI设置计算最佳的G-Hub鼠标校正因子
"""

import time
import pyautogui
from mouse_driver.MouseMove import MouseMove

def test_dpi_1600_accuracy():
    """测试1600 DPI下的鼠标移动精度"""
    print("=== DPI 1600 G-Hub鼠标精度校准 ===\n")
    
    # 初始化G-Hub鼠标
    mouse = MouseMove()
    if not mouse.initialized:
        print("❌ G-Hub鼠标初始化失败")
        return None
    
    print("✅ G-Hub鼠标初始化成功")
    
    # 测试不同的移动距离
    test_cases = [
        (5, 0),    # 右移5像素
        (10, 0),   # 右移10像素
        (20, 0),   # 右移20像素
        (0, 5),    # 下移5像素
        (0, 10),   # 下移10像素
        (0, 20),   # 下移20像素
        (10, 10),  # 对角移动10像素
        (20, 20),  # 对角移动20像素
    ]
    
    correction_factors = []
    
    for i, (dx, dy) in enumerate(test_cases):
        print(f"\n测试 {i+1}: 移动 ({dx}, {dy}) 像素")
        
        # 记录初始位置
        start_pos = pyautogui.position()
        print(f"  初始位置: {start_pos}")
        
        # 等待稳定
        time.sleep(0.5)
        
        # 执行移动
        mouse.move_mouse(dx, dy)
        time.sleep(0.2)
        
        # 记录结束位置
        end_pos = pyautogui.position()
        actual_dx = end_pos.x - start_pos.x
        actual_dy = end_pos.y - start_pos.y
        
        print(f"  结束位置: {end_pos}")
        print(f"  期望移动: ({dx}, {dy})")
        print(f"  实际移动: ({actual_dx}, {actual_dy})")
        
        # 计算校正因子
        if dx != 0:
            factor_x = dx / actual_dx if actual_dx != 0 else 1.0
            correction_factors.append(factor_x)
            print(f"  X轴校正因子: {factor_x:.3f}")
        
        if dy != 0:
            factor_y = dy / actual_dy if actual_dy != 0 else 1.0
            correction_factors.append(factor_y)
            print(f"  Y轴校正因子: {factor_y:.3f}")
        
        # 移动鼠标到新位置准备下次测试
        pyautogui.moveTo(start_pos.x + 100, start_pos.y)
        time.sleep(0.3)
    
    mouse.close()
    
    # 计算平均校正因子
    if correction_factors:
        avg_factor = sum(correction_factors) / len(correction_factors)
        print(f"\n=== 校准结果 ===")
        print(f"平均校正因子: {avg_factor:.3f}")
        print(f"建议的MOVEMENT_CORRECTION_FACTOR: {avg_factor:.2f}")
        
        # 生成校正代码
        correction_code = f"""
# DPI 1600专用校正因子
MOVEMENT_CORRECTION_FACTOR_1600DPI = {avg_factor:.2f}

def ghub_move_1600dpi(x, y):
    \"\"\"为1600 DPI优化的G-Hub鼠标移动函数\"\"\"
    corrected_x = int(x * MOVEMENT_CORRECTION_FACTOR_1600DPI)
    corrected_y = int(y * MOVEMENT_CORRECTION_FACTOR_1600DPI)
    return mouse_instance.move_mouse(corrected_x, corrected_y)
"""
        
        with open("dpi_1600_correction.py", "w", encoding="utf-8") as f:
            f.write(correction_code)
        
        print(f"\n✅ 校正代码已保存到 dpi_1600_correction.py")
        return avg_factor
    else:
        print("\n❌ 无法计算校正因子")
        return None

if __name__ == "__main__":
    print("请确保：")
    print("1. G-Hub软件已运行")
    print("2. DPI设置为1600")
    print("3. 鼠标敏感度为默认设置")
    print("\n按Enter开始校准...")
    input()
    
    factor = test_dpi_1600_accuracy()
    if factor:
        print(f"\n🎯 推荐将MouseMove.py中的MOVEMENT_CORRECTION_FACTOR设置为: {factor:.2f}")
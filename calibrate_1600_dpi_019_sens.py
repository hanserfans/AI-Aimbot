#!/usr/bin/env python3
"""
1600 DPI × 0.19 灵敏度专用校正因子测试和优化脚本
Calibration script specifically for 1600 DPI × 0.19 sensitivity setting
"""

import time
import math
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def calculate_effective_dpi(mouse_dpi, game_sensitivity):
    """计算有效DPI"""
    return mouse_dpi * game_sensitivity

def calculate_optimal_correction_factor(effective_dpi, base_dpi=1600):
    """
    根据有效DPI计算最优校正因子
    基于1600 DPI的基准校正因子0.62进行调整
    """
    base_correction = 0.62
    dpi_ratio = effective_dpi / base_dpi
    
    # 对于低eDPI，需要更大的校正因子来补偿
    if effective_dpi < 400:
        # 低eDPI需要更强的校正
        optimal_correction = base_correction * (1.0 + (1.0 - dpi_ratio) * 0.8)
    elif effective_dpi < 800:
        # 中等eDPI适度调整
        optimal_correction = base_correction * (1.0 + (1.0 - dpi_ratio) * 0.5)
    else:
        # 高eDPI使用标准校正
        optimal_correction = base_correction * dpi_ratio
    
    return round(optimal_correction, 3)

def test_movement_distances():
    """测试不同距离的移动效果"""
    print("🎯 移动距离测试")
    print("=" * 50)
    
    # 用户的DPI设置
    mouse_dpi = 1600
    game_sensitivity = 0.19
    effective_dpi = calculate_effective_dpi(mouse_dpi, game_sensitivity)
    
    print(f"鼠标DPI: {mouse_dpi}")
    print(f"游戏灵敏度: {game_sensitivity}")
    print(f"有效DPI (eDPI): {effective_dpi}")
    print()
    
    # 计算推荐的校正因子
    current_correction = 0.62  # 当前默认值
    optimal_correction = calculate_optimal_correction_factor(effective_dpi)
    
    print(f"当前校正因子: {current_correction}")
    print(f"推荐校正因子: {optimal_correction}")
    print(f"校正因子调整: {((optimal_correction / current_correction - 1) * 100):+.1f}%")
    print()
    
    # 测试不同距离的移动
    test_distances = [50, 100, 150, 200, 300, 400, 500]
    
    print("📏 移动距离分析:")
    print("-" * 50)
    
    for distance in test_distances:
        # 使用当前校正因子
        current_movement = distance * current_correction
        
        # 使用推荐校正因子
        optimal_movement = distance * optimal_correction
        
        # 考虑硬件限制（每步最大127像素）
        steps_needed = math.ceil(optimal_movement / 127)
        actual_per_step = optimal_movement / steps_needed if steps_needed > 0 else 0
        
        print(f"目标距离: {distance:3d}像素")
        print(f"  当前校正: {current_movement:6.1f}像素")
        print(f"  推荐校正: {optimal_movement:6.1f}像素")
        print(f"  需要步数: {steps_needed:2d}步")
        print(f"  每步移动: {actual_per_step:6.1f}像素")
        print()

def generate_optimized_config():
    """生成优化的配置建议"""
    mouse_dpi = 1600
    game_sensitivity = 0.19
    effective_dpi = calculate_effective_dpi(mouse_dpi, game_sensitivity)
    optimal_correction = calculate_optimal_correction_factor(effective_dpi)
    
    print("⚙️ 优化配置建议")
    print("=" * 50)
    
    config_text = f"""
# 针对 {mouse_dpi} DPI × {game_sensitivity} 灵敏度的优化配置

## 1. 鼠标驱动配置
MOVEMENT_CORRECTION_FACTOR = {optimal_correction}  # 优化后的校正因子

## 2. 移动系统配置
# 由于您的eDPI较低({effective_dpi})，建议使用以下设置：

# 最小步长（接近硬件上限以减少步数）
min_step_size = 120

# 步数计算优化（针对低eDPI）
def calculate_steps_for_low_edpi(distance):
    if distance <= 127:
        return 1
    elif distance <= 254:
        return 2
    else:
        return max(2, math.ceil(distance / 120))

## 3. 瞄准系统配置
# 低eDPI用户通常需要更精确的瞄准
headshot_precision_mode = True
micro_adjustment_threshold = 10.0  # 降低微调阈值

## 4. 性能优化
# 低eDPI需要更多移动步数，建议启用非阻塞移动
use_non_blocking_movement = True
movement_smoothing = True
"""
    
    print(config_text)
    
    # 保存配置到文件
    config_filename = f"dpi_{mouse_dpi}_sens_{str(game_sensitivity).replace('.', '_')}_config.txt"
    try:
        with open(config_filename, 'w', encoding='utf-8') as f:
            f.write(config_text)
        print(f"✅ 配置已保存到: {config_filename}")
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")

def test_correction_factors():
    """测试不同校正因子的效果"""
    print("🔬 校正因子效果测试")
    print("=" * 50)
    
    mouse_dpi = 1600
    game_sensitivity = 0.19
    effective_dpi = calculate_effective_dpi(mouse_dpi, game_sensitivity)
    
    # 测试不同的校正因子
    test_factors = [0.5, 0.62, 0.75, 0.9, 1.0, 1.2, 1.5]
    test_distance = 200  # 测试距离
    
    print(f"测试距离: {test_distance}像素")
    print(f"有效DPI: {effective_dpi}")
    print()
    
    optimal_correction = calculate_optimal_correction_factor(effective_dpi)
    
    for factor in test_factors:
        corrected_movement = test_distance * factor
        steps_needed = math.ceil(corrected_movement / 127)
        per_step = corrected_movement / steps_needed if steps_needed > 0 else 0
        
        # 标记推荐值
        marker = " ⭐ 推荐" if abs(factor - optimal_correction) < 0.05 else ""
        
        print(f"校正因子 {factor:4.2f}: {corrected_movement:6.1f}像素, {steps_needed}步, {per_step:5.1f}像素/步{marker}")

def main():
    """主函数"""
    print("🎮 1600 DPI × 0.19 灵敏度专用校正优化工具")
    print("=" * 60)
    print()
    
    # 执行各项测试
    test_movement_distances()
    print()
    
    test_correction_factors()
    print()
    
    generate_optimized_config()
    print()
    
    print("📋 总结建议:")
    print("-" * 30)
    
    mouse_dpi = 1600
    game_sensitivity = 0.19
    effective_dpi = calculate_effective_dpi(mouse_dpi, game_sensitivity)
    optimal_correction = calculate_optimal_correction_factor(effective_dpi)
    
    print(f"1. 您的有效DPI ({effective_dpi}) 属于低eDPI设置")
    print(f"2. 建议将校正因子从 0.62 调整为 {optimal_correction}")
    print(f"3. 启用非阻塞平滑移动系统以提升响应速度")
    print(f"4. 使用较大的移动步长以减少总步数")
    print(f"5. 考虑启用微调模式以提高精度")
    
    print()
    print("🔧 应用建议:")
    print(f"   在 MouseMove.py 中修改:")
    print(f"   MOVEMENT_CORRECTION_FACTOR = {optimal_correction}")

if __name__ == "__main__":
    main()
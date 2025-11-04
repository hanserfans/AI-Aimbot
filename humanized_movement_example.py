#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人性化移动系统使用示例
展示如何使用新的人性化移动特性：
1. 步长控制：最后几步>20px，最后一步<20px
2. 人手抖动模拟：避免机械化直线移动
3. 抛物线轨迹：更符合人手移动习惯
4. 300像素优化：最后一步约占20/300比例
"""

import time
from non_blocking_smooth_movement import NonBlockingSmoothMovement

def simulate_mouse_move(x, y):
    """模拟鼠标移动函数"""
    print(f"    → 移动到 ({x:.1f}, {y:.1f})")
    return True

def demonstrate_humanized_movement():
    """演示人性化移动系统"""
    
    print("🎯 人性化移动系统演示")
    print("="*60)
    
    # 创建移动系统
    movement = NonBlockingSmoothMovement(simulate_mouse_move)
    
    # 配置人性化特性
    print("📋 配置人性化移动特性:")
    
    # 1. 启用人手抖动模拟
    movement.enable_human_tremor = True
    movement.tremor_intensity = 2.0  # 抖动强度
    print(f"✓ 人手抖动: 强度 {movement.tremor_intensity}")
    
    # 2. 启用抛物线轨迹
    movement.enable_parabolic_trajectory = True
    movement.parabolic_height_factor = 0.05  # 抛物线高度因子
    print(f"✓ 抛物线轨迹: 高度因子 {movement.parabolic_height_factor}")
    
    # 3. 步长控制配置
    print(f"✓ 步长控制: 最后一步 {movement.min_final_step}-{movement.max_final_step}px")
    print(f"✓ 倒数第二步: 最小 {movement.min_penultimate_step}px")
    
    # 4. 选择衰减策略
    movement.set_decay_strategy("balanced")  # 平衡策略
    decay_info = movement.get_decay_info()
    print(f"✓ 衰减策略: balanced (系数: {decay_info['decay_factor']})")
    
    print(f"\n🚀 开始移动演示:")
    
    # 演示不同距离的移动
    test_cases = [
        (100, 0, "短距离水平移动"),
        (200, 0, "中距离水平移动"), 
        (300, 0, "长距离水平移动"),
        (200, 150, "斜向移动"),
        (-150, 100, "负方向移动"),
    ]
    
    for i, (target_x, target_y, description) in enumerate(test_cases, 1):
        print(f"\n{i}. {description} -> ({target_x}, {target_y})")
        print("-" * 40)
        
        # 执行移动
        success = movement.move_to_target(target_x, target_y)
        
        # 等待移动完成
        time.sleep(0.5)
        
        # 获取移动状态
        print(f"   移动结果: {'成功' if success else '失败'}")
        
        # 重置位置为下次演示
        time.sleep(0.1)  # 短暂等待
    
    print(f"\n📊 移动统计:")
    final_status = movement.get_movement_status()
    print(f"   总移动次数: {final_status.get('total_movements', 0)}")
    print(f"   成功移动: {final_status.get('successful_movements', 0)}")
    print(f"   成功率: {final_status.get('success_rate', 0):.1f}%")
    
    # 演示不同衰减策略的效果
    print(f"\n🔧 衰减策略对比:")
    strategies = ["aggressive", "balanced", "gentle", "linear"]
    
    for strategy in strategies:
        movement.set_decay_strategy(strategy)
        decay_info = movement.get_decay_info()
        
        print(f"\n   {strategy.upper()} 策略:")
        print(f"   - 衰减系数: {decay_info['decay_factor']}")
        print(f"   - 第一步比例: {decay_info['first_step_percentage']:.1f}%")
    
    # 恢复默认策略
    movement.set_decay_strategy("balanced")
    
    print(f"\n✨ 人性化移动特性总结:")
    print(f"   🎯 精确控制: 最后一步<20px，避免移动过头")
    print(f"   🤏 微调空间: 倒数第二步>20px，保证调整余地")
    print(f"   🌊 自然轨迹: 抛物线路径，符合人手习惯")
    print(f"   🎲 随机抖动: 模拟人手不稳，避免机械感")
    print(f"   📏 比例优化: 300px内最后步约占6.7%")
    print(f"   ⚡ 快速接近: 前三步达到80%+距离")
    
    # 停止移动系统
    movement.stop()
    print(f"\n🏁 演示完成！")

def demonstrate_configuration_options():
    """演示配置选项"""
    
    print(f"\n⚙️  配置选项演示:")
    print("="*40)
    
    def mock_move(x, y):
        return True
    
    movement = NonBlockingSmoothMovement(mock_move)
    
    print(f"1. 人手抖动配置:")
    print(f"   movement.enable_human_tremor = True/False")
    print(f"   movement.tremor_intensity = 1.0-3.0  # 抖动强度")
    
    print(f"\n2. 抛物线轨迹配置:")
    print(f"   movement.enable_parabolic_trajectory = True/False")
    print(f"   movement.parabolic_height_factor = 0.02-0.08  # 高度因子")
    
    print(f"\n3. 步长控制配置:")
    print(f"   movement.min_final_step = 8   # 最后一步最小距离")
    print(f"   movement.max_final_step = 18  # 最后一步最大距离")
    print(f"   movement.min_penultimate_step = 20  # 倒数第二步最小距离")
    
    print(f"\n4. 衰减策略选择:")
    print(f"   movement.set_decay_strategy('aggressive')  # 激进：快速接近")
    print(f"   movement.set_decay_strategy('balanced')   # 平衡：推荐使用")
    print(f"   movement.set_decay_strategy('gentle')     # 温和：平滑过渡")
    print(f"   movement.set_decay_strategy('linear')     # 线性：均匀递减")
    
    print(f"\n5. 获取配置信息:")
    print(f"   decay_info = movement.get_decay_info()")
    print(f"   status = movement.get_movement_status()")
    
    movement.stop()

if __name__ == "__main__":
    # 运行主演示
    demonstrate_humanized_movement()
    
    # 显示配置选项
    demonstrate_configuration_options()
    
    print(f"\n🎉 人性化移动系统已完全优化！")
    print(f"   现在可以提供更自然、更精确的鼠标移动体验。")
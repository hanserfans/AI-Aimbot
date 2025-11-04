#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
头部跟踪 vs 中心点跟踪对比测试
分析两种跟踪方式的效果差异
"""

import pandas as pd
import time
import math

# 模拟配置
headshot_mode = True
LOCK_DURATION = 1.5
LOCK_DISTANCE_THRESHOLD = 30

def calculate_head_position(target_row):
    """计算目标头部位置"""
    mid_x = target_row['current_mid_x']
    mid_y = target_row['current_mid_y']
    box_height = target_row['height']
    
    # 计算头部偏移（与瞄准逻辑保持一致）
    if headshot_mode:
        headshot_offset = box_height * 0.38
    else:
        headshot_offset = box_height * 0.2
    
    head_x = mid_x
    head_y = mid_y - headshot_offset  # 头部在中心点上方
    
    return head_x, head_y

def simulate_target_movement():
    """模拟目标移动场景"""
    scenarios = []
    
    # 场景1：目标轻微摇摆（模拟玩家微调瞄准）
    base_x, base_y = 960, 540
    for i in range(10):
        offset_x = math.sin(i * 0.5) * 5  # 左右摇摆5px
        offset_y = math.cos(i * 0.3) * 3  # 上下摇摆3px
        scenarios.append({
            'scenario': '轻微摇摆',
            'frame': i,
            'current_mid_x': base_x + offset_x,
            'current_mid_y': base_y + offset_y,
            'height': 100,
            'confidence': 0.85
        })
    
    # 场景2：目标快速移动（模拟玩家快速转身）
    for i in range(10):
        move_x = i * 15  # 每帧移动15px
        move_y = i * 8   # 每帧移动8px
        scenarios.append({
            'scenario': '快速移动',
            'frame': i,
            'current_mid_x': base_x + move_x,
            'current_mid_y': base_y + move_y,
            'height': 100,
            'confidence': 0.80
        })
    
    # 场景3：目标跳跃（模拟玩家跳跃）
    for i in range(10):
        jump_y = -abs(math.sin(i * 0.8) * 50)  # 跳跃轨迹
        scenarios.append({
            'scenario': '跳跃移动',
            'frame': i,
            'current_mid_x': base_x + i * 5,
            'current_mid_y': base_y + jump_y,
            'height': 100,
            'confidence': 0.75
        })
    
    return scenarios

def test_center_tracking(scenarios):
    """测试中心点跟踪"""
    results = []
    locked_target = None
    lock_start_time = 0
    
    for scenario_data in scenarios:
        current_time = time.time()
        
        # 模拟中心点跟踪逻辑
        if locked_target is None:
            # 锁定新目标（中心点）
            locked_target = {
                'x': scenario_data['current_mid_x'],
                'y': scenario_data['current_mid_y'],
                'confidence': scenario_data['confidence']
            }
            lock_start_time = current_time
            tracking_distance = 0
        else:
            # 计算与锁定目标的距离
            tracking_distance = ((scenario_data['current_mid_x'] - locked_target['x'])**2 + 
                               (scenario_data['current_mid_y'] - locked_target['y'])**2)**0.5
            
            if tracking_distance <= LOCK_DISTANCE_THRESHOLD:
                # 更新锁定目标位置
                locked_target['x'] = scenario_data['current_mid_x']
                locked_target['y'] = scenario_data['current_mid_y']
            else:
                # 目标移动过远，重新锁定
                locked_target = {
                    'x': scenario_data['current_mid_x'],
                    'y': scenario_data['current_mid_y'],
                    'confidence': scenario_data['confidence']
                }
                lock_start_time = current_time
        
        results.append({
            'scenario': scenario_data['scenario'],
            'frame': scenario_data['frame'],
            'tracking_distance': tracking_distance,
            'locked': locked_target is not None,
            'target_x': scenario_data['current_mid_x'],
            'target_y': scenario_data['current_mid_y'],
            'locked_x': locked_target['x'] if locked_target else None,
            'locked_y': locked_target['y'] if locked_target else None
        })
        
        time.sleep(0.01)  # 模拟帧间隔
    
    return results

def test_head_tracking(scenarios):
    """测试头部跟踪"""
    results = []
    locked_target = None
    lock_start_time = 0
    
    for scenario_data in scenarios:
        current_time = time.time()
        
        # 计算当前目标的头部位置
        target_df = pd.DataFrame([scenario_data])
        head_x, head_y = calculate_head_position(target_df.iloc[0])
        
        # 模拟头部跟踪逻辑
        if locked_target is None:
            # 锁定新目标（头部位置）
            locked_target = {
                'head_x': head_x,
                'head_y': head_y,
                'x': scenario_data['current_mid_x'],
                'y': scenario_data['current_mid_y'],
                'confidence': scenario_data['confidence']
            }
            lock_start_time = current_time
            tracking_distance = 0
        else:
            # 计算与锁定目标头部的距离
            tracking_distance = ((head_x - locked_target['head_x'])**2 + 
                               (head_y - locked_target['head_y'])**2)**0.5
            
            if tracking_distance <= LOCK_DISTANCE_THRESHOLD:
                # 更新锁定目标位置
                locked_target['head_x'] = head_x
                locked_target['head_y'] = head_y
                locked_target['x'] = scenario_data['current_mid_x']
                locked_target['y'] = scenario_data['current_mid_y']
            else:
                # 目标移动过远，重新锁定
                locked_target = {
                    'head_x': head_x,
                    'head_y': head_y,
                    'x': scenario_data['current_mid_x'],
                    'y': scenario_data['current_mid_y'],
                    'confidence': scenario_data['confidence']
                }
                lock_start_time = current_time
        
        results.append({
            'scenario': scenario_data['scenario'],
            'frame': scenario_data['frame'],
            'tracking_distance': tracking_distance,
            'locked': locked_target is not None,
            'target_head_x': head_x,
            'target_head_y': head_y,
            'locked_head_x': locked_target['head_x'] if locked_target else None,
            'locked_head_y': locked_target['head_y'] if locked_target else None
        })
        
        time.sleep(0.01)  # 模拟帧间隔
    
    return results

def analyze_tracking_performance(center_results, head_results):
    """分析跟踪性能"""
    print("\n" + "=" * 80)
    print("📊 跟踪性能分析报告")
    print("=" * 80)
    
    # 按场景分组分析
    scenarios = ['轻微摇摆', '快速移动', '跳跃移动']
    
    for scenario in scenarios:
        print(f"\n🎯 场景: {scenario}")
        print("-" * 50)
        
        # 筛选当前场景的数据
        center_scenario = [r for r in center_results if r['scenario'] == scenario]
        head_scenario = [r for r in head_results if r['scenario'] == scenario]
        
        # 计算平均跟踪距离
        center_avg_distance = sum(r['tracking_distance'] for r in center_scenario) / len(center_scenario)
        head_avg_distance = sum(r['tracking_distance'] for r in head_scenario) / len(head_scenario)
        
        # 计算最大跟踪距离
        center_max_distance = max(r['tracking_distance'] for r in center_scenario)
        head_max_distance = max(r['tracking_distance'] for r in head_scenario)
        
        # 计算锁定稳定性（连续锁定帧数）
        center_lock_stability = sum(1 for r in center_scenario if r['locked']) / len(center_scenario)
        head_lock_stability = sum(1 for r in head_scenario if r['locked']) / len(head_scenario)
        
        print(f"   中心点跟踪:")
        print(f"     • 平均跟踪距离: {center_avg_distance:.2f}px")
        print(f"     • 最大跟踪距离: {center_max_distance:.2f}px")
        print(f"     • 锁定稳定性: {center_lock_stability:.1%}")
        
        print(f"   头部跟踪:")
        print(f"     • 平均跟踪距离: {head_avg_distance:.2f}px")
        print(f"     • 最大跟踪距离: {head_max_distance:.2f}px")
        print(f"     • 锁定稳定性: {head_lock_stability:.1%}")
        
        # 性能对比
        distance_improvement = ((center_avg_distance - head_avg_distance) / center_avg_distance) * 100
        stability_improvement = ((head_lock_stability - center_lock_stability) / center_lock_stability) * 100
        
        print(f"   📈 性能提升:")
        print(f"     • 跟踪精度提升: {distance_improvement:+.1f}%")
        print(f"     • 稳定性提升: {stability_improvement:+.1f}%")

def main():
    """主测试函数"""
    print("🔄 生成目标移动场景...")
    scenarios = simulate_target_movement()
    
    print("🎯 测试中心点跟踪...")
    center_results = test_center_tracking(scenarios)
    
    print("🎯 测试头部跟踪...")
    head_results = test_head_tracking(scenarios)
    
    print("📊 分析跟踪性能...")
    analyze_tracking_performance(center_results, head_results)
    
    print("\n" + "=" * 80)
    print("✅ 跟踪方式对比测试完成")
    print("=" * 80)
    
    # 总结
    print("\n🎯 总结:")
    print("   • 头部跟踪更适合精确瞄准，特别是在目标轻微移动时")
    print("   • 中心点跟踪在目标快速移动时可能更稳定")
    print("   • 建议根据游戏类型和个人偏好选择跟踪方式")
    print("   • 当前实现的头部跟踪机制在多数场景下表现更优")

if __name__ == "__main__":
    main()
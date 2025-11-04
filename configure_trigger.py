#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扳机系统配置工具
快速配置和测试不同的阈值设置
"""

import sys
import os
from auto_trigger_system import get_trigger_system

def main():
    """配置工具主函数"""
    print("🎯 扳机系统配置工具")
    print("=" * 50)
    
    # 获取扳机系统实例
    trigger = get_trigger_system()
    
    while True:
        print("\n📋 配置选项:")
        print("1. 查看当前配置")
        print("2. 切换预设配置")
        print("3. 列出所有预设")
        print("4. 自定义阈值")
        print("5. 游戏推荐配置")
        print("6. 测试当前配置")
        print("7. 重新加载配置文件")
        print("8. 退出")
        
        try:
            choice = input("\n请选择操作 (1-8): ").strip()
            
            if choice == "1":
                show_current_config(trigger)
                
            elif choice == "2":
                change_preset(trigger)
                
            elif choice == "3":
                trigger.list_presets()
                
            elif choice == "4":
                custom_thresholds(trigger)
                
            elif choice == "5":
                game_recommendation(trigger)
                
            elif choice == "6":
                test_configuration(trigger)
                
            elif choice == "7":
                if trigger.reload_config():
                    print("✅ 配置文件已重新加载")
                else:
                    print("❌ 重新加载失败")
                    
            elif choice == "8":
                print("退出配置工具...")
                break
                
            else:
                print("❌ 无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")

def show_current_config(trigger):
    """显示当前配置"""
    config_info = trigger.get_config_info()
    
    print(f"\n📊 当前配置信息:")
    print("=" * 40)
    print(f"预设名称: {config_info['preset_name']}")
    
    if 'preset_description' in config_info:
        print(f"描述: {config_info['preset_description']}")
    
    print(f"\n🎯 阈值设置:")
    print(f"  对齐阈值: {config_info['alignment_threshold']}px")
    print(f"  精确阈值: {config_info['precise_alignment_threshold']}px")
    print(f"  X/Y检查: {config_info['xy_check_threshold']}px")
    
    print(f"\n⏱️ 时间设置:")
    print(f"  冷却时间: {config_info['cooldown_duration']}s")
    print(f"  连发数量: {config_info['shots_per_trigger']}发")
    print(f"  连发间隔: {config_info['shot_interval']}s")
    
    if 'recommended_games' in config_info and config_info['recommended_games']:
        print(f"\n🎮 推荐游戏: {', '.join(config_info['recommended_games'][:3])}")
    
    print(f"\n🔧 配置系统: {'可用' if config_info['config_available'] else '不可用'}")

def change_preset(trigger):
    """切换预设配置"""
    print("\n可用预设:")
    trigger.list_presets()
    
    preset_name = input("\n请输入预设名称: ").strip()
    if preset_name:
        if trigger.set_preset(preset_name):
            print(f"✅ 已切换到预设: {preset_name}")
            show_current_config(trigger)
        else:
            print(f"❌ 预设不存在: {preset_name}")

def custom_thresholds(trigger):
    """自定义阈值设置"""
    print("\n🔧 自定义阈值设置")
    print("提示: 直接按回车跳过某项设置")
    
    try:
        custom_params = {}
        
        # 对齐阈值
        alignment = input(f"对齐阈值 (当前: {trigger.alignment_threshold}px): ").strip()
        if alignment:
            custom_params['alignment_threshold'] = float(alignment)
        
        # 精确阈值
        precise = input(f"精确阈值 (当前: {trigger.precise_alignment_threshold}px): ").strip()
        if precise:
            custom_params['precise_alignment_threshold'] = float(precise)
        
        # X/Y检查阈值
        xy_check = input(f"X/Y检查阈值 (当前: {trigger.xy_check_threshold}px): ").strip()
        if xy_check:
            custom_params['xy_check_threshold'] = float(xy_check)
        
        # 冷却时间
        cooldown = input(f"冷却时间 (当前: {trigger.cooldown_duration}s): ").strip()
        if cooldown:
            custom_params['cooldown_duration'] = float(cooldown)
        
        # 连发数量
        shots = input(f"连发数量 (当前: {trigger.shots_per_trigger}发): ").strip()
        if shots:
            custom_params['shots_per_trigger'] = int(shots)
        
        # 连发间隔
        interval = input(f"连发间隔 (当前: {trigger.shot_interval}s): ").strip()
        if interval:
            custom_params['shot_interval'] = float(interval)
        
        if custom_params:
            trigger.apply_custom_thresholds(**custom_params)
            print("✅ 自定义设置已应用")
        else:
            print("ℹ️ 未修改任何设置")
            
    except ValueError:
        print("❌ 输入格式错误，请输入有效数值")

def game_recommendation(trigger):
    """游戏推荐配置"""
    if not trigger.config_manager:
        print("❌ 配置系统不可用")
        return
    
    game_name = input("\n请输入游戏名称: ").strip()
    if game_name:
        preset_key, preset = trigger.config_manager.get_recommended_preset(game_name)
        
        print(f"\n🎮 为 '{game_name}' 推荐的配置:")
        print(f"预设: {preset['name']}")
        print(f"描述: {preset['description']}")
        
        apply = input("\n是否应用此配置? (y/n): ").strip().lower()
        if apply == 'y':
            if trigger.set_preset(preset_key):
                print("✅ 推荐配置已应用")
            else:
                print("❌ 应用配置失败")

def test_configuration(trigger):
    """测试当前配置"""
    print("\n🧪 测试当前配置")
    print("=" * 30)
    
    # 模拟检测中心
    detection_center = (0.5, 0.5)
    headshot_offset = 0.05
    
    test_cases = [
        (0.5, 0.5, "完美对齐"),
        (0.501, 0.501, "轻微偏移"),
        (0.505, 0.505, "小幅偏移"),
        (0.51, 0.51, "中等偏移"),
        (0.52, 0.52, "较大偏移"),
        (0.55, 0.55, "明显偏移")
    ]
    
    print("测试不同偏移情况下的对齐检测:")
    for target_x, target_y, description in test_cases:
        is_aligned = trigger.is_aligned(target_x, target_y, detection_center, headshot_offset,
                                        game_fov=103, detection_size=320, 
                                        game_width=2560, game_height=1600)
        status = "✅ 会开火" if is_aligned else "❌ 不开火"
        print(f"  {description} ({target_x}, {target_y}): {status}")
    
    # 显示当前配置摘要
    print(f"\n📊 当前配置摘要:")
    print(f"  阈值: {trigger.alignment_threshold}px")
    print(f"  X/Y检查: {trigger.xy_check_threshold}px")
    print(f"  冷却: {trigger.cooldown_duration}s")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复扳机系统阈值设置
将过于宽松的阈值调整为更精确的设置
"""

import json
import os
from auto_trigger_system import get_trigger_system

def fix_trigger_thresholds():
    """修复扳机系统的阈值设置"""
    print("🔧 修复扳机系统阈值设置")
    print("="*50)
    
    # 读取当前配置
    config_file = "trigger_threshold_config.json"
    
    if not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        current_preset = config_data.get('current_preset', 'default')
        print(f"📋 当前预设: {current_preset}")
        
        # 检查当前预设是否过于宽松
        if current_preset in ['relaxed', 'ultra_relaxed']:
            print(f"⚠️ 检测到宽松预设 '{current_preset}'，这会导致误触发")
            
            # 建议切换到更精确的预设
            recommended_preset = 'high_precision'
            
            print(f"💡 建议切换到: {recommended_preset}")
            
            # 显示预设对比
            if current_preset in config_data.get('presets', {}):
                current_config = config_data['presets'][current_preset]
                recommended_config = config_data['presets'].get(recommended_preset, {})
                
                print(f"\n📊 预设对比:")
                print(f"   当前 ({current_preset}):")
                print(f"     • 精确角度阈值: {current_config.get('precise_angle_threshold', 'N/A')}°")
                print(f"     • 角度阈值: {current_config.get('angle_threshold', 'N/A')}°")
                print(f"     • 冷却时间: {current_config.get('cooldown_duration', 'N/A')}s")
                
                print(f"   推荐 ({recommended_preset}):")
                print(f"     • 精确角度阈值: {recommended_config.get('precise_angle_threshold', 'N/A')}°")
                print(f"     • 角度阈值: {recommended_config.get('angle_threshold', 'N/A')}°")
                print(f"     • 冷却时间: {recommended_config.get('cooldown_duration', 'N/A')}s")
            
            # 询问是否切换
            response = input(f"\n🤔 是否切换到 '{recommended_preset}' 预设？(y/n): ").lower().strip()
            
            if response in ['y', 'yes', '是', 'Y']:
                # 切换预设
                config_data['current_preset'] = recommended_preset
                
                # 保存配置
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 已切换到 '{recommended_preset}' 预设")
                
                # 重新加载扳机系统
                trigger_system = get_trigger_system()
                trigger_system.reload_config()
                
                print("🔄 扳机系统配置已重新加载")
                
                # 显示新的设置
                print(f"\n📋 新的扳机设置:")
                print(f"   • 精确角度阈值: {trigger_system.precise_angle_threshold:.3f}°")
                print(f"   • 角度阈值: {trigger_system.angle_threshold:.3f}°")
                print(f"   • 冷却时间: {trigger_system.cooldown_duration}s")
                
                return True
            else:
                print("❌ 用户取消切换")
                return False
        
        elif current_preset in ['ultra_precision', 'high_precision']:
            print(f"✅ 当前预设 '{current_preset}' 已经是精确模式")
            
            # 检查是否需要微调
            trigger_system = get_trigger_system()
            
            if trigger_system.precise_angle_threshold > 0.3:
                print(f"⚠️ 精确角度阈值 {trigger_system.precise_angle_threshold:.3f}° 可能仍然偏大")
                print("💡 建议设置为 0.15° - 0.25°")
                
                # 提供微调选项
                response = input("🤔 是否进行微调？(y/n): ").lower().strip()
                
                if response in ['y', 'yes', '是', 'Y']:
                    return fine_tune_thresholds(config_data, config_file)
            else:
                print("✅ 阈值设置合理")
                return True
        
        else:
            print(f"✅ 当前预设 '{current_preset}' 设置合理")
            return True
            
    except Exception as e:
        print(f"❌ 配置文件处理失败: {e}")
        return False

def fine_tune_thresholds(config_data, config_file):
    """微调阈值设置"""
    print("\n🔧 微调阈值设置")
    
    current_preset = config_data.get('current_preset')
    
    if current_preset not in config_data.get('presets', {}):
        print(f"❌ 预设 '{current_preset}' 不存在")
        return False
    
    preset_config = config_data['presets'][current_preset]
    
    print("💡 推荐的精确设置:")
    print("   • 精确角度阈值: 0.2°")
    print("   • 角度阈值: 0.3°")
    print("   • 冷却时间: 0.4s")
    
    response = input("🤔 是否应用这些设置？(y/n): ").lower().strip()
    
    if response in ['y', 'yes', '是', 'Y']:
        # 更新配置
        preset_config['precise_angle_threshold'] = 0.2
        preset_config['angle_threshold'] = 0.3
        preset_config['cooldown_duration'] = 0.4
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        print("✅ 微调设置已应用")
        
        # 重新加载扳机系统
        trigger_system = get_trigger_system()
        trigger_system.reload_config()
        
        print("🔄 扳机系统配置已重新加载")
        return True
    else:
        print("❌ 用户取消微调")
        return False

def test_new_settings():
    """测试新的设置"""
    print("\n🎯 测试新的扳机设置")
    
    trigger_system = get_trigger_system()
    detection_center = (0.5, 0.5)
    
    # 测试不同的目标位置
    test_cases = [
        (0.5, 0.5, "完全中心"),
        (0.501, 0.501, "轻微偏移"),
        (0.505, 0.505, "小幅偏移"),
        (0.51, 0.51, "中等偏移"),
        (0.52, 0.52, "较大偏移")
    ]
    
    print("📊 对齐测试结果:")
    for target_x, target_y, description in test_cases:
        is_aligned = trigger_system.is_aligned(
            target_x, target_y, detection_center, 0.0,
            103, 320, 2560, 1600
        )
        
        angle_offset = trigger_system.calculate_angle_offset(
            target_x, target_y, detection_center, 0.0,
            103, 320, 2560, 1600
        )
        
        status = "✅ 会开火" if is_aligned else "❌ 不会开火"
        print(f"   • {description}: {status} (角度偏移: {angle_offset:.3f}°)")

if __name__ == "__main__":
    success = fix_trigger_thresholds()
    
    if success:
        test_new_settings()
        print("\n🎉 扳机系统修复完成！")
        print("💡 现在扳机系统应该只在真正精确对齐时才会开火")
    else:
        print("\n❌ 修复失败，请手动检查配置")
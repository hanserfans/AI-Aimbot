"""
开火配置修复工具
解决只开一枪的问题
"""

import json
import os

def show_current_problem():
    """显示当前问题"""
    print("🚨 问题分析")
    print("=" * 50)
    print("发现问题：只开一枪而不是配置的多枪")
    print()
    print("🔍 根本原因：")
    print("   • config.py 中 autoFireShots = 3")
    print("   • 但扳机系统使用 trigger_threshold_config.json 的配置")
    print("   • 当前预设是 'high_precision'，其中 shots_per_trigger = 1")
    print("   • 扳机系统的配置覆盖了 config.py 的设置")
    print()

def show_available_presets():
    """显示可用的预设"""
    try:
        with open('trigger_threshold_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        current_preset = config.get('current_preset', 'balanced')
        presets = config.get('presets', {})
        
        print("📋 可用预设及其开火设置：")
        print("=" * 50)
        
        for preset_name, preset_config in presets.items():
            shots = preset_config.get('shots_per_trigger', 1)
            cooldown = preset_config.get('cooldown_duration', 0.5)
            interval = preset_config.get('shot_interval', 0.3)
            name = preset_config.get('name', preset_name)
            desc = preset_config.get('description', '')
            
            marker = "👉 [当前]" if preset_name == current_preset else "   "
            
            print(f"{marker} {preset_name}:")
            print(f"      名称: {name}")
            print(f"      描述: {desc}")
            print(f"      开火数: {shots} 发")
            print(f"      冷却时间: {cooldown}s")
            print(f"      连发间隔: {interval}s")
            print()
        
        return current_preset, presets
        
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return None, {}

def change_preset(new_preset):
    """更改预设"""
    try:
        with open('trigger_threshold_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if new_preset not in config.get('presets', {}):
            print(f"❌ 预设 '{new_preset}' 不存在")
            return False
        
        config['current_preset'] = new_preset
        
        with open('trigger_threshold_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        preset_info = config['presets'][new_preset]
        shots = preset_info.get('shots_per_trigger', 1)
        name = preset_info.get('name', new_preset)
        
        print(f"✅ 预设已更改为: {new_preset} ({name})")
        print(f"✅ 现在每次触发将开火 {shots} 发")
        
        return True
        
    except Exception as e:
        print(f"❌ 更改预设失败: {e}")
        return False

def modify_current_preset_shots(new_shots):
    """修改当前预设的开火数"""
    try:
        with open('trigger_threshold_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        current_preset = config.get('current_preset', 'balanced')
        
        if current_preset not in config.get('presets', {}):
            print(f"❌ 当前预设 '{current_preset}' 不存在")
            return False
        
        config['presets'][current_preset]['shots_per_trigger'] = new_shots
        
        with open('trigger_threshold_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        preset_name = config['presets'][current_preset].get('name', current_preset)
        
        print(f"✅ 当前预设 '{current_preset}' ({preset_name}) 的开火数已修改为 {new_shots} 发")
        
        return True
        
    except Exception as e:
        print(f"❌ 修改开火数失败: {e}")
        return False

def quick_fix():
    """快速修复：将当前预设改为多发"""
    print("🔧 快速修复")
    print("=" * 50)
    
    try:
        with open('trigger_threshold_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        current_preset = config.get('current_preset', 'balanced')
        current_shots = config['presets'][current_preset].get('shots_per_trigger', 1)
        
        if current_shots >= 2:
            print(f"✅ 当前预设已经是 {current_shots} 发，无需修复")
            return True
        
        # 读取 config.py 中的 autoFireShots
        try:
            from config import autoFireShots
            target_shots = autoFireShots
        except:
            target_shots = 3  # 默认值
        
        print(f"🎯 将当前预设的开火数从 {current_shots} 发改为 {target_shots} 发")
        
        return modify_current_preset_shots(target_shots)
        
    except Exception as e:
        print(f"❌ 快速修复失败: {e}")
        return False

def main():
    print("🔫 开火配置修复工具")
    print("=" * 60)
    
    show_current_problem()
    current_preset, presets = show_available_presets()
    
    if not presets:
        print("❌ 无法读取配置文件")
        return
    
    print("🛠️ 修复选项：")
    print("=" * 50)
    print("1. 快速修复 - 将当前预设改为多发模式")
    print("2. 更换预设 - 选择一个多发预设")
    print("3. 自定义修改 - 手动设置开火数")
    print("4. 仅查看 - 不做任何修改")
    print()
    
    try:
        choice = input("请选择修复方式 (1-4): ").strip()
        
        if choice == "1":
            print()
            if quick_fix():
                print("🎉 快速修复完成！")
            else:
                print("❌ 快速修复失败")
                
        elif choice == "2":
            print()
            print("📋 多发预设选项：")
            multi_shot_presets = []
            for name, preset in presets.items():
                if preset.get('shots_per_trigger', 1) > 1:
                    multi_shot_presets.append(name)
                    shots = preset.get('shots_per_trigger', 1)
                    preset_name = preset.get('name', name)
                    print(f"   • {name}: {preset_name} ({shots} 发)")
            
            if not multi_shot_presets:
                print("❌ 没有找到多发预设")
                return
            
            print()
            new_preset = input("请输入要使用的预设名称: ").strip()
            
            if new_preset in multi_shot_presets:
                if change_preset(new_preset):
                    print("🎉 预设更换完成！")
                else:
                    print("❌ 预设更换失败")
            else:
                print("❌ 无效的预设名称")
                
        elif choice == "3":
            print()
            try:
                new_shots = int(input("请输入开火数 (1-10): "))
                if 1 <= new_shots <= 10:
                    if modify_current_preset_shots(new_shots):
                        print("🎉 自定义修改完成！")
                    else:
                        print("❌ 自定义修改失败")
                else:
                    print("❌ 开火数必须在 1-10 之间")
            except ValueError:
                print("❌ 请输入有效的数字")
                
        elif choice == "4":
            print("ℹ️ 仅查看模式，未做任何修改")
            
        else:
            print("❌ 无效的选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 操作失败: {e}")

if __name__ == "__main__":
    main()
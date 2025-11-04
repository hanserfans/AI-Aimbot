"""
检查扳机系统实际加载的配置
"""

import json

def check_trigger_config():
    """检查扳机系统配置"""
    print("🔍 检查扳机系统实际配置")
    print("=" * 50)
    
    try:
        # 检查JSON配置文件
        with open('trigger_threshold_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        current_preset = config.get('current_preset', 'balanced')
        preset_config = config.get('presets', {}).get(current_preset, {})
        
        print(f"📋 JSON配置文件:")
        print(f"   • 当前预设: {current_preset}")
        print(f"   • 预设名称: {preset_config.get('name', 'N/A')}")
        print(f"   • shots_per_trigger: {preset_config.get('shots_per_trigger', 'N/A')}")
        print(f"   • shot_interval: {preset_config.get('shot_interval', 'N/A')}")
        print(f"   • cooldown_duration: {preset_config.get('cooldown_duration', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 读取JSON配置失败: {e}")
    
    try:
        # 检查实际的扳机系统
        from auto_trigger_system import get_trigger_system
        
        trigger = get_trigger_system()
        
        print(f"\n🎯 扳机系统实际配置:")
        print(f"   • shots_per_trigger: {trigger.shots_per_trigger}")
        print(f"   • shot_interval: {trigger.shot_interval}")
        print(f"   • cooldown_duration: {trigger.cooldown_duration}")
        print(f"   • enabled: {trigger.enabled}")
        
        # 检查配置管理器
        if hasattr(trigger, 'config_manager') and trigger.config_manager:
            current_config = trigger.config_manager.get_current_config()
            print(f"\n⚙️ 配置管理器当前配置:")
            print(f"   • shots_per_trigger: {current_config.get('shots_per_trigger', 'N/A')}")
            print(f"   • shot_interval: {current_config.get('shot_interval', 'N/A')}")
            print(f"   • cooldown_duration: {current_config.get('cooldown_duration', 'N/A')}")
        else:
            print(f"\n⚠️ 配置管理器未初始化")
        
    except Exception as e:
        print(f"❌ 检查扳机系统失败: {e}")
    
    try:
        # 检查config.py
        from config import autoFireShots, autoFireDelay
        
        print(f"\n📄 config.py 配置:")
        print(f"   • autoFireShots: {autoFireShots}")
        print(f"   • autoFireDelay: {autoFireDelay}ms")
        
    except Exception as e:
        print(f"❌ 读取config.py失败: {e}")

def fix_config_mismatch():
    """修复配置不匹配问题"""
    print("\n🔧 修复配置不匹配")
    print("=" * 50)
    
    try:
        # 读取config.py中的设置
        from config import autoFireShots
        
        # 更新JSON配置文件
        with open('trigger_threshold_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        current_preset = config.get('current_preset', 'balanced')
        
        if current_preset in config.get('presets', {}):
            old_shots = config['presets'][current_preset].get('shots_per_trigger', 1)
            config['presets'][current_preset]['shots_per_trigger'] = autoFireShots
            
            with open('trigger_threshold_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 已将 {current_preset} 预设的 shots_per_trigger 从 {old_shots} 更新为 {autoFireShots}")
            
            # 重新初始化扳机系统
            try:
                from auto_trigger_system import get_trigger_system
                trigger = get_trigger_system()
                trigger._load_config_values()  # 重新加载配置
                
                print(f"✅ 扳机系统已重新加载配置")
                print(f"   • 新的 shots_per_trigger: {trigger.shots_per_trigger}")
                
            except Exception as e:
                print(f"⚠️ 重新加载扳机系统配置失败: {e}")
                print("   请重启程序以使配置生效")
        else:
            print(f"❌ 预设 {current_preset} 不存在")
            
    except Exception as e:
        print(f"❌ 修复配置失败: {e}")

if __name__ == "__main__":
    check_trigger_config()
    
    print("\n" + "=" * 50)
    choice = input("是否要修复配置不匹配问题？(y/n): ").strip().lower()
    
    if choice == 'y':
        fix_config_mismatch()
        print("\n🎉 配置修复完成！")
    else:
        print("ℹ️ 未进行修复")
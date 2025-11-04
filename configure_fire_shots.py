"""
扳机开火数配置工具
"""

import sys
import os
import re

def show_current_config():
    """显示当前配置"""
    print("🎯 当前扳机开火配置")
    print("=" * 50)
    
    # 读取config.py中的配置
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 提取autoFireShots值
        match = re.search(r'autoFireShots\s*=\s*(\d+)', content)
        if match:
            config_shots = int(match.group(1))
            print(f"📁 config.py 中的开火数: {config_shots}发")
        else:
            print("❌ 未找到config.py中的autoFireShots配置")
            
        # 提取autoFireDelay值
        delay_match = re.search(r'autoFireDelay\s*=\s*(\d+)', content)
        if delay_match:
            config_delay = int(delay_match.group(1))
            print(f"⏱️  config.py 中的开火延迟: {config_delay}ms")
            
    except FileNotFoundError:
        print("❌ 未找到config.py文件")
        return None, None
    
    # 读取auto_trigger_system.py中的默认配置
    try:
        with open('auto_trigger_system.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 提取shots_per_trigger默认值
        match = re.search(r'self\.shots_per_trigger\s*=\s*(\d+)', content)
        if match:
            trigger_shots = int(match.group(1))
            print(f"🔫 auto_trigger_system.py 中的默认开火数: {trigger_shots}发")
        else:
            print("❌ 未找到auto_trigger_system.py中的shots_per_trigger配置")
            
        # 提取shot_interval默认值
        interval_match = re.search(r'self\.shot_interval\s*=\s*([\d.]+)', content)
        if interval_match:
            trigger_interval = float(interval_match.group(1))
            print(f"⏱️  auto_trigger_system.py 中的连发间隔: {trigger_interval}s")
            
    except FileNotFoundError:
        print("❌ 未找到auto_trigger_system.py文件")
        
    return config_shots if 'config_shots' in locals() else None, config_delay if 'config_delay' in locals() else None

def update_config_shots(new_shots, new_delay=None):
    """更新config.py中的开火数"""
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新autoFireShots
        content = re.sub(
            r'autoFireShots\s*=\s*\d+',
            f'autoFireShots = {new_shots}',
            content
        )
        
        # 如果提供了新的延迟，也更新它
        if new_delay is not None:
            content = re.sub(
                r'autoFireDelay\s*=\s*\d+',
                f'autoFireDelay = {new_delay}',
                content
            )
        
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ config.py 已更新: autoFireShots = {new_shots}")
        if new_delay is not None:
            print(f"✅ config.py 已更新: autoFireDelay = {new_delay}ms")
            
    except Exception as e:
        print(f"❌ 更新config.py失败: {e}")

def update_trigger_shots(new_shots, new_interval=None):
    """更新auto_trigger_system.py中的默认开火数"""
    try:
        with open('auto_trigger_system.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新shots_per_trigger
        content = re.sub(
            r'self\.shots_per_trigger\s*=\s*\d+',
            f'self.shots_per_trigger = {new_shots}',
            content
        )
        
        # 如果提供了新的间隔，也更新它
        if new_interval is not None:
            content = re.sub(
                r'self\.shot_interval\s*=\s*[\d.]+',
                f'self.shot_interval = {new_interval}',
                content
            )
        
        with open('auto_trigger_system.py', 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ auto_trigger_system.py 已更新: shots_per_trigger = {new_shots}")
        if new_interval is not None:
            print(f"✅ auto_trigger_system.py 已更新: shot_interval = {new_interval}s")
            
    except Exception as e:
        print(f"❌ 更新auto_trigger_system.py失败: {e}")

def main():
    print("🔫 扳机开火数配置工具")
    print("=" * 50)
    
    # 显示当前配置
    current_shots, current_delay = show_current_config()
    
    print("\n" + "=" * 50)
    print("💡 配置说明:")
    print("• config.py 中的 autoFireShots: 影响main_onnx.py中的自动开火")
    print("• auto_trigger_system.py 中的 shots_per_trigger: 影响扳机系统的连发")
    print("• 建议两个值保持一致以获得最佳体验")
    print("=" * 50)
    
    # 预设选项
    presets = [
        (1, 0, "单发模式 (精确射击)"),
        (2, 60, "双发模式 (平衡)"),
        (3, 50, "三发模式 (压制)"),
        (5, 40, "连发模式 (火力覆盖)"),
    ]
    
    print("\n🎯 预设配置选项:")
    for i, (shots, delay, desc) in enumerate(presets, 1):
        print(f"{i}. {desc} - {shots}发, {delay}ms间隔")
    
    print("5. 自定义配置")
    
    while True:
        try:
            choice = input("\n请选择配置 (1-5, 或按Enter保持当前设置): ").strip()
            
            if not choice:
                print("保持当前设置")
                break
                
            choice_num = int(choice)
            
            if 1 <= choice_num <= 4:
                shots, delay, desc = presets[choice_num - 1]
                print(f"\n🔧 应用预设: {desc}")
                
                # 更新两个文件
                update_config_shots(shots, delay)
                update_trigger_shots(shots, delay/1000.0)  # 转换为秒
                
                print(f"\n✅ 配置完成! 开火数已设置为 {shots}发")
                break
                
            elif choice_num == 5:
                # 自定义配置
                print("\n🔧 自定义配置:")
                
                shots = int(input(f"开火数 (当前: {current_shots if current_shots else 2}): ") or (current_shots if current_shots else 2))
                delay = int(input(f"开火延迟(ms) (当前: {current_delay if current_delay else 60}): ") or (current_delay if current_delay else 60))
                
                # 更新配置
                update_config_shots(shots, delay)
                update_trigger_shots(shots, delay/1000.0)
                
                print(f"\n✅ 自定义配置完成! 开火数: {shots}发, 延迟: {delay}ms")
                break
                
            else:
                print("请输入1-5之间的数字")
                
        except ValueError:
            print("请输入有效的数字")
        except KeyboardInterrupt:
            print("\n操作取消")
            break

if __name__ == "__main__":
    main()
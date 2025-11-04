#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扳机系统阈值配置文件
提供不同游戏类型和精度要求的预设配置
"""

import json
import os

class ThresholdConfig:
    """阈值配置管理器"""
    
    def __init__(self, config_file="trigger_threshold_config.json"):
        """初始化配置管理器"""
        self.config_file = config_file
        self.presets = {
            "ultra_precision": {
                "name": "超高精度模式",
                "description": "适用于需要极高精度的竞技游戏",
                "alignment_threshold": 20,
                "precise_alignment_threshold": 20.0,
                "xy_check_threshold": 20.0,
                "angle_threshold": 0.2,
                "precise_angle_threshold": 0.15,
                "use_angle_threshold": True,
                "cooldown_duration": 0.3,
                "shots_per_trigger": 1,
                "shot_interval": 0.2,
                "games": ["VALORANT", "CS2", "Rainbow Six Siege"]
            },
            "high_precision": {
                "name": "高精度模式", 
                "description": "平衡精度和反应速度",
                "alignment_threshold": 20,
                "precise_alignment_threshold": 20.0,
                "xy_check_threshold": 20.0,
                "angle_threshold": 0.3,
                "precise_angle_threshold": 0.2,
                "use_angle_threshold": True,
                "cooldown_duration": 0.4,
                "shots_per_trigger": 2,
                "shot_interval": 0.25,
                "games": ["Apex Legends", "Overwatch 2"]
            },
            "balanced": {
                "name": "平衡模式",
                "description": "当前默认设置，适合大多数游戏",
                "alignment_threshold": 20,
                "precise_alignment_threshold": 20.0,
                "xy_check_threshold": 20.0,
                "angle_threshold": 0.5,
                "precise_angle_threshold": 0.3,
                "use_angle_threshold": True,
                "cooldown_duration": 0.5,
                "shots_per_trigger": 2,
                "shot_interval": 0.3,
                "games": ["Fortnite", "PUBG", "Call of Duty"]
            },
            "relaxed": {
                "name": "宽松模式",
                "description": "更快的反应速度，适合快节奏游戏",
                "alignment_threshold": 20,
                "precise_alignment_threshold": 20.0,
                "xy_check_threshold": 20.0,
                "angle_threshold": 0.8,
                "precise_angle_threshold": 0.5,
                "use_angle_threshold": True,
                "cooldown_duration": 0.6,
                "shots_per_trigger": 2,
                "shot_interval": 0.35,
                "games": ["Battlefield", "Titanfall 2"]
            },
            "ultra_relaxed": {
                "name": "超宽松模式",
                "description": "最快反应，适合休闲游戏或练习",
                "alignment_threshold": 20,
                "precise_alignment_threshold": 20.0,
                "xy_check_threshold": 20.0,
                "angle_threshold": 1.2,
                "precise_angle_threshold": 0.8,
                "use_angle_threshold": True,
                "cooldown_duration": 0.8,
                "shots_per_trigger": 3,
                "shot_interval": 0.4,
                "games": ["休闲射击游戏", "练习模式"]
            }
        }
        
        self.current_preset = "balanced"
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_preset = data.get('current_preset', 'balanced')
                    
                    # 从JSON文件覆盖内置预设的值
                    if 'presets' in data:
                        for preset_name, preset_config in data['presets'].items():
                            if preset_name in self.presets:
                                # 更新现有预设的值
                                self.presets[preset_name].update(preset_config)
                            else:
                                # 添加新的自定义预设
                                self.presets[preset_name] = preset_config
                    
                    # 合并用户自定义配置（向后兼容）
                    if 'custom_presets' in data:
                        self.presets.update(data['custom_presets'])
                        
                print(f"[CONFIG] 已加载配置文件: {self.config_file}")
            except Exception as e:
                print(f"[CONFIG] 加载配置文件失败: {e}")
        else:
            self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        try:
            data = {
                'current_preset': self.current_preset,
                'presets': self.presets,
                'version': '1.0'
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[CONFIG] 已保存配置文件: {self.config_file}")
        except Exception as e:
            print(f"[CONFIG] 保存配置文件失败: {e}")
    
    def get_current_config(self):
        """获取当前配置"""
        return self.presets.get(self.current_preset, self.presets['balanced'])
    
    def set_preset(self, preset_name):
        """设置预设配置"""
        if preset_name in self.presets:
            self.current_preset = preset_name
            self.save_config()
            print(f"[CONFIG] 已切换到预设: {self.presets[preset_name]['name']}")
            return True
        else:
            print(f"[CONFIG] 未找到预设: {preset_name}")
            return False
    
    def list_presets(self):
        """列出所有预设"""
        print("\n📋 可用的阈值预设:")
        print("=" * 60)
        for key, preset in self.presets.items():
            current_mark = " ✅" if key == self.current_preset else ""
            print(f"{key:15} | {preset['name']}{current_mark}")
            print(f"{'':15} | {preset['description']}")
            
            # 显示角度阈值信息（如果启用）
            if preset.get('use_angle_threshold', False):
                print(f"{'':15} | 🎯 角度阈值: {preset['angle_threshold']:.1f}°, 冷却: {preset['cooldown_duration']}s")
            else:
                print(f"{'':15} | 📐 像素阈值: {preset['alignment_threshold']}px, 冷却: {preset['cooldown_duration']}s")
            
            print(f"{'':15} | 适用游戏: {', '.join(preset['games'][:3])}")
            print("-" * 60)
    
    def create_custom_preset(self, name, config_dict):
        """创建自定义预设"""
        required_keys = [
            'alignment_threshold', 'precise_alignment_threshold', 
            'xy_check_threshold', 'cooldown_duration', 
            'shots_per_trigger', 'shot_interval'
        ]
        
        # 验证配置
        for key in required_keys:
            if key not in config_dict:
                print(f"[CONFIG] 缺少必需参数: {key}")
                return False
        
        # 添加默认值
        config_dict.setdefault('name', name)
        config_dict.setdefault('description', '用户自定义配置')
        config_dict.setdefault('games', ['自定义'])
        
        self.presets[name] = config_dict
        self.save_config()
        print(f"[CONFIG] 已创建自定义预设: {name}")
        return True
    
    def apply_to_trigger_system(self, trigger_system):
        """将当前配置应用到扳机系统"""
        config = self.get_current_config()
        
        # 应用像素阈值（向后兼容）
        trigger_system.alignment_threshold = config['alignment_threshold']
        trigger_system.precise_alignment_threshold = config['precise_alignment_threshold']
        trigger_system.xy_check_threshold = config['xy_check_threshold']
        
        # 应用角度阈值（如果存在）
        if 'angle_threshold' in config:
            trigger_system.angle_threshold = config['angle_threshold']
        if 'precise_angle_threshold' in config:
            trigger_system.precise_angle_threshold = config['precise_angle_threshold']
        if 'use_angle_threshold' in config:
            trigger_system.use_angle_threshold = config['use_angle_threshold']
        
        # 应用其他配置
        trigger_system.cooldown_duration = config['cooldown_duration']
        trigger_system.shots_per_trigger = config['shots_per_trigger']
        trigger_system.shot_interval = config['shot_interval']
        
        print(f"[CONFIG] 已应用配置: {config['name']}")
        if config.get('use_angle_threshold', False):
            print(f"[CONFIG] 🎯 角度阈值: {config['angle_threshold']:.1f}°, 冷却: {config['cooldown_duration']}s")
        else:
            print(f"[CONFIG] 📐 像素阈值: {config['alignment_threshold']}px, 冷却: {config['cooldown_duration']}s")
        
        return config
    
    def get_recommended_preset(self, game_name):
        """根据游戏名称推荐预设"""
        game_name_lower = game_name.lower()
        
        for preset_key, preset in self.presets.items():
            for game in preset['games']:
                if game.lower() in game_name_lower or game_name_lower in game.lower():
                    return preset_key, preset
        
        # 默认推荐
        return 'balanced', self.presets['balanced']

def main():
    """配置工具主函数"""
    config = ThresholdConfig()
    
    while True:
        print("\n🎯 扳机系统阈值配置工具")
        print("=" * 40)
        print("1. 查看当前配置")
        print("2. 列出所有预设")
        print("3. 切换预设")
        print("4. 游戏推荐")
        print("5. 创建自定义预设")
        print("6. 退出")
        
        try:
            choice = input("\n请选择操作 (1-6): ").strip()
            
            if choice == "1":
                current = config.get_current_config()
                print(f"\n当前配置: {current['name']}")
                print(f"描述: {current['description']}")
                print(f"阈值设置:")
                print(f"  - 对齐阈值: {current['alignment_threshold']}px")
                print(f"  - 精确阈值: {current['precise_alignment_threshold']}px")
                print(f"  - X/Y检查: {current['xy_check_threshold']}px")
                print(f"  - 冷却时间: {current['cooldown_duration']}s")
                print(f"  - 连发数量: {current['shots_per_trigger']}发")
                print(f"  - 连发间隔: {current['shot_interval']}s")
                
            elif choice == "2":
                config.list_presets()
                
            elif choice == "3":
                config.list_presets()
                preset_name = input("\n请输入预设名称: ").strip()
                config.set_preset(preset_name)
                
            elif choice == "4":
                game_name = input("\n请输入游戏名称: ").strip()
                preset_key, preset = config.get_recommended_preset(game_name)
                print(f"\n推荐预设: {preset['name']}")
                print(f"描述: {preset['description']}")
                
                apply = input("是否应用此预设? (y/n): ").strip().lower()
                if apply == 'y':
                    config.set_preset(preset_key)
                    
            elif choice == "5":
                print("\n创建自定义预设:")
                name = input("预设名称: ").strip()
                
                # 询问用户是否使用角度阈值
                use_angle = input("使用角度阈值系统? (推荐) (y/n): ").strip().lower() == 'y'
                
                try:
                    custom_config = {
                        'name': name,
                        'description': input("描述: ").strip(),
                        'cooldown_duration': float(input("冷却时间 (秒): ")),
                        'shots_per_trigger': int(input("连发数量: ")),
                        'shot_interval': float(input("连发间隔 (秒): ")),
                        'use_angle_threshold': use_angle
                    }
                    
                    if use_angle:
                        # 角度阈值配置
                        custom_config.update({
                            'angle_threshold': float(input("角度阈值 (度, 推荐0.3-1.0): ")),
                            'precise_angle_threshold': float(input("精确角度阈值 (度, 推荐0.2-0.8): ")),
                            # 保留像素阈值作为备用
                            'alignment_threshold': 20,
                            'precise_alignment_threshold': 20.0,
                            'xy_check_threshold': 20.0
                        })
                    else:
                        # 像素阈值配置
                        custom_config.update({
                            'alignment_threshold': float(input("对齐阈值 (像素): ")),
                            'precise_alignment_threshold': float(input("精确阈值 (像素): ")),
                            'xy_check_threshold': float(input("X/Y检查阈值 (像素): ")),
                            # 默认角度阈值
                            'angle_threshold': 0.5,
                            'precise_angle_threshold': 0.3
                        })
                    
                    config.create_custom_preset(name, custom_config)
                    
                except ValueError:
                    print("输入格式错误，请输入有效数值")
                    
            elif choice == "6":
                print("退出配置工具...")
                break
                
            else:
                print("无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            break
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
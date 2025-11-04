#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扳机开火诊断工具
用于诊断为什么目标重合了但扳机不开火的问题
"""

import time
import json
from auto_trigger_system import AutoTriggerSystem
from threshold_config import ThresholdConfig

class TriggerDiagnostic:
    def __init__(self):
        """初始化诊断工具"""
        self.trigger_system = AutoTriggerSystem()
        self.config = ThresholdConfig()
        self.test_scenarios = []
        
    def run_comprehensive_diagnostic(self):
        """运行全面的扳机诊断"""
        print("🔧 扳机开火诊断工具")
        print("="*60)
        
        # 1. 检查系统状态
        self.check_system_status()
        
        # 2. 检查配置
        self.check_configuration()
        
        # 3. 测试对齐检测
        self.test_alignment_detection()
        
        # 4. 测试开火逻辑
        self.test_firing_logic()
        
        # 5. 模拟实际场景
        self.simulate_real_scenarios()
        
        # 6. 提供解决方案
        self.provide_solutions()
    
    def check_system_status(self):
        """检查系统状态"""
        print("\n📊 系统状态检查")
        print("-" * 40)
        
        status = self.trigger_system.get_status_info()
        
        print(f"✓ 扳机功能状态: {'启用' if status['enabled'] else '❌ 禁用'}")
        print(f"✓ 对齐阈值: {status['alignment_threshold']}像素")
        print(f"✓ 精确阈值: {self.trigger_system.precise_alignment_threshold}像素")
        print(f"✓ XY检查阈值: {self.trigger_system.xy_check_threshold}像素")
        print(f"✓ 冷却时间: {status['cooldown_duration']}秒")
        print(f"✓ 连发数量: {status['shots_per_trigger']}发")
        print(f"✓ 是否在冷却: {'是' if status['is_on_cooldown'] else '否'}")
        print(f"✓ 总触发次数: {status['total_triggers']}")
        print(f"✓ 总射击次数: {status['total_shots']}")
        
        # 检查潜在问题
        issues = []
        if not status['enabled']:
            issues.append("❌ 扳机功能被禁用")
        if status['is_on_cooldown']:
            issues.append(f"⏰ 正在冷却中，剩余 {status['cooldown_remaining']:.1f}秒")
        if status['alignment_threshold'] > 10:
            issues.append("⚠️ 对齐阈值可能过大")
        if self.trigger_system.xy_check_threshold < 1:
            issues.append("⚠️ XY检查阈值可能过小")
            
        if issues:
            print("\n🚨 发现的问题:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n✅ 系统状态正常")
    
    def check_configuration(self):
        """检查配置"""
        print("\n⚙️ 配置检查")
        print("-" * 40)
        
        try:
            # 检查配置文件
            with open('trigger_threshold_config.json', 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            current_preset = config_data.get('current_preset', 'unknown')
            print(f"✓ 当前预设: {current_preset}")
            
            # 显示当前配置
            if current_preset in config_data.get('presets', {}):
                preset_config = config_data['presets'][current_preset]
                print(f"✓ 配置详情:")
                for key, value in preset_config.items():
                    print(f"  - {key}: {value}")
            
        except FileNotFoundError:
            print("⚠️ 配置文件不存在，使用默认配置")
        except Exception as e:
            print(f"❌ 配置文件读取错误: {e}")
    
    def test_alignment_detection(self):
        """测试对齐检测"""
        print("\n🎯 对齐检测测试")
        print("-" * 40)
        
        # 测试场景：不同的目标位置
        test_cases = [
            # (target_x, target_y, description)
            (0.5, 0.5, "完美中心"),
            (0.501, 0.5, "轻微右偏"),
            (0.499, 0.5, "轻微左偏"),
            (0.5, 0.501, "轻微下偏"),
            (0.5, 0.499, "轻微上偏"),
            (0.51, 0.51, "右下偏移"),
            (0.52, 0.52, "较大偏移"),
            (0.55, 0.55, "明显偏移"),
        ]
        
        detection_center = (0.5, 0.5)  # 检测中心
        
        print("测试不同位置的对齐检测:")
        for target_x, target_y, description in test_cases:
            # 计算距离
            distance = self.trigger_system.calculate_crosshair_distance(
                target_x, target_y, detection_center
            )
            
            # 检查是否对齐
            is_aligned = self.trigger_system.is_aligned(
                target_x, target_y, detection_center, 0.0,
                game_fov=103,  # 默认FOV
                detection_size=320,  # 默认检测尺寸
                game_width=2560,  # 默认游戏宽度
                game_height=1600  # 默认游戏高度
            )
            
            # 计算像素偏移
            x_offset = abs(target_x - detection_center[0]) * 160
            y_offset = abs(target_y - detection_center[1]) * 160
            
            status = "✅ 对齐" if is_aligned else "❌ 未对齐"
            print(f"  {description}: {status} (距离: {distance:.1f}px, X: {x_offset:.1f}px, Y: {y_offset:.1f}px)")
    
    def test_firing_logic(self):
        """测试开火逻辑"""
        print("\n🔫 开火逻辑测试")
        print("-" * 40)
        
        # 保存原始状态
        original_enabled = self.trigger_system.enabled
        original_last_fire_time = self.trigger_system.last_fire_time
        
        # 启用扳机
        self.trigger_system.set_enabled(True)
        
        # 重置冷却时间
        self.trigger_system.last_fire_time = 0
        
        print("测试开火条件:")
        
        # 测试1: 完美对齐
        print("\n1. 测试完美对齐:")
        result = self.trigger_system.check_and_fire(0.5, 0.5, (0.5, 0.5), 0.0)
        print(f"   结果: {'✅ 开火' if result else '❌ 未开火'}")
        
        # 测试2: 冷却时间测试
        print("\n2. 测试冷却时间:")
        result = self.trigger_system.check_and_fire(0.5, 0.5, (0.5, 0.5), 0.0)
        print(f"   结果: {'❌ 应该被冷却阻止' if result else '✅ 正确被冷却阻止'}")
        
        # 等待冷却结束
        print(f"   等待冷却结束 ({self.trigger_system.cooldown_duration}秒)...")
        time.sleep(self.trigger_system.cooldown_duration + 0.1)
        
        # 测试3: 冷却后再次开火
        print("\n3. 测试冷却后开火:")
        result = self.trigger_system.check_and_fire(0.5, 0.5, (0.5, 0.5), 0.0)
        print(f"   结果: {'✅ 开火' if result else '❌ 未开火'}")
        
        # 测试4: 禁用状态测试
        print("\n4. 测试禁用状态:")
        self.trigger_system.set_enabled(False)
        time.sleep(self.trigger_system.cooldown_duration + 0.1)
        result = self.trigger_system.check_and_fire(0.5, 0.5, (0.5, 0.5), 0.0)
        print(f"   结果: {'❌ 应该被禁用阻止' if result else '✅ 正确被禁用阻止'}")
        
        # 恢复原始状态
        self.trigger_system.enabled = original_enabled
        self.trigger_system.last_fire_time = original_last_fire_time
    
    def simulate_real_scenarios(self):
        """模拟真实场景"""
        print("\n🎮 真实场景模拟")
        print("-" * 40)
        
        # 启用扳机进行测试
        self.trigger_system.set_enabled(True)
        self.trigger_system.last_fire_time = 0
        
        scenarios = [
            {
                "name": "敌人头部完美重合",
                "target_x": 0.5,
                "target_y": 0.48,  # 稍微上偏，模拟头部
                "headshot_offset": 0.02,
                "expected": True
            },
            {
                "name": "敌人身体重合",
                "target_x": 0.5,
                "target_y": 0.52,  # 稍微下偏，模拟身体
                "headshot_offset": 0.0,
                "expected": True
            },
            {
                "name": "敌人轻微偏移",
                "target_x": 0.505,
                "target_y": 0.505,
                "headshot_offset": 0.0,
                "expected": False  # 取决于阈值设置
            },
            {
                "name": "敌人明显偏移",
                "target_x": 0.52,
                "target_y": 0.52,
                "headshot_offset": 0.0,
                "expected": False
            }
        ]
        
        for i, scenario in enumerate(scenarios):
            print(f"\n场景 {i+1}: {scenario['name']}")
            
            # 重置冷却
            if i > 0:
                time.sleep(self.trigger_system.cooldown_duration + 0.1)
            
            result = self.trigger_system.check_and_fire(
                scenario['target_x'],
                scenario['target_y'],
                (0.5, 0.5),
                scenario['headshot_offset'],
                game_fov=103,  # 默认FOV
                detection_size=320,  # 默认检测尺寸
                game_width=2560,  # 默认游戏宽度
                game_height=1600  # 默认游戏高度
            )
            
            expected_text = "应该开火" if scenario['expected'] else "不应开火"
            actual_text = "开火了" if result else "未开火"
            
            if result == scenario['expected']:
                print(f"   ✅ {actual_text} ({expected_text})")
            else:
                print(f"   ❌ {actual_text} (但{expected_text})")
    
    def provide_solutions(self):
        """提供解决方案"""
        print("\n💡 问题解决方案")
        print("-" * 40)
        
        print("如果目标重合但不开火，可能的原因和解决方案:")
        print()
        print("1. 🔧 扳机功能被禁用")
        print("   解决方案: 检查扳机开关状态，确保已启用")
        print("   命令: trigger_system.set_enabled(True)")
        print()
        print("2. ⏰ 冷却时间未结束")
        print("   解决方案: 等待冷却时间结束，或调整冷却时间")
        print("   命令: 运行 python configure_trigger.py 调整冷却时间")
        print()
        print("3. 🎯 对齐检测过于严格")
        print("   解决方案: 调整对齐阈值，使其更宽松")
        print("   建议: alignment_threshold > 5, xy_check_threshold > 2")
        print()
        print("4. 📐 XY偏移检查过于严格")
        print("   解决方案: 增大xy_check_threshold值")
        print("   建议: 从2像素增加到3-4像素")
        print()
        print("5. 🖱️ 鼠标驱动问题")
        print("   解决方案: 检查G-Hub驱动是否正常工作")
        print("   测试: 运行 python simple_ghub_test.py")
        print()
        print("6. 🎮 游戏窗口焦点问题")
        print("   解决方案: 确保游戏窗口处于前台焦点状态")
        print()
        
        # 提供快速修复建议
        print("🚀 快速修复建议:")
        print("1. 运行: python configure_trigger.py")
        print("2. 选择 '2' 切换到 'relaxed' 预设")
        print("3. 或选择 '4' 自定义更宽松的阈值")
        print("4. 测试开火功能")

def main():
    """主函数"""
    diagnostic = TriggerDiagnostic()
    
    try:
        diagnostic.run_comprehensive_diagnostic()
    except KeyboardInterrupt:
        print("\n\n诊断被用户中断")
    except Exception as e:
        print(f"\n❌ 诊断过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
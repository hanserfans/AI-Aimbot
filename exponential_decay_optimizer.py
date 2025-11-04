#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指数衰减移动优化器
提供多种衰减系数和移动策略的分析和优化工具
"""

import math
import matplotlib.pyplot as plt
import numpy as np

class ExponentialDecayOptimizer:
    """指数衰减移动优化器"""
    
    def __init__(self):
        self.presets = {
            "aggressive": {"decay_factor": 1.5, "description": "激进递减 - 第一步移动更多"},
            "balanced": {"decay_factor": 1.2, "description": "平衡递减 - 当前使用"},
            "gentle": {"decay_factor": 0.9, "description": "温和递减 - 更平滑的过渡"},
            "linear": {"decay_factor": 0.0, "description": "线性递减 - 等差数列"}
        }
    
    def calculate_movement_ratios(self, decay_factor: float, num_steps: int = 5) -> list:
        """计算移动比例"""
        if decay_factor == 0.0:  # 线性递减
            # 等差数列：5, 4, 3, 2, 1
            step_ratios = [num_steps - i for i in range(num_steps)]
        else:  # 指数递减
            step_ratios = [math.exp(-decay_factor * i) for i in range(num_steps)]
        
        # 归一化
        total_ratio = sum(step_ratios)
        return [ratio / total_ratio for ratio in step_ratios]
    
    def analyze_preset(self, preset_name: str, distance: float = 200) -> dict:
        """分析预设策略"""
        if preset_name not in self.presets:
            raise ValueError(f"未知预设: {preset_name}")
        
        config = self.presets[preset_name]
        ratios = self.calculate_movement_ratios(config["decay_factor"])
        
        # 计算实际距离
        distances = [distance * ratio for ratio in ratios]
        cumulative = np.cumsum(distances)
        
        # 计算递减率
        reductions = []
        for i in range(len(ratios) - 1):
            reduction = (ratios[i] - ratios[i+1]) / ratios[i] * 100
            reductions.append(reduction)
        
        return {
            "name": preset_name,
            "description": config["description"],
            "decay_factor": config["decay_factor"],
            "ratios": ratios,
            "distances": distances,
            "cumulative": cumulative.tolist(),
            "reductions": reductions,
            "first_step_percentage": ratios[0] * 100,
            "first_two_steps_percentage": sum(ratios[:2]) * 100,
            "first_three_steps_percentage": sum(ratios[:3]) * 100
        }
    
    def compare_all_presets(self, distance: float = 200):
        """比较所有预设策略"""
        print(f"🔬 指数衰减策略对比分析 ({distance}像素移动)")
        print("=" * 80)
        
        results = {}
        for preset_name in self.presets:
            results[preset_name] = self.analyze_preset(preset_name, distance)
        
        # 打印对比表格
        print(f"{'策略':<12} {'衰减系数':<8} {'第1步':<8} {'前2步':<8} {'前3步':<8} {'描述'}")
        print("-" * 80)
        
        for preset_name, result in results.items():
            print(f"{preset_name:<12} {result['decay_factor']:<8.1f} "
                  f"{result['first_step_percentage']:<8.1f}% "
                  f"{result['first_two_steps_percentage']:<8.1f}% "
                  f"{result['first_three_steps_percentage']:<8.1f}% "
                  f"{result['description']}")
        
        # 详细分析每个策略
        for preset_name, result in results.items():
            print(f"\n📊 {preset_name.upper()} 策略详细分析:")
            print(f"   衰减系数: {result['decay_factor']}")
            print(f"   各步距离: {[f'{d:.1f}px' for d in result['distances']]}")
            print(f"   各步比例: {[f'{r:.3f}' for r in result['ratios']]}")
            print(f"   递减率: {[f'{r:.1f}%' for r in result['reductions']]}")
            
            # 验证是否满足要求
            if result['first_step_percentage'] >= 50:
                print(f"   ✅ 第一步移动 {result['first_step_percentage']:.1f}% >= 50%")
            else:
                print(f"   ❌ 第一步移动 {result['first_step_percentage']:.1f}% < 50%")
            
            if result['first_three_steps_percentage'] >= 80:
                print(f"   ✅ 前三步移动 {result['first_three_steps_percentage']:.1f}% >= 80%")
            else:
                print(f"   ❌ 前三步移动 {result['first_three_steps_percentage']:.1f}% < 80%")
        
        return results
    
    def generate_optimal_config(self, target_first_step: float = 70, target_three_steps: float = 90):
        """生成最优配置"""
        print(f"\n🎯 寻找最优衰减系数")
        print(f"   目标: 第1步 {target_first_step}%, 前3步 {target_three_steps}%")
        print("-" * 50)
        
        best_factor = 1.2
        best_score = float('inf')
        
        # 搜索最优衰减系数
        for factor in np.arange(0.5, 2.5, 0.1):
            ratios = self.calculate_movement_ratios(factor)
            first_step = ratios[0] * 100
            three_steps = sum(ratios[:3]) * 100
            
            # 计算偏差分数
            score = abs(first_step - target_first_step) + abs(three_steps - target_three_steps)
            
            if score < best_score:
                best_score = score
                best_factor = factor
        
        # 分析最优配置
        optimal_ratios = self.calculate_movement_ratios(best_factor)
        print(f"   最优衰减系数: {best_factor:.2f}")
        print(f"   第1步比例: {optimal_ratios[0]*100:.1f}%")
        print(f"   前3步比例: {sum(optimal_ratios[:3])*100:.1f}%")
        print(f"   各步比例: {[f'{r:.3f}' for r in optimal_ratios]}")
        
        return best_factor, optimal_ratios
    
    def plot_comparison(self, distance: float = 200):
        """绘制策略对比图"""
        try:
            plt.figure(figsize=(15, 10))
            
            # 子图1: 各步移动距离对比
            plt.subplot(2, 2, 1)
            for preset_name in self.presets:
                result = self.analyze_preset(preset_name, distance)
                steps = range(1, 6)
                plt.bar([s + 0.15 * list(self.presets.keys()).index(preset_name) for s in steps], 
                       result['distances'], width=0.15, label=preset_name, alpha=0.7)
            
            plt.xlabel('移动步骤')
            plt.ylabel('移动距离 (像素)')
            plt.title('各步移动距离对比')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 子图2: 累积移动距离
            plt.subplot(2, 2, 2)
            for preset_name in self.presets:
                result = self.analyze_preset(preset_name, distance)
                steps = range(1, 6)
                plt.plot(steps, result['cumulative'], marker='o', label=preset_name, linewidth=2)
            
            plt.xlabel('移动步骤')
            plt.ylabel('累积距离 (像素)')
            plt.title('累积移动距离')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 子图3: 移动比例分布
            plt.subplot(2, 2, 3)
            for preset_name in self.presets:
                result = self.analyze_preset(preset_name, distance)
                steps = range(1, 6)
                plt.plot(steps, [r*100 for r in result['ratios']], 
                        marker='s', label=preset_name, linewidth=2)
            
            plt.xlabel('移动步骤')
            plt.ylabel('移动比例 (%)')
            plt.title('各步移动比例')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 子图4: 递减率对比
            plt.subplot(2, 2, 4)
            for preset_name in self.presets:
                result = self.analyze_preset(preset_name, distance)
                steps = range(1, 5)  # 只有4个递减率
                plt.bar([s + 0.15 * list(self.presets.keys()).index(preset_name) for s in steps], 
                       result['reductions'], width=0.15, label=preset_name, alpha=0.7)
            
            plt.xlabel('步骤转换')
            plt.ylabel('递减率 (%)')
            plt.title('步骤间递减率')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('exponential_decay_comparison.png', dpi=300, bbox_inches='tight')
            plt.show()
            
        except ImportError:
            print("⚠️  matplotlib未安装，跳过图表生成")

def main():
    """主函数"""
    optimizer = ExponentialDecayOptimizer()
    
    # 对比所有预设策略
    results = optimizer.compare_all_presets(200)
    
    # 寻找最优配置
    optimal_factor, optimal_ratios = optimizer.generate_optimal_config(70, 90)
    
    # 生成配置建议
    print(f"\n💡 配置建议:")
    print(f"   推荐使用 'balanced' 策略 (衰减系数 1.2)")
    print(f"   第一步移动 70.1%，前三步移动 97.5%")
    print(f"   完美满足递减要求，移动平滑自然")
    
    # 尝试绘制对比图
    optimizer.plot_comparison(200)

if __name__ == "__main__":
    main()
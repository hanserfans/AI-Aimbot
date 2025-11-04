#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合衰减策略测试
测试所有可用的指数衰减策略，验证200像素内5次移动的效果
"""

import math
import time
from typing import List, Tuple, Dict, Any
from non_blocking_smooth_movement import NonBlockingSmoothMovement

class ComprehensiveDecayTester:
    """综合衰减策略测试器"""
    
    def __init__(self):
        # 创建模拟的移动函数
        def mock_move_function(x: int, y: int) -> bool:
            """模拟鼠标移动函数"""
            return True  # 总是返回成功
        
        self.movement_system = NonBlockingSmoothMovement(mock_move_function)
        self.test_results = {}
        
    def simulate_mouse_move(self, dx: float, dy: float) -> bool:
        """模拟鼠标移动"""
        return True  # 总是成功
    
    def test_strategy(self, strategy: str, test_cases: List[Tuple[int, int]]) -> Dict[str, Any]:
        """测试特定策略"""
        print(f"\n{'='*60}")
        print(f"🧪 测试策略: {strategy.upper()}")
        print(f"{'='*60}")
        
        # 设置策略
        success = self.movement_system.set_decay_strategy(strategy)
        if not success:
            return {"error": "策略设置失败"}
        
        # 获取策略信息
        strategy_info = self.movement_system.get_decay_info()
        print(f"📊 策略信息:")
        print(f"   衰减系数: {strategy_info['decay_factor']}")
        print(f"   第一步移动: {strategy_info['first_step_percentage']:.1f}%")
        print(f"   前三步移动: {strategy_info['first_three_steps_percentage']:.1f}%")
        
        results = {
            "strategy": strategy,
            "strategy_info": strategy_info,
            "test_cases": [],
            "success_count": 0,
            "total_count": len(test_cases)
        }
        
        # 执行测试案例
        for i, (target_x, target_y) in enumerate(test_cases, 1):
            print(f"\n📍 测试案例 {i}: 移动到 ({target_x}, {target_y})")
            
            # 计算移动距离
            distance = math.sqrt(target_x**2 + target_y**2)
            print(f"   总距离: {distance:.1f}px")
            
            # 计算移动步骤 (dx, dy 相对于当前位置的偏移)
            steps = self.movement_system.calculate_movement_steps(target_x, target_y)
            
            # 分析步骤
            case_result = self.analyze_movement_steps(steps, distance)
            case_result.update({
                "target": (target_x, target_y),
                "distance": distance,
                "steps_count": len(steps)
            })
            
            results["test_cases"].append(case_result)
            
            if case_result["success"]:
                results["success_count"] += 1
                print(f"   ✅ 测试成功")
            else:
                print(f"   ❌ 测试失败: {case_result['failure_reason']}")
        
        # 计算成功率
        success_rate = (results["success_count"] / results["total_count"]) * 100
        results["success_rate"] = success_rate
        
        print(f"\n📈 策略 {strategy} 总结:")
        print(f"   成功率: {success_rate:.1f}% ({results['success_count']}/{results['total_count']})")
        
        return results
    
    def analyze_movement_steps(self, steps: List[Tuple[float, float]], total_distance: float) -> Dict[str, Any]:
        """分析移动步骤"""
        if not steps:
            return {"success": False, "failure_reason": "无移动步骤"}
        
        # 计算每步距离和累积距离
        step_distances = []
        cumulative_distances = []
        cumulative_distance = 0
        
        for step_x, step_y in steps:
            step_distance = math.sqrt(step_x**2 + step_y**2)
            step_distances.append(step_distance)
            cumulative_distance += step_distance
            cumulative_distances.append(cumulative_distance)
        
        # 计算累积百分比
        cumulative_percentages = [d / total_distance * 100 for d in cumulative_distances]
        
        # 检查递减性
        is_decreasing = all(step_distances[i] >= step_distances[i+1] for i in range(len(step_distances)-1))
        
        # 检查是否在5步内完成
        completed_in_5_steps = len(steps) <= 5
        
        # 检查第一步是否移动足够距离（建议>=40%）
        first_step_percentage = (step_distances[0] / total_distance) * 100 if step_distances else 0
        first_step_adequate = first_step_percentage >= 40
        
        # 检查前三步是否移动足够距离（建议>=75%）
        first_three_percentage = (sum(step_distances[:3]) / total_distance) * 100 if len(step_distances) >= 3 else 0
        first_three_adequate = first_three_percentage >= 75
        
        # 判断成功条件
        success = (completed_in_5_steps and is_decreasing and 
                  first_step_adequate and first_three_adequate)
        
        failure_reasons = []
        if not completed_in_5_steps:
            failure_reasons.append(f"步数超过5步({len(steps)}步)")
        if not is_decreasing:
            failure_reasons.append("距离未递减")
        if not first_step_adequate:
            failure_reasons.append(f"第一步移动不足({first_step_percentage:.1f}%<40%)")
        if not first_three_adequate:
            failure_reasons.append(f"前三步移动不足({first_three_percentage:.1f}%<75%)")
        
        return {
            "success": success,
            "failure_reason": "; ".join(failure_reasons) if failure_reasons else None,
            "step_distances": step_distances,
            "cumulative_percentages": cumulative_percentages,
            "is_decreasing": is_decreasing,
            "first_step_percentage": first_step_percentage,
            "first_three_percentage": first_three_percentage,
            "steps_count": len(steps)
        }
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始综合衰减策略测试")
        print("=" * 80)
        
        # 定义测试案例 - 200像素内的各种移动
        test_cases = [
            # 水平和垂直移动
            (200, 0),    # 水平200px
            (0, 200),    # 垂直200px
            (-200, 0),   # 反向水平200px
            (0, -200),   # 反向垂直200px
            
            # 对角线移动
            (141, 141),  # 对角线200px (√2 * 141 ≈ 200)
            (-141, 141), # 对角线200px
            (141, -141), # 对角线200px
            (-141, -141),# 对角线200px
            
            # 中等距离移动
            (150, 0),    # 150px
            (100, 100),  # 对角线141px
            (120, 80),   # 144px
            
            # 短距离移动
            (100, 0),    # 100px
            (50, 50),    # 对角线71px
            (80, 60),    # 100px
        ]
        
        # 获取所有可用策略
        strategies = self.movement_system.get_decay_info()["available_strategies"]
        
        # 测试每个策略
        all_results = {}
        for strategy in strategies:
            results = self.test_strategy(strategy, test_cases)
            all_results[strategy] = results
            self.test_results[strategy] = results
        
        # 生成对比报告
        self.generate_comparison_report(all_results)
    
    def generate_comparison_report(self, all_results: Dict[str, Dict]):
        """生成策略对比报告"""
        print(f"\n{'='*80}")
        print("📊 策略对比报告")
        print(f"{'='*80}")
        
        # 按成功率排序
        sorted_strategies = sorted(all_results.items(), 
                                 key=lambda x: x[1]["success_rate"], 
                                 reverse=True)
        
        print(f"{'策略':<12} {'成功率':<8} {'第一步%':<8} {'前三步%':<8} {'衰减系数':<10}")
        print("-" * 60)
        
        for strategy, results in sorted_strategies:
            if "strategy_info" in results:
                info = results["strategy_info"]
                print(f"{strategy:<12} {results['success_rate']:>6.1f}% "
                      f"{info['first_step_percentage']:>6.1f}% "
                      f"{info['first_three_steps_percentage']:>6.1f}% "
                      f"{info['decay_factor']:>8.2f}")
        
        # 推荐最佳策略
        best_strategy = sorted_strategies[0][0]
        best_results = sorted_strategies[0][1]
        
        print(f"\n🏆 推荐策略: {best_strategy.upper()}")
        print(f"   成功率: {best_results['success_rate']:.1f}%")
        if "strategy_info" in best_results:
            info = best_results["strategy_info"]
            print(f"   第一步移动: {info['first_step_percentage']:.1f}%")
            print(f"   前三步移动: {info['first_three_steps_percentage']:.1f}%")
            print(f"   衰减系数: {info['decay_factor']}")

def main():
    """主函数"""
    tester = ComprehensiveDecayTester()
    tester.run_comprehensive_test()
    
    print(f"\n{'='*80}")
    print("✅ 综合测试完成！")
    print("💡 建议根据实际需求选择合适的衰减策略：")
    print("   - aggressive: 激进递减，第一步移动最多")
    print("   - balanced: 平衡递减，推荐日常使用")
    print("   - gentle: 温和递减，更平滑的移动")
    print("   - linear: 线性递减，最均匀的递减")

if __name__ == "__main__":
    main()
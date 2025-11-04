#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阈值分析工具
用于测试和分析不同像素阈值对扳机系统性能的影响
"""

import time
import math
import win32api
from auto_trigger_system import AutoTriggerSystem

class ThresholdAnalyzer:
    """阈值分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.test_scenarios = [
            # [距离, X偏移, Y偏移, 描述]
            [0, 0, 0, "完美重合"],
            [1, 0.5, 0.5, "轻微偏移"],
            [2, 1, 1, "小幅偏移"],
            [3, 1.5, 1.5, "中等偏移"],
            [4, 2, 2, "较大偏移"],
            [5, 2.5, 2.5, "临界偏移"],
            [6, 3, 3, "超出阈值"],
            [8, 4, 4, "明显偏移"],
            [10, 5, 5, "大幅偏移"]
        ]
        
        self.threshold_configs = [
            # [alignment_threshold, precise_alignment_threshold, xy_check_threshold, 描述]
            [3, 3.0, 1.5, "高精度模式"],
            [5, 5.0, 2.0, "当前设置"],
            [7, 7.0, 3.0, "宽松模式"],
            [10, 10.0, 4.0, "超宽松模式"]
        ]
        
    def test_threshold_config(self, alignment_threshold, precise_alignment_threshold, xy_check_threshold, config_name):
        """测试特定阈值配置"""
        print(f"\n{'='*60}")
        print(f"🎯 测试配置: {config_name}")
        print(f"   距离阈值: {alignment_threshold}px")
        print(f"   精确阈值: {precise_alignment_threshold}px") 
        print(f"   X/Y阈值: {xy_check_threshold}px")
        print(f"{'='*60}")
        
        # 创建临时扳机系统实例
        trigger = AutoTriggerSystem()
        trigger.alignment_threshold = alignment_threshold
        trigger.precise_alignment_threshold = precise_alignment_threshold
        
        # 模拟检测图像中心
        detection_center = (0.5, 0.5)  # 归一化坐标
        
        hit_count = 0
        total_tests = len(self.test_scenarios)
        
        for distance, x_offset, y_offset, description in self.test_scenarios:
            # 将像素偏移转换为归一化坐标（假设160x160检测图像）
            target_x = 0.5 + (x_offset / 160.0)
            target_y = 0.5 + (y_offset / 160.0)
            
            # 测试是否会触发
            would_trigger = self._simulate_alignment_check(
                target_x, target_y, detection_center, 
                alignment_threshold, precise_alignment_threshold, xy_check_threshold
            )
            
            if would_trigger:
                hit_count += 1
                status = "✅ 会触发"
            else:
                status = "❌ 不触发"
            
            print(f"  {description:12} | 距离:{distance:2}px | X:{x_offset:3.1f}px Y:{y_offset:3.1f}px | {status}")
        
        hit_rate = (hit_count / total_tests) * 100
        print(f"\n📊 触发率: {hit_count}/{total_tests} ({hit_rate:.1f}%)")
        
        # 评估配置
        if hit_rate < 30:
            evaluation = "🔴 过于严格 - 可能错过有效目标"
        elif hit_rate < 60:
            evaluation = "🟡 较为严格 - 高精度但可能反应慢"
        elif hit_rate < 80:
            evaluation = "🟢 平衡良好 - 推荐设置"
        else:
            evaluation = "🟠 较为宽松 - 反应快但精度可能不足"
            
        print(f"💡 评估: {evaluation}")
        
        return hit_rate, evaluation
    
    def _simulate_alignment_check(self, target_x, target_y, detection_center, 
                                 alignment_threshold, precise_alignment_threshold, xy_check_threshold):
        """模拟对齐检查逻辑"""
        # 计算距离（转换为像素）
        offset_x = target_x - detection_center[0]
        offset_y = target_y - detection_center[1]
        distance = math.sqrt(offset_x**2 + offset_y**2) * 160  # 转换为像素距离
        
        # 距离检查
        distance_ok = distance <= precise_alignment_threshold
        
        # X/Y偏移检查
        x_offset_px = abs(offset_x) * 160
        y_offset_px = abs(offset_y) * 160
        xy_ok = x_offset_px <= xy_check_threshold and y_offset_px <= xy_check_threshold
        
        return distance_ok and xy_ok
    
    def run_full_analysis(self):
        """运行完整的阈值分析"""
        print("🔍 扳机系统阈值分析工具")
        print("=" * 60)
        
        results = []
        
        for config in self.threshold_configs:
            alignment_th, precise_th, xy_th, name = config
            hit_rate, evaluation = self.test_threshold_config(alignment_th, precise_th, xy_th, name)
            results.append((name, hit_rate, evaluation))
        
        # 总结报告
        print(f"\n{'='*60}")
        print("📋 总结报告")
        print(f"{'='*60}")
        
        for name, hit_rate, evaluation in results:
            print(f"{name:15} | 触发率: {hit_rate:5.1f}% | {evaluation}")
        
        # 推荐设置
        print(f"\n💡 推荐设置分析:")
        print(f"   🎮 竞技游戏 (如VALORANT/CS2): 建议使用'高精度模式'")
        print(f"   🎯 休闲游戏: 建议使用'当前设置'或'宽松模式'")
        print(f"   ⚡ 快节奏游戏: 建议使用'宽松模式'")
        
        return results
    
    def interactive_test(self):
        """交互式测试模式"""
        print("\n🎮 交互式阈值测试")
        print("按住鼠标右键测试当前阈值设置...")
        print("按 ESC 键退出")
        
        trigger = AutoTriggerSystem()
        
        while True:
            # 检查ESC键退出
            if win32api.GetAsyncKeyState(0x1B) & 0x8000:  # ESC键
                print("退出测试...")
                break
            
            # 检查鼠标右键
            if win32api.GetAsyncKeyState(0x02) & 0x8000:  # 右键
                print(f"[测试] 当前阈值设置:")
                print(f"  距离阈值: {trigger.alignment_threshold}px")
                print(f"  精确阈值: {trigger.precise_alignment_threshold}px")
                print(f"  扳机状态: {'启用' if trigger.enabled else '禁用'}")
                print(f"  冷却时间: {trigger.cooldown_duration}s")
                time.sleep(0.5)  # 防止重复触发
            
            time.sleep(0.01)

def main():
    """主函数"""
    analyzer = ThresholdAnalyzer()
    
    print("选择测试模式:")
    print("1. 完整分析 (推荐)")
    print("2. 交互式测试")
    print("3. 退出")
    
    try:
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            analyzer.run_full_analysis()
        elif choice == "2":
            analyzer.interactive_test()
        elif choice == "3":
            print("退出程序...")
        else:
            print("无效选择，退出程序...")
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
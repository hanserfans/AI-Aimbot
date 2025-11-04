#!/usr/bin/env python3
"""
平滑移动算法测试脚本
对比平滑移动和普通移动的精度和效果
"""

import time
import pyautogui
from improved_adaptive_correction import ImprovedAdaptiveCorrection

def test_movement_comparison():
    """对比测试平滑移动和普通移动"""
    print("🎯 平滑移动算法对比测试")
    print("=" * 50)
    
    # 初始化自适应校正系统
    adaptive_mouse = ImprovedAdaptiveCorrection()
    
    if not adaptive_mouse.initialize():
        print("❌ G-Hub鼠标初始化失败")
        return
    
    print("✅ G-Hub鼠标初始化成功")
    
    # 测试移动列表
    test_movements = [
        (10, 0),   # 水平移动
        (0, 10),   # 垂直移动
        (15, 15),  # 对角移动
        (20, 0),   # 较大水平移动
        (0, 20),   # 较大垂直移动
        (-15, -15), # 负方向对角移动
        (25, 10),  # 混合移动
        (5, 25),   # 混合移动
    ]
    
    print("\n🔄 开始对比测试...")
    print("每个移动将测试两种方法：普通移动 vs 平滑移动")
    
    normal_results = []
    smooth_results = []
    
    for i, (dx, dy) in enumerate(test_movements):
        print(f"\n--- 测试 {i+1}: 移动 ({dx}, {dy}) ---")
        
        # 记录起始位置
        start_pos = pyautogui.position()
        print(f"起始位置: ({start_pos.x}, {start_pos.y})")
        
        # 测试普通移动
        print("🔸 测试普通移动...")
        normal_start_time = time.time()
        normal_success = adaptive_mouse.stable_move(dx, dy)
        normal_end_time = time.time()
        normal_duration = normal_end_time - normal_start_time
        
        # 检查普通移动结果
        normal_end_pos = pyautogui.position()
        normal_actual_dx = normal_end_pos.x - start_pos.x
        normal_actual_dy = normal_end_pos.y - start_pos.y
        normal_error_x = normal_actual_dx - dx
        normal_error_y = normal_actual_dy - dy
        normal_total_error = (normal_error_x**2 + normal_error_y**2)**0.5
        
        normal_results.append({
            'expected': (dx, dy),
            'actual': (normal_actual_dx, normal_actual_dy),
            'error': (normal_error_x, normal_error_y),
            'total_error': normal_total_error,
            'duration': normal_duration,
            'success': normal_success
        })
        
        print(f"  结果: 期望({dx},{dy}) 实际({normal_actual_dx},{normal_actual_dy})")
        print(f"  误差: ({normal_error_x:.1f},{normal_error_y:.1f}) 总误差: {normal_total_error:.2f}")
        print(f"  耗时: {normal_duration:.3f}秒")
        
        # 等待一下再进行下一个测试
        time.sleep(0.5)
        
        # 回到起始位置准备测试平滑移动
        current_pos = pyautogui.position()
        reset_dx = start_pos.x - current_pos.x
        reset_dy = start_pos.y - current_pos.y
        if abs(reset_dx) > 2 or abs(reset_dy) > 2:
            adaptive_mouse.stable_move(reset_dx, reset_dy)
            time.sleep(0.3)
        
        # 测试平滑移动
        print("🔹 测试平滑移动...")
        smooth_start_pos = pyautogui.position()
        smooth_start_time = time.time()
        smooth_success = adaptive_mouse.smooth_stable_move(dx, dy)
        smooth_end_time = time.time()
        smooth_duration = smooth_end_time - smooth_start_time
        
        # 检查平滑移动结果
        smooth_end_pos = pyautogui.position()
        smooth_actual_dx = smooth_end_pos.x - smooth_start_pos.x
        smooth_actual_dy = smooth_end_pos.y - smooth_start_pos.y
        smooth_error_x = smooth_actual_dx - dx
        smooth_error_y = smooth_actual_dy - dy
        smooth_total_error = (smooth_error_x**2 + smooth_error_y**2)**0.5
        
        smooth_results.append({
            'expected': (dx, dy),
            'actual': (smooth_actual_dx, smooth_actual_dy),
            'error': (smooth_error_x, smooth_error_y),
            'total_error': smooth_total_error,
            'duration': smooth_duration,
            'success': smooth_success
        })
        
        print(f"  结果: 期望({dx},{dy}) 实际({smooth_actual_dx},{smooth_actual_dy})")
        print(f"  误差: ({smooth_error_x:.1f},{smooth_error_y:.1f}) 总误差: {smooth_total_error:.2f}")
        print(f"  耗时: {smooth_duration:.3f}秒")
        
        # 对比结果
        error_improvement = normal_total_error - smooth_total_error
        if error_improvement > 0:
            print(f"  📈 平滑移动误差减少: {error_improvement:.2f}像素")
        elif error_improvement < 0:
            print(f"  📉 平滑移动误差增加: {abs(error_improvement):.2f}像素")
        else:
            print(f"  ➡️ 误差相同")
        
        time.sleep(1)  # 测试间隔
    
    # 生成对比报告
    print("\n" + "=" * 60)
    print("📊 对比测试结果报告")
    print("=" * 60)
    
    # 计算统计数据
    normal_avg_error = sum(r['total_error'] for r in normal_results) / len(normal_results)
    smooth_avg_error = sum(r['total_error'] for r in smooth_results) / len(smooth_results)
    normal_avg_duration = sum(r['duration'] for r in normal_results) / len(normal_results)
    smooth_avg_duration = sum(r['duration'] for r in smooth_results) / len(smooth_results)
    
    normal_success_rate = sum(1 for r in normal_results if r['success']) / len(normal_results) * 100
    smooth_success_rate = sum(1 for r in smooth_results if r['success']) / len(smooth_results) * 100
    
    normal_accurate_count = sum(1 for r in normal_results if r['total_error'] <= 2)
    smooth_accurate_count = sum(1 for r in smooth_results if r['total_error'] <= 2)
    
    print(f"普通移动:")
    print(f"  平均误差: {normal_avg_error:.2f}像素")
    print(f"  平均耗时: {normal_avg_duration:.3f}秒")
    print(f"  成功率: {normal_success_rate:.1f}%")
    print(f"  精确移动(≤2像素): {normal_accurate_count}/{len(normal_results)}")
    
    print(f"\n平滑移动:")
    print(f"  平均误差: {smooth_avg_error:.2f}像素")
    print(f"  平均耗时: {smooth_avg_duration:.3f}秒")
    print(f"  成功率: {smooth_success_rate:.1f}%")
    print(f"  精确移动(≤2像素): {smooth_accurate_count}/{len(smooth_results)}")
    
    # 改善分析
    error_improvement = normal_avg_error - smooth_avg_error
    time_difference = smooth_avg_duration - normal_avg_duration
    accuracy_improvement = smooth_accurate_count - normal_accurate_count
    
    print(f"\n📈 改善分析:")
    if error_improvement > 0:
        print(f"  ✅ 平滑移动平均误差减少: {error_improvement:.2f}像素 ({error_improvement/normal_avg_error*100:.1f}%)")
    else:
        print(f"  ❌ 平滑移动平均误差增加: {abs(error_improvement):.2f}像素")
    
    if accuracy_improvement > 0:
        print(f"  ✅ 精确移动增加: {accuracy_improvement}次")
    elif accuracy_improvement < 0:
        print(f"  ❌ 精确移动减少: {abs(accuracy_improvement)}次")
    else:
        print(f"  ➡️ 精确移动次数相同")
    
    print(f"  ⏱️ 平滑移动额外耗时: {time_difference:.3f}秒 ({time_difference/normal_avg_duration*100:.1f}%)")
    
    # 详细结果表格
    print(f"\n📋 详细结果对比:")
    print(f"{'移动':<12} {'普通误差':<10} {'平滑误差':<10} {'改善':<8} {'普通耗时':<10} {'平滑耗时':<10}")
    print("-" * 70)
    
    for i, (normal, smooth) in enumerate(zip(normal_results, smooth_results)):
        expected = normal['expected']
        normal_err = normal['total_error']
        smooth_err = smooth['total_error']
        improvement = normal_err - smooth_err
        normal_time = normal['duration']
        smooth_time = smooth['duration']
        
        improvement_str = f"+{improvement:.1f}" if improvement > 0 else f"{improvement:.1f}"
        
        print(f"{str(expected):<12} {normal_err:<10.2f} {smooth_err:<10.2f} {improvement_str:<8} {normal_time:<10.3f} {smooth_time:<10.3f}")
    
    print("\n🎯 测试完成！")

if __name__ == "__main__":
    test_movement_comparison()
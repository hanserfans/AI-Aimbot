#!/usr/bin/env python3
"""
精度测试脚本 - 验证优化后的移动精度
测试不同距离和方向的移动精度
"""

import time
import pyautogui
import statistics
from improved_adaptive_correction import improved_adaptive_mouse

def test_movement_precision():
    """测试移动精度"""
    print("🎯 开始精度测试...")
    
    # 初始化
    if not improved_adaptive_mouse.initialize():
        print("❌ G-Hub鼠标初始化失败")
        return False
    
    # 测试用例 - 不同距离和方向
    test_cases = [
        # 小距离移动 (1-10像素)
        (2, 0), (0, 2), (-2, 0), (0, -2),
        (5, 0), (0, 5), (-5, 0), (0, -5),
        (3, 3), (-3, -3), (7, -7), (-7, 7),
        
        # 中等距离移动 (10-50像素)
        (15, 0), (0, 15), (-15, 0), (0, -15),
        (20, 20), (-20, -20), (30, -30), (-30, 30),
        (25, 0), (0, 25), (-25, 0), (0, -25),
        
        # 大距离移动 (50-100像素)
        (50, 0), (0, 50), (-50, 0), (0, -50),
        (70, 70), (-70, -70), (80, -80), (-80, 80),
        (60, 0), (0, 60), (-60, 0), (0, -60),
        
        # 超大距离移动 (100+像素)
        (100, 0), (0, 100), (-100, 0), (0, -100),
        (120, 120), (-120, -120), (150, -150), (-150, 150)
    ]
    
    results = []
    precise_movements = 0  # 误差 <= 2像素
    accurate_movements = 0  # 误差 <= 5像素
    
    print(f"总共测试 {len(test_cases)} 个移动...")
    
    for i, (dx, dy) in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] 测试移动: ({dx}, {dy})")
        
        # 记录初始位置
        start_pos = pyautogui.position()
        start_time = time.time()
        
        # 执行移动
        success = improved_adaptive_mouse.stable_move(dx, dy)
        
        # 计算耗时
        duration = time.time() - start_time
        
        # 检查实际移动
        end_pos = pyautogui.position()
        actual_dx = end_pos.x - start_pos.x
        actual_dy = end_pos.y - start_pos.y
        
        # 计算误差
        error_x = actual_dx - dx
        error_y = actual_dy - dy
        total_error = (error_x**2 + error_y**2)**0.5
        
        # 记录结果
        result = {
            'expected': (dx, dy),
            'actual': (actual_dx, actual_dy),
            'error': (error_x, error_y),
            'total_error': total_error,
            'duration': duration,
            'success': success
        }
        results.append(result)
        
        # 统计精度
        if total_error <= 2:
            precise_movements += 1
            status = "🎯 精确"
        elif total_error <= 5:
            accurate_movements += 1
            status = "✅ 准确"
        else:
            status = "⚠️ 偏差"
        
        print(f"   实际: ({actual_dx}, {actual_dy})")
        print(f"   误差: ({error_x:.1f}, {error_y:.1f}) = {total_error:.1f}px")
        print(f"   耗时: {duration:.3f}s")
        print(f"   状态: {status}")
        
        # 短暂等待
        time.sleep(0.3)
    
    # 分析结果
    analyze_results(results, precise_movements, accurate_movements)
    
    return True

def analyze_results(results, precise_movements, accurate_movements):
    """分析测试结果"""
    print("\n" + "="*60)
    print("📊 精度测试结果分析")
    print("="*60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    
    # 基本统计
    print(f"总测试次数: {total_tests}")
    print(f"成功次数: {successful_tests}")
    print(f"成功率: {successful_tests/total_tests*100:.1f}%")
    print(f"精确移动 (≤2px): {precise_movements} ({precise_movements/total_tests*100:.1f}%)")
    print(f"准确移动 (≤5px): {accurate_movements} ({accurate_movements/total_tests*100:.1f}%)")
    
    # 误差统计
    errors = [r['total_error'] for r in results if r['success']]
    if errors:
        avg_error = statistics.mean(errors)
        median_error = statistics.median(errors)
        max_error = max(errors)
        min_error = min(errors)
        
        print(f"\n误差统计:")
        print(f"平均误差: {avg_error:.2f}px")
        print(f"中位数误差: {median_error:.2f}px")
        print(f"最大误差: {max_error:.2f}px")
        print(f"最小误差: {min_error:.2f}px")
        
        if len(errors) > 1:
            std_error = statistics.stdev(errors)
            print(f"误差标准差: {std_error:.2f}px")
    
    # 耗时统计
    durations = [r['duration'] for r in results if r['success']]
    if durations:
        avg_duration = statistics.mean(durations)
        print(f"\n耗时统计:")
        print(f"平均耗时: {avg_duration:.3f}s")
    
    # 按距离分类分析
    analyze_by_distance(results)
    
    # 显示系统性能报告
    print("\n" + "="*60)
    print("🎯 系统性能报告")
    print("="*60)
    print(improved_adaptive_mouse.get_performance_report())

def analyze_by_distance(results):
    """按移动距离分类分析"""
    print(f"\n按距离分类分析:")
    
    # 分类
    small_moves = []  # 0-10px
    medium_moves = []  # 10-50px
    large_moves = []  # 50-100px
    xlarge_moves = []  # 100px+
    
    for r in results:
        if not r['success']:
            continue
        
        dx, dy = r['expected']
        distance = (dx**2 + dy**2)**0.5
        
        if distance <= 10:
            small_moves.append(r)
        elif distance <= 50:
            medium_moves.append(r)
        elif distance <= 100:
            large_moves.append(r)
        else:
            xlarge_moves.append(r)
    
    # 分析各类别
    categories = [
        ("小距离 (≤10px)", small_moves),
        ("中距离 (10-50px)", medium_moves),
        ("大距离 (50-100px)", large_moves),
        ("超大距离 (>100px)", xlarge_moves)
    ]
    
    for name, moves in categories:
        if not moves:
            continue
        
        errors = [m['total_error'] for m in moves]
        precise = sum(1 for e in errors if e <= 2)
        accurate = sum(1 for e in errors if e <= 5)
        
        avg_error = statistics.mean(errors)
        
        print(f"  {name}: {len(moves)}次")
        print(f"    平均误差: {avg_error:.2f}px")
        print(f"    精确率: {precise/len(moves)*100:.1f}%")
        print(f"    准确率: {accurate/len(moves)*100:.1f}%")

if __name__ == "__main__":
    print("🚀 启动移动精度测试")
    print("请确保鼠标在屏幕中央区域，避免移动到屏幕边缘")
    
    # 等待用户准备
    input("按回车键开始测试...")
    
    # 执行测试
    test_movement_precision()
    
    print("\n✅ 测试完成！")
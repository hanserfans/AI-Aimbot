"""
平滑移动延迟调整工具
"""

import sys
import os
sys.path.append('.')

from smooth_mouse_movement import SmoothMouseMovement, create_smooth_movement_system
import time

def mock_move_function(x, y):
    """模拟移动函数用于测试"""
    print(f"[TEST] 移动: ({x:.1f}, {y:.1f})")
    return True

def test_delay_settings(base_delay, variance, description):
    """测试特定延迟设置"""
    print(f"\n=== {description} ===")
    print(f"基础延迟: {base_delay*1000:.1f}ms, 变化范围: ±{variance*1000:.1f}ms")
    
    # 创建临时的移动系统
    system = SmoothMouseMovement(mock_move_function)
    system.step_delay_base = base_delay
    system.step_delay_variance = variance
    
    # 测试移动
    start_time = time.time()
    system.smooth_move_to_target(50, 40)
    end_time = time.time()
    
    print(f"总耗时: {(end_time - start_time)*1000:.1f}ms")
    return end_time - start_time

def main():
    print("🎯 平滑移动延迟调整工具")
    print("=" * 50)
    
    # 预设配置选项
    delay_presets = [
        (0.004, 0.002, "极速模式 (竞技游戏推荐)"),
        (0.006, 0.003, "快速模式 (平衡性能)"),
        (0.008, 0.004, "当前设置 (标准模式)"),
        (0.012, 0.006, "稳定模式 (更人性化)"),
        (0.016, 0.008, "缓慢模式 (最大隐蔽性)")
    ]
    
    print("可选延迟配置：")
    for i, (base, variance, desc) in enumerate(delay_presets, 1):
        print(f"{i}. {desc}")
    
    print("\n测试各种延迟设置的效果：")
    
    results = []
    for base, variance, desc in delay_presets:
        duration = test_delay_settings(base, variance, desc)
        results.append((base, variance, desc, duration))
    
    print("\n" + "=" * 50)
    print("📊 延迟设置对比总结：")
    print("=" * 50)
    
    for base, variance, desc, duration in results:
        print(f"{desc:20} | 基础: {base*1000:4.1f}ms | 变化: ±{variance*1000:4.1f}ms | 总耗时: {duration*1000:5.1f}ms")
    
    print("\n" + "=" * 50)
    print("💡 选择建议：")
    print("• 竞技游戏 (如CS2/Valorant): 选择极速或快速模式")
    print("• 休闲游戏: 选择标准或稳定模式") 
    print("• 最大隐蔽性: 选择缓慢模式")
    print("=" * 50)
    
    while True:
        try:
            choice = input("\n请选择要应用的配置 (1-5, 或按Enter保持当前设置): ").strip()
            
            if not choice:
                print("保持当前设置")
                break
                
            choice_num = int(choice)
            if 1 <= choice_num <= 5:
                base, variance, desc = delay_presets[choice_num - 1]
                apply_delay_settings(base, variance, desc)
                break
            else:
                print("请输入1-5之间的数字")
                
        except ValueError:
            print("请输入有效的数字")
        except KeyboardInterrupt:
            print("\n操作取消")
            break

def apply_delay_settings(base_delay, variance, description):
    """应用延迟设置到主文件"""
    print(f"\n🔧 正在应用设置: {description}")
    
    # 读取原文件
    with open('smooth_mouse_movement.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换延迟设置
    import re
    
    # 替换基础延迟
    content = re.sub(
        r'self\.step_delay_base = [0-9.]+',
        f'self.step_delay_base = {base_delay}',
        content
    )
    
    # 替换延迟变化范围
    content = re.sub(
        r'self\.step_delay_variance = [0-9.]+',
        f'self.step_delay_variance = {variance}',
        content
    )
    
    # 写回文件
    with open('smooth_mouse_movement.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 延迟设置已更新:")
    print(f"   基础延迟: {base_delay*1000:.1f}ms")
    print(f"   变化范围: ±{variance*1000:.1f}ms")
    print(f"   预计总耗时: ~{(base_delay*4 + variance*2)*1000:.1f}ms")
    
    # 测试新设置
    print(f"\n🧪 测试新设置效果:")
    test_delay_settings(base_delay, variance, "新设置测试")

if __name__ == "__main__":
    main()
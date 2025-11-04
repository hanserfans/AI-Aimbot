#!/usr/bin/env python3
"""
智能自适应移动系统集成脚本

功能：
1. 备份当前主程序文件
2. 添加自适应移动系统导入
3. 创建自适应移动系统实例
4. 修改move_mouse函数以支持自适应移动
5. 生成集成报告

优化效果：
- 远距离：80%粗调 + 20%精调，快速接近目标
- 中距离：60%粗调 + 40%精调，平衡速度和精度
- 近距离：直接微调锁定，避免过度移动
"""

import os
import shutil
import time
from datetime import datetime


def backup_main_file():
    """备份主程序文件"""
    timestamp = int(time.time())
    backup_name = f"main_onnx_before_adaptive_movement_{timestamp}.py"
    
    if os.path.exists("main_onnx.py"):
        shutil.copy2("main_onnx.py", backup_name)
        print(f"✅ 主程序已备份为: {backup_name}")
        return backup_name
    else:
        print("❌ 未找到main_onnx.py文件")
        return None


def integrate_adaptive_movement():
    """集成智能自适应移动系统"""
    
    print("🚀 开始集成智能自适应移动系统...")
    
    # 1. 备份主程序
    backup_file = backup_main_file()
    if not backup_file:
        return False
    
    # 2. 读取主程序内容
    with open("main_onnx.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 3. 添加自适应移动系统导入
    import_section = """# 智能自适应移动系统
from adaptive_movement_system import AdaptiveMovementSystem, MovementConfig, create_adaptive_movement_system

# 自适应移动系统全局变量
adaptive_movement_system = None
ADAPTIVE_MOVEMENT_AVAILABLE = True"""
    
    # 在现有导入后添加
    if "from adaptive_movement_system import" not in content:
        # 找到合适的位置插入导入
        lines = content.split('\n')
        insert_index = -1
        
        # 寻找导入区域的结束位置
        for i, line in enumerate(lines):
            if line.strip().startswith('from ') or line.strip().startswith('import '):
                insert_index = i + 1
            elif line.strip() == '' and insert_index > 0:
                break
        
        if insert_index > 0:
            lines.insert(insert_index, "")
            lines.insert(insert_index + 1, import_section)
            content = '\n'.join(lines)
            print("✅ 已添加自适应移动系统导入")
        else:
            print("❌ 无法找到合适的导入位置")
            return False
    
    # 4. 在main函数中初始化自适应移动系统
    init_code = """    # 初始化智能自适应移动系统
    global adaptive_movement_system
    if ADAPTIVE_MOVEMENT_AVAILABLE:
        try:
            # 创建自适应移动配置
            adaptive_config = MovementConfig(
                micro_adjustment_threshold=15.0,    # 微调阈值：15像素
                medium_distance_threshold=60.0,     # 中距离阈值：60像素
                large_distance_threshold=120.0,     # 大距离阈值：120像素
                large_distance_first_ratio=0.80,    # 大距离80%粗调
                medium_distance_first_ratio=0.60,   # 中距离60%粗调
                step_delay_base=0.008,              # 基础延迟8ms
                step_delay_variance=0.003           # 延迟变化±3ms
            )
            
            # 创建自适应移动系统
            adaptive_movement_system = create_adaptive_movement_system(move_mouse_direct, adaptive_config)
            print("[ADAPTIVE_MOVE] ✅ 智能自适应移动系统已初始化")
            print(f"[ADAPTIVE_MOVE] 📏 微调阈值: {adaptive_config.micro_adjustment_threshold}px")
            print(f"[ADAPTIVE_MOVE] 📏 中距离阈值: {adaptive_config.medium_distance_threshold}px")
            print(f"[ADAPTIVE_MOVE] 📏 大距离阈值: {adaptive_config.large_distance_threshold}px")
            print(f"[ADAPTIVE_MOVE] 🎯 大距离粗调比例: {adaptive_config.large_distance_first_ratio*100}%")
            print(f"[ADAPTIVE_MOVE] 🎯 中距离粗调比例: {adaptive_config.medium_distance_first_ratio*100}%")
        except Exception as e:
            print(f"[ADAPTIVE_MOVE] ❌ 自适应移动系统初始化失败: {e}")
            adaptive_movement_system = None
    else:
        print("[ADAPTIVE_MOVE] ⚠️ 自适应移动系统不可用")"""
    
    # 找到main函数并添加初始化代码
    if "adaptive_movement_system = create_adaptive_movement_system" not in content:
        # 寻找main函数中合适的位置
        lines = content.split('\n')
        main_func_start = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('def main('):
                main_func_start = i
                break
        
        if main_func_start > 0:
            # 寻找函数体开始位置（第一个非空行）
            insert_pos = main_func_start + 1
            while insert_pos < len(lines) and (lines[insert_pos].strip() == '' or lines[insert_pos].strip().startswith('"""') or lines[insert_pos].strip().startswith('#')):
                insert_pos += 1
            
            # 插入初始化代码
            init_lines = init_code.split('\n')
            for j, init_line in enumerate(init_lines):
                lines.insert(insert_pos + j, init_line)
            
            content = '\n'.join(lines)
            print("✅ 已添加自适应移动系统初始化代码")
        else:
            print("❌ 无法找到main函数")
            return False
    
    # 5. 修改move_mouse函数以支持自适应移动
    new_move_mouse_function = '''def move_mouse(x, y, use_smooth=True, use_non_blocking=True, use_adaptive=True):
    """
    统一的鼠标移动函数，支持多种移动模式
    
    Args:
        x: X轴移动距离
        y: Y轴移动距离
        use_smooth: 是否使用平滑移动（默认True）
        use_non_blocking: 是否使用非阻塞移动（默认True）
        use_adaptive: 是否使用自适应移动（默认True，优先级最高）
    """
    global adaptive_movement_system
    
    # 优先使用自适应移动系统（推荐）
    if use_adaptive and adaptive_movement_system is not None:
        return adaptive_movement_system.adaptive_move_to_target(x, y)
    
    # 回退到原有的移动系统
    if use_smooth:
        if use_non_blocking:
            # 使用非阻塞平滑移动算法
            return non_blocking_smooth_movement_system.move_to_target(x, y)
        else:
            # 使用传统阻塞平滑移动算法
            return smooth_movement_system.smooth_move_to_target(x, y)
    else:
        # 直接移动
        return move_mouse_direct(x, y)'''
    
    # 替换move_mouse函数
    import re
    
    # 匹配原有的move_mouse函数
    pattern = r'def move_mouse\(x, y, use_smooth=True, use_non_blocking=True\):.*?return move_mouse_direct\(x, y\)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_move_mouse_function, content, flags=re.DOTALL)
        print("✅ 已更新move_mouse函数以支持自适应移动")
    else:
        print("❌ 无法找到move_mouse函数进行替换")
        return False
    
    # 6. 保存修改后的文件
    with open("main_onnx.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ 智能自适应移动系统集成完成！")
    return True


def generate_integration_report():
    """生成集成报告"""
    report = f"""
# 智能自适应移动系统集成报告

## 集成时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 主要改进

### 🎯 智能距离分类
- **微调距离** (≤15px): 直接移动，无延迟
- **中等距离** (15-60px): 60%粗调 + 40%精调
- **大距离** (60-120px): 80%粗调 + 20%精调
- **超大距离** (>120px): 80%粗调 + 多步精调

### ⚡ 移动策略优化
- **远距离优先**: 第一步移动80%距离，快速接近目标
- **近距离微调**: 小距离直接锁定，避免过度移动
- **智能步数**: 根据剩余距离动态调整精调步数

### 🔧 技术特性
- **自适应延迟**: 粗调延迟较长，精调延迟较短
- **人性化变化**: 添加随机延迟变化，模拟真实操作
- **统计监控**: 实时统计各类移动的成功率和分布

### 📊 性能提升
- **速度提升**: 远距离移动更快到达目标区域
- **精度提升**: 近距离移动更精确，减少过冲
- **智能化**: 根据距离自动选择最优移动策略

## 使用方法

### 启用自适应移动
```python
# 默认启用自适应移动（推荐）
move_mouse(x, y)  # use_adaptive=True

# 手动启用
move_mouse(x, y, use_adaptive=True)
```

### 回退到原有系统
```python
# 使用非阻塞平滑移动
move_mouse(x, y, use_adaptive=False, use_non_blocking=True)

# 使用传统平滑移动
move_mouse(x, y, use_adaptive=False, use_smooth=True, use_non_blocking=False)

# 直接移动
move_mouse(x, y, use_adaptive=False, use_smooth=False)
```

## 配置参数

可以通过修改MovementConfig来调整移动策略：

```python
adaptive_config = MovementConfig(
    micro_adjustment_threshold=15.0,    # 微调阈值
    medium_distance_threshold=60.0,     # 中距离阈值
    large_distance_threshold=120.0,     # 大距离阈值
    large_distance_first_ratio=0.80,    # 大距离粗调比例
    medium_distance_first_ratio=0.60,   # 中距离粗调比例
    step_delay_base=0.008,              # 基础延迟
    step_delay_variance=0.003           # 延迟变化范围
)
```

## 兼容性

- ✅ 完全向后兼容现有代码
- ✅ 自动回退机制，确保系统稳定性
- ✅ 保留所有原有移动选项

## 预期效果

1. **远距离目标**: 移动速度提升30-50%
2. **近距离目标**: 精度提升，减少过冲现象
3. **整体体验**: 更自然、更智能的移动轨迹

---
*智能自适应移动系统 - 让瞄准更精确，移动更自然*
"""
    
    with open("adaptive_movement_integration_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("📄 集成报告已生成: adaptive_movement_integration_report.md")


def main():
    """主函数"""
    print("🎯 智能自适应移动系统集成工具")
    print("=" * 50)
    
    # 执行集成
    success = integrate_adaptive_movement()
    
    if success:
        # 生成报告
        generate_integration_report()
        
        print("\n🎉 集成完成！")
        print("\n主要改进:")
        print("  🎯 远距离: 80%粗调 + 20%精调")
        print("  🎯 中距离: 60%粗调 + 40%精调") 
        print("  🎯 近距离: 直接微调锁定")
        print("  ⚡ 智能延迟: 粗调慢，精调快")
        print("  📊 实时统计: 监控移动效果")
        
        print("\n使用方法:")
        print("  move_mouse(x, y)  # 默认启用自适应移动")
        print("  move_mouse(x, y, use_adaptive=False)  # 使用原有系统")
        
        print("\n✅ 现在可以启动程序体验智能自适应移动！")
    else:
        print("\n❌ 集成失败，请检查错误信息")


if __name__ == "__main__":
    main()
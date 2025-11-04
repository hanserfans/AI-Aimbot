#!/usr/bin/env python3
"""
集成增强目标选择系统到主程序
- 替换现有的目标选择逻辑
- 增加距离权重计算
- 改进移动锁定机制
"""

import os
import shutil
import time

def backup_main_file():
    """备份主程序文件"""
    main_file = "f:\\git\\AI-Aimbot\\main_onnx.py"
    backup_file = f"f:\\git\\AI-Aimbot\\main_onnx_before_enhanced_target_{int(time.time())}.py"
    
    if os.path.exists(main_file):
        shutil.copy2(main_file, backup_file)
        print(f"✅ 已备份主程序文件: {backup_file}")
        return backup_file
    else:
        print("❌ 主程序文件不存在")
        return None

def integrate_enhanced_target_system():
    """集成增强目标选择系统"""
    main_file = "f:\\git\\AI-Aimbot\\main_onnx.py"
    
    # 读取原文件
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 添加增强目标选择系统的导入
    import_section = '''# 增强目标选择系统
try:
    from enhanced_target_selection_system import get_enhanced_target_system, create_enhanced_target_system
    ENHANCED_TARGET_SELECTION_AVAILABLE = True
    print("[INFO] ✅ 增强目标选择系统已加载到主程序")
except ImportError as e:
    print(f"[WARNING] 增强目标选择系统加载失败: {e}")
    ENHANCED_TARGET_SELECTION_AVAILABLE = False

'''
    
    # 在其他系统导入后添加
    if "PERFORMANCE_MONITOR_AVAILABLE = False" in content:
        content = content.replace(
            "PERFORMANCE_MONITOR_AVAILABLE = False",
            "PERFORMANCE_MONITOR_AVAILABLE = False\n\n" + import_section
        )
    
    # 2. 替换 calculate_distance_to_crosshair 函数
    old_distance_function = '''def calculate_distance_to_crosshair(target_x, target_y, box_height, crosshair_x, crosshair_y):
    """计算目标头部到准星的距离"""
    # 计算头部位置（头部在目标中心上方）
    head_offset = box_height * 0.35  # 头部偏移量
    head_x = target_x
    head_y = target_y - head_offset
    
    # 使用平滑后的头部位置
    smoothed_head_x, smoothed_head_y = calculate_smoothed_head_position(head_x, head_y)
    
    # 计算距离
    distance = ((smoothed_head_x - crosshair_x)**2 + (smoothed_head_y - crosshair_y)**2)**0.5
    return distance'''
    
    new_distance_function = '''def calculate_distance_to_crosshair(target_x, target_y, box_height, crosshair_x, crosshair_y):
    """计算目标头部到准星的距离（增强版本）"""
    # 如果增强目标选择系统可用，使用增强版本
    if ENHANCED_TARGET_SELECTION_AVAILABLE:
        enhanced_system = get_enhanced_target_system()
        # 使用加权距离评分（评分越低距离越近）
        weighted_score = enhanced_system.calculate_weighted_distance_score(
            target_x, target_y, box_height, crosshair_x, crosshair_y
        )
        # 转换为距离值（保持兼容性）
        return weighted_score * 10  # 缩放因子，使评分转换为合理的距离值
    else:
        # 原始距离计算逻辑
        head_offset = box_height * 0.35
        head_x = target_x
        head_y = target_y - head_offset
        
        # 使用平滑后的头部位置
        smoothed_head_x, smoothed_head_y = calculate_smoothed_head_position(head_x, head_y)
        
        # 计算距离
        distance = ((smoothed_head_x - crosshair_x)**2 + (smoothed_head_y - crosshair_y)**2)**0.5
        return distance'''
    
    content = content.replace(old_distance_function, new_distance_function)
    
    # 3. 替换 find_best_target_with_lock 函数
    # 找到函数开始位置
    func_start = content.find("def find_best_target_with_lock(targets, current_time):")
    if func_start != -1:
        # 找到函数结束位置（下一个def或类定义）
        func_end = content.find("\n    def ", func_start + 1)
        if func_end == -1:
            func_end = content.find("\ndef ", func_start + 1)
        if func_end == -1:
            func_end = content.find("\nclass ", func_start + 1)
        
        if func_end != -1:
            # 替换整个函数
            new_function = '''def find_best_target_with_lock(targets, current_time):
        """增强的智能目标选择：考虑距离权重和移动锁定"""
        nonlocal locked_target, lock_start_time
        
        if not target_lock_enabled or len(targets) == 0:
            return targets.iloc[0] if len(targets) > 0 else None
        
        # 如果增强目标选择系统可用，使用增强版本
        if ENHANCED_TARGET_SELECTION_AVAILABLE:
            enhanced_system = get_enhanced_target_system()
            
            # 获取当前鼠标位置（如果可用）
            try:
                import win32gui
                mouse_pos = win32gui.GetCursorPos()
            except:
                mouse_pos = (centerOfScreen[0], centerOfScreen[1])
            
            # 使用增强目标选择
            selected_target = enhanced_system.select_best_target(
                targets, 
                centerOfScreen[0], 
                centerOfScreen[1], 
                current_time,
                mouse_pos
            )
            
            if selected_target:
                # 转换为原始格式
                best_target_data = {
                    'current_mid_x': selected_target['x'],
                    'current_mid_y': selected_target['y'],
                    'height': selected_target['height'],
                    'confidence': selected_target['confidence']
                }
                
                # 计算头部位置
                head_x, head_y = calculate_head_position(best_target_data)
                
                # 更新锁定目标
                locked_target = {
                    'head_x': head_x,
                    'head_y': head_y,
                    'x': selected_target['x'],
                    'y': selected_target['y'],
                    'confidence': selected_target['confidence']
                }
                lock_start_time = current_time
                
                # 创建返回的目标数据
                result_target = targets.iloc[0].copy()  # 使用第一个目标作为模板
                result_target['current_mid_x'] = selected_target['x']
                result_target['current_mid_y'] = selected_target['y']
                result_target['height'] = selected_target['height']
                result_target['confidence'] = selected_target['confidence']
                result_target['head_x'] = head_x
                result_target['head_y'] = head_y
                
                print(f"[ENHANCED_TARGET] 🎯 选择目标: ({selected_target['x']:.1f}, {selected_target['y']:.1f}), 评分: {selected_target['weighted_score']:.2f}")
                return result_target
        
        # 原始目标选择逻辑（作为备选）
        # 检查当前锁定是否过期
        if locked_target and (current_time - lock_start_time) > LOCK_DURATION:
            print(f"[TARGET_LOCK] 🔓 目标锁定已过期 ({LOCK_DURATION}秒)")
            locked_target = None
            lock_start_time = 0
        
        # 如果有锁定目标，尝试在当前检测结果中找到它
        if locked_target:
            locked_head_x, locked_head_y = locked_target['head_x'], locked_target['head_y']
            
            # 计算当前所有目标的头部位置
            targets['head_x'] = targets.apply(lambda row: calculate_head_position(row)[0], axis=1)
            targets['head_y'] = targets.apply(lambda row: calculate_head_position(row)[1], axis=1)
            
            # 在当前目标中寻找与锁定目标头部最接近的目标
            targets['distance_to_locked_head'] = targets.apply(
                lambda row: ((row['head_x'] - locked_head_x)**2 + (row['head_y'] - locked_head_y)**2)**0.5,
                axis=1
            )
            
            # 找到距离锁定目标头部最近的目标
            closest_to_locked = targets.loc[targets['distance_to_locked_head'].idxmin()]
            
            # 如果距离在阈值内，继续锁定这个目标
            if closest_to_locked['distance_to_locked_head'] <= LOCK_DISTANCE_THRESHOLD:
                # 更新锁定目标的头部位置
                new_head_x = closest_to_locked['head_x']
                new_head_y = closest_to_locked['head_y']
                
                # 应用头部位置平滑
                if head_smoother is not None:
                    smoothed_head_x, smoothed_head_y = head_smoother.update_position(new_head_x, new_head_y)
                    locked_target['head_x'] = smoothed_head_x
                    locked_target['head_y'] = smoothed_head_y
                else:
                    locked_target['head_x'] = new_head_x
                    locked_target['head_y'] = new_head_y
                
                locked_target['x'] = closest_to_locked['current_mid_x']
                locked_target['y'] = closest_to_locked['current_mid_y']
                locked_target['confidence'] = closest_to_locked['confidence']
                
                print(f"[TARGET_LOCK] 🎯 继续锁定目标头部: ({locked_target['head_x']:.1f}, {locked_target['head_y']:.1f})")
                return closest_to_locked
            else:
                print(f"[TARGET_LOCK] 🔓 锁定目标丢失，距离: {closest_to_locked['distance_to_locked_head']:.1f} > {LOCK_DISTANCE_THRESHOLD}")
                locked_target = None
                lock_start_time = 0
        
        # 选择新目标
        targets = targets.sort_values('distance_to_crosshair')
        best_target = targets.iloc[0]
        
        # 计算头部位置
        head_x, head_y = calculate_head_position(best_target)
        
        # 锁定新目标
        locked_target = {
            'head_x': head_x,
            'head_y': head_y,
            'x': best_target['current_mid_x'],
            'y': best_target['current_mid_y'],
            'confidence': best_target['confidence']
        }
        lock_start_time = current_time
        
        print(f"[TARGET_LOCK] 🔒 锁定新目标头部 - 位置: ({head_x:.1f}, {head_y:.1f})")
        return best_target

'''
            
            content = content[:func_start] + new_function + content[func_end:]
    
    # 4. 在main函数开始处初始化增强目标选择系统
    main_func_start = content.find("def main():")
    if main_func_start != -1:
        # 找到函数体开始位置
        func_body_start = content.find("\"\"\"", main_func_start)
        if func_body_start != -1:
            func_body_start = content.find("\"\"\"", func_body_start + 3) + 3
        else:
            func_body_start = content.find(":", main_func_start) + 1
        
        # 在函数体开始处添加初始化代码
        init_code = '''
    # 初始化增强目标选择系统
    if ENHANCED_TARGET_SELECTION_AVAILABLE:
        enhanced_target_system = get_enhanced_target_system()
        print("[INFO] ✅ 增强目标选择系统已初始化")
    else:
        enhanced_target_system = None
        print("[INFO] ⚠️ 使用原始目标选择逻辑")
'''
        
        content = content[:func_body_start] + init_code + content[func_body_start:]
    
    # 写入修改后的文件
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 增强目标选择系统集成完成")

def create_integration_report():
    """创建集成报告"""
    report_content = """# 增强目标选择系统集成报告

## 集成时间
{timestamp}

## 集成内容

### 1. 新增功能
- ✅ 距离权重计算：距离越近的目标优先级越高
- ✅ 移动锁定机制：移动到目标过程中不会重新选择目标
- ✅ 智能目标切换：结合距离权重和移动状态进行选择
- ✅ 目标优先级显示：实时显示目标评分和优先级信息

### 2. 技术改进
- 🔧 使用指数函数增强距离影响
- 🔧 结合置信度进行综合评分
- 🔧 移动完成阈值检测
- 🔧 目标切换冷却时间控制

### 3. 集成修改
- 📝 添加 `enhanced_target_selection_system` 模块导入
- 📝 替换 `calculate_distance_to_crosshair` 函数
- 📝 增强 `find_best_target_with_lock` 函数
- 📝 在主函数中初始化增强系统

### 4. 配置参数
- 距离权重因子: 2.0
- 移动锁定时长: 0.3秒
- 移动完成阈值: 5.0像素
- 目标切换冷却: 0.1秒

### 5. 兼容性
- ✅ 保持与原始系统的完全兼容
- ✅ 如果增强系统不可用，自动回退到原始逻辑
- ✅ 保持所有现有接口不变

### 6. 预期效果
- 🎯 更准确的目标选择
- 🎯 减少目标跳跃
- 🎯 提高移动过程中的稳定性
- 🎯 更好的用户体验

## 使用说明
1. 系统会自动检测并使用增强目标选择
2. 如果出现问题，会自动回退到原始逻辑
3. 可以通过日志查看目标选择的详细信息

## 回滚方案
如需回滚，请使用备份文件：
- 备份文件位置：`main_onnx_before_enhanced_target_*.py`
- 恢复命令：将备份文件重命名为 `main_onnx.py`
""".format(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
    
    with open("f:\\git\\AI-Aimbot\\enhanced_target_integration_report.md", 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print("✅ 集成报告已生成: enhanced_target_integration_report.md")

def main():
    """主函数"""
    print("=== 增强目标选择系统集成工具 ===")
    
    # 1. 备份原文件
    backup_file = backup_main_file()
    if not backup_file:
        return
    
    # 2. 集成增强系统
    try:
        integrate_enhanced_target_system()
        print("✅ 系统集成成功")
    except Exception as e:
        print(f"❌ 系统集成失败: {e}")
        return
    
    # 3. 生成集成报告
    create_integration_report()
    
    print("\n=== 集成完成 ===")
    print("📋 主要改进:")
    print("  🎯 距离权重：距离越近优先级越高")
    print("  🔒 移动锁定：移动过程中不重新选择目标")
    print("  📊 智能评分：结合距离和置信度")
    print("  🔄 自动回退：兼容原始系统")
    print(f"\n📁 备份文件: {backup_file}")
    print("📄 集成报告: enhanced_target_integration_report.md")
    print("\n🚀 现在可以启动主程序测试增强功能！")

if __name__ == "__main__":
    main()
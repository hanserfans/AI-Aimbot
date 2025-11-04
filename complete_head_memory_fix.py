#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彻底修复头部位置历史记忆问题
确保所有头部位置计算都是实时的，无历史记忆
"""

import os
import re
from datetime import datetime

def complete_head_memory_fix():
    """彻底修复头部位置历史记忆问题"""
    print("🔧 彻底修复头部位置历史记忆问题")
    print("=" * 60)
    
    main_file = "main_onnx.py"
    if not os.path.exists(main_file):
        print("❌ 找不到主程序文件")
        return False
    
    # 备份文件
    timestamp = str(int(datetime.now().timestamp()))
    backup_file = f"main_onnx_before_complete_fix_{timestamp}.py"
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 已备份原文件: {backup_file}")
    
    # 修复项目列表
    fixes = []
    
    # 1. 替换所有 calculate_smoothed_head_position 调用为 calculate_head_position
    old_pattern = r'calculate_smoothed_head_position\('
    new_pattern = 'calculate_head_position('
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_pattern, content)
        fixes.append("替换 calculate_smoothed_head_position 为 calculate_head_position")
    
    # 2. 删除 calculate_smoothed_head_position 函数定义
    smoothed_func_pattern = r'def calculate_smoothed_head_position\(target_x, target_y, box_height\):[^}]+?return head_x, head_y'
    if re.search(smoothed_func_pattern, content, re.DOTALL):
        content = re.sub(smoothed_func_pattern, '', content, flags=re.DOTALL)
        fixes.append("删除 calculate_smoothed_head_position 函数定义")
    
    # 3. 确保 calculate_head_position 函数存在且正确
    head_pos_pattern = r'def calculate_head_position\(target_row\):'
    if not re.search(head_pos_pattern, content):
        print("❌ 找不到 calculate_head_position 函数")
        return False
    
    # 4. 添加实时头部位置说明
    if "# 实时头部位置计算，无历史记忆" not in content:
        # 在 calculate_head_position 函数前添加说明
        content = re.sub(
            r'(def calculate_head_position\(target_row\):)',
            r'# 实时头部位置计算，无历史记忆\n    \1',
            content
        )
        fixes.append("添加实时头部位置说明")
    
    # 5. 确保所有头部位置相关的变量名都是清晰的
    # 替换可能混淆的变量名
    confusing_patterns = [
        (r'smoothed_head_x', 'head_x'),
        (r'smoothed_head_y', 'head_y'),
    ]
    
    for old_var, new_var in confusing_patterns:
        if re.search(old_var, content):
            content = re.sub(old_var, new_var, content)
            fixes.append(f"替换变量名 {old_var} -> {new_var}")
    
    # 6. 检查并修复任何剩余的平滑相关代码
    remaining_smooth_patterns = [
        r'head_smoother\.update_position',
        r'HeadPositionSmoother',
        r'平滑头部位置',
        r'smoothed.*head',
    ]
    
    for pattern in remaining_smooth_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            print(f"⚠️ 发现可能的平滑相关代码: {pattern}")
    
    # 写入修复后的文件
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n🔧 应用的修复:")
    for fix in fixes:
        print(f"   ✅ {fix}")
    
    if not fixes:
        print("   ℹ️ 没有发现需要修复的问题")
    
    return True

def verify_complete_fix():
    """验证彻底修复效果"""
    print("\n🔍 验证彻底修复效果")
    print("=" * 40)
    
    main_file = "main_onnx.py"
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查项目
    checks = [
        ("HEAD_POSITION_SMOOTHER_AVAILABLE = False", "头部平滑系统已禁用"),
        ("head_smoother = None", "头部平滑器已设为None"),
        ("calculate_smoothed_head_position" not in content, "已移除平滑头部位置函数"),
        ("head_smoother.update_position" not in content, "已移除平滑调用"),
        ("实时头部位置计算" in content, "添加了实时计算说明"),
        ("smoothed_head_x" not in content, "已移除混淆变量名"),
        ("smoothed_head_y" not in content, "已移除混淆变量名"),
    ]
    
    all_passed = True
    for check, description in checks:
        if isinstance(check, bool):
            passed = check
        else:
            passed = check in content
        
        status = "✅" if passed else "❌"
        print(f"   {status} {description}")
        
        if not passed:
            all_passed = False
    
    return all_passed

def show_current_head_flow():
    """显示当前头部位置处理流程"""
    print("\n🔄 当前头部位置处理流程:")
    print("   1. 目标检测 → 获取边界框")
    print("   2. 计算中心点 → mid_x, mid_y")
    print("   3. 实时计算头部位置 → calculate_head_position()")
    print("   4. 头部偏移 → head_y = mid_y - box_height*0.38")
    print("   5. 直接返回实时位置 → 无任何历史记忆")
    print("   6. 立即更新渲染 → 实时响应")

if __name__ == "__main__":
    print("🎯 彻底修复头部位置历史记忆问题")
    print("🎯" * 30)
    
    success = complete_head_memory_fix()
    
    if success:
        verification_passed = verify_complete_fix()
        
        if verification_passed:
            show_current_head_flow()
            print("\n" + "🎉" * 30)
            print("头部位置历史记忆问题已彻底解决！")
            print("现在头部位置将完全实时跟随检测结果！")
            print("🎉" * 30)
        else:
            print("\n❌ 验证失败，可能还有遗留问题")
    else:
        print("\n❌ 修复失败")
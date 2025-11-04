#!/usr/bin/env python3
"""
完全禁用头部位置历史记忆系统
解决头部位置渲染在旧位置的问题
"""

import os
import shutil
from datetime import datetime

def disable_head_memory_system():
    """完全禁用头部位置历史记忆系统"""
    
    print("🔧 开始禁用头部位置历史记忆系统...")
    
    main_file = "main_onnx.py"
    
    # 1. 备份原文件
    timestamp = int(datetime.now().timestamp())
    backup_file = f"main_onnx_before_disable_memory_{timestamp}.py"
    shutil.copy2(main_file, backup_file)
    print(f"✅ 已备份原文件: {backup_file}")
    
    # 2. 读取主文件内容
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 3. 禁用头部位置平滑系统
    print("🚫 禁用头部位置平滑系统...")
    
    # 将 HEAD_POSITION_SMOOTHER_AVAILABLE 设置为 False
    old_smoother_import = """from head_position_smoother import get_head_position_smoother, create_head_position_smoother
HEAD_POSITION_SMOOTHER_AVAILABLE = True"""
    
    new_smoother_import = """# from head_position_smoother import get_head_position_smoother, create_head_position_smoother
# HEAD_POSITION_SMOOTHER_AVAILABLE = True  # 已禁用，避免历史记忆
HEAD_POSITION_SMOOTHER_AVAILABLE = False  # 强制禁用头部位置平滑"""
    
    content = content.replace(old_smoother_import, new_smoother_import)
    
    # 4. 注释掉所有头部平滑相关的代码
    print("🚫 注释头部平滑相关代码...")
    
    # 注释头部平滑系统初始化
    old_init = """    # 初始化头部位置平滑系统
    head_smoother = None
    if HEAD_POSITION_SMOOTHER_AVAILABLE:
        print("[INFO] 初始化头部位置平滑系统...")
        head_smoother = create_head_position_smoother(
            smoothing_factor=0.8,       # 高平滑系数，减少抖动
            history_size=10,            # 保持10个历史位置
            velocity_smoothing=0.6,     # 速度平滑
            min_movement_threshold=0.5  # 最小移动阈值
        )
        print("[INFO] ✅ 头部位置平滑系统已初始化")
        print("   • 高平滑系数：大幅减少位置抖动")
        print("   • 速度感知：根据移动速度调整平滑强度")
        print("   • 微小移动过滤：忽略小于0.5像素的移动")
        print("   • 位置预测：基于速度预测未来位置")
    else:
        print("[WARNING] ⚠️ 头部位置平滑系统不可用，将使用原始头部位置")"""
    
    new_init = """    # 头部位置平滑系统已禁用（避免历史记忆问题）
    head_smoother = None
    print("[INFO] 🚫 头部位置平滑系统已禁用 - 使用纯净实时头部位置")
    print("   • 无历史记忆：避免头部位置渲染在旧位置")
    print("   • 实时响应：直接使用当前帧检测结果")
    print("   • 零延迟：无平滑处理延迟")"""
    
    content = content.replace(old_init, new_init)
    
    # 5. 替换所有头部平滑调用为直接使用原始位置
    print("🔄 替换头部平滑调用...")
    
    # 替换模式1：calculate_smoothed_head_position 函数中的调用
    old_smooth_call1 = """        # 应用头部位置平滑
        if head_smoother is not None:
            smoothed_head_x, smoothed_head_y = head_smoother.update_position(head_x, head_y)
            return smoothed_head_x, smoothed_head_y
        else:
            return head_x, head_y"""
    
    new_smooth_call1 = """        # 直接返回原始头部位置（无平滑处理）
        return head_x, head_y"""
    
    content = content.replace(old_smooth_call1, new_smooth_call1)
    
    # 替换模式2：主循环中的调用
    old_smooth_call2 = """                # 应用头部位置平滑
                if head_smoother is not None:
                    smoothed_head_x, smoothed_head_y = head_smoother.update_position(new_head_x, new_head_y)
                    locked_target['head_x'] = smoothed_head_x
                    locked_target['head_y'] = smoothed_head_y
                else:
                    locked_target['head_x'] = new_head_x
                    locked_target['head_y'] = new_head_y"""
    
    new_smooth_call2 = """                # 直接使用原始头部位置（无平滑处理）
                locked_target['head_x'] = new_head_x
                locked_target['head_y'] = new_head_y"""
    
    content = content.replace(old_smooth_call2, new_smooth_call2)
    
    # 6. 移除其他可能的头部平滑调用
    import re
    
    # 查找并替换所有 head_smoother.update_position 调用
    smoother_pattern = r'if head_smoother is not None:\s*\n\s*smoothed_head_x, smoothed_head_y = head_smoother\.update_position\([^)]+\)\s*\n\s*([^=]+= smoothed_head_x[^}]+)\s*else:\s*\n\s*([^}]+)'
    
    def replace_smoother_calls(match):
        # 提取else分支的内容（直接使用原始位置）
        else_content = match.group(2).strip()
        return else_content
    
    content = re.sub(smoother_pattern, replace_smoother_calls, content, flags=re.MULTILINE | re.DOTALL)
    
    # 7. 写入修改后的文件
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 头部位置历史记忆系统已完全禁用")
    print()
    print("📊 修改总结:")
    print("   🚫 HEAD_POSITION_SMOOTHER_AVAILABLE = False")
    print("   🚫 head_smoother = None (强制禁用)")
    print("   🚫 移除所有 head_smoother.update_position() 调用")
    print("   ✅ 直接使用原始头部位置，无历史记忆")
    print()
    print("🎯 效果:")
    print("   • 头部位置将实时跟随当前检测结果")
    print("   • 不会有历史记忆导致的位置延迟")
    print("   • 移动鼠标时头部位置立即更新")
    print("   • 避免多目标混淆问题")
    
    return True

def verify_head_memory_disabled():
    """验证头部记忆是否已禁用"""
    print()
    print("🔍 验证头部记忆禁用状态...")
    
    with open("main_onnx.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键指标
    checks = [
        ("HEAD_POSITION_SMOOTHER_AVAILABLE = False", "头部平滑系统已禁用"),
        ("head_smoother = None", "头部平滑器已设为None"),
        ("head_smoother.update_position" not in content, "头部平滑调用已移除"),
        ("无历史记忆" in content, "添加了无历史记忆说明")
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
    
    if all_passed:
        print("🎉 头部记忆已完全禁用！")
    else:
        print("⚠️ 部分检查未通过，可能需要手动调整")
    
    return all_passed

if __name__ == "__main__":
    print("🎯 头部位置历史记忆禁用工具")
    print("=" * 50)
    
    success = disable_head_memory_system()
    
    if success:
        verify_head_memory_disabled()
        print()
        print("🚀 现在重新启动程序，头部位置将实时跟随检测结果，无历史记忆！")
    else:
        print("❌ 禁用过程中出现错误")
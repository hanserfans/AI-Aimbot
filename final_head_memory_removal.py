#!/usr/bin/env python3
"""
最终头部历史记忆移除脚本
彻底移除所有头部位置历史记忆功能，确保完全实时跟踪
"""

import os
import re
import shutil
from datetime import datetime

def final_head_memory_removal():
    """彻底移除头部历史记忆功能"""
    
    main_file = "main_onnx.py"
    
    if not os.path.exists(main_file):
        print(f"❌ 错误: 找不到文件 {main_file}")
        return False
    
    # 备份原文件
    timestamp = int(datetime.now().timestamp())
    backup_file = f"main_onnx_before_final_memory_removal_{timestamp}.py"
    shutil.copy2(main_file, backup_file)
    print(f"✅ 已备份原文件到: {backup_file}")
    
    # 读取文件内容
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 移除头部记忆增强的代码块
    memory_enhancement_pattern = r'# 🧠 头部记忆增强：.*?(?=\n    # [^🧠]|\n\n|\Z)'
    content = re.sub(memory_enhancement_pattern, '', content, flags=re.DOTALL)
    
    # 2. 移除get_predicted_or_locked_head_position函数调用
    predicted_pos_pattern = r'predicted_pos = get_predicted_or_locked_head_position\(\).*?(?=\n    [^ ]|\n\n|\Z)'
    content = re.sub(predicted_pos_pattern, '', content, flags=re.DOTALL)
    
    # 3. 移除if predicted_pos代码块
    if_predicted_pattern = r'if predicted_pos:.*?(?=\n    [^ ]|\n\n|\Z)'
    content = re.sub(if_predicted_pattern, '', content, flags=re.DOTALL)
    
    # 4. 移除HEAD_MEMORY相关的print语句
    head_memory_print_pattern = r'print\(f"\[HEAD_MEMORY.*?\)\n'
    content = re.sub(head_memory_print_pattern, '', content)
    
    # 5. 移除get_predicted_or_locked_head_position函数定义
    function_def_pattern = r'def get_predicted_or_locked_head_position\(\):.*?(?=\n    def |\n\n|\Z)'
    content = re.sub(function_def_pattern, '', content, flags=re.DOTALL)
    
    # 6. 移除head_position_history相关代码
    history_pattern = r'head_position_history.*?\n'
    content = re.sub(history_pattern, '', content)
    
    # 7. 移除predict_head_position相关调用
    predict_pattern = r'predict_head_position\(\).*?\n'
    content = re.sub(predict_pattern, '', content)
    
    # 8. 移除get_stable_head_position相关调用
    stable_pattern = r'get_stable_head_position\(\).*?\n'
    content = re.sub(stable_pattern, '', content)
    
    # 9. 清理多余的空行
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # 10. 添加实时头部位置说明
    if "# 直接计算实时头部位置，无历史记忆" not in content:
        content = content.replace(
            "# 计算头部位置",
            "# 直接计算实时头部位置，无历史记忆"
        )
    
    # 写入修改后的内容
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已彻底移除头部历史记忆功能")
    
    # 验证修复结果
    verification_checks = [
        ("get_predicted_or_locked_head_position" not in content, "预测位置函数已移除"),
        ("HEAD_MEMORY" not in content, "头部记忆日志已移除"),
        ("🧠 头部记忆增强" not in content, "头部记忆增强注释已移除"),
        ("predicted_pos" not in content, "预测位置变量已移除"),
        ("head_position_history" not in content, "头部位置历史已移除"),
        ("predict_head_position" not in content, "头部位置预测已移除"),
        ("get_stable_head_position" not in content, "稳定头部位置已移除"),
    ]
    
    print("\n📋 验证结果:")
    all_passed = True
    for check, description in verification_checks:
        status = "✅" if check else "❌"
        print(f"  {status} {description}")
        if not check:
            all_passed = False
    
    if all_passed:
        print("\n🎉 头部位置历史记忆已彻底移除！现在头部位置将完全实时跟随检测结果。")
    else:
        print("\n⚠️ 部分检查未通过，可能需要手动清理剩余代码。")
    
    return all_passed

if __name__ == "__main__":
    print("🚀 开始最终头部历史记忆移除...")
    success = final_head_memory_removal()
    if success:
        print("✅ 修复完成！")
    else:
        print("❌ 修复过程中遇到问题。")
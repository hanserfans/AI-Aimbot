#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证瞄准和扳机分离控制配置
检查 main_onnx.py 中的按键配置是否正确分离
"""

import re
import os

def verify_separated_controls():
    """验证瞄准和扳机控制是否正确分离"""
    main_file = "main_onnx.py"
    
    if not os.path.exists(main_file):
        print(f"❌ 错误: 找不到文件 {main_file}")
        return False
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 验证瞄准和扳机分离控制配置...")
    print("=" * 50)
    
    # 检查瞄准激活键 (Caps Lock - 0x14)
    aim_pattern = r'if\s+win32api\.GetKeyState\(0x14\)\s*<\s*0:'
    aim_matches = re.findall(aim_pattern, content)
    
    print(f"🎯 瞄准激活键 (Caps Lock - 0x14):")
    if aim_matches:
        print(f"   ✅ 找到 {len(aim_matches)} 处瞄准激活逻辑")
        # 查找具体位置
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(aim_pattern, line):
                print(f"   📍 第 {i} 行: {line.strip()}")
    else:
        print("   ❌ 未找到瞄准激活逻辑")
    
    print()
    
    # 检查扳机激活键 (右键 - 0x02)
    trigger_pattern = r'if\s+win32api\.GetKeyState\(0x02\)\s*<\s*0.*trigger'
    trigger_matches = re.findall(trigger_pattern, content, re.IGNORECASE)
    
    print(f"🔫 扳机激活键 (鼠标右键 - 0x02):")
    if trigger_matches:
        print(f"   ✅ 找到 {len(trigger_matches)} 处扳机激活逻辑")
        # 查找具体位置
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(trigger_pattern, line, re.IGNORECASE):
                print(f"   📍 第 {i} 行: {line.strip()}")
    else:
        print("   ❌ 未找到扳机激活逻辑")
        # 检查是否还有旧的扳机逻辑
        old_trigger_pattern = r'trigger_system\.enabled'
        old_matches = re.findall(old_trigger_pattern, content)
        if old_matches:
            print(f"   ⚠️  发现 {len(old_matches)} 处旧的扳机逻辑 (trigger_system.enabled)")
    
    print()
    
    # 检查启动说明
    print("📋 启动说明检查:")
    if "Caps Lock - 激活瞄准功能" in content:
        print("   ✅ 瞄准功能说明正确")
    else:
        print("   ❌ 瞄准功能说明缺失或错误")
    
    if "鼠标右键 - 激活扳机功能" in content:
        print("   ✅ 扳机功能说明正确")
    else:
        print("   ❌ 扳机功能说明缺失或错误")
    
    print()
    print("=" * 50)
    print("📝 配置总结:")
    print("   🎯 瞄准激活: Caps Lock (按住)")
    print("   🔫 扳机激活: 鼠标右键 (按住)")
    print("   🔧 扳机开关: 鼠标侧键2 (切换)")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    verify_separated_controls()
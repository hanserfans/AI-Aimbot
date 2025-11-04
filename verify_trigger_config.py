#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扳机激活键配置验证脚本
验证main_onnx.py中的扳机激活键是否正确设置为鼠标右键
"""

import re
import os

def verify_trigger_config():
    """验证扳机激活键配置"""
    print("🔍 验证扳机激活键配置...")
    print("=" * 50)
    
    # 检查main_onnx.py中的扳机激活键
    main_file = "main_onnx.py"
    if not os.path.exists(main_file):
        print(f"❌ 错误: 找不到文件 {main_file}")
        return False
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找扳机激活键配置
    trigger_pattern = r'win32api\.GetKeyState\((0x\w+)\)\s*<\s*0.*?#\s*(.*?)激活'
    matches = re.findall(trigger_pattern, content, re.IGNORECASE)
    
    print("📋 扳机激活键配置检查:")
    
    if matches:
        for key_code, description in matches:
            if key_code == "0x02":
                print(f"✅ 扳机激活键: {key_code} ({description}激活) - 正确!")
            elif key_code == "0x14":
                print(f"❌ 扳机激活键: {key_code} ({description}激活) - 仍为Caps Lock!")
                return False
            else:
                print(f"⚠️  扳机激活键: {key_code} ({description}激活) - 未知键码")
    else:
        print("❌ 未找到扳机激活键配置")
        return False
    
    # 检查config.py中的自动开火键设置
    config_file = "config.py"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # 查找autoFireKey设置
        auto_fire_pattern = r'autoFireKey\s*=\s*["\']([^"\']+)["\']'
        auto_fire_match = re.search(auto_fire_pattern, config_content)
        
        print("\n📋 自动开火键配置检查:")
        if auto_fire_match:
            auto_fire_key = auto_fire_match.group(1)
            print(f"✅ 自动开火键: {auto_fire_key}")
        else:
            print("❌ 未找到自动开火键配置")
    
    print("\n" + "=" * 50)
    print("🎯 配置验证完成!")
    print("\n📖 使用说明:")
    print("🖱️  按住鼠标右键: 激活自动瞄准")
    print("🔫 自动开火: 当目标接近中心时自动开火")
    print("🤖 智能扳机: 独立运行，精确对齐时自动开火")
    print("\n⚠️  注意: 重启AI瞄准程序后新配置才会生效!")
    
    return True

if __name__ == "__main__":
    verify_trigger_config()
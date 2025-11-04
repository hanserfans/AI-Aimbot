#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按键配置验证脚本
验证AI瞄准程序的按键配置是否正确设置
"""

import re
import os

def verify_key_configuration():
    """验证按键配置"""
    print("🔍 验证AI瞄准程序按键配置...")
    print("=" * 50)
    
    # 检查main_onnx.py中的瞄准激活键
    main_onnx_path = "main_onnx.py"
    if os.path.exists(main_onnx_path):
        with open(main_onnx_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找瞄准激活键
        caps_lock_pattern = r'win32api\.GetKeyState\(0x14\).*?#.*?Caps Lock'
        right_click_pattern = r'win32api\.GetKeyState\(0x02\).*?#.*?右键'
        
        if re.search(caps_lock_pattern, content, re.IGNORECASE):
            print("✅ main_onnx.py: 瞄准激活键 = Caps Lock (0x14)")
            aim_key_status = "✅ 正确"
        elif re.search(right_click_pattern, content, re.IGNORECASE):
            print("❌ main_onnx.py: 瞄准激活键 = 右键 (0x02)")
            aim_key_status = "❌ 错误"
        else:
            print("⚠️ main_onnx.py: 未找到明确的瞄准激活键配置")
            aim_key_status = "⚠️ 未知"
    else:
        print("❌ 未找到 main_onnx.py 文件")
        aim_key_status = "❌ 文件不存在"
    
    # 检查config.py中的自动开火键
    config_path = "config.py"
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找自动开火键设置
        fire_key_pattern = r'autoFireKey\s*=\s*["\']([^"\']+)["\']'
        match = re.search(fire_key_pattern, content)
        
        if match:
            fire_key = match.group(1)
            print(f"✅ config.py: 自动开火键 = {fire_key}")
            if fire_key == "left_click":
                fire_key_status = "✅ 正确"
            else:
                fire_key_status = f"⚠️ 设置为 {fire_key}"
        else:
            print("❌ config.py: 未找到 autoFireKey 配置")
            fire_key_status = "❌ 未找到"
    else:
        print("❌ 未找到 config.py 文件")
        fire_key_status = "❌ 文件不存在"
    
    print("\n" + "=" * 50)
    print("📋 配置验证结果:")
    print(f"   瞄准激活键: {aim_key_status}")
    print(f"   自动开火键: {fire_key_status}")
    
    # 显示推荐的按键配置
    print("\n🎯 推荐的按键配置:")
    print("   ⌨️  瞄准激活: Caps Lock")
    print("   🖱️  自动开火: 左键 (left_click)")
    print("   🎯 智能扳机: 鼠标侧键2 (自动检测)")
    
    # 检查是否配置正确
    if aim_key_status == "✅ 正确" and fire_key_status == "✅ 正确":
        print("\n🎉 配置验证通过！按键设置正确。")
        print("\n📖 使用说明:")
        print("   1. 按住 Caps Lock 激活瞄准")
        print("   2. 当目标接近中心时自动用左键开火")
        print("   3. 智能扳机系统独立运行，精确对齐时自动开火")
        return True
    else:
        print("\n⚠️ 配置需要调整，请检查上述问题。")
        return False

if __name__ == "__main__":
    verify_key_configuration()
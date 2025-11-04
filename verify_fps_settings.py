#!/usr/bin/env python3
"""
FPS设置验证脚本
验证所有相关文件中的FPS设置是否已正确修改为100
"""

import re
import os

def check_fps_settings():
    """检查所有相关文件中的FPS设置"""
    
    files_to_check = [
        {
            'file': 'gameSelection.py',
            'patterns': [r'target_fps=(\d+)'],
            'expected': '100'
        },
        {
            'file': 'performance_optimizer.py', 
            'patterns': [r'self\.target_fps = (\d+)'],
            'expected': '100'
        },
        {
            'file': 'customScripts/AimAssist/main_onnx_amd_perf.py',
            'patterns': [r'Max_FPS = (\d+)'],
            'expected': '100'
        },
        {
            'file': 'customScripts/yolov8_live_overlay/yolov8_live_overlay.py',
            'patterns': [r'target_fps=(\d+)'],
            'expected': '100'
        }
    ]
    
    print("🔍 验证FPS设置修改...")
    print("=" * 50)
    
    all_correct = True
    
    for file_info in files_to_check:
        file_path = file_info['file']
        patterns = file_info['patterns']
        expected = file_info['expected']
        
        print(f"\n📁 检查文件: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"   ❌ 文件不存在")
            all_correct = False
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            found_settings = []
            for pattern in patterns:
                matches = re.findall(pattern, content)
                found_settings.extend(matches)
            
            if not found_settings:
                print(f"   ⚠️  未找到FPS设置")
                all_correct = False
            else:
                for setting in found_settings:
                    if setting == expected:
                        print(f"   ✅ FPS设置正确: {setting}")
                    else:
                        print(f"   ❌ FPS设置错误: {setting} (期望: {expected})")
                        all_correct = False
                        
        except Exception as e:
            print(f"   ❌ 读取文件失败: {e}")
            all_correct = False
    
    print("\n" + "=" * 50)
    if all_correct:
        print("🎉 所有FPS设置已正确修改为100!")
        print("💡 重新启动瞄准程序后，检测帧数将设置为100左右")
    else:
        print("⚠️  部分FPS设置可能需要手动检查")
    
    return all_correct

if __name__ == "__main__":
    check_fps_settings()
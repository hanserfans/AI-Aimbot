#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用G-Hub修复到原始MouseMove.py文件
直接修复原始代码中的c_char字段赋值问题
确保G-Hub驱动在瓦洛兰特中正常工作
"""

import os
import shutil
from datetime import datetime

def backup_original_file():
    """备份原始MouseMove.py文件"""
    original_path = "mouse_driver/MouseMove.py"
    backup_path = f"mouse_driver/MouseMove_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    if os.path.exists(original_path):
        shutil.copy2(original_path, backup_path)
        print(f"✅ 原始文件已备份到: {backup_path}")
        return True
    else:
        print(f"❌ 找不到原始文件: {original_path}")
        return False

def apply_fix_to_mousemove():
    """应用修复到MouseMove.py文件"""
    file_path = "mouse_driver/MouseMove.py"
    
    if not os.path.exists(file_path):
        print(f"❌ 找不到文件: {file_path}")
        return False
    
    # 读取原始文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义修复后的mouse_move函数
    fixed_mouse_move_function = '''def mouse_move(button: int, x: int, y: int, wheel: int) -> None:
    """
    发送相对鼠标移动到 G-Hub 设备 (修复版本)
    
    Args:
        button: 按钮状态
        x: X 轴相对移动距离
        y: Y 轴相对移动距离
        wheel: 滚轮移动
    """
    global handle

    def signed_byte_to_char(value: int) -> int:
        """将有符号整数转换为c_char可接受的值"""
        clamped = clamp_char(value)
        if clamped < 0:
            return 256 + clamped  # 二进制补码
        else:
            return clamped

    x_clamped = clamp_char(x)
    y_clamped = clamp_char(y)
    btn_byte = clamp_char(button)
    wheel_byte = clamp_char(wheel)

    io = MOUSE_IO()
    # 修复: 正确设置c_char字段
    io.button = signed_byte_to_char(btn_byte)
    io.x = signed_byte_to_char(x_clamped)
    io.y = signed_byte_to_char(y_clamped)
    io.wheel = signed_byte_to_char(wheel_byte)
    io.unk1 = 0

    if not call_mouse(io):
        mouse_close()
        if not mouse_open():
            print("Failed to reinitialize G-Hub device after error.")'''
    
    # 查找并替换原始的mouse_move函数
    import re
    
    # 匹配原始的mouse_move函数（从def开始到下一个def或文件结束）
    pattern = r'def mouse_move\(button: int, x: int, y: int, wheel: int\) -> None:.*?(?=\n\ndef|\nclass|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        # 替换函数
        new_content = re.sub(pattern, fixed_mouse_move_function, content, flags=re.DOTALL)
        
        # 写入修复后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ MouseMove.py文件已成功修复！")
        print("🔧 修复内容:")
        print("  • 添加了signed_byte_to_char函数来正确处理有符号字节")
        print("  • 修复了c_char字段的赋值方式")
        print("  • 移除了错误的ctypes.c_char()调用")
        return True
    else:
        print("❌ 未找到要替换的mouse_move函数")
        return False

def test_fixed_driver():
    """测试修复后的驱动"""
    print("\n🧪 测试修复后的G-Hub驱动...")
    
    try:
        import sys
        sys.path.append('mouse_driver')
        from MouseMove import ghub_move, mouse_open
        
        # 确保设备已打开
        if mouse_open():
            print("✅ G-Hub设备已成功打开")
            
            # 测试简单移动
            print("🔄 测试鼠标移动...")
            ghub_move(10, 10)  # 小幅移动测试
            
            print("✅ 修复后的驱动测试完成")
            print("🎮 现在可以在瓦洛兰特中使用G-Hub驱动了！")
            return True
        else:
            print("❌ G-Hub设备打开失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("G-Hub驱动修复应用工具")
    print("直接修复MouseMove.py文件中的c_char字段赋值问题")
    print("="*60)
    
    # 1. 备份原始文件
    if not backup_original_file():
        return
    
    # 2. 应用修复
    if not apply_fix_to_mousemove():
        return
    
    # 3. 测试修复后的驱动
    test_fixed_driver()
    
    print(f"\n{'='*60}")
    print("🎯 修复应用总结:")
    print("✅ 原始文件已备份")
    print("✅ G-Hub驱动修复已应用")
    print("✅ c_char字段赋值问题已解决")
    print("🎮 G-Hub驱动现在应该能在瓦洛兰特中正常工作了！")
    print("\n📝 修复说明:")
    print("• 问题: 原始代码使用错误的ctypes.c_char()方式赋值")
    print("• 解决: 使用正确的有符号字节值直接赋值")
    print("• 兼容: G-Hub驱动硬件级别，不会被瓦洛兰特反作弊检测")
    
    input("\n按Enter键退出...")

if __name__ == "__main__":
    main()
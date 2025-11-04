#!/usr/bin/env python3
"""
紧急修复激活键检测逻辑
修复第770行的条件判断错误
"""

def fix_activation_logic():
    """修复激活键检测逻辑中的条件判断错误"""
    print("=== 紧急修复激活键检测逻辑 ===")
    print("问题: 第770行的条件判断导致右键按下时进入else分支")
    print("修复: 简化条件判断逻辑")
    print()
    
    try:
        # 读取当前文件
        with open('main_onnx.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找问题行
        lines = content.split('\n')
        
        # 找到问题行并修复
        for i, line in enumerate(lines):
            if 'elif caps_lock_pressed or (activation_key_pressed and last_caps_lock_state and not last_right_mouse_state):' in line:
                print(f"找到问题行 {i+1}: {line.strip()}")
                
                # 修复条件判断
                lines[i] = '                elif caps_lock_pressed:'
                print(f"修复为: {lines[i].strip()}")
                break
        else:
            print("未找到问题行，可能已经修复")
            return False
        
        # 写回文件
        fixed_content = '\n'.join(lines)
        with open('main_onnx.py', 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("✓ 修复完成")
        return True
        
    except Exception as e:
        print(f"修复失败: {e}")
        return False

def verify_fix():
    """验证修复是否成功"""
    print("\n=== 验证修复结果 ===")
    
    try:
        with open('main_onnx.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # 查找相关行
        for i, line in enumerate(lines, 1):
            if 'elif caps_lock_pressed:' in line and i > 760 and i < 780:
                print(f"✓ 第 {i} 行已修复: {line.strip()}")
                
                # 检查前后几行的逻辑
                print("修复后的逻辑结构:")
                for j in range(max(0, i-5), min(len(lines), i+5)):
                    marker = ">>> " if j == i-1 else "    "
                    print(f"{marker}第 {j+1:3d} 行: {lines[j].strip()}")
                
                return True
        
        print("✗ 修复验证失败")
        return False
        
    except Exception as e:
        print(f"验证失败: {e}")
        return False

def create_simple_test():
    """创建简单的激活键测试"""
    print("\n=== 创建简单测试 ===")
    
    test_code = '''#!/usr/bin/env python3
"""简单的激活键测试"""
import win32api
import time

print("简单激活键测试 - 按右键或Caps Lock测试")
print("按 Ctrl+C 退出")

try:
    while True:
        caps_lock_pressed = win32api.GetKeyState(0x14) & 0x0001
        right_mouse_pressed = win32api.GetKeyState(0x02) & 0x8000
        
        status = []
        if right_mouse_pressed:
            status.append("右键")
        if caps_lock_pressed:
            status.append("Caps Lock")
        
        if status:
            print(f"激活: {' + '.join(status)}")
        else:
            print("无激活键", end="\\r")
        
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\\n测试结束")
'''
    
    with open('simple_activation_test.py', 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    print("✓ 创建了 simple_activation_test.py")
    print("可以运行: python simple_activation_test.py")

if __name__ == "__main__":
    if fix_activation_logic():
        if verify_fix():
            print("\n🎉 修复成功！现在可以测试激活键检测了")
            create_simple_test()
        else:
            print("\n❌ 修复验证失败")
    else:
        print("\n❌ 修复失败")
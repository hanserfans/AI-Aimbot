#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连续移动修复补丁
修复main_onnx.py中鼠标移动一次后停止的问题
"""

def apply_continuous_movement_patch():
    """应用连续移动修复补丁"""
    
    # 读取原始文件
    with open('main_onnx.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找需要修复的代码段
    # 在激活键检测之前添加连续移动逻辑
    
    # 1. 在main函数开始处添加激活键状态变量
    main_func_start = content.find('def main():')
    if main_func_start == -1:
        print("❌ 未找到main函数")
        return False
        
    # 找到main函数内的第一个变量声明位置
    main_body_start = content.find('\n', main_func_start) + 1
    while content[main_body_start:main_body_start+4] == '    ':
        main_body_start = content.find('\n', main_body_start) + 1
    
    # 添加激活键状态缓存变量
    activation_vars = '''    # 激活键状态缓存（用于连续移动）
    last_activation_time = 0
    activation_key_pressed = False
    last_right_mouse_state = False
    last_caps_lock_state = False
    
'''
    
    # 2. 修复激活键检测逻辑
    # 查找激活键检测的位置
    activation_check = content.find('# 检查激活键状态')
    if activation_check == -1:
        print("❌ 未找到激活键检测代码")
        return False
    
    # 查找这个检测块的结束位置（找到else分支）
    else_branch = content.find('else:\n                    print(f"[DEBUG] 目标偏离中心 {distance:.1f}px，无激活键按下")')
    if else_branch == -1:
        print("❌ 未找到else分支")
        return False
    
    # 替换激活键检测逻辑
    new_activation_logic = '''                # 检查激活键状态（增强版 - 支持连续移动）
                caps_lock_pressed = win32api.GetKeyState(0x14) < 0  # Caps Lock
                right_mouse_pressed = win32api.GetKeyState(0x02) < 0  # 鼠标右键
                
                # 激活键状态变化检测
                current_time = time.time()
                activation_changed = (right_mouse_pressed != last_right_mouse_state or 
                                    caps_lock_pressed != last_caps_lock_state)
                
                if activation_changed:
                    last_right_mouse_state = right_mouse_pressed
                    last_caps_lock_state = caps_lock_pressed
                    if right_mouse_pressed or caps_lock_pressed:
                        last_activation_time = current_time
                        activation_key_pressed = True
                        print(f"[DEBUG] 激活键状态变化: 右键={right_mouse_pressed}, Caps={caps_lock_pressed}")
                    else:
                        activation_key_pressed = False
                        print(f"[DEBUG] 激活键释放")
                
                # 连续移动逻辑：如果激活键按下或在短时间内释放，继续移动
                activation_timeout = 0.1  # 100ms激活键释放容忍时间
                is_activation_valid = (right_mouse_pressed or caps_lock_pressed or 
                                     (activation_key_pressed and (current_time - last_activation_time) < activation_timeout))
                
                # 使用动态跟踪系统进行瞄准（鼠标右键激活瞄准和扳机）
                if right_mouse_pressed or (activation_key_pressed and last_right_mouse_state):
                    print(f"[DEBUG] 🖱️ 右键模式激活 - 瞄准+扳机 (连续={activation_key_pressed})")'''
    
    # 3. 修复Caps Lock分支
    caps_elif = content.find('elif caps_lock_pressed:')
    if caps_elif != -1:
        new_caps_logic = '''elif caps_lock_pressed or (activation_key_pressed and last_caps_lock_state and not last_right_mouse_state):
                    # Caps Lock只激活瞄准，不开火（支持连续移动）
                    print(f"[DEBUG] Caps Lock模式激活 - 仅瞄准 (连续={activation_key_pressed})")'''
        
        # 找到这个elif分支的结束位置
        caps_end = content.find('\n                else:', caps_elif)
        if caps_end != -1:
            content = content[:caps_elif] + new_caps_logic + content[caps_end:]
    
    # 4. 修复else分支，添加更详细的调试信息
    new_else_logic = '''else:
                    # 详细的激活键状态调试信息
                    debug_msg = f"[DEBUG] 目标偏离中心 {distance:.1f}px"
                    if not right_mouse_pressed and not caps_lock_pressed:
                        if activation_key_pressed:
                            time_since_release = current_time - last_activation_time
                            debug_msg += f"，激活键刚释放 ({time_since_release*1000:.0f}ms前)"
                        else:
                            debug_msg += f"，无激活键按下"
                    print(debug_msg)'''
    
    # 应用修复
    try:
        # 插入激活键状态变量
        content = content[:main_body_start] + activation_vars + content[main_body_start:]
        
        # 替换激活键检测逻辑
        activation_end = content.find('\n                # 使用动态跟踪系统进行瞄准（鼠标右键激活瞄准和扳机）')
        if activation_end != -1:
            content = content[:activation_check] + new_activation_logic + content[activation_end:]
        
        # 替换else分支
        else_end = content.find('\n                \n                # 显示偏差信息', else_branch)
        if else_end != -1:
            content = content[:else_branch] + new_else_logic + content[else_end:]
        
        # 写入修复后的文件
        with open('main_onnx_fixed.py', 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("✅ 连续移动修复补丁应用成功")
        print("📁 修复后的文件保存为: main_onnx_fixed.py")
        print()
        print("🔧 修复内容:")
        print("1. 添加激活键状态缓存")
        print("2. 支持激活键释放后100ms内继续移动")
        print("3. 增强调试信息显示")
        print("4. 优化连续移动逻辑")
        
        return True
        
    except Exception as e:
        print(f"❌ 应用补丁时出错: {e}")
        return False

def create_simple_fix():
    """创建简单的修复版本"""
    print("🔧 创建简化版连续移动修复...")
    
    # 简单的修复：在移动完成后立即重新检查目标距离
    simple_fix_code = '''
# 简化版连续移动修复
# 在移动完成后添加以下代码：

# 移动完成后重新检查目标距离
time.sleep(0.01)  # 短暂延迟让移动生效
new_offset_info = coord_system.calculate_crosshair_to_target_offset(head_x, head_y)
new_distance = int(new_offset_info['pixel']['distance'])

print(f"[DEBUG] 移动后目标距离: {new_distance:.1f}px (原距离: {distance:.1f}px)")

# 如果目标仍未对齐且激活键仍按下，标记需要继续移动
if new_distance > 10:  # 距离阈值
    # 重新检查激活键状态
    still_right_pressed = win32api.GetKeyState(0x02) < 0
    still_caps_pressed = win32api.GetKeyState(0x14) < 0
    
    if still_right_pressed or still_caps_pressed:
        print(f"[DEBUG] 目标仍未对齐({new_distance:.1f}px)，激活键仍按下，将在下次循环继续移动")
    else:
        print(f"[DEBUG] 目标仍未对齐({new_distance:.1f}px)，但激活键已释放")
else:
    print(f"[DEBUG] 目标已对齐({new_distance:.1f}px)")
'''
    
    with open('simple_movement_fix.py', 'w', encoding='utf-8') as f:
        f.write(simple_fix_code)
    
    print("📁 简化修复代码保存为: simple_movement_fix.py")

if __name__ == "__main__":
    print("🚀 连续移动修复补丁")
    print("=" * 50)
    
    try:
        # 应用完整补丁
        if apply_continuous_movement_patch():
            print("\n✅ 完整补丁应用成功")
        else:
            print("\n⚠️ 完整补丁应用失败，创建简化版本...")
            create_simple_fix()
            
    except Exception as e:
        print(f"\n❌ 补丁应用过程中出错: {e}")
        print("创建简化版本...")
        create_simple_fix()
"""
验证鼠标移动脚本 - 检查鼠标位置是否真的在变化
"""
import sys
import os
import time
import ctypes
from ctypes import wintypes

# 添加mouse_driver路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mouse_driver'))

def get_cursor_position():
    """获取当前鼠标光标位置"""
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    point = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y

def is_admin():
    """检查是否有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    print("=== 鼠标移动验证测试 ===")
    print(f"管理员权限: {'✓' if is_admin() else '✗'}")
    
    if not is_admin():
        print("⚠️  警告: 没有管理员权限，可能影响G-Hub设备访问")
    
    try:
        # 导入G-Hub移动函数
        from mouse_driver.MouseMove import ghub_move, initialize_mouse
        print("✓ 成功导入MouseMove模块")
        
        # 初始化鼠标
        if not initialize_mouse():
            print("✗ G-Hub鼠标初始化失败")
            return
        print("✓ G-Hub鼠标初始化成功")
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return
    
    print("\n开始鼠标移动验证测试...")
    print("请不要移动鼠标，让程序检测移动是否有效")
    
    # 测试1: 记录初始位置
    print("\n=== 测试1: 大幅移动测试 ===")
    initial_x, initial_y = get_cursor_position()
    print(f"初始位置: ({initial_x}, {initial_y})")
    
    time.sleep(1)
    
    # 执行大幅移动
    print("执行: ghub_move(100, 100)")
    result = ghub_move(100, 100)
    print(f"函数返回: {result}")
    
    time.sleep(0.5)
    
    # 检查位置变化
    new_x, new_y = get_cursor_position()
    print(f"移动后位置: ({new_x}, {new_y})")
    
    dx = new_x - initial_x
    dy = new_y - initial_y
    print(f"实际位移: ({dx}, {dy})")
    
    if dx != 0 or dy != 0:
        print("✓ 检测到鼠标移动！")
    else:
        print("✗ 没有检测到鼠标移动")
    
    # 测试2: 连续移动测试
    print("\n=== 测试2: 连续移动测试 ===")
    positions = []
    
    for i in range(5):
        x, y = get_cursor_position()
        positions.append((x, y))
        print(f"位置{i+1}: ({x}, {y})")
        
        if i < 4:  # 不在最后一次执行移动
            print(f"执行: ghub_move(20, 0)")
            ghub_move(20, 0)
            time.sleep(0.3)
    
    # 分析位置变化
    print("\n位置变化分析:")
    total_movement = 0
    for i in range(1, len(positions)):
        prev_x, prev_y = positions[i-1]
        curr_x, curr_y = positions[i]
        dx = curr_x - prev_x
        dy = curr_y - prev_y
        movement = (dx**2 + dy**2)**0.5
        total_movement += movement
        print(f"步骤{i}: 位移({dx}, {dy}), 距离: {movement:.1f}")
    
    print(f"\n总移动距离: {total_movement:.1f} 像素")
    
    if total_movement > 10:
        print("✓ 检测到明显的鼠标移动")
    elif total_movement > 0:
        print("⚠️  检测到轻微移动，可能是系统误差")
    else:
        print("✗ 完全没有检测到移动")
    
    # 测试3: 对比测试 - 使用Windows API移动
    print("\n=== 测试3: 对比测试 (Windows API) ===")
    initial_x, initial_y = get_cursor_position()
    print(f"对比测试初始位置: ({initial_x}, {initial_y})")
    
    # 使用Windows API移动鼠标
    ctypes.windll.user32.SetCursorPos(initial_x + 50, initial_y + 50)
    time.sleep(0.5)
    
    api_x, api_y = get_cursor_position()
    print(f"API移动后位置: ({api_x}, {api_y})")
    
    api_dx = api_x - initial_x
    api_dy = api_y - initial_y
    print(f"API实际位移: ({api_dx}, {api_dy})")
    
    if api_dx != 0 or api_dy != 0:
        print("✓ Windows API移动正常")
    else:
        print("✗ Windows API移动也失败")
    
    # 恢复到初始位置
    ctypes.windll.user32.SetCursorPos(initial_x, initial_y)
    
    print("\n=== 测试结论 ===")
    if total_movement > 10:
        print("✓ G-Hub鼠标移动功能正常工作")
    elif total_movement > 0:
        print("⚠️  G-Hub移动有效果但很微弱，可能需要调整参数")
    else:
        print("✗ G-Hub鼠标移动无效，需要进一步诊断")
        print("\n可能的原因:")
        print("1. G-Hub软件未正确运行")
        print("2. 设备驱动问题")
        print("3. 权限不足")
        print("4. 设备路径错误")

if __name__ == "__main__":
    main()
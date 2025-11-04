"""
综合鼠标输入测试 - 对比不同的输入方法
"""
import sys
import os
import time
import ctypes
from ctypes import wintypes

def get_cursor_position():
    """获取当前鼠标光标位置"""
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    point = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y

def test_windows_api():
    """测试Windows API鼠标移动"""
    print("=== 测试1: Windows API ===")
    
    initial_x, initial_y = get_cursor_position()
    print(f"初始位置: ({initial_x}, {initial_y})")
    
    # 使用SetCursorPos移动鼠标
    new_x, new_y = initial_x + 50, initial_y + 50
    ctypes.windll.user32.SetCursorPos(new_x, new_y)
    time.sleep(0.5)
    
    actual_x, actual_y = get_cursor_position()
    print(f"目标位置: ({new_x}, {new_y})")
    print(f"实际位置: ({actual_x}, actual_y)")
    
    # 恢复原位置
    ctypes.windll.user32.SetCursorPos(initial_x, initial_y)
    
    success = (actual_x == new_x and actual_y == new_y)
    print(f"结果: {'✓ 成功' if success else '✗ 失败'}")
    return success

def test_sendinput_api():
    """测试SendInput API"""
    print("\n=== 测试2: SendInput API ===")
    
    # 定义INPUT结构
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long),
                   ("dy", ctypes.c_long),
                   ("mouseData", wintypes.DWORD),
                   ("dwFlags", wintypes.DWORD),
                   ("time", wintypes.DWORD),
                   ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]
    
    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT)]
        _anonymous_ = ("_input",)
        _fields_ = [("type", wintypes.DWORD),
                   ("_input", _INPUT)]
    
    initial_x, initial_y = get_cursor_position()
    print(f"初始位置: ({initial_x}, {initial_y})")
    
    # 创建INPUT结构
    inp = INPUT()
    inp.type = 0  # INPUT_MOUSE
    inp.mi.dx = 100  # 相对移动
    inp.mi.dy = 100
    inp.mi.mouseData = 0
    inp.mi.dwFlags = 0x0001  # MOUSEEVENTF_MOVE
    inp.mi.time = 0
    inp.mi.dwExtraInfo = None
    
    # 发送输入
    result = ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    time.sleep(0.5)
    
    final_x, final_y = get_cursor_position()
    dx, dy = final_x - initial_x, final_y - initial_y
    print(f"移动后位置: ({final_x}, {final_y})")
    print(f"实际位移: ({dx}, {dy})")
    
    success = (abs(dx) > 0 or abs(dy) > 0)
    print(f"结果: {'✓ 成功' if success else '✗ 失败'}")
    return success

def test_ghub_original():
    """测试原始G-Hub实现"""
    print("\n=== 测试3: 原始G-Hub ===")
    
    # 添加g-input路径
    g_input_path = os.path.join(os.path.dirname(__file__), 'mouse_driver', 'g-input-main', 'g-input-main')
    sys.path.insert(0, g_input_path)
    
    try:
        import mouse as GHUB
        print("✓ 成功导入原始mouse模块")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    
    if not GHUB.mouse_open():
        print("✗ G-Hub设备连接失败")
        return False
    print("✓ G-Hub设备连接成功")
    
    initial_x, initial_y = get_cursor_position()
    print(f"初始位置: ({initial_x}, {initial_y})")
    
    # 尝试多种参数组合
    test_params = [
        (0, 10, 10, 0),    # 标准参数
        (0, 1, 1, 0),      # 最小移动
        (0, 127, 127, 0),  # 最大正值
        (0, -10, -10, 0),  # 负值
    ]
    
    total_movement = 0
    for i, (button, x, y, wheel) in enumerate(test_params):
        before_x, before_y = get_cursor_position()
        print(f"  测试{i+1}: GHUB.mouse_move({button}, {x}, {y}, {wheel})")
        
        GHUB.mouse_move(button, x, y, wheel)
        time.sleep(0.3)
        
        after_x, after_y = get_cursor_position()
        dx, dy = after_x - before_x, after_y - before_y
        total_movement += abs(dx) + abs(dy)
        print(f"    位移: ({dx}, {dy})")
    
    GHUB.mouse_close()
    
    success = total_movement > 0
    print(f"总移动量: {total_movement}")
    print(f"结果: {'✓ 成功' if success else '✗ 失败'}")
    return success

def test_our_implementation():
    """测试我们的实现"""
    print("\n=== 测试4: 我们的实现 ===")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mouse_driver'))
        from MouseMove import ghub_move, initialize_mouse, close_mouse
        print("✓ 成功导入我们的MouseMove模块")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    
    if not initialize_mouse():
        print("✗ 设备初始化失败")
        return False
    print("✓ 设备初始化成功")
    
    initial_x, initial_y = get_cursor_position()
    print(f"初始位置: ({initial_x}, {initial_y})")
    
    # 测试移动
    test_moves = [(10, 10), (20, 0), (0, 20), (-10, -10)]
    total_movement = 0
    
    for i, (x, y) in enumerate(test_moves):
        before_x, before_y = get_cursor_position()
        print(f"  测试{i+1}: ghub_move({x}, {y})")
        
        ghub_move(x, y)
        time.sleep(0.3)
        
        after_x, after_y = get_cursor_position()
        dx, dy = after_x - before_x, after_y - before_y
        total_movement += abs(dx) + abs(dy)
        print(f"    位移: ({dx}, {dy})")
    
    close_mouse()
    
    success = total_movement > 0
    print(f"总移动量: {total_movement}")
    print(f"结果: {'✓ 成功' if success else '✗ 失败'}")
    return success

def main():
    print("综合鼠标输入测试")
    print("=" * 50)
    
    results = {}
    
    # 测试各种方法

    results['原始G-Hub'] = test_ghub_original()
    results['我们的实现'] = test_our_implementation()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结:")
    for method, success in results.items():
        status = "✓ 工作正常" if success else "✗ 无效"
        print(f"  {method}: {status}")
    
    working_methods = [method for method, success in results.items() if success]
    if working_methods:
        print(f"\n可用的方法: {', '.join(working_methods)}")
    else:
        print("\n⚠️  所有方法都无效，可能存在系统级问题")
    
    # 建议
    print("\n建议:")
    if results.get('Windows API', False) and not results.get('原始G-Hub', False):
        print("- G-Hub输入可能被系统或安全软件阻止")
        print("- 考虑使用Windows API作为备选方案")
    elif results.get('原始G-Hub', False) and results.get('我们的实现', False):
        print("- ✅ G-Hub驱动工作正常！")
        print("- 两种G-Hub实现都可以正常使用")
        print("- 建议在主程序中使用我们优化过的实现")
    elif not any(results.values()):
        print("- 检查是否有安全软件阻止鼠标输入")
        print("- 尝试以管理员权限运行")
        print("- 检查Windows安全设置")
    else:
        print("- 部分方法可用，建议使用工作正常的方法")

if __name__ == "__main__":
    main()
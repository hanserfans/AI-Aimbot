"""
简单的方向性矫正系统诊断测试
"""

import time
import pyautogui
from directional_correction import directional_mouse

def simple_test():
    """简单测试"""
    print("🔍 开始简单诊断测试")
    print("="*40)
    
    # 获取初始位置
    start_pos = pyautogui.position()
    print(f"初始位置: ({start_pos.x}, {start_pos.y})")
    
    # 测试一个简单的移动
    print("\n测试移动: (10, 0)")
    
    try:
        result = directional_mouse.move_mouse(10, 0, verify=True)
        print(f"移动结果: {result}")
        
        if result.get('success', False):
            print(f"✅ 移动成功")
            print(f"期望: {result['expected']}")
            print(f"实际: {result['actual']}")
            print(f"矫正: {result['corrected']}")
            print(f"因子: {result['factors']}")
            print(f"误差: {result['total_error']:.2f}px")
            print(f"阈值: {result['threshold']:.2f}px")
        else:
            print(f"❌ 移动失败")
            print(f"期望: {result['expected']}")
            print(f"实际: {result['actual']}")
            print(f"误差: {result['total_error']:.2f}px")
            if 'error' in result and isinstance(result['error'], str):
                print(f"错误: {result['error']}")
    
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

def test_mouse_driver():
    """测试鼠标驱动"""
    print("\n🖱️ 测试鼠标驱动")
    print("="*30)
    
    try:
        # 直接测试鼠标驱动
        mouse = directional_mouse.mouse_driver
        print(f"鼠标驱动类型: {type(mouse)}")
        
        start_pos = pyautogui.position()
        print(f"移动前位置: ({start_pos.x}, {start_pos.y})")
        
        # 尝试直接移动
        mouse.move_mouse(5, 0)
        time.sleep(0.1)
        
        end_pos = pyautogui.position()
        print(f"移动后位置: ({end_pos.x}, {end_pos.y})")
        
        actual_dx = end_pos.x - start_pos.x
        actual_dy = end_pos.y - start_pos.y
        print(f"实际移动: ({actual_dx}, {actual_dy})")
        
    except Exception as e:
        print(f"❌ 鼠标驱动测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 启动简单诊断测试")
    
    # 测试鼠标驱动
    test_mouse_driver()
    
    # 测试方向性矫正
    simple_test()
    
    print("\n✅ 诊断测试完成")
#!/usr/bin/env python3
"""
鼠标移动诊断脚本
用于诊断为什么鼠标代码执行成功但视觉上没有移动
"""

import time
import sys
import os
import ctypes
from ctypes import wintypes

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from mouse_driver.MouseMove import ghub_move, ghub_click, mouse_open
except ImportError as e:
    print(f"❌ 无法导入MouseMove模块: {e}")
    sys.exit(1)

class MouseDiagnostic:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        
    def get_cursor_position(self):
        """获取当前鼠标位置"""
        point = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y
    
    def test_win32_movement(self, dx, dy):
        """使用Win32 API测试鼠标移动"""
        print(f"\n🔧 测试Win32 API移动 ({dx}, {dy})")
        
        # 获取移动前位置
        before_x, before_y = self.get_cursor_position()
        print(f"移动前位置: ({before_x}, {before_y})")
        
        # 使用Win32 API移动
        self.user32.mouse_event(0x0001, dx, dy, 0, 0)  # MOUSEEVENTF_MOVE
        time.sleep(0.1)
        
        # 获取移动后位置
        after_x, after_y = self.get_cursor_position()
        print(f"移动后位置: ({after_x}, {after_y})")
        
        actual_dx = after_x - before_x
        actual_dy = after_y - before_y
        print(f"实际移动: ({actual_dx}, {actual_dy})")
        
        return actual_dx != 0 or actual_dy != 0
    
    def test_ghub_movement(self, dx, dy):
        """测试G-Hub移动"""
        print(f"\n🎮 测试G-Hub移动 ({dx}, {dy})")
        
        # 获取移动前位置
        before_x, before_y = self.get_cursor_position()
        print(f"移动前位置: ({before_x}, {before_y})")
        
        # 使用G-Hub移动
        try:
            ghub_move(dx, dy)
            time.sleep(0.1)
        except Exception as e:
            print(f"❌ G-Hub移动失败: {e}")
            return False
        
        # 获取移动后位置
        after_x, after_y = self.get_cursor_position()
        print(f"移动后位置: ({after_x}, {after_y})")
        
        actual_dx = after_x - before_x
        actual_dy = after_y - before_y
        print(f"实际移动: ({actual_dx}, {actual_dy})")
        
        return actual_dx != 0 or actual_dy != 0
    
    def test_absolute_movement(self, target_x, target_y):
        """测试绝对位置移动"""
        print(f"\n📍 测试绝对位置移动到 ({target_x}, {target_y})")
        
        # 获取移动前位置
        before_x, before_y = self.get_cursor_position()
        print(f"移动前位置: ({before_x}, {before_y})")
        
        # 使用SetCursorPos移动到绝对位置
        self.user32.SetCursorPos(target_x, target_y)
        time.sleep(0.1)
        
        # 获取移动后位置
        after_x, after_y = self.get_cursor_position()
        print(f"移动后位置: ({after_x}, {after_y})")
        
        return after_x == target_x and after_y == target_y
    
    def check_ghub_device_status(self):
        """检查G-Hub设备状态"""
        print("\n🔍 检查G-Hub设备状态")
        
        try:
            # 尝试打开G-Hub设备
            device_status = mouse_open()
            if device_status:
                print("✅ G-Hub设备已连接")
                return True
            else:
                print("❌ G-Hub设备未连接")
                return False
        except Exception as e:
            print(f"❌ 检查G-Hub设备时出错: {e}")
            return False
    
    def check_mouse_sensitivity(self):
        """检查系统鼠标灵敏度设置"""
        print("\n⚙️ 检查系统鼠标设置")
        
        try:
            # 获取鼠标灵敏度
            sensitivity = ctypes.c_int()
            self.user32.SystemParametersInfoW(0x0070, 0, ctypes.byref(sensitivity), 0)  # SPI_GETMOUSESPEED
            print(f"系统鼠标速度: {sensitivity.value}")
            
            # 获取鼠标加速
            mouse_params = (ctypes.c_int * 3)()
            self.user32.SystemParametersInfoW(0x0003, 0, mouse_params, 0)  # SPI_GETMOUSE
            print(f"鼠标加速参数: {list(mouse_params)}")
            
        except Exception as e:
            print(f"❌ 获取鼠标设置时出错: {e}")
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始鼠标移动综合诊断")
        print("=" * 50)
        
        # 1. 检查G-Hub设备状态
        ghub_available = self.check_ghub_device_status()
        
        # 2. 检查系统鼠标设置
        self.check_mouse_sensitivity()
        
        # 3. 测试绝对位置移动（最基本的测试）
        print("\n" + "=" * 30)
        print("测试1: 绝对位置移动")
        abs_success = self.test_absolute_movement(500, 300)
        
        # 4. 测试Win32相对移动
        print("\n" + "=" * 30)
        print("测试2: Win32相对移动")
        win32_success = self.test_win32_movement(50, 50)
        
        # 5. 测试G-Hub移动
        print("\n" + "=" * 30)
        print("测试3: G-Hub相对移动")
        ghub_success = self.test_ghub_movement(50, -50)
        
        # 6. 测试不同大小的移动
        print("\n" + "=" * 30)
        print("测试4: 不同大小的G-Hub移动")
        
        test_movements = [
            (1, 1),      # 最小移动
            (10, 10),    # 小移动
            (100, 100),  # 中等移动
            (200, 0),    # 大水平移动
            (0, 200),    # 大垂直移动
        ]
        
        ghub_detailed_results = []
        for dx, dy in test_movements:
            print(f"\n测试移动 ({dx}, {dy}):")
            result = self.test_ghub_movement(dx, dy)
            ghub_detailed_results.append((dx, dy, result))
            time.sleep(0.5)  # 给用户时间观察
        
        # 总结结果
        print("\n" + "=" * 50)
        print("🎯 诊断结果总结")
        print("=" * 50)
        
        print(f"G-Hub设备可用: {'✅' if ghub_available else '❌'}")
        print(f"绝对位置移动: {'✅' if abs_success else '❌'}")
        print(f"Win32相对移动: {'✅' if win32_success else '❌'}")
        print(f"G-Hub相对移动: {'✅' if ghub_success else '❌'}")
        
        print("\nG-Hub详细测试结果:")
        for dx, dy, success in ghub_detailed_results:
            status = '✅' if success else '❌'
            print(f"  移动({dx:3d}, {dy:3d}): {status}")
        
        # 给出建议
        print("\n💡 建议:")
        if not ghub_available:
            print("- 检查罗技G-Hub软件是否正确安装并运行")
            print("- 确认鼠标是否为罗技品牌且支持G-Hub")
        
        if abs_success and not ghub_success:
            print("- G-Hub驱动可能有问题，建议重新安装G-Hub")
            print("- 检查G-Hub中的游戏配置文件设置")
        
        if not win32_success and not ghub_success:
            print("- 可能存在系统级别的鼠标控制问题")
            print("- 检查是否有其他软件阻止鼠标移动")
            print("- 尝试以管理员权限运行程序")
        
        if ghub_success:
            print("- G-Hub移动功能正常，可能是移动幅度太小或其他配置问题")

def main():
    """主函数"""
    print("鼠标移动诊断工具")
    print("请确保在运行期间观察鼠标光标的移动")
    print("按Enter键开始诊断...")
    input()
    
    diagnostic = MouseDiagnostic()
    diagnostic.run_comprehensive_test()
    
    print("\n诊断完成！")

if __name__ == "__main__":
    main()
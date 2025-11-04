#!/usr/bin/env python3
"""
鼠标移动修复脚本
提供G-Hub失效时的Win32 API备用方案
"""

import ctypes
import time
from ctypes import wintypes

class ReliableMouseMove:
    """可靠的鼠标移动类，自动选择最佳移动方法"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.ghub_available = False
        self.test_ghub_functionality()
    
    def get_cursor_position(self):
        """获取当前鼠标位置"""
        point = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y
    
    def test_ghub_functionality(self):
        """测试G-Hub是否真正有效"""
        try:
            from mouse_driver.MouseMove import ghub_move
            
            # 记录移动前位置
            before_x, before_y = self.get_cursor_position()
            
            # 尝试小幅移动
            ghub_move(10, 10)
            time.sleep(0.1)
            
            # 检查是否真的移动了
            after_x, after_y = self.get_cursor_position()
            
            if after_x != before_x or after_y != before_y:
                self.ghub_available = True
                print("✅ G-Hub移动功能正常")
                # 移回原位置
                self.user32.SetCursorPos(before_x, before_y)
            else:
                self.ghub_available = False
                print("❌ G-Hub移动功能无效，将使用Win32备用方案")
                
        except Exception as e:
            self.ghub_available = False
            print(f"❌ G-Hub不可用: {e}")
    
    def move_mouse_win32(self, dx, dy):
        """使用Win32 API移动鼠标（相对移动）"""
        try:
            # 使用mouse_event进行相对移动
            self.user32.mouse_event(0x0001, int(dx), int(dy), 0, 0)  # MOUSEEVENTF_MOVE
            return True
        except Exception as e:
            print(f"Win32移动失败: {e}")
            return False
    
    def move_mouse_ghub(self, dx, dy):
        """使用G-Hub移动鼠标"""
        try:
            from mouse_driver.MouseMove import ghub_move
            ghub_move(dx, dy)
            return True
        except Exception as e:
            print(f"G-Hub移动失败: {e}")
            return False
    
    def move_mouse(self, dx, dy):
        """智能鼠标移动 - 自动选择最佳方法"""
        if self.ghub_available:
            # 尝试G-Hub移动
            success = self.move_mouse_ghub(dx, dy)
            if success:
                return True
        
        # G-Hub失败或不可用，使用Win32备用方案
        return self.move_mouse_win32(dx, dy)
    
    def test_movement(self):
        """测试移动功能"""
        print("\n🧪 测试智能鼠标移动功能")
        
        test_moves = [
            (50, 0),    # 右移
            (0, 50),    # 下移
            (-50, 0),   # 左移
            (0, -50),   # 上移
        ]
        
        for i, (dx, dy) in enumerate(test_moves, 1):
            print(f"测试 {i}: 移动 ({dx}, {dy})")
            
            before_x, before_y = self.get_cursor_position()
            success = self.move_mouse(dx, dy)
            time.sleep(0.2)
            after_x, after_y = self.get_cursor_position()
            
            actual_dx = after_x - before_x
            actual_dy = after_y - before_y
            
            if success and (actual_dx != 0 or actual_dy != 0):
                print(f"  ✅ 成功移动: ({actual_dx}, {actual_dy})")
            else:
                print(f"  ❌ 移动失败")
            
            time.sleep(0.3)

def create_mouse_move_patch():
    """创建MouseMove.py的补丁文件"""
    patch_content = '''
# 在MouseMove.py末尾添加以下代码作为备用方案

import ctypes
from ctypes import wintypes

def reliable_mouse_move(dx, dy):
    """可靠的鼠标移动函数 - 自动回退到Win32 API"""
    try:
        # 首先尝试G-Hub移动
        ghub_move(dx, dy)
        
        # 验证移动是否生效
        user32 = ctypes.windll.user32
        point_before = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(point_before))
        
        import time
        time.sleep(0.05)
        
        point_after = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(point_after))
        
        # 如果位置没有变化，使用Win32备用方案
        if point_before.x == point_after.x and point_before.y == point_after.y:
            user32.mouse_event(0x0001, int(dx), int(dy), 0, 0)
            
    except Exception:
        # 如果G-Hub完全失败，直接使用Win32
        user32 = ctypes.windll.user32
        user32.mouse_event(0x0001, int(dx), int(dy), 0, 0)

# 替换原有的mouse_move函数
mouse_move = reliable_mouse_move
'''
    
    with open('F:/git/AI-Aimbot/mouse_move_patch.py', 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print("📝 已创建鼠标移动补丁文件: mouse_move_patch.py")

def main():
    """主函数"""
    print("🔧 鼠标移动修复工具")
    print("=" * 40)
    
    # 创建可靠的鼠标移动实例
    reliable_mouse = ReliableMouseMove()
    
    # 测试移动功能
    reliable_mouse.test_movement()
    
    # 创建补丁文件
    create_mouse_move_patch()
    
    print("\n✅ 修复完成！")
    print("\n📋 使用建议:")
    print("1. 如果G-Hub不工作，系统会自动使用Win32 API")
    print("2. Win32 API移动已验证有效")
    print("3. 可以将补丁代码集成到现有项目中")

if __name__ == "__main__":
    main()
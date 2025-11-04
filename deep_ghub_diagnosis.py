#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-Hub驱动深度诊断工具
专门用于检测G-Hub驱动为什么无法产生实际鼠标移动
适用于瓦洛兰特等反作弊游戏环境
"""

import sys
import os
import time
import ctypes
from ctypes import wintypes
import traceback

# 添加mouse_driver路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))

try:
    from mouse_driver.MouseMove import (
        ghub_move, ghub_click, mouse_open, 
        _mouse_move_internal, handle, found,
        MOUSE_IO, call_mouse, device_initialize
    )
    print("✅ 成功导入G-Hub驱动模块")
except ImportError as e:
    print(f"❌ 导入G-Hub驱动模块失败: {e}")
    sys.exit(1)

class GHubDiagnostic:
    def __init__(self):
        self.test_results = {}
        
    def print_separator(self, title):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def test_ghub_dll_status(self):
        """检测G-Hub驱动状态"""
        self.print_separator("G-Hub驱动状态检测")
        
        try:
            # 检查驱动函数是否可用
            print("检查G-Hub驱动函数:")
            
            if callable(mouse_open):
                print("✅ mouse_open函数可用")
            else:
                print("❌ mouse_open函数不可用")
                
            if callable(call_mouse):
                print("✅ call_mouse函数可用")
            else:
                print("❌ call_mouse函数不可用")
                
            if callable(device_initialize):
                print("✅ device_initialize函数可用")
            else:
                print("❌ device_initialize函数不可用")
                
            return True
            
        except Exception as e:
            print(f"❌ G-Hub驱动检测失败: {e}")
            return False
    
    def test_ghub_device_handle(self):
        """检测G-Hub设备句柄"""
        self.print_separator("G-Hub设备句柄检测")
        
        try:
            # 尝试打开设备
            result = mouse_open()
            print(f"mouse_open() 返回值: {result}")
            print(f"found 状态: {found}")
            
            if handle == 0:
                print("❌ G-Hub设备句柄为0")
                return False
            else:
                print(f"✅ G-Hub设备句柄: {handle}")
                print(f"设备句柄类型: {type(handle)}")
                print(f"设备句柄值: {handle}")
                return True
                
        except Exception as e:
            print(f"❌ G-Hub设备句柄检测失败: {e}")
            traceback.print_exc()
            return False
    
    def test_mouse_io_structure(self):
        """检测MOUSE_IO结构体"""
        self.print_separator("MOUSE_IO结构体检测")
        
        try:
            # 创建MOUSE_IO实例
            mouse_io = MOUSE_IO()
            print(f"✅ MOUSE_IO结构体创建成功")
            print(f"结构体大小: {ctypes.sizeof(mouse_io)} 字节")
            
            # 设置测试数据
            mouse_io.button = 0
            mouse_io.x = 10
            mouse_io.y = 10
            mouse_io.wheel = 0
            
            print(f"测试数据设置:")
            print(f"  button: {mouse_io.button}")
            print(f"  x: {mouse_io.x}")
            print(f"  y: {mouse_io.y}")
            print(f"  wheel: {mouse_io.wheel}")
            
            return True
            
        except Exception as e:
            print(f"❌ MOUSE_IO结构体检测失败: {e}")
            traceback.print_exc()
            return False
    
    def test_direct_call_mouse(self):
        """直接调用call_mouse函数测试"""
        self.print_separator("直接call_mouse调用测试")
        
        try:
            if handle == 0 or not found:
                print("❌ 设备未准备好")
                return False
            
            # 创建MOUSE_IO结构体
            mouse_io = MOUSE_IO()
            mouse_io.button = ctypes.c_char(b'\x00')  # 无按钮
            mouse_io.x = ctypes.c_char((50).to_bytes(1, 'little', signed=True))  # 移动50像素
            mouse_io.y = ctypes.c_char(b'\x00')  # Y轴不移动
            mouse_io.wheel = ctypes.c_char(b'\x00')  # 无滚轮
            mouse_io.unk1 = ctypes.c_char(b'\x00')
            
            print(f"准备直接调用call_mouse...")
            print(f"设备句柄: {handle}")
            print(f"移动参数: x=50, y=0")
            
            # 获取当前鼠标位置
            cursor_pos = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor_pos))
            print(f"调用前鼠标位置: ({cursor_pos.x}, {cursor_pos.y})")
            
            # 直接调用call_mouse
            result = call_mouse(mouse_io)
            print(f"call_mouse调用返回值: {result}")
            
            # 等待一下
            time.sleep(0.1)
            
            # 检查鼠标位置是否改变
            new_cursor_pos = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(new_cursor_pos))
            print(f"调用后鼠标位置: ({new_cursor_pos.x}, {new_cursor_pos.y})")
            
            if new_cursor_pos.x != cursor_pos.x or new_cursor_pos.y != cursor_pos.y:
                print("✅ 鼠标位置发生了变化！")
                return True
            else:
                print("❌ 鼠标位置没有变化")
                return False
                
        except Exception as e:
            print(f"❌ 直接call_mouse调用失败: {e}")
            traceback.print_exc()
            return False
    
    def test_internal_function_call(self):
        """测试_mouse_move_internal函数"""
        self.print_separator("_mouse_move_internal函数测试")
        
        try:
            # 获取当前鼠标位置
            cursor_pos = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor_pos))
            print(f"调用前鼠标位置: ({cursor_pos.x}, {cursor_pos.y})")
            
            # 调用内部函数
            print("调用 _mouse_move_internal(0, 30, 0, 0)...")
            result = _mouse_move_internal(0, 30, 0, 0)
            print(f"函数返回值: {result}")
            
            time.sleep(0.1)
            
            # 检查鼠标位置
            new_cursor_pos = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(new_cursor_pos))
            print(f"调用后鼠标位置: ({new_cursor_pos.x}, {new_cursor_pos.y})")
            
            if new_cursor_pos.x != cursor_pos.x or new_cursor_pos.y != cursor_pos.y:
                print("✅ _mouse_move_internal有效！")
                return True
            else:
                print("❌ _mouse_move_internal无效")
                return False
                
        except Exception as e:
            print(f"❌ _mouse_move_internal测试失败: {e}")
            traceback.print_exc()
            return False
    
    def test_ghub_move_function(self):
        """测试ghub_move函数"""
        self.print_separator("ghub_move函数测试")
        
        try:
            # 获取当前鼠标位置
            cursor_pos = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor_pos))
            print(f"调用前鼠标位置: ({cursor_pos.x}, {cursor_pos.y})")
            
            # 调用ghub_move
            print("调用 ghub_move(40, 0)...")
            result = ghub_move(40, 0)
            print(f"函数返回值: {result}")
            
            time.sleep(0.1)
            
            # 检查鼠标位置
            new_cursor_pos = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(new_cursor_pos))
            print(f"调用后鼠标位置: ({new_cursor_pos.x}, {new_cursor_pos.y})")
            
            if new_cursor_pos.x != cursor_pos.x or new_cursor_pos.y != cursor_pos.y:
                print("✅ ghub_move有效！")
                return True
            else:
                print("❌ ghub_move无效")
                return False
                
        except Exception as e:
            print(f"❌ ghub_move测试失败: {e}")
            traceback.print_exc()
            return False
    
    def test_system_environment(self):
        """检测系统环境"""
        self.print_separator("系统环境检测")
        
        try:
            # 检查管理员权限
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            print(f"管理员权限: {'是' if is_admin else '否'}")
            
            # 检查Python架构
            import platform
            print(f"Python架构: {platform.architecture()[0]}")
            print(f"系统架构: {platform.machine()}")
            
            # 检查G-Hub进程
            import subprocess
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq lghub.exe'], 
                                      capture_output=True, text=True)
                if 'lghub.exe' in result.stdout:
                    print("✅ G-Hub进程正在运行")
                else:
                    print("❌ G-Hub进程未运行")
            except:
                print("⚠️ 无法检查G-Hub进程")
            
            return True
            
        except Exception as e:
            print(f"❌ 系统环境检测失败: {e}")
            return False
    
    def run_comprehensive_diagnosis(self):
        """运行完整诊断"""
        print("🔍 G-Hub驱动深度诊断开始...")
        print("专门针对瓦洛兰特等反作弊游戏环境")
        
        tests = [
            ("系统环境", self.test_system_environment),
            ("G-Hub驱动状态", self.test_ghub_dll_status),
            ("G-Hub设备句柄", self.test_ghub_device_handle),
            ("MOUSE_IO结构体", self.test_mouse_io_structure),
            ("直接call_mouse调用", self.test_direct_call_mouse),
            ("_mouse_move_internal函数", self.test_internal_function_call),
            ("ghub_move函数", self.test_ghub_move_function),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
                results[test_name] = False
        
        # 总结报告
        self.print_separator("诊断总结报告")
        
        print("测试结果:")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        # 分析和建议
        print("\n🔧 问题分析和建议:")
        
        if not results.get("G-Hub驱动状态", False):
            print("• G-Hub驱动未正确加载，请检查G-Hub安装")
        
        if not results.get("G-Hub设备句柄", False):
            print("• G-Hub设备句柄无效，可能需要重启G-Hub或检查设备连接")
        
        if results.get("直接call_mouse调用", False):
            print("• 直接call_mouse调用有效，说明底层驱动工作正常")
        elif results.get("_mouse_move_internal函数", False):
            print("• 内部函数有效，但call_mouse调用无效，可能是参数问题")
        elif not results.get("ghub_move函数", False):
            print("• ghub_move函数无效，这是主要问题所在")
        
        # 特别针对瓦洛兰特的建议
        print("\n🎮 瓦洛兰特兼容性建议:")
        print("• G-Hub驱动是硬件级别的，理论上不会被反作弊检测")
        print("• 如果G-Hub驱动仍然无效，可能需要:")
        print("  - 更新G-Hub到最新版本")
        print("  - 重新安装罗技驱动")
        print("  - 检查游戏配置文件中的鼠标设置")
        print("  - 确保使用支持的罗技鼠标型号")
        
        return results

def main():
    """主函数"""
    print("G-Hub驱动深度诊断工具")
    print("=" * 60)
    
    diagnostic = GHubDiagnostic()
    results = diagnostic.run_comprehensive_diagnosis()
    
    # 等待用户确认
    print(f"\n{'='*60}")
    input("按Enter键退出...")

if __name__ == "__main__":
    main()
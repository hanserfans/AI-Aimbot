#!/usr/bin/env python3
"""
检查G-Hub驱动在蓝牙G304上的详细状态
专门为需要G-Hub驱动的游戏进行诊断
"""

import sys
import os
import time

# 添加mouse_driver目录到路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mouse_driver'))

def check_ghub_bluetooth_status():
    """检查G-Hub蓝牙状态"""
    print("🔵 G-Hub蓝牙驱动状态检查")
    print("=" * 50)
    
    try:
        # 导入MouseMove模块
        from MouseMove import mouse_open, mouse_close, ghub_move, found
        print("✅ MouseMove模块导入成功")
        
        # 检查设备连接状态
        print(f"📱 设备连接状态: {found}")
        
        if found:
            print("✅ G-Hub检测到设备连接")
            
            # 测试G-Hub移动功能
            print("\n🧪 测试G-Hub移动功能...")
            
            # 获取当前鼠标位置（使用Windows API）
            import ctypes
            from ctypes import wintypes
            
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            
            user32 = ctypes.windll.user32
            point = POINT()
            user32.GetCursorPos(ctypes.byref(point))
            original_pos = (point.x, point.y)
            print(f"📍 当前鼠标位置: {original_pos}")
            
            # 测试一系列G-Hub移动
            test_movements = [
                (1, 0, "微小向右移动"),
                (5, 0, "小幅向右移动"),
                (10, 0, "中等向右移动"),
                (0, 5, "小幅向下移动"),
                (-16, -5, "回到原点")
            ]
            
            ghub_working = False
            for dx, dy, description in test_movements:
                print(f"🔄 {description}: ghub_move({dx}, {dy})")
                
                # 记录移动前位置
                user32.GetCursorPos(ctypes.byref(point))
                before_pos = (point.x, point.y)
                
                # 执行G-Hub移动
                try:
                    ghub_move(dx, dy)
                    time.sleep(0.05)  # 等待移动完成
                    
                    # 检查移动后位置
                    user32.GetCursorPos(ctypes.byref(point))
                    after_pos = (point.x, point.y)
                    
                    if before_pos != after_pos:
                        print(f"   ✅ 移动成功: {before_pos} -> {after_pos}")
                        ghub_working = True
                    else:
                        print(f"   ⚠️  位置未变化: {before_pos}")
                        
                except Exception as e:
                    print(f"   ❌ 移动失败: {e}")
            
            # 总结G-Hub状态
            print(f"\n📊 G-Hub驱动状态总结:")
            print(f"   设备连接: ✅")
            print(f"   移动功能: {'✅ 正常' if ghub_working else '❌ 异常'}")
            
            if ghub_working:
                print(f"\n🎮 游戏兼容性: ✅ G-Hub驱动可用于游戏")
                return True
            else:
                print(f"\n🎮 游戏兼容性: ⚠️  G-Hub驱动可能无法在游戏中正常工作")
                return False
                
        else:
            print("❌ G-Hub未检测到设备连接")
            print("🔧 可能的原因:")
            print("   1. 蓝牙连接不稳定")
            print("   2. G-Hub软件未正确识别蓝牙设备")
            print("   3. 需要重新配对设备")
            return False
            
    except ImportError as e:
        print(f"❌ MouseMove模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 检查过程中出现错误: {e}")
        return False

def check_ghub_processes():
    """检查G-Hub相关进程"""
    print("\n🔍 检查G-Hub进程状态...")
    
    import subprocess
    try:
        # 检查G-Hub相关进程
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq LGHUB*'], 
                              capture_output=True, text=True, shell=True)
        
        if 'LGHUB' in result.stdout:
            print("✅ G-Hub进程正在运行")
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'LGHUB' in line:
                    print(f"   📱 {line}")
        else:
            print("⚠️  未检测到G-Hub进程")
            
    except Exception as e:
        print(f"❌ 进程检查失败: {e}")

def provide_bluetooth_recommendations():
    """提供蓝牙G304的建议"""
    print("\n💡 蓝牙G304 + G-Hub驱动建议:")
    print("=" * 50)
    print("1. 🔄 确保G-Hub软件是最新版本")
    print("2. 🔵 在G-Hub中检查设备是否被正确识别")
    print("3. ⚡ 蓝牙连接可能比USB稍有延迟，这是正常的")
    print("4. 🎮 某些游戏可能需要特定的G-Hub设置")
    print("5. 🔧 如果问题持续，可以尝试:")
    print("   - 重新配对蓝牙设备")
    print("   - 重启G-Hub软件")
    print("   - 使用USB接收器（如果可用）")

if __name__ == "__main__":
    print("🎯 专为游戏G-Hub驱动需求设计的蓝牙G304检查工具")
    print("=" * 60)
    
    # 检查G-Hub进程
    check_ghub_processes()
    
    # 检查G-Hub蓝牙状态
    ghub_status = check_ghub_bluetooth_status()
    
    # 提供建议
    provide_bluetooth_recommendations()
    
    # 最终结论
    print(f"\n🏁 最终结论:")
    if ghub_status:
        print("✅ 你的蓝牙G304可以与需要G-Hub驱动的游戏正常配合使用！")
    else:
        print("⚠️  蓝牙G304的G-Hub驱动可能需要进一步优化才能在游戏中使用")
        print("💡 建议尝试上述优化步骤，或考虑使用USB连接模式")
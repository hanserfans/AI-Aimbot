#!/usr/bin/env python3
"""
分析G-Hub鼠标控制的不同方式
比较直接调用方式与当前MouseMove.py实现的差异
"""

import sys
import os
import time
import ctypes
import subprocess
import psutil
import win32api

def check_admin_privileges():
    """检查管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_ghub_processes():
    """检查G-Hub相关进程"""
    ghub_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and 'lghub' in proc.info['name'].lower():
                ghub_processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return ghub_processes

def test_original_ginput():
    """测试原始g-input方式"""
    print("🔍 测试原始g-input方式")
    print("-" * 30)
    
    # 添加原始g-input路径
    original_ginput_path = os.path.join(os.path.dirname(__file__), 'mouse_driver', 'g-input-main', 'g-input-main')
    sys.path.insert(0, original_ginput_path)
    
    try:
        import mouse as GHUB
        print("✅ 成功导入原始g-input mouse模块")
        
        # 尝试初始化
        print("🔌 尝试初始化设备...")
        result = GHUB.mouse_open()
        
        print(f"初始化结果: {'✅ 成功' if result else '❌ 失败'}")
        print(f"设备状态: {'✅ 已找到' if GHUB.found else '❌ 未找到'}")
        print(f"设备句柄: {GHUB.handle}")
        
        return result, GHUB.found, GHUB.handle
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False, False, 0
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False, False, 0

def test_current_mousemove():
    """测试当前MouseMove.py实现"""
    print("\n🔍 测试当前MouseMove.py实现")
    print("-" * 30)
    
    # 添加mouse_driver路径
    mouse_driver_path = os.path.join(os.path.dirname(__file__), 'mouse_driver')
    sys.path.insert(0, mouse_driver_path)
    
    try:
        import MouseMove
        print("✅ 成功导入MouseMove模块")
        
        # 检查初始化状态
        print(f"设备状态: {'✅ 已找到' if MouseMove.found else '❌ 未找到'}")
        print(f"设备句柄: {MouseMove.handle}")
        
        # 尝试重新初始化
        print("🔌 尝试重新初始化设备...")
        result = MouseMove.mouse_open()
        
        print(f"重新初始化结果: {'✅ 成功' if result else '❌ 失败'}")
        print(f"更新后设备状态: {'✅ 已找到' if MouseMove.found else '❌ 未找到'}")
        print(f"更新后设备句柄: {MouseMove.handle}")
        
        return result, MouseMove.found, MouseMove.handle
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False, False, 0
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False, False, 0

def analyze_differences():
    """分析两种方式的差异"""
    print("\n📊 分析两种实现方式的差异")
    print("=" * 50)
    
    # 系统环境检查
    print("🖥️  系统环境:")
    print(f"  管理员权限: {'✅ 是' if check_admin_privileges() else '❌ 否'}")
    
    # G-Hub进程检查
    ghub_procs = check_ghub_processes()
    print(f"  G-Hub进程: {len(ghub_procs)} 个")
    for proc in ghub_procs:
        print(f"    - {proc['name']} (PID: {proc['pid']})")
    
    print()
    
    # 测试两种方式
    orig_result, orig_found, orig_handle = test_original_ginput()
    curr_result, curr_found, curr_handle = test_current_mousemove()
    
    # 比较结果
    print("\n📋 比较结果:")
    print("-" * 30)
    print(f"原始g-input:     初始化={'✅' if orig_result else '❌'}, 设备={'✅' if orig_found else '❌'}, 句柄={orig_handle}")
    print(f"当前MouseMove:   初始化={'✅' if curr_result else '❌'}, 设备={'✅' if curr_found else '❌'}, 句柄={curr_handle}")
    
    # 分析原因
    print("\n🔍 可能的问题原因:")
    if not check_admin_privileges():
        print("  ⚠️  缺少管理员权限 - 这可能是主要问题")
    
    if len(ghub_procs) == 0:
        print("  ⚠️  未检测到G-Hub进程 - G-Hub可能未运行")
    
    if not orig_result and not curr_result:
        print("  ⚠️  两种方式都失败 - 可能是系统级问题")
        print("     - 检查G-Hub是否正确安装")
        print("     - 检查是否有Logitech设备连接")
        print("     - 尝试以管理员身份运行")
    
    return orig_result or curr_result

def test_with_admin_suggestion():
    """建议以管理员身份测试"""
    if not check_admin_privileges():
        print("\n💡 建议解决方案:")
        print("1. 以管理员身份运行此脚本")
        print("2. 确保G-Hub软件正在运行")
        print("3. 确保有Logitech设备连接")
        print("\n🚀 尝试以管理员身份运行:")
        print("   Start-Process powershell -ArgumentList \"-Command\", \"cd 'f:\\\\git\\\\AI-Aimbot'; python analyze_ghub_approaches.py; Read-Host 'Press Enter to continue'\" -Verb RunAs")

if __name__ == "__main__":
    print("🎯 G-Hub鼠标控制方式分析")
    print("比较直接调用与当前实现的差异")
    print("=" * 50)
    
    success = analyze_differences()
    
    if not success:
        test_with_admin_suggestion()
    else:
        print("\n✅ 至少有一种方式工作正常！")
    
    print("\n🏁 分析完成")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-Hub虚拟设备重启工具
用于重启和重新初始化G-Hub虚拟鼠标设备
"""

import os
import sys
import time
import subprocess
import ctypes
from ctypes import wintypes

# 添加mouse_driver路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))

try:
    from MouseMove import initialize_mouse, close_mouse, ghub_move
    GHUB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  无法导入G-Hub模块: {e}")
    GHUB_AVAILABLE = False

def check_admin_privileges():
    """检查是否有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def restart_ghub_service():
    """重启G-Hub服务"""
    print("🔄 正在重启G-Hub服务...")
    
    services = [
        "LGHUBUpdaterService",
        "LGHUB",
        "LogiRegistryService"
    ]
    
    for service in services:
        try:
            # 停止服务
            print(f"  停止服务: {service}")
            result = subprocess.run(
                ["sc", "stop", service], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                print(f"    ✓ {service} 已停止")
            else:
                print(f"    ⚠️  {service} 停止失败或未运行")
            
            time.sleep(2)
            
            # 启动服务
            print(f"  启动服务: {service}")
            result = subprocess.run(
                ["sc", "start", service], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                print(f"    ✓ {service} 已启动")
            else:
                print(f"    ⚠️  {service} 启动失败")
                
        except subprocess.TimeoutExpired:
            print(f"    ⚠️  {service} 操作超时")
        except Exception as e:
            print(f"    ❌ {service} 操作失败: {e}")
    
    print("⏳ 等待服务稳定...")
    time.sleep(5)

def restart_ghub_processes():
    """重启G-Hub进程"""
    print("🔄 正在重启G-Hub进程...")
    
    processes = [
        "lghub.exe",
        "lghub_agent.exe",
        "lghub_updater.exe"
    ]
    
    for process in processes:
        try:
            # 结束进程
            print(f"  结束进程: {process}")
            result = subprocess.run(
                ["taskkill", "/f", "/im", process], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                print(f"    ✓ {process} 已结束")
            else:
                print(f"    ⚠️  {process} 未运行或结束失败")
                
        except subprocess.TimeoutExpired:
            print(f"    ⚠️  {process} 结束超时")
        except Exception as e:
            print(f"    ❌ {process} 结束失败: {e}")
    
    print("⏳ 等待进程清理...")
    time.sleep(3)
    
    # 重新启动G-Hub
    try:
        print("  启动G-Hub主程序...")
        ghub_paths = [
            r"C:\Program Files\LGHUB\lghub.exe",
            r"C:\Program Files (x86)\LGHUB\lghub.exe"
        ]
        
        for path in ghub_paths:
            if os.path.exists(path):
                subprocess.Popen([path], shell=False)
                print(f"    ✓ G-Hub已启动: {path}")
                break
        else:
            print("    ⚠️  未找到G-Hub安装路径")
            
    except Exception as e:
        print(f"    ❌ G-Hub启动失败: {e}")

def reinitialize_device():
    """重新初始化设备"""
    print("🔄 正在重新初始化G-Hub设备...")
    
    if not GHUB_AVAILABLE:
        print("❌ G-Hub模块不可用，无法重新初始化设备")
        return False
    
    try:
        # 关闭现有连接
        print("  关闭现有设备连接...")
        close_mouse()
        time.sleep(1)
        
        # 重新初始化
        print("  重新初始化设备...")
        success = initialize_mouse()
        
        if success:
            print("  ✓ 设备重新初始化成功")
            
            # 测试设备功能
            print("  测试设备功能...")
            test_result = ghub_move(5, 5)
            if test_result:
                print("  ✓ 设备功能测试通过")
                return True
            else:
                print("  ⚠️  设备功能测试失败")
                return False
        else:
            print("  ❌ 设备重新初始化失败")
            return False
            
    except Exception as e:
        print(f"  ❌ 设备重新初始化异常: {e}")
        return False

def full_restart():
    """完整重启流程"""
    print("=" * 50)
    print("🚀 G-Hub虚拟设备完整重启流程")
    print("=" * 50)
    
    # 检查管理员权限
    if not check_admin_privileges():
        print("⚠️  建议以管理员权限运行以获得最佳效果")
        print("   某些操作可能需要管理员权限")
    
    # 步骤1: 重新初始化设备
    print("\n📍 步骤1: 重新初始化设备")
    device_success = reinitialize_device()
    
    if device_success:
        print("✅ 设备重新初始化成功，无需重启服务")
        return True
    
    # 步骤2: 重启进程
    print("\n📍 步骤2: 重启G-Hub进程")
    restart_ghub_processes()
    
    # 等待进程启动
    print("⏳ 等待G-Hub进程启动...")
    time.sleep(10)
    
    # 步骤3: 重新测试设备
    print("\n📍 步骤3: 重新测试设备")
    device_success = reinitialize_device()
    
    if device_success:
        print("✅ 进程重启后设备工作正常")
        return True
    
    # 步骤4: 重启服务
    print("\n📍 步骤4: 重启G-Hub服务")
    restart_ghub_service()
    
    # 等待服务启动
    print("⏳ 等待G-Hub服务启动...")
    time.sleep(15)
    
    # 步骤5: 最终测试
    print("\n📍 步骤5: 最终设备测试")
    device_success = reinitialize_device()
    
    if device_success:
        print("✅ 服务重启后设备工作正常")
        return True
    else:
        print("❌ 完整重启后设备仍然无法工作")
        print("💡 建议:")
        print("   1. 检查G-Hub是否正确安装")
        print("   2. 重启计算机")
        print("   3. 重新安装G-Hub软件")
        return False

def quick_restart():
    """快速重启（仅重新初始化设备）"""
    print("=" * 50)
    print("⚡ G-Hub设备快速重启")
    print("=" * 50)
    
    return reinitialize_device()

def main():
    """主函数"""
    print("G-Hub虚拟设备重启工具")
    print("选择重启模式:")
    print("1. 快速重启 (仅重新初始化设备)")
    print("2. 完整重启 (重启进程和服务)")
    print("3. 退出")
    
    while True:
        try:
            choice = input("\n请选择 (1-3): ").strip()
            
            if choice == "1":
                success = quick_restart()
                break
            elif choice == "2":
                success = full_restart()
                break
            elif choice == "3":
                print("退出程序")
                return
            else:
                print("无效选择，请输入1-3")
                continue
                
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            return
        except Exception as e:
            print(f"输入错误: {e}")
            continue
    
    # 显示结果
    print("\n" + "=" * 50)
    if success:
        print("🎉 设备重启成功！")
        print("💡 现在可以正常使用G-Hub鼠标功能")
    else:
        print("❌ 设备重启失败")
        print("💡 请尝试完整重启或检查G-Hub安装")
    print("=" * 50)

if __name__ == "__main__":
    main()
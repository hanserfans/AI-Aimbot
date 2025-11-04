#!/usr/bin/env python3
"""
键盘输入问题修复工具
解决进入游戏后无法按Enter键的问题
"""

import psutil
import subprocess
import sys
import time

def find_python_processes():
    """查找所有Python进程"""
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                python_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': cmdline
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return python_processes

def find_keyboard_blocking_processes():
    """查找可能阻塞键盘输入的进程"""
    blocking_processes = []
    python_procs = find_python_processes()
    
    # 检查可能阻塞键盘的脚本
    blocking_keywords = [
        'yolov8_live_overlay',
        'pynput',
        'keyboard',
        'hook',
        'listener'
    ]
    
    for proc in python_procs:
        cmdline_lower = proc['cmdline'].lower()
        for keyword in blocking_keywords:
            if keyword in cmdline_lower:
                blocking_processes.append(proc)
                break
    
    return blocking_processes

def kill_process(pid):
    """终止指定进程"""
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=3)
        return True
    except (psutil.NoSuchProcess, psutil.TimeoutExpired, psutil.AccessDenied):
        try:
            proc.kill()
            return True
        except:
            return False

def main():
    print("🔍 键盘输入问题诊断工具")
    print("=" * 50)
    
    # 1. 查找所有Python进程
    print("\n📋 当前运行的Python进程:")
    python_procs = find_python_processes()
    
    if not python_procs:
        print("✅ 没有发现Python进程")
        return
    
    for i, proc in enumerate(python_procs, 1):
        print(f"{i}. PID: {proc['pid']}, 名称: {proc['name']}")
        if proc['cmdline']:
            print(f"   命令行: {proc['cmdline'][:100]}...")
    
    # 2. 查找可能阻塞键盘的进程
    print("\n🚫 可能阻塞键盘输入的进程:")
    blocking_procs = find_keyboard_blocking_processes()
    
    if not blocking_procs:
        print("✅ 没有发现阻塞键盘输入的进程")
        
        # 检查是否有其他Python进程
        if python_procs:
            print("\n⚠️  但发现其他Python进程，可能也会影响键盘输入")
            choice = input("\n是否要终止所有Python进程? (y/n): ").lower()
            if choice == 'y':
                print("\n🔄 正在终止所有Python进程...")
                for proc in python_procs:
                    if kill_process(proc['pid']):
                        print(f"✅ 已终止进程 PID: {proc['pid']}")
                    else:
                        print(f"❌ 无法终止进程 PID: {proc['pid']}")
        return
    
    for proc in blocking_procs:
        print(f"⚠️  PID: {proc['pid']}, 命令: {proc['cmdline'][:80]}...")
    
    # 3. 询问是否终止阻塞进程
    choice = input(f"\n发现 {len(blocking_procs)} 个可能阻塞键盘的进程，是否终止? (y/n): ").lower()
    
    if choice == 'y':
        print("\n🔄 正在终止阻塞进程...")
        for proc in blocking_procs:
            if kill_process(proc['pid']):
                print(f"✅ 已终止进程 PID: {proc['pid']}")
            else:
                print(f"❌ 无法终止进程 PID: {proc['pid']}")
        
        print("\n⏳ 等待3秒让系统稳定...")
        time.sleep(3)
        
        print("✅ 键盘输入问题应该已解决!")
        print("💡 现在可以尝试在游戏中按Enter键")
    
    # 4. 提供预防建议
    print("\n📝 预防建议:")
    print("1. 运行AI-Aimbot前，确保没有其他Python脚本在运行")
    print("2. 避免同时运行多个包含键盘监听的脚本")
    print("3. 使用完毕后及时关闭程序")
    print("4. 如果问题持续，重启计算机可以彻底解决")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("请尝试手动终止Python进程或重启计算机")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安静模式的G-Hub测试 - 不显示调试信息
"""

import sys
import os

# 添加mouse_driver路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'mouse_driver'))

def quiet_test():
    """安静模式测试G-Hub设备"""
    try:
        # 临时重定向stderr来隐藏调试信息
        import io
        import contextlib
        
        # 捕获stderr输出
        stderr_capture = io.StringIO()
        
        with contextlib.redirect_stderr(stderr_capture):
            from MouseMove import initialize_mouse, ghub_move, close_mouse
            
            print("🔍 正在初始化G-Hub设备...")
            success = initialize_mouse()
            
            if success:
                print("✅ G-Hub设备初始化成功")
                
                # 测试移动
                print("🎯 测试鼠标移动...")
                move_result = ghub_move(5, 5)
                
                if move_result:
                    print("✅ 鼠标移动测试成功")
                else:
                    print("⚠️  鼠标移动测试失败")
                
                # 关闭设备
                close_mouse()
                print("🔒 设备已关闭")
                
                return True
            else:
                print("❌ G-Hub设备初始化失败")
                return False
                
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False

def verbose_test():
    """详细模式测试G-Hub设备"""
    try:
        from MouseMove import initialize_mouse, ghub_move, close_mouse
        
        print("🔍 正在初始化G-Hub设备（详细模式）...")
        success = initialize_mouse()
        
        if success:
            print("✅ G-Hub设备初始化成功")
            
            # 测试移动
            print("🎯 测试鼠标移动...")
            move_result = ghub_move(5, 5)
            
            if move_result:
                print("✅ 鼠标移动测试成功")
            else:
                print("⚠️  鼠标移动测试失败")
            
            # 关闭设备
            close_mouse()
            print("🔒 设备已关闭")
            
            return True
        else:
            print("❌ G-Hub设备初始化失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False

def main():
    """主函数"""
    print("G-Hub设备测试工具")
    print("选择测试模式:")
    print("1. 安静模式 (隐藏调试信息)")
    print("2. 详细模式 (显示所有信息)")
    print("3. 退出")
    
    while True:
        try:
            choice = input("\n请选择 (1-3): ").strip()
            
            if choice == "1":
                print("\n" + "="*40)
                print("🔇 安静模式测试")
                print("="*40)
                success = quiet_test()
                break
            elif choice == "2":
                print("\n" + "="*40)
                print("🔊 详细模式测试")
                print("="*40)
                success = verbose_test()
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
    print("\n" + "="*40)
    if success:
        print("🎉 G-Hub设备工作正常！")
    else:
        print("❌ G-Hub设备测试失败")
    print("="*40)

if __name__ == "__main__":
    main()
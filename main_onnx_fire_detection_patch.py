#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序开火检测集成补丁
将独立开火检测系统集成到 main_onnx.py 中
"""

import os
import re
import shutil
from datetime import datetime


def create_backup(file_path):
    """创建文件备份"""
    timestamp = int(datetime.now().timestamp())
    backup_path = f"{file_path}_backup_{timestamp}.py"
    shutil.copy2(file_path, backup_path)
    print(f"[BACKUP] 已创建备份文件: {backup_path}")
    return backup_path


def apply_fire_detection_integration_patch():
    """应用开火检测集成补丁"""
    main_file = "f:\\git\\AI-Aimbot\\main_onnx.py"
    
    if not os.path.exists(main_file):
        print(f"[ERROR] 主程序文件不存在: {main_file}")
        return False
    
    # 创建备份
    backup_file = create_backup(main_file)
    
    try:
        # 读取原文件内容
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. 添加独立开火检测系统的导入
        import_section = '''
# 独立开火检测系统导入
try:
    from fire_detection_integration import (
        initialize_fire_integration,
        get_fire_integration,
        update_fire_detection_frame,
        get_fire_detection_stats,
        print_fire_detection_stats
    )
    INDEPENDENT_FIRE_DETECTION_AVAILABLE = True
    print("[INFO] ✅ 独立开火检测系统已加载到主程序")
except ImportError as e:
    print(f"[WARNING] 独立开火检测系统加载失败: {e}")
    INDEPENDENT_FIRE_DETECTION_AVAILABLE = False
'''
        
        # 在智能自适应移动系统导入后添加
        adaptive_import_pattern = r'(ADAPTIVE_MOVEMENT_AVAILABLE = True.*?print\("\[WARNING\] 智能自适应移动系统不可用"\))'
        if re.search(adaptive_import_pattern, content, re.DOTALL):
            content = re.sub(
                adaptive_import_pattern,
                r'\1' + import_section,
                content,
                flags=re.DOTALL
            )
            print("[PATCH] ✅ 已添加独立开火检测系统导入")
        else:
            print("[WARNING] 未找到智能自适应移动系统导入位置，在文件开头添加导入")
            content = import_section + content
        
        # 2. 在main函数中初始化独立开火检测系统
        main_init_code = '''
    # 🔥 初始化独立开火检测系统
    global fire_integration_system
    fire_integration_system = None
    if INDEPENDENT_FIRE_DETECTION_AVAILABLE:
        try:
            # 创建一个简单的主程序实例包装器
            class MainProgramWrapper:
                def auto_fire(self):
                    return auto_fire()
                
                def auto_fire_fast(self):
                    return auto_fire_fast()
            
            main_wrapper = MainProgramWrapper()
            fire_integration_system = initialize_fire_integration(main_wrapper)
            print("[FIRE_DETECTION] 🔥 独立开火检测系统已集成到主程序")
        except Exception as e:
            print(f"[FIRE_DETECTION] ❌ 独立开火检测系统初始化失败: {e}")
            fire_integration_system = None
    else:
        print("[FIRE_DETECTION] ⚠️ 独立开火检测系统不可用")
'''
        
        # 在自适应移动系统初始化后添加
        adaptive_init_pattern = r'(else:\s+print\("\[ADAPTIVE_MOVE\] ⚠️ 自适应移动系统不可用"\))'
        if re.search(adaptive_init_pattern, content):
            content = re.sub(
                adaptive_init_pattern,
                r'\1' + main_init_code,
                content
            )
            print("[PATCH] ✅ 已添加独立开火检测系统初始化代码")
        else:
            print("[WARNING] 未找到自适应移动系统初始化位置")
        
        # 3. 修改主循环，添加帧数据更新
        frame_update_code = '''
                # 🔥 更新独立开火检测系统的帧数据
                if INDEPENDENT_FIRE_DETECTION_AVAILABLE and fire_integration_system:
                    try:
                        # 构建检测结果字典
                        detection_results = {
                            'head_x': head_x_320 if 'head_x_320' in locals() else None,
                            'head_y': head_y_320 if 'head_y_320' in locals() else None,
                            'x': head_x_320 if 'head_x_320' in locals() else None,
                            'y': head_y_320 if 'head_y_320' in locals() else None,
                            'targets': targets_df.to_dict('records') if 'targets_df' in locals() and not targets_df.empty else [],
                            'locked_target': locked_target if 'locked_target' in locals() else None,
                            'frame_id': int(time.time() * 1000)
                        }
                        
                        # 更新到独立开火检测系统
                        fire_integration_system.update_frame_data(
                            detection_results, 
                            crosshair_x=crosshair_x_320, 
                            crosshair_y=crosshair_y_320
                        )
                    except Exception as e:
                        # 静默处理异常，避免影响主循环
                        pass
'''
        
        # 在主循环的检测结果处理后添加
        # 寻找合适的位置插入帧更新代码
        main_loop_pattern = r'(# 检测结果处理.*?)(# 显示实时画面|# 性能监控|# FPS控制|time\.sleep)'
        if re.search(main_loop_pattern, content, re.DOTALL):
            content = re.sub(
                main_loop_pattern,
                r'\1' + frame_update_code + r'\n                \2',
                content,
                flags=re.DOTALL
            )
            print("[PATCH] ✅ 已添加帧数据更新代码到主循环")
        else:
            print("[WARNING] 未找到合适的主循环位置添加帧更新代码")
        
        # 4. 添加统计信息显示（在R键处理中）
        stats_code = '''
                    # 显示独立开火检测系统统计信息
                    if INDEPENDENT_FIRE_DETECTION_AVAILABLE and fire_integration_system:
                        try:
                            print("\\n" + "="*50)
                            print("🔥 独立开火检测系统状态")
                            print("="*50)
                            stats = fire_integration_system.get_stats()
                            print(f"📊 处理帧数: {stats.get('total_frames_processed', 0)}")
                            print(f"🎯 检测到开火机会: {stats.get('fire_opportunities_detected', 0)}")
                            print(f"✅ 成功开火次数: {stats.get('successful_fires', 0)}")
                            print(f"📈 检测FPS: {stats.get('detection_fps', 0):.1f}")
                            print(f"⏱️  平均检测延迟: {stats.get('avg_detection_latency', 0)*1000:.2f}ms")
                            if stats.get('fire_opportunities_detected', 0) > 0:
                                success_rate = (stats.get('successful_fires', 0) / stats.get('fire_opportunities_detected', 1)) * 100
                                print(f"🎯 开火成功率: {success_rate:.1f}%")
                            print("="*50)
                        except Exception as e:
                            print(f"[FIRE_DETECTION] 统计信息显示异常: {e}")
'''
        
        # 在R键处理的扳机系统状态显示后添加
        r_key_pattern = r'(print\("="\\*50\\).*?trigger_system\.print_status\(\).*?print\("="\\*50\\))'
        if re.search(r_key_pattern, content, re.DOTALL):
            content = re.sub(
                r_key_pattern,
                r'\1' + stats_code,
                content,
                flags=re.DOTALL
            )
            print("[PATCH] ✅ 已添加独立开火检测系统统计信息显示")
        else:
            print("[WARNING] 未找到R键处理位置添加统计信息")
        
        # 5. 移除或注释掉原有的开火检测逻辑（可选）
        # 这里我们保留原有逻辑，让两个系统并行运行进行对比
        
        # 6. 添加清理代码
        cleanup_code = '''
    # 🔥 清理独立开火检测系统
    if INDEPENDENT_FIRE_DETECTION_AVAILABLE and fire_integration_system:
        try:
            fire_integration_system.stop()
            print("[FIRE_DETECTION] 🛑 独立开火检测系统已停止")
        except Exception as e:
            print(f"[FIRE_DETECTION] 清理异常: {e}")
'''
        
        # 在main函数结束前添加清理代码
        main_end_pattern = r'(except KeyboardInterrupt:.*?print\("程序已退出"\\))'
        if re.search(main_end_pattern, content, re.DOTALL):
            content = re.sub(
                main_end_pattern,
                cleanup_code + r'\n    \1',
                content,
                flags=re.DOTALL
            )
            print("[PATCH] ✅ 已添加清理代码")
        else:
            print("[WARNING] 未找到合适位置添加清理代码")
        
        # 写入修改后的内容
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[SUCCESS] ✅ 独立开火检测系统集成补丁已应用到 {main_file}")
        print(f"[BACKUP] 📁 原文件备份: {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 补丁应用失败: {e}")
        # 恢复备份
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, main_file)
            print(f"[RESTORE] 已从备份恢复原文件")
        return False


def verify_integration():
    """验证集成是否成功"""
    main_file = "f:\\git\\AI-Aimbot\\main_onnx.py"
    
    if not os.path.exists(main_file):
        print(f"[ERROR] 主程序文件不存在: {main_file}")
        return False
    
    try:
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("独立开火检测系统导入", "from fire_detection_integration import"),
            ("系统初始化", "initialize_fire_integration"),
            ("帧数据更新", "fire_integration_system.update_frame_data"),
            ("统计信息显示", "独立开火检测系统状态"),
            ("清理代码", "fire_integration_system.stop")
        ]
        
        print("\n" + "="*50)
        print("🔍 独立开火检测系统集成验证")
        print("="*50)
        
        all_passed = True
        for check_name, check_pattern in checks:
            if check_pattern in content:
                print(f"✅ {check_name}: 通过")
            else:
                print(f"❌ {check_name}: 失败")
                all_passed = False
        
        print("="*50)
        if all_passed:
            print("🎉 所有检查通过！独立开火检测系统已成功集成")
        else:
            print("⚠️ 部分检查失败，请检查集成是否完整")
        
        return all_passed
        
    except Exception as e:
        print(f"[ERROR] 验证过程异常: {e}")
        return False


def show_integration_summary():
    """显示集成摘要"""
    print("\n" + "="*60)
    print("🔥 独立开火检测系统集成摘要")
    print("="*60)
    print("📋 集成内容:")
    print("   1. ✅ 导入独立开火检测系统模块")
    print("   2. ✅ 在main函数中初始化系统")
    print("   3. ✅ 在主循环中更新帧数据")
    print("   4. ✅ 在R键处理中显示统计信息")
    print("   5. ✅ 添加系统清理代码")
    print()
    print("🎯 系统特性:")
    print("   • 🔄 独立检测循环 - 300Hz高频检测")
    print("   • 📊 实时统计信息 - 检测FPS、成功率等")
    print("   • 🎮 与原系统并行 - 可对比性能差异")
    print("   • 🔧 可配置参数 - 对齐阈值、冷却时间等")
    print("   • 🛡️ 异常处理 - 不影响主程序稳定性")
    print()
    print("⌨️  使用方法:")
    print("   • 鼠标右键 - 激活瞄准和开火（两个系统都会工作）")
    print("   • Caps Lock - 纯开火模式（两个系统都会工作）")
    print("   • R键 - 显示包含独立系统的详细统计信息")
    print()
    print("📈 预期效果:")
    print("   • 更快的开火响应 - 独立循环减少延迟")
    print("   • 更准确的对齐检测 - 使用最新帧数据")
    print("   • 更好的性能监控 - 详细的统计信息")
    print("="*60)


if __name__ == "__main__":
    print("🔥 独立开火检测系统集成工具")
    print("="*50)
    
    # 检查依赖文件
    required_files = [
        "f:\\git\\AI-Aimbot\\independent_fire_detection_system.py",
        "f:\\git\\AI-Aimbot\\fire_detection_integration.py",
        "f:\\git\\AI-Aimbot\\main_onnx.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少必要文件:")
        for file_path in missing_files:
            print(f"   • {file_path}")
        print("\n请确保所有文件都存在后再运行此工具。")
        exit(1)
    
    print("✅ 所有必要文件都存在")
    
    # 应用补丁
    print("\n🔧 开始应用集成补丁...")
    if apply_fire_detection_integration_patch():
        print("\n🔍 验证集成结果...")
        if verify_integration():
            show_integration_summary()
            print("\n🎉 独立开火检测系统集成完成！")
            print("💡 现在可以运行 main_onnx.py 来测试新的开火检测系统")
        else:
            print("\n⚠️ 集成验证失败，请检查日志信息")
    else:
        print("\n❌ 集成补丁应用失败")
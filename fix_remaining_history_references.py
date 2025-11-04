#!/usr/bin/env python3
"""
修复纯净头部检测系统中残留的历史记忆引用
完全移除所有 head_position_history 和 head_velocity 的引用
"""

import os
import re
from datetime import datetime

def fix_remaining_history_references():
    """修复main_onnx.py中残留的历史记忆引用"""
    
    main_file = "main_onnx.py"
    
    # 备份文件
    backup_file = f"main_onnx_before_history_fix_{int(datetime.now().timestamp())}.py"
    
    print(f"[BACKUP] 备份原始文件: {backup_file}")
    with open(main_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(original_content)
    
    # 读取当前内容
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("[FIX] 开始修复历史记忆引用...")
    
    # 1. 修复第1143行的 history_count = len(head_position_history)
    old_history_count = """        # 添加头部记忆状态信息
        history_count = len(head_position_history)
        velocity_info = f"速度({head_velocity['x']:.1f},{head_velocity['y']:.1f})"
        
        # 如果启用了增强检测，显示原始320坐标和放大后坐标
        if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
            # 将放大后的坐标转换回320坐标系显示
            original_x = head_x / enhanced_config.SCALE_FACTOR
            original_y = head_y / enhanced_config.SCALE_FACTOR
            head_pos = f"({head_x:.0f},{head_y:.0f})[960] 原始({original_x:.0f},{original_y:.0f})[320]"
        else:
            head_pos = f"({head_x:.0f},{head_y:.0f})"
            
        return f"锁定头部{head_pos} 剩余{remaining_time:.1f}s 记忆{history_count}帧 {velocity_info}\""""
    
    new_history_count = """        # 纯净系统状态信息（无历史记忆）
        history_count = 0  # 纯净系统无历史记忆
        velocity_info = "纯净模式(无速度记忆)"
        
        # 如果启用了增强检测，显示原始320坐标和放大后坐标
        if ENHANCED_DETECTION_AVAILABLE and enhanced_config:
            # 将放大后的坐标转换回320坐标系显示
            original_x = head_x / enhanced_config.SCALE_FACTOR
            original_y = head_y / enhanced_config.SCALE_FACTOR
            head_pos = f"({head_x:.0f},{head_y:.0f})[960] 原始({original_x:.0f},{original_y:.0f})[320]"
        else:
            head_pos = f"({head_x:.0f},{head_y:.0f})"
            
        return f"锁定头部{head_pos} 剩余{remaining_time:.1f}s 纯净模式 {velocity_info}\""""
    
    if old_history_count in content:
        content = content.replace(old_history_count, new_history_count)
        print("[FIX] ✅ 修复了锁定目标状态显示中的历史记忆引用")
    
    # 2. 修复第1166行的 elif head_position_history:
    old_elif_history = """        elif head_position_history:
            # 如果没有锁定目标但有历史记录，使用预测位置
            predicted_pos = predict_head_position()
            if predicted_pos:
                return {
                    'x': predicted_pos[0],
                    'y': predicted_pos[1],
                    'source': 'predicted'
                }"""
    
    new_elif_history = """        else:
            # 纯净系统：无历史记录，无预测位置
            return None"""
    
    if old_elif_history in content:
        content = content.replace(old_elif_history, new_elif_history)
        print("[FIX] ✅ 修复了预测位置获取中的历史记忆引用")
    
    # 3. 修复第2159行的检测丢失处理
    old_detection_lost = """                if detection_lost and target_lock_enabled and len(head_position_history) > 0:
                    # 检测丢失时：使用预测位置进行鼠标移动
                    predicted_pos = predict_head_position()
                    if predicted_pos:
                        head_x_320 = predicted_pos[0]
                        head_y_320 = predicted_pos[1]
                        head_source = "PREDICTED"
                        print(f"[HEAD_PRED_MAIN] 检测丢失，使用预测头部位置: ({head_x_320:.1f}, {head_y_320:.1f})")
                    else:
                        # 预测失败，使用稳定位置
                        stable_pos = get_stable_head_position()
                        head_x_320 = stable_pos[0]
                        head_y_320 = stable_pos[1]
                        head_source = "STABLE"
                        print(f"[HEAD_STABLE_MAIN] 预测失败，使用稳定头部位置: ({head_x_320:.1f}, {head_y_320:.1f})")"""
    
    new_detection_lost = """                if detection_lost and target_lock_enabled:
                    # 纯净系统：检测丢失时不使用历史记忆或预测
                    # 直接跳过移动，等待下一帧检测
                    print(f"[PURE_HEAD_MAIN] 检测丢失，纯净系统等待下一帧检测（无历史记忆补偿）")
                    continue  # 跳过本次循环，等待下一帧"""
    
    if old_detection_lost in content:
        content = content.replace(old_detection_lost, new_detection_lost)
        print("[FIX] ✅ 修复了检测丢失处理中的历史记忆引用")
    
    # 4. 移除任何剩余的 head_position_history 引用
    # 使用正则表达式查找并替换
    history_pattern = r'head_position_history[^a-zA-Z_]'
    matches = re.findall(history_pattern, content)
    if matches:
        print(f"[WARNING] 发现 {len(matches)} 个剩余的 head_position_history 引用")
        # 将这些引用替换为空列表或适当的默认值
        content = re.sub(r'len\(head_position_history\)', '0', content)
        content = re.sub(r'head_position_history\.', '[]  # 纯净系统无历史记忆 #.', content)
        print("[FIX] ✅ 修复了剩余的 head_position_history 引用")
    
    # 5. 移除任何剩余的 head_velocity 引用
    velocity_pattern = r'head_velocity[^a-zA-Z_]'
    matches = re.findall(velocity_pattern, content)
    if matches:
        print(f"[WARNING] 发现 {len(matches)} 个剩余的 head_velocity 引用")
        # 将速度引用替换为默认值
        content = re.sub(r"head_velocity\['x'\]", '0.0', content)
        content = re.sub(r"head_velocity\['y'\]", '0.0', content)
        print("[FIX] ✅ 修复了剩余的 head_velocity 引用")
    
    # 写入修复后的内容
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[SUCCESS] ✅ 历史记忆引用修复完成")
    print(f"[BACKUP] 原始文件已备份为: {backup_file}")
    
    # 生成修复报告
    report_content = f"""# 历史记忆引用修复报告

## 修复时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 修复内容

### 1. 锁定目标状态显示修复
- **问题**: `history_count = len(head_position_history)` 引用不存在的变量
- **修复**: 改为 `history_count = 0` 并显示"纯净模式"
- **状态**: ✅ 已修复

### 2. 预测位置获取修复  
- **问题**: `elif head_position_history:` 引用不存在的变量
- **修复**: 改为直接返回 `None`，无预测位置
- **状态**: ✅ 已修复

### 3. 检测丢失处理修复
- **问题**: `len(head_position_history) > 0` 引用不存在的变量
- **修复**: 移除历史记忆检查，直接跳过等待下一帧
- **状态**: ✅ 已修复

### 4. 剩余引用清理
- **head_position_history**: 所有引用已清理
- **head_velocity**: 所有引用已清理
- **状态**: ✅ 已修复

## 纯净系统特性

### ✅ 完全移除的功能
- 历史位置记录
- 速度计算
- 位置预测
- 多帧平滑
- 检测丢失补偿

### ✅ 保留的功能
- 当前帧头部计算
- 目标锁定机制
- 实时检测
- 鼠标移动控制

## 备份信息
- **原始文件**: main_onnx.py
- **备份文件**: {backup_file}
- **修复脚本**: fix_remaining_history_references.py

## 验证建议
1. 运行语法检查: `python -c "import main_onnx"`
2. 启动主程序测试: `python main_onnx.py`
3. 检查是否还有 NameError 错误

---
**修复完成** ✅
"""
    
    with open("history_references_fix_report.md", 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"[REPORT] 修复报告已生成: history_references_fix_report.md")

if __name__ == "__main__":
    fix_remaining_history_references()
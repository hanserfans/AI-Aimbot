#!/usr/bin/env python3
"""
鼠标移动问题修复方案

问题分析：
1. ✅ 基础坐标计算逻辑正确（coordinate_system.py）
2. ✅ G-Hub驱动工作正常
3. ❌ 动态跟踪系统中的移动计算有问题

问题根源：
- 在dynamic_tracking_system.py中，_static_aim方法直接使用像素偏移乘以movement_amp
- 这没有考虑游戏FOV、屏幕分辨率等因素
- 应该使用统一的坐标系统进行计算

修复方案：
1. 修改动态跟踪系统，使用coordinate_system进行计算
2. 确保移动方向正确
3. 添加调试信息验证修复效果
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from coordinate_system import CoordinateSystem

def create_fixed_dynamic_tracking():
    """创建修复后的动态跟踪系统代码"""
    
    fixed_code = '''
    def _static_aim(self, target_x: float, target_y: float, crosshair_x: float, crosshair_y: float):
        """传统静态瞄准，返回移动值 - 修复版本"""
        
        # 使用统一坐标系统计算移动
        from coordinate_system import CoordinateSystem
        
        # 初始化坐标系统（使用与main_onnx.py相同的参数）
        coord_system = CoordinateSystem(
            detection_size=320,
            game_width=2560,  # 或使用实际游戏窗口宽度
            game_height=1600, # 或使用实际游戏窗口高度
            game_fov=103.0
        )
        
        # 计算目标到准星的偏移信息
        offset_info = coord_system.calculate_crosshair_to_target_offset(target_x, target_y)
        
        # 使用角度偏移计算鼠标移动 - 精确版本
        move_x, move_y = coord_system.calculate_mouse_movement(
            offset_info['angle']['h'], 
            offset_info['angle']['v'],
            distance_factor=1.0,  # 可以根据需要调整
            base_sensitivity=24.85  # 使用精确的转换系数
        )
        
        print(f"[STATIC-FIXED] 目标: ({target_x:.1f}, {target_y:.1f}), 准星: ({crosshair_x:.1f}, {crosshair_y:.1f})")
        print(f"[STATIC-FIXED] 角度偏移: H={offset_info['angle']['h']:.3f}°, V={offset_info['angle']['v']:.3f}°")
        print(f"[STATIC-FIXED] 计算移动: ({move_x}, {move_y})")
        
        return (int(move_x), int(move_y))
    
    def _predictive_aim(self, target_x: float, target_y: float, crosshair_x: float, crosshair_y: float, confidence: float):
        """预测性瞄准，返回移动值 - 修复版本"""
        
        # 添加目标位置到预测器
        self.tracker.predictor.add_position(target_x, target_y)
        
        # 预测移动延迟后的目标位置
        movement_delay = 0.1  # 估算的移动延迟
        predicted_pos = self.tracker.predictor.predict_position(time.time() + movement_delay)
        
        # 使用统一坐标系统计算移动
        from coordinate_system import CoordinateSystem
        
        coord_system = CoordinateSystem(
            detection_size=320,
            game_width=2560,
            game_height=1600,
            game_fov=103.0
        )
        
        # 计算预测位置到准星的偏移信息
        offset_info = coord_system.calculate_crosshair_to_target_offset(predicted_pos[0], predicted_pos[1])
        
        # 使用角度偏移计算鼠标移动 - 精确版本
        move_x, move_y = coord_system.calculate_mouse_movement(
            offset_info['angle']['h'], 
            offset_info['angle']['v'],
            distance_factor=1.0,
            base_sensitivity=24.85  # 使用精确的转换系数
        )
        
        print(f"[PREDICTIVE-FIXED] 预测位置: ({predicted_pos[0]:.1f}, {predicted_pos[1]:.1f})")
        print(f"[PREDICTIVE-FIXED] 角度偏移: H={offset_info['angle']['h']:.3f}°, V={offset_info['angle']['v']:.3f}°")
        print(f"[PREDICTIVE-FIXED] 预测移动: ({move_x}, {move_y})")
        
        # 只有当移动距离足够大时才返回移动值
        if abs(move_x) > 1 or abs(move_y) > 1:
            return (int(move_x), int(move_y))
        return None
    '''
    
    return fixed_code

def main():
    """主函数"""
    print("🔧 鼠标移动问题修复方案")
    print("=" * 50)
    print()
    
    print("📋 问题分析结果:")
    print("✅ 基础坐标计算逻辑正确")
    print("✅ G-Hub驱动工作正常")
    print("❌ 动态跟踪系统中的移动计算有问题")
    print()
    
    print("🎯 问题根源:")
    print("- 动态跟踪系统直接使用像素偏移 * movement_amp")
    print("- 没有考虑游戏FOV、屏幕分辨率等因素")
    print("- 应该使用统一的坐标系统进行计算")
    print()
    
    print("🛠️ 修复方案:")
    print("1. 修改 dynamic_tracking_system.py 中的 _static_aim 和 _predictive_aim 方法")
    print("2. 使用 coordinate_system.py 进行统一的坐标计算")
    print("3. 确保移动方向与偏移方向一致")
    print()
    
    print("📝 修复后的代码:")
    print(create_fixed_dynamic_tracking())
    
    print("\n" + "=" * 50)
    print("⚠️  接下来需要:")
    print("1. 应用修复到 dynamic_tracking_system.py")
    print("2. 测试修复效果")
    print("3. 验证游戏中的表现")

if __name__ == "__main__":
    main()
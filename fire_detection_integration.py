#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开火检测系统集成模块
将独立开火检测系统与主程序集成
"""

import time
from typing import Optional, Dict, Any
from independent_fire_detection_system import (
    IndependentFireDetectionSystem,
    FireDetectionConfig,
    get_fire_detection_system,
    initialize_fire_detection_system
)


class FireDetectionIntegration:
    """开火检测系统集成器"""
    
    def __init__(self, main_program_instance=None):
        self.main_program = main_program_instance
        self.fire_system: Optional[IndependentFireDetectionSystem] = None
        self.is_integrated = False
        
        # 配置参数
        self.config = FireDetectionConfig(
            detection_fps=300,  # 高频检测
            max_queue_size=5,   # 小队列，保持低延迟
            alignment_threshold=5.0,  # 对齐阈值
            fire_cooldown=0.08,  # 开火冷却时间
            enable_prediction=True,
            prediction_time=0.016
        )
        
        print("[FIRE_INTEGRATION] 🔗 开火检测集成器已初始化")
    
    def initialize(self, main_program_instance=None):
        """初始化集成系统"""
        if main_program_instance:
            self.main_program = main_program_instance
        
        # 创建独立开火检测系统
        self.fire_system = initialize_fire_detection_system(self.config)
        
        # 设置开火回调
        self.fire_system.set_fire_callback(self._fire_callback)
        
        # 启动检测系统
        self.fire_system.start()
        
        self.is_integrated = True
        print("[FIRE_INTEGRATION] ✅ 开火检测系统集成完成")
        
        return self.fire_system
    
    def _fire_callback(self) -> bool:
        """开火回调函数"""
        try:
            if self.main_program and hasattr(self.main_program, 'auto_fire'):
                # 调用主程序的开火函数
                return self.main_program.auto_fire()
            elif self.main_program and hasattr(self.main_program, 'auto_fire_fast'):
                # 或者调用快速开火函数
                return self.main_program.auto_fire_fast()
            else:
                # 如果没有主程序实例，使用默认开火逻辑
                return self._default_fire_action()
        except Exception as e:
            print(f"[FIRE_INTEGRATION] ❌ 开火回调异常: {e}")
            return False
    
    def _default_fire_action(self) -> bool:
        """默认开火动作"""
        try:
            import win32api
            import win32con
            
            # 模拟鼠标左键点击
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.001)  # 短暂按下
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            print("[FIRE_INTEGRATION] 💥 执行默认开火动作")
            return True
        except Exception as e:
            print(f"[FIRE_INTEGRATION] ❌ 默认开火动作失败: {e}")
            return False
    
    def update_frame_data(self, detection_results: Dict[str, Any], 
                         crosshair_x: float = 160, crosshair_y: float = 160):
        """更新帧数据到开火检测系统"""
        if not self.is_integrated or not self.fire_system:
            return
        
        try:
            # 从检测结果中提取头部位置
            head_x, head_y = self._extract_head_position(detection_results)
            
            if head_x is not None and head_y is not None:
                # 更新到独立开火检测系统
                self.fire_system.update_frame_data(
                    head_x=head_x,
                    head_y=head_y,
                    crosshair_x=crosshair_x,
                    crosshair_y=crosshair_y,
                    targets=detection_results.get('targets', []),
                    frame_id=detection_results.get('frame_id', int(time.time() * 1000))
                )
        except Exception as e:
            print(f"[FIRE_INTEGRATION] ❌ 更新帧数据异常: {e}")
    
    def _extract_head_position(self, detection_results: Dict[str, Any]) -> tuple:
        """从检测结果中提取头部位置"""
        try:
            # 尝试多种可能的头部位置字段
            head_x = None
            head_y = None
            
            # 方式1: 直接从结果中获取
            if 'head_x' in detection_results and 'head_y' in detection_results:
                head_x = detection_results['head_x']
                head_y = detection_results['head_y']
            
            # 方式2: 从目标列表中获取最佳目标的头部
            elif 'targets' in detection_results and detection_results['targets']:
                best_target = detection_results['targets'][0]  # 假设第一个是最佳目标
                if isinstance(best_target, dict):
                    head_x = best_target.get('head_x') or best_target.get('x')
                    head_y = best_target.get('head_y') or best_target.get('y')
                elif hasattr(best_target, 'head_x') and hasattr(best_target, 'head_y'):
                    head_x = best_target.head_x
                    head_y = best_target.head_y
            
            # 方式3: 从locked_target中获取
            elif 'locked_target' in detection_results and detection_results['locked_target']:
                locked = detection_results['locked_target']
                if isinstance(locked, dict):
                    head_x = locked.get('head_x') or locked.get('x')
                    head_y = locked.get('head_y') or locked.get('y')
            
            # 方式4: 从其他可能的字段获取
            elif 'x' in detection_results and 'y' in detection_results:
                head_x = detection_results['x']
                head_y = detection_results['y']
            
            return head_x, head_y
            
        except Exception as e:
            print(f"[FIRE_INTEGRATION] ❌ 提取头部位置异常: {e}")
            return None, None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取开火检测统计信息"""
        if self.fire_system:
            return self.fire_system.get_stats()
        return {}
    
    def print_stats(self):
        """打印统计信息"""
        if self.fire_system:
            self.fire_system.print_stats()
    
    def stop(self):
        """停止开火检测系统"""
        if self.fire_system:
            self.fire_system.stop()
            self.is_integrated = False
            print("[FIRE_INTEGRATION] 🛑 开火检测系统已停止")
    
    def restart(self):
        """重启开火检测系统"""
        self.stop()
        time.sleep(0.1)
        if self.fire_system:
            self.fire_system.start()
            self.is_integrated = True
            print("[FIRE_INTEGRATION] 🔄 开火检测系统已重启")
    
    def update_config(self, **kwargs):
        """更新配置参数"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                print(f"[FIRE_INTEGRATION] ⚙️ 配置更新: {key} = {value}")
        
        # 如果系统正在运行，重启以应用新配置
        if self.is_integrated:
            print("[FIRE_INTEGRATION] 🔄 重启系统以应用新配置...")
            self.restart()


# 全局集成器实例
_fire_integration: Optional[FireDetectionIntegration] = None


def get_fire_integration() -> FireDetectionIntegration:
    """获取全局开火检测集成器"""
    global _fire_integration
    if _fire_integration is None:
        _fire_integration = FireDetectionIntegration()
    return _fire_integration


def initialize_fire_integration(main_program_instance=None) -> FireDetectionIntegration:
    """初始化开火检测集成"""
    global _fire_integration
    _fire_integration = FireDetectionIntegration(main_program_instance)
    _fire_integration.initialize()
    return _fire_integration


# 便捷函数
def update_fire_detection_frame(detection_results: Dict[str, Any], 
                               crosshair_x: float = 160, crosshair_y: float = 160):
    """更新开火检测帧数据（便捷函数）"""
    integration = get_fire_integration()
    integration.update_frame_data(detection_results, crosshair_x, crosshair_y)


def get_fire_detection_stats() -> Dict[str, Any]:
    """获取开火检测统计信息（便捷函数）"""
    integration = get_fire_integration()
    return integration.get_stats()


def print_fire_detection_stats():
    """打印开火检测统计信息（便捷函数）"""
    integration = get_fire_integration()
    integration.print_stats()


if __name__ == "__main__":
    # 测试集成
    print("🧪 开火检测集成测试")
    
    # 初始化集成器
    integration = initialize_fire_integration()
    
    try:
        # 模拟检测结果更新
        for i in range(50):
            detection_results = {
                'head_x': 160 + (i % 10) - 5,
                'head_y': 160 + (i % 8) - 4,
                'targets': [{'x': 160, 'y': 160}],
                'frame_id': i
            }
            
            integration.update_frame_data(detection_results)
            time.sleep(0.02)  # 50FPS
        
        # 等待处理
        time.sleep(1.0)
        
        # 打印统计
        integration.print_stats()
        
    finally:
        integration.stop()
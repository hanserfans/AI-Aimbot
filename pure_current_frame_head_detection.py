#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纯净当前帧头部检测系统
完全基于当前帧数据，不使用任何历史记忆、预测或平滑处理
避免多目标场景下的历史信息混淆问题
"""

import time
import threading
from typing import Optional, Dict, Any

class PureCurrentFrameHeadDetection:
    """
    纯净的当前帧头部检测系统
    - 只使用当前帧数据
    - 不保存历史记忆
    - 不进行预测
    - 不进行平滑处理
    """
    
    def __init__(self):
        """初始化纯净头部检测系统"""
        self.lock = threading.Lock()
        self.stats = {
            'total_detections': 0,
            'successful_detections': 0,
            'start_time': time.time()
        }
        print("[PURE_HEAD] 纯净当前帧头部检测系统初始化完成")
    
    def calculate_head_position(self, target_data: Dict[str, Any], headshot_mode: bool = True) -> Dict[str, float]:
        """
        基于当前帧数据计算头部位置
        
        Args:
            target_data: 目标检测数据，包含边界框信息
            headshot_mode: 是否为爆头模式
            
        Returns:
            Dict: 包含头部位置的字典 {'x': float, 'y': float}
        """
        with self.lock:
            self.stats['total_detections'] += 1
            
            try:
                # 获取目标中心点和边界框高度
                center_x = target_data.get('current_mid_x', target_data.get('x', 0))
                center_y = target_data.get('current_mid_y', target_data.get('y', 0))
                box_height = target_data.get('height', target_data.get('h', 0))
                
                # 根据模式计算头部偏移
                if headshot_mode:
                    head_offset = box_height * 0.38  # 爆头模式偏移
                else:
                    head_offset = box_height * 0.2   # 普通模式偏移
                
                # 计算头部位置（向上偏移）
                head_x = center_x
                head_y = center_y - head_offset
                
                self.stats['successful_detections'] += 1
                
                result = {
                    'x': head_x,
                    'y': head_y,
                    'confidence': target_data.get('confidence', 0.0),
                    'source': 'current_frame_only'
                }
                
                print(f"[PURE_HEAD] 当前帧头部位置: ({head_x:.1f}, {head_y:.1f}) 置信度: {result['confidence']:.3f}")
                return result
                
            except Exception as e:
                print(f"[PURE_HEAD] 头部位置计算失败: {e}")
                return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            runtime = time.time() - self.stats['start_time']
            success_rate = (self.stats['successful_detections'] / max(1, self.stats['total_detections'])) * 100
            
            return {
                'total_detections': self.stats['total_detections'],
                'successful_detections': self.stats['successful_detections'],
                'success_rate': success_rate,
                'runtime_seconds': runtime,
                'avg_detections_per_second': self.stats['total_detections'] / max(1, runtime)
            }
    
    def reset_stats(self):
        """重置统计信息"""
        with self.lock:
            self.stats = {
                'total_detections': 0,
                'successful_detections': 0,
                'start_time': time.time()
            }
            print("[PURE_HEAD] 统计信息已重置")

class SimpleSingleFrameCamera:
    """
    简单的单帧相机系统
    不使用多线程，直接获取当前帧
    """
    
    def __init__(self, screenshot_system=None):
        """
        初始化简单相机系统
        
        Args:
            screenshot_system: 截图系统实例
        """
        self.screenshot_system = screenshot_system
        self.stats = {
            'frames_captured': 0,
            'start_time': time.time()
        }
        print("[SIMPLE_CAMERA] 简单单帧相机系统初始化完成")
    
    def get_current_frame(self):
        """
        获取当前帧
        直接调用截图系统，不使用缓存或队列
        
        Returns:
            numpy.ndarray: 当前帧图像
        """
        try:
            self.stats['frames_captured'] += 1
            
            if self.screenshot_system:
                # 使用现有截图系统
                if hasattr(self.screenshot_system, 'get_optimized_frame'):
                    frame = self.screenshot_system.get_optimized_frame(use_cache=False)
                elif hasattr(self.screenshot_system, 'get_latest_frame'):
                    frame = self.screenshot_system.get_latest_frame()
                else:
                    frame = None
            else:
                # 如果没有截图系统，返回None
                frame = None
            
            if frame is not None:
                print(f"[SIMPLE_CAMERA] 获取当前帧成功，大小: {frame.shape}")
            else:
                print("[SIMPLE_CAMERA] 获取当前帧失败")
            
            return frame
            
        except Exception as e:
            print(f"[SIMPLE_CAMERA] 获取帧时出错: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        runtime = time.time() - self.stats['start_time']
        fps = self.stats['frames_captured'] / max(1, runtime)
        
        return {
            'frames_captured': self.stats['frames_captured'],
            'runtime_seconds': runtime,
            'fps': fps
        }

class PureRealtimeHeadSystem:
    """
    纯净实时头部检测系统
    整合简单相机和纯净头部检测
    """
    
    def __init__(self, screenshot_system=None):
        """初始化纯净实时头部检测系统"""
        self.camera = SimpleSingleFrameCamera(screenshot_system)
        self.head_detector = PureCurrentFrameHeadDetection()
        self.is_running = False
        print("[PURE_REALTIME] 纯净实时头部检测系统初始化完成")
    
    def detect_head_in_current_frame(self, target_data: Dict[str, Any], headshot_mode: bool = True) -> Optional[Dict[str, float]]:
        """
        在当前帧中检测头部位置
        
        Args:
            target_data: 目标检测数据
            headshot_mode: 是否为爆头模式
            
        Returns:
            Dict: 头部位置信息，如果失败返回None
        """
        if not target_data:
            return None
        
        # 直接基于当前目标数据计算头部位置
        head_position = self.head_detector.calculate_head_position(target_data, headshot_mode)
        
        return head_position
    
    def get_current_frame(self):
        """获取当前帧"""
        return self.camera.get_current_frame()
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """获取综合统计信息"""
        camera_stats = self.camera.get_stats()
        head_stats = self.head_detector.get_stats()
        
        return {
            'camera': camera_stats,
            'head_detection': head_stats,
            'system_status': 'running' if self.is_running else 'stopped'
        }
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_comprehensive_stats()
        
        print("\n" + "="*50)
        print("纯净实时头部检测系统统计")
        print("="*50)
        print(f"相机系统:")
        print(f"  • 捕获帧数: {stats['camera']['frames_captured']}")
        print(f"  • 运行时间: {stats['camera']['runtime_seconds']:.1f}秒")
        print(f"  • 平均FPS: {stats['camera']['fps']:.1f}")
        print(f"头部检测:")
        print(f"  • 检测次数: {stats['head_detection']['total_detections']}")
        print(f"  • 成功次数: {stats['head_detection']['successful_detections']}")
        print(f"  • 成功率: {stats['head_detection']['success_rate']:.1f}%")
        print(f"  • 平均检测频率: {stats['head_detection']['avg_detections_per_second']:.1f}/秒")
        print(f"系统状态: {stats['system_status']}")
        print("="*50)

# 全局实例
pure_head_system = None

def initialize_pure_head_system(screenshot_system=None):
    """
    初始化纯净头部检测系统
    
    Args:
        screenshot_system: 截图系统实例
    """
    global pure_head_system
    pure_head_system = PureRealtimeHeadSystem(screenshot_system)
    print("[PURE_SYSTEM] 全局纯净头部检测系统已初始化")
    return pure_head_system

def get_pure_head_position(target_data: Dict[str, Any], headshot_mode: bool = True) -> Optional[Dict[str, float]]:
    """
    获取纯净的头部位置（全局函数）
    
    Args:
        target_data: 目标检测数据
        headshot_mode: 是否为爆头模式
        
    Returns:
        Dict: 头部位置信息
    """
    global pure_head_system
    
    if pure_head_system is None:
        print("[PURE_SYSTEM] 系统未初始化，使用默认计算")
        # 如果系统未初始化，使用简单计算
        detector = PureCurrentFrameHeadDetection()
        return detector.calculate_head_position(target_data, headshot_mode)
    
    return pure_head_system.detect_head_in_current_frame(target_data, headshot_mode)

def clear_all_memory():
    """
    清除所有记忆（实际上这个系统没有记忆需要清除）
    """
    print("[PURE_SYSTEM] 纯净系统无记忆需要清除")

if __name__ == "__main__":
    # 测试代码
    print("🧪 测试纯净当前帧头部检测系统")
    
    # 初始化系统
    system = PureRealtimeHeadSystem()
    
    # 模拟目标数据
    test_target = {
        'current_mid_x': 160,
        'current_mid_y': 120,
        'height': 80,
        'confidence': 0.85
    }
    
    # 测试头部位置计算
    for i in range(5):
        head_pos = system.detect_head_in_current_frame(test_target, headshot_mode=True)
        if head_pos:
            print(f"测试 {i+1}: 头部位置 ({head_pos['x']:.1f}, {head_pos['y']:.1f})")
        time.sleep(0.1)
    
    # 打印统计信息
    system.print_stats()
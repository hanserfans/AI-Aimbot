#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立开火检测系统
与移动系统完全解耦，实时检测最新帧中的头部位置与准星重合度
"""

import threading
import time
import queue
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
import win32api
import win32con


@dataclass
class FrameData:
    """帧数据结构"""
    timestamp: float
    head_x: float
    head_y: float
    crosshair_x: float
    crosshair_y: float
    targets: list
    frame_id: int


@dataclass
class FireDetectionConfig:
    """开火检测配置"""
    detection_fps: int = 300  # 检测频率（Hz）
    max_queue_size: int = 10  # 最大队列大小
    alignment_threshold: float = 5.0  # 对齐阈值（像素）
    fire_cooldown: float = 0.1  # 开火冷却时间（秒）
    enable_prediction: bool = True  # 启用预测开火
    prediction_time: float = 0.016  # 预测时间（秒，约1帧）


class IndependentFireDetectionSystem:
    """独立开火检测系统"""
    
    def __init__(self, config: FireDetectionConfig = None):
        self.config = config or FireDetectionConfig()
        
        # 线程控制
        self._running = False
        self._detection_thread = None
        
        # 数据队列
        self._frame_queue = queue.Queue(maxsize=self.config.max_queue_size)
        self._latest_frame: Optional[FrameData] = None
        
        # 开火控制
        self._last_fire_time = 0.0
        self._fire_callback: Optional[Callable] = None
        
        # 统计信息
        self._stats = {
            'total_frames_processed': 0,
            'fire_opportunities_detected': 0,
            'successful_fires': 0,
            'detection_fps': 0.0,
            'avg_detection_latency': 0.0
        }
        
        # 性能监控
        self._detection_times = []
        self._last_stats_update = time.time()
        
        print("[FIRE_DETECTION] 🔥 独立开火检测系统已初始化")
        print(f"[FIRE_DETECTION] 配置: 检测频率={self.config.detection_fps}Hz, 对齐阈值={self.config.alignment_threshold}px")
    
    def set_fire_callback(self, callback: Callable):
        """设置开火回调函数"""
        self._fire_callback = callback
        print("[FIRE_DETECTION] 🎯 开火回调函数已设置")
    
    def update_frame_data(self, head_x: float, head_y: float, 
                         crosshair_x: float, crosshair_y: float, 
                         targets: list, frame_id: int = None):
        """更新最新帧数据（主线程调用）"""
        frame_data = FrameData(
            timestamp=time.time(),
            head_x=head_x,
            head_y=head_y,
            crosshair_x=crosshair_x,
            crosshair_y=crosshair_y,
            targets=targets,
            frame_id=frame_id or int(time.time() * 1000)
        )
        
        # 非阻塞更新队列
        try:
            if self._frame_queue.full():
                # 移除最旧的帧
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    pass
            
            self._frame_queue.put_nowait(frame_data)
            self._latest_frame = frame_data
            
        except queue.Full:
            # 队列满时直接更新最新帧
            self._latest_frame = frame_data
    
    def start(self):
        """启动独立检测循环"""
        if self._running:
            print("[FIRE_DETECTION] ⚠️ 检测系统已在运行")
            return
        
        self._running = True
        self._detection_thread = threading.Thread(
            target=self._detection_loop,
            name="FireDetectionThread",
            daemon=True
        )
        self._detection_thread.start()
        print("[FIRE_DETECTION] 🚀 独立开火检测循环已启动")
    
    def stop(self):
        """停止检测循环"""
        if not self._running:
            return
        
        self._running = False
        if self._detection_thread and self._detection_thread.is_alive():
            self._detection_thread.join(timeout=1.0)
        
        print("[FIRE_DETECTION] 🛑 独立开火检测循环已停止")
    
    def _detection_loop(self):
        """独立检测循环（在单独线程中运行）"""
        detection_interval = 1.0 / self.config.detection_fps
        
        print(f"[FIRE_DETECTION] 🔄 检测循环开始，间隔={detection_interval*1000:.1f}ms")
        
        while self._running:
            loop_start_time = time.time()
            
            try:
                # 获取最新帧数据
                current_frame = self._get_latest_frame()
                
                if current_frame:
                    # 执行开火检测
                    self._process_fire_detection(current_frame)
                    
                    # 更新统计信息
                    self._update_stats(loop_start_time)
                
                # 控制检测频率
                elapsed = time.time() - loop_start_time
                sleep_time = max(0, detection_interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                print(f"[FIRE_DETECTION] ❌ 检测循环异常: {e}")
                time.sleep(0.001)  # 短暂延迟避免CPU占用过高
    
    def _get_latest_frame(self) -> Optional[FrameData]:
        """获取最新帧数据"""
        # 优先从队列获取最新数据
        latest_from_queue = None
        
        # 清空队列，获取最新的帧
        while not self._frame_queue.empty():
            try:
                latest_from_queue = self._frame_queue.get_nowait()
            except queue.Empty:
                break
        
        # 返回队列中的最新帧或直接存储的最新帧
        return latest_from_queue or self._latest_frame
    
    def _process_fire_detection(self, frame_data: FrameData):
        """处理开火检测逻辑"""
        current_time = time.time()
        
        # 检查冷却时间
        if current_time - self._last_fire_time < self.config.fire_cooldown:
            return
        
        # 检查按键状态
        if not self._should_detect_fire():
            return
        
        # 计算头部与准星的距离
        distance = self._calculate_alignment_distance(frame_data)
        
        # 检查是否满足开火条件
        if self._should_fire(frame_data, distance):
            self._execute_fire(frame_data, distance, current_time)
    
    def _should_detect_fire(self) -> bool:
        """检查是否应该进行开火检测"""
        try:
            # 检查右键（瞄准+开火）或Caps Lock（纯开火）
            right_mouse_pressed = win32api.GetKeyState(0x02) < 0
            caps_lock_pressed = win32api.GetKeyState(0x14) < 0
            
            return right_mouse_pressed or caps_lock_pressed
        except:
            return False
    
    def _calculate_alignment_distance(self, frame_data: FrameData) -> float:
        """计算头部与准星的对齐距离"""
        dx = frame_data.head_x - frame_data.crosshair_x
        dy = frame_data.head_y - frame_data.crosshair_y
        return (dx * dx + dy * dy) ** 0.5
    
    def _should_fire(self, frame_data: FrameData, distance: float) -> bool:
        """判断是否应该开火"""
        # 基础对齐检查
        if distance > self.config.alignment_threshold:
            return False
        
        # 预测开火（可选）
        if self.config.enable_prediction:
            return self._predict_fire_opportunity(frame_data, distance)
        
        return True
    
    def _predict_fire_opportunity(self, frame_data: FrameData, distance: float) -> bool:
        """预测开火机会（考虑移动趋势）"""
        # 简单的预测逻辑：如果距离很小，直接开火
        if distance <= self.config.alignment_threshold * 0.5:
            return True
        
        # 这里可以添加更复杂的预测逻辑
        # 例如：分析头部移动趋势，预测未来位置等
        
        return distance <= self.config.alignment_threshold
    
    def _execute_fire(self, frame_data: FrameData, distance: float, current_time: float):
        """执行开火"""
        self._stats['fire_opportunities_detected'] += 1
        
        print(f"[FIRE_DETECTION] 🔥 检测到开火机会！")
        print(f"[FIRE_DETECTION] - 头部位置: ({frame_data.head_x:.1f}, {frame_data.head_y:.1f})")
        print(f"[FIRE_DETECTION] - 准星位置: ({frame_data.crosshair_x:.1f}, {frame_data.crosshair_y:.1f})")
        print(f"[FIRE_DETECTION] - 对齐距离: {distance:.1f}px")
        print(f"[FIRE_DETECTION] - 帧延迟: {(current_time - frame_data.timestamp)*1000:.1f}ms")
        
        # 调用开火回调
        if self._fire_callback:
            try:
                success = self._fire_callback()
                if success:
                    self._stats['successful_fires'] += 1
                    self._last_fire_time = current_time
                    print(f"[FIRE_DETECTION] ✅ 开火成功！")
                else:
                    print(f"[FIRE_DETECTION] ❌ 开火失败")
            except Exception as e:
                print(f"[FIRE_DETECTION] ❌ 开火回调异常: {e}")
        else:
            print(f"[FIRE_DETECTION] ⚠️ 未设置开火回调函数")
    
    def _update_stats(self, loop_start_time: float):
        """更新统计信息"""
        current_time = time.time()
        detection_time = current_time - loop_start_time
        
        self._detection_times.append(detection_time)
        self._stats['total_frames_processed'] += 1
        
        # 每秒更新一次统计信息
        if current_time - self._last_stats_update >= 1.0:
            if self._detection_times:
                self._stats['avg_detection_latency'] = sum(self._detection_times) / len(self._detection_times)
                self._stats['detection_fps'] = len(self._detection_times)
                
                # 清理旧数据
                self._detection_times = []
            
            self._last_stats_update = current_time
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._stats.copy()
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()
        print("\n" + "="*50)
        print("🔥 独立开火检测系统统计信息")
        print("="*50)
        print(f"📊 处理帧数: {stats['total_frames_processed']}")
        print(f"🎯 检测到开火机会: {stats['fire_opportunities_detected']}")
        print(f"✅ 成功开火次数: {stats['successful_fires']}")
        print(f"📈 检测FPS: {stats['detection_fps']:.1f}")
        print(f"⏱️  平均检测延迟: {stats['avg_detection_latency']*1000:.2f}ms")
        
        if stats['fire_opportunities_detected'] > 0:
            success_rate = (stats['successful_fires'] / stats['fire_opportunities_detected']) * 100
            print(f"🎯 开火成功率: {success_rate:.1f}%")
        
        print("="*50)


def create_independent_fire_detection_system(config: FireDetectionConfig = None) -> IndependentFireDetectionSystem:
    """创建独立开火检测系统实例"""
    return IndependentFireDetectionSystem(config)


# 全局实例
_fire_detection_system: Optional[IndependentFireDetectionSystem] = None


def get_fire_detection_system() -> IndependentFireDetectionSystem:
    """获取全局开火检测系统实例"""
    global _fire_detection_system
    if _fire_detection_system is None:
        _fire_detection_system = create_independent_fire_detection_system()
    return _fire_detection_system


def initialize_fire_detection_system(config: FireDetectionConfig = None):
    """初始化全局开火检测系统"""
    global _fire_detection_system
    _fire_detection_system = create_independent_fire_detection_system(config)
    return _fire_detection_system


if __name__ == "__main__":
    # 测试代码
    print("🧪 独立开火检测系统测试")
    
    # 创建系统
    config = FireDetectionConfig(
        detection_fps=200,
        alignment_threshold=3.0,
        fire_cooldown=0.05
    )
    
    fire_system = create_independent_fire_detection_system(config)
    
    # 设置模拟开火回调
    def mock_fire_callback():
        print("💥 模拟开火！")
        return True
    
    fire_system.set_fire_callback(mock_fire_callback)
    
    # 启动系统
    fire_system.start()
    
    try:
        # 模拟帧数据更新
        for i in range(100):
            # 模拟头部逐渐接近准星
            head_x = 160 + (i % 20) - 10  # 在准星附近摆动
            head_y = 160 + (i % 15) - 7
            
            fire_system.update_frame_data(
                head_x=head_x,
                head_y=head_y,
                crosshair_x=160,
                crosshair_y=160,
                targets=[],
                frame_id=i
            )
            
            time.sleep(0.01)  # 模拟100FPS
        
        # 等待处理完成
        time.sleep(1.0)
        
        # 打印统计信息
        fire_system.print_stats()
        
    finally:
        fire_system.stop()
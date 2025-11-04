"""
实时头部检测系统
集成增强的多线程相机系统和优化的头部跟踪系统
解决历史记忆问题，确保获取最新的头部位置数据
"""

import time
import threading
import numpy as np
from typing import Optional, Dict, List, Tuple, Any
import cv2

# 导入优化组件
from enhanced_latest_frame_system import EnhancedMultiThreadedCamera, create_enhanced_camera_system
from optimized_head_tracking_system import HeadTrackingOptimizer, get_head_tracking_optimizer

class RealtimeHeadDetectionSystem:
    """实时头部检测系统"""
    
    def __init__(self, 
                 camera_system,
                 detection_model,
                 max_frame_age_ms: float = 16.67,  # 约60fps
                 detection_confidence: float = 0.5):
        """
        初始化实时头部检测系统
        
        Args:
            camera_system: 底层相机系统
            detection_model: 头部检测模型
            max_frame_age_ms: 最大帧年龄（毫秒）
            detection_confidence: 检测置信度阈值
        """
        # 增强的相机系统
        self.enhanced_camera = create_enhanced_camera_system(camera_system, max_frame_age_ms)
        
        # 检测模型
        self.detection_model = detection_model
        self.detection_confidence = detection_confidence
        
        # 优化的头部跟踪器
        self.head_tracker = get_head_tracking_optimizer()
        
        # 系统状态
        self.running = False
        self.detection_thread = None
        self.detection_interval = 1.0 / 120  # 120fps检测频率
        
        # 性能监控
        self.detection_fps = 0
        self.last_detection_time = 0
        self.frame_processing_time = 0
        
        # 检测结果缓存
        self.latest_detections = None
        self.latest_detection_timestamp = 0
        self.detection_lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            'frames_processed': 0,
            'detections_found': 0,
            'fresh_frames_used': 0,
            'stale_frames_discarded': 0,
            'avg_processing_time': 0,
            'detection_success_rate': 0
        }
        
        print(f"[INFO] 实时头部检测系统初始化完成")
        print(f"   • 最大帧年龄: {max_frame_age_ms:.2f}ms")
        print(f"   • 检测置信度: {detection_confidence}")
    
    def start(self):
        """启动实时检测系统"""
        if self.running:
            print("[WARNING] 检测系统已在运行")
            return
        
        # 启动增强相机系统
        self.enhanced_camera.start()
        
        # 启动检测线程
        self.running = True
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        
        print("[INFO] 实时头部检测系统已启动")
    
    def stop(self):
        """停止实时检测系统"""
        self.running = False
        
        # 停止检测线程
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1.0)
        
        # 停止相机系统
        self.enhanced_camera.stop()
        
        print("[INFO] 实时头部检测系统已停止")
    
    def _detection_loop(self):
        """检测循环"""
        print("[INFO] 开始头部检测循环")
        frame_count = 0
        last_fps_time = time.time()
        
        while self.running:
            try:
                loop_start_time = time.time()
                
                # 获取最新帧
                frame_data = self.enhanced_camera.get_latest_frame(max_age_ms=20.0)  # 20ms内的帧
                
                if frame_data and frame_data.get('is_fresh', True):
                    # 处理新鲜帧
                    self.stats['fresh_frames_used'] += 1
                    
                    # 执行头部检测
                    detections = self._detect_heads(frame_data['frame'])
                    
                    if detections:
                        # 更新检测结果
                        with self.detection_lock:
                            self.latest_detections = detections
                            self.latest_detection_timestamp = frame_data['timestamp']
                        
                        # 更新头部跟踪器
                        self._update_head_tracking(detections, frame_data['timestamp'])
                        
                        self.stats['detections_found'] += 1
                    
                    self.stats['frames_processed'] += 1
                    frame_count += 1
                    
                    # 记录处理时间
                    processing_time = (time.time() - loop_start_time) * 1000
                    self.stats['avg_processing_time'] = (
                        self.stats['avg_processing_time'] * 0.9 + processing_time * 0.1
                    )
                    
                elif frame_data:
                    # 帧过时，丢弃
                    self.stats['stale_frames_discarded'] += 1
                
                # 计算检测FPS
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    self.detection_fps = frame_count / (current_time - last_fps_time)
                    frame_count = 0
                    last_fps_time = current_time
                    
                    # 更新成功率
                    if self.stats['frames_processed'] > 0:
                        self.stats['detection_success_rate'] = (
                            self.stats['detections_found'] / self.stats['frames_processed'] * 100
                        )
                
                # 控制检测频率
                elapsed = time.time() - loop_start_time
                sleep_time = max(0, self.detection_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                print(f"[ERROR] 检测循环错误: {e}")
                time.sleep(0.01)
    
    def _detect_heads(self, frame: np.ndarray) -> Optional[List[Dict[str, Any]]]:
        """
        执行头部检测
        
        Args:
            frame: 输入图像帧
            
        Returns:
            检测结果列表
        """
        try:
            start_time = time.time()
            
            # 使用检测模型进行推理
            if hasattr(self.detection_model, 'predict'):
                # YOLOv8模型
                results = self.detection_model.predict(frame, conf=self.detection_confidence, verbose=False)
                detections = self._parse_yolo_results(results)
            elif hasattr(self.detection_model, 'detect'):
                # 自定义检测模型
                detections = self.detection_model.detect(frame, confidence=self.detection_confidence)
            else:
                print("[ERROR] 不支持的检测模型类型")
                return None
            
            # 记录检测时间
            detection_time = (time.time() - start_time) * 1000
            self.frame_processing_time = detection_time
            
            return detections
            
        except Exception as e:
            print(f"[ERROR] 头部检测失败: {e}")
            return None
    
    def _parse_yolo_results(self, results) -> List[Dict[str, Any]]:
        """解析YOLO检测结果"""
        detections = []
        
        try:
            for result in results:
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confidences = result.boxes.conf.cpu().numpy()
                    classes = result.boxes.cls.cpu().numpy()
                    
                    for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
                        if conf >= self.detection_confidence:
                            x1, y1, x2, y2 = box
                            center_x = (x1 + x2) / 2
                            center_y = (y1 + y2) / 2
                            width = x2 - x1
                            height = y2 - y1
                            
                            detection = {
                                'bbox': [x1, y1, x2, y2],
                                'center': [center_x, center_y],
                                'confidence': float(conf),
                                'class': int(cls),
                                'width': width,
                                'height': height,
                                'area': width * height
                            }
                            detections.append(detection)
            
        except Exception as e:
            print(f"[ERROR] 解析YOLO结果失败: {e}")
        
        return detections
    
    def _update_head_tracking(self, detections: List[Dict[str, Any]], timestamp: float):
        """
        更新头部跟踪
        
        Args:
            detections: 检测结果
            timestamp: 时间戳
        """
        try:
            if not detections:
                return
            
            # 选择最佳检测目标（置信度最高或面积最大）
            best_detection = max(detections, key=lambda d: d['confidence'] * d['area'])
            
            # 更新头部跟踪器
            center_x, center_y = best_detection['center']
            success = self.head_tracker.update_head_position(
                center_x, center_y, timestamp / 1000.0  # 转换为秒
            )
            
            if not success:
                print(f"[DEBUG] 头部位置更新失败或变化太小")
            
        except Exception as e:
            print(f"[ERROR] 更新头部跟踪失败: {e}")
    
    def get_latest_head_position(self, use_prediction: bool = True) -> Optional[Dict[str, Any]]:
        """
        获取最新的头部位置
        
        Args:
            use_prediction: 是否使用位置预测
            
        Returns:
            头部位置信息
        """
        try:
            # 从头部跟踪器获取优化的位置
            position = self.head_tracker.get_optimized_head_position(use_prediction=use_prediction)
            
            if position:
                # 添加检测相关信息
                with self.detection_lock:
                    if self.latest_detections:
                        position['detection_count'] = len(self.latest_detections)
                        position['detection_timestamp'] = self.latest_detection_timestamp
                    else:
                        position['detection_count'] = 0
                        position['detection_timestamp'] = 0
                
                # 添加系统状态信息
                position['system_running'] = self.running
                position['detection_fps'] = self.detection_fps
                position['processing_time_ms'] = self.frame_processing_time
            
            return position
            
        except Exception as e:
            print(f"[ERROR] 获取最新头部位置失败: {e}")
            return None
    
    def get_stable_head_position(self) -> Optional[Dict[str, Any]]:
        """获取稳定的头部位置"""
        return self.head_tracker.get_stable_head_position()
    
    def clear_head_memory(self):
        """清除头部记忆"""
        self.head_tracker.clear_head_memory()
        self.enhanced_camera.clear_frame_buffer()
        
        with self.detection_lock:
            self.latest_detections = None
            self.latest_detection_timestamp = 0
        
        print("[DEBUG] 头部记忆和帧缓冲已清除")
    
    def configure_system(self, 
                        max_frame_age_ms: float = None,
                        detection_confidence: float = None,
                        enable_prediction: bool = None,
                        enable_smoothing: bool = None):
        """
        配置系统参数
        
        Args:
            max_frame_age_ms: 最大帧年龄
            detection_confidence: 检测置信度
            enable_prediction: 是否启用预测
            enable_smoothing: 是否启用平滑
        """
        if max_frame_age_ms is not None:
            self.enhanced_camera.frame_system.max_frame_age_ms = max_frame_age_ms
            print(f"[INFO] 最大帧年龄设置为: {max_frame_age_ms:.2f}ms")
        
        if detection_confidence is not None:
            self.detection_confidence = detection_confidence
            print(f"[INFO] 检测置信度设置为: {detection_confidence}")
        
        if enable_prediction is not None or enable_smoothing is not None:
            self.head_tracker.configure_optimization(
                prediction_enabled=enable_prediction if enable_prediction is not None else self.head_tracker.prediction_enabled,
                smoothing_enabled=enable_smoothing if enable_smoothing is not None else self.head_tracker.smoothing_enabled
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        camera_stats = self.enhanced_camera.get_performance_stats()
        tracking_stats = self.head_tracker.get_performance_stats()
        
        return {
            'detection_fps': self.detection_fps,
            'avg_processing_time_ms': self.stats['avg_processing_time'],
            'detection_success_rate': self.stats['detection_success_rate'],
            'system_stats': self.stats.copy(),
            'camera_stats': camera_stats,
            'tracking_stats': tracking_stats,
            'is_running': self.running
        }
    
    def print_performance_stats(self):
        """打印性能统计"""
        stats = self.get_performance_stats()
        
        print(f"\n📊 实时头部检测系统统计:")
        print(f"   • 检测FPS: {stats['detection_fps']:.1f}")
        print(f"   • 平均处理时间: {stats['avg_processing_time_ms']:.2f}ms")
        print(f"   • 检测成功率: {stats['detection_success_rate']:.1f}%")
        print(f"   • 已处理帧数: {stats['system_stats']['frames_processed']}")
        print(f"   • 发现检测数: {stats['system_stats']['detections_found']}")
        print(f"   • 新鲜帧使用: {stats['system_stats']['fresh_frames_used']}")
        print(f"   • 过时帧丢弃: {stats['system_stats']['stale_frames_discarded']}")
        print(f"   • 系统运行: {'是' if stats['is_running'] else '否'}")
        
        # 打印相机和跟踪统计
        print(f"\n📷 相机系统:")
        print(f"   • 捕获FPS: {stats['camera_stats']['capture_fps']:.1f}")
        print(f"   • 新鲜帧率: {stats['camera_stats']['frame_stats']['fresh_frame_rate']:.1f}%")
        
        print(f"\n🎯 头部跟踪:")
        print(f"   • 跟踪置信度: {stats['tracking_stats']['tracking_confidence']:.2f}")
        print(f"   • 跟踪稳定: {'是' if stats['tracking_stats']['is_stable'] else '否'}")


def create_realtime_head_detection_system(camera_system, detection_model, **kwargs):
    """
    创建实时头部检测系统
    
    Args:
        camera_system: 相机系统
        detection_model: 检测模型
        **kwargs: 其他参数
        
    Returns:
        RealtimeHeadDetectionSystem实例
    """
    return RealtimeHeadDetectionSystem(camera_system, detection_model, **kwargs)


if __name__ == "__main__":
    # 测试代码
    print("实时头部检测系统测试...")
    
    # 这里需要实际的相机系统和检测模型
    # 仅作为示例展示系统架构
    
    class MockCamera:
        def get_latest_frame(self):
            return {'frame': np.zeros((320, 320, 3), dtype=np.uint8), 'timestamp': time.time() * 1000}
        
        def get_optimized_frame(self, use_cache=False):
            return np.zeros((320, 320, 3), dtype=np.uint8)
    
    class MockModel:
        def predict(self, frame, conf=0.5, verbose=False):
            # 模拟检测结果
            class MockResult:
                def __init__(self):
                    self.boxes = None
            return [MockResult()]
    
    # 创建测试系统
    mock_camera = MockCamera()
    mock_model = MockModel()
    
    detection_system = create_realtime_head_detection_system(
        mock_camera, mock_model, max_frame_age_ms=20.0
    )
    
    print("测试系统创建完成！")
    print("在实际使用中，请提供真实的相机系统和检测模型。")
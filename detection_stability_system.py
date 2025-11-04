"""
检测稳定性优化系统
通过多帧检测历史、置信度平滑和目标跟踪来减少丢失目标的情况
"""

import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import deque
import pandas as pd


class DetectionStabilitySystem:
    """检测稳定性优化系统"""
    
    def __init__(self, 
                 history_frames: int = 5,
                 confidence_smoothing: float = 0.3,
                 position_smoothing: float = 0.2,
                 min_detection_count: int = 2,
                 max_missing_frames: int = 3):
        """
        初始化检测稳定性系统
        
        Args:
            history_frames: 保持的历史帧数
            confidence_smoothing: 置信度平滑系数 (0-1)
            position_smoothing: 位置平滑系数 (0-1)
            min_detection_count: 最小检测次数才认为是稳定目标
            max_missing_frames: 最大丢失帧数，超过则移除目标
        """
        self.history_frames = history_frames
        self.confidence_smoothing = confidence_smoothing
        self.position_smoothing = position_smoothing
        self.min_detection_count = min_detection_count
        self.max_missing_frames = max_missing_frames
        
        # 检测历史记录
        self.detection_history = deque(maxlen=history_frames)
        
        # 稳定目标跟踪
        self.stable_targets = {}  # target_id -> target_info
        self.next_target_id = 0
        
        # 统计信息
        self.stats = {
            'total_detections': 0,
            'stable_detections': 0,
            'filtered_detections': 0,
            'smoothed_positions': 0
        }
        
        print("[STABILITY] 检测稳定性系统已初始化")
        print(f"   • 历史帧数: {history_frames}")
        print(f"   • 置信度平滑: {confidence_smoothing}")
        print(f"   • 位置平滑: {position_smoothing}")
        print(f"   • 最小检测次数: {min_detection_count}")
        print(f"   • 最大丢失帧数: {max_missing_frames}")
    
    def process_detections(self, raw_detections: pd.DataFrame) -> pd.DataFrame:
        """
        处理原始检测结果，返回稳定的检测结果
        
        Args:
            raw_detections: 原始检测结果DataFrame
            
        Returns:
            稳定的检测结果DataFrame
        """
        current_time = time.time()
        
        # 更新统计信息
        self.stats['total_detections'] += len(raw_detections)
        
        # 添加到历史记录
        self.detection_history.append({
            'timestamp': current_time,
            'detections': raw_detections.copy() if len(raw_detections) > 0 else pd.DataFrame()
        })
        
        # 如果没有检测到目标，尝试使用历史数据
        if len(raw_detections) == 0:
            return self._handle_no_detections(current_time)
        
        # 匹配和更新稳定目标
        matched_targets = self._match_targets(raw_detections, current_time)
        
        # 过滤稳定目标
        stable_detections = self._filter_stable_targets(matched_targets)
        
        # 应用平滑处理
        smoothed_detections = self._apply_smoothing(stable_detections)
        
        # 更新统计信息
        self.stats['stable_detections'] += len(smoothed_detections)
        
        return smoothed_detections
    
    def _match_targets(self, detections: pd.DataFrame, current_time: float) -> List[Dict]:
        """匹配当前检测与历史目标"""
        matched_targets = []
        used_detection_indices = set()
        
        # 检查DataFrame是否为空或缺少必要字段
        if detections.empty:
            return matched_targets
            
        # 首先检查数据格式并尝试转换
        detections_copy = detections.copy()
        format_recognized = False
        
        # 检查是否是 multi_threaded_ai_processor 的输出格式 [x1, y1, x2, y2, confidence, class, center_x, center_y, width, height]
        if len(detections.columns) == 10 and 'center_x' in detections.columns and 'center_y' in detections.columns:
            # 直接重命名字段
            detections_copy['current_mid_x'] = detections_copy['center_x']
            detections_copy['current_mid_y'] = detections_copy['center_y']
            print(f"[DEBUG] 识别为多线程处理器格式: [x1, y1, x2, y2, confidence, class, center_x, center_y, width, height]")
            format_recognized = True
        # 检查是否是 non_max_suppression 的输出格式 [x1, y1, x2, y2, confidence, class]
        elif len(detections.columns) == 6:
            detections_copy.columns = ['x1', 'y1', 'x2', 'y2', 'confidence', 'class']
            # 计算中心点和尺寸
            detections_copy['current_mid_x'] = (detections_copy['x1'] + detections_copy['x2']) / 2
            detections_copy['current_mid_y'] = (detections_copy['y1'] + detections_copy['y2']) / 2
            detections_copy['width'] = detections_copy['x2'] - detections_copy['x1']
            detections_copy['height'] = detections_copy['y2'] - detections_copy['y1']
            print(f"[DEBUG] 推断为6列格式: [x1, y1, x2, y2, confidence, class]")
            format_recognized = True
        elif len(detections.columns) == 5:
            # 假设前5列是 [x1, y1, x2, y2, confidence] 格式
            detections_copy.columns = ['x1', 'y1', 'x2', 'y2', 'confidence']
            # 计算中心点和尺寸
            detections_copy['current_mid_x'] = (detections_copy['x1'] + detections_copy['x2']) / 2
            detections_copy['current_mid_y'] = (detections_copy['y1'] + detections_copy['y2']) / 2
            detections_copy['width'] = detections_copy['x2'] - detections_copy['x1']
            detections_copy['height'] = detections_copy['y2'] - detections_copy['y1']
            print(f"[DEBUG] 推断为5列格式: [x1, y1, x2, y2, confidence]")
            format_recognized = True
        # 检查是否已经包含所需字段
        elif 'current_mid_x' in detections.columns and 'current_mid_y' in detections.columns:
            print(f"[DEBUG] 数据已包含所需字段")
            format_recognized = True
        else:
            print(f"[WARNING] 无法推断 {len(detections.columns)} 列的数据格式")
            print(f"[DEBUG] 可用字段: {list(detections.columns)}")
            return matched_targets
        
        # 如果格式识别成功，使用转换后的数据
        if format_recognized:
            detections = detections_copy
        
        # 为每个检测分配目标ID
        for idx, detection in detections.iterrows():
            detection_pos = (detection['current_mid_x'], detection['current_mid_y'])
            detection_conf = detection['confidence']
            
            # 寻找最匹配的历史目标
            best_match_id = None
            best_distance = float('inf')
            
            for target_id, target_info in self.stable_targets.items():
                if target_info['last_seen'] < current_time - 1.0:  # 超过1秒的目标不考虑
                    continue
                
                # 计算位置距离
                last_pos = (target_info['last_x'], target_info['last_y'])
                distance = np.sqrt((detection_pos[0] - last_pos[0])**2 + 
                                 (detection_pos[1] - last_pos[1])**2)
                
                # 距离阈值基于目标大小
                max_distance = max(50, target_info.get('avg_size', 50) * 0.5)
                
                if distance < max_distance and distance < best_distance:
                    best_distance = distance
                    best_match_id = target_id
            
            # 更新或创建目标
            if best_match_id is not None:
                # 更新现有目标
                self._update_target(best_match_id, detection, current_time)
                matched_targets.append({
                    'target_id': best_match_id,
                    'detection': detection,
                    'is_new': False
                })
            else:
                # 创建新目标
                new_target_id = self._create_new_target(detection, current_time)
                matched_targets.append({
                    'target_id': new_target_id,
                    'detection': detection,
                    'is_new': True
                })
            
            used_detection_indices.add(idx)
        
        # 更新丢失的目标
        self._update_missing_targets(current_time)
        
        return matched_targets
    
    def _create_new_target(self, detection: pd.Series, current_time: float) -> int:
        """创建新目标"""
        target_id = self.next_target_id
        self.next_target_id += 1
        
        self.stable_targets[target_id] = {
            'first_seen': current_time,
            'last_seen': current_time,
            'detection_count': 1,
            'missing_count': 0,
            'last_x': detection['current_mid_x'],
            'last_y': detection['current_mid_y'],
            'smoothed_x': detection['current_mid_x'],
            'smoothed_y': detection['current_mid_y'],
            'confidence_history': deque([detection['confidence']], maxlen=5),
            'avg_confidence': detection['confidence'],
            'avg_size': detection['height'],
            'is_stable': False
        }
        
        return target_id
    
    def _update_target(self, target_id: int, detection: pd.Series, current_time: float):
        """更新现有目标"""
        target = self.stable_targets[target_id]
        
        # 更新基本信息
        target['last_seen'] = current_time
        target['detection_count'] += 1
        target['missing_count'] = 0
        
        # 更新位置（应用平滑）
        alpha = self.position_smoothing
        target['last_x'] = detection['current_mid_x']
        target['last_y'] = detection['current_mid_y']
        target['smoothed_x'] = (1 - alpha) * target['smoothed_x'] + alpha * detection['current_mid_x']
        target['smoothed_y'] = (1 - alpha) * target['smoothed_y'] + alpha * detection['current_mid_y']
        
        # 更新置信度历史
        target['confidence_history'].append(detection['confidence'])
        target['avg_confidence'] = np.mean(list(target['confidence_history']))
        
        # 更新平均大小
        target['avg_size'] = (target['avg_size'] + detection['height']) / 2
        
        # 检查是否成为稳定目标
        if target['detection_count'] >= self.min_detection_count:
            target['is_stable'] = True
    
    def _update_missing_targets(self, current_time: float):
        """更新丢失的目标"""
        targets_to_remove = []
        
        for target_id, target in self.stable_targets.items():
            if target['last_seen'] < current_time - 0.1:  # 100ms内没有更新
                target['missing_count'] += 1
                
                # 如果丢失帧数过多，移除目标
                if target['missing_count'] > self.max_missing_frames:
                    targets_to_remove.append(target_id)
        
        # 移除过期目标
        for target_id in targets_to_remove:
            del self.stable_targets[target_id]
    
    def _filter_stable_targets(self, matched_targets: List[Dict]) -> pd.DataFrame:
        """过滤出稳定的目标"""
        stable_detections = []
        
        for match in matched_targets:
            target_id = match['target_id']
            target_info = self.stable_targets[target_id]
            
            # 只保留稳定的目标
            if target_info['is_stable']:
                detection = match['detection'].copy()
                
                # 使用平滑后的位置
                detection['current_mid_x'] = target_info['smoothed_x']
                detection['current_mid_y'] = target_info['smoothed_y']
                
                # 使用平均置信度（确保数据类型兼容）
                detection['confidence'] = float(target_info['avg_confidence'])
                
                # 添加目标ID信息
                detection['target_id'] = target_id
                detection['detection_count'] = target_info['detection_count']
                
                stable_detections.append(detection)
        
        if stable_detections:
            result_df = pd.DataFrame(stable_detections)
            self.stats['filtered_detections'] += len(result_df)
            return result_df
        else:
            return pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', 'height', 'confidence'])
    
    def _apply_smoothing(self, detections: pd.DataFrame) -> pd.DataFrame:
        """应用额外的平滑处理"""
        if len(detections) == 0:
            return detections
        
        # 置信度平滑已在目标更新中处理
        # 这里可以添加其他平滑逻辑
        
        self.stats['smoothed_positions'] += len(detections)
        return detections
    
    def _handle_no_detections(self, current_time: float) -> pd.DataFrame:
        """处理没有检测到目标的情况"""
        # 尝试使用最近的稳定目标进行预测
        predicted_targets = []
        
        for target_id, target in self.stable_targets.items():
            # 如果目标最近刚丢失，尝试预测其位置
            time_since_last = current_time - target['last_seen']
            if time_since_last < 0.2 and target['is_stable']:  # 200ms内的稳定目标
                # 简单的位置预测（可以扩展为更复杂的预测）
                predicted_detection = {
                    'current_mid_x': target['smoothed_x'],
                    'current_mid_y': target['smoothed_y'],
                    'width': target['avg_size'] * 0.8,  # 假设宽高比
                    'height': target['avg_size'],
                    'confidence': target['avg_confidence'] * 0.8,  # 降低置信度
                    'target_id': target_id,
                    'is_predicted': True
                }
                predicted_targets.append(predicted_detection)
        
        if predicted_targets:
            print(f"[STABILITY] 使用 {len(predicted_targets)} 个预测目标")
            return pd.DataFrame(predicted_targets)
        
        return pd.DataFrame(columns=['current_mid_x', 'current_mid_y', 'width', 'height', 'confidence'])
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = self.stats['total_detections']
        if total > 0:
            stability_rate = self.stats['stable_detections'] / total
            filter_rate = self.stats['filtered_detections'] / total
        else:
            stability_rate = 0
            filter_rate = 0
        
        return {
            'total_detections': total,
            'stable_detections': self.stats['stable_detections'],
            'filtered_detections': self.stats['filtered_detections'],
            'stability_rate': stability_rate,
            'filter_rate': filter_rate,
            'active_targets': len(self.stable_targets),
            'stable_targets': sum(1 for t in self.stable_targets.values() if t['is_stable'])
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            'total_detections': 0,
            'stable_detections': 0,
            'filtered_detections': 0,
            'smoothed_positions': 0
        }
    
    def clear_targets(self):
        """清除所有目标"""
        self.stable_targets.clear()
        self.detection_history.clear()
        self.next_target_id = 0
        print("[STABILITY] 已清除所有目标跟踪数据")


# 全局实例
_stability_system = None

def get_stability_system() -> DetectionStabilitySystem:
    """获取检测稳定性系统实例"""
    global _stability_system
    if _stability_system is None:
        _stability_system = DetectionStabilitySystem()
    return _stability_system

def create_stability_system(**kwargs) -> DetectionStabilitySystem:
    """创建新的检测稳定性系统实例"""
    global _stability_system
    _stability_system = DetectionStabilitySystem(**kwargs)
    return _stability_system
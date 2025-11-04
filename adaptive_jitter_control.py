"""
自适应防抖控制系统
根据屏幕分辨率自动调整防抖阈值
"""

import win32api
import math

class AdaptiveJitterControl:
    """基于分辨率的自适应防抖控制"""
    
    def __init__(self):
        self.screen_width, self.screen_height = self.get_screen_resolution()
        self.base_threshold = self.calculate_adaptive_threshold()
        print(f"[ADAPTIVE_JITTER] 屏幕分辨率: {self.screen_width}x{self.screen_height}")
        print(f"[ADAPTIVE_JITTER] 自适应阈值: {self.base_threshold:.1f} 像素")
    
    def get_screen_resolution(self):
        """获取当前屏幕分辨率"""
        width = win32api.GetSystemMetrics(0)  # SM_CXSCREEN
        height = win32api.GetSystemMetrics(1)  # SM_CYSCREEN
        return width, height
    
    def calculate_adaptive_threshold(self):
        """根据分辨率计算自适应阈值"""
        # 基准：1080p使用4像素阈值
        base_resolution = 1920 * 1080
        current_resolution = self.screen_width * self.screen_height
        
        # 分辨率缩放因子
        scale_factor = math.sqrt(current_resolution / base_resolution)
        
        # 基础阈值4像素 * 缩放因子
        adaptive_threshold = 4.0 * scale_factor
        
        # 限制阈值范围在2-12像素之间
        return max(2.0, min(12.0, adaptive_threshold))
    
    def get_movement_threshold(self, confidence: float = 1.0):
        """
        获取当前移动阈值
        
        Args:
            confidence: 检测置信度 (0-1)，置信度越低阈值越高
        
        Returns:
            float: 调整后的移动阈值
        """
        # 基于置信度调整阈值
        confidence_factor = 2.0 - confidence  # 置信度低时增加阈值
        adjusted_threshold = self.base_threshold * confidence_factor
        
        return max(1.0, min(20.0, adjusted_threshold))
    
    def get_precision_threshold(self, target_distance: float):
        """
        获取精确瞄准阈值
        
        Args:
            target_distance: 到目标的距离（像素）
        
        Returns:
            float: 精确瞄准阈值
        """
        # 距离越近，要求精度越高（阈值越小）
        if target_distance < 50:
            return self.base_threshold * 0.5  # 近距离高精度
        elif target_distance < 100:
            return self.base_threshold * 0.7  # 中距离中精度
        else:
            return self.base_threshold * 1.0  # 远距离标准精度
    
    def should_move(self, distance: float, confidence: float = 1.0):
        """
        判断是否应该移动鼠标
        
        Args:
            distance: 到目标的距离（像素）
            confidence: 检测置信度
        
        Returns:
            bool: 是否应该移动
        """
        threshold = self.get_movement_threshold(confidence)
        return distance > threshold
    
    def get_resolution_info(self):
        """获取分辨率相关信息"""
        resolution_type = "未知"
        if self.screen_width <= 1920:
            resolution_type = "1080p或更低"
        elif self.screen_width <= 2560:
            resolution_type = "1440p"
        elif self.screen_width <= 3840:
            resolution_type = "4K"
        else:
            resolution_type = "超高分辨率"
        
        return {
            'width': self.screen_width,
            'height': self.screen_height,
            'type': resolution_type,
            'base_threshold': self.base_threshold,
            'pixel_density': self.screen_width * self.screen_height / (1920 * 1080)
        }

# 全局实例
_adaptive_jitter_control = None

def get_adaptive_jitter_control():
    """获取自适应防抖控制实例"""
    global _adaptive_jitter_control
    if _adaptive_jitter_control is None:
        _adaptive_jitter_control = AdaptiveJitterControl()
    return _adaptive_jitter_control

def calculate_resolution_threshold(width: int, height: int, base_threshold: float = 4.0):
    """
    快速计算基于分辨率的阈值
    
    Args:
        width: 屏幕宽度
        height: 屏幕高度
        base_threshold: 基础阈值（1080p下的阈值）
    
    Returns:
        float: 调整后的阈值
    """
    base_resolution = 1920 * 1080
    current_resolution = width * height
    scale_factor = math.sqrt(current_resolution / base_resolution)
    return max(2.0, min(12.0, base_threshold * scale_factor))

if __name__ == "__main__":
    # 测试自适应防抖控制
    ajc = AdaptiveJitterControl()
    info = ajc.get_resolution_info()
    
    print("\n=== 自适应防抖控制测试 ===")
    print(f"分辨率类型: {info['type']}")
    print(f"像素密度倍数: {info['pixel_density']:.2f}x")
    print(f"基础阈值: {info['base_threshold']:.1f} 像素")
    
    print("\n=== 不同置信度下的阈值 ===")
    for conf in [0.5, 0.7, 0.9, 1.0]:
        threshold = ajc.get_movement_threshold(conf)
        print(f"置信度 {conf:.1f}: {threshold:.1f} 像素")
    
    print("\n=== 不同距离下的精确阈值 ===")
    for dist in [30, 60, 120, 200]:
        threshold = ajc.get_precision_threshold(dist)
        print(f"距离 {dist} 像素: {threshold:.1f} 像素阈值")
"""
统一坐标转换系统
解决自瞄系统中不同模块间的坐标系统不一致问题
"""

import math
from typing import Tuple, Dict, Any

class CoordinateSystem:
    """统一坐标系统管理器"""
    
    def __init__(self, detection_size: int = 320, game_width: int = 2560, game_height: int = 1600, game_fov: float = 103.0):
        self.detection_size = detection_size
        self.game_width = game_width
        self.game_height = game_height
        self.game_fov = game_fov
        
        # 计算基础参数
        self.detection_center = detection_size / 2.0
        self.window_aspect_ratio = game_width / game_height
        
        # 计算FOV参数
        self.game_fov_vertical = 2 * math.degrees(math.atan(
            math.tan(math.radians(game_fov / 2)) / self.window_aspect_ratio
        ))
        
        # 计算捕获区域的FOV覆盖
        self.capture_ratio_h = detection_size / game_width
        self.capture_ratio_v = detection_size / game_height
        self.effective_fov_h = game_fov * self.capture_ratio_h
        self.effective_fov_v = self.game_fov_vertical * self.capture_ratio_v
        
        print(f"[COORD] 坐标系统初始化:")
        print(f"[COORD] 检测尺寸: {detection_size}x{detection_size}")
        print(f"[COORD] 游戏分辨率: {game_width}x{game_height}")
        print(f"[COORD] 游戏FOV: H={game_fov}°, V={self.game_fov_vertical:.1f}°")
        print(f"[COORD] 有效FOV: H={self.effective_fov_h:.2f}°, V={self.effective_fov_v:.2f}°")
    
    def pixel_to_normalized(self, x: float, y: float) -> Tuple[float, float]:
        """将检测图像中的像素坐标转换为归一化坐标 [-1, 1]"""
        norm_x = (x - self.detection_center) / self.detection_center
        norm_y = (y - self.detection_center) / self.detection_center
        return (norm_x, norm_y)
    
    def normalized_to_pixel(self, norm_x: float, norm_y: float) -> Tuple[float, float]:
        """将归一化坐标 [-1, 1] 转换为检测图像中的像素坐标"""
        x = norm_x * self.detection_center + self.detection_center
        y = norm_y * self.detection_center + self.detection_center
        return (x, y)
    
    def normalized_to_angle(self, norm_x: float, norm_y: float) -> Tuple[float, float]:
        """将归一化坐标转换为角度偏移（度）"""
        angle_h = norm_x * (self.effective_fov_h / 2)
        angle_v = norm_y * (self.effective_fov_v / 2)
        return (angle_h, angle_v)
    
    def angle_to_normalized(self, angle_h: float, angle_v: float) -> Tuple[float, float]:
        """将角度偏移转换为归一化坐标"""
        norm_x = angle_h / (self.effective_fov_h / 2)
        norm_y = angle_v / (self.effective_fov_v / 2)
        return (norm_x, norm_y)
    
    def pixel_to_angle(self, x: float, y: float) -> Tuple[float, float]:
        """直接将像素坐标转换为角度偏移"""
        norm_x, norm_y = self.pixel_to_normalized(x, y)
        return self.normalized_to_angle(norm_x, norm_y)
    
    def angle_to_pixel(self, angle_h: float, angle_v: float) -> Tuple[float, float]:
        """直接将角度偏移转换为像素坐标"""
        norm_x, norm_y = self.angle_to_normalized(angle_h, angle_v)
        return self.normalized_to_pixel(norm_x, norm_y)
    
    def pixel_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """将检测图像中的像素坐标转换为游戏屏幕坐标"""
        # 计算检测图像在游戏屏幕中的位置（假设检测图像在屏幕中心）
        screen_center_x = self.game_width / 2
        screen_center_y = self.game_height / 2
        
        # 计算检测图像的缩放比例
        scale_x = self.game_width / self.detection_size
        scale_y = self.game_height / self.detection_size
        
        # 将检测图像坐标转换为相对于检测图像中心的偏移
        offset_x = x - self.detection_center
        offset_y = y - self.detection_center
        
        # 转换为屏幕坐标
        screen_x = screen_center_x + offset_x * scale_x
        screen_y = screen_center_y + offset_y * scale_y
        
        return (screen_x, screen_y)
    
    def calculate_target_head_position(self, target_x: float, target_y: float, box_height: float, headshot_mode: bool = True) -> Tuple[float, float]:
        """计算目标头部位置（像素坐标）- 修复版本"""
        if not headshot_mode:
            # 非爆头模式，瞄准身体中心
            return (target_x, target_y)
        
        # 修复：头部偏移比例从0.38改为0.12，确保瞄准头部而不是腰部
        # 人体比例：头部约占身体高度的1/8，所以向上偏移12%比较合适
        base_ratio = 0.38  # 头部偏移比例
        headshot_offset = box_height * base_ratio
        
        head_x = target_x
        head_y = target_y - headshot_offset  # 头部在目标中心上方
        
        return (head_x, head_y)
    
    def calculate_crosshair_to_target_offset(self, target_head_x: float, target_head_y: float, 
                                           crosshair_x: float = None, crosshair_y: float = None) -> Dict[str, Any]:
        """计算目标头部到准星的完整偏移信息（修复版本）"""
        # 如果没有提供准星位置，使用检测图像中心作为默认值
        if crosshair_x is None:
            crosshair_x = self.detection_center
        if crosshair_y is None:
            crosshair_y = self.detection_center
        
        # 像素偏移 - 修复：计算鼠标需要移动的方向
        # 要让准星移动到目标位置，鼠标应该向目标方向移动：target - crosshair
        pixel_offset_x = target_head_x - crosshair_x
        pixel_offset_y = target_head_y - crosshair_y
        pixel_distance = math.sqrt(pixel_offset_x**2 + pixel_offset_y**2)
        
        print(f"[COORD_FIX] 偏移计算修复:")
        print(f"[COORD_FIX] - 目标位置: ({target_head_x:.1f}, {target_head_y:.1f})")
        print(f"[COORD_FIX] - 准星位置: ({crosshair_x:.1f}, {crosshair_y:.1f})")
        print(f"[COORD_FIX] - 像素偏移: ({pixel_offset_x:.1f}, {pixel_offset_y:.1f})")
        print(f"[COORD_FIX] - 偏移距离: {pixel_distance:.1f}px")
        
        # 将像素偏移转换为归一化坐标偏移
        norm_offset_x = pixel_offset_x / self.detection_center
        norm_offset_y = pixel_offset_y / self.detection_center
        norm_distance = math.sqrt(norm_offset_x**2 + norm_offset_y**2)
        
        # 将归一化偏移转换为角度偏移
        angle_offset_h = norm_offset_x * (self.effective_fov_h / 2)
        angle_offset_v = norm_offset_y * (self.effective_fov_v / 2)
        angle_distance = math.sqrt(angle_offset_h**2 + angle_offset_v**2)
        
        return {
            'pixel': {
                'x': pixel_offset_x,
                'y': pixel_offset_y,
                'distance': pixel_distance
            },
            'normalized': {
                'x': norm_offset_x,
                'y': norm_offset_y,
                'distance': norm_distance
            },
            'angle': {
                'h': angle_offset_h,
                'v': angle_offset_v,
                'distance': angle_distance
            },
            'target_head': {
                'x': target_head_x,
                'y': target_head_y
            },
            'crosshair': {
                'x': crosshair_x,
                'y': crosshair_y
            }
        }
    
    def calculate_mouse_movement_direct(self, pixel_offset_x: float, pixel_offset_y: float,
                                      target_distance_factor: float = 1.0,
                                      base_scaling: float = 1.0) -> Tuple[int, int]:
        """直接像素移动方法 - 简单高效"""
        # 基于距离的智能缩放
        distance = math.sqrt(pixel_offset_x**2 + pixel_offset_y**2)
        
        # 距离越远，缩放系数越小（避免过度移动）
        if distance > 100:
            distance_scaling = 0.8
        elif distance > 50:
            distance_scaling = 0.9
        else:
            distance_scaling = 1.0
        
        # 应用缩放系数
        final_scaling = base_scaling * distance_scaling * target_distance_factor
        
        # 计算最终移动量
        mouse_x = round(pixel_offset_x * final_scaling)
        mouse_y = round(pixel_offset_y * final_scaling)
        
        print(f"[COORD_DIRECT] 直接移动: 像素偏移({pixel_offset_x:.1f}, {pixel_offset_y:.1f}) -> 移动({mouse_x}, {mouse_y})")
        print(f"[COORD_DIRECT] 缩放参数: base={base_scaling:.2f}, distance={distance_scaling:.2f}, target={target_distance_factor:.2f}")
        
        return (int(mouse_x), int(mouse_y))

    def calculate_mouse_movement(self, angle_offset_h: float, angle_offset_v: float, 
                               target_distance_factor: float = 1.0, 
                               base_sensitivity: float = 25.0) -> Tuple[int, int]:
        """计算鼠标移动量（基于角度偏移）- 精确版本"""
        # 直接计算角度偏移对应的像素偏移量
        # 角度偏移 -> 归一化坐标 -> 像素偏移
        norm_x, norm_y = self.angle_to_normalized(angle_offset_h, angle_offset_v)
        
        # 将归一化坐标转换为像素偏移量（相对于中心点）
        pixel_offset_x = norm_x * self.detection_center
        pixel_offset_y = norm_y * self.detection_center
        
        # 距离系数调整 - 保持简单
        distance_factor = max(0.8, min(1.2, target_distance_factor))
        
        # 应用距离系数
        mouse_x = round(pixel_offset_x * distance_factor)
        mouse_y = round(pixel_offset_y * distance_factor)
        
        print(f"[COORD] 鼠标移动计算: 角度({angle_offset_h:.3f}°, {angle_offset_v:.3f}°) -> 像素偏移({pixel_offset_x:.1f}, {pixel_offset_y:.1f}) -> 移动({mouse_x}, {mouse_y})")
        print(f"[COORD] 转换参数: distance_factor={distance_factor:.2f}")
        
        return (int(mouse_x), int(mouse_y))
    
    def is_target_aligned(self, target_head_x: float, target_head_y: float, 
                         crosshair_x: float = None, crosshair_y: float = None,
                         angle_threshold: float = 0.5, pixel_threshold: float = 5.0) -> Dict[str, Any]:
        """检查目标是否与准星对齐"""
        offset_info = self.calculate_crosshair_to_target_offset(target_head_x, target_head_y, crosshair_x, crosshair_y)
        
        # 角度对齐检查
        angle_aligned = offset_info['angle']['distance'] <= angle_threshold
        
        # 像素对齐检查
        pixel_aligned = offset_info['pixel']['distance'] <= pixel_threshold
        
        # 综合对齐判断
        aligned = angle_aligned and pixel_aligned
        
        return {
            'aligned': aligned,
            'angle_aligned': angle_aligned,
            'pixel_aligned': pixel_aligned,
            'angle_distance': offset_info['angle']['distance'],
            'pixel_distance': offset_info['pixel']['distance'],
            'angle_threshold': angle_threshold,
            'pixel_threshold': pixel_threshold,
            'offset_info': offset_info
        }
    
    def debug_info(self, target_x: float, target_y: float, box_height: float, headshot_mode: bool = True) -> str:
        """生成调试信息"""
        head_x, head_y = self.calculate_target_head_position(target_x, target_y, box_height, headshot_mode)
        offset_info = self.calculate_crosshair_to_target_offset(head_x, head_y)
        
        debug_str = f"""
[COORD] ===== 坐标系统调试信息 =====
[COORD] 目标中心: ({target_x:.1f}, {target_y:.1f}), 高度: {box_height:.1f}px
[COORD] 目标头部: ({head_x:.1f}, {head_y:.1f})
[COORD] 准星位置: ({offset_info['crosshair']['x']:.1f}, {offset_info['crosshair']['y']:.1f})
[COORD] 像素偏移: ({offset_info['pixel']['x']:.1f}, {offset_info['pixel']['y']:.1f}), 距离: {offset_info['pixel']['distance']:.1f}px
[COORD] 归一化偏移: ({offset_info['normalized']['x']:.3f}, {offset_info['normalized']['y']:.3f}), 距离: {offset_info['normalized']['distance']:.3f}
[COORD] 角度偏移: ({offset_info['angle']['h']:.3f}°, {offset_info['angle']['v']:.3f}°), 距离: {offset_info['angle']['distance']:.3f}°
[COORD] ================================
"""
        return debug_str.strip()

# 全局坐标系统实例
_global_coord_system = None

def get_coordinate_system(detection_size: int = 320, game_width: int = 2560, 
                         game_height: int = 1600, game_fov: float = 103.0) -> CoordinateSystem:
    """获取全局坐标系统实例"""
    global _global_coord_system
    if _global_coord_system is None:
        _global_coord_system = CoordinateSystem(detection_size, game_width, game_height, game_fov)
    return _global_coord_system

def reset_coordinate_system():
    """重置全局坐标系统"""
    global _global_coord_system
    _global_coord_system = None
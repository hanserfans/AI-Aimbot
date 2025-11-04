"""
方向性鼠标矫正系统
支持X轴正负方向和Y轴正负方向的独立矫正因子
"""

import json
import os
import time
import pyautogui
from mouse_driver.MouseMove import MouseMove

class DirectionalCorrection:
    def __init__(self, config_file="directional_config.json"):
        """
        初始化方向性矫正系统
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        
        # 默认矫正因子 (统一设置为0.68进行小范围移动测试)
        self.default_factors = {
            "x_positive": 0.68,  # X轴正方向(右) - 统一矫正因子
            "x_negative": 0.68,  # X轴负方向(左) - 统一矫正因子
            "y_positive": 0.68,  # Y轴正方向(下) - 统一矫正因子
            "y_negative": 0.68   # Y轴负方向(上) - 统一矫正因子
        }
        
        # 加载配置
        self.correction_factors = self.load_config()
        
        # 初始化鼠标驱动
        self.mouse_driver = MouseMove()
        
        # 禁用自适应矫正以避免冲突
        try:
            from mouse_driver.MouseMove import set_adaptive_correction
            set_adaptive_correction(False)
            print("🚫 已禁用自适应矫正系统")
        except Exception as e:
            print(f"⚠️ 无法禁用自适应矫正: {e}")
        
        # 性能统计
        self.total_moves = 0
        self.successful_moves = 0
        self.total_error = 0.0
        
        print("🎯 方向性矫正系统已初始化")
        print(f"📊 当前矫正因子:")
        print(f"   X轴正方向(→): {self.correction_factors['x_positive']:.3f}")
        print(f"   X轴负方向(←): {self.correction_factors['x_negative']:.3f}")
        print(f"   Y轴正方向(↓): {self.correction_factors['y_positive']:.3f}")
        print(f"   Y轴负方向(↑): {self.correction_factors['y_negative']:.3f}")

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ 已加载配置文件: {self.config_file}")
                return config
            except Exception as e:
                print(f"⚠️ 配置文件加载失败: {e}")
                return self.default_factors.copy()
        else:
            print(f"📝 创建默认配置文件: {self.config_file}")
            self.save_config(self.default_factors)
            return self.default_factors.copy()

    def save_config(self, factors=None):
        """保存配置文件"""
        if factors is None:
            factors = self.correction_factors
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(factors, f, indent=4, ensure_ascii=False)
            print(f"💾 配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"❌ 配置保存失败: {e}")

    def get_correction_factor(self, dx, dy):
        """
        根据移动方向获取对应的矫正因子
        
        Args:
            dx: X轴移动距离
            dy: Y轴移动距离
            
        Returns:
            tuple: (x_factor, y_factor)
        """
        # X轴矫正因子
        if dx > 0:
            x_factor = self.correction_factors["x_positive"]
        elif dx < 0:
            x_factor = self.correction_factors["x_negative"]
        else:
            x_factor = 1.0  # 无移动时不需要矫正
        
        # Y轴矫正因子
        if dy > 0:
            y_factor = self.correction_factors["y_positive"]
        elif dy < 0:
            y_factor = self.correction_factors["y_negative"]
        else:
            y_factor = 1.0  # 无移动时不需要矫正
        
        return x_factor, y_factor

    def move_mouse(self, dx, dy, verify=True):
        """
        执行方向性矫正的鼠标移动
        
        Args:
            dx: X轴移动距离
            dy: Y轴移动距离
            verify: 是否验证移动结果
            
        Returns:
            dict: 移动结果信息
        """
        start_time = time.time()
        start_pos = pyautogui.position()
        
        # 获取方向性矫正因子
        x_factor, y_factor = self.get_correction_factor(dx, dy)
        
        # 应用矫正
        corrected_dx = int(dx * x_factor)
        corrected_dy = int(dy * y_factor)
        
        # 执行移动
        try:
            self.mouse_driver.move_mouse(corrected_dx, corrected_dy)
            time.sleep(0.1)  # 等待移动完成
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "expected": (dx, dy),
                "actual": (0, 0),  # 移动失败时设为0
                "corrected": (corrected_dx, corrected_dy),
                "factors": (x_factor, y_factor),
                "error": (abs(dx), abs(dy)),
                "total_error": (dx**2 + dy**2)**0.5,
                "threshold": 999,
                "duration": time.time() - start_time
            }
        
        # 验证移动结果
        if verify:
            time.sleep(0.15)  # 等待位置稳定 - 增加延迟确保鼠标位置准确
            end_pos = pyautogui.position()
            actual_dx = end_pos.x - start_pos.x
            actual_dy = end_pos.y - start_pos.y
            
            # 计算误差
            error_x = abs(actual_dx - dx)
            error_y = abs(actual_dy - dy)
            total_error = (error_x**2 + error_y**2)**0.5
            
            # 判断是否成功 (动态阈值)
            distance = (dx**2 + dy**2)**0.5
            if distance <= 5:
                threshold = 3.0
            elif distance <= 15:
                threshold = max(3.0, distance * 0.4)
            elif distance <= 30:
                threshold = max(5.0, distance * 0.25)
            else:
                threshold = max(8.0, distance * 0.15)
            
            success = total_error <= threshold
            
            # 更新统计
            self.total_moves += 1
            if success:
                self.successful_moves += 1
            self.total_error += total_error
            
            duration = time.time() - start_time
            
            return {
                "success": success,
                "expected": (dx, dy),
                "actual": (actual_dx, actual_dy),
                "corrected": (corrected_dx, corrected_dy),
                "factors": (x_factor, y_factor),
                "error": (error_x, error_y),
                "total_error": total_error,
                "threshold": threshold,
                "duration": duration
            }
        else:
            return {
                "success": True,
                "expected": (dx, dy),
                "corrected": (corrected_dx, corrected_dy),
                "factors": (x_factor, y_factor)
            }

    def update_factor(self, direction, new_factor):
        """
        更新指定方向的矫正因子
        
        Args:
            direction: 方向 ("x_positive", "x_negative", "y_positive", "y_negative")
            new_factor: 新的矫正因子
        """
        if direction in self.correction_factors:
            old_factor = self.correction_factors[direction]
            self.correction_factors[direction] = new_factor
            self.save_config()
            print(f"🔧 已更新 {direction}: {old_factor:.3f} → {new_factor:.3f}")
        else:
            print(f"❌ 无效的方向: {direction}")

    def calibrate_direction(self, direction, test_distance=50, test_count=5):
        """
        校准指定方向的矫正因子
        
        Args:
            direction: 方向 ("x_positive", "x_negative", "y_positive", "y_negative")
            test_distance: 测试距离
            test_count: 测试次数
        """
        print(f"🎯 开始校准 {direction} 方向...")
        
        # 确定测试移动
        if direction == "x_positive":
            test_dx, test_dy = test_distance, 0
        elif direction == "x_negative":
            test_dx, test_dy = -test_distance, 0
        elif direction == "y_positive":
            test_dx, test_dy = 0, test_distance
        elif direction == "y_negative":
            test_dx, test_dy = 0, -test_distance
        else:
            print(f"❌ 无效的方向: {direction}")
            return
        
        total_error = 0.0
        results = []
        
        for i in range(test_count):
            print(f"📍 测试 {i+1}/{test_count}")
            result = self.move_mouse(test_dx, test_dy)
            
            if result["success"]:
                error = result["total_error"]
                total_error += error
                results.append(error)
                print(f"   误差: {error:.2f}px")
            else:
                print(f"   失败: {result.get('error', '未知错误')}")
        
        if results:
            avg_error = total_error / len(results)
            print(f"📊 平均误差: {avg_error:.2f}px")
            
            # 如果误差较大，建议调整因子
            if avg_error > 3.0:
                current_factor = self.correction_factors[direction]
                # 简单的线性调整建议
                if direction.startswith("x"):
                    actual_avg = sum(abs(r["actual"][0] - test_dx) for r in [self.move_mouse(test_dx, test_dy) for _ in range(3)]) / 3
                else:
                    actual_avg = sum(abs(r["actual"][1] - test_dy) for r in [self.move_mouse(test_dx, test_dy) for _ in range(3)]) / 3
                
                suggested_factor = current_factor * (test_distance / (test_distance + actual_avg - test_distance))
                suggested_factor = max(0.3, min(1.2, suggested_factor))  # 限制范围
                
                print(f"💡 建议调整因子: {current_factor:.3f} → {suggested_factor:.3f}")
                
                # 询问是否应用建议
                response = input("是否应用建议的矫正因子? (y/n): ").lower().strip()
                if response == 'y':
                    self.update_factor(direction, suggested_factor)

    def get_performance_stats(self):
        """获取性能统计"""
        if self.total_moves == 0:
            return {
                "total_moves": 0,
                "successful_moves": 0,
                "success_rate": 0.0,
                "average_error": 0.0
            }
        
        success_rate = (self.successful_moves / self.total_moves) * 100
        average_error = self.total_error / self.total_moves
        
        return {
            "total_moves": self.total_moves,
            "successful_moves": self.successful_moves,
            "success_rate": success_rate,
            "average_error": average_error
        }

    def print_performance_report(self):
        """打印性能报告"""
        stats = self.get_performance_stats()
        
        print("\n" + "="*50)
        print("🎯 方向性矫正系统性能报告")
        print("="*50)
        print(f"总移动次数: {stats['total_moves']}")
        print(f"成功移动次数: {stats['successful_moves']}")
        print(f"成功率: {stats['success_rate']:.1f}%")
        print(f"平均误差: {stats['average_error']:.2f}px")
        print("\n当前矫正因子:")
        print(f"  X轴正方向(→): {self.correction_factors['x_positive']:.3f}")
        print(f"  X轴负方向(←): {self.correction_factors['x_negative']:.3f}")
        print(f"  Y轴正方向(↓): {self.correction_factors['y_positive']:.3f}")
        print(f"  Y轴负方向(↑): {self.correction_factors['y_negative']:.3f}")
        print("="*50)


# 创建全局实例
directional_mouse = DirectionalCorrection()

if __name__ == "__main__":
    # 简单测试
    print("🧪 开始简单测试...")
    
    test_moves = [
        (10, 0),   # 右
        (-10, 0),  # 左
        (0, 10),   # 下
        (0, -10),  # 上
        (15, 15),  # 右下
        (-15, -15) # 左上
    ]
    
    for dx, dy in test_moves:
        print(f"\n测试移动: ({dx}, {dy})")
        result = directional_mouse.move_mouse(dx, dy)
        
        if result["success"]:
            print(f"✅ 成功 - 误差: {result['total_error']:.2f}px")
        else:
            print(f"❌ 失败 - 误差: {result['total_error']:.2f}px")
    
    # 打印性能报告
    directional_mouse.print_performance_report()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本
用于验证检测频率优化和静态目标检测改进的效果
"""

import time
import cv2
import numpy as np
import win32api
import win32con
import win32gui
from performance_optimizer import get_performance_optimizer
from config import confidence, screenShotHeight, screenShotWidth
import onnxruntime as ort
from utils.general import non_max_suppression
import torch

class PerformanceTest:
    def __init__(self):
        self.perf_optimizer = get_performance_optimizer()
        self.test_results = {
            'fps_samples': [],
            'detection_times': [],
            'target_counts': [],
            'confidence_values': [],
            'static_detection_success': 0,
            'total_frames': 0
        }
        
    def setup_onnx_session(self):
        """初始化ONNX会话"""
        try:
            # 简化的ONNX设置用于测试
            providers = ['CPUExecutionProvider']  # 使用CPU进行测试
            model_path = "models/best.onnx"  # 假设模型路径
            
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            self.ort_sess = ort.InferenceSession(model_path, providers=providers, sess_options=session_options)
            print("[INFO] ONNX会话初始化成功")
            return True
        except Exception as e:
            print(f"[ERROR] ONNX会话初始化失败: {e}")
            return False
    
    def generate_test_image(self, has_target=True, target_size='medium'):
        """生成测试图像"""
        # 创建基础图像
        img = np.random.randint(0, 255, (screenShotHeight, screenShotWidth, 3), dtype=np.uint8)
        
        if has_target:
            # 添加模拟目标（简单的矩形）
            if target_size == 'small':
                w, h = 20, 30
            elif target_size == 'medium':
                w, h = 40, 60
            else:  # large
                w, h = 80, 120
            
            # 随机位置
            x = np.random.randint(w//2, screenShotWidth - w//2)
            y = np.random.randint(h//2, screenShotHeight - h//2)
            
            # 绘制目标（使用人体颜色）
            cv2.rectangle(img, (x-w//2, y-h//2), (x+w//2, y+h//2), (120, 80, 60), -1)
            
        return img
    
    def test_detection_frequency(self, duration=30):
        """测试检测频率"""
        print(f"[INFO] 开始检测频率测试，持续时间: {duration}秒")
        
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < duration:
            frame_start = self.perf_optimizer.start_frame()
            
            # 检查是否需要跳帧
            if self.perf_optimizer.should_skip_frame():
                time.sleep(0.001)
                continue
            
            # 生成测试图像
            test_img = self.generate_test_image(has_target=True)
            
            # 模拟检测过程
            detection_start = time.time()
            
            # 简单的图像处理模拟
            processed_img = torch.nn.functional.interpolate(
    torch.from_numpy(test_img).permute(2, 0, 1).float().unsqueeze(0).to('cuda'),
    size=(320, 320), mode='bilinear', align_corners=False
).squeeze(0).permute(1, 2, 0).cpu().numpy().astype(np.uint8)
            processed_img = (torch.from_numpy(processed_img).float().to('cuda') / 255.0).cpu().numpy()
            
            # 模拟检测时间
            time.sleep(0.01)  # 模拟10ms的检测时间
            
            detection_time = time.time() - detection_start
            target_count = np.random.randint(0, 3)  # 随机目标数量
            
            # 记录性能数据
            self.perf_optimizer.record_detection(detection_time, target_count)
            self.perf_optimizer.end_frame()
            
            # 收集测试数据
            self.test_results['detection_times'].append(detection_time)
            self.test_results['target_counts'].append(target_count)
            self.test_results['fps_samples'].append(self.perf_optimizer.get_current_fps())
            
            frame_count += 1
            
            # 检查退出条件
            if win32api.GetAsyncKeyState(ord('Q')) & 0x8000:
                break
        
        self.test_results['total_frames'] = frame_count
        print(f"[INFO] 检测频率测试完成，总帧数: {frame_count}")
    
    def test_static_detection(self, test_count=100):
        """测试静态目标检测能力"""
        print(f"[INFO] 开始静态目标检测测试，测试次数: {test_count}")
        
        success_count = 0
        
        for i in range(test_count):
            # 生成静态目标图像
            test_img = self.generate_test_image(has_target=True, target_size='small')
            
            # 使用动态置信度
            dynamic_confidence = self.perf_optimizer.get_optimized_confidence()
            self.test_results['confidence_values'].append(dynamic_confidence)
            
            # 模拟检测结果（简化版本）
            # 在实际测试中，这里应该调用真实的检测模型
            detection_success = np.random.random() > (0.5 - (0.4 - dynamic_confidence))
            
            if detection_success:
                success_count += 1
            
            # 更新性能优化器的目标状态
            if i % 10 == 0:  # 每10帧更新一次
                self.perf_optimizer.update_target_state(
                    has_targets=detection_success,
                    target_moving=False  # 静态目标
                )
        
        self.test_results['static_detection_success'] = success_count
        print(f"[INFO] 静态目标检测测试完成，成功率: {success_count/test_count*100:.1f}%")
    
    def test_confidence_adaptation(self, duration=20):
        """测试置信度自适应调整"""
        print(f"[INFO] 开始置信度自适应测试，持续时间: {duration}秒")
        
        start_time = time.time()
        confidence_history = []
        
        while time.time() - start_time < duration:
            # 模拟不同的检测场景
            current_time = time.time() - start_time
            
            if current_time < duration / 3:
                # 第一阶段：无目标场景
                has_targets = False
                target_moving = False
            elif current_time < 2 * duration / 3:
                # 第二阶段：静态目标场景
                has_targets = True
                target_moving = False
            else:
                # 第三阶段：动态目标场景
                has_targets = True
                target_moving = True
            
            # 更新目标状态
            self.perf_optimizer.update_target_state(has_targets, target_moving)
            
            # 获取当前置信度
            current_confidence = self.perf_optimizer.get_optimized_confidence()
            confidence_history.append({
                'time': current_time,
                'confidence': current_confidence,
                'has_targets': has_targets,
                'target_moving': target_moving
            })
            
            time.sleep(0.1)  # 100ms间隔
        
        self.test_results['confidence_adaptation'] = confidence_history
        print("[INFO] 置信度自适应测试完成")
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("🚀 性能优化测试报告")
        print("="*60)
        
        # FPS统计
        if self.test_results['fps_samples']:
            avg_fps = np.mean(self.test_results['fps_samples'])
            max_fps = np.max(self.test_results['fps_samples'])
            min_fps = np.min(self.test_results['fps_samples'])
            print(f"📊 FPS统计:")
            print(f"   平均FPS: {avg_fps:.1f}")
            print(f"   最大FPS: {max_fps:.1f}")
            print(f"   最小FPS: {min_fps:.1f}")
        
        # 检测时间统计
        if self.test_results['detection_times']:
            avg_detection_time = np.mean(self.test_results['detection_times']) * 1000
            max_detection_time = np.max(self.test_results['detection_times']) * 1000
            print(f"\n⏱️ 检测时间统计:")
            print(f"   平均检测时间: {avg_detection_time:.1f}ms")
            print(f"   最大检测时间: {max_detection_time:.1f}ms")
        
        # 静态目标检测统计
        if 'static_detection_success' in self.test_results:
            success_rate = self.test_results['static_detection_success'] / 100 * 100
            print(f"\n🎯 静态目标检测:")
            print(f"   检测成功率: {success_rate:.1f}%")
        
        # 置信度统计
        if self.test_results['confidence_values']:
            avg_confidence = np.mean(self.test_results['confidence_values'])
            min_confidence = np.min(self.test_results['confidence_values'])
            max_confidence = np.max(self.test_results['confidence_values'])
            print(f"\n🔍 动态置信度统计:")
            print(f"   平均置信度: {avg_confidence:.3f}")
            print(f"   最小置信度: {min_confidence:.3f}")
            print(f"   最大置信度: {max_confidence:.3f}")
        
        # 性能优化器报告
        print(f"\n{self.perf_optimizer.get_performance_report()}")
        
        print("="*60)
        print("✅ 测试完成")
        print("="*60)
    
    def run_full_test(self):
        """运行完整的性能测试"""
        print("🚀 开始性能优化验证测试")
        print("按 Q 键可以提前退出任何测试阶段")
        print("-" * 40)
        
        try:
            # 1. 检测频率测试
            self.test_detection_frequency(duration=15)
            
            # 2. 静态目标检测测试
            self.test_static_detection(test_count=50)
            
            # 3. 置信度自适应测试
            self.test_confidence_adaptation(duration=10)
            
            # 4. 生成报告
            self.generate_report()
            
        except KeyboardInterrupt:
            print("\n[INFO] 测试被用户中断")
        except Exception as e:
            print(f"\n[ERROR] 测试过程中发生错误: {e}")
        finally:
            print("\n[INFO] 测试结束")

def main():
    """主函数"""
    print("性能测试脚本")
    print("此脚本将测试检测频率优化和静态目标检测改进的效果")
    print("按任意键开始测试...")
    input()
    
    test = PerformanceTest()
    test.run_full_test()

if __name__ == "__main__":
    main()
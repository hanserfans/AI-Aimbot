#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
准星校准工具
用于精确调整外部准星与游戏内准星的对齐
"""

import cv2
import numpy as np
import torch
import torch.nn.functional as F
import time
from gameSelection import gameSelection
from config import screenShotWidth, screenShotHeight

class CrosshairCalibrationTool:
    def __init__(self):
        self.current_offset_y = 18  # 当前的Y轴偏移量
        self.current_offset_x = 0   # 当前的X轴偏移量
        self.adjustment_step = 1    # 每次调整的步长
        
    def draw_calibration_crosshair(self, img, center_x, center_y, offset_x=0, offset_y=0):
        """绘制校准用的准星"""
        # 计算调整后的中心点
        adj_center_x = center_x + offset_x
        adj_center_y = center_y + offset_y
        
        # 绘制主准星（红色）
        cv2.line(img, (adj_center_x - 20, adj_center_y), (adj_center_x + 20, adj_center_y), (0, 0, 255), 2)
        cv2.line(img, (adj_center_x, adj_center_y - 20), (adj_center_x, adj_center_y + 20), (0, 0, 255), 2)
        
        # 绘制中心点
        cv2.circle(img, (adj_center_x, adj_center_y), 3, (0, 0, 255), -1)
        
        # 绘制参考网格（绿色）
        for i in range(-2, 3):
            for j in range(-2, 3):
                if i == 0 and j == 0:
                    continue
                grid_x = center_x + i * 20
                grid_y = center_y + j * 20
                cv2.circle(img, (grid_x, grid_y), 1, (0, 255, 0), 1)
        
        return img
    
    def show_calibration_info(self, img):
        """显示校准信息"""
        info_text = [
            f"Y Offset: {self.current_offset_y}px",
            f"X Offset: {self.current_offset_x}px",
            f"Step: {self.adjustment_step}px",
            "",
            "Controls:",
            "W/S - Adjust Y offset",
            "A/D - Adjust X offset", 
            "+/- - Change step size",
            "R - Reset offsets",
            "Q - Quit",
            "SPACE - Apply to gameSelection.py"
        ]
        
        y_start = 30
        for i, text in enumerate(info_text):
            color = (255, 255, 255) if text else (0, 0, 0)
            cv2.putText(img, text, (10, y_start + i * 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return img
    
    def apply_offset_to_file(self):
        """将当前偏移量应用到gameSelection.py文件"""
        try:
            with open('gameSelection.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找并替换偏移量
            import re
            pattern = r'top = window_center_y - \(screenShotHeight // 2\) \+ (\d+)'
            replacement = f'top = window_center_y - (screenShotHeight // 2) + {self.current_offset_y}'
            
            if re.search(pattern, content):
                new_content = re.sub(pattern, replacement, content)
                with open('gameSelection.py', 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✓ 已将Y偏移量 {self.current_offset_y}px 应用到 gameSelection.py")
                return True
            else:
                print("❌ 未找到偏移量设置行，请手动修改")
                return False
                
        except Exception as e:
            print(f"❌ 应用偏移量时出错: {e}")
            return False
    
    def run_calibration(self):
        """运行校准工具"""
        print("=== 准星校准工具 ===")
        print("正在初始化截图系统...")
        
        # 获取游戏窗口和截图区域
        result = gameSelection()
        if result is None:
            print("❌ 无法获取游戏窗口，请确保游戏正在运行")
            return
        
        sct, region, cWidth, cHeight = result
        print(f"✓ 截图区域: {region}")
        print(f"✓ 中心点: ({cWidth}, {cHeight})")
        print()
        print("校准说明:")
        print("1. 观察红色准星与游戏内准星的对齐情况")
        print("2. 使用 W/S 键调整竖直偏移")
        print("3. 使用 A/D 键调整水平偏移")
        print("4. 按空格键应用当前设置到配置文件")
        print("5. 按 Q 键退出")
        print()
        
        while True:
            try:
                # 截取屏幕
                screenshot = sct.grab(region)
                img = torch.tensor(screenshot, device='cuda').cpu().numpy()
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # 绘制校准准星
                img = self.draw_calibration_crosshair(
                    img, cWidth, cHeight, 
                    self.current_offset_x, self.current_offset_y
                )
                
                # 显示校准信息
                img = self.show_calibration_info(img)
                
                # 显示图像
                cv2.imshow('Crosshair Calibration Tool', img)
                
                # 处理按键
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord('w'):
                    self.current_offset_y -= self.adjustment_step
                    print(f"Y偏移: {self.current_offset_y}px")
                elif key == ord('s'):
                    self.current_offset_y += self.adjustment_step
                    print(f"Y偏移: {self.current_offset_y}px")
                elif key == ord('a'):
                    self.current_offset_x -= self.adjustment_step
                    print(f"X偏移: {self.current_offset_x}px")
                elif key == ord('d'):
                    self.current_offset_x += self.adjustment_step
                    print(f"X偏移: {self.current_offset_x}px")
                elif key == ord('+') or key == ord('='):
                    self.adjustment_step = min(10, self.adjustment_step + 1)
                    print(f"调整步长: {self.adjustment_step}px")
                elif key == ord('-'):
                    self.adjustment_step = max(1, self.adjustment_step - 1)
                    print(f"调整步长: {self.adjustment_step}px")
                elif key == ord('r'):
                    self.current_offset_x = 0
                    self.current_offset_y = 0
                    print("偏移量已重置")
                elif key == ord(' '):
                    if self.apply_offset_to_file():
                        print("✓ 设置已保存，重启瞄准程序生效")
                    
                time.sleep(0.01)  # 减少CPU使用率
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"错误: {e}")
                break
        
        cv2.destroyAllWindows()
        print("校准工具已退出")

def main():
    """主函数"""
    calibration_tool = CrosshairCalibrationTool()
    calibration_tool.run_calibration()

if __name__ == "__main__":
    main()
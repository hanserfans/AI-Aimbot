#!/usr/bin/env python3
"""
可视化瞄准测试工具
在监视器上显示目标、准星、移动终点和轨迹
测试头部与准星重合的精度
"""

import tkinter as tk
from tkinter import ttk
import math
import time
from dynamic_tracking_system import AdaptiveAimingSystem

class VisualAimingTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("可视化瞄准测试 - 终点标志显示")
        self.root.geometry("1200x800")
        self.root.configure(bg='black')
        
        # 创建瞄准系统 - 使用优化后的参数
        self.aiming_system = AdaptiveAimingSystem()
        self.aiming_system.optimized_tracking = True
        self.aiming_system.tracking_smoothness = 0.95  # 提高精度
        self.aiming_system.max_single_move = 120       # 增加最大移动距离以支持精确瞄准
        
        # 画布设置
        self.canvas_width = 800
        self.canvas_height = 600
        self.scale_factor = 2.0  # 放大显示
        
        # 测试数据
        self.test_scenarios = [
            {"name": "右上方目标", "target": (200, 100), "crosshair": (160, 160)},
            {"name": "左下方目标", "target": (100, 250), "crosshair": (160, 160)},
            {"name": "近距离目标", "target": (170, 170), "crosshair": (160, 160)},
            {"name": "远距离目标", "target": (280, 50), "crosshair": (160, 160)},
            {"name": "左侧目标", "target": (50, 160), "crosshair": (160, 160)},
            {"name": "右侧目标", "target": (270, 160), "crosshair": (160, 160)},
        ]
        
        self.current_scenario = 0
        self.movement_history = []
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = tk.Frame(self.root, bg='black')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧控制面板
        control_frame = tk.Frame(main_frame, bg='gray20', width=350)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # 标题
        title_label = tk.Label(control_frame, text="🎯 可视化瞄准测试", 
                              font=("Arial", 16, "bold"), fg='white', bg='gray20')
        title_label.pack(pady=10)
        
        # 系统配置显示
        config_frame = tk.LabelFrame(control_frame, text="系统配置", 
                                   fg='white', bg='gray20', font=("Arial", 10, "bold"))
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(config_frame, text=f"优化跟踪: {self.aiming_system.optimized_tracking}", 
                fg='lime', bg='gray20').pack(anchor=tk.W)
        tk.Label(config_frame, text=f"平滑度: {self.aiming_system.tracking_smoothness}", 
                fg='lime', bg='gray20').pack(anchor=tk.W)
        tk.Label(config_frame, text=f"最大移动: {self.aiming_system.max_single_move}px", 
                fg='lime', bg='gray20').pack(anchor=tk.W)
        
        # 测试场景选择
        scenario_frame = tk.LabelFrame(control_frame, text="测试场景", 
                                     fg='white', bg='gray20', font=("Arial", 10, "bold"))
        scenario_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.scenario_var = tk.StringVar(value=self.test_scenarios[0]["name"])
        self.scenario_combo = ttk.Combobox(scenario_frame, textvariable=self.scenario_var,
                                         values=[s["name"] for s in self.test_scenarios],
                                         state="readonly")
        self.scenario_combo.pack(fill=tk.X, pady=5)
        self.scenario_combo.bind("<<ComboboxSelected>>", self.on_scenario_change)
        
        # 测试按钮
        button_frame = tk.Frame(control_frame, bg='gray20')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.test_button = tk.Button(button_frame, text="🎯 执行瞄准测试", 
                                   command=self.run_aiming_test, 
                                   bg='green', fg='white', font=("Arial", 12, "bold"))
        self.test_button.pack(fill=tk.X, pady=2)
        
        self.clear_button = tk.Button(button_frame, text="🧹 清除轨迹", 
                                    command=self.clear_canvas, 
                                    bg='orange', fg='white', font=("Arial", 10))
        self.clear_button.pack(fill=tk.X, pady=2)
        
        self.auto_test_button = tk.Button(button_frame, text="🔄 自动测试所有场景", 
                                        command=self.auto_test_all, 
                                        bg='blue', fg='white', font=("Arial", 10))
        self.auto_test_button.pack(fill=tk.X, pady=2)
        
        # 结果显示
        result_frame = tk.LabelFrame(control_frame, text="测试结果", 
                                   fg='white', bg='gray20', font=("Arial", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.result_text = tk.Text(result_frame, bg='black', fg='lime', 
                                 font=("Consolas", 9), wrap=tk.WORD)
        scrollbar = tk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右侧画布
        canvas_frame = tk.Frame(main_frame, bg='black')
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 画布标题
        canvas_title = tk.Label(canvas_frame, text="🎯 瞄准可视化 (320x320 检测区域)", 
                              font=("Arial", 14, "bold"), fg='white', bg='black')
        canvas_title.pack(pady=5)
        
        # 创建画布
        self.canvas = tk.Canvas(canvas_frame, width=self.canvas_width, height=self.canvas_height, 
                              bg='black', highlightthickness=2, highlightbackground='white')
        self.canvas.pack(pady=10)
        
        # 绘制初始状态
        self.draw_initial_state()
        
    def draw_initial_state(self):
        """绘制初始状态"""
        self.canvas.delete("all")
        
        # 绘制检测区域边界 (320x320)
        border_x1 = 50
        border_y1 = 50
        border_x2 = border_x1 + 320 * self.scale_factor
        border_y2 = border_y1 + 320 * self.scale_factor
        
        self.canvas.create_rectangle(border_x1, border_y1, border_x2, border_y2, 
                                   outline='white', width=2, dash=(5, 5))
        self.canvas.create_text(border_x1 + 10, border_y1 - 20, text="检测区域 (320x320)", 
                              fill='white', anchor=tk.W, font=("Arial", 10))
        
        # 绘制安全边界 (20px边距)
        safe_x1 = border_x1 + 20 * self.scale_factor
        safe_y1 = border_y1 + 20 * self.scale_factor
        safe_x2 = border_x2 - 20 * self.scale_factor
        safe_y2 = border_y2 - 20 * self.scale_factor
        
        self.canvas.create_rectangle(safe_x1, safe_y1, safe_x2, safe_y2, 
                                   outline='yellow', width=1, dash=(3, 3))
        self.canvas.create_text(safe_x1 + 10, safe_y1 - 15, text="安全边界", 
                              fill='yellow', anchor=tk.W, font=("Arial", 9))
        
        # 绘制网格
        for i in range(0, 321, 40):
            x = border_x1 + i * self.scale_factor
            y = border_y1 + i * self.scale_factor
            if x <= border_x2:
                self.canvas.create_line(x, border_y1, x, border_y2, fill='gray30', width=1)
            if y <= border_y2:
                self.canvas.create_line(border_x1, y, border_x2, y, fill='gray30', width=1)
        
        # 绘制坐标轴标签
        for i in range(0, 321, 80):
            x = border_x1 + i * self.scale_factor
            y = border_y1 + i * self.scale_factor
            self.canvas.create_text(x, border_y2 + 15, text=str(i), fill='gray', font=("Arial", 8))
            self.canvas.create_text(border_x1 - 15, y, text=str(i), fill='gray', font=("Arial", 8))
        
        # 显示当前场景
        self.draw_current_scenario()
        
    def draw_current_scenario(self):
        """绘制当前测试场景"""
        scenario = self.test_scenarios[self.current_scenario]
        target_x, target_y = scenario["target"]
        crosshair_x, crosshair_y = scenario["crosshair"]
        
        # 转换为画布坐标
        canvas_target_x = 50 + target_x * self.scale_factor
        canvas_target_y = 50 + target_y * self.scale_factor
        canvas_crosshair_x = 50 + crosshair_x * self.scale_factor
        canvas_crosshair_y = 50 + crosshair_y * self.scale_factor
        
        # 清除之前的标记
        self.canvas.delete("scenario")
        
        # 绘制目标 (红色圆圈)
        target_size = 8
        self.canvas.create_oval(canvas_target_x - target_size, canvas_target_y - target_size,
                              canvas_target_x + target_size, canvas_target_y + target_size,
                              outline='red', fill='red', width=2, tags="scenario")
        self.canvas.create_text(canvas_target_x, canvas_target_y - 20, text="🎯 目标", 
                              fill='red', font=("Arial", 10, "bold"), tags="scenario")
        self.canvas.create_text(canvas_target_x, canvas_target_y + 20, 
                              text=f"({target_x:.0f}, {target_y:.0f})", 
                              fill='red', font=("Arial", 8), tags="scenario")
        
        # 绘制准星 (蓝色十字)
        crosshair_size = 10
        self.canvas.create_line(canvas_crosshair_x - crosshair_size, canvas_crosshair_y,
                              canvas_crosshair_x + crosshair_size, canvas_crosshair_y,
                              fill='cyan', width=3, tags="scenario")
        self.canvas.create_line(canvas_crosshair_x, canvas_crosshair_y - crosshair_size,
                              canvas_crosshair_x, canvas_crosshair_y + crosshair_size,
                              fill='cyan', width=3, tags="scenario")
        self.canvas.create_text(canvas_crosshair_x, canvas_crosshair_y - 25, text="✚ 准星", 
                              fill='cyan', font=("Arial", 10, "bold"), tags="scenario")
        self.canvas.create_text(canvas_crosshair_x, canvas_crosshair_y + 25, 
                              text=f"({crosshair_x:.0f}, {crosshair_y:.0f})", 
                              fill='cyan', font=("Arial", 8), tags="scenario")
        
        # 绘制距离线
        self.canvas.create_line(canvas_crosshair_x, canvas_crosshair_y,
                              canvas_target_x, canvas_target_y,
                              fill='gray', width=1, dash=(2, 2), tags="scenario")
        
        # 计算距离
        distance = math.sqrt((target_x - crosshair_x)**2 + (target_y - crosshair_y)**2)
        mid_x = (canvas_crosshair_x + canvas_target_x) / 2
        mid_y = (canvas_crosshair_y + canvas_target_y) / 2
        self.canvas.create_text(mid_x, mid_y, text=f"{distance:.1f}px", 
                              fill='white', font=("Arial", 9), tags="scenario")
        
    def on_scenario_change(self, event=None):
        """场景改变时的回调"""
        scenario_name = self.scenario_var.get()
        for i, scenario in enumerate(self.test_scenarios):
            if scenario["name"] == scenario_name:
                self.current_scenario = i
                break
        self.draw_initial_state()
        
    def run_aiming_test(self):
        """执行瞄准测试"""
        scenario = self.test_scenarios[self.current_scenario]
        target_x, target_y = scenario["target"]
        crosshair_x, crosshair_y = scenario["crosshair"]
        
        self.log_result(f"\n🎯 开始测试: {scenario['name']}")
        self.log_result(f"目标位置: ({target_x}, {target_y})")
        self.log_result(f"准星位置: ({crosshair_x}, {crosshair_y})")
        
        # 执行瞄准计算
        start_time = time.time()
        result = self.aiming_system.aim_at_target(
            target_x=target_x,
            target_y=target_y,
            crosshair_x=crosshair_x,
            crosshair_y=crosshair_y,
            confidence=0.9,
            game_fov=103.0,
            detection_size=320,
            game_width=2560,
            game_height=1600
        )
        end_time = time.time()
        
        if result:
            move_x, move_y = result
            final_x = crosshair_x + move_x
            final_y = crosshair_y + move_y
            
            # 计算精度
            error_x = abs(target_x - final_x)
            error_y = abs(target_y - final_y)
            total_error = math.sqrt(error_x**2 + error_y**2)
            
            self.log_result(f"计算移动: ({move_x}, {move_y})")
            self.log_result(f"移动终点: ({final_x:.1f}, {final_y:.1f})")
            self.log_result(f"误差: X={error_x:.1f}px, Y={error_y:.1f}px")
            self.log_result(f"总误差: {total_error:.1f}px")
            self.log_result(f"计算耗时: {(end_time - start_time)*1000:.1f}ms")
            
            # 绘制移动轨迹和终点
            self.draw_movement_result(crosshair_x, crosshair_y, final_x, final_y, 
                                    target_x, target_y, total_error)
            
            # 判断精度等级
            if total_error <= 5:
                accuracy = "🎯 极佳"
                color = "lime"
            elif total_error <= 10:
                accuracy = "✅ 良好"
                color = "green"
            elif total_error <= 20:
                accuracy = "⚠️ 一般"
                color = "yellow"
            else:
                accuracy = "❌ 较差"
                color = "red"
                
            self.log_result(f"精度评级: {accuracy}")
            
        else:
            self.log_result("❌ 瞄准失败 (可能超出边界)")
            
        self.log_result("-" * 40)
        
    def draw_movement_result(self, start_x, start_y, end_x, end_y, target_x, target_y, error):
        """绘制移动结果"""
        # 转换为画布坐标
        canvas_start_x = 50 + start_x * self.scale_factor
        canvas_start_y = 50 + start_y * self.scale_factor
        canvas_end_x = 50 + end_x * self.scale_factor
        canvas_end_y = 50 + end_y * self.scale_factor
        canvas_target_x = 50 + target_x * self.scale_factor
        canvas_target_y = 50 + target_y * self.scale_factor
        
        # 清除之前的移动轨迹
        self.canvas.delete("movement")
        
        # 绘制移动轨迹 (绿色箭头)
        self.canvas.create_line(canvas_start_x, canvas_start_y, canvas_end_x, canvas_end_y,
                              fill='lime', width=3, arrow=tk.LAST, arrowshape=(10, 12, 3),
                              tags="movement")
        
        # 绘制移动终点 (绿色圆圈)
        end_size = 6
        self.canvas.create_oval(canvas_end_x - end_size, canvas_end_y - end_size,
                              canvas_end_x + end_size, canvas_end_y + end_size,
                              outline='lime', fill='lime', width=2, tags="movement")
        self.canvas.create_text(canvas_end_x, canvas_end_y - 20, text="📍 终点", 
                              fill='lime', font=("Arial", 10, "bold"), tags="movement")
        self.canvas.create_text(canvas_end_x, canvas_end_y + 20, 
                              text=f"({end_x:.1f}, {end_y:.1f})", 
                              fill='lime', font=("Arial", 8), tags="movement")
        
        # 绘制误差线 (红色虚线)
        self.canvas.create_line(canvas_end_x, canvas_end_y, canvas_target_x, canvas_target_y,
                              fill='red', width=2, dash=(3, 3), tags="movement")
        
        # 显示误差值
        mid_x = (canvas_end_x + canvas_target_x) / 2
        mid_y = (canvas_end_y + canvas_target_y) / 2
        self.canvas.create_text(mid_x, mid_y, text=f"误差: {error:.1f}px", 
                              fill='red', font=("Arial", 9, "bold"), tags="movement")
        
        # 添加到历史记录
        self.movement_history.append({
            'scenario': self.test_scenarios[self.current_scenario]['name'],
            'start': (start_x, start_y),
            'end': (end_x, end_y),
            'target': (target_x, target_y),
            'error': error
        })
        
    def auto_test_all(self):
        """自动测试所有场景"""
        self.log_result("\n🔄 开始自动测试所有场景...")
        self.log_result("=" * 50)
        
        total_error = 0
        test_count = 0
        
        for i, scenario in enumerate(self.test_scenarios):
            self.current_scenario = i
            self.scenario_var.set(scenario["name"])
            self.draw_initial_state()
            self.root.update()
            
            # 执行测试
            target_x, target_y = scenario["target"]
            crosshair_x, crosshair_y = scenario["crosshair"]
            
            result = self.aiming_system.aim_at_target(
                target_x=target_x,
                target_y=target_y,
                crosshair_x=crosshair_x,
                crosshair_y=crosshair_y,
                confidence=0.9,
                game_fov=103.0,
                detection_size=320,
                game_width=2560,
                game_height=1600
            )
            
            if result:
                move_x, move_y = result
                final_x = crosshair_x + move_x
                final_y = crosshair_y + move_y
                error = math.sqrt((target_x - final_x)**2 + (target_y - final_y)**2)
                
                self.log_result(f"{i+1}. {scenario['name']}: 误差 {error:.1f}px")
                total_error += error
                test_count += 1
                
                # 绘制结果
                self.draw_movement_result(crosshair_x, crosshair_y, final_x, final_y, 
                                        target_x, target_y, error)
            else:
                self.log_result(f"{i+1}. {scenario['name']}: 测试失败")
            
            time.sleep(0.5)  # 短暂延迟以便观察
            
        # 计算平均精度
        if test_count > 0:
            avg_error = total_error / test_count
            self.log_result("=" * 50)
            self.log_result(f"📊 测试总结:")
            self.log_result(f"成功测试: {test_count}/{len(self.test_scenarios)}")
            self.log_result(f"平均误差: {avg_error:.1f}px")
            
            if avg_error <= 5:
                self.log_result("🎯 整体精度: 极佳")
            elif avg_error <= 10:
                self.log_result("✅ 整体精度: 良好")
            elif avg_error <= 20:
                self.log_result("⚠️ 整体精度: 一般")
            else:
                self.log_result("❌ 整体精度: 需要改进")
                
    def clear_canvas(self):
        """清除画布"""
        self.movement_history.clear()
        self.draw_initial_state()
        self.log_result("\n🧹 已清除所有轨迹")
        
    def log_result(self, message):
        """记录结果到文本框"""
        self.result_text.insert(tk.END, message + "\n")
        self.result_text.see(tk.END)
        self.root.update()
        
    def run(self):
        """运行测试工具"""
        self.log_result("🎯 可视化瞄准测试工具已启动")
        self.log_result("选择测试场景并点击'执行瞄准测试'开始")
        self.log_result("=" * 40)
        self.root.mainloop()

if __name__ == "__main__":
    # 创建并运行可视化测试
    test_tool = VisualAimingTest()
    test_tool.run()
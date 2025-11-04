#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Aimbot GUI 控制界面
现代化的图形用户界面，支持多种硬件控制方式
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
import json
import serial.tools.list_ports
from pathlib import Path
import time

class AimbotGUI:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_variables()
        self.create_widgets()
        self.load_config()
        self.update_arduino_status()
        
        # 运行状态
        self.is_running = False
        self.current_process = None
        
    def setup_window(self):
        """设置主窗口"""
        self.root.title("AI-Aimbot 控制中心 v2.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 设置图标和样式
        try:
            self.root.iconbitmap("imgs/banner.png")
        except:
            pass
            
        # 配置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义颜色
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2E86AB')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), foreground='#A23B72')
        style.configure('Success.TLabel', foreground='#28A745')
        style.configure('Warning.TLabel', foreground='#FFC107')
        style.configure('Error.TLabel', foreground='#DC3545')
        
    def setup_variables(self):
        """设置变量"""
        # 硬件控制方式
        self.control_method = tk.StringVar(value="ghub")
        
        # 配置参数
        self.confidence = tk.DoubleVar(value=0.4)
        self.movement_amp = tk.DoubleVar(value=0.4)
        self.headshot_mode = tk.BooleanVar(value=True)
        self.game_fov = tk.IntVar(value=103)
        
        # Arduino 状态
        self.arduino_status = tk.StringVar(value="未检测")
        self.arduino_port = tk.StringVar(value="未连接")
        
        # 运行状态
        self.status_text = tk.StringVar(value="就绪")
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="AI-Aimbot 控制中心", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 左侧控制面板
        self.create_control_panel(main_frame)
        
        # 右侧状态面板
        self.create_status_panel(main_frame)
        
        # 底部按钮区域
        self.create_button_panel(main_frame)
        
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制设置", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 硬件控制方式选择
        ttk.Label(control_frame, text="鼠标控制方式:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        methods_frame = ttk.Frame(control_frame)
        methods_frame.grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        ttk.Radiobutton(methods_frame, text="G-Hub 驱动 (推荐)",
                       variable=self.control_method, value="ghub").grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(methods_frame, text="Arduino 硬件 (最安全)",
                       variable=self.control_method, value="arduino").grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(methods_frame, text="Win32 API (测试)",
                       variable=self.control_method, value="win32").grid(row=2, column=0, sticky=tk.W)
        
        # AI 配置参数
        ttk.Label(control_frame, text="AI 配置参数:", style='Header.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(15, 5))
        
        # 置信度
        ttk.Label(control_frame, text="置信度阈值:").grid(row=3, column=0, sticky=tk.W)
        confidence_scale = ttk.Scale(control_frame, from_=0.1, to=0.9, variable=self.confidence, orient=tk.HORIZONTAL)
        confidence_scale.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Label(control_frame, textvariable=self.confidence).grid(row=4, column=1, sticky=tk.W, padx=(10, 0))
        
        # 移动幅度
        ttk.Label(control_frame, text="移动幅度:").grid(row=5, column=0, sticky=tk.W)
        movement_scale = ttk.Scale(control_frame, from_=0.1, to=1.0, variable=self.movement_amp, orient=tk.HORIZONTAL)
        movement_scale.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Label(control_frame, textvariable=self.movement_amp).grid(row=6, column=1, sticky=tk.W, padx=(10, 0))
        
        # 游戏FOV
        ttk.Label(control_frame, text="游戏FOV:").grid(row=7, column=0, sticky=tk.W)
        fov_scale = ttk.Scale(control_frame, from_=60, to=120, variable=self.game_fov, orient=tk.HORIZONTAL)
        fov_scale.grid(row=8, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Label(control_frame, textvariable=self.game_fov).grid(row=8, column=1, sticky=tk.W, padx=(10, 0))
        
        # 爆头模式
        ttk.Checkbutton(control_frame, text="启用爆头模式",
                        variable=self.headshot_mode).grid(row=9, column=0, sticky=tk.W, pady=(10, 0))
        
    def create_status_panel(self, parent):
        """创建状态面板"""
        status_frame = ttk.LabelFrame(parent, text="系统状态", padding="10")
        status_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Arduino 状态
        ttk.Label(status_frame, text="Arduino 状态:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        arduino_frame = ttk.Frame(status_frame)
        arduino_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(arduino_frame, text="连接状态:").grid(row=0, column=0, sticky=tk.W)
        self.arduino_status_label = ttk.Label(arduino_frame, textvariable=self.arduino_status, style='Warning.TLabel')
        self.arduino_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(arduino_frame, text="串口:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(arduino_frame, textvariable=self.arduino_port).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Button(arduino_frame, text="刷新", command=self.update_arduino_status).grid(row=2, column=0, pady=(5, 0))
        ttk.Button(arduino_frame, text="测试连接", command=self.test_arduino).grid(row=2, column=1, pady=(5, 0), padx=(10, 0))
        
        # 运行状态
        ttk.Label(status_frame, text="运行状态:", style='Header.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(15, 5))
        self.status_label = ttk.Label(status_frame, textvariable=self.status_text, style='Success.TLabel')
        self.status_label.grid(row=3, column=0, sticky=tk.W)
        
        # 日志输出
        ttk.Label(status_frame, text="系统日志:", style='Header.TLabel').grid(row=4, column=0, sticky=tk.W, pady=(15, 5))
        
        self.log_text = scrolledtext.ScrolledText(status_frame, height=15, width=40)
        self.log_text.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(5, weight=1)
        
    def create_button_panel(self, parent):
        """创建按钮面板"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))
        
        # 主要控制按钮
        self.start_button = ttk.Button(button_frame, text="启动 AI-Aimbot", 
                                      command=self.start_aimbot, style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="停止", 
                                     command=self.stop_aimbot, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        # 辅助按钮
        ttk.Button(button_frame, text="保存配置", 
                  command=self.save_config).grid(row=0, column=2, padx=(0, 10))
        
        ttk.Button(button_frame, text="打开配置文件", 
                  command=self.open_config_file).grid(row=0, column=3, padx=(0, 10))
        
        ttk.Button(button_frame, text="帮助", 
                  command=self.show_help).grid(row=0, column=4)
        
    def update_arduino_status(self):
        """更新 Arduino 状态"""
        try:
            ports = serial.tools.list_ports.comports()
            arduino_ports = []
            
            for port in ports:
                if any(keyword in port.description.lower() for keyword in ['arduino', 'ch340', 'cp210', 'ftdi']):
                    arduino_ports.append(port.device)
            
            if arduino_ports:
                self.arduino_status.set("已检测到")
                self.arduino_port.set(", ".join(arduino_ports))
                self.arduino_status_label.configure(style='Success.TLabel')
                self.log_message(f"[SUCCESS] 检测到 Arduino 设备: {', '.join(arduino_ports)}")
            else:
                self.arduino_status.set("未检测到")
                self.arduino_port.set("无设备")
                self.arduino_status_label.configure(style='Warning.TLabel')
                self.log_message("[WARNING] 未检测到 Arduino 设备")
                
        except Exception as e:
            self.arduino_status.set("检测失败")
            self.arduino_port.set("错误")
            self.arduino_status_label.configure(style='Error.TLabel')
            self.log_message(f"[ERROR] Arduino 检测失败: {str(e)}")
    
    def test_arduino(self):
        """测试 Arduino 连接"""
        def test_thread():
            try:
                self.log_message("[TEST] 正在测试 Arduino 连接...")
                result = subprocess.run([sys.executable, "test_arduino_connection.py"], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.log_message("[SUCCESS] Arduino 连接测试成功")
                    messagebox.showinfo("测试成功", "Arduino 连接正常！")
                else:
                    self.log_message(f"[ERROR] Arduino 测试失败: {result.stderr}")
                    messagebox.showerror("测试失败", f"Arduino 连接失败:\n{result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.log_message("[TIMEOUT] Arduino 测试超时")
                messagebox.showwarning("测试超时", "Arduino 连接测试超时，请检查设备连接")
            except Exception as e:
                self.log_message(f"[ERROR] 测试异常: {str(e)}")
                messagebox.showerror("测试异常", f"测试过程中发生错误:\n{str(e)}")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def start_aimbot(self):
        """启动 AI-Aimbot"""
        if self.is_running:
            return
            
        # 保存当前配置
        self.save_config()
        
        # 选择启动脚本
        script_map = {
            "ghub": "main_onnx.py",
            "arduino": "customScripts/afyScripts/arduino_leonardo_aimbot.py",
            "win32": "main.py"
        }
        
        script = script_map.get(self.control_method.get(), "main.py")
        
        try:
            self.log_message(f"[START] 启动 AI-Aimbot ({self.control_method.get().upper()} 模式)")
            self.log_message(f"[INFO] 执行脚本: {script}")
            
            # 启动进程
            # 设置环境变量标识GUI模式
            env = os.environ.copy()
            env['AIMBOT_GUI_MODE'] = '1'
            
            self.current_process = subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            
            self.is_running = True
            self.status_text.set("运行中")
            self.status_label.configure(style='Success.TLabel')
            self.start_button.configure(state='disabled')
            self.stop_button.configure(state='normal')
            
            # 启动输出监控线程
            threading.Thread(target=self.monitor_process, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"[ERROR] 启动失败: {str(e)}")
            messagebox.showerror("启动失败", f"无法启动 AI-Aimbot:\n{str(e)}")
    
    def stop_aimbot(self):
        """停止 AI-Aimbot"""
        if not self.is_running or not self.current_process:
            return
            
        try:
            self.log_message("[STOP] 正在停止 AI-Aimbot...")
            self.current_process.terminate()
            
            # 等待进程结束
            try:
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
                self.log_message("[FORCE] 强制终止进程")
            
            self.is_running = False
            self.current_process = None
            self.status_text.set("已停止")
            self.status_label.configure(style='Warning.TLabel')
            self.start_button.configure(state='normal')
            self.stop_button.configure(state='disabled')
            
            self.log_message("[SUCCESS] AI-Aimbot 已停止")
            
        except Exception as e:
            self.log_message(f"[ERROR] 停止失败: {str(e)}")
    
    def monitor_process(self):
        """监控进程输出"""
        if not self.current_process:
            return
            
        try:
            for line in iter(self.current_process.stdout.readline, ''):
                if line:
                    self.log_message(line.strip())
                    
                if self.current_process.poll() is not None:
                    break
                    
        except Exception as e:
            self.log_message(f"[ERROR] 进程监控异常: {str(e)}")
        
        # 进程结束处理
        if self.is_running:
            self.root.after(0, self.on_process_ended)
    
    def on_process_ended(self):
        """进程结束回调"""
        self.is_running = False
        self.current_process = None
        self.status_text.set("已结束")
        self.status_label.configure(style='Warning.TLabel')
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.log_message("[INFO] AI-Aimbot 进程已结束")
    
    def save_config(self):
        """保存配置"""
        config = {
            "control_method": self.control_method.get(),
            "confidence": self.confidence.get(),
            "movement_amp": self.movement_amp.get(),
            "headshot_mode": self.headshot_mode.get(),
            "game_fov": self.game_fov.get()
        }
        
        try:
            with open("gui_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.log_message("[SAVE] 配置已保存")
        except Exception as e:
            self.log_message(f"[ERROR] 保存配置失败: {str(e)}")
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists("gui_config.json"):
                with open("gui_config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                self.control_method.set(config.get("control_method", "ghub"))
                self.confidence.set(config.get("confidence", 0.4))
                self.movement_amp.set(config.get("movement_amp", 0.4))
                self.headshot_mode.set(config.get("headshot_mode", True))
                self.game_fov.set(config.get("game_fov", 103))
                
                self.log_message("[LOAD] 配置已加载")
        except Exception as e:
            self.log_message(f"[ERROR] 加载配置失败: {str(e)}")
    
    def open_config_file(self):
        """打开配置文件"""
        try:
            if os.path.exists("config.py"):
                os.startfile("config.py")
            else:
                messagebox.showwarning("文件不存在", "config.py 文件不存在")
        except Exception as e:
            messagebox.showerror("打开失败", f"无法打开配置文件:\n{str(e)}")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
AI-Aimbot 控制中心使用指南

鼠标控制方式:
• G-Hub 驱动: 需要安装 Logitech G-Hub 软件，使用右键激活
• Arduino 硬件: 最安全的方式，需要连接 Arduino 设备，使用 Caps Lock 激活
• Win32 API: 测试模式，使用 Caps Lock 激活

AI 配置参数:
• 置信度阈值: 目标检测的最低置信度 (0.1-0.9)
• 移动幅度: 鼠标移动的强度 (0.1-1.0)
• 爆头模式: 优先瞄准头部区域

Arduino 设置:
1. 连接 Arduino 到电脑
2. 烧录对应的固件 (arduino_firmware 文件夹)
3. 点击"刷新"检测设备
4. 点击"测试连接"验证通信

注意事项:
• 请在合适的环境下使用
• 建议先在测试环境中验证功能
• Arduino 方案提供最高的安全性
        """
        
        messagebox.showinfo("使用帮助", help_text)
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.root.after(0, lambda: self._append_log(log_entry))
    
    def _append_log(self, message):
        """在主线程中添加日志"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        
        # 限制日志行数
        lines = self.log_text.get("1.0", tk.END).split("\n")
        if len(lines) > 100:
            self.log_text.delete("1.0", f"{len(lines)-100}.0")

def main():
    """主函数"""
    root = tk.Tk()
    app = AimbotGUI(root)
    
    # 优雅退出处理
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("退出确认", "AI-Aimbot 正在运行，确定要退出吗？"):
                app.stop_aimbot()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 启动消息
    app.log_message("[INIT] AI-Aimbot 控制中心已启动")
    app.log_message("[INFO] 请选择控制方式并配置参数")
    
    root.mainloop()

if __name__ == "__main__":
    main()
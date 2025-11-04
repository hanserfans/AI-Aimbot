#!/usr/bin/env python3
"""
Arduino Leonardo 固件烧录助手
自动检测Arduino设备并提供烧录指导
"""

import serial
import serial.tools.list_ports
import subprocess
import os
import sys
import time
from pathlib import Path

class ArduinoFirmwareBurner:
    def __init__(self):
        self.arduino_port = None
        self.firmware_path = Path("arduino_firmware/arduino_leonardo_mouse.ino")
        
    def find_arduino_device(self):
        """查找Arduino Leonardo设备"""
        print("🔍 正在扫描Arduino设备...")
        
        ports = serial.tools.list_ports.comports()
        arduino_keywords = ['arduino', 'leonardo', 'pro micro']
        
        found_devices = []
        for port in ports:
            description_lower = port.description.lower()
            if any(keyword in description_lower for keyword in arduino_keywords):
                found_devices.append({
                    'port': port.device,
                    'description': port.description,
                    'vid_pid': f"{port.vid:04X}:{port.pid:04X}" if port.vid and port.pid else "Unknown"
                })
        
        if not found_devices:
            print("❌ 未找到Arduino Leonardo设备")
            print("\n可用串口设备:")
            for port in ports:
                print(f"  📍 {port.device} - {port.description}")
            return False
        
        print(f"✅ 找到 {len(found_devices)} 个Arduino设备:")
        for i, device in enumerate(found_devices, 1):
            print(f"  {i}. {device['port']} - {device['description']} ({device['vid_pid']})")
        
        if len(found_devices) == 1:
            self.arduino_port = found_devices[0]['port']
            print(f"🎯 自动选择设备: {self.arduino_port}")
        else:
            while True:
                try:
                    choice = int(input(f"\n请选择设备 (1-{len(found_devices)}): ")) - 1
                    if 0 <= choice < len(found_devices):
                        self.arduino_port = found_devices[choice]['port']
                        break
                    else:
                        print("❌ 无效选择，请重试")
                except ValueError:
                    print("❌ 请输入数字")
        
        return True
    
    def check_firmware_file(self):
        """检查固件文件是否存在"""
        if not self.firmware_path.exists():
            print(f"❌ 固件文件不存在: {self.firmware_path}")
            return False
        
        print(f"✅ 固件文件已找到: {self.firmware_path}")
        return True
    
    def test_current_firmware(self):
        """测试当前固件状态"""
        print(f"\n🧪 测试当前固件状态 ({self.arduino_port})...")
        
        try:
            with serial.Serial(self.arduino_port, 9600, timeout=2) as ser:
                time.sleep(2)  # 等待Arduino重启
                
                # 发送状态查询
                ser.write(b'STATUS\\n')
                response = ser.readline().decode().strip()
                
                if response == "OK":
                    print("✅ 当前固件正常工作")
                    return True
                else:
                    print(f"❌ 固件响应异常: '{response}'")
                    return False
                    
        except Exception as e:
            print(f"❌ 固件测试失败: {e}")
            return False
    
    def check_arduino_ide(self):
        """检查Arduino IDE是否安装"""
        print("\n🔍 检查Arduino IDE...")
        
        # 常见的Arduino IDE安装路径
        possible_paths = [
            "C:\\Program Files\\Arduino IDE\\Arduino IDE.exe",
            "C:\\Program Files (x86)\\Arduino IDE\\Arduino IDE.exe",
            "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Arduino IDE\\Arduino IDE.exe",
            "arduino-cli.exe"  # 命令行版本
        ]
        
        for path in possible_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                print(f"✅ 找到Arduino IDE: {expanded_path}")
                return expanded_path
        
        print("❌ 未找到Arduino IDE")
        return None
    
    def provide_manual_instructions(self):
        """提供手动烧录指导"""
        print("\n" + "="*60)
        print("📋 手动烧录指导")
        print("="*60)
        
        print(f"""
🔧 烧录步骤:

1. 打开Arduino IDE
2. 选择开发板: 工具 → 开发板 → Arduino Leonardo
3. 选择端口: 工具 → 端口 → {self.arduino_port}
4. 打开固件文件: {self.firmware_path.absolute()}
5. 点击上传按钮 (→)

⚠️  如果上传失败:
- 按住Arduino的Reset按钮，然后点击上传
- 确保USB线是数据线（非充电线）
- 尝试不同的USB端口

✅ 烧录完成后运行测试:
   python test_arduino_connection.py
""")
    
    def run_post_burn_test(self):
        """烧录后测试"""
        print("\n🧪 正在进行烧录后测试...")
        
        input("请按Enter键开始测试（确保固件已烧录完成）...")
        
        if self.test_current_firmware():
            print("🎉 固件烧录成功！Arduino驱动已就绪")
            
            # 运行完整测试
            try:
                print("\n🚀 运行完整连接测试...")
                result = subprocess.run([sys.executable, "test_arduino_connection.py"], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ Arduino连接测试通过")
                else:
                    print(f"⚠️  测试警告: {result.stderr}")
                    
            except Exception as e:
                print(f"⚠️  无法运行自动测试: {e}")
                print("请手动运行: python test_arduino_connection.py")
        else:
            print("❌ 固件测试失败，请检查烧录过程")
    
    def run(self):
        """主运行流程"""
        print("🎯 Arduino Leonardo 固件烧录助手")
        print("="*50)
        
        # 1. 检查固件文件
        if not self.check_firmware_file():
            return
        
        # 2. 查找Arduino设备
        if not self.find_arduino_device():
            print("\n💡 请确保:")
            print("  - Arduino Leonardo已连接到电脑")
            print("  - 使用的是数据线（非充电线）")
            print("  - 设备驱动已正确安装")
            return
        
        # 3. 测试当前固件
        firmware_ok = self.test_current_firmware()
        
        if firmware_ok:
            print("\n🤔 当前固件似乎正常工作")
            choice = input("是否仍要重新烧录固件? (y/N): ").lower()
            if choice not in ['y', 'yes']:
                print("✅ 保持当前固件，无需烧录")
                return
        
        # 4. 检查Arduino IDE
        arduino_ide = self.check_arduino_ide()
        
        if arduino_ide:
            print(f"\n🚀 可以使用Arduino IDE进行烧录")
            choice = input("是否打开Arduino IDE? (Y/n): ").lower()
            if choice not in ['n', 'no']:
                try:
                    subprocess.Popen([arduino_ide])
                    print("✅ Arduino IDE已启动")
                except Exception as e:
                    print(f"❌ 启动Arduino IDE失败: {e}")
        
        # 5. 提供手动指导
        self.provide_manual_instructions()
        
        # 6. 烧录后测试
        self.run_post_burn_test()

def main():
    try:
        burner = ArduinoFirmwareBurner()
        burner.run()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("请查看Arduino固件烧录指南.md获取详细帮助")

if __name__ == "__main__":
    main()
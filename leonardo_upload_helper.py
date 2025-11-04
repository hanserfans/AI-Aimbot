#!/usr/bin/env python3
"""
Arduino Leonardo 烧录助手
专门解决Leonardo烧录连接问题
"""

import serial
import time
import subprocess
import os
from pathlib import Path

class LeonardoUploadHelper:
    def __init__(self):
        self.port = "COM6"
        self.firmware_path = Path("arduino_firmware/arduino_leonardo_mouse/arduino_leonardo_mouse.ino").absolute()
        
    def check_port_status(self):
        """检查端口状态"""
        try:
            ser = serial.Serial(self.port, 9600, timeout=1)
            ser.close()
            return True
        except Exception as e:
            print(f"❌ 端口检查失败: {e}")
            return False
    
    def wait_for_bootloader(self):
        """等待bootloader模式"""
        print("🔄 等待Arduino进入bootloader模式...")
        print("请按照以下步骤操作：")
        print("1. 快速双击Arduino板上的Reset按钮")
        print("2. 或者按住Reset按钮，然后点击上传，再松开Reset")
        
        # 监控端口变化
        for i in range(10):
            try:
                ser = serial.Serial(self.port, 1200, timeout=0.1)
                ser.close()
                time.sleep(0.1)
                print(f"⏳ 等待bootloader... ({i+1}/10)")
                time.sleep(1)
            except:
                print("🎯 检测到bootloader模式!")
                return True
        
        return False
    
    def upload_with_avrdude(self):
        """使用avrdude直接烧录"""
        hex_file = self.firmware_path.with_suffix('.hex')
        
        if not hex_file.exists():
            print("❌ 需要先编译固件生成.hex文件")
            return False
        
        cmd = [
            "avrdude",
            "-C", "avrdude.conf",
            "-v",
            "-p", "atmega32u4",
            "-c", "avr109",
            "-P", self.port,
            "-b", "57600",
            "-D",
            "-U", f"flash:w:{hex_file}:i"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ 烧录成功!")
                return True
            else:
                print(f"❌ 烧录失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ avrdude执行失败: {e}")
            return False
    
    def provide_manual_guide(self):
        """提供手动烧录指导"""
        print("\n" + "="*60)
        print("🎯 Arduino Leonardo 手动烧录指导")
        print("="*60)
        
        print(f"\n📁 固件文件: {self.firmware_path}")
        print(f"🔌 目标端口: {self.port}")
        
        print("\n🔧 烧录步骤:")
        print("1. 打开Arduino IDE")
        print("2. 文件 → 打开 → 选择固件文件")
        print("3. 工具 → 板子 → Arduino Leonardo")
        print("4. 工具 → 端口 → COM6")
        
        print("\n⚡ 关键时序操作:")
        print("方法A (推荐):")
        print("  1. 点击'上传'按钮")
        print("  2. 立即按住Reset按钮")
        print("  3. 看到'正在上传...'时松开Reset")
        
        print("\n方法B:")
        print("  1. 快速双击Reset按钮")
        print("  2. 在8秒内点击'上传'按钮")
        
        print("\n⚠️  如果失败:")
        print("- 检查USB线是数据线")
        print("- 重新插拔USB")
        print("- 重启Arduino IDE")
        
        print("\n✅ 成功标志:")
        print("- 看到'Done uploading.'")
        print("- 没有avrdude错误信息")
        
    def test_connection_after_upload(self):
        """烧录后测试连接"""
        print("\n🧪 测试Arduino连接...")
        time.sleep(2)  # 等待Arduino重启
        
        try:
            ser = serial.Serial(self.port, 9600, timeout=2)
            ser.write(b"STATUS\n")
            response = ser.readline().decode().strip()
            ser.close()
            
            if response == "OK":
                print("✅ Arduino固件测试成功!")
                print("✅ 设备已准备就绪")
                return True
            else:
                print(f"❌ 固件响应异常: {response}")
                return False
                
        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
            return False
    
    def run(self):
        """运行烧录助手"""
        print("🎯 Arduino Leonardo 烧录助手")
        print("="*50)
        
        # 检查固件文件
        if not self.firmware_path.exists():
            print(f"❌ 固件文件不存在: {self.firmware_path}")
            return
        
        print(f"✅ 固件文件: {self.firmware_path}")
        
        # 检查端口
        if not self.check_port_status():
            print("❌ 无法访问COM6端口")
            return
        
        print(f"✅ 检测到设备: {self.port}")
        
        # 提供手动指导
        self.provide_manual_guide()
        
        # 等待用户完成烧录
        input("\n按Enter键继续测试连接（确保已完成烧录）...")
        
        # 测试连接
        if self.test_connection_after_upload():
            print("\n🎉 Arduino Leonardo 烧录完成!")
            print("现在可以运行: python test_arduino_connection.py")
        else:
            print("\n❌ 烧录可能未成功，请重试")

if __name__ == "__main__":
    helper = LeonardoUploadHelper()
    helper.run()
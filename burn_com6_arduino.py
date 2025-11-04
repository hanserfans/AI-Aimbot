#!/usr/bin/env python3
"""
COM6 Arduino Leonardo 固件烧录助手
专门针对COM6端口的Arduino设备
"""

import serial
import time
import os
import subprocess
import sys
from pathlib import Path

def test_com6_firmware():
    """测试COM6端口的Arduino固件状态"""
    print("🧪 测试COM6端口Arduino固件...")
    
    try:
        with serial.Serial('COM6', 9600, timeout=3) as ser:
            time.sleep(2)  # 等待Arduino重启
            
            # 发送状态查询
            ser.write(b'STATUS\n')
            response = ser.readline().decode().strip()
            
            print(f"固件响应: '{response}'")
            
            if response == "OK":
                print("✅ 固件正常工作")
                return True
            else:
                print("❌ 固件响应异常，需要重新烧录")
                return False
                
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

def check_arduino_ide():
    """检查Arduino IDE是否可用"""
    print("🔍 检查Arduino IDE...")
    
    # 常见Arduino IDE路径
    ide_paths = [
        "C:\\Program Files\\Arduino IDE\\Arduino IDE.exe",
        "C:\\Program Files (x86)\\Arduino IDE\\Arduino IDE.exe",
        "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Arduino IDE\\Arduino IDE.exe"
    ]
    
    for path in ide_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            print(f"✅ 找到Arduino IDE: {expanded_path}")
            return expanded_path
    
    print("❌ 未找到Arduino IDE")
    return None

def provide_burning_guide():
    """提供详细的烧录指导"""
    firmware_path = Path("arduino_firmware/arduino_leonardo_mouse/arduino_leonardo_mouse.ino").absolute()
    
    print("\n" + "="*60)
    print("📋 COM6 Arduino Leonardo 烧录指导")
    print("="*60)
    
    print(f"""
🎯 设备信息:
   端口: COM6
   设备: Arduino Leonardo (2341:8036)
   固件: {firmware_path}

🔧 烧录步骤:

1. 打开Arduino IDE
2. 配置设备:
   - 工具 → 开发板 → Arduino Leonardo
   - 工具 → 端口 → COM6 (Arduino Leonardo)
3. 打开固件文件:
   - 文件 → 打开 → {firmware_path}
4. 上传固件:
   - 点击上传按钮 (→)

⚠️  如果上传失败:
   方法1: 按住Reset按钮，然后点击上传
   方法2: 快速双击Reset按钮，立即点击上传
   方法3: 检查USB线是数据线（非充电线）

✅ 烧录完成后运行测试:
   python test_arduino_connection.py
""")

def run_post_burn_test():
    """烧录后测试"""
    print("\n🧪 烧录后测试...")
    
    input("请按Enter键开始测试（确保固件已烧录完成）...")
    
    if test_com6_firmware():
        print("🎉 固件烧录成功！")
        
        # 运行完整测试
        try:
            print("\n🚀 运行完整连接测试...")
            result = subprocess.run([sys.executable, "test_arduino_connection.py"], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Arduino连接测试通过")
                print("🎯 Arduino驱动已就绪，可以在AI-Aimbot中使用！")
            else:
                print(f"⚠️  测试输出: {result.stdout}")
                
        except Exception as e:
            print(f"⚠️  无法运行自动测试: {e}")
            print("请手动运行: python test_arduino_connection.py")
    else:
        print("❌ 固件测试失败，请重新检查烧录过程")

def main():
    """主函数"""
    print("🎯 COM6 Arduino Leonardo 固件烧录助手")
    print("="*50)
    
    # 检查固件文件
    firmware_path = Path("arduino_firmware/arduino_leonardo_mouse/arduino_leonardo_mouse.ino")
    if not firmware_path.exists():
        print(f"❌ 固件文件不存在: {firmware_path}")
        return
    
    print(f"✅ 固件文件: {firmware_path}")
    
    # 测试当前固件
    firmware_ok = test_com6_firmware()
    
    if firmware_ok:
        print("\n🤔 当前固件似乎正常工作")
        choice = input("是否仍要重新烧录固件? (y/N): ").lower()
        if choice not in ['y', 'yes']:
            print("✅ 保持当前固件，无需烧录")
            return
    
    # 检查Arduino IDE
    arduino_ide = check_arduino_ide()
    
    if arduino_ide:
        print(f"\n🚀 可以使用Arduino IDE进行烧录")
        choice = input("是否打开Arduino IDE? (Y/n): ").lower()
        if choice not in ['n', 'no']:
            try:
                subprocess.Popen([arduino_ide])
                print("✅ Arduino IDE已启动")
            except Exception as e:
                print(f"❌ 启动Arduino IDE失败: {e}")
    
    # 提供烧录指导
    provide_burning_guide()
    
    # 烧录后测试
    run_post_burn_test()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("请查看 烧录COM6设备.md 获取详细帮助")
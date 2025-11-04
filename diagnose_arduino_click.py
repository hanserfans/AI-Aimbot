#!/usr/bin/env python3
"""
Arduino 点击功能诊断脚本
用于测试Arduino串口通信和鼠标点击功能
"""

import serial
import serial.tools.list_ports
import time
import sys

def find_arduino_ports():
    """查找所有可能的Arduino端口"""
    arduino_ports = []
    ports = serial.tools.list_ports.comports()
    
    print("=== 扫描串口设备 ===")
    for port in ports:
        print(f"端口: {port.device}")
        print(f"  描述: {port.description}")
        print(f"  硬件ID: {port.hwid}")
        
        # 检查是否为Arduino设备
        if any(keyword in port.description.lower() for keyword in ['arduino', 'ch340', 'ch341', 'ftdi', 'usb serial']):
            arduino_ports.append(port.device)
            print(f"  ✓ 可能的Arduino设备")
        print()
    
    return arduino_ports

def test_arduino_connection(port, baudrate=9600):
    """测试Arduino连接和基本通信"""
    print(f"=== 测试端口 {port} ===")
    
    try:
        # 建立连接
        ser = serial.Serial(port, baudrate, timeout=2)
        print(f"✓ 串口连接成功: {port}")
        
        # 等待Arduino重启
        print("等待Arduino初始化...")
        time.sleep(3)
        
        # 清空缓冲区
        ser.flushInput()
        ser.flushOutput()
        
        # 测试STATUS命令
        print("发送STATUS命令...")
        ser.write(b'STATUS\n')
        time.sleep(0.5)
        
        response = ser.readline().decode().strip()
        print(f"Arduino响应: '{response}'")
        
        if response == "OK":
            print("✓ Arduino STATUS测试通过")
            return ser
        else:
            print(f"✗ Arduino响应异常: '{response}'")
            ser.close()
            return None
            
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return None

def test_click_commands(ser):
    """测试点击命令"""
    print("\n=== 测试点击命令 ===")
    
    click_tests = [
        ('CL\n', '左键点击'),
        ('CR\n', '右键点击'),
        ('CM\n', '中键点击')
    ]
    
    for command, description in click_tests:
        print(f"\n测试 {description}...")
        print(f"发送命令: '{command.strip()}'")
        
        try:
            # 清空缓冲区
            ser.flushInput()
            ser.flushOutput()
            
            # 发送命令
            ser.write(command.encode())
            time.sleep(0.2)
            
            # 读取响应
            response = ser.readline().decode().strip()
            print(f"Arduino响应: '{response}'")
            
            # 检查响应
            expected_responses = {
                'CL\n': 'Left Click',
                'CR\n': 'Right Click', 
                'CM\n': 'Middle Click'
            }
            
            if response == expected_responses[command]:
                print(f"✓ {description} 测试通过")
            else:
                print(f"✗ {description} 响应异常")
                
        except Exception as e:
            print(f"✗ {description} 测试失败: {e}")
        
        time.sleep(0.5)

def test_invalid_commands(ser):
    """测试无效命令处理"""
    print("\n=== 测试无效命令处理 ===")
    
    invalid_tests = [
        ('CX\n', '无效点击命令'),
        ('INVALID\n', '完全无效命令'),
        ('C\n', '空点击命令')
    ]
    
    for command, description in invalid_tests:
        print(f"\n测试 {description}...")
        print(f"发送命令: '{command.strip()}'")
        
        try:
            ser.flushInput()
            ser.flushOutput()
            
            ser.write(command.encode())
            time.sleep(0.2)
            
            response = ser.readline().decode().strip()
            print(f"Arduino响应: '{response}'")
            
            if "ERROR" in response:
                print(f"✓ {description} 正确返回错误")
            else:
                print(f"? {description} 响应: '{response}'")
                
        except Exception as e:
            print(f"✗ {description} 测试失败: {e}")

def main():
    print("Arduino 点击功能诊断工具")
    print("=" * 50)
    
    # 查找Arduino端口
    arduino_ports = find_arduino_ports()
    
    if not arduino_ports:
        print("✗ 未找到Arduino设备")
        print("\n请检查:")
        print("1. Arduino是否正确连接到电脑")
        print("2. Arduino驱动是否已安装")
        print("3. Arduino是否已烧录正确的固件")
        return
    
    print(f"找到 {len(arduino_ports)} 个可能的Arduino设备: {arduino_ports}")
    
    # 测试每个端口
    for port in arduino_ports:
        ser = test_arduino_connection(port)
        
        if ser:
            print(f"✓ Arduino连接成功: {port}")
            
            # 测试点击命令
            test_click_commands(ser)
            
            # 测试无效命令
            test_invalid_commands(ser)
            
            # 关闭连接
            ser.close()
            print(f"\n✓ 端口 {port} 测试完成")
            break
    else:
        print("✗ 所有端口测试失败")
        print("\n可能的问题:")
        print("1. Arduino固件未正确烧录")
        print("2. 串口波特率不匹配")
        print("3. Arduino硬件故障")

if __name__ == "__main__":
    main()
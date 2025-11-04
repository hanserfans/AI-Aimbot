# Arduino 硬件安装指南

## 🎯 概述

本指南将帮助你完成 Arduino 硬件与 AI-Aimbot 的集成配置，实现最安全的外部硬件鼠标控制。

## 📋 硬件要求

### 推荐硬件（支持 USB HID）
- ✅ **Arduino Leonardo** - 最佳选择
- ✅ **Arduino Pro Micro** - 小巧便携
- ✅ **Arduino Micro** - 原生 HID 支持

### 备选硬件（需要额外配置）
- ⚠️ **Arduino Uno/Nano** - 需要串口 + 软件配合
- ⚠️ **ESP32** - WiFi 无线方案

## 🔧 安装步骤

### 第一步：准备 Arduino IDE

1. **下载 Arduino IDE**
   - 访问：https://www.arduino.cc/en/software
   - 下载并安装最新版本

2. **安装必要的库**
   ```
   工具 -> 管理库 -> 搜索并安装：
   - Mouse (Arduino 内置)
   - Keyboard (Arduino 内置)
   ```

### 第二步：烧录固件

#### 方案A：Arduino Leonardo/Pro Micro（推荐）

1. **连接 Arduino**
   - 使用 USB 线连接 Arduino 到电脑
   - 等待驱动自动安装

2. **配置 Arduino IDE**
   ```
   工具 -> 开发板 -> Arduino Leonardo
   工具 -> 端口 -> 选择对应的 COM 端口
   ```

3. **烧录固件**
   - 打开文件：`arduino_firmware/arduino_leonardo_mouse.ino`
   - 点击"上传"按钮
   - 等待烧录完成

#### 方案B：Arduino Uno/Nano

1. **配置 Arduino IDE**
   ```
   工具 -> 开发板 -> Arduino Uno
   工具 -> 端口 -> 选择对应的 COM 端口
   ```

2. **烧录固件**
   - 打开文件：`arduino_firmware/arduino_uno_serial.ino`
   - 点击"上传"按钮

### 第三步：安装 Python 依赖

```bash
# 进入 AI-Aimbot 目录
cd f:/git/AI-Aimbot

# 安装串口通信库
pip install pyserial

# 验证安装
python -c "import serial; print('Serial library installed successfully')"
```

### 第四步：测试连接

#### 测试 Arduino Leonardo

1. **运行测试脚本**
   ```bash
   python customScripts/afyScripts/arduino_leonardo_aimbot.py
   ```

2. **预期输出**
   ```
   找到 Arduino 设备: COM3 - Arduino Leonardo
   Arduino 连接成功: COM3
   AI-Aimbot Arduino 版本启动成功!
   按住 Caps Lock 激活自动瞄准
   按 F2 退出程序
   ```

#### 测试 Arduino Uno

1. **打开串口监视器**
   - Arduino IDE -> 工具 -> 串口监视器
   - 波特率设置为 9600

2. **发送测试命令**
   ```
   STATUS    -> 应该返回 "OK"
   M10,5     -> 应该返回 "MOVE:10,5"
   TEST      -> 应该返回 "Arduino Uno Serial Test OK"
   ```

## 🎮 使用方法

### Arduino Leonardo 使用

1. **启动程序**
   ```bash
   python customScripts/afyScripts/arduino_leonardo_aimbot.py
   ```

2. **操作说明**
   - **Caps Lock**: 激活自动瞄准
   - **F2**: 退出程序
   - Arduino 会自动控制鼠标移动

### Arduino Uno 使用

Arduino Uno 需要配合额外的鼠标控制软件使用，因为它不支持原生 HID。

## 🔍 故障排除

### 常见问题

#### 1. 找不到 Arduino 设备
```
错误: 未找到 Arduino 设备，请检查连接
```

**解决方案：**
- 检查 USB 连接
- 重新安装 Arduino 驱动
- 尝试不同的 USB 端口

#### 2. 串口权限错误
```
Arduino 连接失败: [Errno 13] Permission denied: '/dev/ttyACM0'
```

**解决方案：**
- Windows: 以管理员身份运行
- Linux: `sudo usermod -a -G dialout $USER`

#### 3. Arduino 无响应
```
Arduino 响应异常: 
```

**解决方案：**
- 重新烧录固件
- 检查波特率设置（9600）
- 重启 Arduino

### 调试技巧

1. **查看可用串口**
   ```python
   import serial.tools.list_ports
   ports = serial.tools.list_ports.comports()
   for port in ports:
       print(f"{port.device} - {port.description}")
   ```

2. **手动测试串口**
   ```python
   import serial
   ser = serial.Serial('COM3', 9600, timeout=1)
   ser.write(b'STATUS\n')
   print(ser.readline().decode())
   ```

## 🛡️ 安全优势

### 为什么选择 Arduino？

1. **物理隔离**
   - Arduino 作为独立的 USB HID 设备
   - 游戏无法检测到与软件的关联

2. **硬件级控制**
   - 真实的鼠标输入信号
   - 与人工操作完全相同

3. **无法检测**
   - 游戏只能看到标准的鼠标移动
   - 没有软件注入痕迹

## 📊 性能对比

| 控制方式 | 延迟 | 安全性 | 检测难度 | 成本 |
|---------|------|--------|----------|------|
| Win32 API | ~1ms | ⭐⭐ | 容易 | 免费 |
| G-Hub 驱动 | ~2ms | ⭐⭐⭐⭐ | 困难 | 需要设备 |
| **Arduino** | ~5ms | ⭐⭐⭐⭐⭐ | **几乎不可能** | $10-30 |

## 🎯 下一步

1. **选择你的 Arduino 型号**
2. **按照对应的方案进行配置**
3. **测试连接和功能**
4. **享受最安全的自动瞄准体验！**

---

## 📞 技术支持

如果遇到问题，请检查：
1. Arduino 固件是否正确烧录
2. Python 依赖是否正确安装
3. 串口连接是否正常
4. 防火墙是否阻止了串口通信

**祝你使用愉快！** 🎮
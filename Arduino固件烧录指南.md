# 🔧 Arduino Leonardo 固件烧录指南

## 📋 准备工作

### 1. 硬件要求
- **Arduino Leonardo** 或 **Pro Micro** (必须支持HID功能)
- USB数据线（非充电线）
- Windows 10/11 系统

### 2. 软件要求
- **Arduino IDE** (推荐版本 2.0+)
- Arduino Leonardo 驱动程序

## 🚀 烧录步骤

### 步骤1: 安装Arduino IDE

1. 访问 [Arduino官网](https://www.arduino.cc/en/software)
2. 下载并安装 Arduino IDE 2.0+
3. 启动Arduino IDE

### 步骤2: 连接Arduino设备

1. 使用USB线连接Arduino Leonardo到电脑
2. 等待Windows自动安装驱动
3. 在设备管理器中确认设备显示为 "Arduino Leonardo (COMx)"

### 步骤3: 配置Arduino IDE

1. 打开Arduino IDE
2. 选择 **工具 → 开发板 → Arduino AVR Boards → Arduino Leonardo**
3. 选择 **工具 → 端口 → COMx (Arduino Leonardo)**
   - 注意：端口号应该与设备管理器中显示的一致

### 步骤4: 打开固件文件

1. 在Arduino IDE中选择 **文件 → 打开**
2. 导航到项目目录：`f:\git\AI-Aimbot\arduino_firmware\`
3. 选择并打开 `arduino_leonardo_mouse.ino`

### 步骤5: 编译和上传

1. 点击 **验证** 按钮 (✓) 编译代码
2. 确保编译无错误
3. 点击 **上传** 按钮 (→) 烧录固件
4. 等待上传完成（状态栏显示"上传完成"）

## ✅ 验证烧录结果

### 方法1: 使用测试脚本
```bash
cd f:\git\AI-Aimbot
python test_arduino_connection.py
```

### 方法2: 手动测试
1. 打开Arduino IDE的串口监视器
2. 设置波特率为 **9600**
3. 发送命令测试：
   - `STATUS` → 应该返回 `OK`
   - `M10,-5` → 应该移动鼠标
   - `CL` → 应该执行左键点击

## 🔧 故障排除

### 问题1: 找不到端口
**解决方案：**
- 检查USB线是否为数据线（非充电线）
- 重新插拔USB连接
- 在设备管理器中检查驱动状态

### 问题2: 上传失败
**解决方案：**
- 按住Arduino上的Reset按钮，然后点击上传
- 确保选择了正确的开发板类型
- 尝试不同的USB端口

### 问题3: 编译错误
**解决方案：**
- 确保Arduino IDE版本为2.0+
- 检查是否选择了Arduino Leonardo开发板
- 重新安装Arduino AVR Boards包

### 问题4: 固件无响应
**解决方案：**
- 重新烧录固件
- 检查串口波特率设置（应为9600）
- 确认Arduino Leonardo支持Mouse库

## 📊 固件功能说明

### 支持的命令
| 命令格式 | 功能 | 示例 |
|---------|------|------|
| `STATUS` | 状态查询 | `STATUS` → `OK` |
| `M<x>,<y>` | 鼠标移动 | `M10,-5` → 向右10像素，向上5像素 |
| `CL` | 左键点击 | `CL` → 执行左键点击 |
| `CR` | 右键点击 | `CR` → 执行右键点击 |
| `CM` | 中键点击 | `CM` → 执行中键点击 |

### 技术特性
- **硬件级HID控制**：直接作为USB鼠标设备
- **原生精度**：无需软件修正，1:1像素精确控制
- **低延迟**：硬件级响应，延迟极低
- **安全范围限制**：移动范围限制在±127像素内

## 🎯 集成到AI-Aimbot

烧录完成后，Arduino驱动将自动集成到AI-Aimbot系统中：

1. **优先级最高**：Arduino > G-Hub > Win32 API
2. **自动检测**：系统启动时自动检测Arduino设备
3. **无缝切换**：Arduino不可用时自动切换到备选方案
4. **状态显示**：实时显示当前使用的鼠标控制方法

## 📞 技术支持

如果遇到问题，请：
1. 检查本指南的故障排除部分
2. 确认硬件连接正常
3. 验证Arduino IDE配置正确
4. 联系技术支持获取帮助

---
**注意**：Arduino Leonardo是唯一推荐的型号，因为它原生支持USB HID功能。Arduino Uno等型号不支持鼠标控制功能。
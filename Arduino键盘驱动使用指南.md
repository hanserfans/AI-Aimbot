# Arduino 键盘驱动使用指南

## 概述

本指南介绍如何使用 Arduino Leonardo 板子创建一个专门控制 WASD 四个键的键盘驱动。该驱动可以通过串口接收指令，模拟键盘按键的按下和弹起操作。

## 硬件要求

### 必需硬件
- **Arduino Leonardo** 或其他支持 HID 功能的 Arduino 板子
- **USB 数据线** (Type-A 到 Micro-USB)
- **电脑** (Windows/Mac/Linux)

### 为什么选择 Arduino Leonardo？
- 内置 USB HID 功能，可以直接模拟键盘和鼠标
- 无需额外的 USB-HID 芯片
- 编程简单，稳定性好

## 软件要求

### Arduino IDE
- **Arduino IDE 1.8.x** 或 **Arduino IDE 2.x**
- 下载地址：https://www.arduino.cc/en/software

### Python 环境
- **Python 3.7+**
- **pyserial** 库：`pip install pyserial`

## 文件结构

```
AI-Aimbot/
├── arduino_firmware/
│   └── arduino_keyboard_wasd/
│       └── arduino_keyboard_wasd.ino    # Arduino 固件代码
├── arduino_keyboard_controller.py       # Python 控制接口
├── test_arduino_keyboard.py            # 测试脚本
└── Arduino键盘驱动使用指南.md           # 本文档
```

## 烧录步骤

### 1. 准备 Arduino IDE

1. **下载并安装 Arduino IDE**
   - 访问 https://www.arduino.cc/en/software
   - 下载适合你操作系统的版本
   - 安装完成后启动 Arduino IDE

2. **配置板子类型**
   - 打开 Arduino IDE
   - 菜单：`工具` → `开发板` → `Arduino AVR Boards` → `Arduino Leonardo`

### 2. 连接硬件

1. **连接 Arduino Leonardo**
   - 使用 USB 数据线连接 Arduino Leonardo 到电脑
   - 等待驱动自动安装（Windows 可能需要几分钟）

2. **选择串口**
   - 菜单：`工具` → `端口`
   - 选择显示 "Arduino Leonardo" 的端口（通常是 COM3、COM4 等）

### 3. 烧录固件

1. **打开固件文件**
   - 在 Arduino IDE 中打开 `arduino_firmware/arduino_keyboard_wasd/arduino_keyboard_wasd.ino`

2. **编译和上传**
   - 点击 "验证" 按钮（✓）检查代码是否有错误
   - 点击 "上传" 按钮（→）将代码烧录到 Arduino
   - 等待上传完成（状态栏显示 "上传完成"）

3. **验证烧录**
   - 打开串口监视器：`工具` → `串口监视器`
   - 设置波特率为 `115200`
   - 应该看到启动信息：
     ```
     === Arduino WASD 键盘驱动已启动 ===
     版本: 1.0
     支持指令:
       按下: w, a, s, d (小写)
       弹起: W, A, S, D (大写)
       释放所有: R 或 r
       查询状态: ?
     ================================
     ```

## 使用方法

### 1. 串口指令控制

在 Arduino IDE 的串口监视器中，你可以直接发送指令：

| 指令 | 功能 | 示例 |
|------|------|------|
| `w` | 按下 W 键 | 发送 `w` |
| `a` | 按下 A 键 | 发送 `a` |
| `s` | 按下 S 键 | 发送 `s` |
| `d` | 按下 D 键 | 发送 `d` |
| `W` | 弹起 W 键 | 发送 `W` |
| `A` | 弹起 A 键 | 发送 `A` |
| `S` | 弹起 S 键 | 发送 `S` |
| `D` | 弹起 D 键 | 发送 `D` |
| `R` 或 `r` | 释放所有按键 | 发送 `R` |
| `?` | 查询当前状态 | 发送 `?` |

### 2. Python 程序控制

#### 基本使用示例

```python
from arduino_keyboard_controller import ArduinoKeyboardController

# 创建控制器
controller = ArduinoKeyboardController()

# 连接设备
if controller.connect():
    # 按下 W 键（向前移动）
    controller.press_key('w')
    
    # 等待 2 秒
    time.sleep(2)
    
    # 弹起 W 键
    controller.release_key('w')
    
    # 断开连接
    controller.disconnect()
```

#### 使用上下文管理器

```python
from arduino_keyboard_controller import ArduinoKeyboardController
import time

# 使用 with 语句自动管理连接
with ArduinoKeyboardController() as controller:
    # 同时按下 W 和 D（向前右移动）
    controller.press_key('w')
    controller.press_key('d')
    
    time.sleep(2)
    
    # 释放所有按键
    controller.release_all_keys()
```

### 3. 运行测试

运行完整的测试套件来验证功能：

```bash
python test_arduino_keyboard.py
```

测试包括：
- 基本连接功能
- 单个按键功能
- 同时按下多个按键
- 压力测试（快速按键操作）
- 错误处理
- 交互式测试

## 集成到 AI-Aimbot

### 在主程序中使用

你可以在 `main_onnx.py` 中集成键盘控制功能：

```python
from arduino_keyboard_controller import ArduinoKeyboardController

# 在程序初始化时创建键盘控制器
keyboard_controller = ArduinoKeyboardController()
if keyboard_controller.connect():
    print("[INFO] Arduino 键盘控制器已连接")
else:
    print("[WARNING] Arduino 键盘控制器连接失败")
    keyboard_controller = None

# 在需要移动时控制按键
def control_movement(direction):
    if keyboard_controller:
        if direction == "forward":
            keyboard_controller.press_key('w')
        elif direction == "backward":
            keyboard_controller.press_key('s')
        elif direction == "left":
            keyboard_controller.press_key('a')
        elif direction == "right":
            keyboard_controller.press_key('d')
        elif direction == "stop":
            keyboard_controller.release_all_keys()
```

### 与现有鼠标控制结合

```python
# 在瞄准时同时控制移动
if target_detected:
    # 鼠标瞄准
    move_mouse(mouseMove[0] * aaMovementAmp, mouseMove[1] * aaMovementAmp)
    
    # 键盘移动（例如：向目标方向移动）
    if keyboard_controller:
        if target_x > screen_center_x:
            keyboard_controller.press_key('d')  # 向右移动
        else:
            keyboard_controller.press_key('a')  # 向左移动
```

## 故障排除

### 常见问题

#### 1. Arduino 无法识别
**症状**：电脑无法识别 Arduino 设备
**解决方案**：
- 检查 USB 数据线是否正常（尝试其他设备）
- 重新安装 Arduino 驱动程序
- 尝试不同的 USB 端口
- 检查 Arduino 板子是否损坏

#### 2. 烧录失败
**症状**：上传代码时出现错误
**解决方案**：
- 确认选择了正确的板子类型（Arduino Leonardo）
- 确认选择了正确的串口
- 尝试按住 Arduino 上的 Reset 按钮，然后立即点击上传
- 关闭其他可能占用串口的程序

#### 3. 串口连接失败
**症状**：Python 程序无法连接到 Arduino
**解决方案**：
- 检查串口是否被其他程序占用（关闭 Arduino IDE 的串口监视器）
- 确认串口号是否正确
- 检查波特率设置（应为 115200）
- 重新插拔 USB 连接

#### 4. 按键无响应
**症状**：发送指令后按键没有反应
**解决方案**：
- 检查 Arduino 是否正确烧录了键盘固件
- 确认 Arduino Leonardo 支持 HID 功能
- 检查串口通信是否正常
- 尝试重启 Arduino（断开并重新连接 USB）

#### 5. 按键卡住
**症状**：按键一直处于按下状态
**解决方案**：
- 发送释放指令：`R` 或调用 `release_all_keys()`
- 重启 Arduino
- 检查程序逻辑，确保每个 `press_key()` 都有对应的 `release_key()`

### 调试技巧

#### 1. 使用串口监视器
- 在 Arduino IDE 中打开串口监视器
- 观察 Arduino 的输出信息
- 手动发送测试指令

#### 2. 检查设备管理器（Windows）
- 打开设备管理器
- 查看 "端口 (COM 和 LPT)" 部分
- 确认 Arduino 设备显示正常

#### 3. Python 调试
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查可用端口
controller = ArduinoKeyboardController()
ports = controller.find_arduino_ports()
print(f"可用端口: {ports}")
```

## 高级配置

### 自定义波特率

如果需要修改通信速度，可以在 Arduino 代码中修改：

```cpp
// 在 setup() 函数中
Serial.begin(9600);  // 改为更低的波特率
```

同时在 Python 代码中也要相应修改：

```python
controller = ArduinoKeyboardController(baudrate=9600)
```

### 添加更多按键

如果需要支持更多按键，可以修改 Arduino 代码：

```cpp
// 添加新的按键处理
case 'e':
    pressKey(4);  // 添加 E 键支持
    break;
case 'E':
    releaseKey(4);
    break;
```

### 状态指示灯

Arduino 代码中已包含 LED 状态指示：
- **心跳闪烁**：每秒闪烁一次，表示设备正常运行
- **启动闪烁**：启动时快速闪烁 3 次

## 安全注意事项

1. **避免按键卡住**：始终确保程序正常退出时释放所有按键
2. **异常处理**：在程序中添加适当的异常处理，防止意外情况
3. **测试环境**：在安全的测试环境中验证功能，避免在重要应用中误操作
4. **备用方案**：保留传统的键盘作为备用输入方式

## 性能优化

### 减少延迟
- 使用较高的波特率（115200）
- 避免不必要的状态查询
- 批量处理按键操作

### 提高稳定性
- 添加重连机制
- 实现心跳检测
- 使用线程安全的操作

## 总结

Arduino 键盘驱动为 AI-Aimbot 项目提供了硬件级的键盘控制能力，具有以下优势：

1. **低延迟**：硬件级控制，响应速度快
2. **高兼容性**：模拟真实键盘，兼容所有游戏
3. **可扩展性**：易于添加新功能和按键
4. **稳定性**：独立硬件，不受软件环境影响

通过本指南，你应该能够成功设置和使用 Arduino 键盘驱动。如果遇到问题，请参考故障排除部分或查看测试脚本的输出信息。
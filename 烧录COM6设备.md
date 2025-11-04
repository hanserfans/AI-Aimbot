# 🎯 Arduino Leonardo (COM6) 固件烧录指导

## 📍 设备信息
- **端口**: COM6
- **设备**: Arduino Leonardo (VID:PID 2341:8036)
- **状态**: 硬件连接正常，固件需要烧录

## 🚀 快速烧录步骤

### 1. 打开Arduino IDE
- 启动Arduino IDE软件

### 2. 配置设备
- **开发板**: 工具 → 开发板 → Arduino Leonardo
- **端口**: 工具 → 端口 → COM6 (Arduino Leonardo)

### 3. 打开固件文件
- 文件 → 打开 → `arduino_firmware/arduino_leonardo_mouse.ino`

### 4. 上传固件
- 点击上传按钮 (→)
- 等待编译和上传完成

## ⚠️ 如果上传失败

### 方法1: Reset按钮法
1. 按住Arduino的**Reset按钮**
2. 点击Arduino IDE的**上传按钮**
3. 当IDE显示"上传中..."时，松开Reset按钮

### 方法2: 双击Reset法
1. 快速**双击**Arduino的Reset按钮
2. 立即点击Arduino IDE的**上传按钮**

### 方法3: 检查连接
- 确保USB线是**数据线**（非充电线）
- 尝试不同的USB端口
- 重新插拔USB线

## 🧪 验证烧录结果

烧录完成后运行测试：
```bash
python test_arduino_connection.py
```

成功的输出应该显示：
```
✅ Arduino连接成功!
✅ Arduino状态: 已连接并就绪
🎉 Arduino驱动工作正常，可以在AI-Aimbot中使用
```

## 🎉 烧录成功后

Arduino将提供：
- **硬件级精确控制**
- **零延迟响应**
- **原生HID设备**
- **无需校正因子**

现在你可以在AI-Aimbot中享受最高精度的瞄准体验！
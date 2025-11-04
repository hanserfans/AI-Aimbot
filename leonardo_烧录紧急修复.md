# Arduino Leonardo 烧录紧急修复指南

## 🚨 问题症状
```
avrdude: butterfly_recv(): programmer is not responding
Found programmer: Id = "�"; type = �
```

## ✅ 解决方法

### 方法1：双击Reset按钮法（推荐）
1. **准备**：在Arduino IDE中打开 `arduino_leonardo_mouse.ino`
2. **设置**：选择板子 "Arduino Leonardo"，端口 "COM6"
3. **操作**：
   - 点击"上传"按钮
   - **立即双击**板子上的Reset按钮（快速按两次）
   - 观察板子LED灯快速闪烁（进入bootloader模式）
   - 等待上传完成

### 方法2：时序控制法
1. **准备上传**：点击"上传"按钮
2. **等待提示**：看到"Connecting to programmer"时
3. **按Reset**：立即按一次Reset按钮
4. **观察LED**：板子LED应该快速闪烁
5. **等待完成**：保持连接直到上传成功

### 方法3：手动进入Bootloader
1. **断开USB**：拔掉USB线
2. **按住Reset**：按住Reset按钮不放
3. **插入USB**：重新插入USB线
4. **释放Reset**：松开Reset按钮
5. **立即上传**：在Arduino IDE中点击上传

## 🎯 成功标志
- LED灯快速闪烁（约1秒1次）
- Arduino IDE显示"上传成功"
- 串口监视器显示"Arduino Mouse Controller Ready!"

## ⚠️ 注意事项
- Leonardo的bootloader只有8秒窗口期
- 时序很关键，需要多次尝试
- 确保USB线连接稳定
- 如果失败，等待10秒后重试

## 🔍 验证方法
上传成功后运行：
```bash
python test_arduino_connection.py
```
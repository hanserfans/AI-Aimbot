# G-Hub 驱动使用指南

## 📋 概述

AI-Aimbot 项目现已成功升级到 Logitech G-Hub 驱动控制，提供更安全、更难被检测的鼠标控制方式。

## ✅ 升级完成状态

- ✅ **mouse_driver 模块**: 已完成实现
- ✅ **G-Hub 集成**: 基于 G-Input 项目的稳定代码
- ✅ **兼容性测试**: 通过所有功能测试
- ✅ **文档更新**: 完整的使用说明

## 🔧 系统要求

### 必需组件
1. **Logitech G-Hub 软件**
   - 下载地址: https://www.logitechg.com/innovation/g-hub.html
   - 兼容版本: 2021.3.9205 或更高版本
   - 状态: 必须安装并运行

2. **Logitech 游戏设备** (推荐)
   - 任何 Logitech G 系列鼠标、键盘或耳机
   - 注意: 某些情况下仅安装 G-Hub 软件也可工作

3. **管理员权限**
   - 程序需要以管理员身份运行
   - 用于访问硬件驱动接口

## 🎮 使用方法

### 1. 激活 G-Hub 驱动
G-Hub 驱动使用 **右键** 作为激活键：

```
按住右键 → 激活自瞄 → 鼠标自动移动到目标
```

### 2. 与 Win32 API 的区别

| 特性 | Win32 API | G-Hub 驱动 |
|------|-----------|------------|
| 激活键 | Caps Lock | 右键 |
| 检测难度 | 容易被检测 | 难以检测 |
| 硬件要求 | 无 | 需要 G-Hub |
| 性能 | 快速 | 稍慢但更安全 |

### 3. 配置建议

在 `config.py` 中推荐的 G-Hub 驱动配置：

```python
# 鼠标移动幅度 (建议值: 0.3-0.5)
aaMovementAmp = 0.4

# 置信度阈值 (建议值: 0.4-0.6)  
confidence = 0.4

# 爆头模式 (建议开启)
headshot_mode = True

# 退出键 (可自定义)
aaQuitKey = "F2"
```

## 🧪 测试验证

### 运行测试脚本
```bash
python test_ghub_driver.py
```

### 测试项目
- ✅ 模块导入测试
- ✅ 函数调用测试  
- ✅ 右键触发测试
- ✅ 兼容性验证

### 预期结果
```
=== G-Hub 驱动测试开始 ===
✓ 成功导入 ghub_move 和 mouse_move 函数
✓ ghub_move 函数调用成功
✓ mouse_move 别名函数调用成功
✓ 所有基础功能测试通过！
```

## 🔍 故障排除

### 常见问题

#### 1. "G-Hub device not found" 错误
**原因**: G-Hub 软件未安装或未运行
**解决方案**:
- 下载并安装 Logitech G-Hub
- 确保 G-Hub 正在运行
- 重启程序

#### 2. 鼠标不移动
**原因**: 权限不足或设备未识别
**解决方案**:
- 以管理员身份运行程序
- 检查 Logitech 设备连接
- 重启 G-Hub 软件

#### 3. 右键触发无响应
**原因**: 按键检测问题
**解决方案**:
- 确认使用鼠标右键（不是键盘）
- 检查其他程序是否占用右键
- 尝试重启程序

### 调试步骤

1. **检查 G-Hub 状态**
   ```bash
   # 查看 G-Hub 进程
   tasklist | findstr "LGHUB"
   ```

2. **验证设备连接**
   - 打开 G-Hub 软件界面
   - 确认设备显示在设备列表中

3. **测试基础功能**
   ```bash
   python test_ghub_driver.py
   ```

## 📊 性能对比

### 检测风险评估
- **Win32 API**: 高风险 (已知被 Splitgate、EQU8 检测)
- **G-Hub 驱动**: 低风险 (硬件级别，难以检测)
- **外部硬件**: 无风险 (物理隔离)

### 推荐使用场景
- **竞技游戏**: 使用 G-Hub 驱动
- **休闲游戏**: Win32 API 或 G-Hub 驱动
- **高风险环境**: 外部硬件控制

## 🔄 从 Win32 API 迁移

### 自动切换
项目支持多种鼠标控制方式，可以根据需要选择：

1. **保持 Win32 API**: 继续使用 Caps Lock 激活
2. **切换到 G-Hub**: 使用右键激活（推荐）
3. **混合使用**: 根据游戏环境选择

### 配置切换
无需修改代码，只需：
- Win32 API: 按 Caps Lock
- G-Hub 驱动: 按右键

## 📚 技术细节

### 实现架构
```
AI-Aimbot/
├── mouse_driver/           # G-Hub 驱动模块
│   ├── __init__.py        # 模块初始化
│   └── MouseMove.py       # 核心实现
├── test_ghub_driver.py    # 测试脚本
└── customScripts/         # 应用脚本
    ├── main_onnx.py       # ONNX 版本
    └── main_tensorrt.py   # TensorRT 版本
```

### 核心函数
```python
# 主要接口函数
def ghub_move(x: int, y: int) -> None:
    """G-Hub 鼠标移动函数"""
    
# 兼容性别名
mouse_move = ghub_move
```

## 🎯 最佳实践

### 安全使用建议
1. **适度使用**: 避免过度依赖自瞄
2. **参数调整**: 根据游戏调整 `aaMovementAmp`
3. **环境感知**: 在安全环境下测试
4. **备份方案**: 保持多种控制方式可用

### 性能优化
1. **降低移动幅度**: `aaMovementAmp = 0.3`
2. **提高置信度**: `confidence = 0.5`
3. **启用爆头模式**: `headshot_mode = True`

## 📞 支持

如遇到问题，请参考：
1. `鼠标控制机制分析.md` - 技术原理
2. `鼠标控制问题解决方案.md` - 问题解决
3. `test_ghub_driver.py` - 功能测试

---

**升级完成时间**: 2024年10月30日  
**基于项目**: [G-Input](https://github.com/xxreflextheone/g-input)  
**状态**: ✅ 生产就绪
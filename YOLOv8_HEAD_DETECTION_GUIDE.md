# YOLOv8头部检测使用指南

## 概述

本指南将帮助您配置和使用YOLOv8头部检测模型来提升瞄准精度。

## 快速开始

### 1. 准备YOLOv8头部检测模型

将您的YOLOv8s头部检测模型（.pt文件）放置在项目目录中，例如：
```
models/
├── yolov8s_head.pt          # 您的头部检测模型
├── yolov5s.pt              # 原始全身检测模型
└── custom_head_model.pt    # 其他自定义模型
```

### 2. 配置模型

编辑 `model_config.py` 或使用代码添加您的模型：

```python
from model_config import ModelConfig

config = ModelConfig()

# 添加您的YOLOv8头部检测模型
config.add_model(
    name="my_yolov8_head",
    model_type="yolov8",
    path="models/yolov8s_head.pt",
    description="我的YOLOv8头部检测模型",
    headshot_offset=0.1,  # 头部检测专用偏移（较小值）
    body_offset=0.2,      # 身体检测偏移
    confidence=0.6        # 置信度阈值
)

# 设置为当前模型
config.set_current_model("my_yolov8_head")
```

### 3. 运行智能瞄准机器人

```bash
python smart_aimbot.py
```

## 详细配置

### 模型配置参数

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `headshot_offset` | 头部模式偏移比例 | 0.05-0.15 |
| `body_offset` | 身体模式偏移比例 | 0.15-0.25 |
| `confidence` | 检测置信度阈值 | 0.5-0.7 |

### 捕获模式配置

```python
# 全屏捕获（推荐用于头部检测）
config.set_capture_mode("fullscreen")

# 中心区域捕获
config.set_capture_mode("center", center_size=640)
```

### 瞄准设置

```python
# 配置瞄准参数
config.set_aiming_settings({
    "target_selection": "closest",      # 目标选择: closest, highest_conf, largest
    "max_distance": 200,                # 最大瞄准距离（像素）
    "movement_amp": 0.5,                # 移动幅度
    "smoothing_factor": 0.3             # 平滑因子
})
```

## 使用技巧

### 1. 头部检测模型优势

- **更精确的头部定位**：专门训练的头部检测模型能更准确地识别头部区域
- **更小的偏移值**：由于直接检测头部，可以使用更小的偏移值（0.05-0.15）
- **更好的远距离表现**：头部特征在远距离时更容易识别

### 2. 模型选择建议

| 场景 | 推荐模型 | 偏移设置 |
|------|----------|----------|
| 近距离战斗 | 全身检测模型 | headshot_offset=0.38 |
| 中远距离狙击 | 头部检测模型 | headshot_offset=0.1 |
| 混合场景 | 智能切换 | 动态调整 |

### 3. 性能优化

```python
# 针对头部检测的优化设置
config.models["my_yolov8_head"].update({
    "confidence": 0.6,          # 提高置信度以减少误检
    "headshot_offset": 0.08,    # 较小偏移值
    "capture_mode": "fullscreen" # 全屏捕获获得更多信息
})
```

## 运行时操作

### 快捷键

- **右键**：按住进行瞄准
- **M键**：切换模型
- **Q键**：退出程序

### 模型切换

运行时按 `M` 键可以在不同模型间切换：

```
可用模型:
1. yolov5_original (当前) - 原始YOLOv5全身检测
2. my_yolov8_head - 我的YOLOv8头部检测模型
3. custom_head - 自定义头部检测模型
0. 取消

请选择模型 (输入数字): 2
```

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查模型文件路径是否正确
   - 确认已安装 `ultralytics` 库：`pip install ultralytics`

2. **检测效果不佳**
   - 调整置信度阈值
   - 检查模型是否适合当前游戏场景
   - 尝试不同的偏移值

3. **性能问题**
   - 降低捕获分辨率
   - 使用中心区域捕获模式
   - 调整帧率限制

### 调试模式

启用视觉调试查看检测效果：

```python
# 在 config.py 中设置
visuals = True
```

这将显示：
- 检测框和置信度
- 瞄准点位置
- FPS和目标数量
- 当前模型信息

## 高级配置

### 自定义检测后处理

```python
class CustomSmartAimbot(SmartAimbot):
    def select_best_target(self, detections):
        """自定义目标选择逻辑"""
        # 优先选择头部大小合适的目标
        valid_targets = []
        for detection in detections:
            head_size = detection['width'] * detection['height']
            if 100 < head_size < 5000:  # 合理的头部大小范围
                valid_targets.append(detection)
        
        if not valid_targets:
            return None
            
        # 选择最近的目标
        return min(valid_targets, key=lambda x: x['distance'])
```

### 多模型自动切换

```python
def auto_switch_model(self, target_distance):
    """根据目标距离自动切换模型"""
    if target_distance > 300:
        # 远距离使用头部检测
        self.config.set_current_model("my_yolov8_head")
    else:
        # 近距离使用全身检测
        self.config.set_current_model("yolov5_original")
```

## 模型训练建议

如果您想训练自己的头部检测模型：

1. **数据集准备**
   - 收集游戏中的头部截图
   - 标注头部边界框
   - 确保数据多样性（不同角度、光照、距离）

2. **训练参数**
   ```bash
   yolo train data=head_dataset.yaml model=yolov8s.pt epochs=100 imgsz=640
   ```

3. **验证和优化**
   - 在实际游戏场景中测试
   - 调整置信度阈值
   - 优化偏移参数

## 总结

YOLOv8头部检测模型能够显著提升瞄准精度，特别是在中远距离场景中。通过合理配置模型参数和瞄准设置，您可以获得更好的游戏体验。

记住：
- 头部检测模型使用更小的偏移值（0.05-0.15）
- 全屏捕获模式通常效果更好
- 根据实际使用情况调整置信度阈值
- 利用模型切换功能适应不同场景
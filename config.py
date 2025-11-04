# Portion of screen to be captured (This forms a square/rectangle around the center of screen)
screenShotHeight = 320
screenShotWidth = 320

# 调试日志总开关（True=输出调试信息，False=静默）
DEBUG_LOG = False

# Use "left" or "right" for the mask side depending on where the interfering object is, useful for 3rd player models or large guns
useMask = False
maskSide = "left"
maskWidth = 80
maskHeight = 200

# Autoaim mouse movement amplifier
aaMovementAmp = 2   # 自动瞄准鼠标移动放大器（推荐范围：0.3-0.8）

# 🎯 目标范围内停止增强配置
# Target range threshold for enhanced stopping (pixels)
targetRangeThreshold = 18# 目标范围阈值（像素）- 改为15像素

# Stop duration when entering target range (seconds)
inRangeStopDuration = 0.0  # 进入范围内停止时间（秒）- 已取消停止

# Precision stop duration for very close targets (seconds)  
precisionStopDuration = 0.0  # 精确瞄准停止时间（秒）- 已取消停止

# Precision mode threshold (pixels)
precisionModeThreshold = 18 # 精确模式阈值（像素）

# Stability check interval during stop (seconds)
stabilityCheckInterval = 0.005  # 稳定性检查间隔（秒）

# Person Class Confidence (提升以过滤假阳性目标，真实目标置信度通常>0.55)
confidence = 0.34 # 降低置信度阈值以显示更多目标，提高检测灵敏度

# Target Detection Limits (目标检测限制)
# Maximum number of targets to detect and process (1-20 recommended)
# 减少到1个目标以节省内存和提升性能
maxTargets = 2

# Target selection strategy when multiple targets are detected
# Options: "closest" (最近距离), "highest_conf" (最高置信度), "largest" (最大目标)
targetSelectionStrategy = "closest"

# What key to press to quit and shutdown the autoaim
aaQuitKey = "Q"

# If you want to main slightly upwards towards the head
# 启用头部模式但不进行预测 - 只调整瞄准点到头部位置
headshot_mode = True

# Displays the Corrections per second in the terminal
cpsDisplay = True

# Set to True if you want to get the visuals
visuals = True

# Live Feed Display Settings
# Set to False to disable live feed window and save memory (6-8MB per frame)
# 暂时禁用实时显示以节省内存和避免死机
showLiveFeed = True

# Model Selection Settings
# Choose between different YOLO models for speed vs accuracy trade-off
# Options: "yolov5s320Half.onnx" (fast, 70 FPS) or "yolov5m320Half.onnx" (accurate, 32 FPS)
modelPath = "yolov5s320Half.onnx"

# Dynamic model switching based on game type (experimental)
# Set to True to automatically use faster model for fast-paced games
dynamicModelSwitching = False

# Smarter selection of people
centerOfScreen = True

# ONNX ONLY - Choose 1 of the 3 below
# 1 - CPU
# 2 - AMD
# 3 - NVIDIA
onnxChoice = 3

# Window Selection Settings
# Set to True to enable automatic window selection in GUI mode
autoSelectWindow = True

# Preferred game window title (partial match, case insensitive)
# Leave empty to use automatic detection
preferredWindowTitle = ""

# Custom game keywords for auto-detection (add your game here if not detected)
customGameKeywords = [
    # Add your game window titles here, e.g.:
    # "My Game Title",
    # "Another Game"
]

# Auto Fire Settings
# Set to True to enable automatic firing after aiming
autoFire = True

# Number of shots to fire automatically (1-5 recommended)
autoFireShots =1

# Delay between shots in milliseconds (50-200ms recommended)
autoFireDelay = 0

# Fire key to simulate (default is left mouse button)
# Options: "left_click", "right_click", "space", "f", "r", etc.
autoFireKey = "left_click"

# Pure Trigger Mode Settings (Caps Lock mode)
# Set to True to skip WASD detection for faster firing in pure trigger mode
pureTriggerFastMode = True

# Pure trigger mode distance threshold (pixels from center)
pureTriggerThreshold = 15

# ============================================================================
# YOLOv8 Model Settings (New Feature)
# ============================================================================

# Enable YOLOv8 PT model support
# Set to True to use YOLOv8 .pt models instead of ONNX
useYOLOv8 = True

# YOLOv8 model path options
yolov8ModelPath = {
    'valorant': 'models/valorant/best.pt',  # Valorant专用模型
    'general': 'yolov8s.pt',                # 通用YOLOv8s模型
    'custom': 'best.pt'                     # 自定义模型
}

# Current YOLOv8 model selection
# Options: 'valorant', 'general', 'custom', or direct path
currentYOLOv8Model = 'valorant'

# YOLOv8 specific settings
yolov8Settings = {
    'confidence': 0.75,     # 提高置信度以减少枪支误识别为头部的问题
    'iou_threshold': 0.45,  # NMS IoU阈值
    'max_detections': 1,    # 减少最大检测数量以节省内存
    'use_half_precision': True,  # 启用半精度以节省内存
    'device': 'cuda',       # 设备选择: 'cuda', 'cpu', 'auto'
    'classes': [0, 1],      # 检测类别 (0=enemyBody, 1=enemyHead)
    'agnostic_nms': False   # 类别无关NMS
}

# YOLOv8 capture settings
yolov8Capture = {
    'fov_width': 320, # FOV宽度
    'fov_height': 320,      # FOV高度
    'input_width': 416,     # 模型输入宽度
    'input_height': 416,    # 模型输入高度
    'mouse_speed': 5      # 鼠标移动速度系数 - 提高到2.0以加快移动
}

# Auto-switch between ONNX and YOLOv8 based on game
autoSwitchModel = False

# Model switching rules
modelSwitchRules = {
    'VALORANT': 'yolov8',   # 瓦洛兰特使用YOLOv8
    'default': 'onnx'       # 其他游戏使用ONNX
}
"""
YOLOv8头部检测快速配置脚本
帮助用户快速设置和测试YOLOv8头部检测模型
"""

import os
import sys
from model_config import ModelConfig

def setup_yolov8_head_model():
    """设置YOLOv8头部检测模型"""
    print("YOLOv8头部检测模型配置向导")
    print("=" * 50)
    
    config = ModelConfig()
    
    # 显示当前状态
    print("\n当前模型配置:")
    config.print_model_status()
    
    # 获取模型文件路径
    print("\n请提供您的YOLOv8头部检测模型信息:")
    
    while True:
        model_path = input("模型文件路径 (.pt文件): ").strip()
        if not model_path:
            print("请输入模型文件路径")
            continue
            
        if not os.path.exists(model_path):
            print(f"文件不存在: {model_path}")
            continue
            
        if not model_path.endswith('.pt'):
            print("请提供.pt格式的模型文件")
            continue
            
        break
    
    # 获取模型名称
    default_name = "yolov8_head_custom"
    model_name = input(f"模型名称 (默认: {default_name}): ").strip()
    if not model_name:
        model_name = default_name
    
    # 获取描述
    description = input("模型描述 (可选): ").strip()
    if not description:
        description = f"自定义YOLOv8头部检测模型"
    
    # 配置参数
    print("\n配置检测参数:")
    
    # 置信度
    while True:
        try:
            confidence = input("置信度阈值 (0.1-0.9, 推荐0.6): ").strip()
            if not confidence:
                confidence = 0.6
            else:
                confidence = float(confidence)
            
            if 0.1 <= confidence <= 0.9:
                break
            else:
                print("置信度应在0.1-0.9之间")
        except ValueError:
            print("请输入有效的数字")
    
    # 头部偏移
    while True:
        try:
            headshot_offset = input("头部模式偏移比例 (0.05-0.2, 推荐0.1): ").strip()
            if not headshot_offset:
                headshot_offset = 0.1
            else:
                headshot_offset = float(headshot_offset)
            
            if 0.05 <= headshot_offset <= 0.2:
                break
            else:
                print("头部偏移应在0.05-0.2之间")
        except ValueError:
            print("请输入有效的数字")
    
    # 身体偏移
    while True:
        try:
            body_offset = input("身体模式偏移比例 (0.15-0.3, 推荐0.2): ").strip()
            if not body_offset:
                body_offset = 0.2
            else:
                body_offset = float(body_offset)
            
            if 0.15 <= body_offset <= 0.3:
                break
            else:
                print("身体偏移应在0.15-0.3之间")
        except ValueError:
            print("请输入有效的数字")
    
    # 添加模型
    print(f"\n正在添加模型: {model_name}")
    success = config.add_model(
        name=model_name,
        model_type="yolov8",
        path=model_path,
        description=description,
        headshot_offset=headshot_offset,
        body_offset=body_offset,
        confidence=confidence
    )
    
    if success:
        print("✓ 模型添加成功")
        
        # 询问是否设为当前模型
        set_current = input(f"\n是否将 '{model_name}' 设为当前使用的模型? (y/n): ").strip().lower()
        if set_current in ['y', 'yes', '是']:
            if config.set_current_model(model_name):
                print("✓ 已设为当前模型")
            else:
                print("✗ 设置当前模型失败")
        
        # 配置捕获模式
        print("\n配置屏幕捕获模式:")
        print("1. 全屏捕获 (推荐用于头部检测)")
        print("2. 中心区域捕获")
        
        capture_choice = input("选择捕获模式 (1/2, 默认1): ").strip()
        if capture_choice == "2":
            try:
                center_size = input("中心区域大小 (像素, 默认640): ").strip()
                center_size = int(center_size) if center_size else 640
                config.set_capture_mode("center", center_size=center_size)
                print(f"✓ 已设置为中心区域捕获 ({center_size}x{center_size})")
            except ValueError:
                print("使用默认中心区域大小640")
                config.set_capture_mode("center", center_size=640)
        else:
            config.set_capture_mode("fullscreen")
            print("✓ 已设置为全屏捕获")
        
        # 显示最终配置
        print("\n" + "=" * 50)
        print("配置完成! 最终设置:")
        config.print_model_status()
        
        print(f"\n模型详情:")
        model_info = config.get_model_info(model_name)
        for key, value in model_info.items():
            print(f"  {key}: {value}")
        
        print(f"\n使用方法:")
        print(f"1. 运行: python smart_aimbot.py")
        print(f"2. 按住右键进行瞄准")
        print(f"3. 按 M 键切换模型")
        print(f"4. 按 Q 键退出")
        
        # 询问是否立即测试
        test_now = input(f"\n是否立即启动智能瞄准机器人进行测试? (y/n): ").strip().lower()
        if test_now in ['y', 'yes', '是']:
            print("正在启动智能瞄准机器人...")
            try:
                from smart_aimbot import SmartAimbot
                aimbot = SmartAimbot()
                aimbot.run()
            except ImportError as e:
                print(f"启动失败: {e}")
                print("请确保所有依赖已安装")
            except Exception as e:
                print(f"运行错误: {e}")
        
    else:
        print("✗ 模型添加失败")

def test_model_detection():
    """测试模型检测效果"""
    print("\n模型检测测试")
    print("=" * 30)
    
    config = ModelConfig()
    current_model = config.get_current_model()
    
    print(f"当前模型: {config.config['current_model']}")
    print(f"模型类型: {current_model['type']}")
    print(f"模型路径: {current_model['path']}")
    
    if not os.path.exists(current_model['path']):
        print("错误: 模型文件不存在")
        return
    
    try:
        print("正在加载模型...")
        if current_model['type'] == 'yolov8':
            from ultralytics import YOLO
            model = YOLO(current_model['path'])
            print("✓ YOLOv8模型加载成功")
            
            # 简单测试
            print("进行简单检测测试...")
            import numpy as np
            test_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            results = model(test_img, verbose=False)
            print(f"✓ 检测测试完成，检测到 {len(results[0].boxes) if results[0].boxes is not None else 0} 个目标")
            
        else:
            print("当前模型不是YOLOv8类型，跳过测试")
            
    except ImportError:
        print("错误: 缺少ultralytics库，请安装: pip install ultralytics")
    except Exception as e:
        print(f"测试失败: {e}")

def main():
    """主菜单"""
    while True:
        print("\nYOLOv8头部检测配置工具")
        print("=" * 30)
        print("1. 添加新的YOLOv8头部检测模型")
        print("2. 查看当前模型配置")
        print("3. 测试模型检测")
        print("4. 启动智能瞄准机器人")
        print("5. 查看使用指南")
        print("0. 退出")
        
        choice = input("\n请选择操作 (0-5): ").strip()
        
        if choice == "1":
            setup_yolov8_head_model()
        elif choice == "2":
            config = ModelConfig()
            config.print_model_status()
        elif choice == "3":
            test_model_detection()
        elif choice == "4":
            try:
                from smart_aimbot import SmartAimbot
                aimbot = SmartAimbot()
                aimbot.run()
            except ImportError as e:
                print(f"启动失败: {e}")
            except Exception as e:
                print(f"运行错误: {e}")
        elif choice == "5":
            guide_path = "YOLOv8_HEAD_DETECTION_GUIDE.md"
            if os.path.exists(guide_path):
                print(f"\n请查看使用指南: {guide_path}")
            else:
                print("使用指南文件不存在")
        elif choice == "0":
            print("再见!")
            break
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    main()
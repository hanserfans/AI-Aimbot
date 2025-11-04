#!/usr/bin/env python3
"""
检查Valorant头部检测模型的详细信息
"""

import torch
import os
from pathlib import Path

def check_valorant_model():
    """检查Valorant头部检测模型信息"""
    model_path = Path("models/valorant_head_detector.pt")
    
    if not model_path.exists():
        print(f"❌ 模型文件不存在: {model_path}")
        return
    
    print(f"📁 模型文件路径: {model_path.absolute()}")
    print(f"📊 文件大小: {os.path.getsize(model_path) / (1024*1024):.2f} MB")
    
    try:
        # 加载模型
        print("\n🔄 正在加载模型...")
        model = torch.load(model_path, map_location='cpu', weights_only=False)
        print(f"✅ 模型加载成功")
        print(f"🔍 模型类型: {type(model)}")
        
        if isinstance(model, dict):
            print(f"📋 模型字典键: {list(model.keys())}")
            
            if 'model' in model:
                actual_model = model['model']
                print(f"🧠 实际模型类型: {type(actual_model)}")
                
                if hasattr(actual_model, 'names'):
                    print(f"🏷️  类别名称: {actual_model.names}")
                if hasattr(actual_model, 'nc'):
                    print(f"🔢 类别数量: {actual_model.nc}")
                if hasattr(actual_model, 'yaml'):
                    print(f"⚙️  模型配置: {actual_model.yaml}")
                    
            if 'epoch' in model:
                print(f"🔄 训练轮数: {model['epoch']}")
            if 'best_fitness' in model:
                print(f"🎯 最佳适应度: {model['best_fitness']}")
                
        else:
            if hasattr(model, 'names'):
                print(f"🏷️  类别名称: {model.names}")
            if hasattr(model, 'nc'):
                print(f"🔢 类别数量: {model.nc}")
                
        print("\n✅ 模型检查完成")
        
    except Exception as e:
        print(f"❌ 加载模型时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_valorant_model()
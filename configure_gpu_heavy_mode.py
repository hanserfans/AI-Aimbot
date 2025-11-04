#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU重度访问模式自动配置脚本
自动检测GPU硬件并设置最优的统一内存参数
"""

import 
import os
import sys
import torch
import psutil
from typing import Dict, Any, Tuple

def get_gpu_info() -> Dict[str, Any]:
    """获取GPU硬件信息"""
    gpu_info = {
        'available': False,
        'name': 'Unknown',
        'memory_gb': 0,
        'compute_capability': (0, 0),
        'cuda_version': 'Unknown'
    }
    
    try:
        if torch.cuda.is_available():
            gpu_info['available'] = True
            gpu_info['name'] = torch.cuda.get_device_name(0)
            gpu_info['memory_gb'] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            gpu_info['compute_capability'] = torch.cuda.get_device_capability(0)
            gpu_info['cuda_version'] = torch.version.cuda
            
            print(f"[INFO] 🎯 检测到GPU: {gpu_info['name']}")
            print(f"[INFO] 💾 GPU内存: {gpu_info['memory_gb']:.1f} GB")
            print(f"[INFO] 🔧 计算能力: {gpu_info['compute_capability'][0]}.{gpu_info['compute_capability'][1]}")
            print(f"[INFO] 🚀 CUDA版本: {gpu_info['cuda_version']}")
            
    except Exception as e:
        print(f"[WARNING] GPU信息获取失败: {e}")
        
    return gpu_info

def get_system_memory() -> float:
    """获取系统内存信息（GB）"""
    try:
        memory_info = psutil.virtual_memory()
        total_memory_gb = memory_info.total / (1024**3)
        available_memory_gb = memory_info.available / (1024**3)
        
        print(f"[INFO] 🖥️ 系统总内存: {total_memory_gb:.1f} GB")
        print(f"[INFO] 📊 可用内存: {available_memory_gb:.1f} GB")
        
        return total_memory_gb, available_memory_gb
    except Exception as e:
        print(f"[WARNING] 系统内存信息获取失败: {e}")
        return 16.0, 8.0  # 默认值

def calculate_optimal_memory_settings(gpu_info: Dict[str, Any], 
                                    system_memory: Tuple[float, float]) -> Dict[str, Any]:
    """根据硬件配置计算最优的内存设置"""
    total_memory, available_memory = system_memory
    gpu_memory = gpu_info['memory_gb']
    
    # 基础配置
    config = {
        'use_unified_memory': True,
        'unified_memory_access_pattern': 'gpu_heavy',
        'enable_auto_migration': True,
        'fallback_to_traditional_gpu': True,
        'performance_monitoring': True,
        'memory_pool_preallocation': True,
        'zero_copy_optimization': True
    }
    
    # 根据GPU内存容量调整设置
    if gpu_memory >= 12:
        # 高端GPU (12GB+)
        config.update({
            'unified_memory_size_gb': min(4.0, gpu_memory * 0.3),
            'memory_optimization_level': 'aggressive',
            'debug_unified_memory': False
        })
        print(f"[CONFIG] 🚀 高端GPU配置 - 内存池: {config['unified_memory_size_gb']:.1f}GB")
        
    elif gpu_memory >= 8:
        # 中高端GPU (8-12GB)
        config.update({
            'unified_memory_size_gb': min(3.0, gpu_memory * 0.25),
            'memory_optimization_level': 'aggressive',
            'debug_unified_memory': False
        })
        print(f"[CONFIG] ⚡ 中高端GPU配置 - 内存池: {config['unified_memory_size_gb']:.1f}GB")
        
    elif gpu_memory >= 6:
        # 中端GPU (6-8GB)
        config.update({
            'unified_memory_size_gb': min(2.0, gpu_memory * 0.2),
            'memory_optimization_level': 'balanced',
            'debug_unified_memory': False
        })
        print(f"[CONFIG] 🎯 中端GPU配置 - 内存池: {config['unified_memory_size_gb']:.1f}GB")
        
    elif gpu_memory >= 4:
        # 入门级GPU (4-6GB)
        config.update({
            'unified_memory_size_gb': min(1.5, gpu_memory * 0.15),
            'memory_optimization_level': 'balanced',
            'debug_unified_memory': False
        })
        print(f"[CONFIG] 📱 入门级GPU配置 - 内存池: {config['unified_memory_size_gb']:.1f}GB")
        
    else:
        # 低端GPU (<4GB)
        config.update({
            'unified_memory_size_gb': 1.0,
            'memory_optimization_level': 'conservative',
            'debug_unified_memory': True,
            'unified_memory_access_pattern': 'mixed'  # 改为混合模式
        })
        print(f"[CONFIG] ⚠️ 低端GPU配置 - 内存池: {config['unified_memory_size_gb']:.1f}GB (混合模式)")
    
    # 检查计算能力兼容性
    compute_major, compute_minor = gpu_info['compute_capability']
    if compute_major < 6:
        print(f"[WARNING] ⚠️ GPU计算能力 {compute_major}.{compute_minor} 可能不支持统一内存")
        config['use_unified_memory'] = False
        return config
    
    # 系统内存检查
    if available_memory < 4.0:
        print(f"[WARNING] ⚠️ 系统可用内存不足 ({available_memory:.1f}GB)，降低内存池大小")
        config['unified_memory_size_gb'] = min(config['unified_memory_size_gb'], 1.0)
        config['memory_optimization_level'] = 'conservative'
    
    return config

def update_gui_config(unified_memory_config: Dict[str, Any]) -> bool:
    """更新gui_config.文件"""
    config_file = "gui_config."
    
    try:
        # 读取现有配置
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                gui_config = .load(f)
        else:
            # 创建默认配置
            gui_config = {
                "control_method": "arduino",
                "confidence": 0.6,
                "movement_amp": 0.35,
                "headshot_mode": True,
                "game_fov": 103
            }
        
        # 更新统一内存配置
        gui_config['unified_memory'] = unified_memory_config
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            .dump(gui_config, f, indent=2, ensure_ascii=False)
        
        print(f"[SUCCESS] ✅ 配置已保存到 {config_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] ❌ 配置保存失败: {e}")
        return False

def print_configuration_summary(config: Dict[str, Any]):
    """打印配置摘要"""
    print("\n" + "="*60)
    print("🎯 GPU重度访问模式配置摘要")
    print("="*60)
    
    if config['use_unified_memory']:
        print(f"✅ 统一内存: 已启用")
        print(f"🎯 访问模式: {config['unified_memory_access_pattern']}")
        print(f"💾 内存池大小: {config['unified_memory_size_gb']:.1f} GB")
        print(f"⚡ 优化级别: {config['memory_optimization_level']}")
        print(f"🔄 自动迁移: {'启用' if config['enable_auto_migration'] else '禁用'}")
        print(f"📊 性能监控: {'启用' if config['performance_monitoring'] else '禁用'}")
        print(f"🚀 零拷贝优化: {'启用' if config['zero_copy_optimization'] else '禁用'}")
        print(f"🛡️ 回退机制: {'启用' if config['fallback_to_traditional_gpu'] else '禁用'}")
    else:
        print(f"❌ 统一内存: 已禁用 (硬件不兼容)")
    
    print("="*60)

def main():
    """主函数"""
    print("🎯 GPU重度访问模式自动配置工具")
    print("="*50)
    
    # 检测GPU硬件
    print("\n[STEP 1] 🔍 检测GPU硬件...")
    gpu_info = get_gpu_info()
    
    if not gpu_info['available']:
        print("[ERROR] ❌ 未检测到可用的CUDA GPU，无法启用统一内存")
        return False
    
    # 检测系统内存
    print("\n[STEP 2] 🖥️ 检测系统内存...")
    system_memory = get_system_memory()
    
    # 计算最优配置
    print("\n[STEP 3] ⚙️ 计算最优配置...")
    unified_memory_config = calculate_optimal_memory_settings(gpu_info, system_memory)
    
    # 更新配置文件
    print("\n[STEP 4] 💾 更新配置文件...")
    success = update_gui_config(unified_memory_config)
    
    if success:
        print_configuration_summary(unified_memory_config)
        print("\n🎉 GPU重度访问模式配置完成！")
        print("💡 提示: 重启AI瞄准程序以应用新配置")
        return True
    else:
        print("\n❌ 配置失败，请检查错误信息")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)
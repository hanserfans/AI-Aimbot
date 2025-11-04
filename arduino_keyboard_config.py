#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arduino键盘控制器配置文件
用于优化连接和性能设置
"""

# Arduino连接配置
ARDUINO_CONFIG = {
    # 串口设置
    'baudrate': 9600,
    'timeout': 1.0,
    'write_timeout': 1.0,
    
    # 连接重试设置
    'max_retries': 3,
    'retry_delay': 0.5,
    
    # 设备识别
    'device_keywords': ['Arduino', 'Leonardo', 'Uno', 'Nano'],
    'preferred_ports': ['COM11', 'COM10', 'COM9', 'COM8'],
    
    # 命令设置
    'command_delay': 0.05,  # 命令间延迟
    'response_timeout': 0.5,  # 响应超时
    
    # WASD键释放设置
    'release_duration': 0.1,  # 释放后等待时间
    'force_release_on_fire': True,  # 开火前强制释放
}

# 自动开火配置
AUTO_FIRE_CONFIG = {
    # 键盘控制设置
    'use_arduino_keyboard': True,  # 优先使用Arduino键盘
    'keyboard_release_duration': 0.1,  # WASD键释放持续时间
    'fallback_to_win32': True,  # 失败时回退到Win32 API
    
    # 开火前准备
    'pre_fire_delay': 0.05,  # 开火前延迟
    'post_release_delay': 0.1,  # 释放后延迟
    
    # 调试设置
    'debug_mode': False,  # 调试模式
    'log_keyboard_actions': True,  # 记录键盘操作
}

# 日志配置
LOGGING_CONFIG = {
    'enable_arduino_logs': True,
    'enable_keyboard_logs': True,
    'enable_fire_logs': True,
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
}

def get_arduino_config():
    """获取Arduino配置"""
    return ARDUINO_CONFIG.copy()

def get_auto_fire_config():
    """获取自动开火配置"""
    return AUTO_FIRE_CONFIG.copy()

def get_logging_config():
    """获取日志配置"""
    return LOGGING_CONFIG.copy()

def update_config(config_type, **kwargs):
    """更新配置"""
    if config_type == 'arduino':
        ARDUINO_CONFIG.update(kwargs)
    elif config_type == 'auto_fire':
        AUTO_FIRE_CONFIG.update(kwargs)
    elif config_type == 'logging':
        LOGGING_CONFIG.update(kwargs)
    else:
        raise ValueError(f"未知的配置类型: {config_type}")

# 预设配置
PRESET_CONFIGS = {
    'performance': {
        'arduino': {
            'timeout': 0.5,
            'command_delay': 0.02,
            'response_timeout': 0.3,
        },
        'auto_fire': {
            'keyboard_release_duration': 0.05,
            'pre_fire_delay': 0.02,
            'post_release_delay': 0.05,
        }
    },
    
    'stability': {
        'arduino': {
            'timeout': 2.0,
            'command_delay': 0.1,
            'response_timeout': 1.0,
            'max_retries': 5,
        },
        'auto_fire': {
            'keyboard_release_duration': 0.2,
            'pre_fire_delay': 0.1,
            'post_release_delay': 0.15,
        }
    },
    
    'debug': {
        'arduino': {
            'timeout': 3.0,
            'command_delay': 0.2,
            'max_retries': 1,
        },
        'auto_fire': {
            'debug_mode': True,
        },
        'logging': {
            'log_level': 'DEBUG',
            'enable_arduino_logs': True,
            'enable_keyboard_logs': True,
            'enable_fire_logs': True,
        }
    }
}

def apply_preset(preset_name):
    """应用预设配置"""
    if preset_name not in PRESET_CONFIGS:
        raise ValueError(f"未知的预设配置: {preset_name}")
    
    preset = PRESET_CONFIGS[preset_name]
    
    for config_type, config_data in preset.items():
        update_config(config_type, **config_data)
    
    print(f"✅ 已应用预设配置: {preset_name}")

if __name__ == "__main__":
    print("Arduino键盘控制器配置")
    print("="*50)
    
    print("\n📊 当前配置:")
    print(f"Arduino配置: {ARDUINO_CONFIG}")
    print(f"自动开火配置: {AUTO_FIRE_CONFIG}")
    print(f"日志配置: {LOGGING_CONFIG}")
    
    print("\n🎛️ 可用预设:")
    for preset_name in PRESET_CONFIGS.keys():
        print(f"   • {preset_name}")
    
    print("\n💡 使用示例:")
    print("   from arduino_keyboard_config import apply_preset")
    print("   apply_preset('performance')  # 应用性能优化配置")
    print("   apply_preset('stability')    # 应用稳定性配置")
    print("   apply_preset('debug')        # 应用调试配置")
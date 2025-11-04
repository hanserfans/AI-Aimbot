"""
开火问题诊断工具
分析为什么只开了一枪而不是配置的多枪
"""

import time
import sys
import os

# 导入配置
from config import autoFire, autoFireShots, autoFireDelay, autoFireKey

def diagnose_fire_configuration():
    """诊断开火配置"""
    print("🔍 开火配置诊断")
    print("=" * 50)
    
    print(f"📋 当前配置:")
    print(f"   • autoFire (自动开火开关): {autoFire}")
    print(f"   • autoFireShots (开火数量): {autoFireShots}")
    print(f"   • autoFireDelay (开火延迟): {autoFireDelay}ms")
    print(f"   • autoFireKey (开火按键): {autoFireKey}")
    
    # 检查配置问题
    issues = []
    
    if not autoFire:
        issues.append("❌ autoFire 设置为 False - 自动开火已禁用")
    
    if autoFireShots <= 1:
        issues.append(f"❌ autoFireShots 设置为 {autoFireShots} - 只会开一枪")
    
    if autoFireDelay < 10:
        issues.append(f"⚠️ autoFireDelay 设置为 {autoFireDelay}ms - 延迟可能过短")
    
    if issues:
        print(f"\n🚨 发现问题:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print(f"\n✅ 配置看起来正常")
    
    return len(issues) == 0

def diagnose_trigger_system():
    """诊断扳机系统"""
    print(f"\n🎯 扳机系统诊断")
    print("=" * 50)
    
    try:
        from auto_trigger_system import get_trigger_system
        trigger_system = get_trigger_system()
        
        print(f"📋 扳机系统状态:")
        print(f"   • 扳机功能启用: {trigger_system.enabled}")
        print(f"   • 连发数量: {trigger_system.shots_per_trigger}")
        print(f"   • 连发间隔: {trigger_system.shot_interval}s")
        print(f"   • 冷却时间: {trigger_system.cooldown_duration}s")
        print(f"   • 当前是否在冷却: {trigger_system.is_on_cooldown()}")
        
        # 检查扳机系统问题
        issues = []
        
        if not trigger_system.enabled:
            issues.append("❌ 扳机系统已禁用")
        
        if trigger_system.shots_per_trigger <= 1:
            issues.append(f"❌ shots_per_trigger 设置为 {trigger_system.shots_per_trigger} - 只会开一枪")
        
        if trigger_system.cooldown_duration > 1.0:
            issues.append(f"⚠️ 冷却时间过长 ({trigger_system.cooldown_duration}s) - 可能影响连发")
        
        if trigger_system.is_on_cooldown():
            remaining = trigger_system.cooldown_duration - (time.time() - trigger_system.last_fire_time)
            issues.append(f"⚠️ 当前在冷却中，剩余 {remaining:.1f}s")
        
        if issues:
            print(f"\n🚨 发现问题:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print(f"\n✅ 扳机系统配置正常")
            
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ 扳机系统诊断失败: {e}")
        return False

def diagnose_driver_issues():
    """诊断驱动问题"""
    print(f"\n🖱️ 鼠标驱动诊断")
    print("=" * 50)
    
    # 检查Arduino驱动
    try:
        from arduino_mouse_driver import ArduinoMouseDriver
        arduino_driver = ArduinoMouseDriver()
        arduino_connected = arduino_driver.connect()
        
        if arduino_connected:
            print(f"✅ Arduino 驱动连接成功")
            
            # 测试点击功能
            print(f"🧪 测试Arduino点击功能...")
            result = arduino_driver.click_mouse("L")
            if result.get('success', False):
                print(f"✅ Arduino 点击测试成功")
            else:
                print(f"❌ Arduino 点击测试失败: {result.get('error', 'Unknown')}")
                
            arduino_driver.close()
        else:
            print(f"❌ Arduino 驱动连接失败")
            
    except Exception as e:
        print(f"❌ Arduino 驱动测试失败: {e}")
    
    # 检查G-Hub驱动
    try:
        from mouse_driver.MouseMove import ghub_click
        print(f"✅ G-Hub 驱动导入成功")
        
        # 注意：这里不实际测试点击，因为会真的点击
        print(f"ℹ️ G-Hub 驱动可用（未实际测试点击）")
        
    except Exception as e:
        print(f"❌ G-Hub 驱动导入失败: {e}")

def simulate_auto_fire():
    """模拟auto_fire函数执行"""
    print(f"\n🔥 模拟auto_fire函数执行")
    print("=" * 50)
    
    if not autoFire:
        print(f"❌ autoFire = False，函数直接返回")
        return
    
    try:
        from auto_trigger_system import get_trigger_system
        trigger_system = get_trigger_system()
        
        # 检查冷却时间
        if trigger_system.is_on_cooldown():
            remaining = trigger_system.cooldown_duration - (time.time() - trigger_system.last_fire_time)
            print(f"❌ 在冷却时间内，剩余 {remaining:.1f}s，函数返回")
            return
        
        print(f"✅ 通过冷却检查，开始执行开火循环")
        print(f"📋 将执行 {autoFireShots} 次开火，间隔 {autoFireDelay}ms")
        
        for i in range(autoFireShots):
            print(f"   🔥 第 {i+1} 发开火")
            
            if i < autoFireShots - 1:
                delay_seconds = autoFireDelay / 1000.0
                print(f"   ⏱️ 等待 {delay_seconds}s 后继续")
        
        print(f"✅ 模拟开火完成")
        print(f"⏱️ 设置冷却时间 {trigger_system.cooldown_duration}s")
        
    except Exception as e:
        print(f"❌ 模拟执行失败: {e}")

def check_possible_causes():
    """检查可能的原因"""
    print(f"\n🔍 可能的原因分析")
    print("=" * 50)
    
    causes = []
    
    # 配置问题
    if not autoFire:
        causes.append("配置问题: autoFire = False")
    
    if autoFireShots <= 1:
        causes.append(f"配置问题: autoFireShots = {autoFireShots}")
    
    # 扳机系统问题
    try:
        from auto_trigger_system import get_trigger_system
        trigger_system = get_trigger_system()
        
        if trigger_system.shots_per_trigger <= 1:
            causes.append(f"扳机系统问题: shots_per_trigger = {trigger_system.shots_per_trigger}")
        
        if trigger_system.cooldown_duration > 0.1:
            causes.append(f"冷却时间问题: 每次开火后有 {trigger_system.cooldown_duration}s 冷却")
            
    except:
        causes.append("扳机系统导入失败")
    
    # 驱动问题
    causes.append("驱动问题: 点击命令可能失败但没有正确处理")
    
    # 逻辑问题
    causes.append("逻辑问题: auto_fire() 可能被多次调用但被冷却机制阻止")
    
    if causes:
        print(f"🚨 可能的原因:")
        for i, cause in enumerate(causes, 1):
            print(f"   {i}. {cause}")
    
    print(f"\n💡 建议解决方案:")
    print(f"   1. 检查 config.py 中的 autoFireShots 设置")
    print(f"   2. 检查 auto_trigger_system.py 中的 shots_per_trigger 设置")
    print(f"   3. 调整冷却时间设置")
    print(f"   4. 检查驱动连接状态")
    print(f"   5. 查看程序运行时的控制台输出")

def main():
    print("🔫 开火问题诊断工具")
    print("=" * 60)
    print("分析为什么只开了一枪而不是配置的多枪")
    print("=" * 60)
    
    # 执行各项诊断
    config_ok = diagnose_fire_configuration()
    trigger_ok = diagnose_trigger_system()
    diagnose_driver_issues()
    simulate_auto_fire()
    check_possible_causes()
    
    print(f"\n" + "=" * 60)
    if config_ok and trigger_ok:
        print(f"✅ 配置看起来正常，问题可能在驱动或执行逻辑")
    else:
        print(f"❌ 发现配置问题，请根据上述建议进行修复")
    print(f"=" * 60)

if __name__ == "__main__":
    main()
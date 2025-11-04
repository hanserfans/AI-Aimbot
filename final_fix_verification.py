#!/usr/bin/env python3
"""
最终修复验证脚本
验证所有语法错误和变量定义问题都已解决
"""

import sys
import traceback

def verify_all_fixes():
    """验证所有修复"""
    print("=" * 60)
    print("🔧 最终修复验证")
    print("=" * 60)
    
    fixes_status = []
    
    # 1. 语法检查
    print("1️⃣ 语法检查...")
    try:
        import py_compile
        py_compile.compile('main_onnx.py', doraise=True)
        fixes_status.append("✅ 语法检查通过")
        print("   ✅ 语法检查通过")
    except Exception as e:
        fixes_status.append(f"❌ 语法错误: {e}")
        print(f"   ❌ 语法错误: {e}")
    
    # 2. 检查关键修复点
    print("\n2️⃣ 检查关键修复点...")
    try:
        with open('main_onnx.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查字典键修复
        if "offset_x = offset_info['pixel']['x']" in content:
            fixes_status.append("✅ offset_x 字典键修复")
            print("   ✅ offset_x 字典键修复")
        else:
            fixes_status.append("❌ offset_x 字典键未修复")
            print("   ❌ offset_x 字典键未修复")
        
        if "offset_y = offset_info['pixel']['y']" in content:
            fixes_status.append("✅ offset_y 字典键修复")
            print("   ✅ offset_y 字典键修复")
        else:
            fixes_status.append("❌ offset_y 字典键未修复")
            print("   ❌ offset_y 字典键未修复")
        
        if "distance = offset_info['pixel']['distance']" in content:
            fixes_status.append("✅ distance 变量定义修复")
            print("   ✅ distance 变量定义修复")
        else:
            fixes_status.append("❌ distance 变量定义未修复")
            print("   ❌ distance 变量定义未修复")
        
        # 检查激活键逻辑简化
        if "elif caps_lock_pressed:" in content:
            fixes_status.append("✅ 激活键检测逻辑简化")
            print("   ✅ 激活键检测逻辑简化")
        else:
            fixes_status.append("❌ 激活键检测逻辑未简化")
            print("   ❌ 激活键检测逻辑未简化")
            
    except Exception as e:
        fixes_status.append(f"❌ 文件检查失败: {e}")
        print(f"   ❌ 文件检查失败: {e}")
    
    # 3. 测试坐标系统
    print("\n3️⃣ 测试坐标系统...")
    try:
        from coordinate_system import get_coordinate_system
        coord_system = get_coordinate_system()
        
        # 测试函数调用
        offset_info = coord_system.calculate_crosshair_to_target_offset(170.0, 150.0)
        
        # 测试字典访问
        test_x = offset_info['pixel']['x']
        test_y = offset_info['pixel']['y']
        test_distance = offset_info['pixel']['distance']
        
        fixes_status.append("✅ 坐标系统测试通过")
        print("   ✅ 坐标系统测试通过")
        print(f"   📊 测试结果: x={test_x:.1f}, y={test_y:.1f}, distance={test_distance:.1f}")
        
    except Exception as e:
        fixes_status.append(f"❌ 坐标系统测试失败: {e}")
        print(f"   ❌ 坐标系统测试失败: {e}")
    
    # 4. 总结
    print("\n" + "=" * 60)
    print("📋 修复状态总结")
    print("=" * 60)
    
    success_count = len([s for s in fixes_status if s.startswith("✅")])
    total_count = len(fixes_status)
    
    for status in fixes_status:
        print(f"  {status}")
    
    print(f"\n📊 修复进度: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 所有修复完成！")
        print("💡 现在可以安全地运行 main_onnx.py 了")
        print("\n🔧 修复内容总结:")
        print("  1. 修复了第664行未终止的字符串字面量")
        print("  2. 修复了字典键访问错误 (pixel_offset_x → pixel.x)")
        print("  3. 添加了缺失的 distance 变量定义")
        print("  4. 保持了激活键检测逻辑的简化")
        print("  5. 保持了连续移动修复功能")
        return True
    else:
        print(f"\n❌ 还有 {total_count - success_count} 个问题需要解决")
        return False

if __name__ == "__main__":
    success = verify_all_fixes()
    
    if success:
        print("\n🚀 准备就绪！可以重新启动自瞄程序了。")
    else:
        print("\n⚠️  请解决剩余问题后再运行程序。")
    
    print("\n" + "=" * 60)
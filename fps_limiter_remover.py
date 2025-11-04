#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FPS限制器移除工具
移除或优化主要文件中的性能限制，释放351+ FPS的真正潜力
"""

import re
from pathlib import Path

class FPSLimiterRemover:
    """FPS限制器移除器"""
    
    def __init__(self):
        # 需要优化的主要文件
        self.target_files = [
            "main_onnx.py",
            "yolov8_headshot_aimbot.py", 
            "smart_aimbot.py",
            "main_onnx_fixed.py",
            "main_onnx_backup.py"
        ]
        
        # 优化规则
        self.optimization_rules = [
            {
                "pattern": r"time\.sleep\(0\.01\)",
                "replacement": "time.sleep(0.001)  # 高性能模式：1ms延迟",
                "description": "将10ms延迟优化为1ms"
            },
            {
                "pattern": r"if loop_time < 0\.016:",
                "replacement": "if loop_time < 0.003:  # 高性能模式：333+ FPS",
                "description": "移除60FPS限制，支持333+ FPS"
            },
            {
                "pattern": r"await asyncio\.sleep\(0\.016 - loop_time\)",
                "replacement": "await asyncio.sleep(max(0.001, 0.003 - loop_time))  # 高性能模式",
                "description": "优化异步睡眠时间"
            }
        ]
    
    def analyze_file(self, file_path):
        """分析文件中的性能限制"""
        if not file_path.exists():
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # 检查time.sleep(0.01)
                if "time.sleep(0.01)" in line:
                    issues.append({
                        "line": i,
                        "content": line.strip(),
                        "type": "10ms延迟限制",
                        "severity": "medium"
                    })
                
                # 检查60FPS限制
                if "0.016" in line and ("loop_time" in line or "sleep" in line):
                    issues.append({
                        "line": i,
                        "content": line.strip(),
                        "type": "60FPS限制器",
                        "severity": "high"
                    })
                
                # 检查其他可能的限制
                if "time.sleep(0.1)" in line:
                    issues.append({
                        "line": i,
                        "content": line.strip(),
                        "type": "100ms延迟限制",
                        "severity": "high"
                    })
            
            return issues
            
        except Exception as e:
            print(f"❌ 分析文件失败 {file_path}: {e}")
            return None
    
    def optimize_file(self, file_path):
        """优化单个文件"""
        if not file_path.exists():
            return False, []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            changes = []
            
            # 应用优化规则
            for rule in self.optimization_rules:
                pattern = rule['pattern']
                replacement = rule['replacement']
                description = rule['description']
                
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    changes.append(description)
            
            # 如果有变化，保存文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, changes
            else:
                return False, []
                
        except Exception as e:
            print(f"❌ 优化文件失败 {file_path}: {e}")
            return False, []
    
    def run_analysis(self):
        """运行完整分析"""
        print("🔍 分析FPS限制器...")
        print("=" * 60)
        
        total_issues = 0
        
        for file_name in self.target_files:
            file_path = Path(file_name)
            print(f"\n📁 分析文件: {file_name}")
            
            issues = self.analyze_file(file_path)
            if issues is None:
                print("   ⚠️ 文件不存在或无法读取")
                continue
            
            if not issues:
                print("   ✅ 未发现性能限制")
                continue
            
            print(f"   ⚠️ 发现 {len(issues)} 个性能限制:")
            for issue in issues:
                severity_icon = "🔴" if issue['severity'] == 'high' else "🟡"
                print(f"      {severity_icon} 第{issue['line']}行: {issue['type']}")
                print(f"         {issue['content']}")
            
            total_issues += len(issues)
        
        print(f"\n📊 总计发现 {total_issues} 个性能限制点")
        return total_issues
    
    def run_optimization(self):
        """运行完整优化"""
        print("\n⚡ 开始FPS限制器移除...")
        print("=" * 60)
        
        total_optimized = 0
        total_changes = 0
        
        for file_name in self.target_files:
            file_path = Path(file_name)
            print(f"\n🔧 优化文件: {file_name}")
            
            success, changes = self.optimize_file(file_path)
            
            if success:
                print(f"   ✅ 优化成功，应用了 {len(changes)} 个改进:")
                for change in changes:
                    print(f"      • {change}")
                total_optimized += 1
                total_changes += len(changes)
            else:
                if file_path.exists():
                    print("   ℹ️ 无需优化")
                else:
                    print("   ⚠️ 文件不存在")
        
        print(f"\n🎉 优化完成！")
        print(f"📁 已优化 {total_optimized} 个文件")
        print(f"⚡ 应用了 {total_changes} 个性能改进")
        
        return total_optimized, total_changes

def main():
    """主函数"""
    print("🚀 FPS限制器移除工具")
    print("释放351+ FPS的真正潜力！")
    
    remover = FPSLimiterRemover()
    
    # 1. 分析现状
    total_issues = remover.run_analysis()
    
    if total_issues > 0:
        # 2. 执行优化
        total_optimized, total_changes = remover.run_optimization()
        
        print("\n" + "=" * 60)
        print("🔥 高性能模式已全面激活！")
        print("💡 建议:")
        print("   1. 重启AI瞄准程序")
        print("   2. 监控GPU温度")
        print("   3. 观察实际FPS表现")
        print("   4. 如有不稳定可适当调整")
    else:
        print("\n✅ 系统已处于最优状态，无需进一步优化！")

if __name__ == "__main__":
    main()
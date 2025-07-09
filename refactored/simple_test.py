#!/usr/bin/env python3
"""
简化的功能验证测试
"""

import sys
import os
from pathlib import Path

# 添加包路径，并确保导入顺序
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 删除可能冲突的路径
if str(project_root.parent) in sys.path:
    sys.path.remove(str(project_root.parent))

def test_imports():
    """测试基本导入"""
    print("🧪 测试模块导入...")
    
    try:
        from ai_companion.core.config import ConfigManager, AIServiceConfig
        print("✅ 核心配置模块导入成功")
        
        from ai_companion.core.system_info import SystemInfoCollector
        print("✅ 系统信息模块导入成功")
        
        from ai_companion.analyzers.context_analyzer import ContextAnalyzer
        print("✅ 上下文分析模块导入成功")
        
        from ai_companion.providers.ai_provider import AIProviderFactory
        print("✅ AI提供商模块导入成功")
        
        from ai_companion import AICompanion
        print("✅ 主应用模块导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试基本功能...")
    
    try:
        from ai_companion import AICompanion
        
        # 创建实例
        companion = AICompanion("/tmp/test_config.json")
        print("✅ AI伴侣实例创建成功")
        
        # 测试配置设置
        companion.set_api_config("test", "https://test.com", "test-model", "test-key")
        print("✅ API配置设置成功")
        
        # 测试配置显示
        companion.show_config()
        print("✅ 配置显示正常")
        
        return True
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行简化测试"""
    print("🚀 开始运行简化测试...")
    print()
    
    success = True
    
    if not test_imports():
        success = False
    print()
    
    if not test_basic_functionality():
        success = False
    print()
    
    if success:
        print("🎉 所有测试通过！重构版本基本功能正常")
    else:
        print("❌ 部分测试失败")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

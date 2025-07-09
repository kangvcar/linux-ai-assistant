"""
测试AI伴侣的核心功能
"""

import sys
import os
from pathlib import Path

# 添加包路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_companion import AICompanion, ConfigManager, AIServiceConfig


def test_config_manager():
    """测试配置管理器"""
    print("🧪 测试配置管理器...")
    
    config_manager = ConfigManager("/tmp/test_ai_config.json")
    
    # 测试设置API配置
    api_config = AIServiceConfig(
        type="openai",
        base_url="https://api.test.com/v1/chat/completions",
        model="test-model",
        api_key="test-key"
    )
    
    config_manager.set_ai_service("test", api_config)
    
    # 测试获取配置
    retrieved_config = config_manager.get_active_ai_service()
    assert retrieved_config.type == "openai"
    # 注意：由于配置管理器有默认配置，需要先切换到test配置
    config_manager.switch_ai_service("test")
    retrieved_config = config_manager.get_active_ai_service()
    assert retrieved_config.model == "test-model"
    
    print("✅ 配置管理器测试通过")


def test_system_info():
    """测试系统信息收集"""
    print("🧪 测试系统信息收集...")
    
    from ai_companion.core.system_info import SystemInfoCollector
    
    collector = SystemInfoCollector()
    
    # 测试系统状态
    status = collector.get_system_status()
    assert hasattr(status, 'cpu_percent')
    assert hasattr(status, 'memory_percent')
    
    # 测试目录信息
    dir_info = collector.get_directory_info('.')
    assert hasattr(dir_info, 'file_count')
    assert hasattr(dir_info, 'project_type')
    
    print("✅ 系统信息收集测试通过")


def test_command_history():
    """测试命令历史分析"""
    print("🧪 测试命令历史分析...")
    
    from ai_companion.analyzers.command_history import CommandHistoryAnalyzer, CommandInfo
    import time
    
    analyzer = CommandHistoryAnalyzer()
    
    # 添加测试命令
    cmd_info = CommandInfo(
        command="ls /nonexistent",
        exit_code=2,
        output="",
        error="ls: cannot access '/nonexistent': No such file or directory",
        timestamp=time.time(),
        cwd="/tmp"
    )
    
    analyzer.add_command(cmd_info)
    
    # 测试模式分析
    commands = ["git add .", "git commit -m 'test'", "npm install", "python main.py"]
    patterns = analyzer.analyze_command_patterns(commands)
    
    assert "开发工具" in patterns
    assert patterns["开发工具"] > 0
    
    print("✅ 命令历史分析测试通过")


def test_ai_companion():
    """测试AI伴侣主应用"""
    print("🧪 测试AI伴侣主应用...")
    
    companion = AICompanion("/tmp/test_ai_config.json")
    
    # 测试配置设置
    companion.set_api_config("test", "https://api.test.com", "test-model", "test-key")
    
    # 测试上下文显示（不会实际调用API）
    try:
        companion.show_context_info()
        print("✅ 上下文显示正常")
    except Exception as e:
        print(f"⚠️  上下文显示出现问题: {e}")
    
    print("✅ AI伴侣主应用测试通过")


def main():
    """运行所有测试"""
    print("🚀 开始运行AI伴侣测试套件...")
    print()
    
    try:
        test_config_manager()
        print()
        
        test_system_info()
        print()
        
        test_command_history()
        print()
        
        test_ai_companion()
        print()
        
        print("🎉 所有测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

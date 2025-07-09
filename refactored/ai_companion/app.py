"""
AI伴侣主应用类
整合所有功能模块，提供统一的接口
"""

import sys
import base64
from typing import Optional

from .core.config import ConfigManager, AIServiceConfig
from .analyzers.context_analyzer import ContextAnalyzer
from .analyzers.error_analyzer import ErrorAnalyzer
from .shell.integration import ShellIntegrationManager
from .providers.ai_provider import AIProviderFactory


class AICompanion:
    """AI伴侣主应用"""
    
    def __init__(self, config_path: str = "~/.ai_config.json"):
        # 初始化各个模块
        self.config_manager = ConfigManager(config_path)
        self.context_analyzer = ContextAnalyzer()
        self.error_analyzer = ErrorAnalyzer(self.config_manager, self.context_analyzer)
        self.shell_manager = ShellIntegrationManager()
    
    def monitor_command(self, command: str, exit_code: int, stderr_content: str = ""):
        """监控命令执行结果（Shell钩子调用）"""
        # 解码stderr内容
        decoded_stderr = self._decode_stderr(stderr_content)
        
        # 添加到命令历史
        self.context_analyzer.add_command_to_history(command, exit_code, "", decoded_stderr)
        
        # 如果命令失败且启用了自动错误分析，立即分析
        if (exit_code != 0 and 
            self.config_manager.get_features().auto_error_analysis):
            
            suggestion = self.error_analyzer.analyze_error(command, exit_code, decoded_stderr)
            if suggestion:
                self._display_suggestion(suggestion, command)
    
    def ask_question(self, question: str) -> str:
        """处理用户提问"""
        return self.error_analyzer.ask_question(question)
    
    def show_context_info(self):
        """显示详细的上下文信息"""
        context = self.context_analyzer.get_full_context()
        formatted_context = self.context_analyzer.format_display_context(context)
        
        print("🔍 \\033[1;36m上下文信息详览\\033[0m")
        print(formatted_context)
    
    def show_config(self):
        """显示当前配置"""
        services = self.config_manager.get_all_services()
        active_service_name = self.config_manager._config.get('active_ai_service', '无')
        
        print("所有API配置:")
        for name, config in services.items():
            active_marker = " (激活)" if name == active_service_name else ""
            print(f"  配置名称: {name}{active_marker}")
            print(f"    服务类型: {config.type}")
            print(f"    API地址: {config.base_url}")
            print(f"    模型: {config.model}")
            api_key_display = f"{config.api_key[:10]}..." if config.api_key else "未设置"
            print(f"    API Key: {api_key_display}")
            print(f"    超时时间: {config.timeout}秒")
            print()
        
        print(f"当前激活的配置: {active_service_name}")
        features = self.config_manager.get_features()
        print(f"自动错误分析: {features.auto_error_analysis}")
    
    def test_api_connection(self):
        """测试API连接"""
        try:
            test_response = self.ask_question("你好，请回复'连接成功'")
            if test_response and "连接成功" in test_response:
                print("✅ API连接测试成功")
            else:
                print(f"⚠️  API连接可能有问题，响应: {test_response}")
        except Exception as e:
            print(f"❌ API连接测试失败: {e}")
    
    def set_api_config(self, api_type: str, base_url: str, model: str, api_key: str, name: str = "default"):
        """设置API配置"""
        try:
            config = AIServiceConfig(
                type=api_type,
                base_url=base_url,
                model=model,
                api_key=api_key
            )
            
            self.config_manager.set_ai_service(name, config)
            print(f"✅ API配置 '{name}' 已保存。")
            
            # 如果是默认配置或第一个配置，设为激活状态
            current_active = self.config_manager._config.get('active_ai_service')
            if not current_active or name == "default":
                self.config_manager.switch_ai_service(name)
                print(f"✅ 配置 '{name}' 已被激活。")
                
        except ValueError as e:
            print(f"❌ 配置错误: {e}")
        except Exception as e:
            print(f"❌ 设置配置失败: {e}")
    
    def switch_api_service(self, name: str):
        """切换API服务"""
        if self.config_manager.switch_ai_service(name):
            print(f"✅ 已切换到API配置: {name}")
        else:
            available_services = list(self.config_manager.get_all_services().keys())
            print(f"❌ 未找到名为 '{name}' 的API配置。")
            if available_services:
                print(f"可用的配置: {', '.join(available_services)}")
    
    def install_shell_hooks(self):
        """安装Shell钩子"""
        return self.shell_manager.install_shell_hooks()
    
    def uninstall_shell_hooks(self):
        """卸载Shell钩子"""
        return self.shell_manager.uninstall_shell_hooks()
    
    def _decode_stderr(self, stderr_content: str) -> str:
        """解码stderr内容"""
        if not stderr_content:
            return ""
        
        try:
            # 尝试base64解码
            return base64.b64decode(stderr_content).decode('utf-8')
        except:
            # 如果解码失败，直接使用原始内容
            return stderr_content
    
    def _display_suggestion(self, suggestion: str, command: str):
        """显示AI建议"""
        print(f"🤖 \\033[1;36mAI伴侣建议\\033[0m (命令: \\033[1;33m{command}\\033[0m)")
        
        # 处理建议内容，使其更易读
        lines = suggestion.strip().split('\\n')
        for line in lines:
            if line.strip():
                if '```' in line:
                    continue
                elif line.strip().startswith('`') and line.strip().endswith('`'):
                    code = line.strip()[1:-1]
                    print(f"   \\033[1;32m{code}\\033[0m")
                elif line.strip().startswith(('**错误原因：**', '**解决方案：**', '**后续建议：**')):
                    print(f"\\033[1;34m{line}\\033[0m")
                else:
                    print(f"   {line}")
        
        print(f"💡 \\033[2m输入 'ask \"更多问题\"' 可以继续咨询\\033[0m")
        sys.stdout.flush()
    
    def get_supported_ai_types(self) -> list:
        """获取支持的AI服务类型"""
        return AIProviderFactory.get_supported_types()

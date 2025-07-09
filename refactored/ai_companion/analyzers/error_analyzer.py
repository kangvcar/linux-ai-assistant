"""
错误分析器
负责构建AI提示词和分析命令错误
"""

import time
from typing import Optional

from ..analyzers.context_analyzer import ContextAnalyzer, FullContext
from ..providers.ai_provider import AIProviderFactory
from ..core.config import ConfigManager


class ErrorAnalyzer:
    """错误分析器"""
    
    def __init__(self, config_manager: ConfigManager, context_analyzer: ContextAnalyzer):
        self.config_manager = config_manager
        self.context_analyzer = context_analyzer
        self.last_analyzed_command = None
        self.last_analyzed_time = 0
    
    def analyze_error(self, command: str, exit_code: int, error_output: str = "") -> Optional[str]:
        """分析命令错误"""
        # 去重检查
        if not self._should_analyze(command, exit_code):
            return None
        
        try:
            # 获取上下文
            context = self.context_analyzer.get_full_context()
            
            # 构建提示词
            prompt = self._build_error_prompt(command, exit_code, error_output, context)
            
            # 调用AI分析
            ai_service_config = self.config_manager.get_active_ai_service()
            provider = AIProviderFactory.create_provider(ai_service_config)
            
            suggestion = provider.call_api(prompt)
            
            # 更新去重信息
            self._update_analysis_cache(command, exit_code)
            
            return suggestion
            
        except Exception as e:
            return f"分析错误时出现问题: {e}"
    
    def ask_question(self, question: str) -> str:
        """处理用户直接提问"""
        try:
            # 获取上下文
            context = self.context_analyzer.get_full_context()
            
            # 构建提示词
            prompt = self._build_question_prompt(question, context)
            
            # 调用AI
            ai_service_config = self.config_manager.get_active_ai_service()
            provider = AIProviderFactory.create_provider(ai_service_config)
            
            return provider.call_api(prompt)
            
        except Exception as e:
            return f"处理问题时出现错误: {e}"
    
    def _should_analyze(self, command: str, exit_code: int) -> bool:
        """判断是否应该分析此错误"""
        current_time = time.time()
        command_key = f"{command}_{exit_code}"
        
        # 去重：如果是相同的命令和错误码，且在5秒内，则忽略
        if (self.last_analyzed_command == command_key and 
            current_time - self.last_analyzed_time < 5):
            return False
        
        # 使用上下文分析器的判断逻辑
        return self.context_analyzer.should_analyze_error(command, exit_code)
    
    def _update_analysis_cache(self, command: str, exit_code: int):
        """更新分析缓存"""
        current_time = time.time()
        command_key = f"{command}_{exit_code}"
        self.last_analyzed_command = command_key
        self.last_analyzed_time = current_time
    
    def _build_error_prompt(self, command: str, exit_code: int, error_output: str, context: FullContext) -> str:
        """构建错误分析提示词"""
        # 获取模型名称
        model_name = self.config_manager.get_active_ai_service().model
        
        # 构建上下文信息
        context_info = self.context_analyzer.build_detailed_context_info(context)
        history_context = self.context_analyzer.build_command_context(context)
        
        prompt = f"""你是一个智能的Linux终端AI伴侣，专门帮助用户解决Linux命令问题。请用中文回答，并保持简洁实用。
当前模型: {model_name}
{context_info}{history_context}

刚才执行的命令失败了：
命令: {command}
退出码: {exit_code}
错误输出: {error_output if error_output else '无'}

请根据当前环境和操作上下文，特别是最近的命令序列和操作模式，按以下格式回答：

**错误原因：** [结合当前环境、错误输出和操作上下文分析错误原因]

**解决方案：** 
[提供1-2个针对当前环境和操作流程的具体修复命令]

**后续建议：** [基于你的工作模式、目录环境和命令序列，建议接下来可能需要的操作]

请特别注意用户的操作模式和意图，提供连贯性的建议。"""
        
        return prompt
    
    def _build_question_prompt(self, question: str, context: FullContext) -> str:
        """构建问答提示词"""
        # 获取模型名称
        model_name = self.config_manager.get_active_ai_service().model
        
        # 构建上下文摘要
        context_summary = self.context_analyzer.build_context_summary(context)
        
        # 分析最近的命令模式
        pattern_summary = ""
        if context.command_patterns:
            top_patterns = list(context.command_patterns.items())[:2]
            pattern_summary = f"\n最近主要操作: {', '.join([f'{name}({count}次)' for name, count in top_patterns])}"
        
        recent_commands_str = ' → '.join(context.recent_commands[-10:]) if context.recent_commands else '无'
        
        prompt = f"""你是一个智能的Linux终端AI伴侣，用中文回答问题。
当前模型: {model_name}
{context_summary}{pattern_summary}

最近10条命令: {recent_commands_str}

用户问题: {question}

请根据当前环境、工作上下文和最近的操作模式，提供针对性的Linux命令和建议。如果问题与当前环境或最近的操作相关，请特别说明。保持回答简洁明了。"""
        
        return prompt

"""
AI Companion - Linux终端AI伴侣

一个智能的Linux终端伴侣，提供：
- 自动错误分析和解决建议
- 智能命令建议
- 上下文感知的AI交互
- Shell集成和命令监控
"""

from .app import AICompanion
from .core.config import ConfigManager, AIServiceConfig, FeatureConfig
from .providers.ai_provider import AIProviderFactory

__version__ = "2.0.0"
__author__ = "AI Companion Team"

__all__ = [
    'AICompanion',
    'ConfigManager',
    'AIServiceConfig',
    'FeatureConfig',
    'AIProviderFactory'
]

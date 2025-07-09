"""
AI Companion 配置管理模块
负责配置文件的加载、保存和验证
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AIServiceConfig:
    """AI服务配置"""
    type: str
    base_url: str
    model: str
    api_key: Optional[str] = None
    timeout: int = 30

    def __post_init__(self):
        """配置验证"""
        if not self.type or not self.base_url or not self.model:
            raise ValueError("type, base_url, model 字段不能为空")
        
        if self.timeout <= 0:
            raise ValueError("timeout 必须大于0")


@dataclass
class FeatureConfig:
    """功能配置"""
    auto_error_analysis: bool = True
    command_suggestion: bool = True
    context_aware: bool = True
    chinese_help: bool = True


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "~/.ai_config.json"):
        self.config_path = Path(config_path).expanduser()
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "ai_services": {
                "default": {
                    "type": "openai",
                    "base_url": "https://api.deepbricks.ai/v1/chat/completions",
                    "model": "gpt-4o-mini",
                    "api_key": "sk-97RxyS9R2dsqFTUxcUZOpZwhnbjQCSOaFboooKDeTv5nHJgg",
                    "timeout": 30
                }
            },
            "active_ai_service": "default",
            "features": {
                "auto_error_analysis": True,
                "command_suggestion": True,
                "context_aware": True,
                "chinese_help": True
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return {**default_config, **json.load(f)}
            except (json.JSONDecodeError, IOError):
                pass
        return default_config
    
    def save_config(self):
        """保存配置文件"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    def get_active_ai_service(self) -> AIServiceConfig:
        """获取当前激活的AI服务配置"""
        active_service_name = self._config.get('active_ai_service', 'default')
        service_dict = self._config.get('ai_services', {}).get(active_service_name, {})
        
        if not service_dict:
            raise ValueError(f"未找到AI服务配置: {active_service_name}")
        
        return AIServiceConfig(**service_dict)
    
    def set_ai_service(self, name: str, config: AIServiceConfig):
        """设置AI服务配置"""
        if 'ai_services' not in self._config:
            self._config['ai_services'] = {}
        
        self._config['ai_services'][name] = asdict(config)
        
        # 如果是第一个配置，设为激活状态
        if not self._config.get('active_ai_service'):
            self._config['active_ai_service'] = name
        
        self.save_config()
    
    def switch_ai_service(self, name: str) -> bool:
        """切换激活的AI服务"""
        if name in self._config.get('ai_services', {}):
            self._config['active_ai_service'] = name
            self.save_config()
            return True
        return False
    
    def get_features(self) -> FeatureConfig:
        """获取功能配置"""
        features_dict = self._config.get('features', {})
        return FeatureConfig(**features_dict)
    
    def set_features(self, features: FeatureConfig):
        """设置功能配置"""
        self._config['features'] = asdict(features)
        self.save_config()
    
    def get_all_services(self) -> Dict[str, AIServiceConfig]:
        """获取所有AI服务配置"""
        services = {}
        for name, config_dict in self._config.get('ai_services', {}).items():
            services[name] = AIServiceConfig(**config_dict)
        return services
    
    def list_services(self) -> Dict[str, str]:
        """列出所有服务及其状态"""
        result = {}
        active_service = self._config.get('active_ai_service')
        
        for name in self._config.get('ai_services', {}):
            status = "激活" if name == active_service else "可用"
            result[name] = status
        
        return result

"""
AI服务提供商接口
支持OpenAI兼容API和Ollama等不同的AI服务
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from abc import ABC, abstractmethod
from typing import Dict, Any

from ..core.config import AIServiceConfig


class AIProvider(ABC):
    """AI服务提供商抽象基类"""
    
    def __init__(self, config: AIServiceConfig):
        self.config = config
    
    @abstractmethod
    def call_api(self, prompt: str) -> str:
        """调用AI API"""
        pass
    
    def _http_request(self, url: str, data: dict = None, headers: dict = None, timeout: int = 30) -> Dict:
        """发送HTTP请求"""
        try:
            # 准备请求数据
            if data:
                json_data = json.dumps(data).encode('utf-8')
            else:
                json_data = None
            
            # 创建请求
            req = urllib.request.Request(url, data=json_data)
            
            # 设置请求头
            if headers:
                for key, value in headers.items():
                    req.add_header(key, value)
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = {
                    'status_code': response.getcode(),
                    'content': response.read().decode('utf-8')
                }
                return result
                
        except urllib.error.HTTPError as e:
            return {
                'status_code': e.code,
                'content': e.read().decode('utf-8') if e.fp else '',
                'error': str(e)
            }
        except Exception as e:
            return {
                'status_code': 0,
                'content': '',
                'error': str(e)
            }


class OpenAIProvider(AIProvider):
    """OpenAI兼容API提供商"""
    
    def call_api(self, prompt: str) -> str:
        """调用OpenAI兼容API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.config.api_key}'
            }
            
            data = {
                "model": self.config.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = self._http_request(
                self.config.base_url,
                data=data,
                headers=headers,
                timeout=self.config.timeout
            )
            
            if response['status_code'] == 200:
                result = json.loads(response['content'])
                return result['choices'][0]['message']['content'].strip()
            else:
                error_info = f"API调用失败: {response['status_code']}"
                if 'error' in response:
                    error_info += f" - {response['error']}"
                if response.get('content'):
                    try:
                        error_content = json.loads(response['content'])
                        if 'error' in error_content:
                            error_info += f" - {error_content['error'].get('message', '')}"
                    except:
                        error_info += f" - Response: {response['content'][:200]}"
                return error_info
                
        except Exception as e:
            return f"API调用失败: {e}"


class OllamaProvider(AIProvider):
    """Ollama API提供商"""
    
    def call_api(self, prompt: str) -> str:
        """调用Ollama API"""
        try:
            data = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False
            }
            
            # Ollama API通常不需要Authorization header
            headers = {'Content-Type': 'application/json'}
            
            response = self._http_request(
                f"{self.config.base_url.rstrip('/')}/api/generate",
                data=data,
                headers=headers,
                timeout=self.config.timeout
            )
            
            if response['status_code'] == 200:
                result = json.loads(response['content'])
                return result['response'].strip()
            else:
                return f"Ollama API调用失败: {response['status_code']} - {response.get('content', '')}"
                
        except Exception as e:
            return f"连接Ollama失败: {e}"


class AnthropicProvider(AIProvider):
    """Anthropic API提供商"""
    
    def call_api(self, prompt: str) -> str:
        """调用Anthropic API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.config.api_key,
                'anthropic-version': '2023-06-01'
            }
            
            data = {
                "model": self.config.model,
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = self._http_request(
                self.config.base_url,
                data=data,
                headers=headers,
                timeout=self.config.timeout
            )
            
            if response['status_code'] == 200:
                result = json.loads(response['content'])
                return result['content'][0]['text'].strip()
            else:
                return f"Anthropic API调用失败: {response['status_code']}"
                
        except Exception as e:
            return f"Anthropic API调用失败: {e}"


class AIProviderFactory:
    """AI提供商工厂"""
    
    providers = {
        'openai': OpenAIProvider,
        'ollama': OllamaProvider,
        'anthropic': AnthropicProvider,
        'custom': OpenAIProvider,  # 自定义API通常兼容OpenAI格式
    }
    
    @classmethod
    def create_provider(cls, config: AIServiceConfig) -> AIProvider:
        """创建AI提供商实例"""
        provider_class = cls.providers.get(config.type.lower())
        if not provider_class:
            raise ValueError(f"不支持的AI服务类型: {config.type}")
        
        return provider_class(config)
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的AI服务类型"""
        return list(cls.providers.keys())

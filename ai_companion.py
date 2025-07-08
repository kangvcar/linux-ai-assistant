#!/usr/bin/env python3
"""
Linux终端AI伴侣 - 独立版本（无外部依赖）
"""

import os
import sys
import json
import subprocess
import time
import urllib.request
import urllib.parse
import urllib.error
import shutil
from pathlib import Path
from typing import Dict, List, Optional

class LinuxAICompanion:
    def __init__(self, config_path: str = "~/.ai_config.json"):
        self.config_path = Path(config_path).expanduser()
        self.config = self.load_config()
        self.command_history = []
        self.context_cache = {}
        self.last_analyzed_command = None
        self.last_analyzed_time = 0
        
    def load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "ai_service": {
                "type": "custom_api",
                "base_url": "https://api.deepbricks.ai/v1/chat/completions",
                "model": "gpt-4o-mini",
                "api_key": "sk-97RxyS9R2dsqFTUxcUZOpZwhnbjQCSOaFboooKDeTv5nHJgg",
                "timeout": 30
            },
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
            except Exception:
                pass
        return default_config
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get_system_info_native(self) -> Dict:
        """使用原生方法获取系统信息"""
        try:
            info = {}
            
            # 获取内存信息
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    mem_total = int([line for line in meminfo.split('\n') if 'MemTotal' in line][0].split()[1]) * 1024
                    mem_available = int([line for line in meminfo.split('\n') if 'MemAvailable' in line][0].split()[1]) * 1024
                    info['memory_usage'] = round((mem_total - mem_available) / mem_total * 100, 1)
                    info['memory_total_gb'] = round(mem_total / (1024**3), 1)
                    info['memory_available_gb'] = round(mem_available / (1024**3), 1)
            except:
                info['memory_usage'] = 0
                info['memory_total_gb'] = 0
                info['memory_available_gb'] = 0
            
            # 获取磁盘信息
            try:
                stat = shutil.disk_usage('/')
                info['disk_usage'] = round(stat.used / stat.total * 100, 1)
                info['disk_total_gb'] = round(stat.total / (1024**3), 1)
                info['disk_free_gb'] = round(stat.free / (1024**3), 1)
            except:
                info['disk_usage'] = 0
                info['disk_total_gb'] = 0
                info['disk_free_gb'] = 0
            
            # 获取CPU信息
            try:
                # 简单的CPU使用率获取方法
                result = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Cpu(s)' in line:
                            # 解析类似：%Cpu(s):  1.2 us,  0.6 sy,  0.0 ni, 98.1 id...
                            parts = line.split(',')
                            idle = float(parts[3].split()[0])
                            info['cpu_percent'] = round(100 - idle, 1)
                            break
                else:
                    info['cpu_percent'] = 0
            except:
                info['cpu_percent'] = 0
            
            # 获取进程数
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                if result.returncode == 0:
                    info['processes'] = len(result.stdout.strip().split('\n')) - 1  # 减去标题行
                else:
                    info['processes'] = 0
            except:
                info['processes'] = 0
            
            return info
        except Exception as e:
            return {'error': str(e)}
    
    def get_system_context(self) -> Dict:
        """获取系统上下文信息"""
        try:
            context = {
                'cwd': os.getcwd(),
                'user': os.getenv('USER', 'unknown'),
                'shell': os.getenv('SHELL', 'unknown'),
                'os_info': subprocess.check_output(['uname', '-a'], text=True).strip(),
                'python_version': sys.version,
                'env_vars': dict(os.environ)
            }
            
            # 使用原生方法获取系统信息
            context.update(self.get_system_info_native())
            
            # 检查常用工具是否安装
            tools = ['git', 'docker', 'node', 'python3', 'vim', 'curl', 'wget', 'nginx', 'mysql', 'redis']
            context['installed_tools'] = {}
            for tool in tools:
                try:
                    result = subprocess.run(['which', tool], 
                                          capture_output=True, text=True)
                    context['installed_tools'][tool] = result.returncode == 0
                except:
                    context['installed_tools'][tool] = False
            
            # 增强的上下文信息
            context.update(self.get_enhanced_context())
            
            return context
        except Exception as e:
            return {'error': str(e)}
    
    def http_request(self, url: str, data: dict = None, headers: dict = None, timeout: int = 30) -> Dict:
        """使用urllib发送HTTP请求"""
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
    
    def call_custom_api(self, prompt: str) -> str:
        """调用自定义API（使用urllib）"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.config["ai_service"]["api_key"]}'
            }
            
            data = {
                "model": self.config['ai_service']['model'],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = self.http_request(
                self.config['ai_service']['base_url'],
                data=data,
                headers=headers,
                timeout=self.config['ai_service']['timeout']
            )
            
            if response['status_code'] == 200:
                result = json.loads(response['content'])
                return result['choices'][0]['message']['content'].strip()
            else:
                return f"API调用失败: {response['status_code']}"
        except Exception as e:
            return f"API调用失败: {e}"
    
    def call_ollama(self, prompt: str) -> str:
        """调用Ollama API（使用urllib）"""
        try:
            data = {
                "model": self.config['ai_service']['model'],
                "prompt": prompt,
                "stream": False
            }
            
            response = self.http_request(
                f"{self.config['ai_service']['base_url']}/api/generate",
                data=data,
                timeout=self.config['ai_service']['timeout']
            )
            
            if response['status_code'] == 200:
                result = json.loads(response['content'])
                return result['response'].strip()
            else:
                return f"API调用失败: {response['status_code']}"
        except Exception as e:
            return f"连接Ollama失败: {e}"
    
    # 复制原有的其他方法...
    def get_enhanced_context(self) -> Dict:
        """获取增强的上下文信息"""
        enhanced = {}
        
        try:
            enhanced['current_dir_files'] = self.analyze_current_directory()
            enhanced['git_info'] = self.get_git_context()
            enhanced['running_services'] = self.get_running_services()
            enhanced['network_info'] = self.get_network_context()
            enhanced['recent_history'] = self.get_shell_history()
            enhanced['work_pattern'] = self.identify_work_pattern()
            enhanced['system_status'] = self.get_system_status()
        except Exception as e:
            enhanced['context_error'] = str(e)
        
        return enhanced
    
    def analyze_current_directory(self) -> Dict:
        """分析当前目录内容，识别项目类型"""
        try:
            files = os.listdir('.')
            analysis = {
                'file_count': len(files),
                'has_hidden_files': any(f.startswith('.') for f in files),
                'file_types': {},
                'project_type': 'unknown',
                'key_files': []
            }
            
            # 统计文件类型
            for file in files:
                if os.path.isfile(file):
                    ext = os.path.splitext(file)[1].lower()
                    analysis['file_types'][ext] = analysis['file_types'].get(ext, 0) + 1
            
            # 识别项目类型
            key_indicators = {
                'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'main.py'],
                'node': ['package.json', 'node_modules'],
                'web': ['index.html', 'index.php'],
                'docker': ['Dockerfile', 'docker-compose.yml'],
                'git': ['.git'],
                'config': ['nginx.conf', 'apache.conf', '.env']
            }
            
            for project_type, indicators in key_indicators.items():
                if any(indicator in files for indicator in indicators):
                    analysis['project_type'] = project_type
                    analysis['key_files'].extend([f for f in indicators if f in files])
                    break
            
            return analysis
        except Exception:
            return {'error': 'Cannot analyze directory'}
    
    def get_git_context(self) -> Dict:
        """获取Git仓库上下文"""
        try:
            git_info = {}
            
            # 检查是否在Git仓库中
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return {'in_repo': False}
            
            git_info['in_repo'] = True
            
            # 当前分支
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True)
            git_info['current_branch'] = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            # 状态信息
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                git_info['has_changes'] = len(status_lines) > 0
                git_info['changed_files'] = len(status_lines)
            
            # 最近提交
            result = subprocess.run(['git', 'log', '--oneline', '-5'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                git_info['recent_commits'] = result.stdout.strip().split('\n')[:3]
            
            return git_info
        except Exception:
            return {'in_repo': False, 'error': 'Git not available'}
    
    def get_running_services(self) -> Dict:
        """获取运行中的重要服务"""
        try:
            services = {}
            important_services = ['nginx', 'apache2', 'mysql', 'redis', 'docker', 'ssh']
            
            for service in important_services:
                try:
                    result = subprocess.run(['systemctl', 'is-active', service], 
                                          capture_output=True, text=True)
                    services[service] = result.stdout.strip() == 'active'
                except:
                    services[service] = False
            
            return services
        except Exception:
            return {'error': 'Cannot get services info'}
    
    def get_network_context(self) -> Dict:
        """获取网络上下文"""
        try:
            network = {}
            
            # 检查网络连接
            try:
                result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                      capture_output=True, text=True, timeout=3)
                network['internet_available'] = result.returncode == 0
            except:
                network['internet_available'] = False
            
            return network
        except Exception:
            return {'error': 'Cannot get network info'}
    
    def get_shell_history(self, limit: int = 20) -> List[str]:
        """获取最近的shell历史命令"""
        try:
            # 首先尝试从内部历史中获取
            if len(self.command_history) > 0:
                internal_history = [cmd['command'] for cmd in self.command_history[-limit:]]
                if len(internal_history) >= limit:
                    return internal_history
            
            # 如果内部历史不够，尝试读取shell历史文件
            history_commands = []
            
            # 尝试使用history命令获取当前会话历史
            try:
                result = subprocess.run(['bash', '-c', 'history'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[-limit:]:
                        if line.strip():
                            parts = line.strip().split(None, 1)
                            if len(parts) >= 2:
                                command = parts[1]
                                if command and not command.startswith('history'):
                                    history_commands.append(command)
            except Exception:
                pass
            
            # 如果history命令失败，尝试读取历史文件
            if len(history_commands) < limit:
                try:
                    history_file = os.path.expanduser('~/.bash_history')
                    if os.path.exists(history_file):
                        with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            file_commands = [line.strip() for line in lines[-limit:] 
                                           if line.strip() and not line.strip().startswith('#')]
                            if len(file_commands) > len(history_commands):
                                history_commands = file_commands
                except Exception:
                    pass
            
            # 合并内部历史和外部历史
            if len(self.command_history) > 0:
                internal_commands = [cmd['command'] for cmd in self.command_history[-10:]]
                seen = set(history_commands)
                for cmd in internal_commands:
                    if cmd not in seen:
                        history_commands.append(cmd)
                        seen.add(cmd)
            
            return history_commands[-limit:] if history_commands else []
            
        except Exception:
            return []
    
    def identify_work_pattern(self) -> Dict:
        """识别用户的工作模式"""
        try:
            pattern = {
                'mode': 'general',
                'activities': [],
                'suggestions': []
            }
            
            recent_commands = self.get_shell_history()
            if not recent_commands:
                return pattern
            
            # 分析命令模式
            command_categories = {
                'development': ['git', 'npm', 'pip', 'python', 'node', 'make', 'gcc'],
                'system_admin': ['systemctl', 'service', 'chmod', 'chown', 'mount', 'sudo'],
                'web_server': ['nginx', 'apache', 'curl', 'wget', 'netstat'],
                'database': ['mysql', 'redis', 'mongo', 'psql'],
                'docker': ['docker', 'docker-compose'],
                'file_management': ['ls', 'cd', 'cp', 'mv', 'rm', 'find', 'grep']
            }
            
            for category, keywords in command_categories.items():
                if any(any(keyword in cmd for keyword in keywords) for cmd in recent_commands):
                    pattern['activities'].append(category)
            
            return pattern
        except Exception:
            return {'mode': 'general', 'error': 'Cannot identify pattern'}
    
    def get_system_status(self) -> Dict:
        """获取系统状态信息"""
        try:
            # 使用原生方法获取的系统信息
            info = self.get_system_info_native()
            
            status = {
                'cpu_percent': info.get('cpu_percent', 0),
                'memory': {
                    'percent': info.get('memory_usage', 0),
                    'available_gb': info.get('memory_available_gb', 0),
                    'total_gb': info.get('memory_total_gb', 0)
                },
                'disk': {
                    'percent': info.get('disk_usage', 0),
                    'free_gb': info.get('disk_free_gb', 0),
                    'total_gb': info.get('disk_total_gb', 0)
                }
            }
            
            return status
        except Exception:
            return {'error': 'Cannot get system status'}
    
    # 其他方法保持不变...
    def analyze_command_patterns(self, commands: List[str]) -> Dict[str, int]:
        """分析命令模式，统计不同类型命令的使用频率"""
        if not commands:
            return {}
        
        patterns = {
            "文件操作": ["ls", "cd", "pwd", "mkdir", "rmdir", "cp", "mv", "rm", "find", "locate"],
            "文本处理": ["cat", "less", "more", "head", "tail", "grep", "sed", "awk", "sort", "uniq"],
            "系统管理": ["ps", "top", "htop", "kill", "systemctl", "service", "mount", "umount"],
            "网络操作": ["ping", "curl", "wget", "ssh", "scp", "rsync", "netstat", "ss"],
            "权限管理": ["chmod", "chown", "sudo", "su", "whoami", "groups"],
            "开发工具": ["git", "npm", "pip", "python", "node", "make", "gcc", "vim", "nano"],
            "容器技术": ["docker", "docker-compose", "kubectl", "podman"],
            "压缩解压": ["tar", "zip", "unzip", "gzip", "gunzip"],
            "包管理": ["apt", "yum", "dnf", "brew", "snap"],
            "进程监控": ["ps", "pgrep", "pkill", "jobs", "nohup", "screen", "tmux"]
        }
        
        pattern_counts = {}
        
        for command in commands:
            cmd_name = command.split()[0] if command.split() else ""
            
            for pattern_name, pattern_commands in patterns.items():
                if any(cmd_name.startswith(pc) for pc in pattern_commands):
                    pattern_counts[pattern_name] = pattern_counts.get(pattern_name, 0) + 1
                    break
        
        return dict(sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True))
    
    def analyze_command_sequence(self, commands: List[str]) -> str:
        """分析命令序列，识别用户的操作意图"""
        if len(commands) < 2:
            return ""
        
        patterns = {
            "项目设置": ["git clone", "cd", "npm install", "pip install"],
            "开发调试": ["python", "node", "npm run", "git add", "git commit"],
            "系统配置": ["sudo", "systemctl", "chmod", "chown"],
            "文件操作": ["mkdir", "cp", "mv", "rm", "ls"],
            "网络调试": ["curl", "wget", "ping", "netstat"],
            "容器操作": ["docker", "docker-compose"]
        }
        
        for pattern_name, keywords in patterns.items():
            if any(any(keyword in cmd for keyword in keywords) for cmd in commands[-3:]):
                return f"正在进行{pattern_name}"
        
        return "常规操作"
    
    def monitor_command(self, command: str, exit_code: int, output: str, error: str):
        """监控命令执行结果"""
        cmd_info = {
            'command': command,
            'exit_code': exit_code,
            'output': output,
            'error': error,
            'timestamp': time.time(),
            'cwd': os.getcwd()
        }
        
        self.command_history.append(cmd_info)
        
        # 保持历史记录在合理范围内
        if len(self.command_history) > 100:
            self.command_history = self.command_history[-50:]
        
        # 如果命令执行失败且启用了自动错误分析，立即分析
        if exit_code != 0 and self.config['features']['auto_error_analysis']:
            self.analyze_error_sync(cmd_info)
    
    def analyze_error_sync(self, cmd_info: Dict):
        """同步分析错误，立即显示结果，包含去重逻辑"""
        current_time = time.time()
        command_key = f"{cmd_info['command']}_{cmd_info['exit_code']}"
        
        # 去重：如果是相同的命令和错误码，且在5秒内，则忽略
        if (self.last_analyzed_command == command_key and 
            current_time - self.last_analyzed_time < 5):
            return
        
        # 跳过 SIGINT (Ctrl+C) 退出码 130
        if cmd_info['exit_code'] == 130:
            return
            
        # 过滤掉一些明显不需要分析的命令
        if (cmd_info['command'].startswith(('return', 'local', 'set', 'export')) or
            'python3' in cmd_info['command'] and '--monitor' in cmd_info['command'] or
            '_ai_companion' in cmd_info['command']):
            return
            
        try:
            suggestion = self.get_ai_suggestion(cmd_info)
            if suggestion:
                self.display_suggestion(suggestion, cmd_info['command'])
                self.last_analyzed_command = command_key
                self.last_analyzed_time = current_time
        except Exception as e:
            print(f"\n💡 AI伴侣暂时无法分析此错误: {e}")
            sys.stdout.flush()
    
    def get_ai_suggestion(self, cmd_info: Dict) -> str:
        """获取AI建议"""
        context = self.get_system_context()
        
        # 构建提示词
        prompt = self.build_prompt(cmd_info, context)
        
        # 调用AI服务
        if self.config['ai_service']['type'] == 'ollama':
            return self.call_ollama(prompt)
        else:
            return self.call_custom_api(prompt)
    
    def build_prompt(self, cmd_info: Dict, context: Dict) -> str:
        """构建AI提示词，充分利用上下文信息"""
        recent_commands = [cmd['command'] for cmd in self.command_history[-5:]]
        all_recent_commands = self.get_shell_history(10)
        
        # 构建详细的上下文信息
        context_info = f"""当前环境信息：
- 工作目录: {context.get('cwd', 'unknown')}
- 用户: {context.get('user', 'unknown')}
- 系统: {context.get('os_info', 'unknown')}"""

        # 添加目录分析信息
        if 'current_dir_files' in context:
            dir_info = context['current_dir_files']
            context_info += f"""
- 当前目录: {dir_info.get('file_count', 0)}个文件
- 项目类型: {dir_info.get('project_type', 'unknown')}"""
            if dir_info.get('key_files'):
                context_info += f"""
- 关键文件: {', '.join(dir_info['key_files'])}"""

        # 添加Git信息
        if context.get('git_info', {}).get('in_repo'):
            git_info = context['git_info']
            context_info += f"""
- Git仓库: 是 (分支: {git_info.get('current_branch', 'unknown')})"""
            if git_info.get('has_changes'):
                context_info += f"""
- Git状态: {git_info.get('changed_files', 0)}个文件有变更"""

        # 构建命令历史上下文
        history_context = ""
        if all_recent_commands:
            recent_5 = all_recent_commands[-5:]
            history_context = f"\n最近执行的命令序列: {' → '.join(recent_5)}"
            
            try:
                command_patterns = self.analyze_command_patterns(all_recent_commands)
                if command_patterns:
                    top_patterns = list(command_patterns.items())[:3]
                    pattern_str = ", ".join([f"{name}({count}次)" for name, count in top_patterns])
                    history_context += f"\n最近操作模式: {pattern_str}"
            except Exception:
                pass
            
            try:
                sequence_analysis = self.analyze_command_sequence(all_recent_commands)
                if sequence_analysis:
                    history_context += f"\n当前操作意图: {sequence_analysis}"
            except Exception:
                pass

        prompt = f"""你是一个智能的Linux终端AI伴侣，专门帮助用户解决Linux命令问题。请用中文回答，并保持简洁实用。

{context_info}{history_context}

刚才执行的命令失败了：
命令: {cmd_info['command']}
退出码: {cmd_info['exit_code']}
错误输出: {cmd_info.get('error', '无') if cmd_info.get('error') else '无'}

请根据当前环境和操作上下文，特别是最近的命令序列和操作模式，按以下格式回答：

**错误原因：** [结合当前环境、错误输出和操作上下文分析错误原因]

**解决方案：** 
[提供1-2个针对当前环境和操作流程的具体修复命令]

**后续建议：** [基于你的工作模式、目录环境和命令序列，建议接下来可能需要的操作]

请特别注意用户的操作模式和意图，提供连贯性的建议。"""
        
        return prompt
    
    def display_suggestion(self, suggestion: str, command: str):
        """优化的建议显示方式"""
        print(f"🤖 \033[1;36mAI伴侣建议\033[0m (命令: \033[1;33m{command}\033[0m)")
        
        
        # 处理建议内容，使其更易读
        lines = suggestion.strip().split('\n')
        for line in lines:
            if line.strip():
                if '```' in line:
                    continue
                elif line.strip().startswith('`') and line.strip().endswith('`'):
                    code = line.strip()[1:-1]
                    print(f"   \033[1;32m{code}\033[0m")
                elif line.strip().startswith(('**错误原因：**', '**解决方案：**', '**后续建议：**')):
                    print(f"\033[1;34m{line}\033[0m")
                else:
                    print(f"   {line}")
        
        print(f"💡 \033[2m输入 'ask \"更多问题\"' 可以继续咨询\033[0m")
        sys.stdout.flush()
    
    def ask_question(self, question: str) -> str:
        """直接提问功能，增强上下文感知"""
        context = self.get_system_context()
        
        # 构建上下文感知的提示词
        context_summary = self.build_context_summary(context)
        recent_commands = self.get_shell_history(10)
        
        # 分析最近的命令模式
        pattern_summary = ""
        try:
            command_patterns = self.analyze_command_patterns(recent_commands) if recent_commands else {}
            if command_patterns:
                top_patterns = list(command_patterns.items())[:2]
                pattern_summary = f"\n最近主要操作: {', '.join([f'{name}({count}次)' for name, count in top_patterns])}"
        except Exception:
            pass

        prompt = f"""你是一个智能的Linux终端AI伴侣，用中文回答问题。

{context_summary}{pattern_summary}

最近10条命令: {' → '.join(recent_commands[-10:]) if recent_commands else '无'}

用户问题: {question}

请根据当前环境、工作上下文和最近的操作模式，提供针对性的Linux命令和建议。如果问题与当前环境或最近的操作相关，请特别说明。保持回答简洁明了。"""
        
        if self.config['ai_service']['type'] == 'ollama':
            return self.call_ollama(prompt)
        else:
            return self.call_custom_api(prompt)
    
    def build_context_summary(self, context: Dict) -> str:
        """构建简洁的上下文摘要"""
        summary_parts = []
        
        # 基本环境
        summary_parts.append(f"环境: {context.get('cwd', 'unknown')}")
        
        # 项目类型
        if 'current_dir_files' in context:
            project_type = context['current_dir_files'].get('project_type', 'unknown')
            if project_type != 'unknown':
                summary_parts.append(f"项目类型: {project_type}")
        
        # Git状态
        if context.get('git_info', {}).get('in_repo'):
            git_info = context['git_info']
            git_status = f"Git仓库 ({git_info.get('current_branch', 'unknown')}分支)"
            if git_info.get('has_changes'):
                git_status += " [有变更]"
            summary_parts.append(git_status)
        
        return " | ".join(summary_parts)
    
    def configure_api(self, api_type: str = None, base_url: str = None, 
                     model: str = None, api_key: str = None):
        """配置API服务"""
        if api_type:
            self.config['ai_service']['type'] = api_type
        if base_url:
            self.config['ai_service']['base_url'] = base_url
        if model:
            self.config['ai_service']['model'] = model
        if api_key:
            self.config['ai_service']['api_key'] = api_key
        
        self.save_config()
        print("✅ API配置已更新")
    
    def test_api_connection(self):
        """测试API连接"""
        try:
            test_prompt = "你好，请回复'连接成功'"
            response = self.ask_question(test_prompt)
            if response and "连接成功" in response:
                print("✅ API连接测试成功")
            else:
                print(f"⚠️  API连接可能有问题，响应: {response}")
        except Exception as e:
            print(f"❌ API连接测试失败: {e}")
    
    def show_config(self):
        """显示当前配置"""
        print("当前配置:")
        print(f"  服务类型: {self.config['ai_service']['type']}")
        print(f"  API地址: {self.config['ai_service']['base_url']}")
        print(f"  模型: {self.config['ai_service']['model']}")
        print(f"  API Key: {self.config['ai_service']['api_key'][:20]}...")
        print(f"  超时时间: {self.config['ai_service']['timeout']}秒")
        print(f"  自动错误分析: {self.config['features']['auto_error_analysis']}")
    
    def show_context_info(self):
        """显示详细的上下文信息"""
        context = self.get_system_context()
        
        print("🔍 \033[1;36m上下文信息详览\033[0m")
        
        # 基本环境
        print(f"\033[1;34m📍 基本环境\033[0m")
        print(f"   工作目录: {context.get('cwd', 'unknown')}")
        print(f"   用户: {context.get('user', 'unknown')}")
        print(f"   系统: {context.get('os_info', 'unknown')[:50]}...")
        
        # 当前目录分析
        if 'current_dir_files' in context:
            dir_info = context['current_dir_files']
            print(f"\n\033[1;34m📁 目录分析\033[0m")
            print(f"   文件数量: {dir_info.get('file_count', 0)}")
            print(f"   项目类型: {dir_info.get('project_type', 'unknown')}")
            if dir_info.get('key_files'):
                print(f"   关键文件: {', '.join(dir_info['key_files'])}")
        
        # Git信息
        if 'git_info' in context:
            git_info = context['git_info']
            print(f"\n\033[1;34m🔄 Git状态\033[0m")
            if git_info.get('in_repo'):
                print(f"   当前分支: {git_info.get('current_branch', 'unknown')}")
                print(f"   有变更: {'是' if git_info.get('has_changes') else '否'}")
                if git_info.get('recent_commits'):
                    print(f"   最近提交: {git_info['recent_commits'][0][:50]}...")
            else:
                print("   不在Git仓库中")
        
        # 系统状态
        if 'system_status' in context:
            status = context['system_status']
            print(f"\n\033[1;34m⚡ 系统状态\033[0m")
            print(f"   CPU使用率: {status.get('cpu_percent', 0):.1f}%")
            if 'memory' in status:
                mem = status['memory']
                print(f"   内存使用: {mem.get('percent', 0):.1f}% ({mem.get('available_gb', 0):.1f}GB可用)")
            if 'disk' in status:
                disk = status['disk']
                print(f"   磁盘使用: {disk.get('percent', 0):.1f}% ({disk.get('free_gb', 0):.1f}GB可用)")
        
    def install_shell_hook(self):
        """安装Shell钩子函数 - 统一完整版（包含所有高级功能）"""
        # 创建安装目录
        install_dir = Path.home() / '.ai_companion'
        install_dir.mkdir(exist_ok=True)
        
        # 复制主程序文件到安装目录
        current_file = Path(__file__).resolve()
        target_file = install_dir / 'ai_companion.py'
        
        if current_file != target_file:
            shutil.copy2(current_file, target_file)
            print(f"✅ 已复制程序文件到 {target_file}")
        
        # 创建stderr捕获脚本 - 所有高级功能
        capture_script = install_dir / 'capture_stderr.sh'
        with open(capture_script, 'w') as f:
            f.write(f'''#!/bin/bash
# AI Companion - 智能错误捕获脚本 (完整版)

# 全局变量
AI_STDERR_FILE="/tmp/ai_stderr_$$"
AI_LAST_COMMAND=""
AI_LAST_EXIT_CODE=0

# 高级命令执行包装器 - 支持实时stderr捕获
ai_exec() {{
    # 清空之前的错误
    > "$AI_STDERR_FILE" 2>/dev/null || true
    
    # 执行命令并捕获stderr，同时保持用户交互
    "$@" 2> >(tee "$AI_STDERR_FILE" >&2)
    local exit_code=$?
    
    AI_LAST_EXIT_CODE=$exit_code
    AI_LAST_COMMAND="$*"
    
    return $exit_code
}}

# 智能错误分析函数
ai_analyze_error() {{
    if [ $AI_LAST_EXIT_CODE -ne 0 ] && [ $AI_LAST_EXIT_CODE -ne 130 ] && [ -n "$AI_LAST_COMMAND" ]; then
        local stderr_content=""
        if [ -f "$AI_STDERR_FILE" ] && [ -s "$AI_STDERR_FILE" ]; then
            stderr_content=$(cat "$AI_STDERR_FILE" 2>/dev/null || echo "")
        fi
        
        # 编码stderr内容避免特殊字符问题
        local stderr_encoded=""
        if [ -n "$stderr_content" ]; then
            stderr_encoded=$(echo "$stderr_content" | base64 -w 0 2>/dev/null || echo "$stderr_content")
        fi
        
        echo "⏳ AI伴侣正在帮你分析错误，请稍候..."
        python3 "{target_file}" --monitor "$AI_LAST_COMMAND" "$AI_LAST_EXIT_CODE" "$stderr_encoded" 2>/dev/null || true
        
        # 重置状态
        AI_LAST_COMMAND=""
        AI_LAST_EXIT_CODE=0
        > "$AI_STDERR_FILE" 2>/dev/null || true
    fi
}}

# 清理函数
ai_cleanup() {{
    rm -f "$AI_STDERR_FILE" 2>/dev/null || true
}}

# 注册清理函数
trap ai_cleanup EXIT

# 导出函数供shell使用
export -f ai_exec ai_analyze_error ai_cleanup
''')
        
        capture_script.chmod(0o755)
        
        # 创建统一完整版shell钩子，包含所有高级功能
        shell_hook = f'''
# Linux AI Companion Hook - 统一完整版
# 包含所有高级功能：智能错误分析、实时stderr捕获、命令包装、上下文感知

# 加载错误捕获脚本
source "{capture_script}"

# 创建临时目录存储错误输出（备用方案）
_ai_temp_dir="/tmp/ai_companion_$$"
mkdir -p "$_ai_temp_dir" 2>/dev/null || true

# 为常用命令创建智能包装器
_ai_setup_command_wrappers() {{
    local basic_commands=("ls" "mkdir" "rmdir" "cp" "mv" "rm" "find" "grep" "sed" "awk" "cat" "less" "more" "head" "tail")
    local dev_commands=("git" "npm" "yarn" "pip" "pip3" "python" "python3" "node" "java" "javac" "make" "gcc" "g++" "rustc" "cargo")
    local editor_commands=("vim" "nano" "emacs" "code")
    local sys_commands=("systemctl" "service" "chmod" "chown" "sudo" "mount" "umount" "ps" "kill" "killall")
    local net_commands=("curl" "wget" "ping" "ssh" "scp" "rsync" "netstat" "ss")
    local container_commands=("docker" "docker-compose" "kubectl" "podman")
    local archive_commands=("tar" "zip" "unzip" "gzip" "gunzip" "7z")
    
    local all_commands=("${{basic_commands[@]}}" "${{dev_commands[@]}}" "${{editor_commands[@]}}" "${{sys_commands[@]}}" "${{net_commands[@]}}" "${{container_commands[@]}}" "${{archive_commands[@]}}")
    
    for cmd in "${{all_commands[@]}}"; do
        if command -v "$cmd" >/dev/null 2>&1 && [[ "$cmd" != "cd" ]]; then
            # 不包装cd命令，因为它会影响shell环境
            alias "$cmd"="ai_exec $cmd"
        fi
    done
}}

# 混合模式的PROMPT_COMMAND钩子 - 结合实时捕获和历史分析
_ai_companion_prompt_command() {{
    local current_exit_code=$?
    
    # 如果上一个命令失败了，就进行智能分析（跳过Ctrl+C触发的退出码130）
    if [ $current_exit_code -ne 0 ] && [ $current_exit_code -ne 130 ]; then
        local last_command=$(history 1 | sed 's/^[ ]*[0-9]*[ ]*//')
        
        # 过滤内部命令和特殊情况
        if [[ "$last_command" != *"_ai_"* ]] && [[ "$last_command" != *"ai_"* ]] && [[ "$last_command" != *"history"* ]]; then
            
            # 尝试多种方式获取错误输出
            local stderr_output=""
            
            # 方法1: 优先使用ai_exec捕获的错误
            if [ -f "$AI_STDERR_FILE" ] && [ -s "$AI_STDERR_FILE" ]; then
                stderr_output=$(cat "$AI_STDERR_FILE" 2>/dev/null || echo "")
                > "$AI_STDERR_FILE" 2>/dev/null || true  # 清空文件
            else
                # 方法2: 回退到临时文件捕获
                local stderr_file="$_ai_temp_dir/last_stderr"
                if [ -f "$stderr_file" ] && [ -s "$stderr_file" ]; then
                    stderr_output=$(cat "$stderr_file" 2>/dev/null || echo "")
                    > "$stderr_file"
                fi
            fi
            
            # 方法3: 专门处理"command not found"和其他错误类型
            if [ -z "$stderr_output" ]; then
                # 对于"command not found"错误，bash通常会输出到stderr
                # 我们尝试重新执行命令来捕获错误信息
                if [[ "$last_command" != *"|"* ]] && [[ "$last_command" != *">"* ]] && [[ "$last_command" != *"&"* ]] && [[ "$last_command" != *"sudo"* ]]; then
                    # 安全地重新执行命令，只获取stderr
                    stderr_output=$(eval "$last_command" 2>&1 >/dev/null || true)
                fi
                
                # 如果还是没有捕获到错误，生成通用错误信息
                if [ -z "$stderr_output" ]; then
                    # 检查是否是拼写错误的命令
                    local cmd_name=$(echo "$last_command" | awk '{{print $1}}')
                    if ! command -v "$cmd_name" >/dev/null 2>&1; then
                        stderr_output="bash: $cmd_name: command not found"
                    else
                        stderr_output="Command failed with exit code $current_exit_code"
                    fi
                fi
            fi
            
            # 编码错误输出避免特殊字符问题
            local stderr_encoded=""
            if [ -n "$stderr_output" ]; then
                stderr_encoded=$(echo "$stderr_output" | base64 -w 0 2>/dev/null || echo "$stderr_output")
            fi
            
            echo "⏳ AI伴侣正在帮你分析错误，请稍候..."
            python3 "{target_file}" --monitor "$last_command" "$current_exit_code" "$stderr_encoded" 2>/dev/null || true
        fi
    fi
}}

# 应用命令包装器
_ai_setup_command_wrappers

# 清理函数
_ai_cleanup() {{
    rm -rf "$_ai_temp_dir" 2>/dev/null || true
    ai_cleanup 2>/dev/null || true
}}

# 注册清理函数
trap _ai_cleanup EXIT

# ask命令 - 智能问答
ask() {{
    if [ $# -eq 0 ]; then
        echo "用法: ask <问题>"
        echo "示例: ask '如何查看系统内存使用情况？'"
        return 1
    fi
    python3 "{target_file}" --ask "$@"
}}

# ai_context命令 - 显示详细上下文
ai_context() {{
    python3 "{target_file}" --context
}}

# ai_debug命令 - 调试和状态信息
ai_debug() {{
    echo "🔧 AI伴侣调试信息:"
    echo "  PROMPT_COMMAND: $PROMPT_COMMAND"
    echo "  AI伴侣路径: {target_file}"
    echo "  错误捕获文件: $AI_STDERR_FILE"
    echo "  临时目录: $_ai_temp_dir"
    echo "  命令包装器状态: $(alias ls 2>/dev/null | grep -q ai_exec && echo '已启用' || echo '未启用')"
    echo ""
    echo "🧪 测试API连接:"
    python3 "{target_file}" --test
}}

# ai_run命令 - 手动执行并分析命令
ai_run() {{
    if [ $# -eq 0 ]; then
        echo "用法: ai_run <命令>"
        echo "示例: ai_run ls /nonexistent"
        return 1
    fi
    ai_exec "$@"
    ai_analyze_error
}}

# ai_config命令 - 快速查看配置
ai_config() {{
    python3 "{target_file}" --config
}}

# 只在没有安装时才添加钩子
if [[ "${{BASH_COMMAND_HOOKS:-}}" != *"ai_companion"* ]]; then
    # 保持原有的PROMPT_COMMAND，如果存在的话
    if [ -n "$PROMPT_COMMAND" ]; then
        export PROMPT_COMMAND="$PROMPT_COMMAND; _ai_companion_prompt_command"
    else
        export PROMPT_COMMAND="_ai_companion_prompt_command"
    fi
    
    export BASH_COMMAND_HOOKS="${{BASH_COMMAND_HOOKS}} ai_companion"
    echo "🤖 Linux AI伴侣已启动 - 统一完整版"
    echo "💡 包含功能:"
    echo "   ✅ 智能错误分析 - 自动捕获stderr并提供解决方案"
    echo "   ✅ 实时stderr捕获 - 精确获取命令错误输出"
    echo "   ✅ 命令自动包装 - 为常用命令添加智能监控"
    echo "   ✅ 上下文感知 - 基于当前环境提供建议"
    echo "   ✅ AI问答功能 - ask命令直接咨询问题"
    echo ""
    echo "�️  可用命令:"
    echo "   ask '问题'        - 智能问答"
    echo "   ai_context       - 查看详细上下文"
    echo "   ai_debug         - 调试和状态信息"
    echo "   ai_run <命令>     - 手动执行并分析"
    echo "   ai_config        - 查看配置"
fi
# Linux AI Companion Hook - 结束
'''
        
        bashrc_path = Path.home() / '.bashrc'
        
        # 检查是否已安装
        if bashrc_path.exists():
            content = bashrc_path.read_text()
            if 'Linux AI Companion Hook - 开始' not in content and 'Linux AI Companion Hook - 统一完整版' not in content:
                with open(bashrc_path, 'a') as f:
                    f.write('\n' + shell_hook)
                print("✅ Shell钩子已安装到 ~/.bashrc")
                print("请运行以下命令生效:")
                print("  source ~/.bashrc")
                print("")
                print("🎉 安装完成！现在包含所有高级功能:")
                print("  📊 智能错误分析 - 自动分析失败命令并提供解决建议")
                print("  🔄 实时stderr捕获 - 精确捕获命令错误输出")
                print("  🤖 命令自动包装 - 为常用命令添加智能监控")
                print("  📋 上下文感知 - 基于当前环境和历史提供个性化建议")
                print("  💬 AI问答功能 - 随时使用ask命令咨询问题")
                print("")
                print("🛠️  可用命令:")
                print("  ask '问题'        - 智能问答")
                print("  ai_context       - 查看详细上下文")
                print("  ai_debug         - 调试和状态信息")
                print("  ai_run <命令>     - 手动执行并分析")
                print("  ai_config        - 查看配置")
            else:
                print("⚠️  Shell钩子已存在")
                print("如需重新安装，请先手动删除 ~/.bashrc 中的钩子部分")
        else:
            print("❌ 未找到 ~/.bashrc 文件")
    

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Linux终端AI伴侣 - 统一完整版')
    parser.add_argument('--install', action='store_true', help='安装Shell钩子（包含所有高级功能）')
    parser.add_argument('--config', action='store_true', help='显示当前配置')
    parser.add_argument('--context', action='store_true', help='显示详细上下文信息')
    parser.add_argument('--test', action='store_true', help='测试API连接')
    parser.add_argument('--set-api', nargs=4, metavar=('TYPE', 'URL', 'MODEL', 'KEY'), 
                       help='设置API配置: TYPE URL MODEL KEY')
    parser.add_argument('--ask', nargs='+', help='直接提问')
    parser.add_argument('--monitor', nargs='+', metavar='ARG', 
                       help='监控命令执行结果（内部使用）: COMMAND EXIT_CODE [STDERR]')
    
    args = parser.parse_args()
    
    companion = LinuxAICompanion()
    
    if args.install:
        companion.install_shell_hook()
    elif args.config:
        companion.show_config()
    elif args.context:
        companion.show_context_info()
    elif args.test:
        companion.test_api_connection()
    elif args.set_api:
        api_type, base_url, model, api_key = args.set_api
        companion.configure_api(api_type, base_url, model, api_key)
    elif args.monitor:
        command = args.monitor[0]
        exit_code = int(args.monitor[1])
        stderr_content = ""
        
        # 如果提供了stderr参数
        if len(args.monitor) > 2 and args.monitor[2]:
            import base64
            try:
                # 尝试base64解码
                stderr_content = base64.b64decode(args.monitor[2]).decode('utf-8')
            except:
                # 如果解码失败，直接使用原始内容
                stderr_content = args.monitor[2]
        
        companion.monitor_command(command, exit_code, '', stderr_content)
    elif args.ask:
        question = ' '.join(args.ask)
        response = companion.ask_question(question)

        print(f"🤖 \033[1;36mAI伴侣回答\033[0m")
        print(response)
    else:
        print("Linux终端AI伴侣 - 统一完整版（无外部依赖）")
        print("使用 --install 安装Shell钩子（包含所有高级功能）")
        print("使用 --config 查看当前配置")
        print("使用 --context 查看详细上下文")
        print("使用 --test 测试API连接")
        print("使用 --ask '问题' 直接提问")

if __name__ == "__main__":
    main()

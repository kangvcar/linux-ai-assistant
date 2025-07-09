"""
命令历史分析模块
负责命令历史的收集、模式分析和意图识别
"""

import os
import subprocess
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CommandInfo:
    """命令信息"""
    command: str
    exit_code: int
    output: str
    error: str
    timestamp: float
    cwd: str


@dataclass
class WorkPattern:
    """工作模式"""
    mode: str
    activities: List[str]
    suggestions: List[str]


class CommandHistoryAnalyzer:
    """命令历史分析器"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.command_history: List[CommandInfo] = []
        
        # 命令分类模式
        self.command_patterns = {
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
        
        # 工作模式识别
        self.work_categories = {
            'development': ['git', 'npm', 'pip', 'python', 'node', 'make', 'gcc'],
            'system_admin': ['systemctl', 'service', 'chmod', 'chown', 'mount', 'sudo'],
            'web_server': ['nginx', 'apache', 'curl', 'wget', 'netstat'],
            'database': ['mysql', 'redis', 'mongo', 'psql'],
            'docker': ['docker', 'docker-compose'],
            'file_management': ['ls', 'cd', 'cp', 'mv', 'rm', 'find', 'grep']
        }
    
    def add_command(self, command_info: CommandInfo):
        """添加命令到历史记录"""
        self.command_history.append(command_info)
        
        # 保持历史记录在合理范围内
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[-self.max_history//2:]
    
    def get_shell_history(self, limit: int = 20) -> List[str]:
        """获取shell历史命令"""
        history_commands = []
        
        # 首先从内部历史获取
        if self.command_history:
            internal_history = [cmd.command for cmd in self.command_history[-limit:]]
            if len(internal_history) >= limit:
                return internal_history
        
        # 尝试从history命令获取
        try:
            result = subprocess.run(
                ['bash', '-c', 'history'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
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
        
        # 如果不够，尝试读取历史文件
        if len(history_commands) < limit:
            try:
                history_file = os.path.expanduser('~/.bash_history')
                if os.path.exists(history_file):
                    with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        file_commands = [
                            line.strip() for line in lines[-limit:] 
                            if line.strip() and not line.strip().startswith('#')
                        ]
                        if len(file_commands) > len(history_commands):
                            history_commands = file_commands
            except Exception:
                pass
        
        # 合并内部历史
        if self.command_history:
            internal_commands = [cmd.command for cmd in self.command_history[-10:]]
            seen = set(history_commands)
            for cmd in internal_commands:
                if cmd not in seen:
                    history_commands.append(cmd)
                    seen.add(cmd)
        
        return history_commands[-limit:] if history_commands else []
    
    def analyze_command_patterns(self, commands: List[str]) -> Dict[str, int]:
        """分析命令模式，统计不同类型命令的使用频率"""
        if not commands:
            return {}
        
        pattern_counts = defaultdict(int)
        
        for command in commands:
            cmd_name = command.split()[0] if command.split() else ""
            
            for pattern_name, pattern_commands in self.command_patterns.items():
                if any(cmd_name.startswith(pc) for pc in pattern_commands):
                    pattern_counts[pattern_name] += 1
                    break
        
        return dict(sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True))
    
    def analyze_command_sequence(self, commands: List[str]) -> str:
        """分析命令序列，识别用户的操作意图"""
        if len(commands) < 2:
            return ""
        
        sequence_patterns = {
            "项目设置": ["git clone", "cd", "npm install", "pip install"],
            "开发调试": ["python", "node", "npm run", "git add", "git commit"],
            "系统配置": ["sudo", "systemctl", "chmod", "chown"],
            "文件操作": ["mkdir", "cp", "mv", "rm", "ls"],
            "网络调试": ["curl", "wget", "ping", "netstat"],
            "容器操作": ["docker", "docker-compose"]
        }
        
        recent_commands = commands[-3:]  # 分析最近3个命令
        
        for pattern_name, keywords in sequence_patterns.items():
            if any(any(keyword in cmd for keyword in keywords) for cmd in recent_commands):
                return f"正在进行{pattern_name}"
        
        return "常规操作"
    
    def identify_work_pattern(self, commands: Optional[List[str]] = None) -> WorkPattern:
        """识别用户的工作模式"""
        if commands is None:
            commands = self.get_shell_history()
        
        if not commands:
            return WorkPattern(mode='general', activities=[], suggestions=[])
        
        activities = []
        
        for category, keywords in self.work_categories.items():
            if any(any(keyword in cmd for keyword in keywords) for cmd in commands):
                activities.append(category)
        
        # 确定主要工作模式
        if 'development' in activities:
            mode = 'development'
        elif 'system_admin' in activities:
            mode = 'system_admin'
        elif 'docker' in activities:
            mode = 'container_ops'
        else:
            mode = 'general'
        
        return WorkPattern(mode=mode, activities=activities, suggestions=[])
    
    def get_recent_failed_commands(self, limit: int = 5) -> List[CommandInfo]:
        """获取最近失败的命令"""
        failed_commands = [
            cmd for cmd in self.command_history 
            if cmd.exit_code != 0 and cmd.exit_code != 130  # 排除Ctrl+C
        ]
        return failed_commands[-limit:]
    
    def should_analyze_command(self, command: str, exit_code: int) -> bool:
        """判断是否应该分析此命令"""
        # 跳过 SIGINT (Ctrl+C) 退出码 130
        if exit_code == 130:
            return False
        
        # 过滤掉一些明显不需要分析的命令
        if (command.startswith(('return', 'local', 'set', 'export')) or
            'python3' in command and '--monitor' in command or
            '_ai_companion' in command or
            command.startswith('history')):
            return False
        
        return True
    
    def build_context_summary(self, commands: List[str]) -> str:
        """构建命令上下文摘要"""
        if not commands:
            return "无命令历史"
        
        # 分析命令模式
        patterns = self.analyze_command_patterns(commands)
        sequence = self.analyze_command_sequence(commands)
        
        summary_parts = []
        
        # 添加最近命令
        recent_5 = commands[-5:] if len(commands) >= 5 else commands
        if recent_5:
            summary_parts.append(f"最近命令: {' → '.join(recent_5)}")
        
        # 添加主要操作模式
        if patterns:
            top_patterns = list(patterns.items())[:2]
            pattern_str = ", ".join([f"{name}({count}次)" for name, count in top_patterns])
            summary_parts.append(f"主要操作: {pattern_str}")
        
        # 添加操作意图
        if sequence:
            summary_parts.append(f"当前意图: {sequence}")
        
        return " | ".join(summary_parts)

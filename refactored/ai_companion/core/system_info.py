"""
系统信息收集模块
负责收集系统状态、环境信息等上下文数据
"""

import os
import sys
import subprocess
import shutil
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SystemStatus:
    """系统状态信息"""
    cpu_percent: float
    memory_percent: float
    memory_total_gb: float
    memory_available_gb: float
    disk_percent: float
    disk_total_gb: float
    disk_free_gb: float
    processes: int


@dataclass
class DirectoryInfo:
    """目录信息"""
    file_count: int
    has_hidden_files: bool
    file_types: Dict[str, int]
    project_type: str
    key_files: List[str]


@dataclass
class GitInfo:
    """Git仓库信息"""
    in_repo: bool
    current_branch: Optional[str] = None
    has_changes: bool = False
    changed_files: int = 0
    recent_commits: List[str] = None


class SystemInfoCollector:
    """系统信息收集器"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 30  # 缓存30秒
    
    def get_system_status(self) -> SystemStatus:
        """获取系统状态"""
        try:
            # 获取内存信息
            memory_info = self._get_memory_info()
            
            # 获取磁盘信息
            disk_info = self._get_disk_info()
            
            # 获取CPU信息
            cpu_percent = self._get_cpu_percent()
            
            # 获取进程数
            processes = self._get_process_count()
            
            return SystemStatus(
                cpu_percent=cpu_percent,
                memory_percent=memory_info['usage_percent'],
                memory_total_gb=memory_info['total_gb'],
                memory_available_gb=memory_info['available_gb'],
                disk_percent=disk_info['usage_percent'],
                disk_total_gb=disk_info['total_gb'],
                disk_free_gb=disk_info['free_gb'],
                processes=processes
            )
        except Exception as e:
            # 返回默认值而不是抛出异常
            return SystemStatus(0, 0, 0, 0, 0, 0, 0, 0)
    
    def _get_memory_info(self) -> Dict[str, float]:
        """获取内存信息"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                mem_total = int([line for line in meminfo.split('\n') if 'MemTotal' in line][0].split()[1]) * 1024
                mem_available = int([line for line in meminfo.split('\n') if 'MemAvailable' in line][0].split()[1]) * 1024
                
                return {
                    'usage_percent': round((mem_total - mem_available) / mem_total * 100, 1),
                    'total_gb': round(mem_total / (1024**3), 1),
                    'available_gb': round(mem_available / (1024**3), 1)
                }
        except:
            return {'usage_percent': 0, 'total_gb': 0, 'available_gb': 0}
    
    def _get_disk_info(self) -> Dict[str, float]:
        """获取磁盘信息"""
        try:
            stat = shutil.disk_usage('/')
            return {
                'usage_percent': round(stat.used / stat.total * 100, 1),
                'total_gb': round(stat.total / (1024**3), 1),
                'free_gb': round(stat.free / (1024**3), 1)
            }
        except:
            return {'usage_percent': 0, 'total_gb': 0, 'free_gb': 0}
    
    def _get_cpu_percent(self) -> float:
        """获取CPU使用率"""
        try:
            result = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Cpu(s)' in line:
                        parts = line.split(',')
                        idle = float(parts[3].split()[0])
                        return round(100 - idle, 1)
        except:
            pass
        return 0.0
    
    def _get_process_count(self) -> int:
        """获取进程数"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if result.returncode == 0:
                return len(result.stdout.strip().split('\n')) - 1  # 减去标题行
        except:
            pass
        return 0
    
    def get_directory_info(self, path: str = '.') -> DirectoryInfo:
        """分析目录内容"""
        try:
            files = os.listdir(path)
            file_types = {}
            key_files = []
            
            # 统计文件类型
            for file in files:
                if os.path.isfile(os.path.join(path, file)):
                    ext = os.path.splitext(file)[1].lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            # 识别项目类型
            project_type = self._identify_project_type(files, key_files)
            
            return DirectoryInfo(
                file_count=len(files),
                has_hidden_files=any(f.startswith('.') for f in files),
                file_types=file_types,
                project_type=project_type,
                key_files=key_files
            )
        except Exception:
            return DirectoryInfo(0, False, {}, 'unknown', [])
    
    def _identify_project_type(self, files: List[str], key_files: List[str]) -> str:
        """识别项目类型"""
        key_indicators = {
            'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'main.py'],
            'node': ['package.json', 'node_modules'],
            'web': ['index.html', 'index.php'],
            'docker': ['Dockerfile', 'docker-compose.yml'],
            'git': ['.git'],
            'config': ['nginx.conf', 'apache.conf', '.env']
        }
        
        for project_type, indicators in key_indicators.items():
            found_indicators = [f for f in indicators if f in files]
            if found_indicators:
                key_files.extend(found_indicators)
                return project_type
        
        return 'unknown'
    
    def get_git_info(self, path: str = '.') -> GitInfo:
        """获取Git仓库信息"""
        try:
            # 检查是否在Git仓库中
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return GitInfo(in_repo=False)
            
            git_info = GitInfo(in_repo=True)
            
            # 获取当前分支
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=path,
                capture_output=True,
                text=True
            )
            git_info.current_branch = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            # 获取状态信息
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                git_info.has_changes = len(status_lines) > 0
                git_info.changed_files = len(status_lines)
            
            # 获取最近提交
            result = subprocess.run(
                ['git', 'log', '--oneline', '-3'],
                cwd=path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                git_info.recent_commits = result.stdout.strip().split('\n')
            
            return git_info
            
        except Exception:
            return GitInfo(in_repo=False)
    
    def get_installed_tools(self) -> Dict[str, bool]:
        """检查常用工具是否安装"""
        tools = ['git', 'docker', 'node', 'python3', 'vim', 'curl', 'wget', 'nginx', 'mysql', 'redis']
        installed = {}
        
        for tool in tools:
            try:
                result = subprocess.run(['which', tool], capture_output=True, text=True)
                installed[tool] = result.returncode == 0
            except:
                installed[tool] = False
        
        return installed
    
    def get_running_services(self) -> Dict[str, bool]:
        """获取运行中的重要服务"""
        services = ['nginx', 'apache2', 'mysql', 'redis', 'docker', 'ssh']
        running = {}
        
        for service in services:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True
                )
                running[service] = result.stdout.strip() == 'active'
            except:
                running[service] = False
        
        return running
    
    def check_network(self) -> bool:
        """检查网络连接"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '8.8.8.8'],
                capture_output=True,
                text=True,
                timeout=3
            )
            return result.returncode == 0
        except:
            return False

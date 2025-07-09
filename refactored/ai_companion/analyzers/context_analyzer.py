"""
上下文分析器
整合系统信息和命令历史，提供完整的上下文分析
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

from ..core.system_info import SystemInfoCollector, SystemStatus, DirectoryInfo, GitInfo
from .command_history import CommandHistoryAnalyzer, WorkPattern


@dataclass
class FullContext:
    """完整上下文信息"""
    # 基本环境
    cwd: str
    user: str
    shell: str
    os_info: str
    
    # 系统状态
    system_status: SystemStatus
    
    # 目录信息
    directory_info: DirectoryInfo
    
    # Git信息
    git_info: GitInfo
    
    # 工具和服务
    installed_tools: Dict[str, bool]
    running_services: Dict[str, bool]
    
    # 网络状态
    network_available: bool
    
    # 命令历史和工作模式
    recent_commands: List[str]
    work_pattern: WorkPattern
    command_patterns: Dict[str, int]


class ContextAnalyzer:
    """上下文分析器"""
    
    def __init__(self):
        self.system_collector = SystemInfoCollector()
        self.history_analyzer = CommandHistoryAnalyzer()
    
    def get_full_context(self) -> FullContext:
        """获取完整的上下文信息"""
        # 获取基本环境信息
        cwd = os.getcwd()
        user = os.getenv('USER', 'unknown')
        shell = os.getenv('SHELL', 'unknown')
        
        try:
            import subprocess
            os_info = subprocess.check_output(['uname', '-a'], text=True).strip()
        except:
            os_info = 'unknown'
        
        # 收集系统信息
        system_status = self.system_collector.get_system_status()
        directory_info = self.system_collector.get_directory_info(cwd)
        git_info = self.system_collector.get_git_info(cwd)
        installed_tools = self.system_collector.get_installed_tools()
        running_services = self.system_collector.get_running_services()
        network_available = self.system_collector.check_network()
        
        # 分析命令历史
        recent_commands = self.history_analyzer.get_shell_history(20)
        work_pattern = self.history_analyzer.identify_work_pattern(recent_commands)
        command_patterns = self.history_analyzer.analyze_command_patterns(recent_commands)
        
        return FullContext(
            cwd=cwd,
            user=user,
            shell=shell,
            os_info=os_info,
            system_status=system_status,
            directory_info=directory_info,
            git_info=git_info,
            installed_tools=installed_tools,
            running_services=running_services,
            network_available=network_available,
            recent_commands=recent_commands,
            work_pattern=work_pattern,
            command_patterns=command_patterns
        )
    
    def build_context_summary(self, context: FullContext) -> str:
        """构建简洁的上下文摘要"""
        summary_parts = []
        
        # 基本环境
        summary_parts.append(f"环境: {context.cwd}")
        
        # 项目类型
        if context.directory_info.project_type != 'unknown':
            summary_parts.append(f"项目类型: {context.directory_info.project_type}")
        
        # Git状态
        if context.git_info.in_repo:
            git_status = f"Git仓库 ({context.git_info.current_branch}分支)"
            if context.git_info.has_changes:
                git_status += " [有变更]"
            summary_parts.append(git_status)
        
        return " | ".join(summary_parts)
    
    def build_detailed_context_info(self, context: FullContext) -> str:
        """构建详细的上下文信息字符串（用于AI提示）"""
        info_parts = []
        
        # 基本环境
        info_parts.append(f"""当前环境信息：
- 工作目录: {context.cwd}
- 用户: {context.user}
- 系统: {context.os_info}""")
        
        # 目录分析
        if context.directory_info.project_type != 'unknown':
            info_parts.append(f"""
- 当前目录: {context.directory_info.file_count}个文件
- 项目类型: {context.directory_info.project_type}""")
            if context.directory_info.key_files:
                info_parts.append(f"- 关键文件: {', '.join(context.directory_info.key_files)}")
        
        # Git信息
        if context.git_info.in_repo:
            info_parts.append(f"""
- Git仓库: 是 (分支: {context.git_info.current_branch})""")
            if context.git_info.has_changes:
                info_parts.append(f"- Git状态: {context.git_info.changed_files}个文件有变更")
        
        return "".join(info_parts)
    
    def build_command_context(self, context: FullContext) -> str:
        """构建命令历史上下文"""
        if not context.recent_commands:
            return ""
        
        context_parts = []
        
        # 最近命令序列
        recent_5 = context.recent_commands[-5:]
        context_parts.append(f"\n最近执行的命令序列: {' → '.join(recent_5)}")
        
        # 主要操作模式
        if context.command_patterns:
            top_patterns = list(context.command_patterns.items())[:3]
            pattern_str = ", ".join([f"{name}({count}次)" for name, count in top_patterns])
            context_parts.append(f"\n最近操作模式: {pattern_str}")
        
        # 当前操作意图
        sequence_analysis = self.history_analyzer.analyze_command_sequence(context.recent_commands)
        if sequence_analysis:
            context_parts.append(f"\n当前操作意图: {sequence_analysis}")
        
        return "".join(context_parts)
    
    def format_display_context(self, context: FullContext) -> str:
        """格式化显示上下文信息（用于终端显示）"""
        lines = []
        
        # 基本环境
        lines.append("\033[1;34m📍 基本环境\033[0m")
        lines.append(f"   工作目录: {context.cwd}")
        lines.append(f"   用户: {context.user}")
        lines.append(f"   系统: {context.os_info[:50]}...")
        
        # 目录分析
        lines.append(f"\n\033[1;34m📁 目录分析\033[0m")
        lines.append(f"   文件数量: {context.directory_info.file_count}")
        lines.append(f"   项目类型: {context.directory_info.project_type}")
        if context.directory_info.key_files:
            lines.append(f"   关键文件: {', '.join(context.directory_info.key_files)}")
        
        # Git信息
        lines.append(f"\n\033[1;34m🔄 Git状态\033[0m")
        if context.git_info.in_repo:
            lines.append(f"   当前分支: {context.git_info.current_branch}")
            lines.append(f"   有变更: {'是' if context.git_info.has_changes else '否'}")
            if context.git_info.recent_commits:
                lines.append(f"   最近提交: {context.git_info.recent_commits[0][:50]}...")
        else:
            lines.append("   不在Git仓库中")
        
        # 系统状态
        lines.append(f"\n\033[1;34m⚡ 系统状态\033[0m")
        lines.append(f"   CPU使用率: {context.system_status.cpu_percent:.1f}%")
        lines.append(f"   内存使用: {context.system_status.memory_percent:.1f}% ({context.system_status.memory_available_gb:.1f}GB可用)")
        lines.append(f"   磁盘使用: {context.system_status.disk_percent:.1f}% ({context.system_status.disk_free_gb:.1f}GB可用)")
        
        return "\n".join(lines)
    
    def add_command_to_history(self, command: str, exit_code: int, output: str = "", error: str = ""):
        """添加命令到历史记录"""
        from .command_history import CommandInfo
        import time
        
        cmd_info = CommandInfo(
            command=command,
            exit_code=exit_code,
            output=output,
            error=error,
            timestamp=time.time(),
            cwd=os.getcwd()
        )
        
        self.history_analyzer.add_command(cmd_info)
    
    def should_analyze_error(self, command: str, exit_code: int) -> bool:
        """判断是否应该分析此错误"""
        return self.history_analyzer.should_analyze_command(command, exit_code)

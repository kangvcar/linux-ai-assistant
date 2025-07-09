"""
Shell集成管理器
负责生成和安装Shell钩子、脚本管理
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any


class ShellIntegrationManager:
    """Shell集成管理器"""
    
    def __init__(self, install_dir: str = "~/.ai_companion"):
        self.install_dir = Path(install_dir).expanduser()
        self.current_file = Path(__file__).resolve().parent.parent.parent / "main.py"
    
    def install_shell_hooks(self) -> bool:
        """安装Shell钩子"""
        try:
            # 创建安装目录
            self.install_dir.mkdir(exist_ok=True)
            
            # 复制主程序文件
            target_file = self.install_dir / 'ai_companion.py'
            if self.current_file.exists():
                shutil.copy2(self.current_file, target_file)
                print(f"✅ 已复制程序文件到 {target_file}")
            
            # 创建stderr捕获脚本
            self._create_capture_script()
            
            # 创建shell钩子脚本
            self._create_hook_script()
            
            # 安装到bashrc
            return self._install_to_bashrc()
            
        except Exception as e:
            print(f"❌ 安装失败: {e}")
            return False
    
    def _create_capture_script(self):
        """创建stderr捕获脚本"""
        capture_script = self.install_dir / 'capture_stderr.sh'
        target_file = self.install_dir / 'ai_companion.py'
        
        script_content = f'''#!/bin/bash
# AI Companion - 智能错误捕获脚本

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
'''
        
        with open(capture_script, 'w') as f:
            f.write(script_content)
        capture_script.chmod(0o755)
    
    def _create_hook_script(self):
        """创建shell钩子脚本"""
        hook_script = self.install_dir / 'shell_hook.sh'
        target_file = self.install_dir / 'ai_companion.py'
        
        script_content = f"""#!/bin/bash
# AI Companion Hook
export AI_COMPANION_SCRIPT="{target_file}"

# 主命令别名
alias ai="python3 $AI_COMPANION_SCRIPT"
alias ask="python3 $AI_COMPANION_SCRIPT ask"
alias ai_context="python3 $AI_COMPANION_SCRIPT context"
alias ai_config="python3 $AI_COMPANION_SCRIPT config"
alias ai_test_api="python3 $AI_COMPANION_SCRIPT test_api"
alias ai_set_api="python3 $AI_COMPANION_SCRIPT set_api"
alias ai_switch_model="python3 $AI_COMPANION_SCRIPT switch_model"
"""
        
        with open(hook_script, 'w') as f:
            f.write(script_content)
        hook_script.chmod(0o755)
    
    def _install_to_bashrc(self) -> bool:
        """安装到bashrc"""
        bashrc_path = Path.home() / '.bashrc'
        capture_script = self.install_dir / 'capture_stderr.sh'
        target_file = self.install_dir / 'ai_companion.py'
        
        shell_hook = f'''
# Linux AI Companion Hook
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
            fi
            
            # 方法2: 专门处理"command not found"和其他错误类型
            if [ -z "$stderr_output" ]; then
                # 检查是否是拼写错误的命令
                local cmd_name=$(echo "$last_command" | awk '{{print $1}}')
                if ! command -v "$cmd_name" >/dev/null 2>&1; then
                    stderr_output="bash: $cmd_name: command not found"
                else
                    stderr_output="Command failed with exit code $current_exit_code"
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
    echo "🤖 Linux AI伴侣已启动"
    echo "💡 包含功能:"
    echo "   ✅ 智能错误分析 - 自动捕获stderr并提供解决方案"
    echo "   ✅ 实时stderr捕获 - 精确获取命令错误输出"
    echo "   ✅ 命令自动包装 - 为常用命令添加智能监控"
    echo "   ✅ 上下文感知 - 基于当前环境提供建议"
    echo "   ✅ AI问答功能 - ask命令直接咨询问题"
    echo ""
    echo "🛠️  可用命令:"
    echo "   ask '问题'        - 智能问答"
    echo "   ai_context       - 查看详细上下文"
    echo "   ai_debug         - 调试和状态信息"
    echo "   ai_run <命令>     - 手动执行并分析"
    echo "   ai_config        - 查看配置"
fi
# Linux AI Companion Hook - 结束
'''
        
        # 检查是否已安装
        if not bashrc_path.exists():
            print("❌ 未找到 ~/.bashrc 文件")
            return False
        
        content = bashrc_path.read_text()
        if 'Linux AI Companion Hook' in content:
            print("⚠️  Shell钩子已存在")
            print("如需重新安装，请先手动删除 ~/.bashrc 中的钩子部分")
            return False
        
        # 安装钩子
        with open(bashrc_path, 'a') as f:
            f.write('\\n' + shell_hook)
        
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
        
        return True
    
    def uninstall_shell_hooks(self) -> bool:
        """卸载Shell钩子"""
        try:
            bashrc_path = Path.home() / '.bashrc'
            
            if not bashrc_path.exists():
                print("❌ 未找到 ~/.bashrc 文件")
                return False
            
            content = bashrc_path.read_text()
            
            # 查找并删除钩子部分
            start_marker = "# Linux AI Companion Hook"
            end_marker = "# Linux AI Companion Hook - 结束"
            
            start_pos = content.find(start_marker)
            end_pos = content.find(end_marker)
            
            if start_pos == -1 or end_pos == -1:
                print("⚠️  未找到AI伴侣的Shell钩子")
                return False
            
            # 删除钩子部分
            new_content = content[:start_pos] + content[end_pos + len(end_marker):]
            
            # 写回文件
            with open(bashrc_path, 'w') as f:
                f.write(new_content)
            
            # 删除安装目录
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
            
            print("✅ AI伴侣Shell钩子已卸载")
            print("请运行以下命令生效:")
            print("  source ~/.bashrc")
            
            return True
            
        except Exception as e:
            print(f"❌ 卸载失败: {e}")
            return False

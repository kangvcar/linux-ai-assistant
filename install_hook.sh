#!/bin/bash

# 创建AI助手钩子脚本
mkdir -p ~/.ai_assistant

# 创建stderr捕获脚本
cat > ~/.ai_assistant/capture_stderr.sh << 'EOF'
#!/bin/bash
# AI Assistant - 智能错误捕获脚本 (完整版)

# 全局变量
AI_STDERR_FILE="/tmp/ai_stderr_$$"
AI_LAST_COMMAND=""
AI_LAST_EXIT_CODE=0

# 高级命令执行包装器 - 支持实时stderr捕获
ai_exec() {
    # 清空之前的错误
    > "$AI_STDERR_FILE" 2>/dev/null || true
    
    # 执行命令并捕获stderr，同时保持用户交互
    "$@" 2> >(tee "$AI_STDERR_FILE" >&2)
    local exit_code=$?
    
    AI_LAST_EXIT_CODE=$exit_code
    AI_LAST_COMMAND="$*"
    
    return $exit_code
}

# 智能错误分析函数
ai_analyze_error() {
    if [ $AI_LAST_EXIT_CODE -ne 0 ] && [ -n "$AI_LAST_COMMAND" ]; then
        local stderr_content=""
        if [ -f "$AI_STDERR_FILE" ] && [ -s "$AI_STDERR_FILE" ]; then
            stderr_content=$(cat "$AI_STDERR_FILE" 2>/dev/null || echo "")
        fi
        
        # 编码stderr内容避免特殊字符问题
        local stderr_encoded=""
        if [ -n "$stderr_content" ]; then
            stderr_encoded=$(echo "$stderr_content" | base64 -w 0 2>/dev/null || echo "$stderr_content")
        fi
        
        echo  # 添加空行
        python3 ~/.ai_assistant/ai_assistant.py --monitor "$AI_LAST_COMMAND" "$AI_LAST_EXIT_CODE" "$stderr_encoded" 2>/dev/null || true
        
        # 重置状态
        AI_LAST_COMMAND=""
        AI_LAST_EXIT_CODE=0
        > "$AI_STDERR_FILE" 2>/dev/null || true
    fi
}

# 清理函数
ai_cleanup() {
    rm -f "$AI_STDERR_FILE" 2>/dev/null || true
}

# 注册清理函数
trap ai_cleanup EXIT

# 导出函数供shell使用
export -f ai_exec ai_analyze_error ai_cleanup
EOF

chmod +x ~/.ai_assistant/capture_stderr.sh

# 复制主程序到安装目录
cp /root/ai/ai_assistant_standalone.py ~/.ai_assistant/ai_assistant.py

# 添加shell钩子到bashrc
cat >> ~/.bashrc << 'EOF'

# Linux AI Assistant Hook - 统一完整版
# 包含所有高级功能：智能错误分析、实时stderr捕获、命令包装、上下文感知

# 加载错误捕获脚本
source ~/.ai_assistant/capture_stderr.sh

# 创建临时目录存储错误输出（备用方案）
_ai_temp_dir="/tmp/ai_assistant_$$"
mkdir -p "$_ai_temp_dir" 2>/dev/null || true

# 混合模式的PROMPT_COMMAND钩子 - 结合实时捕获和历史分析
_ai_assistant_prompt_command() {
    local current_exit_code=$?
    
    # 如果上一个命令失败了，就进行智能分析
    if [ $current_exit_code -ne 0 ]; then
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
                    local cmd_name=$(echo "$last_command" | awk '{print $1}')
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
            
            echo  # 添加空行分隔
            python3 ~/.ai_assistant/ai_assistant.py --monitor "$last_command" "$current_exit_code" "$stderr_encoded" 2>/dev/null || true
        fi
    fi
}

# 清理函数
_ai_cleanup() {
    rm -rf "$_ai_temp_dir" 2>/dev/null || true
    ai_cleanup 2>/dev/null || true
}

# 注册清理函数
trap _ai_cleanup EXIT

# ask命令 - 智能问答
ask() {
    if [ $# -eq 0 ]; then
        echo "用法: ask <问题>"
        echo "示例: ask '如何查看系统内存使用情况？'"
        return 1
    fi
    python3 ~/.ai_assistant/ai_assistant.py --ask "$@"
}

# ai_context命令 - 显示详细上下文
ai_context() {
    python3 ~/.ai_assistant/ai_assistant.py --context
}

# ai_debug命令 - 调试和状态信息
ai_debug() {
    echo "🔧 AI助手调试信息:"
    echo "  PROMPT_COMMAND: $PROMPT_COMMAND"
    echo "  AI助手路径: ~/.ai_assistant/ai_assistant.py"
    echo "  错误捕获文件: $AI_STDERR_FILE"
    echo "  临时目录: $_ai_temp_dir"
    echo ""
    echo "🧪 测试API连接:"
    python3 ~/.ai_assistant/ai_assistant.py --test
}

# ai_run命令 - 手动执行并分析命令
ai_run() {
    if [ $# -eq 0 ]; then
        echo "用法: ai_run <命令>"
        echo "示例: ai_run ls /nonexistent"
        return 1
    fi
    ai_exec "$@"
    ai_analyze_error
}

# ai_config命令 - 快速查看配置
ai_config() {
    python3 ~/.ai_assistant/ai_assistant.py --config
}

# 只在没有安装时才添加钩子
if [[ "${BASH_COMMAND_HOOKS:-}" != *"ai_assistant"* ]]; then
    # 保持原有的PROMPT_COMMAND，如果存在的话
    if [ -n "$PROMPT_COMMAND" ]; then
        export PROMPT_COMMAND="$PROMPT_COMMAND; _ai_assistant_prompt_command"
    else
        export PROMPT_COMMAND="_ai_assistant_prompt_command"
    fi
    
    export BASH_COMMAND_HOOKS="${BASH_COMMAND_HOOKS} ai_assistant"
    echo "🤖 Linux AI助手已启动 - 统一完整版"
    echo "💡 包含功能:"
    echo "   ✅ 智能错误分析 - 自动捕获stderr并提供解决方案"
    echo "   ✅ 实时stderr捕获 - 精确获取命令错误输出"  
    echo "   ✅ 命令错误捕获 - 包括拼写错误和未找到命令"
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
# Linux AI Assistant Hook - 结束
EOF

echo "✅ AI助手Shell钩子安装完成！"
echo "请运行: source ~/.bashrc"
echo "然后测试拼写错误命令，如: mkddr"

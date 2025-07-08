# Linux 终端 AI 助手 🤖

一个智能的 Linux 终端助手，无需任何外部依赖，能够自动分析命令错误并提供解决方案。

![版本](https://img.shields.io/badge/版本-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.6+-green)
![平台](https://img.shields.io/badge/平台-Linux-orange)
![授权](https://img.shields.io/badge/授权-MIT-lightgrey)

## 📝 功能概述

Linux 终端 AI 助手是一个无需任何外部依赖的智能工具，它能够：

- 🔍 **自动错误分析**：当命令执行失败时，自动分析错误原因并提供解决方案
- 🔄 **实时捕获错误**：多种方式精确捕获命令错误输出
- 💡 **智能上下文感知**：基于当前工作环境和历史命令提供个性化建议
- 💬 **自然语言交互**：通过简单的 `ask` 命令直接咨询 AI 助手
- 🧠 **适应性学习**：识别用户的工作模式，提供更符合工作流程的建议

## ⚡ 快速开始

### 安装

只需一条命令即可完成安装：

```bash
# 克隆仓库并安装
git clone https://github.com/yourusername/linux-ai-assistant.git
cd linux-ai-assistant
./ai_assistant_standalone.py --install
source ~/.bashrc
```

### 使用示例

当命令执行失败时，AI 助手会自动分析并提供解决方案：

```bash
$ ls /nonexistent
ls: cannot access '/nonexistent': No such file or directory

⏳ AI伴侣正在帮你分析错误，请稍候...

🤖 AI助手建议 (命令: ls /nonexistent)
**错误原因：** 您尝试列出的目录 '/nonexistent' 不存在，所以 ls 命令无法访问它。

**解决方案：** 
   确认正确的路径或创建该目录：
   mkdir -p /nonexistent && ls /nonexistent

**后续建议：** 如果您不确定想要查看的目录名称，可以使用 find 命令在系统中搜索类似名称的目录。

💡 输入 'ask "更多问题"' 可以继续咨询
```

### AI 问答功能

```bash
# 直接提问
ask "如何查看系统内存使用情况？"
ask "如何安装nginx？"
ask "git push失败怎么办？"
```

### 系统信息查看

```bash
# 查看详细上下文
ai_context

# 查看配置
ai_config

# 调试信息
ai_debug
```

### 手动分析命令

```bash
# 手动执行命令并分析结果
ai_run ls /nonexistent
ai_run git push origin main
```

## ⚙️ 配置说明

### API 配置

支持多种 AI 服务：

```bash
# OpenAI API
python3 ~/.ai_assistant/ai_assistant.py --set-api openai https://api.openai.com/v1/chat/completions gpt-3.5-turbo YOUR_API_KEY

# 自定义 API
python3 ~/.ai_assistant/ai_assistant.py --set-api custom_api https://your-api.com/v1/chat/completions model_name YOUR_API_KEY

# Ollama 本地 API  
python3 ~/.ai_assistant/ai_assistant.py --set-api ollama http://localhost:11434 llama2 ""
```

### 查看当前配置

```bash
python3 ~/.ai_assistant/ai_assistant.py --config
```

### 测试 API 连接

```bash
python3 ~/.ai_assistant/ai_assistant.py --test
```

## 🔧 技术特性

### 零外部依赖
- 使用 Python 标准库实现
- 无需安装 requests、psutil 等第三方包
- 兼容 Python 3.6+

### 智能错误捕获
- 实时 stderr 捕获机制
- Base64 编码处理特殊字符
- 多重备份捕获方案
- 自动清理临时文件

### Shell 集成
- PROMPT_COMMAND 钩子
- 命令别名包装
- 环境变量管理
- 清理函数注册

## 🛠️ 可用命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `ask '问题'` | 智能问答 | `ask '如何解压tar.gz文件?'` |
| `ai_context` | 显示详细上下文 | `ai_context` |
| `ai_debug` | 调试和状态信息 | `ai_debug` |
| `ai_run <命令>` | 手动执行并分析 | `ai_run ls /tmp` |
| `ai_config` | 查看配置 | `ai_config` |

## 🔍 故障排除

### 安装问题

```bash
# 检查 Python 版本
python3 --version

# 手动重新安装钩子
python3 ~/.ai_assistant/ai_assistant.py --install

# 重新加载配置
source ~/.bashrc
```

### 功能测试

```bash
# 测试错误捕获
ai_run ls /nonexistent

# 测试 API 连接
python3 ~/.ai_assistant/ai_assistant.py --test

# 查看调试信息
ai_debug
```

### 卸载

```bash
# 删除安装目录
rm -rf ~/.ai_assistant

# 从 ~/.bashrc 中删除钩子部分
# 手动编辑 ~/.bashrc，删除 "Linux AI Assistant Hook" 部分
```

## 📄 项目结构

```
linux-ai-assistant/
├── ai_assistant_standalone.py  # 主程序（无依赖版本）
├── install_hook.sh            # 安装脚本
├── README.md                  # 项目说明
└── test.py                    # 测试脚本
```

## 💡 工作原理

1. **钩子机制**：利用 Bash 的 PROMPT_COMMAND 钩子，在每次命令执行后检查退出码
2. **错误捕获**：使用多种方法捕获命令的标准错误输出
3. **上下文分析**：收集系统环境、目录信息、Git 状态等上下文信息
4. **智能分析**：将错误信息和上下文发送给 AI 模型进行分析
5. **结果展示**：以友好的方式展示分析结果和建议

## 📊 上下文感知能力

AI 助手会收集和分析以下上下文信息：

- 当前工作目录和文件结构
- Git 仓库状态（如果在 Git 仓库中）
- 系统状态（内存、CPU、磁盘使用情况）
- 已安装的工具和服务
- 命令执行历史和模式
- 网络连接状态

## 🔒 隐私说明

- 所有数据处理在本地进行，仅将必要信息发送给 AI API
- 不收集个人身份信息
- 可以配置使用本地 AI 模型（如 Ollama）以增强隐私保护

## 🤝 贡献指南

欢迎贡献代码、报告问题或提供改进建议！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

MIT License

## 👏 致谢

- 感谢各种 AI 服务提供商
- 感谢 Linux 和 Bash 开发者
- 感谢所有开源社区的贡献者

---

💻 希望这个工具能让你的 Linux 终端使用体验更加智能、高效！

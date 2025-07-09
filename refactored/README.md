# Linux终端AI伴侣 - 重构版本 🤖

## 项目重构说明

本项目是对原始Linux终端AI伴侣的完全重构，采用模块化架构设计，提高了代码的可维护性、可扩展性和可测试性。

## 🏗️ 架构设计

### 模块化结构
```
ai_companion/
├── core/                   # 核心功能模块
│   ├── config.py          # 配置管理
│   └── system_info.py     # 系统信息收集
├── analyzers/             # 分析器模块
│   ├── context_analyzer.py    # 上下文分析
│   ├── error_analyzer.py      # 错误分析
│   └── command_history.py     # 命令历史分析
├── providers/             # AI服务提供商
│   └── ai_provider.py     # AI API接口
├── shell/                 # Shell集成
│   └── integration.py     # Shell钩子管理
└── app.py                 # 主应用类
```

### 设计原则

1. **单一职责原则**：每个模块只负责一个特定功能
2. **开放封闭原则**：对扩展开放，对修改封闭
3. **依赖倒置原则**：依赖抽象而不是具体实现
4. **接口隔离原则**：提供清晰的接口定义

## 🔧 核心组件

### 1. 配置管理器 (ConfigManager)
- **责任**：管理AI服务配置、功能开关等
- **特性**：
  - 支持多个AI服务配置
  - 类型安全的配置验证
  - 自动配置文件管理

```python
config_manager = ConfigManager()
api_config = AIServiceConfig(
    type="openai",
    base_url="https://api.openai.com/v1/chat/completions",
    model="gpt-3.5-turbo",
    api_key="your-key"
)
config_manager.set_ai_service("openai", api_config)
```

### 2. 系统信息收集器 (SystemInfoCollector)
- **责任**：收集系统状态、目录信息、Git状态等
- **特性**：
  - 非阻塞式信息收集
  - 错误容错机制
  - 结构化数据返回

### 3. 上下文分析器 (ContextAnalyzer)
- **责任**：整合各种上下文信息，提供统一视图
- **特性**：
  - 完整的环境上下文
  - 智能信息摘要
  - 格式化显示支持

### 4. AI提供商工厂 (AIProviderFactory)
- **责任**：创建和管理不同AI服务提供商
- **特性**：
  - 支持OpenAI、Ollama、Anthropic等
  - 统一的接口抽象
  - 易于扩展新的提供商

### 5. 错误分析器 (ErrorAnalyzer)
- **责任**：分析命令错误，生成AI建议
- **特性**：
  - 智能去重机制
  - 上下文感知的提示词构建
  - 结构化错误分析

## 🚀 主要改进

### 1. 代码结构优化
- **原版**：单文件1200+行，难以维护
- **重构版**：模块化设计，每个文件职责清晰，易于理解和修改

### 2. 错误处理改进
- **原版**：异常处理分散，容易崩溃
- **重构版**：统一的错误处理机制，优雅降级

### 3. 配置管理增强
- **原版**：配置结构混乱，验证不足
- **重构版**：强类型配置，自动验证，支持多配置

### 4. 可测试性提升
- **原版**：难以进行单元测试
- **重构版**：每个模块都可独立测试

### 5. 扩展性改善
- **原版**：添加新功能需要修改主类
- **重构版**：通过工厂模式和接口抽象，易于扩展

## 📦 安装和使用

### 快速开始

```bash
# 进入重构版本目录
cd refactored

# 安装Shell钩子
python3 main.py --install

# 配置API
python3 main.py --set-api openai https://api.openai.com/v1/chat/completions gpt-3.5-turbo YOUR_KEY

# 测试连接
python3 main.py --test

# 激活环境
source ~/.bashrc
```

### 主要命令

```bash
# 基本操作
python3 main.py --install           # 安装Shell钩子
python3 main.py --config            # 查看配置
python3 main.py --context           # 查看上下文
python3 main.py --test              # 测试API

# API管理
python3 main.py --set-api openai https://api.openai.com/v1/chat/completions gpt-3.5-turbo YOUR_KEY
python3 main.py --switch-model openai
python3 main.py --list-types

# 交互功能
python3 main.py --ask "如何查看内存使用情况？"
```

### Shell命令（安装后可用）

```bash
ask "如何解压tar.gz文件？"
ai_context
ai_config
ai_debug
ai_run ls /nonexistent
```

## 🧪 测试

运行测试套件：

```bash
cd refactored
python3 tests/test_ai_companion.py
```

测试覆盖：
- 配置管理器功能
- 系统信息收集
- 命令历史分析
- 主应用集成

## 🔍 兼容性

### 保持兼容
- ✅ 所有原有功能完全保留
- ✅ Shell集成方式不变
- ✅ 用户配置自动迁移
- ✅ 命令行接口兼容

### 改进点
- 🔧 更好的错误处理
- 🔧 更快的响应速度
- 🔧 更清晰的代码结构
- 🔧 更容易的功能扩展

## 📈 性能优化

1. **启动速度**：模块按需加载，减少启动时间
2. **内存使用**：优化数据结构，减少内存占用
3. **响应时间**：改进上下文收集算法
4. **错误处理**：减少异常传播，提高稳定性

## 🛣️ 未来扩展

### 已规划功能
- [ ] 插件系统支持
- [ ] 自定义命令模式
- [ ] 更多AI服务提供商
- [ ] Web界面管理
- [ ] 命令学习和建议优化

### 扩展示例

添加新的AI提供商：

```python
class CustomProvider(AIProvider):
    def call_api(self, prompt: str) -> str:
        # 实现自定义API调用
        pass

# 注册到工厂
AIProviderFactory.providers['custom'] = CustomProvider
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 添加测试用例
4. 确保所有测试通过
5. 提交Pull Request

## 📄 许可证

MIT License - 详见LICENSE文件

---

**重构版本的目标是在保持原有功能的基础上，提供更好的代码质量、更强的扩展性和更优的用户体验。**

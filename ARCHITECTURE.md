# CLI AI Agent — 架构设计文档

> 目标：从零构建一个类 Claude Code 的终端 AI Agent，保留核心机制，最大化学习价值。

---

## 一、系统总览

```
┌──────────────────────────────────────────────────┐
│                    CLI Layer                     │
│           (Rich + Prompt Toolkit)                │
├──────────────────────────────────────────────────┤
│                  Agent Loop                      │
│        ┌──────────────────────────┐              │
│        │  1. 构建 Prompt          │              │
│        │  2. 调用 LLM (streaming) │              │
│        │  3. 解析 Tool Call       │              │
│        │  4. 执行 Tool            │              │
│        │  5. 结果注入上下文       │              │
│        │  6. 回到步骤 1           │              │
│        └──────────────────────────┘              │
├──────────┬──────────┬──────────┬─────────────────┤
│ File     │ Bash     │ Grep     │  ...更多Tool    │
│ Tool     │ Tool     │ Tool     │                 │
├──────────┴──────────┴──────────┴─────────────────┤
│              LLM Provider Layer                  │
│        (OpenAI / Anthropic / Local)              │
├──────────────────────────────────────────────────┤
│              Core Infrastructure                 │
│   Config │ Logger │ Context Manager │ Safety     │
└──────────────────────────────────────────────────┘
```

---

## 二、核心架构拆解

### 1. Agent Loop（智能体循环）—— 整个项目的灵魂

这是 AI Agent 与普通 ChatBot 的根本区别。普通对话是一次性的问答，而 Agent 是一个**自主循环**——LLM 自己决定什么时候完成，什么时候需要调用工具继续。

```
User Input
    │
    ▼
┌──────────────┐
│ Build Prompt │ ◄── System Prompt + History + Tool Results
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Call LLM    │ ──► Streaming Output to Terminal
└──────┬───────┘
       │
       ▼
┌──────────────┐     No Tool Call
│ Has Tool Call?├──────────────────► Done → Wait for next user input
└──────┬───────┘
       │ Yes
       ▼
┌──────────────┐
│ Execute Tool │ ──► May require user confirmation
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Inject Result│ ──► Append tool result to message history
└──────┬───────┘
       │
       └──────► 回到 Build Prompt (新一轮循环)
```

**关键设计决策：**

| 决策点 | 选项 | 推荐 | 理由 |
|--------|------|------|------|
| 循环终止条件 | 最大轮数 / LLM说停 | 两者结合 | 防止无限循环 |
| Tool并行执行 | 串行 / 并行 | 先串行后优化 | 串行逻辑简单，并行涉及依赖分析 |
| 流式输出 | 等完整响应 / 逐token | 逐token流式 | 用户体验核心 |

**你能学到：**
- **ReAct 模式**：Reasoning + Acting，当前主流 Agent 范式
- **Tool Calling 协议**：LLM 如何通过结构化输出调用外部函数
- **流式处理**：SSE/WebSocket 流式解析，增量渲染
- **状态机设计**：有限状态机管理对话流转

---

### 2. Tool System（工具系统）—— Agent 的手和脚

```
┌─────────────────────────────────┐
│         ToolRegistry            │
│  ┌───────────────────────────┐  │
│  │ name: "read_file"         │  │
│  │ description: "..."        │  │
│  │ parameters: JSON Schema   │  │
│  │ execute: callable         │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ name: "write_file"        │  │
│  │ ...                       │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ name: "run_bash"          │  │
│  │ ...                       │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

**最小工具集（6个）：**

| 工具 | 功能 | 对标 Claude Code |
|------|------|-----------------|
| `read_file` | 读取文件内容 | Read |
| `write_file` | 写入/创建文件 | Write |
| `edit_file` | 精确字符串替换编辑 | Edit |
| `list_directory` | 列出目录结构 | Glob/Ls |
| `search_content` | 正则搜索文件内容 | Grep |
| `run_bash` | 执行 shell 命令 | Bash |

**Tool 定义协议（与 LLM 对接）：**

```python
# 每个Tool必须提供JSON Schema描述，这是LLM理解工具的唯一方式
TOOL_SCHEMA = {
    "name": "read_file",
    "description": "Read the contents of a file at the given path",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute file path"}
        },
        "required": ["path"]
    }
}
```

**你能学到：**
- **JSON Schema**：如何用结构化方式描述函数签名
- **插件化架构**：注册-发现-执行模式，开闭原则实践
- **权限与安全**：沙箱执行、路径校验、命令白名单
- **进程管理**：subprocess 的正确使用，超时控制，输出捕获

---

### 3. Context Manager（上下文管理）—— 决定智能体智商的上限

这是最容易被忽视但最影响质量的模块。LLM 的上下文窗口是有限的，如何管理历史消息直接决定了 Agent 的表现。

```
┌─────────────────────────────────────────┐
│           Message History                │
│                                         │
│  [System Prompt]                        │
│  [User Message]                         │
│  [Assistant Message + Tool Call]        │
│  [Tool Result]                          │
│  [Assistant Message + Tool Call]        │
│  [Tool Result]                          │
│  [Assistant Message]  ← 最终回复        │
│  ...                                    │
│                                         │
│  ⚠️ 超过 token limit 时需要裁剪策略     │
└─────────────────────────────────────────┘
```

**裁剪策略（由简到难）：**

```
Level 1: 简单截断 —— 保留最近 N 轮对话
Level 2: 摘要压缩 —— 用LLM总结旧对话，替换原文
Level 3: 重要性评分 —— 保留关键决策节点，丢弃冗余
```

**System Prompt 工程：**

```python
SYSTEM_PROMPT = """You are an AI assistant that helps with software engineering tasks.

You have access to the following tools:
- read_file: Read file contents
- write_file: Write to files
- edit_file: Make precise edits to files
- list_directory: List directory contents
- search_content: Search file contents with regex
- run_bash: Execute shell commands

Important rules:
1. Always read a file before editing it
2. Confirm before executing destructive commands
3. Be concise in your responses
4. Use tools to verify your work when possible
"""
```

**你能学到：**
- **Token 计数**：tiktoken 库的使用，不同模型的 tokenizer 差异
- **Prompt Engineering**：System Prompt 的设计艺术，角色设定与约束注入
- **滑动窗口 / 摘要压缩**：经典的上下文窗口管理策略
- **消息格式协议**：ChatML / 对话消息的标准结构

---

### 4. LLM Provider Layer（模型接入层）—— 统一接口，切换自如

```
┌──────────────────────┐
│    LLM Provider      │
│      (ABC)           │
│  + chat(messages)    │
│  + chat_stream(msgs) │
│  + get_tool_calls()  │
├──────────┬───────────┤
│          │           │
▼          ▼           ▼
OpenAI   Anthropic   Ollama
Provider  Provider   Provider
```

**统一接口设计：**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict

@dataclass  
class StreamChunk:
    content: str | None        # 文本内容
    tool_calls: list[ToolCall] # 工具调用
    finish_reason: str | None  # 结束原因

class LLMProvider(ABC):
    @abstractmethod
    async def chat_stream(
        self, 
        messages: list[dict], 
        tools: list[dict] | None = None
    ) -> AsyncIterator[StreamChunk]:
        """流式调用LLM，统一返回格式"""
        ...
```

**你能学到：**
- **抽象工厂模式**：面向接口编程，解耦具体实现
- **AsyncIterator**：Python 异步迭代器，流式数据处理
- **API 对接**：OpenAI / Anthropic SDK 的使用，SSE 流解析
- **适配器模式**：不同厂商 API 格式差异的统一封装

---

### 5. CLI Layer（终端交互层）—— 用户体验的门面

```
┌──────────────────────────────────────────┐
│  $ ai-coder "帮我创建一个FastAPI项目"      │
│                                          │
│  🤔 Thinking...                          │
│                                          │
│  🔧 read_file("./src/main.py")           │
│  📄 File not found, creating new...      │
│                                          │
│  🔧 write_file("./src/main.py", ...)     │
│  ✅ File created successfully            │
│                                          │
│  🔧 run_bash("pip install fastapi")      │
│  ⚠️  This will install packages. Allow?  │
│  > [y/n]: y                              │
│  ✅ Installed successfully               │
│                                          │
│  项目已创建！入口文件在 src/main.py       │
│  运行 `uvicorn src.main:app` 启动服务    │
│                                          │
│  $ _                                     │
└──────────────────────────────────────────┘
```

**你能学到：**
- **Rich 库**：终端富文本渲染，Markdown 渲染，进度条，语法高亮
- **Prompt Toolkit**：交互式命令行，自动补全，历史记录，多行输入
- **事件驱动 UI**：异步渲染，不阻塞用户输入

---

### 6. Safety Layer（安全层）—— 不可或缺的防线

```
Tool Call Request
       │
       ▼
┌──────────────┐
│ 权限检查      │ ── 写操作 / 删除操作 → 需要用户确认
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 路径沙箱      │ ── 禁止访问项目目录外的文件
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 命令过滤      │ ── 禁止 rm -rf /, curl | bash 等
└──────┬───────┘
       │
       ▼
   Execute Tool
```

**你能学到：**
- **安全沙箱设计**：最小权限原则
- **用户确认机制**：人机协作中的信任建立
- **输入验证**：路径遍历攻击、命令注入防御

---

## 三、技术选型

### 核心框架

| 层级 | 技术 | 理由 | 替代方案 |
|------|------|------|----------|
| 语言 | **Python 3.12+** | AI 生态最成熟，学习资源最多 | TypeScript (更接近真实 Claude Code) |
| 异步框架 | **asyncio** | 标准库，无额外依赖，流式处理必备 | trio, anyio |
| CLI | **Rich** | 终端渲染天花板，Markdown/代码高亮/进度条 | textual (TUI框架，更重量级) |
| 输入处理 | **Prompt Toolkit** | 交互式输入，多行编辑，历史补全 | python-inquirer (更简单) |
| LLM SDK | **openai** + **anthropic** | 官方 SDK，流式支持完善 | litellm (统一接口但多一层抽象) |
| 配置 | **pydantic-settings** | 类型安全的配置管理，.env 支持 | hydra (更复杂) |

### 开发工具

| 用途 | 技术 | 理由 |
|------|------|------|
| 包管理 | **uv** | 比 pip 快 10-100 倍，自带虚拟环境 |
| 代码质量 | **ruff** | 集成 lint + format，极快 |
| 类型检查 | **mypy** | 静态类型检查，大型项目必备 |
| 测试 | **pytest** + **pytest-asyncio** | 异步测试支持 |
| Token 计数 | **tiktoken** | OpenAI 开源，支持多种模型 |

---

## 四、项目结构

```
cli-agent/
├── pyproject.toml              # 项目配置 & 依赖
├── src/
│   └── cli_agent/
│       ├── __init__.py
│       ├── __main__.py         # python -m cli_agent 入口
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── loop.py         # ⭐ 核心：Agent 主循环
│       │   └── context.py      # 上下文管理，Token 计数，裁剪策略
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── base.py         # LLMProvider 抽象基类
│       │   ├── openai.py       # OpenAI 适配器
│       │   └── anthropic.py    # Anthropic 适配器
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── registry.py     # ToolRegistry 工具注册中心
│       │   ├── base.py         # Tool 基类
│       │   ├── file_read.py    # read_file
│       │   ├── file_write.py   # write_file
│       │   ├── file_edit.py    # edit_file (字符串替换)
│       │   ├── list_dir.py     # list_directory
│       │   ├── search.py       # search_content (正则搜索)
│       │   └── bash.py         # run_bash (含安全检查)
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── app.py          # CLI 主应用
│       │   └── renderer.py     # 终端渲染 (Markdown, 代码块, 工具调用)
│       └── config/
│           ├── __init__.py
│           └── settings.py     # Pydantic Settings 配置管理
├── tests/
│   ├── test_agent_loop.py
│   ├── test_tools.py
│   └── test_context.py
└── .env.example                # API Keys 配置模板
```

---

## 五、开发路线图（建议顺序）

按依赖关系排序，每一步都可独立运行验证：

```
Phase 1: 基础设施 ──────────────────────────────────
  ① 项目初始化 (uv init, pyproject.toml)
  ② 配置管理 (pydantic-settings, .env)
  ③ LLM Provider 基类 + OpenAI 适配器 (流式输出)

  🎯 里程碑: 能在终端流式打印 LLM 回复

Phase 2: 工具系统 ──────────────────────────────────
  ④ Tool 基类 + Registry
  ⑤ 实现 read_file / write_file / list_directory
  ⑥ 实现 search_content / edit_file / run_bash

  🎯 里程碑: 工具可独立调用和测试

Phase 3: Agent 核心 ────────────────────────────────
  ⑦ Agent Loop: 解析 Tool Call → 执行 → 注入结果 → 循环
  ⑧ Context Manager: 消息历史管理 + Token 计数
  ⑨ 安全层: 用户确认 + 路径沙箱 + 命令过滤

  🎯 里程碑: 完整的 Agent 循环可以端到端运行

Phase 4: 终端体验 ──────────────────────────────────
  ⑩ Rich 渲染: Markdown/代码高亮/工具调用展示
  ⑪ Prompt Toolkit: 多行输入/历史/补全
  ⑫ 交互模式: 持续对话 (非一次性问答)

  🎯 里程碑: 完整的 CLI Agent 可以日常使用

Phase 5: 进阶优化 ──────────────────────────────────
  ⑬ 上下文裁剪策略 (摘要压缩)
  ⑭ Anthropic Provider 适配
  ⑮ 错误恢复与重试机制
  ⑯ 多工具并行执行

  🎯 里程碑: 生产级可靠性
```

---

## 六、每一步具体学什么（知识地图）

| 阶段 | 编号 | 核心知识点 |
|------|------|-----------|
| **Phase 1** | ① | Python 项目管理, pyproject.toml 规范, uv 工具链 |
| | ② | Pydantic, 环境变量管理, 类型安全配置 |
| | ③ | **async/await**, **AsyncIterator**, SSE 流解析, API SDK 使用 |
| **Phase 2** | ④ | **抽象基类 (ABC)**, **JSON Schema**, 注册表模式, 插件架构 |
| | ⑤ | pathlib, 文件 I/O, 编码处理 |
| | ⑥ | **正则表达式**, subprocess, 文本 diff 算法 (edit_file) |
| **Phase 3** | ⑦ | **ReAct 循环**, 状态机, Tool Calling 协议解析, 消息格式 (ChatML) |
| | ⑧ | tiktoken, 滑动窗口, 消息裁剪策略, **Prompt Engineering** |
| | ⑨ | 沙箱设计, 路径遍历防御, 命令注入防御, 最小权限原则 |
| **Phase 4** | ⑩ | Rich 库, Markdown AST 渲染, 语法高亮, Live Display |
| | ⑪ | Prompt Toolkit, 事件循环集成, 异步输入处理 |
| | ⑫ | REPL 模式, 会话管理, 优雅退出 (信号处理) |
| **Phase 5** | ⑬ | LLM 摘要, 重要性评分, 上下文压缩算法 |
| | ⑭ | 适配器模式, Anthropic API 差异, 流式格式统一 |
| | ⑮ | 指数退避重试, 断路器模式, 错误分类处理 |
| | ⑯ | asyncio.gather, 依赖图分析, 并发安全 |

---

## 七、关键代码骨架参考

### Agent Loop 核心伪代码

```python
async def agent_loop(user_input: str, history: list[dict]):
    history.append({"role": "user", "content": user_input})
    
    while True:
        # 1. 调用 LLM（流式）
        assistant_content = ""
        tool_calls = []
        
        async for chunk in provider.chat_stream(
            messages=history, 
            tools=tool_schemas
        ):
            if chunk.content:
                render_to_terminal(chunk.content)  # 流式渲染
                assistant_content += chunk.content
            if chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)
        
        # 2. 记录 assistant 消息
        history.append({
            "role": "assistant",
            "content": assistant_content,
            "tool_calls": tool_calls or None
        })
        
        # 3. 无工具调用 → 循环结束
        if not tool_calls:
            break
        
        # 4. 执行工具调用
        for tc in tool_calls:
            if requires_confirmation(tc):
                if not await ask_user(tc):
                    result = "User denied this operation"
                else:
                    result = await registry.execute(tc.name, tc.arguments)
            else:
                result = await registry.execute(tc.name, tc.arguments)
            
            # 5. 注入工具结果
            history.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(result)
            })
        
        # 6. 检查上下文长度，必要时裁剪
        history = context_manager.maybe_truncate(history)
        
        # 继续循环，让 LLM 看到工具结果后决定下一步
```

---

## 八、参考资源

| 资源 | 用途 |
|------|------|
| [OpenAI Tool Calling 文档](https://platform.openai.com/docs/guides/function-calling) | 理解 Tool Calling 协议 |
| [Anthropic Tool Use 文档](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) | 对比不同厂商实现差异 |
| [ReAct 论文](https://arxiv.org/abs/2210.03629) | Agent 范式的学术根基 |
| [Rich 官方文档](https://rich.readthedocs.io/) | 终端渲染 |
| [tiktoken](https://github.com/openai/tiktoken) | Token 计数 |

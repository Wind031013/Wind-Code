# Changelog

## [0.1.0] - 2026-05-26

### 新增

- **智能体循环**：基于思维链 (CoT) 的多步任务拆解与模型推理。
- **Human-in-the-Loop**：中/高风险工具调用前弹出确认对话框，支持批准(y)、拒绝(n)、编辑参数(e)。
- **文件系统工具**：
  - `get_file_path` — 获取当前工作目录及文件列表
  - `get_file_content` — 读取指定文件内容
  - `write_file` — 写入文件（已存在则覆盖，自动创建父目录）
  - `delete_file` — 删除指定文件
- **工具风险分级**：`SAFE` / `MODERATE` / `DANGEROUS` 三级风险等级，支持按参数动态调整。
- **消息管理**：基于滑动窗口的短期记忆机制（默认保留最近 20 条对话）。
- **日志系统**：`RotatingFileHandler` 滚动日志（单文件 1MB，保留 5 个备份）。
- **交互模式**：支持 REPL 交互模式与单次查询模式（`wind <query>`）。
- **模型配置**：通过环境变量 `WindCode_API_KEY` / `WindCode_BASE_URL` 配置 API 连接。

### 开发中

- 终端交互能力（Shell 命令执行与反馈解析）
- 文件重命名与局部更新 (Patching)

### 规划中

- 自我修正机制（基于执行反馈的自动 Debug 与路径调整）
- 长期记忆（用户编程习惯与偏好风格记录）
- WIND.md 指令记忆约束

## [0.2.0] - 2026-06-11

### 修复

- 文件terminal_tool.py
  - 缩进存在问题
- 文件agent.py
  - 错误解析缺少返回给LLM的
  - 没有调用短期记忆的裁切

### 新增
- [自定义错误类](/utils/exceptions.py)
- [自定义模型](/utils/config.py)
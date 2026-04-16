# 版本管理功能 - 代码变更说明

## 概述

为 WindCode 添加基于 git 的版本管理功能，在每次文件修改操作后自动创建版本快照，支持通过 CLI 命令查看历史、回退版本、对比差异。版本数据存储在独立 git 仓库中，不影响用户原有的 git 配置。

---

## 新增文件

### `agent/utils/version.py`

VersionManager 核心类，负责版本快照的创建、查询、回退和差异对比。

#### 类属性

```python
VERSIONS_DIR = ".windcode_versions"
```

独立 git 仓库的目录名，存放在项目根目录下。通过 `.gitignore` 和 `info/exclude` 确保该目录不会被用户 git 或版本管理 git 自身跟踪。

```python
SNAPSHOT_TOOLS = {"write_file", "delete_file", "run_command"}
```

会触发自动快照的工具名称集合，这些工具可能修改项目文件。

#### `__init__(self, project_dir: str)`

- 保存项目目录的绝对路径
- 计算独立 git 仓库路径 `project_dir / .windcode_versions`
- 通过 `shutil.which("git")` 检测 git 是否可用，不可用时禁用版本管理并提示

#### `_git_env(self) -> dict`

构建 git 命令所需的环境变量，设置 `GIT_DIR` 和 `GIT_WORK_TREE` 指向独立仓库和项目目录，使 git 操作与用户原有仓库完全隔离。

#### `_run_git(self, *args) -> subprocess.CompletedProcess`

执行 git 命令的统一方法：
- 使用 `_git_env()` 的环境变量
- 设置 `cwd` 为项目目录
- 使用 `encoding="utf-8"` + `errors="replace"` 处理 Windows 下的编码问题
- 设置 30 秒超时防止挂起

#### `is_initialized` (property)

检查独立 git 仓库是否已初始化：判断 `.windcode_versions/HEAD` 文件是否存在。

#### `initialize(self) -> bool`

初始化版本管理：
1. 执行 `git init` 创建独立仓库
2. 调用 `_setup_excludes()` 将 `.windcode_versions/` 加入 git 排除列表
3. 调用 `_add_to_project_gitignore()` 将其加入用户项目的 `.gitignore`（仅当文件已存在时追加）
4. 执行 `git add -A && git commit` 创建初始快照

#### `create_snapshot(self, message: str = "") -> tuple[bool, str]`

创建版本快照的核心方法：
1. 若未初始化则自动调用 `initialize()`
2. `git add -A` 暂存所有变更
3. 通过 `git status --porcelain` 检查是否有实际变更，无变更则跳过
4. 截断超过 100 字符的提交信息
5. `git commit -m "windcode: {message}"` 提交
6. 通过 `git rev-parse --short HEAD` 获取短哈希用于返回信息

#### `list_versions(self, count: int = 20) -> list[dict]`

查询最近 N 条版本记录：
- 使用 `git log` 的自定义格式 `%h|%ai|%s`（短哈希|日期|提交信息）
- 按 `|` 分隔解析为字典列表，每项包含 `hash`、`date`、`message`

#### `rollback(self, version_hash: str) -> tuple[bool, str]`

回退到指定版本：
1. 通过 `git rev-parse --verify` 验证目标哈希是否存在
2. 调用 `create_snapshot("回退前自动保存")` 保存当前状态作为安全点
3. 使用 `git read-tree -u --reset <hash>` 将工作目录恢复到目标版本状态
   - 选择 `read-tree` 而非 `checkout` 是因为 `git checkout <hash> -- .` 在使用独立 GIT_DIR 时存在 pathspec 匹配问题
4. `git add -A && git commit` 将恢复后的状态提交为新版本（保留完整历史）

#### `get_diff(self, version_hash: str) -> str`

对比当前 HEAD 与指定版本的差异，使用 `git diff HEAD <hash>`。

---

## 修改文件

### `agent/agent.py`

原始备份位于 `backups/agent.py`。

#### 1. 新增导入

```python
from agent.utils.version import VersionManager
```

#### 2. `CliAgent.__init__` 新增两行

```python
self.version_manager = VersionManager(os.getcwd())
self.current_instruction = ""
```

- `version_manager`：版本管理器实例，绑定到当前工作目录
- `current_instruction`：记录当前用户输入的指令，用作快照的 commit message

#### 3. `CliAgent.run` 新增一行

```python
def run(self, user_input: str):
    self.current_instruction = user_input  # 新增：记录用户指令
    self.messages.append({"role": "user", "content": user_input})
```

在每次对话开始时保存用户指令，供后续快照使用。

#### 4. `_execute_tool_with_hitl` 新增自动快照逻辑

在工具执行成功后添加：

```python
if result.success and tool_name in VersionManager.SNAPSHOT_TOOLS:
    snapshot_ok, snapshot_msg = self.version_manager.create_snapshot(
        self.current_instruction
    )
    if snapshot_ok and "跳过快照" not in snapshot_msg:
        print(f"📸 {snapshot_msg}")
```

- 仅当工具执行成功且属于修改类工具（`write_file`、`delete_file`、`run_command`）时触发
- 无文件变更时静默跳过（不打印提示）
- 快照创建成功时打印提示信息

---

### `agent/cli.py`

原始备份位于 `backups/cli.py`。

#### 1. 新增 `_handle_version_commands` 函数

处理以 `/` 开头的版本管理命令，返回 `True` 表示已处理该命令。

**`/versions` 命令：**
- 检查 git 可用性
- 调用 `vm.list_versions()` 获取版本列表
- 格式化输出哈希、日期和提交信息

**`/rollback [hash]` 命令：**
- 不带参数时：显示版本列表，用户可输入序号或哈希选择
- 带参数时：直接使用指定哈希
- 回退前需用户输入 `y` 确认
- 调用 `vm.rollback()` 执行回退

**`/diff <hash>` 命令：**
- 调用 `vm.get_diff()` 显示当前状态与指定版本的差异

#### 2. `main` 函数修改

启动信息增加版本管理命令提示：

```python
print("版本管理: /versions 查看历史  /rollback 回退  /diff 对比")
```

主循环中增加 `/` 命令拦截：

```python
if user_input.startswith("/"):
    if _handle_version_commands(user_input, agent):
        continue
```

在将输入传递给 agent 之前，先检查是否为版本管理命令，若是则处理并跳过 agent 执行。

---

## 数据流

```
用户输入指令
    │
    ├─ 以 / 开头 → _handle_version_commands() → 版本管理操作
    │
    └─ 普通指令 → agent.run(user_input)
                     │
                     ├─ self.current_instruction = user_input
                     │
                     └─ 工具循环
                          │
                          ├─ write_file/delete_file/run_command 成功
                          │   └─ version_manager.create_snapshot(用户指令)
                          │       └─ git add -A && git commit
                          │
                          └─ 其他工具 → 不创建快照
```

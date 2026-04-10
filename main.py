import os
import json
from pathlib import Path
from openai import OpenAI
import tiktoken

from tools.base import BaseTool, ToolResult, RiskLevel
from tools.OSTools import (
    GetFilePathTool,
    ReadFileTool,
    WriteFileTool,
    DeleteFileTool,
    ListDirTool,
)
from tools.TerminalTool import RunCommandTool
from utils.logger import setup_logger


class Config:
    API_KEY = os.environ.get("ZHI_PU_API_KEY")
    BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
    LOG_DIR = Path("./logs")
    TOOLS_JSON = Path("./tools/tools.json")
    PROMPT_PATH = Path("./prompt")
    MODEL = "glm-4"


logger = setup_logger(__name__, Config.LOG_DIR)


class HumanApproval:
    APPROVE = "y"
    REJECT = "n"
    EDIT = "e"

    @staticmethod
    def ask(tool: BaseTool, **kwargs) -> str:
        message = tool.confirm_message(**kwargs)
        print(f"\n{'=' * 60}")
        print(message)
        print(f"{'=' * 60}")
        print("[y] 批准  [n] 拒绝  [e] 编辑参数")
        choice = input("请选择: ").strip().lower()
        return choice

    @staticmethod
    def edit_params(kwargs: dict) -> dict:
        print(f"\n当前参数: {json.dumps(kwargs, ensure_ascii=False, indent=2)}")
        print("输入新的JSON参数（直接回车保持原参数）:")
        user_input = input("> ").strip()
        if not user_input:
            return kwargs
        try:
            new_kwargs = json.loads(user_input)
            return new_kwargs
        except json.JSONDecodeError:
            print("JSON解析失败，保持原参数")
            return kwargs


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def all_tools(self) -> dict[str, BaseTool]:
        return self._tools


class CliAgent:

    def __init__(self):
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL,
        )
        logger.debug("OpenAI 客户端创建成功")

        # Token 计算
        try:
            self.encoding = tiktoken.encoding_for_model(Config.MODEL)
            logger.debug("分词器初始化成功...")
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")
            logger.debug(f"未找到模型: {Config.MODEL}的分词器，使用 cl100k_base")

        # 加载主提示词
        main_prompt_path = Config.PROMPT_PATH / "main.md"
        if main_prompt_path.exists():
            self.main_prompt = main_prompt_path.read_text(encoding="utf-8")
            logger.debug("加载主提示成功...")
        else:
            logger.warning(f"未找到提示文件: {main_prompt_path}")
            self.main_prompt = "你是一个ai助手。"
        # 工具映射表
        self.registry = ToolRegistry()
        self._register_tools()
        # 注册工具
        self.tools_schema = self._load_tools_schema()

        # 初始化对话历史
        self.messages = [{"role": "system", "content": self.main_prompt}]

    def _register_tools(self):
        tools = [
            GetFilePathTool(),
            ReadFileTool(),
            WriteFileTool(),
            DeleteFileTool(),
            ListDirTool(),
            RunCommandTool(),
        ]
        for tool in tools:
            self.registry.register(tool)
            logger.debug(f"注册工具: {tool.name} (风险: {tool.risk_level.value})")

    def _load_tools_schema(self):
        with open(Config.TOOLS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)

    def count_tokens(self, text):
        return len(self.encoding.encode(text))

    def call_model(self):
        try:
            response = self.client.chat.completions.create(
                model=Config.MODEL,
                messages=self.messages,
                tools=self.tools_schema,
                timeout=60,
            )
            return response
        except Exception as e:
            logger.error(f"调用模型失败: {e}")
            raise

    def _execute_tool_with_hitl(self, tool_name: str,
                                kwargs: dict) -> ToolResult:
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolResult(f"工具不存在: {tool_name}", success=False)

        if tool.requires_confirmation():
            while True:
                choice = HumanApproval.ask(tool, **kwargs)

                if choice == HumanApproval.APPROVE:
                    break
                elif choice == HumanApproval.REJECT:
                    print("❌ 已拒绝执行")
                    return ToolResult("用户拒绝了此操作", success=False)
                elif choice == HumanApproval.EDIT:
                    kwargs = HumanApproval.edit_params(kwargs)
                else:
                    print("无效输入，请重新选择")
                    continue

        result = tool.execute(**kwargs)
        status = "✅" if result.success else "❌"
        print(f"{status} {tool_name}: {result.output[:200]}")
        return result

    def run(self, user_input: str):
        # 添加用户消息到对话历史
        self.messages.append({"role": "user", "content": user_input})

        while True:
            # 发送请求
            response = self.call_model()
            # 读取响应
            msg = response.choices[0].message

            self.messages.append({
                "role":
                "assistant",
                "content":
                msg.content,
                "tool_calls":
                [{
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                 for tc in (msg.tool_calls or [])] if msg.tool_calls else None,
            })

            if not msg.tool_calls:
                if msg.content:
                    print(f"\n{msg.content}")
                break
            # 获取工具调用
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                try:
                    arg = json.loads(tool_call.function.arguments)
                    result = self._execute_tool_with_hitl(func_name, arg)
                except Exception as e:
                    result = ToolResult(f"执行函数异常: {e}", success=False)

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })


if __name__ == "__main__":
    exit_words = ["exit", "quit", "e", "E"]
    agent = CliAgent()
    logger.debug("CliAgent 启动成功...")
    while True:
        try:
            user_input = input("\n请输入: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nbyebye")
            break

        if not user_input:
            continue
        if user_input in exit_words:
            print("byebye")
            break

        try:
            agent.run(user_input)
        except Exception as e:
            logger.error(f"运行出错: {e}")
            print(f"运行出错: {e}")

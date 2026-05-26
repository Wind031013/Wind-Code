from tools.base import BaseTool, ToolResult, RiskLevel
from tools.os_tools import (
    GetFilePath,
    GetFileContent,
    WriteFile,
    DeleteFile
)
from utils.logger import setup_logger
from enum import Enum
import json
logger = setup_logger(__name__)

class Operation(Enum):
    APPROVE = "y"
    REJECT = "n"
    EDIT = "e"

class ToolRegistry:
    """注册工具"""
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)
    
    def all_tools(self) -> dict[str, BaseTool]:
        return self._tools

class UseTools:
    """工具调用类"""
    def __init__(self):
        self._register_tools()

    def _register_tools(self):
        """注册工具"""
        tools = [
            GetFilePath(),
            GetFileContent(),
            WriteFile(),
            DeleteFile(),
        ]
        self.registry = ToolRegistry()
        for tool in tools:
            self.registry.register(tool)
            logger.debug(f"注册工具：{tool.name}")

    def ask(self, tool: BaseTool, **kwargs) -> str:
        """请求权限"""
        message = tool.confirm_message(**kwargs)
        print(message)
        choice = input("请选择：").strip().lower()
        return choice

    def edit_params(self, kwargs: dict) -> dict:
        """修改参数"""
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

    def execute_tool(self, tool_name: str, kwargs) -> ToolResult:
        """调用工具"""
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolResult(f"工具不存在: {tool_name} ", False)

        risk = tool.get_risk_level(**kwargs)

        if risk in (RiskLevel.MODERATE, RiskLevel.DANGEROUS):
            while True:
                choice = self.ask(tool, **kwargs)
                if choice == Operation.APPROVE.value:
                    break
                elif choice == Operation.REJECT.value:
                    return ToolResult("用户拒绝了此次操作", False)
                elif choice == Operation.EDIT.value:
                    kwargs = self.edit_params(kwargs)
                    continue

        return tool.execute(**kwargs)


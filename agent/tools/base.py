from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class RiskLevel(Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    DANGEROUS = "dangerous"


class ToolResult:
    """
    工具调用结果
    output: 输出结果
    success: 是否成功
    metadata: 元数据
    """
    def __init__(self, output: str, success: bool = True, metadata: dict = None):
        self.output = output
        self.success = success
        self.metadata = metadata or {}

    def __str__(self):
        return self.output


class BaseTool(ABC):
    """工具基类"""
    name: str = ""
    description: str = ""
    risk_level: RiskLevel = RiskLevel.SAFE

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult: ...

    def requires_confirmation(self) -> bool:
        return self.risk_level in (RiskLevel.MODERATE, RiskLevel.DANGEROUS)

    def confirm_message(self, **kwargs) -> str:
        return f"即将执行 [{self.name}]，参数: {kwargs}"

    def format_display(self, **kwargs) -> str:
        return self.confirm_message(**kwargs)

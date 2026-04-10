from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

# 危险级别
class RiskLevel(Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    DANGEROUS = "dangerous"


class ToolResult:
    def __init__(self, output: str, success: bool = True, metadata: dict = None):
        self.output = output
        self.success = success
        self.metadata = metadata or {}

    def __str__(self):
        return self.output


class BaseTool(ABC):
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

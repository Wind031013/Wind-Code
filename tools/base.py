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

    def __init__(self, output: str, success: bool = True):
        self.output = output
        self.success = success

    def __str__(self):
        return self.output


class BaseTool(ABC):
    """工具基类"""

    name: str = ""
    description: str = ""
    risk_level: RiskLevel = RiskLevel.SAFE

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult: ...

    def get_risk_level(self, **kwargs) -> RiskLevel:
        """根据参数动态返回风险等级，默认返回类级 risk_level"""
        return self.risk_level

    def confirm_message(self, **kwargs) -> str:
        """确认消息"""
        dividing_line = "=" * 60
        message = f"工具: {self.name}\n描述: {self.description}\n参数: {kwargs}"
        return f"{dividing_line}\n{message}\n{dividing_line}\n[y] 批准  [n] 拒绝  [e] 编辑参数"

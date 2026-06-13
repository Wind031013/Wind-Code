class WindCodeError(Exception):
    pass

class UnknownToolTypeError(WindCodeError):
    def __init__(self, tool_type: str, tool_call_id: str):
        super().__init__(
            f"未知的工具调用类型: '{tool_type}'（仅支持 function）",
        )
        self.tool_call_id=tool_call_id,
        self.tool_type = tool_type

class ToolArgumentParseError(WindCodeError):
    def __init__(self, raw_arguments: str, tool_call_id: str, cause: Exception):
        super().__init__(
            f"工具参数解析失败: {cause}",
            tool_call_id=tool_call_id,
        )
        self.raw_arguments = raw_arguments
        self.cause = cause
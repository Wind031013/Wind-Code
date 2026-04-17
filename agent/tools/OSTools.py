import os
from agent.tools.base import BaseTool, ToolResult, RiskLevel
from agent.utils.logger import setup_logger

logger = setup_logger(__name__)

class GetFilePathTool(BaseTool):
    """
    获取当前工作目录以及该目录下的所有文件名
    """
    name = "get_file_path"
    description = "获取当前工作目录以及该目录下的所有文件名"
    risk_level = RiskLevel.SAFE
    def execute(self, **kwargs) -> ToolResult:
        current_dir = os.getcwd()
        try:
            items = os.listdir(current_dir)
            files = []
            dirs = []
            for item in items:
                full_path = os.path.join(current_dir, item)
                if os.path.isfile(full_path):
                    files.append(item)
                elif os.path.isdir(full_path):
                    dirs.append(item)

            result = f"当前目录: {current_dir}\n"
            logger.debug("已获取目录下的文件和文件夹")
            if files:
                result += f"\n文件 ({len(files)}个):\n" + "\n".join(files)

            return ToolResult(result)
        except Exception as e:
            return ToolResult(f"Error: {str(e)}", success=False)


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "读取指定路径文件内容"
    risk_level = RiskLevel.SAFE

    def execute(self, path: str = "", **kwargs) -> ToolResult:
        if not os.path.exists(path):
            return ToolResult("Error: File not found.", success=False)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return ToolResult(content)
        except Exception as e:
            return ToolResult(f"Error: {str(e)}", success=False)


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "将内容写入指定路径的文件（会覆盖已有文件）"
    risk_level = RiskLevel.DANGEROUS

    def confirm_message(self, path: str = "", content: str = "", **kwargs) -> str:
        is_overwrite = os.path.exists(path)
        action = "覆盖" if is_overwrite else "创建"
        preview = content[:200] + "..." if len(content) > 200 else content
        return (
            f"⚠️  写入文件 [{action}]: {path}\n"
            f"    内容预览 ({len(content)} 字符):\n"
            f"    {preview}"
        )

    def execute(self, path: str = "", content: str = "", **kwargs) -> ToolResult:
        try:
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(f"Successfully wrote to {path}")
        except Exception as e:
            return ToolResult(f"Error: {str(e)}", success=False)


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "删除指定路径的文件"
    risk_level = RiskLevel.DANGEROUS

    def confirm_message(self, path: str = "", **kwargs) -> str:
        return f"🔴 删除文件: {path}"

    def execute(self, path: str = "", **kwargs) -> ToolResult:
        if not os.path.exists(path):
            return ToolResult("Error: File not found.", success=False)
        try:
            os.remove(path)
            return ToolResult(f"Successfully deleted {path}")
        except Exception as e:
            return ToolResult(f"Error: {str(e)}", success=False)


class ListDirTool(BaseTool):
    name = "list_dir"
    description = "列出指定目录下的文件和子目录"
    risk_level = RiskLevel.SAFE

    def execute(self, path: str = ".", **kwargs) -> ToolResult:
        target = path if path else "."
        if not os.path.isdir(target):
            return ToolResult(f"Error: {target} is not a directory", success=False)
        try:
            entries = os.listdir(target)
            result_lines = []
            for entry in sorted(entries):
                full = os.path.join(target, entry)
                if os.path.isdir(full):
                    result_lines.append(f"  📁 {entry}/")
                else:
                    size = os.path.getsize(full)
                    result_lines.append(f"  📄 {entry}  ({size} bytes)")
            output = f"目录: {os.path.abspath(target)}\n" + "\n".join(result_lines)
            return ToolResult(output)
        except Exception as e:
            return ToolResult(f"Error: {str(e)}", success=False)

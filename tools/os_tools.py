import os
from tools.base import BaseTool, RiskLevel, ToolResult
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GetFilePath(BaseTool):
    """获取当前工作目录以及该目录下的所有文件名"""

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
                complete_path = os.path.join(current_dir, item)
                if os.path.isfile(complete_path):
                    files.append(item)
                elif os.path.isdir(complete_path):
                    dirs.append(item)

            result = f"当前目录: {current_dir}\n"
            result += f"\n文件 ({len(files)}):\n" + "\n".join(f"  - {f}" for f in files)
            result += f"\n\n目录 ({len(dirs)}):\n" + "\n".join(f"  - {d}" for d in dirs)
            logger.debug("当前工作目录以及该目录下的所有文件名获取成功")
            return ToolResult(result)
        except Exception as e:
            logger.error(f"GetFilePathTool运行失败{e}")
            return ToolResult(f"Error{str(e)}", success=False)

class GetFileContent(BaseTool):
    """读取指定路径文件内容"""
    name = "get_file_content"
    description = "读取指定路径文件内容"
    risk_level = RiskLevel.SAFE

    def execute(self, file_path: str = "", **kwargs) -> ToolResult:
        if not os.path.exists(file_path):
            return ToolResult(f"文件不存在: {file_path}", success=False)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return ToolResult(content)
        except Exception as e:
            logger.error(f"ReadFileTool运行失败{e}")
            return ToolResult(f"Error{str(e)}", success=False)
    
class WriteFile(BaseTool):
    """将内容写入指定路径的文件"""
    name = "write_file"
    description = "将内容写入指定路径的文件"
    risk_level = RiskLevel.SAFE

    def get_risk_level(self, **kwargs) -> RiskLevel:
        file_path = kwargs.get("file_path", "")
        if file_path and os.path.exists(file_path):
            return RiskLevel.MODERATE
        return RiskLevel.SAFE

    def execute(self, file_path: str = "", content: str = "", **kwargs) -> ToolResult:
        try:
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(f"文件写入成功: {file_path}")
        except Exception as e:
            logger.error(f"WriteFileTool运行失败{e}")
            return ToolResult(f"Error{str(e)}", success=False)

class DeleteFile(BaseTool):
    """删除指定路径的文件"""
    name = "delete_file"
    description = "删除指定路径的文件"
    risk_level = RiskLevel.MODERATE

    def execute(self, file_path: str = "", **kwargs) -> ToolResult:
        if not os.path.exists(file_path):
            return ToolResult(f"文件不存在: {file_path}", success=False)
        try:
            os.remove(file_path)
            return ToolResult(f"文件删除成功: {file_path}")
        except Exception as e:
            logger.error(f"DeleteFileTool运行失败{e}")
            return ToolResult(f"Error{str(e)}", success=False)
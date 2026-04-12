import subprocess
from agent.tools.base import BaseTool, ToolResult, RiskLevel


BLOCKED_PATTERNS = [
    "rm -rf /",
    "mkfs",
    "dd if=",
    ":(){:|:&};:",
    "chmod -R 777 /",
    " > /dev/sda",
]


class RunCommandTool(BaseTool):
    name = "run_command"
    description = "在终端中执行shell命令并返回结果"
    risk_level = RiskLevel.DANGEROUS

    def confirm_message(self, command: str = "", cwd: str = "", **kwargs) -> str:
        dir_info = f" (工作目录: {cwd})" if cwd else ""
        return f"🖥️  执行命令{dir_info}: {command}"

    def execute(
        self, command: str = "", cwd: str = "", timeout: int = 120, **kwargs
    ) -> ToolResult:
        if not command:
            return ToolResult("Error: command is empty", success=False)

        for pattern in BLOCKED_PATTERNS:
            if pattern in command:
                return ToolResult(
                    f"命令被安全策略拦截: 包含危险模式 '{pattern}'",
                    success=False,
                )

        actual_cwd = cwd if cwd else None

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=actual_cwd,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )

            MAX_OUTPUT = 8000
            stdout = result.stdout
            stderr = result.stderr

            if len(stdout) > MAX_OUTPUT:
                stdout = f"...(截断，共{len(stdout)}字符)\n" + stdout[-MAX_OUTPUT:]
            if len(stderr) > MAX_OUTPUT:
                stderr = f"...(截断，共{len(stderr)}字符)\n" + stderr[-MAX_OUTPUT:]

            output_parts = []
            if stdout:
                output_parts.append(stdout)
            if stderr:
                output_parts.append(f"[stderr]\n{stderr}")

            output = "\n".join(output_parts) if output_parts else "(无输出)"
            success = result.returncode == 0

            if not success:
                output += f"\n[退出码: {result.returncode}]"

            return ToolResult(output, success=success)

        except subprocess.TimeoutExpired:
            return ToolResult(
                f"命令执行超时（{timeout}秒）: {command}",
                success=False,
            )
        except Exception as e:
            return ToolResult(f"执行异常: {str(e)}", success=False)

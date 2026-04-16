import os
import shutil
import subprocess
from pathlib import Path


class VersionManager:
    VERSIONS_DIR = ".windcode_versions"
    SNAPSHOT_TOOLS = {"write_file", "delete_file", "run_command"}

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir).resolve()
        self.git_dir = self.project_dir / self.VERSIONS_DIR
        self._available = shutil.which("git") is not None
        if not self._available:
            print("⚠️  未检测到 git，版本管理功能已禁用")

    @property
    def available(self) -> bool:
        return self._available

    def _git_env(self) -> dict:
        """获取git环境变量"""
        return {
            **os.environ,
            "GIT_DIR": str(self.git_dir),
            "GIT_WORK_TREE": str(self.project_dir),
        }

    def _run_git(self, *args) -> subprocess.CompletedProcess:
        """执行git命令"""
        return subprocess.run(
            ["git", *args],
            env=self._git_env(),
            capture_output=True,
            text=True,
            cwd=str(self.project_dir),
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )

    @property
    def is_initialized(self) -> bool:
        """检测是否已初始化"""
        return self.git_dir.exists() and (self.git_dir / "HEAD").exists()

    def initialize(self) -> bool:
        """初始化版本管理"""
        if not self._available:
            return False
        if self.is_initialized:
            return True

        result = self._run_git("init")
        if result.returncode != 0:
            print(f"版本管理初始化失败: {result.stderr}")
            return False

        self._setup_excludes()
        self._add_to_project_gitignore()

        self._run_git("add", "-A")
        self._run_git("commit", "-m", "初始化", "--allow-empty")
        return True

    def _setup_excludes(self):
        """创建git忽略文件"""
        exclude_path = self.git_dir / "info" / "exclude"
        exclude_path.parent.mkdir(parents=True, exist_ok=True)
        with open(exclude_path, "a", encoding="utf-8") as f:
            f.write("\n.windcode_versions/\n")

    def _add_to_project_gitignore(self):
        gitignore = self.project_dir / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text(encoding="utf-8")
            if ".windcode_versions/" not in content:
                with open(gitignore, "a", encoding="utf-8") as f:
                    f.write("\n.windcode_versions/\n")

    def create_snapshot(self, message: str = "") -> tuple[bool, str]:
        if not self._available:
            return False, "Git 不可用，版本管理已禁用"
        if not self.is_initialized:
            if not self.initialize():
                return False, "版本管理初始化失败"

        self._run_git("add", "-A")

        status = self._run_git("status", "--porcelain")
        if status.returncode == 0 and not status.stdout.strip():
            return True, "无变更，跳过快照"

        if len(message) > 100:
            message = message[:97] + "..."

        result = self._run_git("commit", "-m", f" {message}")
        if result.returncode == 0:
            hash_result = self._run_git("rev-parse", "--short", "HEAD")
            short_hash = (hash_result.stdout.strip()
                          if hash_result.returncode == 0 else "?")
            return True, f"版本快照已创建 [{short_hash}]: {message}"

        if "nothing to commit" in result.stdout:
            return True, "无变更，跳过快照"

        return False, f"创建快照失败: {result.stderr}"

    def list_versions(self, count: int = 20) -> list[dict]:
        if not self.is_initialized:
            return []

        result = self._run_git("log", f"-{count}", "--oneline",
                               "--format=%h|%ai|%s")
        if result.returncode != 0:
            return []

        versions = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                versions.append({
                    "hash": parts[0],
                    "date": parts[1],
                    "message": parts[2]
                })
        return versions

    def rollback(self, version_hash: str) -> tuple[bool, str]:
        if not self._available:
            return False, "Git 不可用，版本管理已禁用"
        if not self.is_initialized:
            return False, "版本管理未初始化"

        verify = self._run_git("rev-parse", "--verify", version_hash)
        if verify.returncode != 0:
            return False, f"版本 {version_hash} 不存在"

        self.create_snapshot("回退前自动保存")

        result = self._run_git("read-tree", "-u", "--reset", version_hash)
        if result.returncode != 0:
            return False, f"回退失败: {result.stderr}"

        self._run_git("add", "-A")
        self._run_git("commit", "-m", f"windcode: 回退到版本 {version_hash}")
        return True, f"已回退到版本 {version_hash}"

    def get_diff(self, version_hash: str) -> str:
        if not self.is_initialized:
            return "版本管理未初始化"

        result = self._run_git("diff", "HEAD", version_hash)
        if result.returncode != 0:
            return f"获取差异失败: {result.stderr}"
        return result.stdout if result.stdout else "无差异"

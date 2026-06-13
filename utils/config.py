import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".windcode"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "model": "deepseek-v4-flash",
    "models": [
        "deepseek-v4-flash",
        "deepseek-v4-pro",
    ],
}


class Config:
    API_KEY = os.environ.get("WindCode_API_KEY")
    BASE_URL = os.environ.get("WindCode_BASE_URL")
    TOOLS_JSON = Path(__file__).parent.parent / "tools" / "tools.json"
    COMMAND_PATH = Path.cwd() / "WIND.md"

    _config = None
    MODEL = None
    MODELS = []

    @classmethod
    def init(cls, cli_model=None):
        cls._config = dict(DEFAULT_CONFIG)
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cls._config.update(json.load(f))
            except Exception:
                pass
        env_model = os.environ.get("WindCode_MODEL")
        if env_model:
            cls._config["model"] = env_model
        if cli_model:
            cls._config["model"] = cli_model
        cls.MODEL = cls._config["model"]
        cls.MODELS = cls._config.get("models", DEFAULT_CONFIG["models"])

    @classmethod
    def switch_model(cls, model: str):
        cls.MODEL = model
        cls._config["model"] = model
        cls._save()
        return cls.MODEL

    @classmethod
    def _save(cls):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cls._config, f, indent=2, ensure_ascii=False)


class Prompt:
    MAIN_PROMPT = Path(__file__).parent / "prompt" / "main.md"

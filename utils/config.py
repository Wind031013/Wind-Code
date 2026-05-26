import os
from pathlib import Path
class Config:
    API_KEY = os.environ.get("WindCode_API_KEY")
    BASE_URL = os.environ.get("WindCode_BASE_URL")
    MODEL = "deepseek-v4-flash"
    TOOLS_JSON = Path(__file__).parent.parent / "tools" / "tools.json"

class Prompt:
    MAIN_PROMPT = Path(__file__).parent / "prompt" / "main.md"

if __name__ == "__main__":
    print(Prompt.MAIN_PROMPT)

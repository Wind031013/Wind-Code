from openai import OpenAI
from utils.logger import setup_logger
from utils.config import Config, Prompt
import json

logger = setup_logger()


class ConfigError(Exception):
    pass


def call_model(client: OpenAI, messages):
    """调用模型"""
    try:
        response = client.chat.completions.create(
            model=Config.MODEL,
            messages=messages,
            tools=load_tools_menu(),
            timeout=60,
        )
        return response.choices[0].message
    except Exception as e:
        logger.error(e)
        return None


def load_tools_menu():
    """加载工具菜单"""
    with open(Config.TOOLS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def load_main_prompt():
    """加载主提示词"""
    with open(Prompt.MAIN_PROMPT, "r", encoding="utf-8") as f:
        return f.read()


def load_api_config():
    """加载API配置"""
    api_key = Config.API_KEY
    base_url = Config.BASE_URL
    if api_key is None or base_url is None:
        logger.error("请配置API_KEY和BASE_URL")
        raise ConfigError("未配置API_KEY或者BASE_URL")
    else:
        return api_key, base_url

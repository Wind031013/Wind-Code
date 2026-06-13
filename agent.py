from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
from utils.logger import setup_logger
from utils.model import call_model, load_api_config
from utils.use_tools import UseTools
from utils.messages_manager import MessagesManager
from utils.exceptions import ToolArgumentParseError, UnknownToolTypeError
import json

logger = setup_logger(__name__)


class WindCode:
    def __init__(self):
        api_key, base_url = load_api_config()
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.use_tools = UseTools()
        self.messages_manager = MessagesManager(20)

    def run(self, user_input: str):
        self.messages_manager.add_user_message(user_input)
        while True:
            self.messages_manager.short_term()
            message: ChatCompletionMessage = call_model(
                self.client, self.messages_manager.messages
            )
            if message is None:
                logger.error("模型调用失败，终止对话")
                break
            else:
                self.messages_manager.add_message(message)

            if not message.tool_calls:
                if message.content:
                    print(message.content)
                break
            for tool_call in message.tool_calls:
                try:
                    if tool_call.type != "function":
                        raise UnknownToolTypeError(tool_call.type, tool_call.id)
                    kwargs = json.loads(tool_call.function.arguments)
                    result = self.use_tools.execute_tool(
                        tool_call.function.name, kwargs
                    )
                    tool_content = str(result)
                except UnknownToolTypeError as e:
                    logger.warning(f"未知的工具调用类型：{tool_call.type}")
                    tool_content = f"Error: {e}"
                except json.JSONDecodeError as e:
                    ex = ToolArgumentParseError(
                        tool_call.function.arguments, tool_call.id, e
                    )
                    logger.warning(str(ex))
                    tool_content = f"Error: {e}"
                except Exception as e:
                    logger.error(f"工具调用意外错误: {e}")
                    tool_content = f"Error: 工具执行异常 - {e}"
                self.messages_manager.add_tool_message(tool_call.id, tool_content)

from utils.model import load_main_prompt
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageFunctionToolCall
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MessagesManager:
    def __init__(self, short_term_size: int):
        self.short_term_size = short_term_size
        self.command_path = Config.COMMAND_PATH
        self.messages = self.init_messages()

    def init_messages(self):
        main_prompt = load_main_prompt()
        self.command_messages = ""
        if self.command_path.exists():
            try:
                self.command_messages = self.command_path.read_text(encoding="utf-8")
                logger.debug("指令记忆加载成功")
            except Exception as e:
                logger.error(f"指令记忆读取错误：{e}")
        system_prompt = main_prompt + self.command_messages
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        return messages
    def add_user_message(self, user_input):
        self.messages.append({"role": "user", "content": user_input})

    def add_message(self, message: ChatCompletionMessage):
        tool_calls_data = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in (message.tool_calls or [])
        ]
        new_content = {"role": "assistant", "content": message.content or ""}
        reasoning = getattr(message, "reasoning_content", None)
        if reasoning:
            new_content["reasoning_content"] = reasoning
        if tool_calls_data:
            new_content["tool_calls"] = tool_calls_data
        self.messages.append(new_content)

    def short_term(self):
        chat_messages = [msg for msg in self.messages if msg["role"] != "system"]
        remove_count = len(chat_messages) - self.short_term_size
        if remove_count > 0:
            self.messages = self.messages[:1] + chat_messages[remove_count:]
            
    def add_tool_message(self, tool_call_id:str, content: str):
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })

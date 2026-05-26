from utils.model import load_main_prompt
from openai.types.chat import ChatCompletionMessage


class MessagesManager:
    def __init__(self, short_term_size: int):
        self.short_term_size = short_term_size
        self.messages = self.init_messages()
        pass

    def init_messages(self):
        messages = [
            {"role": "system", "content": load_main_prompt()},
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

    def short_term(self, messages: list[dict]):
        system_messages = [msg for msg in messages if msg["role"] == "system"]
        chat_messages = [msg for msg in messages if msg["role"] != "system"]
        remove_count = len(chat_messages) - self.short_term_size
        if remove_count > 0:
            chat_messages = chat_messages[remove_count:]
        return system_messages + chat_messages

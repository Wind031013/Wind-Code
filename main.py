from openai import OpenAI
import os
import json
from OSTools import read_file, write_file, get_file_path


class Config:
    API_KEY = os.environ.get("ZHI_PU_API_KEY")
    BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
    MODEL = "glm-4"


class CliAgent:

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL,
        )

        self.tools = self.load_tools("tools.json")
        self.func_map = {
            "get_file_path": get_file_path,
            "read_file": read_file,
            "write_file": write_file,
        }

    def load_tools(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def call_model(self, messages):
        try:
            print(f"发送消息到模型，消息数量: {len(messages)}")
            response = self.client.chat.completions.create(
                model=Config.MODEL,
                messages=messages,
                tools=self.tools,
                timeout=60,  # 设置60秒超时
            )
            return response
        except Exception as e:
            print(f"调用模型失败: {e}")
            raise

    def run(self, user_input):
        print(f"用户输入: {user_input}")
        messages = [
            {
                "role": "system",
                "content": "你是一个可以操作文件的AI助手。"
            },
            {
                "role": "user",
                "content": user_input
            },
        ]

        while True:
            response = self.call_model(messages)
            msg = response.choices[0].message
            messages.append(msg)
            if not msg.tool_calls:
                print(msg.content)
                break

            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                try:
                    arg = json.loads(tool_call.function.arguments)
                    print(f"执行函数: {func_name}, 参数: {arg}")

                    if func_name in self.func_map:
                        result = self.func_map[func_name](**arg)
                    else:
                        result = f"工具不存在: {func_name}"
                except Exception as e:
                    result = f"执行函数异常: {e}"

                messages.append(response.choices[0].message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })


if __name__ == "__main__":
    agent = CliAgent()
    while True:
        user_input = input("请输入: ")
        if user_input == "exit":
            print("byebye")
            break
        agent.run(user_input)

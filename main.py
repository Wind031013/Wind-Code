from Tools.OSTools import read_file, write_file, get_file_path
from pathlib import Path
from openai import OpenAI
import tiktoken
import json
import os

from utils.logger import setup_logger

class Config:
    API_KEY = os.environ.get("ZHI_PU_API_KEY")
    BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
    LOG_DIR = Path("./logs")
    MODEL = "glm-4"
    _logger = None

logger = setup_logger(__name__, Config.LOG_DIR)
    
class CliAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL,
        )
        logger.debug("OpenAI 客户端创建成功")
        
        # Token 计算
        try:
            self.encoding = tiktoken.encoding_for_model(Config.MODEL)
            logger.debug("分词器初始化成功...")
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")
            logger.debug(f"未找到模型: {Config.MODEL}的分词器，使用 cl100k_base")

        self.func_map = {
            "get_file_path": get_file_path,
            "read_file": read_file,
            "write_file": write_file,
        }
        
        # 初始化对话历史
        self.messages = [
            {
                "role": "system",
                "content": "你是一个可以操作文件的AI助手。"
            }
        ]
        self.tools = self.load_tools("tools.json")

    def count_tokens(self, text):
        return len(self.encoding.encode(text))
    
    def count_messages_tokens(self, messages):
        """计算所有消息的总token数"""
        total_tokens = 0
        for msg in messages:
            # 处理不同类型的消息对象
            if isinstance(msg, dict):
                # 字典类型的消息（用户手动创建的）
                role = msg["role"]
                content = msg["content"]
            else:
                # ChatCompletionMessage 对象（API返回的）
                role = msg.role
                content = msg.content if msg.content else ""
            
            # 计算角色和内容的token
            total_tokens += len(self.encoding.encode(role))
            total_tokens += len(self.encoding.encode(content))
        return total_tokens

    def load_tools(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def call_model(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=Config.MODEL,
                messages=messages,
                tools=self.tools,
                timeout=60,  # 设置60秒超时
            )
            return response
        except Exception as e:
            logger.error(f"调用模型失败: {e}")
            raise

    def run(self, user_input):
        
        # 添加用户消息到对话历史
        self.messages.append({
            "role": "user",
            "content": user_input
        })

        while True:
            # 计算输入token数（发送前的消息总token）
            input_token_count = self.count_messages_tokens(self.messages)
            
            # 发送请求
            response = self.call_model(self.messages)
            # 读取响应
            msg = response.choices[0].message
            
            print(f"输入token: {input_token_count}")
            
            output_token_count = self.count_tokens(msg.content)
            print(f"输出token: {output_token_count}")
            
            self.messages.append(msg)
            if not msg.tool_calls:
                print(msg.content)
                break
            # 获取工具调用
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

                self.messages.append(response.choices[0].message)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })


if __name__ == "__main__":
    exit = ["exit", "quit", "e", "E"]
    agent = CliAgent()
    logger.debug("CliAgent 启动成功...")
    while True:
        user_input = input("请输入: ")
        if user_input in exit:
            print("byebye")
            break
        agent.run(user_input)

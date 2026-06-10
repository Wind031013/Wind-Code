import json
from utils.logger import setup_logger
from tools.base import BaseTool, RiskLevel, ToolResult
logger = setup_logger(__name__)

class WindRouter(BaseTool):
    name="wind_router"
    description="当遇到的任务有不清楚的地方，需要向用户确认细节征求用户意见时，向用户提出问题并获取用户的选择或输入，支持一次提出多个问题，批量收集用户回答"
    risk_level=RiskLevel.SAFE

    def _ask(self, question: str, options: str):
        print(f"\n{question}")
        option_list = []
        if options:
            option_list = [o.strip() for o in options.split("|") if o.strip()]
        if option_list:
            for i, opt in enumerate(option_list, 1):
                print(f"\t[{i}]{opt}")
            print("\t[0] 自行输入")
        
        while True:
            choice = input("请选择(编号或者自定义内容)：").strip()
            if not choice:
                continue
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(option_list):
                    return option_list[idx - 1]
                elif idx == 0:
                    break
                else:
                    print(f"  无效编号，请输入 0-{len(option_list)}")
                    continue
            else:
                return choice
        while True:
            user_input = input("请输入自定义内容：").strip()
            if user_input:
                return user_input
            print("输入不能为空")
    def execute(self, questions_json: str="", **kwargs):
        if not questions_json:
            return ToolResult("Error: questions_json为空", success=False)
        
        try:
            questions = json.loads(questions_json)
        except json.JSONDecodeError as e:
            return ToolResult(f"Error: questions_json格式错误 - {e}", success=False)
        
        if not isinstance(questions, list) or len(questions) == 0:
            return ToolResult("Error: questions_json 必须是非空数组", success=False)
        
        for i, q in enumerate(questions):
            if not isinstance(q, dict) or "question" not in q:
                return ToolResult(
                    f"Error: 第 {i + 1} 项缺少 'question' 字段", success=False
                )
        total = len(questions)
        print(f"\n{'=' * 60}")
        print(f"需要你的意见 (共 {total} 个问题):")
        print(f"{'=' * 60}")
        answer_list = []
        for i, q in enumerate(questions, 1):
            question_text = q["question"]
            options_text = q.get("options", "")
            print(f"\n  ── 问题 {i}/{total} ──")
            answer = self._ask(question_text, options_text)
            answer_list.append(f"Q{i}:{question_text}\nA{i}:{answer}")
        result = "\n\n".join(answer_list)

        return ToolResult(result)

        



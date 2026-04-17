import json
from agent.tools.base import BaseTool, ToolResult, RiskLevel
from agent.utils.logger import setup_logger

logger = setup_logger(__name__)


class WindRouterTool(BaseTool):
    name = "wind_router"
    description = "当遇到复杂任务且有不清楚的地方需要征求用户意见时，向用户提出问题并获取用户的选择或输入。支持一次提出多个问题，批量收集用户回答"
    risk_level = RiskLevel.SAFE

    def _ask_single(self, question: str, options: str = "") -> str:
        print(f"\n  ❓ {question}")

        option_list = []
        if options:
            option_list = [o.strip() for o in options.split("|") if o.strip()]

        if option_list:
            for i, opt in enumerate(option_list, 1):
                print(f"     [{i}] {opt}")
            print(f"     [0] 自行输入")

            while True:
                choice = input("  请选择 (编号或自定义): ").strip()
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
            user_input = input("  请输入: ").strip()
            if user_input:
                return user_input
            print("  输入不能为空，请重新输入")

    def execute(self, questions_json: str = "", **kwargs) -> ToolResult:
        if not questions_json:
            return ToolResult("Error: questions_json is empty", success=False)

        try:
            questions = json.loads(questions_json)
        except json.JSONDecodeError as e:
            return ToolResult(f"Error: questions_json 格式无效 - {e}", success=False)

        if not isinstance(questions, list) or len(questions) == 0:
            return ToolResult("Error: questions_json 必须是非空数组", success=False)

        for i, q in enumerate(questions):
            if not isinstance(q, dict) or "question" not in q:
                return ToolResult(
                    f"Error: 第 {i + 1} 项缺少 'question' 字段", success=False
                )

        total = len(questions)
        print(f"\n{'=' * 60}")
        print(f"🤔 助手需要你的意见 (共 {total} 个问题):")
        print(f"{'=' * 60}")

        answers = []
        for i, q in enumerate(questions, 1):
            question_text = q["question"]
            options_text = q.get("options", "")

            print(f"\n  ── 问题 {i}/{total} ──")
            answer = self._ask_single(question_text, options_text)
            print(f"  ✅ 回答: {answer}")
            answers.append({"question": question_text, "answer": answer})

        result_parts = []
        for i, a in enumerate(answers, 1):
            result_parts.append(f"Q{i}: {a['question']}\nA{i}: {a['answer']}")
        result = "\n".join(result_parts)

        print(f"\n{'=' * 60}")
        print(f"📋 所有回答已收集完毕")
        print(f"{'=' * 60}")

        return ToolResult(result)

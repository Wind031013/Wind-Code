import argparse
from pathlib import Path

from agent import WindCode
from utils.config import Config


def main():
    parser = argparse.ArgumentParser(
        prog="wind",
        description="智能 Agent 编程协作工具",
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="要执行的查询/任务",
    )
    parser.add_argument(
        "-w", "--workdir",
        type=Path,
        default=Path.cwd(),
        help="工作目录",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help="指定使用的模型",
    )
    args = parser.parse_args()

    Config.init(cli_model=args.model)

    print("WindCode 智能 Agent 编程协作工具")
    print(f"当前模型: {Config.MODEL}")

    if args.query:
        agent = WindCode()
        user_input = " ".join(args.query)
        agent.run(user_input)
    else:
        agent = WindCode()
        while True:
            try:
                user_input = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break
            if not user_input:
                continue
            if user_input.lower() in ("/quit", "/exit"):
                print("再见！")
                break
            if user_input.startswith("/model"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print(f"当前模型: {Config.MODEL}")
                    print(f"可用模型: {', '.join(Config.MODELS)}")
                    print("用法: /model <模型名称>")
                else:
                    new_model = parts[1].strip()
                    if new_model in Config.MODELS:
                        Config.switch_model(new_model)
                        print(f"已切换到模型: {Config.MODEL}")
                    else:
                        Config.MODELS.append(new_model)
                        Config.switch_model(new_model)
                        print(f"已添加并切换到模型: {Config.MODEL}")
                continue
            agent.run(user_input)


if __name__ == "__main__":
    main()

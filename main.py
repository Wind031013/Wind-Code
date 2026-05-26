import argparse
from pathlib import Path

from agent import WindCode

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
    args = parser.parse_args()

    agent = WindCode()

    if args.query:
        user_input = " ".join(args.query)
        agent.run(user_input)
    else:
        print("WindCode 智能 Agent 编程协作工具")
        print("输入 '/quit' 或 '/exit' 退出\n")
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
            agent.run(user_input)

if __name__ == "__main__":
    main()
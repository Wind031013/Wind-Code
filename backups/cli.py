import argparse
from agent.agent import CliAgent


def main():
    parser = argparse.ArgumentParser(
        prog="wind",
        description="Wind Code - 智能 Agent 编程协作工具",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="直接传入指令，不填则进入交互模式",
    )
    args = parser.parse_args()

    agent = CliAgent()

    if args.prompt:
        user_input = " ".join(args.prompt)
        agent.run(user_input)
        return

    exit_words = ["exit", "quit", "e", "E"]
    print("🌬️ Wind Code - 输入指令开始，输入 exit 退出")

    while True:
        try:
            user_input = input("\n请输入: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nbyebye")
            break

        if not user_input:
            continue
        if user_input in exit_words:
            print("byebye")
            break

        try:
            agent.run(user_input)
        except Exception as e:
            print(f"运行出错: {e}")


if __name__ == "__main__":
    main()

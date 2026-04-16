import argparse
from agent.agent import CliAgent


def _handle_version_commands(user_input: str, agent: CliAgent) -> bool:
    vm = agent.version_manager
    parts = user_input.strip().split(maxsplit=1)
    cmd = parts[0]
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/versions" or cmd == "/v":
        if not vm.available:
            print("⚠️  Git 不可用，版本管理已禁用")
            return True
        versions = vm.list_versions()
        if not versions:
            print("暂无版本记录")
            return True
        print("\n📜 版本记录:")
        print("-" * 60)
        for v in versions:
            print(f"  [{v['hash']}] {v['date']}")
            print(f"       {v['message']}")
        print("-" * 60)
        print(f"共 {len(versions)} 条记录")
        return True

    if cmd == "/rollback" or cmd == "/rb":
        if not vm.available:
            print("⚠️  Git 不可用，版本管理已禁用")
            return True
        if not arg:
            versions = vm.list_versions()
            if not versions:
                print("暂无版本记录，无法回退")
                return True
            print("\n📜 可回退的版本:")
            print("-" * 60)
            for i, v in enumerate(versions, 1):
                print(f"  {i}. [{v['hash']}] {v['date']}")
                print(f"       {v['message']}")
            print("-" * 60)
            try:
                choice = input("请输入序号或者对应哈希值进行回退 (q取消): ").strip()
            except (KeyboardInterrupt, EOFError):
                print("已取消")
                return True
            if choice.lower() == "q":
                print("已取消")
                return True
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(versions):
                    arg = versions[idx]["hash"]
                else:
                    print("无效序号")
                    return True
            else:
                arg = choice

        confirm = (
            input(f"⚠️  确认回退到版本 {arg}？此操作将恢复文件到该版本状态 [y/N]: ")
            .strip()
            .lower()
        )
        if confirm != "y":
            print("已取消回退")
            return True
        ok, msg = vm.rollback(arg)
        print(f"{'✅' if ok else '❌'} {msg}")
        return True

    if cmd == "/diff":
        if not vm.available:
            print("⚠️  Git 不可用，版本管理已禁用")
            return True
        if not arg:
            print("用法: /diff <版本哈希>")
            return True
        diff = vm.get_diff(arg)
        if diff == "无差异":
            print("当前工作区与指定版本无差异")
        else:
            print(f"\n📄 与版本 {arg} 的差异:")
            print("-" * 60)
            print(diff)
        return True

    return False


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
    # print("版本管理: /versions 查看历史  /rollback 回退")

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

        if user_input.startswith("/"):
            if _handle_version_commands(user_input, agent):
                continue

        try:
            agent.run(user_input)
        except Exception as e:
            print(f"运行出错: {e}")


if __name__ == "__main__":
    main()

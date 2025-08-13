from .llm import complete

WELCOME = "CodeCompanion chat – type /exit to quit. Use /provider <name> to switch provider (claude, gpt4, gemini)."


def chat_repl(provider: str):
    print(WELCOME)
    history = []
    cur_provider = provider
    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if line in ("/exit", "/quit"):
            return 0
        if line.startswith("/provider "):
            cur_provider = line.split(" ", 1)[1].strip() or cur_provider
            print(f"[set provider] {cur_provider}")
            continue
        # call LLM
        try:
            msg = complete(
                "You are CodeCompanion, a helpful coding assistant with strong tooling knowledge.",
                history + [{"role": "user", "content": line}],
                provider=cur_provider,
            )
            content = msg.get("content", "")
            print(content)
            history.append({"role": "user", "content": line})
            history.append({"role": "assistant", "content": content})
        except Exception as e:
            print(f"Error: {e}")

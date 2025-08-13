from .llm import complete


def chat_repl(provider):
    print("CodeCompanion Chat - type /exit to quit")
    history = []

    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if line in ("/exit", "/quit"):
            return 0

        try:
            msg = complete(
                "You are CodeCompanion, a helpful coding assistant.",
                history + [{"role": "user", "content": line}],
                provider=provider,
            )
            content = msg.get("content", "")
            print(content)
            history.append({"role": "user", "content": line})
            history.append({"role": "assistant", "content": content})
        except Exception as e:
            print(f"Error: {e}")

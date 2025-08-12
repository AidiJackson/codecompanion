import sys
from .llm import complete

WELCOME = "CodeCompanion chat – type /exit to quit. Use /model <id> to switch model."

def chat_repl(model: str):
    print(WELCOME)
    history = []
    cur_model = model
    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); return 0
        if line in ("/exit", "/quit"):
            return 0
        if line.startswith("/model "):
            cur_model = line.split(" ",1)[1].strip() or cur_model
            print(f"[set model] {cur_model}"); continue
        # call LLM
        msg = complete(
            "You are CodeCompanion, a helpful coding assistant with strong tooling knowledge.",
            history + [{"role":"user","content":line}],
            model=cur_model
        )
        content = msg.get("content","")
        print(content)
        history.append({"role":"user","content":line})
        history.append({"role":"assistant","content":content})
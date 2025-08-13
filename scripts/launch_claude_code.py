import os
import sys
import subprocess
import threading

BOOT = open(".cc/bootstrap.txt", "r", encoding="utf-8").read()

env = os.environ.copy()
env.setdefault("CC_AGENT_PACK", ".cc/agent_pack.json")
env.setdefault("CC_MODE", "orchestrated")
env.setdefault("AI_PROVIDER", os.getenv("AI_PROVIDER", "openrouter"))

p = subprocess.Popen(
    ["claude-code"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    env=env,
)


def pump_out():
    for line in p.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()


t = threading.Thread(target=pump_out, daemon=True)
t.start()

p.stdin.write(BOOT + "\n")
p.stdin.flush()

try:
    for line in sys.stdin:
        p.stdin.write(line)
        p.stdin.flush()
except KeyboardInterrupt:
    pass

p.stdin.close()
p.wait()

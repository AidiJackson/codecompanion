import os
import sys
import json
import pathlib
import urllib.request
import urllib.error
import time

API_URL = "https://code-companion-aidanjackson86.replit.app"
TOKEN = os.getenv("CODECOMPANION_TOKEN") or "sullykevjackson050522"


def _slug(s):
    import re

    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or f"task-{int(time.time())}"


def _save(goal, data):
    out = pathlib.Path("cc_artifacts") / f"{_slug(goal)}-{int(time.time())}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "response.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    for a in data.get("artifacts") or []:
        name = {
            "SpecDoc": "SPEC.md",
            "CodePatch": "PATCH.diff",
            "TestPlan": "TESTPLAN.md",
            "DesignDoc": "DESIGN.md",
            "EvalReport": "EVAL.md",
        }.get(a.get("type", "Artifact"), f"{a.get('type', 'Artifact')}.md")
        (out / name).write_text(a.get("content", ""), encoding="utf-8")
    return out


def _post(path, body):
    req = urllib.request.Request(
        f"{API_URL}{path}",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    if len(sys.argv) < 2:
        print('Usage: ./codecompanion/ccmd "Your task"')
        sys.exit(1)
    goal = " ".join(sys.argv[1:]).strip()
    try:
        data = _post("/run_real", {"objective": goal})
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}\n{e.read().decode('utf-8', 'ignore')[:800]}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Network error: {e}")
        sys.exit(1)
    out = _save(goal, data)
    print(json.dumps(data, indent=2)[:4000])
    print(f"\n💾 Saved artifacts to {out}")
    if (out / "PATCH.diff").exists():
        print(f"👉 Apply with: git apply --whitespace=fix {out / 'PATCH.diff'}")


if __name__ == "__main__":
    main()

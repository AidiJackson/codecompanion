from importlib.resources import files
import os
import shutil
import json

DEFAULT_PKG = "codecompanion.defaults"

AGENT_FILES = [
    "orchestrator.md",
    "installer.md",
    "env_doctor.md",
    "analyzer.md",
    "dep_auditor.md",
    "bug_triage.md",
    "fixer.md",
    "test_runner.md",
    "web_doctor.md",
    "pr_preparer.md",
]

STUB_TEXT = """# <AGENT_NAME> (stub)
This is a placeholder for your ClaudeCode agent prompt.
Paste the full prompt you use for <AGENT_NAME> here so CodeCompanion runs with your custom agents by default.
"""


def ensure_bootstrap(project_root: str = ".") -> dict:
    """
    Ensure .cc/bootstrap.txt and .cc/agent_pack.json exist (copied from package defaults if missing).
    Ensure .cc/agents/ exists and contains stub files for the 10 agents if missing.
    Returns details about created items.
    """
    created = []
    cc_dir = os.path.join(project_root, ".cc")
    os.makedirs(cc_dir, exist_ok=True)

    # Copy defaults (no overwrite)
    for fname in ("bootstrap.txt", "agent_pack.json"):
        dest = os.path.join(cc_dir, fname)
        if not os.path.exists(dest):
            src = files(DEFAULT_PKG).joinpath(fname)
            shutil.copy(src, dest)
            created.append(dest)

    # Ensure settings.json exists with fail_path configuration
    settings_file = os.path.join(cc_dir, "settings.json")
    if not os.path.exists(settings_file):
        default_settings = {
            "version": "1.0.0",
            "fail_path": {
                "max_attempts": 2,
                "backoff_seconds": 0.0,
                "fallback_enabled": False,
                "strict_validation": False,
            },
        }
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(default_settings, f, indent=2, ensure_ascii=False)
        created.append(settings_file)

    # Ensure .cc/agents stubs exist (do not overwrite if already present)
    agents_dir = os.path.join(cc_dir, "agents")
    os.makedirs(agents_dir, exist_ok=True)
    for af in AGENT_FILES:
        dest = os.path.join(agents_dir, af)
        if not os.path.exists(dest):
            name = af.replace(".md", "").replace("_", " ").title()
            with open(dest, "w", encoding="utf-8") as f:
                f.write(STUB_TEXT.replace("<AGENT_NAME>", name))
            created.append(dest)

    return {"created": created, "dir": cc_dir, "agents_dir": agents_dir}

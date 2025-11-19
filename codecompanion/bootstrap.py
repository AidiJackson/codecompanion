from importlib.resources import files
import os
import shutil
from typing import Union, Optional
from pathlib import Path
from .target import TargetContext

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


def ensure_bootstrap(target: Optional[Union[TargetContext, str, Path]] = None) -> dict:
    """
    Ensure .cc/bootstrap.txt and .cc/agent_pack.json exist (copied from package defaults if missing).
    Ensure .cc/agents/ exists and contains stub files for the 10 agents if missing.

    Args:
        target: TargetContext, path string, or None (uses cwd)

    Returns:
        dict with 'created', 'dir', 'agents_dir' keys
    """
    # Convert to TargetContext if needed
    if target is None:
        target = TargetContext(os.getcwd())
    elif isinstance(target, (str, Path)):
        target = TargetContext(target)
    elif not isinstance(target, TargetContext):
        raise TypeError(f"target must be TargetContext, str, Path, or None, got {type(target)}")

    created = []

    # Ensure .cc directory exists
    target.mkdir(".cc")
    cc_dir = target.cc_dir

    # Copy defaults (no overwrite)
    for fname in ("bootstrap.txt", "agent_pack.json"):
        dest_rel = f".cc/{fname}"
        if not target.file_exists(dest_rel):
            src = files(DEFAULT_PKG).joinpath(fname)
            # Read from package resources and write to target
            content = src.read_text(encoding='utf-8')
            target.write_file(dest_rel, content)
            created.append(str(cc_dir / fname))

    # Ensure .cc/agents stubs exist (do not overwrite if already present)
    target.mkdir(".cc/agents")
    agents_dir = target.agents_dir

    for af in AGENT_FILES:
        dest_rel = f".cc/agents/{af}"
        if not target.file_exists(dest_rel):
            name = af.replace(".md", "").replace("_", " ").title()
            content = STUB_TEXT.replace("<AGENT_NAME>", name)
            target.write_file(dest_rel, content)
            created.append(str(agents_dir / af))

    return {
        "created": created,
        "dir": str(cc_dir),
        "agents_dir": str(agents_dir),
        "target": target
    }

from pathlib import Path

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


def ensure_bootstrap(project_root="."):
    created = []
    cc_dir = Path(project_root) / ".cc"
    cc_dir.mkdir(exist_ok=True)

    # Create bootstrap.txt
    bootstrap_file = cc_dir / "bootstrap.txt"
    if not bootstrap_file.exists():
        bootstrap_file.write_text("CodeCompanion agents ready for use.")
        created.append(str(bootstrap_file))

    # Create agents directory
    agents_dir = cc_dir / "agents"
    agents_dir.mkdir(exist_ok=True)

    for agent_file in AGENT_FILES:
        agent_path = agents_dir / agent_file
        if not agent_path.exists():
            name = agent_file.replace(".md", "").replace("_", " ").title()
            agent_path.write_text(
                f"# {name} Agent\n\nReady for CodeCompanion workflow."
            )
            created.append(str(agent_path))

    return {"created": created, "dir": str(cc_dir), "agents_dir": str(agents_dir)}

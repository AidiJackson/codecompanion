"""
Advanced system introspection panel for CodeCompanion.

Provides a read-only, computed dashboard of project state, agent status,
model policy, and system health.
"""

import os
import json
from pathlib import Path
from datetime import datetime


def show_info_command(args) -> int:
    """
    Print an advanced introspection panel for the current CodeCompanion project.

    Args:
        args: Parsed command-line arguments (should have 'raw' attribute)

    Returns:
        0 on success
    """
    # Gather all data
    data = gather_info_data()

    # Output format
    if getattr(args, 'raw', False):
        print_raw_json(data)
    else:
        print_text_panel(data)

    return 0


def gather_info_data() -> dict:
    """Gather all introspection data into a structured dict."""
    project_root = Path.cwd()
    cc_dir = project_root / ".cc"

    # Import here to avoid circular dependencies
    from codecompanion.runner import AGENT_WORKFLOW
    from codecompanion.llm import PROVIDERS
    from codecompanion import __version__

    # Section 1: Project / Bootstrap
    bootstrap_info = {
        "project_root": str(project_root),
        "cc_dir_exists": cc_dir.exists(),
        "bootstrap_txt_exists": (cc_dir / "bootstrap.txt").exists() if cc_dir.exists() else False,
        "agent_pack_json_exists": (cc_dir / "agent_pack.json").exists() if cc_dir.exists() else False,
        "agents_dir_exists": (cc_dir / "agents").exists() if cc_dir.exists() else False,
        "status": "INITIALISED" if cc_dir.exists() else "UNINITIALISED",
        "version": __version__,
    }

    # Section 2: Agent files
    agent_files = []
    if bootstrap_info["agents_dir_exists"]:
        agents_dir = cc_dir / "agents"
        agent_files = sorted([f.name for f in agents_dir.glob("*.md")])

    # Section 3: Model Policy (from AGENT_WORKFLOW)
    agent_workflow = []
    for agent_cfg in AGENT_WORKFLOW:
        agent_workflow.append({
            "name": agent_cfg["name"],
            "provider": agent_cfg["provider"] or "none",
        })

    # Section 4: Provider configurations
    providers = {}
    for name, cfg in PROVIDERS.items():
        env_var = cfg["api_key_env"]
        providers[name] = {
            "model": cfg["model"],
            "api_key_set": os.getenv(env_var) is not None,
            "api_key_env": env_var,
            "base_url": cfg["base_url"],
        }

    # Section 5: Pipeline status (check for logs or state)
    pipeline_status = {
        "last_run": None,
        "logs_exist": (cc_dir / "logs").exists() if cc_dir.exists() else False,
    }

    if pipeline_status["logs_exist"]:
        logs_dir = cc_dir / "logs"
        log_files = list(logs_dir.glob("*.log"))
        if log_files:
            # Get most recent log file
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            pipeline_status["last_run"] = datetime.fromtimestamp(
                latest_log.stat().st_mtime
            ).isoformat()

    # Section 6: Fail-path & Self-Repair (not yet implemented)
    fail_path = {
        "implemented": False,
        "note": "Fail-path and self-repair features are planned for future releases",
    }

    # Section 7: Errors & Recovery (not yet implemented)
    errors = {
        "implemented": False,
        "note": "Error tracking and recovery features are planned for future releases",
    }

    # Section 8: Recommendations
    recommendations = generate_recommendations(
        bootstrap_info, providers, agent_workflow, agent_files
    )

    return {
        "bootstrap": bootstrap_info,
        "agent_files": agent_files,
        "agent_workflow": agent_workflow,
        "providers": providers,
        "pipeline_status": pipeline_status,
        "fail_path": fail_path,
        "errors": errors,
        "recommendations": recommendations,
    }


def generate_recommendations(bootstrap_info, providers, agent_workflow, agent_files) -> list:
    """Generate recommendations based on current state."""
    recs = []

    # Check if project is initialized
    if not bootstrap_info["cc_dir_exists"]:
        recs.append({
            "priority": "high",
            "message": "Project not initialized. Run 'codecompanion --check' to initialize.",
        })

    # Check if any API keys are configured
    any_key_set = any(p["api_key_set"] for p in providers.values())
    if not any_key_set:
        recs.append({
            "priority": "medium",
            "message": "No API keys configured. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY to enable LLM features.",
        })

    # Check agent files vs workflow
    expected_agents = {a["name"].lower() for a in agent_workflow}
    actual_agents = {f.replace(".md", "").replace("_", "").lower() for f in agent_files}

    if bootstrap_info["agents_dir_exists"] and len(agent_files) == 0:
        recs.append({
            "priority": "low",
            "message": "No agent prompt files found. Agents will use default stubs.",
        })

    # General health check
    if bootstrap_info["status"] == "INITIALISED" and any_key_set:
        recs.append({
            "priority": "info",
            "message": "System appears healthy. Ready to run agents.",
        })

    return recs


def print_text_panel(data: dict) -> None:
    """Print formatted text panel."""
    print("=" * 70)
    print("CODECOMPANION SYSTEM INTROSPECTION PANEL")
    print("=" * 70)
    print()

    # Section 1: Project / Bootstrap
    print_section_header("PROJECT / BOOTSTRAP")
    bs = data["bootstrap"]
    print(f"Project root:        {bs['project_root']}")
    print(f"Version:             {bs['version']}")
    print(f".cc/ directory:      {'EXISTS' if bs['cc_dir_exists'] else 'NOT FOUND'}")
    if bs['cc_dir_exists']:
        print(f"  bootstrap.txt:     {'✓' if bs['bootstrap_txt_exists'] else '✗'}")
        print(f"  agent_pack.json:   {'✓' if bs['agent_pack_json_exists'] else '✗'}")
        print(f"  agents/:           {'✓' if bs['agents_dir_exists'] else '✗'}")
    print(f"Project Status:      {bs['status']}")
    print()

    # Section 2: Agent Files
    print_section_header("AGENT FILES")
    if data["agent_files"]:
        print(f"Found {len(data['agent_files'])} agent prompt files:")
        for af in data["agent_files"]:
            print(f"  - {af}")
    else:
        print("No custom agent prompt files found (using defaults)")
    print()

    # Section 3: Agent Workflow & Model Policy
    print_section_header("AGENT WORKFLOW & MODEL POLICY")
    print("Configured agent pipeline:")
    print()
    print(f"{'Agent':<20} {'Provider':<15} {'Model':<40}")
    print("-" * 70)
    for agent in data["agent_workflow"]:
        provider = agent["provider"]
        if provider == "none":
            model = "(no LLM needed)"
        elif provider in data["providers"]:
            model = data["providers"][provider]["model"]
        else:
            model = "(unknown)"
        print(f"{agent['name']:<20} {provider:<15} {model:<40}")
    print()

    # Section 4: Provider Configurations
    print_section_header("PROVIDER CONFIGURATIONS")
    for name, cfg in data["providers"].items():
        key_status = "✓ SET" if cfg["api_key_set"] else "✗ NOT SET"
        print(f"{name}:")
        print(f"  Model:       {cfg['model']}")
        print(f"  API Key:     {key_status} ({cfg['api_key_env']})")
        print(f"  Base URL:    {cfg['base_url'][:50]}...")
        print()

    # Section 5: Pipeline Status
    print_section_header("PIPELINE STATUS")
    ps = data["pipeline_status"]
    if ps["last_run"]:
        print(f"Last run:            {ps['last_run']}")
    else:
        print("Last run:            Never (no logs found)")
    print(f"Logs directory:      {'EXISTS' if ps['logs_exist'] else 'NOT FOUND'}")
    print()

    # Section 6: Fail-Path & Self-Repair
    print_section_header("FAIL-PATH & SELF-REPAIR")
    fp = data["fail_path"]
    if fp["implemented"]:
        print("Status:              CONFIGURED")
        # Future: print actual config
    else:
        print("Status:              NOT IMPLEMENTED")
        print(f"Note:                {fp['note']}")
    print()

    # Section 7: Errors & Recovery
    print_section_header("ERRORS & RECOVERY")
    err = data["errors"]
    if err["implemented"]:
        print("Status:              ACTIVE")
        # Future: print error stats
    else:
        print("Status:              NOT IMPLEMENTED")
        print(f"Note:                {err['note']}")
    print()

    # Section 8: Recommendations
    print_section_header("RECOMMENDATIONS")
    if data["recommendations"]:
        for i, rec in enumerate(data["recommendations"], 1):
            priority = rec["priority"].upper()
            print(f"{i}. [{priority}] {rec['message']}")
    else:
        print("No recommendations at this time.")
    print()

    print("=" * 70)


def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print(f"{title}")
    print("-" * 70)


def print_raw_json(data: dict) -> None:
    """Print data as JSON for machine consumption."""
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    # For testing
    class Args:
        raw = False

    show_info_command(Args())

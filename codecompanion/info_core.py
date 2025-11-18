"""
Core information gathering module for CodeCompanion dashboard.
Provides read-only system status, provider configs, and diagnostics.
"""
import os
import json
from pathlib import Path
from .bootstrap import ensure_bootstrap, AGENT_FILES
from .llm import PROVIDERS


def get_project_info(project_root: str = ".") -> dict:
    """Get project and bootstrap information."""
    bootstrap_info = ensure_bootstrap(project_root)
    cc_dir = Path(bootstrap_info["dir"])

    # Check if bootstrap files exist
    bootstrap_file = cc_dir / "bootstrap.txt"
    agent_pack_file = cc_dir / "agent_pack.json"

    status = "initialized" if bootstrap_file.exists() and agent_pack_file.exists() else "incomplete"

    return {
        "root": str(Path(project_root).resolve()),
        "cc_dir": str(cc_dir),
        "status": status,
        "bootstrap_file": str(bootstrap_file) if bootstrap_file.exists() else None,
        "agent_pack_file": str(agent_pack_file) if agent_pack_file.exists() else None,
    }


def get_agent_workflow_info(project_root: str = ".") -> dict:
    """Get agent workflow and agent pack information."""
    bootstrap_info = ensure_bootstrap(project_root)
    agents_dir = Path(bootstrap_info["agents_dir"])

    # Count how many agent files exist
    existing_agents = []
    missing_agents = []

    for agent_file in AGENT_FILES:
        agent_path = agents_dir / agent_file
        if agent_path.exists():
            # Check if it's still a stub
            content = agent_path.read_text()
            is_stub = "This is a placeholder" in content
            existing_agents.append({
                "name": agent_file.replace(".md", "").replace("_", " ").title(),
                "file": agent_file,
                "is_stub": is_stub,
            })
        else:
            missing_agents.append(agent_file)

    return {
        "agents_dir": str(agents_dir),
        "total_agents": len(AGENT_FILES),
        "existing_agents": existing_agents,
        "missing_agents": missing_agents,
        "completion": f"{len(existing_agents)}/{len(AGENT_FILES)}",
    }


def get_providers_info() -> list:
    """Get provider configurations and API key status."""
    providers_list = []

    for provider_name, config in PROVIDERS.items():
        api_key_env = config["api_key_env"]
        api_key_set = bool(os.getenv(api_key_env))

        providers_list.append({
            "name": provider_name,
            "model": config["model"],
            "api_key_env": api_key_env,
            "api_key_set": api_key_set,
            "base_url": config["base_url"],
        })

    return providers_list


def get_pipeline_status(project_root: str = ".") -> dict:
    """Get pipeline execution status (placeholder for now)."""
    # In a real implementation, this would check for pipeline run history
    # For now, return placeholder data
    return {
        "last_run": None,
        "status": "idle",
        "total_runs": 0,
        "success_rate": None,
    }


def get_errors_and_recovery(project_root: str = ".") -> list:
    """Get error history and recovery status (placeholder for now)."""
    # In a real implementation, this would read from error logs
    # For now, return empty list
    return []


def get_recommendations(project_root: str = ".") -> list:
    """Generate recommendations based on current state."""
    recommendations = []

    # Check provider API keys
    providers = get_providers_info()
    missing_keys = [p for p in providers if not p["api_key_set"]]

    if missing_keys:
        for provider in missing_keys:
            recommendations.append({
                "level": "warning",
                "message": f"Set {provider['api_key_env']} to use {provider['name']} provider",
                "action": f"export {provider['api_key_env']}=your-api-key",
            })

    # Check agent stubs
    workflow = get_agent_workflow_info(project_root)
    stub_agents = [a for a in workflow["existing_agents"] if a["is_stub"]]

    if stub_agents:
        recommendations.append({
            "level": "info",
            "message": f"{len(stub_agents)} agents are still using default stubs",
            "action": "Replace stubs in .cc/agents/ with your custom agent prompts",
        })

    return recommendations


def gather_all_info(project_root: str = ".") -> dict:
    """Gather all system information for dashboard display."""
    return {
        "bootstrap": get_project_info(project_root),
        "agent_workflow": get_agent_workflow_info(project_root),
        "providers": get_providers_info(),
        "pipeline": get_pipeline_status(project_root),
        "errors": get_errors_and_recovery(project_root),
        "recommendations": get_recommendations(project_root),
    }

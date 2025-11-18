from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from .bootstrap import ensure_bootstrap, AGENT_FILES
from .runner import AGENT_WORKFLOW
from .llm import PROVIDERS


@dataclass
class InfoSnapshot:
    """Structured snapshot of CodeCompanion system state for dashboards/CLI."""
    raw: Dict[str, Any]  # full JSON-ish payload used by --info --raw and /api/info


def gather_info_snapshot(project_root: str = ".") -> InfoSnapshot:
    """
    Collect and compute the same data currently printed by the info panel.

    Returns:
        InfoSnapshot with a `raw` dict containing:
          - bootstrap
          - agent_files / workflow
          - providers
          - pipeline_status
          - fail_path (can be stubbed if not implemented)
          - errors (can be stubbed if not implemented)
          - recommendations
    """
    # Bootstrap info
    bootstrap_info = ensure_bootstrap(project_root)
    cc_dir = os.path.join(project_root, ".cc")
    agents_dir = os.path.join(cc_dir, "agents")

    # Check which agent files exist
    agent_files_status = []
    for agent_file in AGENT_FILES:
        file_path = os.path.join(agents_dir, agent_file)
        exists = os.path.exists(file_path)
        size = os.path.getsize(file_path) if exists else 0
        agent_files_status.append({
            "name": agent_file,
            "path": file_path,
            "exists": exists,
            "size_bytes": size,
            "is_stub": size < 500 if exists else True,  # Heuristic: small files are likely stubs
        })

    # Agent workflow with model assignments
    agent_workflow = []
    for agent_config in AGENT_WORKFLOW:
        name = agent_config["name"]
        provider = agent_config.get("provider")
        model = None
        if provider and provider in PROVIDERS:
            model = PROVIDERS[provider].get("model")

        agent_workflow.append({
            "name": name,
            "provider": provider or "none",
            "model": model,
        })

    # Provider configurations and API key status
    providers_status = []
    for provider_name, config in PROVIDERS.items():
        api_key_env = config.get("api_key_env")
        api_key_set = bool(os.getenv(api_key_env)) if api_key_env else False
        providers_status.append({
            "name": provider_name,
            "api_key_env": api_key_env,
            "api_key_set": api_key_set,
            "model": config.get("model"),
            "base_url": config.get("base_url"),
        })

    # Pipeline status (stub for now)
    pipeline_status = {
        "last_run": None,
        "status": "not_run",
        "agents_completed": 0,
        "agents_failed": 0,
    }

    # Fail path (stub - would track failed runs and self-repair attempts)
    fail_path = {
        "enabled": False,
        "failure_log": None,
        "self_repair_attempts": 0,
    }

    # Errors (stub - would track recent errors)
    errors = []

    # Generate recommendations based on what we found
    recommendations = []

    # Check for missing API keys
    missing_keys = [p["name"] for p in providers_status if not p["api_key_set"]]
    if missing_keys:
        recommendations.append({
            "severity": "warning",
            "category": "configuration",
            "message": f"Missing API keys for providers: {', '.join(missing_keys)}",
            "action": f"Set environment variables: {', '.join([PROVIDERS[p]['api_key_env'] for p in missing_keys])}",
        })

    # Check for stub agent files
    stub_agents = [a["name"] for a in agent_files_status if a["is_stub"]]
    if stub_agents:
        recommendations.append({
            "severity": "info",
            "category": "configuration",
            "message": f"{len(stub_agents)} agent files appear to be stubs",
            "action": f"Consider customizing agent prompts in {agents_dir}/",
        })

    # Check if .cc directory was just created
    if bootstrap_info.get("created"):
        recommendations.append({
            "severity": "info",
            "category": "setup",
            "message": "Bootstrap directory was just created",
            "action": "Review and customize agent prompts and configuration files",
        })

    # Build the full info payload
    raw_data = {
        "bootstrap": {
            "project_root": os.path.abspath(project_root),
            "cc_dir": cc_dir,
            "agents_dir": agents_dir,
            "status": "initialized" if os.path.exists(cc_dir) else "not_initialized",
            "created_files": bootstrap_info.get("created", []),
        },
        "agent_files": agent_files_status,
        "agent_workflow": agent_workflow,
        "providers": providers_status,
        "pipeline_status": pipeline_status,
        "fail_path": fail_path,
        "errors": errors,
        "recommendations": recommendations,
    }

    return InfoSnapshot(raw=raw_data)

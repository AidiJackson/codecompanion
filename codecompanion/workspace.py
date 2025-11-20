"""
Workspace configuration and metadata management.

Handles initialization of .cc/ directories and workspace.json metadata
for repository-level CodeCompanion configuration.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from .target import TargetContext
from .project_detector import ProjectDetector


def is_initialized(target: TargetContext) -> bool:
    """
    Check if workspace is already initialized.

    Args:
        target: TargetContext for the repository

    Returns:
        True if workspace.json exists
    """
    return target.file_exists(".cc/workspace.json")


def get_git_info(target: TargetContext) -> Optional[Dict[str, str]]:
    """
    Extract git repository information.

    Args:
        target: TargetContext for the repository

    Returns:
        Dict with git info or None if not a git repo
    """
    try:
        # First check if this is even a git repo
        check_result = target.safe_cmd("git rev-parse --git-dir")
        if check_result['code'] != 0:
            return None

        git_info = {}

        # Get remote URL (might not exist for new repos)
        remote_result = target.safe_cmd("git remote get-url origin")
        if remote_result['code'] == 0:
            git_info['remote_url'] = remote_result['stdout'].strip()

        # Get current branch
        branch_result = target.safe_cmd("git rev-parse --abbrev-ref HEAD")
        if branch_result['code'] == 0:
            git_info['current_branch'] = branch_result['stdout'].strip()

        # Get commit hash if available
        commit_result = target.safe_cmd("git rev-parse HEAD")
        if commit_result['code'] == 0:
            git_info['commit_hash'] = commit_result['stdout'].strip()[:8]

        return git_info if git_info else None

    except Exception:
        return None


def create_workspace_config(target: TargetContext, force: bool = False) -> Dict[str, Any]:
    """
    Create or update workspace.json with repository metadata.

    Args:
        target: TargetContext for the repository
        force: If True, overwrite existing config. If False, update existing.

    Returns:
        Workspace configuration dict
    """
    # Check if already initialized
    if is_initialized(target) and not force:
        # Load and update existing config
        try:
            existing_content = target.read_file(".cc/workspace.json")
            existing = json.loads(existing_content)

            # Update project type detection (may have changed)
            existing["project_type"] = ProjectDetector.detect_project_type(target.root)
            existing["last_updated"] = datetime.utcnow().isoformat() + "Z"

            # Update git info
            git_info = get_git_info(target)
            if git_info:
                existing["git"] = git_info

            return existing
        except (json.JSONDecodeError, KeyError):
            # If config is corrupted, recreate it
            pass

    # Create new configuration
    project_info = ProjectDetector.detect_project_type(target.root)
    git_info = get_git_info(target)

    config = {
        "version": "0.1.0",
        "initialized_at": datetime.utcnow().isoformat() + "Z",
        "project_root": str(target.root),
        "project_type": project_info,
        "git": git_info,
        "codecompanion": {
            "agents_enabled": True,
            "auto_update": False,
            "default_provider": "claude"
        }
    }

    return config


def save_workspace_config(target: TargetContext, config: Dict[str, Any]) -> None:
    """
    Save workspace configuration to .cc/workspace.json.

    Args:
        target: TargetContext for the repository
        config: Configuration dict to save
    """
    target.write_file(".cc/workspace.json", json.dumps(config, indent=2))


def load_workspace_config(target: TargetContext) -> Optional[Dict[str, Any]]:
    """
    Load workspace configuration from .cc/workspace.json.

    Args:
        target: TargetContext for the repository

    Returns:
        Configuration dict or None if not initialized
    """
    if not is_initialized(target):
        return None

    try:
        content = target.read_file(".cc/workspace.json")
        return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def get_workspace_summary(config: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of workspace configuration.

    Args:
        config: Workspace configuration dict

    Returns:
        Formatted summary string
    """
    lines = []

    # Project info
    project_type = config.get("project_type", {})
    lines.append(f"📦 Project Type: {project_type.get('type', 'unknown')}")

    if project_type.get('language'):
        lines.append(f"💬 Language: {project_type.get('language')}")

    if project_type.get('framework'):
        lines.append(f"🔧 Framework: {project_type.get('framework')}")

    # Git info
    git_info = config.get("git")
    if git_info:
        if 'remote_url' in git_info:
            lines.append(f"🔗 Remote: {git_info['remote_url']}")
        if 'current_branch' in git_info:
            lines.append(f"🌿 Branch: {git_info['current_branch']}")

    # Initialization time
    if 'initialized_at' in config:
        lines.append(f"📅 Initialized: {config['initialized_at'][:10]}")

    return "\n".join(lines)

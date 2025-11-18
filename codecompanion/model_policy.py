"""
Model Policy Engine - Multi-Model Selection System

This module provides a configurable policy-based system for selecting
which LLM (provider + model + parameters) to use for each task type.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ModelCandidate:
    """Represents a candidate model configuration."""
    provider: str
    model: str
    max_tokens: int
    temperature: float


@dataclass
class RolePolicy:
    """Policy configuration for a specific role."""
    role: str
    candidates: list[ModelCandidate]


@dataclass
class PolicyMode:
    """A complete policy mode with all role configurations."""
    name: str
    description: str
    roles: dict[str, RolePolicy]


@dataclass
class ModelSelection:
    """The final selected model configuration for a task."""
    provider: str
    model: str
    max_tokens: int
    temperature: float
    mode: str
    role: str


class PolicyError(Exception):
    """Raised when there's an issue with policy configuration."""
    pass


def load_model_policy(path: Path | None = None) -> dict[str, Any]:
    """
    Load the model policy JSON file.

    Args:
        path: Path to the policy file. If None, uses default ops/MODEL_POLICY.json

    Returns:
        The parsed policy dictionary

    Raises:
        PolicyError: If the file doesn't exist or is malformed
    """
    if path is None:
        path = Path("ops/MODEL_POLICY.json")

    if not path.exists():
        raise PolicyError(
            f"Model policy file not found at {path}. "
            "Please ensure ops/MODEL_POLICY.json exists."
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            policy = json.load(f)
    except json.JSONDecodeError as e:
        raise PolicyError(f"Invalid JSON in policy file {path}: {e}")
    except Exception as e:
        raise PolicyError(f"Error loading policy file {path}: {e}")

    # Basic validation
    if "modes" not in policy:
        raise PolicyError("Policy file must contain a 'modes' key")

    if not isinstance(policy["modes"], dict):
        raise PolicyError("Policy 'modes' must be a dictionary")

    return policy


def get_default_mode(policy: dict[str, Any]) -> str:
    """
    Get the default mode from the policy.

    Args:
        policy: The loaded policy dictionary

    Returns:
        The default mode name (defaults to "balanced" if not specified)
    """
    return policy.get("default_mode", "balanced")


def select_model(
    policy: dict[str, Any],
    mode: str,
    role: str
) -> ModelSelection:
    """
    Select the appropriate model based on policy, mode, and role.

    Args:
        policy: The loaded policy dictionary
        mode: The policy mode to use (e.g., "balanced", "cheapest")
        role: The task role (e.g., "planner", "architect", "specialist_frontend")

    Returns:
        ModelSelection with the chosen configuration

    Raises:
        PolicyError: If the mode or role is not found
    """
    modes = policy.get("modes", {})

    # Check if mode exists, fall back to default if not
    if mode not in modes:
        default_mode = get_default_mode(policy)
        if mode != default_mode:
            # Only warn if different from default
            print(f"[model-policy] WARNING: Mode '{mode}' not found, falling back to '{default_mode}'")
        mode = default_mode

        if mode not in modes:
            raise PolicyError(
                f"Default mode '{mode}' not found in policy. "
                f"Available modes: {list(modes.keys())}"
            )

    mode_config = modes[mode]
    roles = mode_config.get("roles", {})

    # Check if role exists
    if role not in roles:
        # Try generic fallback
        if "generic" in roles:
            print(f"[model-policy] WARNING: Role '{role}' not found in mode '{mode}', using 'generic'")
            role = "generic"
        else:
            raise PolicyError(
                f"Role '{role}' not found in mode '{mode}' and no 'generic' fallback available. "
                f"Available roles: {list(roles.keys())}"
            )

    role_candidates = roles[role]

    # Validate role has candidates
    if not role_candidates or len(role_candidates) == 0:
        raise PolicyError(f"No candidates defined for role '{role}' in mode '{mode}'")

    # Take the first candidate
    candidate = role_candidates[0]

    # Validate candidate has required fields
    required_fields = ["provider", "model", "max_tokens", "temperature"]
    for field in required_fields:
        if field not in candidate:
            raise PolicyError(
                f"Candidate for role '{role}' in mode '{mode}' missing required field '{field}'"
            )

    return ModelSelection(
        provider=candidate["provider"],
        model=candidate["model"],
        max_tokens=candidate["max_tokens"],
        temperature=candidate["temperature"],
        mode=mode,
        role=role
    )


@dataclass
class TaskContext:
    """Context information for a task requiring LLM processing."""
    role: str
    purpose: str = ""
    project_name: str | None = None


def get_model_for_task(
    task_context: TaskContext,
    policy_path: Path | None = None,
    mode: str | None = None
) -> ModelSelection:
    """
    High-level helper to get the model selection for a task.

    Args:
        task_context: The task context with role information
        policy_path: Optional custom policy file path
        mode: Optional mode override (uses default from policy if not specified)

    Returns:
        ModelSelection for the task
    """
    policy = load_model_policy(policy_path)

    if mode is None:
        mode = get_default_mode(policy)

    return select_model(policy, mode, task_context.role)

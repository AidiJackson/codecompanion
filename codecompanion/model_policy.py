"""Model policy engine for selecting appropriate LLM providers and models based on roles and modes."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class ModelSelection:
    """Result of model selection from policy."""

    provider: str
    model: str
    temperature: float = 0.2
    max_tokens: int = 4096
    role: str = "default"
    mode: str = "default"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ModelPolicy:
    """Model policy configuration."""

    modes: dict[str, dict[str, Any]]
    roles: dict[str, dict[str, Any]]
    defaults: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def load_model_policy(policy_file: str = ".cc/model_policy.json") -> ModelPolicy:
    """Load model policy from file, or return default policy if file doesn't exist."""
    policy_path = Path(policy_file)

    if policy_path.exists():
        try:
            with open(policy_path, "r") as f:
                data = json.load(f)
            return ModelPolicy(
                modes=data.get("modes", {}),
                roles=data.get("roles", {}),
                defaults=data.get("defaults", {}),
            )
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    # Return default policy
    return _get_default_policy()


def _get_default_policy() -> ModelPolicy:
    """Get default model policy."""
    return ModelPolicy(
        modes={
            "fast": {
                "description": "Fast, cost-effective mode",
                "default_provider": "claude",
                "default_model": "claude-3-haiku-20240307",
                "temperature": 0.1,
                "max_tokens": 2048,
            },
            "balanced": {
                "description": "Balanced performance and cost",
                "default_provider": "claude",
                "default_model": "claude-3-5-sonnet-20241022",
                "temperature": 0.2,
                "max_tokens": 4096,
            },
            "powerful": {
                "description": "Maximum capability mode",
                "default_provider": "gpt4",
                "default_model": "gpt-4o",
                "temperature": 0.3,
                "max_tokens": 8192,
            },
        },
        roles={
            "recovery": {
                "description": "Self-repair and error recovery",
                "preferred_provider": "claude",
                "preferred_model": "claude-3-5-sonnet-20241022",
                "temperature": 0.1,
                "max_tokens": 4096,
            },
            "analysis": {
                "description": "Code analysis and understanding",
                "preferred_provider": "gpt4",
                "preferred_model": "gpt-4o",
                "temperature": 0.2,
                "max_tokens": 4096,
            },
            "generation": {
                "description": "Code generation and patching",
                "preferred_provider": "claude",
                "preferred_model": "claude-3-5-sonnet-20241022",
                "temperature": 0.3,
                "max_tokens": 8192,
            },
        },
        defaults={
            "provider": "claude",
            "model": "claude-3-5-sonnet-20241022",
            "temperature": 0.2,
            "max_tokens": 4096,
        },
    )


def select_model(
    policy: ModelPolicy, mode: str = "balanced", role: str = "default"
) -> ModelSelection:
    """Select appropriate model based on mode and role."""
    # Start with defaults
    provider = policy.defaults.get("provider", "claude")
    model = policy.defaults.get("model", "claude-3-5-sonnet-20241022")
    temperature = policy.defaults.get("temperature", 0.2)
    max_tokens = policy.defaults.get("max_tokens", 4096)

    # Apply mode-specific settings
    if mode in policy.modes:
        mode_config = policy.modes[mode]
        provider = mode_config.get("default_provider", provider)
        model = mode_config.get("default_model", model)
        temperature = mode_config.get("temperature", temperature)
        max_tokens = mode_config.get("max_tokens", max_tokens)

    # Override with role-specific settings (roles take precedence)
    if role in policy.roles:
        role_config = policy.roles[role]
        provider = role_config.get("preferred_provider", provider)
        model = role_config.get("preferred_model", model)
        temperature = role_config.get("temperature", temperature)
        max_tokens = role_config.get("max_tokens", max_tokens)

    return ModelSelection(
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        role=role,
        mode=mode,
    )


def save_model_policy(policy: ModelPolicy, policy_file: str = ".cc/model_policy.json") -> None:
    """Save model policy to file."""
    policy_path = Path(policy_file)
    policy_path.parent.mkdir(parents=True, exist_ok=True)

    with open(policy_path, "w") as f:
        json.dump(policy.to_dict(), f, indent=2)

"""
Model policy and selection logic for CodeCompanion.

Provides model selection based on policy mode (balanced, cheapest, fastest, etc.)
integrated with project settings.
"""

from typing import Dict, Any, Optional

from .settings import Settings


# Embedded model policy configuration
# Maps mode names to model selection criteria
MODEL_POLICY = {
    "balanced": {
        "description": "Balanced performance and cost",
        "primary_model": "claude",
        "fallback_model": "gpt4",
        "cost_threshold": "medium"
    },
    "cheapest": {
        "description": "Minimize costs",
        "primary_model": "claude",
        "fallback_model": "gemini",
        "cost_threshold": "low"
    },
    "fastest": {
        "description": "Maximize speed",
        "primary_model": "gpt4",
        "fallback_model": "claude",
        "cost_threshold": "high"
    },
    "quality": {
        "description": "Highest quality outputs",
        "primary_model": "claude",
        "fallback_model": "gpt4",
        "cost_threshold": "high"
    }
}

# Default mode if none specified
DEFAULT_MODE = "balanced"


def get_model_policy(mode: Optional[str] = None, settings: Optional[Settings] = None) -> Dict[str, Any]:
    """
    Get model policy configuration for the specified mode.

    Policy selection order:
    1. Explicit mode parameter
    2. Settings.model_policy_mode (if settings provided)
    3. DEFAULT_MODE

    Args:
        mode: Optional explicit mode to use
        settings: Optional Settings instance to read mode from

    Returns:
        Dictionary with policy configuration including:
        - description: Human-readable description
        - primary_model: Primary model to use
        - fallback_model: Fallback model if primary fails
        - cost_threshold: Cost management level

    Raises:
        ValueError: If specified mode is not found in MODEL_POLICY
    """
    # Determine which mode to use
    selected_mode = mode

    if selected_mode is None and settings is not None:
        selected_mode = settings.model_policy_mode

    if selected_mode is None:
        selected_mode = DEFAULT_MODE

    # Get policy for selected mode
    if selected_mode not in MODEL_POLICY:
        # Fall back to default if mode not found
        if selected_mode != DEFAULT_MODE:
            print(f"[codecompanion] Warning: Mode '{selected_mode}' not found, using '{DEFAULT_MODE}'")
        selected_mode = DEFAULT_MODE

    policy = MODEL_POLICY[selected_mode].copy()
    policy["mode"] = selected_mode

    return policy


def get_primary_model(mode: Optional[str] = None, settings: Optional[Settings] = None) -> str:
    """
    Get the primary model for the specified mode.

    Args:
        mode: Optional explicit mode
        settings: Optional Settings instance

    Returns:
        Model identifier string (e.g., "claude", "gpt4", "gemini")
    """
    policy = get_model_policy(mode=mode, settings=settings)
    return policy["primary_model"]


def get_available_modes() -> list[str]:
    """
    Get list of available policy modes.

    Returns:
        List of mode names
    """
    return list(MODEL_POLICY.keys())

"""
Output validation for CodeCompanion agent execution.

Provides structural validation of agent outputs to catch common failure modes
early in the execution pipeline.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    """Result of validating an agent's output."""

    ok: bool
    """Validation passed?"""

    issues: list[str]
    """List of validation issues found."""

    agent: str
    """Name of the agent that produced this output."""

    raw: Any
    """Raw output from the agent."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional context about the validation."""


# LLM-based agents that should produce meaningful text/structured output
LLM_AGENTS = {
    "EnvDoctor",
    "Analyzer",
    "DepAuditor",
    "BugTriage",
    "Fixer",
    "WebDoctor",
    "PRPreparer",
}

# Tooling agents that return exit codes
TOOLING_AGENTS = {
    "Installer",
    "TestRunner",
}

# Common LLM failure patterns
LLM_FAILURE_PATTERNS = [
    "i cannot",
    "i can't",
    "i am unable",
    "error:",
    "exception:",
    "failed to",
    "sorry, i",
]


def validate_agent_output(agent: str, payload: Any) -> ValidationResult:
    """
    Validate agent output based on agent type and expected structure.

    Args:
        agent: Name of the agent (e.g., "Analyzer", "Installer")
        payload: Raw output from the agent

    Returns:
        ValidationResult indicating success or issues found

    Note:
        This function does NOT raise exceptions. All validation failures
        are returned as ValidationResult with ok=False and issues list.
    """
    issues = []
    metadata = {}

    # Universal check: output should be non-empty
    if payload is None:
        issues.append("Output is None")
        return ValidationResult(
            ok=False, issues=issues, agent=agent, raw=payload, metadata=metadata
        )

    if isinstance(payload, str) and not payload.strip():
        issues.append("Output is empty string")
        return ValidationResult(
            ok=False, issues=issues, agent=agent, raw=payload, metadata=metadata
        )

    # For LLM-based agents, perform deeper validation
    if agent in LLM_AGENTS:
        llm_issues = _validate_llm_output(payload)
        issues.extend(llm_issues)
        metadata["agent_type"] = "llm"

    # For tooling agents, validate exit code
    elif agent in TOOLING_AGENTS:
        tooling_issues = _validate_tooling_output(payload)
        issues.extend(tooling_issues)
        metadata["agent_type"] = "tooling"

    # Unknown agent type - basic validation only
    else:
        metadata["agent_type"] = "unknown"
        if isinstance(payload, str) and len(payload.strip()) < 10:
            issues.append("Output suspiciously short (< 10 chars)")

    return ValidationResult(
        ok=(len(issues) == 0), issues=issues, agent=agent, raw=payload, metadata=metadata
    )


def _validate_llm_output(payload: Any) -> list[str]:
    """Validate output from LLM-based agents."""
    issues = []

    # Check for string output
    if isinstance(payload, str):
        text = payload.lower().strip()

        # Check minimum length
        if len(text) < 20:
            issues.append("LLM output too short (< 20 chars)")

        # Check for common failure patterns
        for pattern in LLM_FAILURE_PATTERNS:
            if pattern in text[:100]:  # Check first 100 chars
                issues.append(f"LLM output contains failure pattern: '{pattern}'")
                break

    # Check for dict output
    elif isinstance(payload, dict):
        if not payload:
            issues.append("LLM output is empty dict")
        # Could add specific key checks here for known output structures

    # Check for list output
    elif isinstance(payload, list):
        if not payload:
            issues.append("LLM output is empty list")

    # Unexpected type
    else:
        issues.append(f"LLM output has unexpected type: {type(payload).__name__}")

    return issues


def _validate_tooling_output(payload: Any) -> list[str]:
    """Validate output from tooling agents (exit codes)."""
    issues = []

    # Tooling agents typically return exit codes (int)
    # or dicts with 'code' key (from run_cmd)
    if isinstance(payload, int):
        if payload != 0:
            issues.append(f"Tooling agent returned non-zero exit code: {payload}")
    elif isinstance(payload, dict) and "code" in payload:
        if payload["code"] != 0:
            issues.append(
                f"Tooling agent returned non-zero exit code: {payload['code']}"
            )
            if "stderr" in payload and payload["stderr"]:
                issues.append(f"Stderr: {payload['stderr'][:200]}")
    else:
        # If it's not a clear exit code, just warn
        if not isinstance(payload, (int, dict)):
            issues.append(
                f"Tooling output has unexpected type: {type(payload).__name__}"
            )

    return issues


def is_validation_strict() -> bool:
    """
    Check if strict validation mode is enabled.

    In strict mode, validation is more rigorous and may catch
    edge cases that would otherwise be allowed.

    Returns:
        True if strict validation is enabled (from settings)
    """
    # TODO: Load from settings.json when available
    # For now, always return False (permissive mode)
    return False

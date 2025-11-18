"""
Recovery engine for CodeCompanion agent failures.

Provides retry and recovery strategies for agent execution failures,
with hooks for future LLM-driven self-repair.
"""

import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RetryConfig:
    """Configuration for retry and recovery strategies."""

    max_attempts: int = 2
    """Maximum number of retry attempts."""

    backoff: float = 0.0
    """Backoff delay in seconds between retries."""

    fallback_enabled: bool = False
    """Enable fallback to alternative models/strategies."""

    strict_mode: bool = False
    """Strict validation mode (more rigorous checks)."""


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""

    ok: bool
    """Was recovery successful?"""

    attempts: int
    """Number of attempts made."""

    used_fallback: bool
    """Did recovery use a fallback strategy?"""

    final_payload: Optional[Any] = None
    """Recovered output (if ok=True)."""

    error: Optional[str] = None
    """Error message (if ok=False)."""


class RecoveryEngine:
    """
    Engine for attempting to recover from agent execution failures.

    Current implementation (Phase F):
    - Simple JSON parsing recovery
    - No-op for most failures (logged and returned as-is)

    Future implementation (Phase G+):
    - LLM-driven self-repair
    - Multi-model fallback via model_policy
    - Prompt adjustment and retry
    """

    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """
        Initialize recovery engine.

        Args:
            retry_config: Configuration for retry/recovery behavior
        """
        self.config = retry_config or RetryConfig()

    def attempt_recover(
        self,
        agent: str,
        raw_output: Any,
        issues: list[str],
    ) -> RecoveryResult:
        """
        Attempt to recover from validation failure.

        Args:
            agent: Name of the agent that failed
            raw_output: Raw output from the agent
            issues: List of validation issues

        Returns:
            RecoveryResult indicating success or failure

        Current Strategy:
        1. If no issues → immediate success
        2. If raw_output is JSON string → try parsing
        3. If parsing succeeds → recovered
        4. Otherwise → unrecovered failure
        """
        # No issues - immediate success
        if not issues:
            return RecoveryResult(
                ok=True,
                attempts=0,
                used_fallback=False,
                final_payload=raw_output,
                error=None,
            )

        # Attempt recovery strategies
        attempts = 0
        max_attempts = self.config.max_attempts

        while attempts < max_attempts:
            attempts += 1

            # Strategy 1: Try to parse as JSON if it's a string
            if isinstance(raw_output, str):
                recovery = self._try_json_parse_recovery(raw_output)
                if recovery.ok:
                    return RecoveryResult(
                        ok=True,
                        attempts=attempts,
                        used_fallback=False,
                        final_payload=recovery.final_payload,
                        error=None,
                    )

            # Strategy 2: Check if it's a partial success (future)
            # ...

            # Strategy 3: LLM-driven repair (future)
            # if self.config.fallback_enabled:
            #     recovery = self._llm_repair(agent, raw_output, issues)
            #     if recovery.ok:
            #         return recovery

            # No more strategies to try
            break

        # All recovery attempts failed
        error_msg = f"Recovery failed after {attempts} attempt(s). Issues: {', '.join(issues[:3])}"
        return RecoveryResult(
            ok=False,
            attempts=attempts,
            used_fallback=False,
            final_payload=None,
            error=error_msg,
        )

    def _try_json_parse_recovery(self, raw_output: str) -> RecoveryResult:
        """
        Attempt to recover by parsing string as JSON.

        This handles cases where the LLM returns valid JSON but
        it was captured as a plain string.
        """
        try:
            # Try to find JSON in the output
            # Look for {...} or [...]
            trimmed = raw_output.strip()

            # Try direct JSON parse
            parsed = json.loads(trimmed)

            # Successfully parsed
            return RecoveryResult(
                ok=True,
                attempts=1,
                used_fallback=False,
                final_payload=parsed,
                error=None,
            )

        except (json.JSONDecodeError, ValueError):
            # JSON parsing failed - try to extract JSON from text
            # Look for code blocks or JSON-like patterns
            if "```json" in raw_output:
                try:
                    # Extract JSON from markdown code block
                    start = raw_output.find("```json") + 7
                    end = raw_output.find("```", start)
                    if end > start:
                        json_text = raw_output[start:end].strip()
                        parsed = json.loads(json_text)
                        return RecoveryResult(
                            ok=True,
                            attempts=1,
                            used_fallback=False,
                            final_payload=parsed,
                            error=None,
                        )
                except (json.JSONDecodeError, ValueError):
                    pass

            # Could not recover
            return RecoveryResult(
                ok=False,
                attempts=1,
                used_fallback=False,
                final_payload=None,
                error="JSON parsing failed",
            )

    def _llm_repair(
        self, agent: str, raw_output: Any, issues: list[str]
    ) -> RecoveryResult:
        """
        Use LLM to repair invalid output.

        FUTURE IMPLEMENTATION (Phase G):
        - Construct repair prompt with agent context and issues
        - Select repair model via model_policy
        - Ask LLM to fix or regenerate output
        - Re-validate result

        For now, this is a stub that returns failure.
        """
        # TODO: Implement LLM-driven repair
        # This is where we'll integrate with model_policy
        # and use an LLM to analyze the failure and generate a fix

        return RecoveryResult(
            ok=False,
            attempts=1,
            used_fallback=True,
            final_payload=None,
            error="LLM repair not yet implemented",
        )


def create_default_config() -> RetryConfig:
    """
    Create default retry configuration.

    Returns:
        RetryConfig with conservative defaults
    """
    return RetryConfig(
        max_attempts=2,
        backoff=0.0,
        fallback_enabled=False,
        strict_mode=False,
    )


def load_config_from_settings(settings: dict) -> RetryConfig:
    """
    Load retry configuration from settings dict.

    Args:
        settings: Settings dict with 'fail_path' key

    Returns:
        RetryConfig populated from settings
    """
    fail_path = settings.get("fail_path", {})

    return RetryConfig(
        max_attempts=fail_path.get("max_attempts", 2),
        backoff=fail_path.get("backoff_seconds", 0.0),
        fallback_enabled=fail_path.get("fallback_enabled", False),
        strict_mode=fail_path.get("strict_validation", False),
    )

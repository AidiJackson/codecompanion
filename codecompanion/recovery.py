"""Recovery engine for handling agent failures and attempting repairs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .settings import Settings


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""

    ok: bool
    used_fallback: bool = False
    final_payload: Any = None
    message: str | None = None
    details: dict[str, Any] = None

    def __post_init__(self):
        """Initialize details if needed."""
        if self.details is None:
            self.details = {}


class RecoveryEngine:
    """Engine for attempting recovery from agent failures."""

    def __init__(self, settings: Settings, self_repair_agent=None):
        """
        Initialize recovery engine.

        Args:
            settings: CodeCompanion settings
            self_repair_agent: Optional SelfRepairAgent instance for LLM-based repair
        """
        self.settings = settings
        self.self_repair_agent = self_repair_agent

    def attempt_recover(
        self,
        agent: str,
        stage: str,
        raw_output: Any,
        error: Exception,
        issues: list[str] | None = None,
    ) -> RecoveryResult:
        """
        Attempt to recover from an agent failure.

        Args:
            agent: Name of the agent that failed
            stage: Stage of execution where failure occurred
            raw_output: Raw output from the failed agent
            error: Exception that was raised
            issues: List of validation issues (if available)

        Returns:
            RecoveryResult indicating success/failure and recovered payload
        """
        if issues is None:
            issues = [str(error)]

        # First, try lightweight recovery (JSON parsing, simple fixes)
        lightweight_result = self._lightweight_recovery(raw_output, error)
        if lightweight_result.ok:
            return lightweight_result

        # If lightweight recovery failed and LLM repair is enabled, try self-repair
        if (
            self.settings.fail_path.llm_repair_enabled
            and self.self_repair_agent is not None
        ):
            return self._llm_recovery(agent, stage, raw_output, issues)

        # No recovery possible
        return RecoveryResult(
            ok=False,
            message="No recovery method succeeded",
            details={"issues": issues},
        )

    def _lightweight_recovery(
        self, raw_output: Any, error: Exception
    ) -> RecoveryResult:
        """
        Attempt lightweight recovery without LLM.

        This handles common issues like:
        - JSON parsing errors with extra text
        - Missing fields with sensible defaults
        - Simple formatting issues
        """
        # If it's a JSON parsing error, try to extract JSON from text
        if "JSON" in str(error) or "json" in str(error):
            if isinstance(raw_output, str):
                # Try to find JSON in the text
                fixed = self._extract_json(raw_output)
                if fixed is not None:
                    return RecoveryResult(
                        ok=True,
                        used_fallback=True,
                        final_payload=fixed,
                        message="Extracted JSON from text",
                        details={"method": "json_extraction"},
                    )

        # No lightweight recovery succeeded
        return RecoveryResult(ok=False, message="Lightweight recovery failed")

    def _extract_json(self, text: str) -> Any:
        """Try to extract valid JSON from text."""
        # Look for JSON object or array
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start_idx = text.find(start_char)
            if start_idx == -1:
                continue

            # Find matching closing bracket
            end_idx = text.rfind(end_char)
            if end_idx == -1:
                continue

            candidate = text[start_idx : end_idx + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

        return None

    def _llm_recovery(
        self, agent: str, stage: str, raw_output: Any, issues: list[str]
    ) -> RecoveryResult:
        """
        Attempt LLM-based recovery using self-repair agent.

        Args:
            agent: Name of the agent that failed
            stage: Stage of execution
            raw_output: Raw output from failed agent
            issues: List of validation issues

        Returns:
            RecoveryResult with LLM repair attempt result
        """
        from .self_repair import SelfRepairRequest

        # Create repair request
        request = SelfRepairRequest(
            agent=agent,
            stage=stage,
            issues=issues,
            raw_output=raw_output,
        )

        try:
            # Attempt repair
            repair_result = self.self_repair_agent.repair(request)

            if repair_result.ok:
                return RecoveryResult(
                    ok=True,
                    used_fallback=True,
                    final_payload=repair_result.fixed_output,
                    message=f"LLM repair succeeded using {repair_result.used_model}",
                    details={
                        "method": "llm_repair",
                        "model": repair_result.used_model,
                        "attempts": repair_result.attempts,
                    },
                )
            else:
                return RecoveryResult(
                    ok=False,
                    message=f"LLM repair failed: {repair_result.message}",
                    details={
                        "method": "llm_repair",
                        "attempts": repair_result.attempts,
                    },
                )

        except Exception as e:
            return RecoveryResult(
                ok=False,
                message=f"LLM recovery error: {str(e)}",
                details={"method": "llm_repair", "error": str(e)},
            )

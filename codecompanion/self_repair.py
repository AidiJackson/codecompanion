"""LLM-based self-repair agent for fixing invalid agent outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .model_policy import ModelSelection, load_model_policy, select_model
from .settings import Settings
from .llm import complete, LLMError


@dataclass
class SelfRepairConfig:
    """Configuration for self-repair behavior."""

    max_attempts: int
    enabled: bool
    mode: str  # model policy mode to use (e.g., "balanced", "fast", "powerful")
    role: str = "recovery"


@dataclass
class SelfRepairRequest:
    """Request for self-repair of agent output."""

    agent: str  # e.g., "specialist_backend"
    stage: str  # e.g., "specialist"
    issues: list[str]  # List of validation issues
    raw_output: Any  # Raw output from the agent


@dataclass
class SelfRepairResult:
    """Result of a self-repair attempt."""

    ok: bool
    attempts: int
    used_model: str | None
    fixed_output: Any | None
    message: str | None


class SelfRepairAgent:
    """Agent that uses LLM to repair invalid agent outputs."""

    def __init__(self, settings: Settings):
        """
        Initialize self-repair agent.

        Args:
            settings: CodeCompanion settings
        """
        self.settings = settings
        self.policy = load_model_policy()

        # Create repair configuration from settings
        self.config = SelfRepairConfig(
            max_attempts=settings.fail_path.llm_repair_max_attempts,
            enabled=settings.fail_path.llm_repair_enabled,
            mode=settings.model_policy_mode,
            role="recovery",
        )

    def select_model(self) -> ModelSelection:
        """
        Select appropriate model for recovery using policy.

        Returns:
            ModelSelection with provider, model, and parameters
        """
        return select_model(self.policy, mode=self.config.mode, role=self.config.role)

    def repair(self, request: SelfRepairRequest) -> SelfRepairResult:
        """
        Attempt to repair invalid agent output using LLM.

        Args:
            request: SelfRepairRequest with agent info and issues

        Returns:
            SelfRepairResult indicating success/failure and fixed output
        """
        if not self.config.enabled:
            return SelfRepairResult(
                ok=False,
                attempts=0,
                used_model=None,
                fixed_output=None,
                message="Self-repair disabled in settings.",
            )

        # Select model for repair
        model_selection = self.select_model()

        # Build repair prompt
        prompt = self._build_repair_prompt(request)

        # Attempt repair
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                # Call LLM
                response = complete(
                    system=prompt["system"],
                    messages=prompt["messages"],
                    provider=model_selection.provider,
                    temperature=model_selection.temperature,
                    max_tokens=model_selection.max_tokens,
                )

                # Extract content
                content = response.get("content", "")
                if not content:
                    continue

                # Try to parse as JSON (for structured outputs)
                fixed_output = self._parse_response(content)
                if fixed_output is not None:
                    return SelfRepairResult(
                        ok=True,
                        attempts=attempt,
                        used_model=f"{model_selection.provider}:{model_selection.model}",
                        fixed_output=fixed_output,
                        message="Successfully repaired output",
                    )

            except LLMError as e:
                # LLM call failed
                if attempt >= self.config.max_attempts:
                    return SelfRepairResult(
                        ok=False,
                        attempts=attempt,
                        used_model=f"{model_selection.provider}:{model_selection.model}",
                        fixed_output=None,
                        message=f"LLM error: {str(e)}",
                    )
                # Otherwise, try again

            except Exception as e:
                # Unexpected error
                return SelfRepairResult(
                    ok=False,
                    attempts=attempt,
                    used_model=f"{model_selection.provider}:{model_selection.model}",
                    fixed_output=None,
                    message=f"Unexpected error: {str(e)}",
                )

        # All attempts failed
        return SelfRepairResult(
            ok=False,
            attempts=self.config.max_attempts,
            used_model=f"{model_selection.provider}:{model_selection.model}",
            fixed_output=None,
            message="Failed to repair output after all attempts",
        )

    def _build_repair_prompt(self, request: SelfRepairRequest) -> dict[str, Any]:
        """
        Build LLM prompt for repairing agent output.

        Args:
            request: SelfRepairRequest with agent info and issues

        Returns:
            Dictionary with 'system' and 'messages' keys for LLM call
        """
        # Format issues
        issues_text = "\n".join(f"- {issue}" for issue in request.issues)

        # Format raw output
        if isinstance(request.raw_output, (dict, list)):
            raw_output_text = json.dumps(request.raw_output, indent=2)
        else:
            raw_output_text = str(request.raw_output)

        system = f"""You are a self-repair agent for CodeCompanion. Your task is to fix invalid agent outputs.

Agent: {request.agent}
Stage: {request.stage}

The agent produced output with the following validation issues:
{issues_text}

Your job is to repair the output to make it valid. Return ONLY the corrected output in valid JSON format or the appropriate text format. Do not include explanations or markdown formatting."""

        messages = [
            {
                "role": "user",
                "content": f"""Here is the invalid output that needs to be repaired:

{raw_output_text}

Please return the corrected version.""",
            }
        ]

        return {"system": system, "messages": messages}

    def _parse_response(self, content: str) -> Any:
        """
        Parse LLM response to extract fixed output.

        Args:
            content: Raw response content from LLM

        Returns:
            Parsed output, or None if parsing failed
        """
        # First, try to parse as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from text (in case LLM added extra text)
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start_idx = content.find(start_char)
            if start_idx == -1:
                continue

            end_idx = content.rfind(end_char)
            if end_idx == -1:
                continue

            candidate = content[start_idx : end_idx + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

        # If JSON parsing failed, return the content as-is (might be plain text)
        # Only return it if it's non-empty and looks reasonable
        stripped = content.strip()
        if stripped and len(stripped) > 0:
            return stripped

        return None

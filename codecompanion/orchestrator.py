"""Orchestrator for running agents with error tracking and recovery."""

from __future__ import annotations

from typing import Any, Callable

from .errors import ErrorLogger, create_error_record
from .recovery import RecoveryEngine
from .self_repair import SelfRepairAgent
from .settings import Settings, load_settings


class Orchestrator:
    """Orchestrates agent execution with error tracking and recovery."""

    def __init__(self, settings: Settings | None = None):
        """
        Initialize orchestrator.

        Args:
            settings: CodeCompanion settings (loads from file if not provided)
        """
        self.settings = settings or load_settings()
        self.error_logger = ErrorLogger()

        # Initialize self-repair agent if enabled
        self.self_repair_agent = None
        if self.settings.fail_path.llm_repair_enabled:
            try:
                self.self_repair_agent = SelfRepairAgent(self.settings)
            except Exception:
                # If self-repair agent fails to initialize, continue without it
                pass

        # Initialize recovery engine
        self.recovery_engine = RecoveryEngine(
            settings=self.settings, self_repair_agent=self.self_repair_agent
        )

    def run_with_failpath(
        self,
        agent_name: str,
        stage: str,
        agent_fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> tuple[bool, Any]:
        """
        Run an agent function with fail-path and recovery.

        Args:
            agent_name: Name of the agent being run
            stage: Stage of execution
            agent_fn: Agent function to execute
            *args: Positional arguments for agent_fn
            **kwargs: Keyword arguments for agent_fn

        Returns:
            Tuple of (success, result) where success is True if agent succeeded
            or was recovered, and result is the agent output
        """
        for attempt in range(1, self.settings.fail_path.max_attempts + 1):
            try:
                # Execute agent
                result = agent_fn(*args, **kwargs)
                return True, result

            except Exception as error:
                # Log the error
                error_record = create_error_record(
                    agent=agent_name,
                    stage=stage,
                    error_type=type(error).__name__,
                    message=str(error),
                    attempt=attempt,
                )
                self.error_logger.log_error(error_record)

                # Try recovery if enabled
                if self.settings.fail_path.fallback_enabled:
                    recovery_result = self.recovery_engine.attempt_recover(
                        agent=agent_name,
                        stage=stage,
                        raw_output=kwargs.get("raw_output"),
                        error=error,
                    )

                    if recovery_result.ok:
                        # Log successful recovery
                        recovery_record = create_error_record(
                            agent=agent_name,
                            stage=stage,
                            error_type="Recovery",
                            message=recovery_result.message or "Recovered",
                            recovered=True,
                            used_fallback=recovery_result.used_fallback,
                            recovery_method=recovery_result.details.get("method"),
                            recovery_model=recovery_result.details.get("model"),
                        )
                        self.error_logger.log_error(recovery_record)

                        return True, recovery_result.final_payload

                # Check if we should retry
                if attempt >= self.settings.fail_path.max_attempts:
                    break

                # Backoff before retry
                if self.settings.fail_path.backoff_seconds > 0:
                    import time

                    time.sleep(self.settings.fail_path.backoff_seconds)

        # All attempts failed
        return False, None

    def get_error_summary(self, limit: int | None = 10) -> list[dict[str, Any]]:
        """
        Get recent error records.

        Args:
            limit: Maximum number of errors to return (default: 10)

        Returns:
            List of error record dictionaries
        """
        return self.error_logger.get_errors(limit=limit)

    def clear_errors(self) -> None:
        """Clear the error log."""
        self.error_logger.clear_log()

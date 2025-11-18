"""
Recovery Engine - Error Detection and Self-Repair

This module provides infrastructure for detecting failures and
coordinating recovery actions using the model policy engine.
"""

from dataclasses import dataclass
from typing import Optional, List
from .settings import Settings, load_settings
from .model_policy import load_model_policy, select_model


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    success: bool
    error_type: str
    recovery_action: str
    details: str
    recovery_model: Optional[str] = None  # Format: "provider:model"


class RecoveryEngine:
    """
    Handles error detection and recovery coordination.

    This engine is aware of the model policy and can select
    appropriate models for recovery tasks, but does not yet
    perform actual LLM-based recovery (that's for future phases).
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize the recovery engine.

        Args:
            settings: Project settings (loaded from default location if None)
        """
        self.settings = settings or load_settings()
        self.recovery_history: List[RecoveryResult] = []

    def detect_failure(
        self,
        error_output: str,
        context: str = ""
    ) -> Optional[str]:
        """
        Detect and classify failures from error output.

        Args:
            error_output: Error message or output
            context: Additional context about where the error occurred

        Returns:
            Error type classification, or None if no error detected
        """
        error_lower = error_output.lower()

        # Simple pattern-based detection
        if "importerror" in error_lower or "modulenotfounderror" in error_lower:
            return "import_error"
        elif "syntaxerror" in error_lower:
            return "syntax_error"
        elif "typeerror" in error_lower:
            return "type_error"
        elif "attributeerror" in error_lower:
            return "attribute_error"
        elif "filenotfounderror" in error_lower:
            return "file_not_found"
        elif "failed" in error_lower or "error" in error_lower:
            return "generic_error"

        return None

    def plan_recovery(
        self,
        error_type: str,
        error_output: str,
        context: str = ""
    ) -> RecoveryResult:
        """
        Plan a recovery action for a detected error.

        This method determines what recovery model would be used
        (based on policy) but does not yet execute LLM-based recovery.

        Args:
            error_type: Type of error detected
            error_output: The actual error message
            context: Additional context

        Returns:
            RecoveryResult with planned action
        """
        # Determine which model would be used for recovery
        recovery_model_str = None
        try:
            policy = load_model_policy()
            selection = select_model(
                policy,
                mode=self.settings.model_policy_mode,
                role="recovery"
            )
            recovery_model_str = f"{selection.provider}:{selection.model}"
        except Exception as e:
            print(f"[recovery] WARNING: Could not load recovery model from policy: {e}")

        # Plan recovery action based on error type
        recovery_action = self._plan_action_for_error_type(error_type)

        result = RecoveryResult(
            success=False,  # Planning only, not executed yet
            error_type=error_type,
            recovery_action=recovery_action,
            details=f"Planned recovery for {error_type}",
            recovery_model=recovery_model_str
        )

        self.recovery_history.append(result)
        return result

    def _plan_action_for_error_type(self, error_type: str) -> str:
        """
        Determine the recovery action for a specific error type.

        Args:
            error_type: The classified error type

        Returns:
            Description of the recovery action
        """
        action_map = {
            "import_error": "Install missing dependencies",
            "syntax_error": "Fix syntax issues in code",
            "type_error": "Fix type mismatches",
            "attribute_error": "Fix attribute access errors",
            "file_not_found": "Create or locate missing file",
            "generic_error": "Investigate and fix generic error"
        }

        return action_map.get(error_type, "Unknown recovery action")

    def get_recovery_stats(self) -> dict:
        """
        Get statistics about recovery attempts.

        Returns:
            Dict with recovery statistics
        """
        total = len(self.recovery_history)
        successful = sum(1 for r in self.recovery_history if r.success)
        failed = total - successful

        error_types = {}
        for result in self.recovery_history:
            error_types[result.error_type] = error_types.get(result.error_type, 0) + 1

        return {
            "total_attempts": total,
            "successful": successful,
            "failed": failed,
            "error_types": error_types
        }

    def record_recovery_attempt(
        self,
        error_type: str,
        recovery_action: str,
        success: bool,
        details: str = ""
    ) -> None:
        """
        Record a recovery attempt.

        Args:
            error_type: Type of error
            recovery_action: Action taken
            success: Whether recovery succeeded
            details: Additional details
        """
        result = RecoveryResult(
            success=success,
            error_type=error_type,
            recovery_action=recovery_action,
            details=details
        )
        self.recovery_history.append(result)

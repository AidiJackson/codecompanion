from __future__ import annotations
from typing import Optional

from codecompanion.quality import run_quality_gate, QualityReport
from codecompanion.model_policy import ModelPolicy


class Orchestrator:
    """High-level orchestrator for CodeCompanion operations.

    Manages quality gates, model policy, and coordination between
    different agents and subsystems.
    """

    def __init__(self):
        """Initialize the orchestrator with model policy and quality tracking."""
        # Load model policy from configuration
        self.model_policy = ModelPolicy.load()

        # Track quality reports for operations
        self.last_quality_report: Optional[QualityReport] = None

    def run_quality_gate(self, diff_summary: str | None = None) -> QualityReport:
        """
        Run the (stubbed) quality gate for the current operation.

        In the future this will:
          - Run static analysis tools (ruff, pyright, pytest).
          - Optionally call an LLM to critique proposed changes.
          - Aggregate results into a comprehensive quality report.

        For now it delegates to codecompanion.quality.run_quality_gate().

        Args:
            diff_summary: Optional summary of changes being reviewed

        Returns:
            QualityReport with pass/fail status, issues, and notes
        """
        report = run_quality_gate(diff_summary=diff_summary)
        self.last_quality_report = report
        # In the future we may also store this in project state.
        return report

    def get_model_policy(self) -> ModelPolicy:
        """
        Return the currently loaded model policy to inform which LLMs are used
        for planners, architect, and specialists.

        Returns:
            ModelPolicy with mode, defaults, and routing rules
        """
        return self.model_policy

    def get_last_quality_report(self) -> Optional[QualityReport]:
        """
        Get the most recent quality report.

        Returns:
            The last QualityReport, or None if no quality gate has been run
        """
        return self.last_quality_report

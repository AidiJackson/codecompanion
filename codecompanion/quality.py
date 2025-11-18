from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class QualityReport:
    """Report from a quality gate check.

    Attributes:
        passed: Whether the quality check passed
        issues: List of problems found (empty if passed)
        notes: Additional information about the check
    """
    passed: bool
    issues: List[str]
    notes: List[str]


def run_quality_gate(diff_summary: str | None = None) -> QualityReport:
    """
    Stub for the future Quality Gate.

    In the future this will:
      - Run static tools (ruff/flake8, mypy, pytest, etc.).
      - Optionally call an LLM to critique the proposed change.
      - Aggregate results into a single QualityReport.

    For now, it always returns `passed=True` with a placeholder note.

    Args:
        diff_summary: Optional summary of changes being reviewed

    Returns:
        QualityReport indicating whether the quality gate passed
    """
    return QualityReport(
        passed=True,
        issues=[],
        notes=["Quality gate not yet implemented; stub passed by default."],
    )

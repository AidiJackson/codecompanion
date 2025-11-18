"""
Quality gates for code quality validation.

Provides quality checks and reporting for the codebase.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import json
from datetime import datetime


@dataclass
class QualityReport:
    """
    Report containing quality gate results.

    Attributes:
        timestamp: When the report was generated
        passed: Whether all quality gates passed
        score: Overall quality score (0-100)
        checks: Individual check results
        issues: List of issues found
    """

    timestamp: str
    passed: bool
    score: float
    checks: Dict[str, bool]
    issues: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class QualityGates:
    """
    Quality gates validator.

    Runs various quality checks and generates reports.
    """

    def __init__(self, state_file: str = ".codecompanion_state.json") -> None:
        """
        Initialize quality gates.

        Args:
            state_file: Path to the project state file
        """
        self.state_file = state_file
        self.state: Dict[str, Any] = {}
        self._load_state()

    def _load_state(self) -> None:
        """Load project state from file."""
        try:
            with open(self.state_file, "r") as f:
                self.state = json.load(f)
        except FileNotFoundError:
            self.state = {"initialized": False}
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse state file: {e}")
            self.state = {"initialized": False}

    def _save_state(self) -> None:
        """Save project state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Error: Failed to save state: {e}")

    def run_quality_checks(self) -> int:
        """
        Run all quality checks and generate report.

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        print("[quality] Running quality checks...")

        # Run individual checks
        checks = {
            "architecture_defined": self._check_architecture(),
            "specialists_run": self._check_specialists(),
            "project_initialized": self._check_initialization(),
        }

        # Collect issues
        issues: List[str] = []
        if not checks["project_initialized"]:
            issues.append("Project not initialized - run 'cc init'")
        if not checks["architecture_defined"]:
            issues.append("Architecture not defined - run 'cc run architect'")
        if not checks["specialists_run"]:
            issues.append("No specialists have been run - try 'cc run specialist --type <type>'")

        # Calculate score
        passed_checks = sum(1 for check in checks.values() if check)
        total_checks = len(checks)
        score = (passed_checks / total_checks * 100) if total_checks > 0 else 0.0

        # Create report
        report = QualityReport(
            timestamp=datetime.now().isoformat(),
            passed=all(checks.values()),
            score=score,
            checks=checks,
            issues=issues,
        )

        # Save report to state
        if "quality_reports" not in self.state:
            self.state["quality_reports"] = []

        self.state["quality_reports"].append(report.to_dict())

        # Keep only last 10 reports
        if len(self.state["quality_reports"]) > 10:
            self.state["quality_reports"] = self.state["quality_reports"][-10:]

        self._save_state()

        # Print report
        self._print_report(report)

        return 0 if report.passed else 1

    def _check_architecture(self) -> bool:
        """Check if architecture is defined."""
        return bool(self.state.get("architecture", {}))

    def _check_specialists(self) -> bool:
        """Check if any specialists have been run."""
        return len(self.state.get("specialists_run", [])) > 0

    def _check_initialization(self) -> bool:
        """Check if project is initialized."""
        return self.state.get("initialized", False)

    def _print_report(self, report: QualityReport) -> None:
        """
        Print quality report to console.

        Args:
            report: Quality report to print
        """
        print("\n" + "=" * 60)
        print("QUALITY REPORT")
        print("=" * 60)
        print(f"Timestamp: {report.timestamp}")
        print(f"Overall Score: {report.score:.1f}/100")
        print(f"Status: {'PASSED' if report.passed else 'FAILED'}")
        print()
        print("Checks:")
        for check_name, passed in report.checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")
        print()

        if report.issues:
            print("Issues Found:")
            for issue in report.issues:
                print(f"  • {issue}")
            print()

        print("=" * 60)

    def get_latest_report(self) -> Optional[QualityReport]:
        """
        Get the most recent quality report.

        Returns:
            Latest quality report or None if no reports exist
        """
        reports = self.state.get("quality_reports", [])
        if not reports:
            return None

        latest = reports[-1]
        return QualityReport(**latest)

    def print_latest_report(self) -> int:
        """
        Print the most recent quality report.

        Returns:
            Exit code (0 for success, 1 if no report exists)
        """
        report = self.get_latest_report()
        if report is None:
            print("[quality] No quality reports found")
            print("[quality] Run 'cc quality' to generate a report")
            return 1

        self._print_report(report)
        return 0

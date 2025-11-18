"""
File-based run history and error timeline management.
Provides read-only access to pipeline execution records and error logs.
"""
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class RunRecord:
    """Represents a single pipeline run execution."""
    timestamp: str  # ISO 8601 format
    project_root: str
    branch: Optional[str] = None
    agents_run: list = None  # List of agent names/roles
    status: str = "success"  # "success" | "failure" | "partial"
    summary: str = ""

    def __post_init__(self):
        if self.agents_run is None:
            self.agents_run = []


@dataclass
class ErrorRecord:
    """Represents a single error occurrence during pipeline execution."""
    timestamp: str  # ISO 8601 format
    agent: Optional[str] = None  # Which agent failed
    stage: Optional[str] = None  # e.g. "analysis", "fix", "test"
    message: str = ""  # Short error summary
    recovered: bool = False
    details: Optional[str] = None  # Optional additional context


def load_run_history(path: Path) -> list:
    """
    Load run history from JSON file.

    Args:
        path: Path to run_history.json

    Returns:
        List of RunRecord objects, empty list if file doesn't exist or is malformed
    """
    if not path.exists():
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate that data is a list
        if not isinstance(data, list):
            print(f"[history] Warning: {path} is not a list, returning empty history")
            return []

        # Convert dicts to RunRecord objects (best effort)
        records = []
        for item in data:
            if isinstance(item, dict):
                try:
                    # Use only fields that RunRecord knows about
                    record = RunRecord(
                        timestamp=item.get('timestamp', ''),
                        project_root=item.get('project_root', ''),
                        branch=item.get('branch'),
                        agents_run=item.get('agents_run', []),
                        status=item.get('status', 'unknown'),
                        summary=item.get('summary', ''),
                    )
                    records.append(record)
                except (TypeError, ValueError) as e:
                    # Skip malformed records
                    print(f"[history] Warning: Skipping malformed run record: {e}")
                    continue

        return records

    except (json.JSONDecodeError, IOError) as e:
        print(f"[history] Warning: Failed to load {path}: {e}")
        return []


def load_error_timeline(path: Path) -> list:
    """
    Load error timeline from JSON file.

    Args:
        path: Path to error_timeline.json

    Returns:
        List of ErrorRecord objects, empty list if file doesn't exist or is malformed
    """
    if not path.exists():
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate that data is a list
        if not isinstance(data, list):
            print(f"[history] Warning: {path} is not a list, returning empty timeline")
            return []

        # Convert dicts to ErrorRecord objects (best effort)
        records = []
        for item in data:
            if isinstance(item, dict):
                try:
                    # Use only fields that ErrorRecord knows about
                    record = ErrorRecord(
                        timestamp=item.get('timestamp', ''),
                        agent=item.get('agent'),
                        stage=item.get('stage'),
                        message=item.get('message', ''),
                        recovered=item.get('recovered', False),
                        details=item.get('details'),
                    )
                    records.append(record)
                except (TypeError, ValueError) as e:
                    # Skip malformed records
                    print(f"[history] Warning: Skipping malformed error record: {e}")
                    continue

        return records

    except (json.JSONDecodeError, IOError) as e:
        print(f"[history] Warning: Failed to load {path}: {e}")
        return []

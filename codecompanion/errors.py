"""Error tracking and logging for CodeCompanion."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ErrorRecord:
    """Record of an error that occurred during agent execution."""

    timestamp: str
    agent: str
    stage: str
    error_type: str
    message: str
    recovered: bool = False
    used_fallback: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class ErrorLogger:
    """Logger for tracking errors during pipeline execution."""

    def __init__(self, log_file: str = ".cc/error_log.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_error(self, record: ErrorRecord) -> None:
        """Log an error record to the error log file."""
        # Load existing errors
        errors = []
        if self.log_file.exists():
            try:
                with open(self.log_file, "r") as f:
                    errors = json.load(f)
            except (json.JSONDecodeError, OSError):
                errors = []

        # Append new error
        errors.append(record.to_dict())

        # Write back
        with open(self.log_file, "w") as f:
            json.dump(errors, f, indent=2)

    def get_errors(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Retrieve error records from the log file."""
        if not self.log_file.exists():
            return []

        try:
            with open(self.log_file, "r") as f:
                errors = json.load(f)
            if limit:
                return errors[-limit:]
            return errors
        except (json.JSONDecodeError, OSError):
            return []

    def clear_log(self) -> None:
        """Clear the error log file."""
        if self.log_file.exists():
            self.log_file.unlink()


def create_error_record(
    agent: str,
    stage: str,
    error_type: str,
    message: str,
    recovered: bool = False,
    used_fallback: bool = False,
    **details: Any,
) -> ErrorRecord:
    """Create an error record with current timestamp."""
    return ErrorRecord(
        timestamp=datetime.now().isoformat(),
        agent=agent,
        stage=stage,
        error_type=error_type,
        message=message,
        recovered=recovered,
        used_fallback=used_fallback,
        details=details,
    )

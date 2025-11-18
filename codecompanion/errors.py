"""
Centralized error logging and retrieval for CodeCompanion.

Provides persistent error tracking across agent execution with
structured logging to .cc/error_log.json.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Optional filelock for thread-safe appends
try:
    from filelock import FileLock, Timeout

    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False


# Error severity levels
WARNING = "warning"
ERROR = "error"


@dataclass
class ErrorRecord:
    """A single error record in the error log."""

    timestamp: str
    """ISO timestamp of when the error occurred."""

    agent: str
    """Name of the agent that encountered the error."""

    stage: str
    """Workflow stage (e.g., 'workflow.analyze', 'setup', 'execution')."""

    message: str
    """Human-readable error message."""

    severity: str
    """Error severity: 'warning' or 'error'."""

    recovered: bool
    """Was the error successfully recovered from?"""

    details: Optional[dict[str, Any]] = None
    """Additional error context and metadata."""


def get_error_log_path(project_root: str = ".") -> Path:
    """Get the path to the error log file."""
    return Path(project_root) / ".cc" / "error_log.json"


def get_lock_path(project_root: str = ".") -> Path:
    """Get the path to the error log lock file."""
    return Path(project_root) / ".cc" / "error_log.lock"


def load_error_log(path: Optional[Path | str] = None) -> list[ErrorRecord]:
    """
    Load the error log from disk.

    Args:
        path: Path to error log file (default: .cc/error_log.json)

    Returns:
        List of ErrorRecord objects (empty list if file doesn't exist)
    """
    if path is None:
        path = get_error_log_path()
    else:
        path = Path(path)

    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert dicts to ErrorRecord objects
        records = []
        for item in data:
            records.append(
                ErrorRecord(
                    timestamp=item["timestamp"],
                    agent=item["agent"],
                    stage=item["stage"],
                    message=item["message"],
                    severity=item["severity"],
                    recovered=item["recovered"],
                    details=item.get("details"),
                )
            )
        return records

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # Log corruption - return empty list and warn
        print(f"[warning] Error log corrupted: {e}")
        return []


def save_error_log(
    records: list[ErrorRecord], path: Optional[Path | str] = None
) -> None:
    """
    Save the error log to disk.

    Args:
        records: List of ErrorRecord objects to save
        path: Path to error log file (default: .cc/error_log.json)
    """
    if path is None:
        path = get_error_log_path()
    else:
        path = Path(path)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert ErrorRecord objects to dicts
    data = [asdict(record) for record in records]

    # Write atomically using temp file + rename
    temp_path = path.with_suffix(".json.tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic rename
        temp_path.replace(path)

    except Exception as e:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise e


def append_error(record: ErrorRecord, path: Optional[Path | str] = None) -> None:
    """
    Append a single error record to the error log.

    Thread-safe via file locking (if filelock is available).

    Args:
        record: ErrorRecord to append
        path: Path to error log file (default: .cc/error_log.json)
    """
    if path is None:
        path = get_error_log_path()
        lock_path = get_lock_path()
    else:
        path = Path(path)
        lock_path = path.with_suffix(".lock")

    # Ensure .cc directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Use file locking for thread safety if available
    if FILELOCK_AVAILABLE:
        lock = FileLock(str(lock_path), timeout=5)
        try:
            with lock:
                # Load existing records
                records = load_error_log(path)

                # Append new record
                records.append(record)

                # Save back
                save_error_log(records, path)

        except Timeout:
            # Lock timeout - log warning and skip append
            print(f"[warning] Could not acquire lock on error log: {lock_path}")
    else:
        # No filelock available - simple append (not thread-safe)
        # Load existing records
        records = load_error_log(path)

        # Append new record
        records.append(record)

        # Save back
        save_error_log(records, path)


def create_error_record(
    agent: str,
    stage: str,
    message: str,
    severity: str = ERROR,
    recovered: bool = False,
    details: Optional[dict[str, Any]] = None,
) -> ErrorRecord:
    """
    Create a new ErrorRecord with current timestamp.

    Args:
        agent: Name of the agent
        stage: Workflow stage
        message: Human-readable error message
        severity: 'warning' or 'error'
        recovered: Was the error recovered from?
        details: Additional error context

    Returns:
        New ErrorRecord object
    """
    return ErrorRecord(
        timestamp=datetime.now().isoformat(),
        agent=agent,
        stage=stage,
        message=message,
        severity=severity,
        recovered=recovered,
        details=details,
    )


def clear_error_log(path: Optional[Path | str] = None) -> None:
    """
    Clear the error log (useful for testing).

    Args:
        path: Path to error log file (default: .cc/error_log.json)
    """
    if path is None:
        path = get_error_log_path()
    else:
        path = Path(path)

    if path.exists():
        path.unlink()


def get_error_summary(path: Optional[Path | str] = None) -> dict[str, Any]:
    """
    Get a summary of errors in the log.

    Returns:
        Dict with counts and recent errors:
        {
            "total": int,
            "unrecovered": int,
            "recovered": int,
            "by_agent": dict[str, int],
            "recent": list[ErrorRecord]  # Last 5 errors
        }
    """
    records = load_error_log(path)

    unrecovered = [r for r in records if not r.recovered]
    recovered = [r for r in records if r.recovered]

    # Count by agent
    by_agent = {}
    for r in records:
        by_agent[r.agent] = by_agent.get(r.agent, 0) + 1

    return {
        "total": len(records),
        "unrecovered": len(unrecovered),
        "recovered": len(recovered),
        "by_agent": by_agent,
        "recent": records[-5:] if records else [],  # Last 5 errors
    }

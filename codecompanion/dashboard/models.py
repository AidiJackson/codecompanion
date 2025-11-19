"""
Data models and storage for CodeCompanion async job execution.

This module provides:
- Job/Run data model with status tracking
- SQLite-based persistent storage
- Thread-safe database operations
"""
import sqlite3
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, asdict
from contextlib import contextmanager


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"      # Queued but not started
    RUNNING = "running"      # Currently executing
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"        # Finished with error
    CANCELLED = "cancelled"  # User cancelled


class JobMode(str, Enum):
    """Job execution mode."""
    CHAT = "chat"          # Single LLM chat turn
    AUTO = "auto"          # Full 9-agent pipeline
    AGENT = "agent"        # Single agent execution
    TASK = "task"          # Natural language task


@dataclass
class Job:
    """
    Represents an async CodeCompanion job/run.

    Attributes:
        id: Unique job identifier (UUID)
        mode: Execution mode (chat, auto, agent, task)
        input: User input/instruction
        agent_name: Optional agent name (for mode=agent)
        provider: LLM provider (claude, gpt4, gemini)
        target_root: Target repository root path
        status: Current job status
        created_at: ISO timestamp when job was created
        started_at: ISO timestamp when execution started (optional)
        finished_at: ISO timestamp when execution finished (optional)
        output: Captured stdout/stderr (optional)
        error: Error message if failed (optional)
        exit_code: Process exit code (optional)
        can_cancel: Whether job can be cancelled
    """
    id: str
    mode: JobMode
    input: str
    agent_name: Optional[str]
    provider: str
    target_root: str
    status: JobStatus
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    can_cancel: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Job':
        """Create Job from dictionary."""
        # Convert string enums back to enum types
        if isinstance(data.get('mode'), str):
            data['mode'] = JobMode(data['mode'])
        if isinstance(data.get('status'), str):
            data['status'] = JobStatus(data['status'])
        return Job(**data)


class JobStore:
    """
    Thread-safe SQLite-based storage for jobs.

    Stores job metadata and execution results with persistence
    across dashboard restarts.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize job store.

        Args:
            db_path: Path to SQLite database file. Defaults to .cc/jobs.db
        """
        if db_path is None:
            # Default to .cc/jobs.db in current directory
            db_path = Path.cwd() / ".cc" / "jobs.db"

        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    input TEXT NOT NULL,
                    agent_name TEXT,
                    provider TEXT NOT NULL,
                    target_root TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    output TEXT,
                    error TEXT,
                    exit_code INTEGER,
                    can_cancel INTEGER DEFAULT 1
                )
            """)

            # Create index on created_at for efficient sorting
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_created_at
                ON jobs(created_at DESC)
            """)

            # Create index on status for filtering
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status
                ON jobs(status)
            """)

            conn.commit()

    @contextmanager
    def _get_conn(self):
        """Get thread-safe database connection."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            try:
                yield conn
            finally:
                conn.close()

    def create(self, job: Job) -> Job:
        """
        Create a new job in the database.

        Args:
            job: Job to create

        Returns:
            Created job
        """
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO jobs (
                    id, mode, input, agent_name, provider, target_root,
                    status, created_at, started_at, finished_at,
                    output, error, exit_code, can_cancel
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.id,
                job.mode.value,
                job.input,
                job.agent_name,
                job.provider,
                job.target_root,
                job.status.value,
                job.created_at,
                job.started_at,
                job.finished_at,
                job.output,
                job.error,
                job.exit_code,
                1 if job.can_cancel else 0,
            ))
            conn.commit()

        return job

    def get(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job if found, None otherwise
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE id = ?",
                (job_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_job(row)

    def list(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Job]:
        """
        List jobs with optional filtering.

        Args:
            status: Filter by status (optional)
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of jobs sorted by created_at DESC
        """
        with self._get_conn() as conn:
            if status is not None:
                cursor = conn.execute("""
                    SELECT * FROM jobs
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (status.value, limit, offset))
            else:
                cursor = conn.execute("""
                    SELECT * FROM jobs
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

            rows = cursor.fetchall()
            return [self._row_to_job(row) for row in rows]

    def update(self, job: Job) -> Job:
        """
        Update existing job.

        Args:
            job: Job with updated fields

        Returns:
            Updated job
        """
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE jobs SET
                    mode = ?,
                    input = ?,
                    agent_name = ?,
                    provider = ?,
                    target_root = ?,
                    status = ?,
                    created_at = ?,
                    started_at = ?,
                    finished_at = ?,
                    output = ?,
                    error = ?,
                    exit_code = ?,
                    can_cancel = ?
                WHERE id = ?
            """, (
                job.mode.value,
                job.input,
                job.agent_name,
                job.provider,
                job.target_root,
                job.status.value,
                job.created_at,
                job.started_at,
                job.finished_at,
                job.output,
                job.error,
                job.exit_code,
                1 if job.can_cancel else 0,
                job.id,
            ))
            conn.commit()

        return job

    def delete(self, job_id: str) -> bool:
        """
        Delete job by ID.

        Args:
            job_id: Job ID

        Returns:
            True if job was deleted, False if not found
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM jobs WHERE id = ?",
                (job_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def count(self, status: Optional[JobStatus] = None) -> int:
        """
        Count jobs with optional filtering.

        Args:
            status: Filter by status (optional)

        Returns:
            Number of jobs
        """
        with self._get_conn() as conn:
            if status is not None:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM jobs WHERE status = ?",
                    (status.value,)
                )
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM jobs")

            return cursor.fetchone()[0]

    def _row_to_job(self, row: sqlite3.Row) -> Job:
        """Convert database row to Job object."""
        return Job(
            id=row['id'],
            mode=JobMode(row['mode']),
            input=row['input'],
            agent_name=row['agent_name'],
            provider=row['provider'],
            target_root=row['target_root'],
            status=JobStatus(row['status']),
            created_at=row['created_at'],
            started_at=row['started_at'],
            finished_at=row['finished_at'],
            output=row['output'],
            error=row['error'],
            exit_code=row['exit_code'],
            can_cancel=bool(row['can_cancel']),
        )


# Global job store instance (singleton)
_job_store: Optional[JobStore] = None


def get_job_store(db_path: Optional[Path] = None) -> JobStore:
    """
    Get global job store instance.

    Args:
        db_path: Optional path to database file

    Returns:
        JobStore instance
    """
    global _job_store

    if _job_store is None:
        _job_store = JobStore(db_path)

    return _job_store

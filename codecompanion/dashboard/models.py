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
class Session:
    """
    Represents a grouping of related jobs.

    Sessions allow grouping jobs that are part of the same workflow
    or initiated from the same context.

    Attributes:
        id: Unique session identifier (UUID)
        name: Human-readable session name
        created_at: ISO timestamp when session was created
        updated_at: ISO timestamp when session was last updated
        total_jobs: Total number of jobs in this session
        completed_jobs: Number of completed jobs
        total_cost: Total estimated cost across all jobs (USD)
        total_tokens: Total tokens used across all jobs
    """
    id: str
    name: str
    created_at: str
    updated_at: str
    total_jobs: int = 0
    completed_jobs: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Session':
        """Create Session from dictionary."""
        return Session(**data)


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
        session_id: Optional session ID for grouping related jobs
        input_tokens: Estimated input tokens used
        output_tokens: Estimated output tokens used
        total_tokens: Total tokens (input + output)
        estimated_cost: Estimated cost in USD
        model_used: Specific model used (e.g., claude-3-sonnet-20240229)
        process_id: Process ID of running subprocess (if any)
        cancellation_mode: Mode used for cancellation (graceful/forced)
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
    session_id: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    model_used: Optional[str] = None
    process_id: Optional[int] = None
    cancellation_mode: Optional[str] = None

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
        """Initialize database schema with migrations."""
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_conn() as conn:
            # Create jobs table with all fields
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
                    can_cancel INTEGER DEFAULT 1,
                    session_id TEXT,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    estimated_cost REAL DEFAULT 0.0,
                    model_used TEXT,
                    process_id INTEGER,
                    cancellation_mode TEXT
                )
            """)

            # Migrate existing tables (add new columns if they don't exist)
            self._migrate_schema(conn)

            # Create sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    total_jobs INTEGER DEFAULT 0,
                    completed_jobs INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    total_tokens INTEGER DEFAULT 0
                )
            """)

            # Create indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_created_at
                ON jobs(created_at DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status
                ON jobs(status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_session_id
                ON jobs(session_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_created_at
                ON sessions(created_at DESC)
            """)

            conn.commit()

    def _migrate_schema(self, conn):
        """Add new columns to existing tables if they don't exist."""
        # Get existing columns
        cursor = conn.execute("PRAGMA table_info(jobs)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Add new columns if they don't exist
        new_columns = {
            'session_id': 'TEXT',
            'input_tokens': 'INTEGER DEFAULT 0',
            'output_tokens': 'INTEGER DEFAULT 0',
            'total_tokens': 'INTEGER DEFAULT 0',
            'estimated_cost': 'REAL DEFAULT 0.0',
            'model_used': 'TEXT',
            'process_id': 'INTEGER',
            'cancellation_mode': 'TEXT'
        }

        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    conn.execute(f"ALTER TABLE jobs ADD COLUMN {column_name} {column_type}")
                except sqlite3.OperationalError:
                    # Column might already exist due to race condition
                    pass

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
                    output, error, exit_code, can_cancel,
                    session_id, input_tokens, output_tokens, total_tokens,
                    estimated_cost, model_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                job.session_id,
                job.input_tokens,
                job.output_tokens,
                job.total_tokens,
                job.estimated_cost,
                job.model_used,
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
                    can_cancel = ?,
                    session_id = ?,
                    input_tokens = ?,
                    output_tokens = ?,
                    total_tokens = ?,
                    estimated_cost = ?,
                    model_used = ?
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
                job.session_id,
                job.input_tokens,
                job.output_tokens,
                job.total_tokens,
                job.estimated_cost,
                job.model_used,
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
            session_id=row['session_id'] if 'session_id' in row.keys() else None,
            input_tokens=row['input_tokens'] if 'input_tokens' in row.keys() else 0,
            output_tokens=row['output_tokens'] if 'output_tokens' in row.keys() else 0,
            total_tokens=row['total_tokens'] if 'total_tokens' in row.keys() else 0,
            estimated_cost=row['estimated_cost'] if 'estimated_cost' in row.keys() else 0.0,
            model_used=row['model_used'] if 'model_used' in row.keys() else None,
            process_id=row['process_id'] if 'process_id' in row.keys() else None,
            cancellation_mode=row['cancellation_mode'] if 'cancellation_mode' in row.keys() else None,
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

# ==============================================================================
# Session Store
# ==============================================================================


class SessionStore:
    """
    Thread-safe SQLite-based storage for sessions.

    Manages session grouping and aggregated metrics.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize session store.

        Args:
            db_path: Path to SQLite database file (uses same as JobStore)
        """
        if db_path is None:
            db_path = Path.cwd() / ".cc" / "jobs.db"

        self.db_path = db_path
        self._lock = threading.Lock()

    @contextmanager
    def _get_conn(self):
        """Get thread-safe database connection."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def create(self, session: Session) -> Session:
        """Create a new session."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO sessions (
                    id, name, created_at, updated_at,
                    total_jobs, completed_jobs, total_cost, total_tokens
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id,
                session.name,
                session.created_at,
                session.updated_at,
                session.total_jobs,
                session.completed_jobs,
                session.total_cost,
                session.total_tokens,
            ))
            conn.commit()

        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_session(row)

    def list(self, limit: int = 100, offset: int = 0) -> List[Session]:
        """List sessions sorted by updated_at DESC."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM sessions
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            rows = cursor.fetchall()
            return [self._row_to_session(row) for row in rows]

    def update(self, session: Session) -> Session:
        """Update existing session."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE sessions SET
                    name = ?,
                    updated_at = ?,
                    total_jobs = ?,
                    completed_jobs = ?,
                    total_cost = ?,
                    total_tokens = ?
                WHERE id = ?
            """, (
                session.name,
                session.updated_at,
                session.total_jobs,
                session.completed_jobs,
                session.total_cost,
                session.total_tokens,
                session.id,
            ))
            conn.commit()

        return session

    def delete(self, session_id: str) -> bool:
        """Delete session by ID."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE id = ?",
                (session_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def count(self) -> int:
        """Count total sessions."""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM sessions")
            return cursor.fetchone()[0]

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        """Convert database row to Session object."""
        return Session(
            id=row['id'],
            name=row['name'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            total_jobs=row['total_jobs'],
            completed_jobs=row['completed_jobs'],
            total_cost=row['total_cost'],
            total_tokens=row['total_tokens'],
        )


# Global session store instance (singleton)
_session_store: Optional[SessionStore] = None


def get_session_store(db_path: Optional[Path] = None) -> SessionStore:
    """
    Get global session store instance.

    Args:
        db_path: Optional path to database file

    Returns:
        SessionStore instance
    """
    global _session_store

    if _session_store is None:
        _session_store = SessionStore(db_path)

    return _session_store


# ==============================================================================
# Token Estimation and Cost Calculation
# ==============================================================================


# Provider pricing (USD per 1M tokens)
PROVIDER_PRICING = {
    'claude': {
        'input': 3.0,
        'output': 15.0,
        'models': {
            'claude-3-sonnet-20240229': {'input': 3.0, 'output': 15.0},
            'claude-3-opus-20240229': {'input': 15.0, 'output': 75.0},
            'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25},
        }
    },
    'gpt4': {
        'input': 10.0,
        'output': 30.0,
        'models': {
            'gpt-4': {'input': 30.0, 'output': 60.0},
            'gpt-4-turbo': {'input': 10.0, 'output': 30.0},
            'gpt-3.5-turbo': {'input': 0.5, 'output': 1.5},
        }
    },
    'gemini': {
        'input': 1.25,
        'output': 5.0,
        'models': {
            'gemini-pro': {'input': 1.25, 'output': 5.0},
            'gemini-ultra': {'input': 2.5, 'output': 10.0},
        }
    }
}


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses simple character-based estimation: 1 token ≈ 4 characters.
    This is a rough approximation for planning purposes.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    # Simple estimation: 1 token ≈ 4 characters
    return max(1, len(text) // 4)


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    provider: str,
    model: Optional[str] = None
) -> float:
    """
    Calculate estimated cost in USD.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        provider: Provider name (claude, gpt4, gemini)
        model: Optional specific model name

    Returns:
        Estimated cost in USD
    """
    if provider not in PROVIDER_PRICING:
        return 0.0

    pricing = PROVIDER_PRICING[provider]

    # Try to use specific model pricing
    if model and 'models' in pricing:
        for model_key, model_pricing in pricing['models'].items():
            if model_key in model.lower() if model else False:
                pricing = model_pricing
                break

    # Calculate cost per million tokens
    input_cost = (input_tokens / 1_000_000) * pricing.get('input', 0.0)
    output_cost = (output_tokens / 1_000_000) * pricing.get('output', 0.0)

    return input_cost + output_cost


def estimate_job_cost(job: Job) -> float:
    """
    Estimate cost for a job based on input/output.

    Args:
        job: Job object

    Returns:
        Estimated cost in USD
    """
    if job.estimated_cost > 0:
        return job.estimated_cost

    input_tokens = estimate_tokens(job.input)
    output_tokens = estimate_tokens(job.output or "")

    return calculate_cost(
        input_tokens,
        output_tokens,
        job.provider,
        job.model_used
    )


def update_job_metrics(job: Job) -> Job:
    """
    Update job token and cost metrics.

    Args:
        job: Job object to update

    Returns:
        Updated job with calculated metrics
    """
    if job.input_tokens == 0:
        job.input_tokens = estimate_tokens(job.input)

    if job.output_tokens == 0 and job.output:
        job.output_tokens = estimate_tokens(job.output)

    job.total_tokens = job.input_tokens + job.output_tokens

    if job.estimated_cost == 0.0:
        job.estimated_cost = calculate_cost(
            job.input_tokens,
            job.output_tokens,
            job.provider,
            job.model_used
        )

    return job


class BudgetPeriod(str, Enum):
    """Budget period types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SESSION = "session"      # Per-session limit
    TOTAL = "total"          # Total limit (no reset)


@dataclass
class Budget:
    """
    Represents a spending budget with alerts.

    Budgets can be set for different time periods or per-session.
    Alerts are triggered when spending reaches threshold percentages.

    Attributes:
        id: Unique budget identifier
        name: Human-readable budget name
        period: Budget period (daily, weekly, monthly, session, total)
        limit: Maximum spending limit in USD
        current_spending: Current spending in period
        alert_threshold: Alert when spending reaches this percentage (0-100)
        enabled: Whether budget is active
        created_at: ISO timestamp when budget was created
        period_start: ISO timestamp when current period started
        period_end: ISO timestamp when current period ends (for time-based budgets)
        last_alert_at: ISO timestamp of last alert sent
    """
    id: str
    name: str
    period: BudgetPeriod
    limit: float
    current_spending: float = 0.0
    alert_threshold: float = 80.0
    enabled: bool = True
    created_at: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    last_alert_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Budget':
        """Create Budget from dictionary."""
        if isinstance(data.get('period'), str):
            data['period'] = BudgetPeriod(data['period'])
        return Budget(**data)

    def usage_percentage(self) -> float:
        """Calculate usage as percentage of limit."""
        if self.limit <= 0:
            return 0.0
        return (self.current_spending / self.limit) * 100.0

    def remaining(self) -> float:
        """Calculate remaining budget."""
        return max(0.0, self.limit - self.current_spending)

    def is_exceeded(self) -> bool:
        """Check if budget is exceeded."""
        return self.current_spending >= self.limit

    def should_alert(self) -> bool:
        """Check if alert threshold is reached."""
        return self.usage_percentage() >= self.alert_threshold


class BudgetStore:
    """
    Thread-safe SQLite-based storage for budgets.

    Stores budget configurations and tracks spending per period.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize budget store.

        Args:
            db_path: Path to SQLite database file. Uses same DB as jobs
        """
        if db_path is None:
            db_path = Path.cwd() / ".cc" / "jobs.db"

        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    period TEXT NOT NULL,
                    limit_amount REAL NOT NULL,
                    current_spending REAL DEFAULT 0.0,
                    alert_threshold REAL DEFAULT 80.0,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    period_start TEXT,
                    period_end TEXT,
                    last_alert_at TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_budgets_period
                ON budgets(period)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_budgets_enabled
                ON budgets(enabled)
            """)

            conn.commit()

    @contextmanager
    def _get_conn(self):
        """Get thread-safe database connection."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def create(self, budget: Budget) -> Budget:
        """Create a new budget."""
        if not budget.created_at:
            budget.created_at = datetime.utcnow().isoformat() + "Z"

        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO budgets (
                    id, name, period, limit_amount, current_spending,
                    alert_threshold, enabled, created_at, period_start,
                    period_end, last_alert_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                budget.id,
                budget.name,
                budget.period.value,
                budget.limit,
                budget.current_spending,
                budget.alert_threshold,
                int(budget.enabled),
                budget.created_at,
                budget.period_start,
                budget.period_end,
                budget.last_alert_at
            ))
            conn.commit()

        return budget

    def get(self, budget_id: str) -> Optional[Budget]:
        """Get budget by ID."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM budgets WHERE id = ?",
                (budget_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_budget(row)
            return None

    def list(
        self,
        period: Optional[BudgetPeriod] = None,
        enabled_only: bool = False
    ) -> List[Budget]:
        """List budgets with optional filters."""
        with self._get_conn() as conn:
            query = "SELECT * FROM budgets WHERE 1=1"
            params = []

            if period:
                query += " AND period = ?"
                params.append(period.value)

            if enabled_only:
                query += " AND enabled = 1"

            query += " ORDER BY created_at DESC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_budget(row) for row in rows]

    def update(self, budget: Budget) -> Budget:
        """Update existing budget."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE budgets
                SET name = ?, period = ?, limit_amount = ?, current_spending = ?,
                    alert_threshold = ?, enabled = ?, period_start = ?,
                    period_end = ?, last_alert_at = ?
                WHERE id = ?
            """, (
                budget.name,
                budget.period.value,
                budget.limit,
                budget.current_spending,
                budget.alert_threshold,
                int(budget.enabled),
                budget.period_start,
                budget.period_end,
                budget.last_alert_at,
                budget.id
            ))
            conn.commit()

        return budget

    def delete(self, budget_id: str) -> bool:
        """Delete budget by ID."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM budgets WHERE id = ?",
                (budget_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def add_spending(self, budget_id: str, amount: float) -> Optional[Budget]:
        """
        Add spending to a budget.

        Args:
            budget_id: Budget ID
            amount: Amount to add to current_spending

        Returns:
            Updated budget or None if not found
        """
        budget = self.get(budget_id)
        if not budget:
            return None

        budget.current_spending += amount
        return self.update(budget)

    def reset_period(self, budget_id: str) -> Optional[Budget]:
        """
        Reset budget period spending.

        Sets current_spending to 0 and updates period_start.

        Args:
            budget_id: Budget ID

        Returns:
            Updated budget or None if not found
        """
        budget = self.get(budget_id)
        if not budget:
            return None

        budget.current_spending = 0.0
        budget.period_start = datetime.utcnow().isoformat() + "Z"

        # Calculate period_end based on period type
        if budget.period == BudgetPeriod.DAILY:
            from datetime import timedelta
            end = datetime.utcnow() + timedelta(days=1)
            budget.period_end = end.isoformat() + "Z"
        elif budget.period == BudgetPeriod.WEEKLY:
            from datetime import timedelta
            end = datetime.utcnow() + timedelta(weeks=1)
            budget.period_end = end.isoformat() + "Z"
        elif budget.period == BudgetPeriod.MONTHLY:
            from datetime import timedelta
            end = datetime.utcnow() + timedelta(days=30)
            budget.period_end = end.isoformat() + "Z"

        return self.update(budget)

    def check_budgets(self, cost: float) -> Dict[str, Any]:
        """
        Check if adding cost would exceed any active budgets.

        Args:
            cost: Cost to check

        Returns:
            Dict with:
              - exceeded: List of exceeded budget IDs
              - warnings: List of budget IDs reaching alert threshold
              - allowed: Boolean, whether cost can be added
        """
        exceeded = []
        warnings = []

        budgets = self.list(enabled_only=True)

        for budget in budgets:
            if budget.period == BudgetPeriod.SESSION:
                continue  # Session budgets checked separately

            projected_spending = budget.current_spending + cost

            if projected_spending > budget.limit:
                exceeded.append(budget.id)
            elif (projected_spending / budget.limit * 100.0) >= budget.alert_threshold:
                if budget.usage_percentage() < budget.alert_threshold:
                    warnings.append(budget.id)

        return {
            'exceeded': exceeded,
            'warnings': warnings,
            'allowed': len(exceeded) == 0
        }

    def _row_to_budget(self, row: sqlite3.Row) -> Budget:
        """Convert database row to Budget object."""
        return Budget(
            id=row['id'],
            name=row['name'],
            period=BudgetPeriod(row['period']),
            limit=row['limit_amount'],
            current_spending=row['current_spending'],
            alert_threshold=row['alert_threshold'],
            enabled=bool(row['enabled']),
            created_at=row['created_at'],
            period_start=row['period_start'],
            period_end=row['period_end'],
            last_alert_at=row['last_alert_at']
        )


# Global budget store instance (singleton)
_budget_store: Optional[BudgetStore] = None


def get_budget_store(db_path: Optional[Path] = None) -> BudgetStore:
    """
    Get global budget store instance.

    Args:
        db_path: Optional path to database file

    Returns:
        BudgetStore instance
    """
    global _budget_store

    if _budget_store is None:
        _budget_store = BudgetStore(db_path=db_path)

    return _budget_store

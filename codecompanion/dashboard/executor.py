"""
Background job executor for CodeCompanion async runs.

This module provides:
- ThreadPoolExecutor-based async job execution
- Output streaming with real-time capture
- Cancellation support
- Thread-safe job management
"""
import os
import sys
import uuid
import threading
import queue
import io
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Callable
from contextlib import redirect_stdout, redirect_stderr

from .models import Job, JobStatus, JobMode, JobStore, get_job_store, update_job_metrics


class CancellationToken:
    """Thread-safe cancellation token."""

    def __init__(self):
        self._cancelled = threading.Event()

    def cancel(self):
        """Mark as cancelled."""
        self._cancelled.set()

    def is_cancelled(self) -> bool:
        """Check if cancelled."""
        return self._cancelled.is_set()


class OutputCapture:
    """Captures stdout/stderr with real-time streaming support."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self._buffer = io.StringIO()
        self._lock = threading.Lock()

    def write(self, text: str):
        """Write text to buffer."""
        with self._lock:
            self._buffer.write(text)

    def getvalue(self) -> str:
        """Get current buffer contents."""
        with self._lock:
            return self._buffer.getvalue()

    def flush(self):
        """Flush buffer (no-op for StringIO)."""
        pass


class JobExecutor:
    """
    Manages async job execution with background thread pool.

    Features:
    - Parallel job execution with configurable worker pool
    - Real-time output capture
    - Cancellation support
    - Automatic status updates to JobStore
    """

    def __init__(
        self,
        max_workers: int = 4,
        job_store: Optional[JobStore] = None
    ):
        """
        Initialize job executor.

        Args:
            max_workers: Maximum number of concurrent jobs
            job_store: JobStore instance (uses global if None)
        """
        self.max_workers = max_workers
        self.job_store = job_store or get_job_store()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: Dict[str, Future] = {}
        self._cancellation_tokens: Dict[str, CancellationToken] = {}
        self._output_captures: Dict[str, OutputCapture] = {}
        self._lock = threading.Lock()

    def submit(
        self,
        mode: JobMode,
        input_text: str,
        agent_name: Optional[str] = None,
        provider: str = "claude",
        target_root: Optional[str] = None
    ) -> Job:
        """
        Submit a new job for async execution.

        Args:
            mode: Execution mode (chat, auto, agent, task)
            input_text: User input/instruction
            agent_name: Optional agent name (for mode=agent)
            provider: LLM provider (claude, gpt4, gemini)
            target_root: Target repository root (defaults to cwd)

        Returns:
            Created job with PENDING status
        """
        if target_root is None:
            target_root = os.getcwd()

        # Create job
        job = Job(
            id=str(uuid.uuid4()),
            mode=mode,
            input=input_text,
            agent_name=agent_name,
            provider=provider,
            target_root=target_root,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow().isoformat() + "Z",
        )

        # Save to store
        self.job_store.create(job)

        # Create cancellation token and output capture
        cancellation_token = CancellationToken()
        output_capture = OutputCapture(job.id)

        with self._lock:
            self._cancellation_tokens[job.id] = cancellation_token
            self._output_captures[job.id] = output_capture

        # Submit to thread pool
        future = self._executor.submit(
            self._execute_job,
            job,
            cancellation_token,
            output_capture
        )

        with self._lock:
            self._futures[job.id] = future

        # Add callback to cleanup on completion
        future.add_done_callback(
            lambda f: self._cleanup_job(job.id)
        )

        return job

    def get_status(self, job_id: str) -> Optional[Job]:
        """
        Get current job status.

        Args:
            job_id: Job ID

        Returns:
            Job if found, None otherwise
        """
        return self.job_store.get(job_id)

    def get_output(self, job_id: str) -> Optional[str]:
        """
        Get current job output (may be incomplete if still running).

        Args:
            job_id: Job ID

        Returns:
            Current output or None if job not found
        """
        with self._lock:
            capture = self._output_captures.get(job_id)
            if capture:
                return capture.getvalue()

        # Job may be finished, check store
        job = self.job_store.get(job_id)
        return job.output if job else None

    def cancel(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job ID

        Returns:
            True if job was cancelled, False if not found or already finished
        """
        with self._lock:
            token = self._cancellation_tokens.get(job_id)
            if not token:
                return False

        # Mark token as cancelled
        token.cancel()

        # Update job status
        job = self.job_store.get(job_id)
        if job and job.status == JobStatus.RUNNING:
            job.status = JobStatus.CANCELLED
            job.finished_at = datetime.utcnow().isoformat() + "Z"
            job.can_cancel = False
            self.job_store.update(job)
            return True

        return False

    def _execute_job(
        self,
        job: Job,
        cancellation_token: CancellationToken,
        output_capture: OutputCapture
    ):
        """Execute job in background thread."""
        # Import here to avoid circular dependencies
        from codecompanion.llm import complete, LLMError
        from codecompanion.runner import run_pipeline, run_single_agent
        from codecompanion.task_handler import run_task
        from codecompanion.target import TargetContext

        # Update status to RUNNING
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow().isoformat() + "Z"
        self.job_store.update(job)

        try:
            # Change to target directory
            original_cwd = os.getcwd()
            os.chdir(job.target_root)

            # Create target context
            target = TargetContext(job.target_root)

            # Redirect output to capture
            with redirect_stdout(output_capture), redirect_stderr(output_capture):
                if cancellation_token.is_cancelled():
                    raise Exception("Job cancelled before execution")

                if job.mode == JobMode.CHAT:
                    # Single-turn chat mode
                    response = complete(
                        "You are CodeCompanion, a helpful coding assistant. Respond to the user's question or instruction concisely.",
                        [{"role": "user", "content": job.input}],
                        provider=job.provider,
                    )
                    output = response.get("content", "")
                    print(output)
                    exit_code = 0

                elif job.mode == JobMode.AUTO:
                    # Full pipeline
                    print(f"[executor] Running full pipeline...")
                    print(f"[executor] Project root: {job.target_root}")
                    exit_code = run_pipeline(provider=job.provider, target=target)
                    print(f"[executor] Pipeline completed with exit code {exit_code}")

                elif job.mode == JobMode.AGENT:
                    # Single agent
                    if not job.agent_name:
                        raise Exception("Agent name is required for mode='agent'")
                    print(f"[executor] Running agent: {job.agent_name}")
                    print(f"[executor] Project root: {job.target_root}")
                    exit_code = run_single_agent(
                        job.agent_name,
                        provider=job.provider,
                        target=target
                    )
                    print(f"[executor] Agent completed with exit code {exit_code}")

                elif job.mode == JobMode.TASK:
                    # Natural language task
                    print(f"[executor] Running task: {job.input}")
                    print(f"[executor] Project root: {job.target_root}")
                    exit_code = run_task(
                        job.input,
                        target=target,
                        provider=job.provider
                    )
                    print(f"[executor] Task completed with exit code {exit_code}")

                else:
                    raise Exception(f"Unknown mode: {job.mode}")

                # Check for cancellation after execution
                if cancellation_token.is_cancelled():
                    raise Exception("Job cancelled during execution")

            # Restore cwd
            os.chdir(original_cwd)

            # Success
            job.status = JobStatus.COMPLETED
            job.exit_code = exit_code
            job.output = output_capture.getvalue()
            job.finished_at = datetime.utcnow().isoformat() + "Z"
            job.can_cancel = False

            # Calculate token usage and cost
            update_job_metrics(job)

        except Exception as e:
            # Restore cwd
            try:
                os.chdir(original_cwd)
            except:
                pass

            # Check if it was a cancellation
            if cancellation_token.is_cancelled():
                job.status = JobStatus.CANCELLED
            else:
                job.status = JobStatus.FAILED

            job.error = str(e)
            job.output = output_capture.getvalue()
            job.finished_at = datetime.utcnow().isoformat() + "Z"
            job.can_cancel = False

            # Calculate token usage and cost even for failed jobs
            update_job_metrics(job)

        finally:
            # Update job in store
            self.job_store.update(job)

    def _cleanup_job(self, job_id: str):
        """Clean up job resources after completion."""
        with self._lock:
            self._futures.pop(job_id, None)
            self._cancellation_tokens.pop(job_id, None)
            # Keep output_capture briefly for final reads

    def shutdown(self, wait: bool = True):
        """
        Shutdown executor and wait for pending jobs.

        Args:
            wait: If True, wait for all jobs to complete
        """
        self._executor.shutdown(wait=wait)


# Global executor instance (singleton)
_executor: Optional[JobExecutor] = None


def get_executor(max_workers: int = 4) -> JobExecutor:
    """
    Get global executor instance.

    Args:
        max_workers: Maximum number of concurrent jobs

    Returns:
        JobExecutor instance
    """
    global _executor

    if _executor is None:
        _executor = JobExecutor(max_workers=max_workers)

    return _executor

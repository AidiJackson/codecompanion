"""
Process management utilities for enhanced job cancellation.

This module provides:
- Process tree discovery
- Graceful and forced termination
- Orphaned process cleanup
- Cross-platform support (Linux, macOS, Windows)
"""
import os
import sys
import signal
import time
import psutil
from typing import List, Set, Optional
from enum import Enum


class CancellationMode(Enum):
    """Job cancellation modes."""
    GRACEFUL = "graceful"  # SIGTERM, wait, then SIGKILL
    FORCED = "forced"       # SIGKILL immediately


class ProcessManager:
    """
    Manages process lifecycle for job execution.

    Features:
    - Process tree discovery
    - Graceful shutdown with timeout
    - Forced termination
    - Orphaned process cleanup
    """

    def __init__(self, graceful_timeout: float = 5.0):
        """
        Initialize process manager.

        Args:
            graceful_timeout: Seconds to wait during graceful shutdown
        """
        self.graceful_timeout = graceful_timeout

    def get_process_tree(self, pid: int) -> List[psutil.Process]:
        """
        Get all processes in the process tree.

        Args:
            pid: Root process ID

        Returns:
            List of Process objects (parent + all descendants)
        """
        try:
            parent = psutil.Process(pid)
            tree = [parent]

            # Recursively get all children
            children = parent.children(recursive=True)
            tree.extend(children)

            return tree
        except psutil.NoSuchProcess:
            return []

    def kill_gracefully(self, pid: int) -> bool:
        """
        Kill process tree gracefully (SIGTERM -> wait -> SIGKILL).

        Process:
        1. Send SIGTERM to all processes
        2. Wait up to graceful_timeout seconds
        3. Send SIGKILL to any remaining processes

        Args:
            pid: Root process ID

        Returns:
            True if all processes terminated, False if some remained
        """
        processes = self.get_process_tree(pid)

        if not processes:
            return True  # Already dead

        # Step 1: Send SIGTERM to all (bottom-up to avoid zombies)
        for proc in reversed(processes):
            try:
                if proc.is_running():
                    proc.terminate()  # SIGTERM
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Step 2: Wait for processes to exit
        gone, alive = psutil.wait_procs(
            processes,
            timeout=self.graceful_timeout
        )

        # Step 3: Force kill remaining processes
        for proc in alive:
            try:
                if proc.is_running():
                    proc.kill()  # SIGKILL
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Final check
        final_gone, final_alive = psutil.wait_procs(alive, timeout=1.0)

        return len(final_alive) == 0

    def kill_forcefully(self, pid: int) -> bool:
        """
        Kill process tree immediately (SIGKILL).

        Args:
            pid: Root process ID

        Returns:
            True if all processes terminated, False if some remained
        """
        processes = self.get_process_tree(pid)

        if not processes:
            return True  # Already dead

        # Send SIGKILL to all (bottom-up)
        for proc in reversed(processes):
            try:
                if proc.is_running():
                    proc.kill()  # SIGKILL
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Wait briefly and check
        gone, alive = psutil.wait_procs(processes, timeout=1.0)

        return len(alive) == 0

    def cancel_process(self, pid: int, mode: CancellationMode) -> bool:
        """
        Cancel a process using the specified mode.

        Args:
            pid: Process ID to cancel
            mode: Cancellation mode (graceful or forced)

        Returns:
            True if successfully cancelled, False otherwise
        """
        if mode == CancellationMode.GRACEFUL:
            return self.kill_gracefully(pid)
        elif mode == CancellationMode.FORCED:
            return self.kill_forcefully(pid)
        else:
            raise ValueError(f"Unknown cancellation mode: {mode}")

    def find_orphaned_processes(
        self,
        parent_pid: int,
        expected_children: Set[int]
    ) -> List[psutil.Process]:
        """
        Find orphaned child processes.

        Orphans are processes that:
        - Were spawned by parent_pid
        - Are not in expected_children set
        - Are still running

        Args:
            parent_pid: Parent process ID
            expected_children: Set of expected child PIDs

        Returns:
            List of orphaned Process objects
        """
        orphans = []

        try:
            parent = psutil.Process(parent_pid)
            all_children = parent.children(recursive=True)

            for child in all_children:
                if child.pid not in expected_children:
                    orphans.append(child)
        except psutil.NoSuchProcess:
            pass

        return orphans

    def cleanup_orphans(self, orphans: List[psutil.Process]) -> int:
        """
        Clean up orphaned processes.

        Args:
            orphans: List of orphaned Process objects

        Returns:
            Number of processes successfully killed
        """
        killed = 0

        for proc in orphans:
            try:
                if proc.is_running():
                    proc.kill()
                    proc.wait(timeout=1.0)
                    killed += 1
            except (psutil.NoSuchProcess, psutil.TimeoutExpired, psutil.AccessDenied):
                pass

        return killed

    def get_process_info(self, pid: int) -> Optional[dict]:
        """
        Get information about a process.

        Args:
            pid: Process ID

        Returns:
            Dict with process info or None if not found
        """
        try:
            proc = psutil.Process(pid)

            return {
                'pid': proc.pid,
                'name': proc.name(),
                'status': proc.status(),
                'create_time': proc.create_time(),
                'cmdline': ' '.join(proc.cmdline()) if proc.cmdline() else '',
                'num_children': len(proc.children(recursive=True))
            }
        except psutil.NoSuchProcess:
            return None


# Global process manager instance (singleton)
_process_manager: Optional[ProcessManager] = None


def get_process_manager(graceful_timeout: float = 5.0) -> ProcessManager:
    """
    Get global process manager instance.

    Args:
        graceful_timeout: Timeout for graceful cancellation

    Returns:
        ProcessManager instance
    """
    global _process_manager

    if _process_manager is None:
        _process_manager = ProcessManager(graceful_timeout=graceful_timeout)

    return _process_manager

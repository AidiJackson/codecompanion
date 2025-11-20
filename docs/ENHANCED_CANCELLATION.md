# Enhanced Cancellation Controls

**Phase 3b Implementation - Process Tree Management & Dual-Mode Cancellation**

## Overview

Phase 3b enhances the job cancellation system with robust process tree management and two cancellation modes (graceful and forced). This provides fine-grained control over how running jobs are terminated, ensuring clean shutdown while offering an immediate kill option when needed.

### Key Features

- ✅ **Process Tree Management**: Track and kill entire process hierarchies
- ✅ **Dual-Mode Cancellation**: Choose between graceful and forced termination
- ✅ **Orphan Detection**: Find and cleanup orphaned child processes
- ✅ **Cross-Platform**: Works on Linux, macOS, and Windows (via psutil)
- ✅ **UI Controls**: Easy-to-use buttons for each cancellation mode
- ✅ **Cancellation History**: Track which mode was used for each cancelled job

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Dashboard UI                                                 │
│  - "Cancel" button (yellow) → graceful mode                   │
│  - "⚡ Force" button (red) → forced mode                      │
│  - Mode-specific confirmation dialogs                         │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────┐
│  API Endpoint                                                 │
│  POST /api/runs/{id}/cancel?mode=graceful|forced             │
│  - Validates mode parameter                                   │
│  - Returns cancellation result with mode                      │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────┐
│  Job Executor                                                 │
│  - cancel(job_id, CancellationMode)                           │
│  - Sets cancellation token (cooperative)                      │
│  - Gets job's process_id                                      │
│  - Calls ProcessManager.cancel_process()                      │
│  - Updates job with cancellation_mode                         │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────┐
│  Process Manager                                              │
│  - get_process_tree(pid) → find all children                 │
│  - kill_gracefully(pid):                                      │
│    1. SIGTERM to all processes                                │
│    2. Wait graceful_timeout (5s)                              │
│    3. SIGKILL to survivors                                    │
│  - kill_forcefully(pid):                                      │
│    1. SIGKILL to all processes immediately                    │
│  - Uses psutil for cross-platform process control             │
└──────────────────────────────────────────────────────────────┘
```

## Process Manager

The `ProcessManager` class provides low-level process tree management using the `psutil` library.

### Class: ProcessManager

```python
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
```

### Methods

#### get_process_tree(pid)

Discover all processes in the process tree.

```python
def get_process_tree(self, pid: int) -> List[psutil.Process]:
    """
    Get all processes in the process tree.

    Recursively finds parent and all descendants.

    Args:
        pid: Root process ID

    Returns:
        List of Process objects (parent + all descendants)
    """
```

**Example:**

```python
from codecompanion.dashboard.process_manager import get_process_manager

pm = get_process_manager()
tree = pm.get_process_tree(12345)

print(f"Process tree has {len(tree)} processes")
for proc in tree:
    print(f"  - PID {proc.pid}: {proc.name()}")
```

#### kill_gracefully(pid)

Gracefully terminate a process tree with SIGTERM, then SIGKILL if needed.

```python
def kill_gracefully(self, pid: int) -> bool:
    """
    Kill process tree gracefully (SIGTERM -> wait -> SIGKILL).

    Process:
    1. Send SIGTERM to all processes (bottom-up)
    2. Wait up to graceful_timeout seconds
    3. Send SIGKILL to any remaining processes

    Args:
        pid: Root process ID

    Returns:
        True if all processes terminated, False if some remained
    """
```

**Timeline:**

```
t=0s    SIGTERM sent to all processes
t=0-5s  Wait for processes to exit gracefully
t=5s    SIGKILL sent to survivors
t=6s    Return result
```

**Example:**

```python
success = pm.kill_gracefully(12345)

if success:
    print("All processes terminated cleanly")
else:
    print("Warning: Some processes may have survived")
```

#### kill_forcefully(pid)

Immediately terminate a process tree with SIGKILL.

```python
def kill_forcefully(self, pid: int) -> bool:
    """
    Kill process tree immediately (SIGKILL).

    Sends SIGKILL to all processes in bottom-up order.

    Args:
        pid: Root process ID

    Returns:
        True if all processes terminated, False if some remained
    """
```

**Example:**

```python
success = pm.kill_forcefully(12345)
print("Forced termination complete")
```

#### cancel_process(pid, mode)

Cancel a process using the specified mode.

```python
def cancel_process(self, pid: int, mode: CancellationMode) -> bool:
    """
    Cancel a process using the specified mode.

    Args:
        pid: Process ID to cancel
        mode: Cancellation mode (graceful or forced)

    Returns:
        True if successfully cancelled, False otherwise
    """
```

**Example:**

```python
from codecompanion.dashboard.process_manager import CancellationMode

# Graceful cancellation
success = pm.cancel_process(12345, CancellationMode.GRACEFUL)

# Forced cancellation
success = pm.cancel_process(12345, CancellationMode.FORCED)
```

#### find_orphaned_processes(parent_pid, expected_children)

Find orphaned child processes that aren't in the expected set.

```python
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
```

**Example:**

```python
expected = {12346, 12347, 12348}
orphans = pm.find_orphaned_processes(12345, expected)

if orphans:
    print(f"Found {len(orphans)} orphaned processes:")
    for proc in orphans:
        print(f"  - PID {proc.pid}: {proc.name()}")
```

#### cleanup_orphans(orphans)

Clean up orphaned processes by killing them.

```python
def cleanup_orphans(self, orphans: List[psutil.Process]) -> int:
    """
    Clean up orphaned processes.

    Args:
        orphans: List of orphaned Process objects

    Returns:
        Number of processes successfully killed
    """
```

**Example:**

```python
orphans = pm.find_orphaned_processes(12345, expected)
killed = pm.cleanup_orphans(orphans)
print(f"Cleaned up {killed}/{len(orphans)} orphaned processes")
```

#### get_process_info(pid)

Get detailed information about a process.

```python
def get_process_info(self, pid: int) -> Optional[dict]:
    """
    Get information about a process.

    Args:
        pid: Process ID

    Returns:
        Dict with process info or None if not found
    """
```

**Returns:**

```python
{
    'pid': 12345,
    'name': 'python',
    'status': 'running',
    'create_time': 1705685234.567,
    'cmdline': 'python script.py --arg value',
    'num_children': 3
}
```

## Cancellation Modes

### Enum: CancellationMode

```python
class CancellationMode(Enum):
    """Job cancellation modes."""
    GRACEFUL = "graceful"  # SIGTERM, wait, then SIGKILL
    FORCED = "forced"       # SIGKILL immediately
```

### Graceful Mode

**Behavior:**
1. Send SIGTERM to all processes in tree
2. Wait up to 5 seconds for graceful shutdown
3. Send SIGKILL to any survivors

**Use When:**
- Normal cancellation needed
- Want to allow cleanup handlers to run
- Process may have important cleanup tasks

**Example:**
- Cancelling a long-running test suite
- Stopping a build process
- Interrupting an analysis job

### Forced Mode

**Behavior:**
1. Send SIGKILL to all processes immediately
2. No grace period
3. Processes cannot catch or ignore the signal

**Use When:**
- Job is unresponsive or hung
- Immediate termination required
- Graceful cancellation failed
- Emergency stop needed

**Example:**
- Job is stuck in infinite loop
- Process consuming too many resources
- Graceful cancellation timed out

## Job Model Enhancements

### New Fields

```python
@dataclass
class Job:
    # ... existing fields ...
    process_id: Optional[int] = None           # PID of running subprocess
    cancellation_mode: Optional[str] = None    # "graceful" or "forced"
```

**Database Schema:**

```sql
ALTER TABLE jobs ADD COLUMN process_id INTEGER;
ALTER TABLE jobs ADD COLUMN cancellation_mode TEXT;
```

Migration is automatic on first access.

### Process ID Tracking

When a job starts, the executor stores `os.getpid()` as the process ID:

```python
job.process_id = os.getpid()  # Main Python process
```

This allows the process manager to find and kill all child processes spawned by the job.

**Note:** Currently tracks the main executor process. Future enhancement could track actual subprocess PIDs if jobs spawn subprocesses directly.

### Cancellation Mode Recording

When a job is cancelled, the mode is recorded:

```python
job.cancellation_mode = mode.value  # "graceful" or "forced"
```

This provides an audit trail of how each job was terminated.

## Executor Enhancement

### Updated cancel() Method

```python
def cancel(
    self,
    job_id: str,
    mode: CancellationMode = CancellationMode.GRACEFUL
) -> bool:
    """
    Cancel a running job using the specified mode.

    Cancellation process:
    1. Set cancellation token (for cooperative cancellation)
    2. If job has a process ID, kill the process tree
       - Graceful: SIGTERM -> wait -> SIGKILL
       - Forced: SIGKILL immediately
    3. Update job status and record cancellation mode

    Args:
        job_id: Job ID
        mode: Cancellation mode (graceful or forced)

    Returns:
        True if job was cancelled, False if not found or already finished
    """
```

**Usage:**

```python
from codecompanion.dashboard.executor import get_executor
from codecompanion.dashboard.process_manager import CancellationMode

executor = get_executor()

# Graceful cancellation (default)
executor.cancel("job-123")

# Explicit graceful
executor.cancel("job-123", CancellationMode.GRACEFUL)

# Forced cancellation
executor.cancel("job-123", CancellationMode.FORCED)
```

## API Reference

### POST /api/runs/{run_id}/cancel

Cancel a running job with specified mode.

**Query Parameters:**
- `mode` (optional): Cancellation mode
  - `"graceful"` (default) - SIGTERM → wait 5s → SIGKILL
  - `"forced"` - SIGKILL immediately

**Example Requests:**

```bash
# Graceful cancellation (default)
curl -X POST http://localhost:3000/api/runs/job-123/cancel

# Explicit graceful
curl -X POST "http://localhost:3000/api/runs/job-123/cancel?mode=graceful"

# Forced cancellation
curl -X POST "http://localhost:3000/api/runs/job-123/cancel?mode=forced"
```

**Success Response (200):**

```json
{
  "success": true,
  "message": "Run job-123 cancelled successfully (graceful mode)",
  "mode": "graceful"
}
```

**Not Found Response (404):**

```json
{
  "success": false,
  "message": "Run job-123 not found or already finished"
}
```

**Invalid Mode Response (400):**

```json
{
  "detail": "Invalid cancellation mode: invalid. Use 'graceful' or 'forced'"
}
```

## Dashboard UI

### Cancel Buttons

For each running job, two buttons are displayed:

1. **"Cancel" (Yellow)** - Graceful cancellation
   - Tooltip: "Graceful shutdown (SIGTERM then SIGKILL)"
   - Confirmation: "Cancel will attempt graceful shutdown (SIGTERM, then SIGKILL after 5s). Continue?"

2. **"⚡ Force" (Red)** - Forced cancellation
   - Tooltip: "Force stop immediately (SIGKILL)"
   - Confirmation: "Force stop will immediately kill the process tree (SIGKILL). Continue?"

**HTML:**

```html
<button class="btn btn-small btn-warning"
        onclick="cancelJob('job-123', 'graceful')"
        title="Graceful shutdown (SIGTERM then SIGKILL)">
    Cancel
</button>
<button class="btn btn-small btn-danger"
        onclick="cancelJob('job-123', 'forced')"
        title="Force stop immediately (SIGKILL)">
    ⚡ Force
</button>
```

**CSS:**

```css
.btn-warning {
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.btn-warning:hover {
    background: rgba(245, 158, 11, 0.25);
}
```

### JavaScript Function

```javascript
async function cancelJob(jobId, mode = 'graceful') {
    const modeText = mode === 'forced' ? 'force stop' : 'cancel';
    const confirmText = mode === 'forced'
        ? 'Force stop will immediately kill the process tree (SIGKILL). Continue?'
        : 'Cancel will attempt graceful shutdown (SIGTERM, then SIGKILL after 5s). Continue?';

    if (!confirm(confirmText)) {
        return;
    }

    const response = await fetch(`/api/runs/${jobId}/cancel?mode=${mode}`, {
        method: 'POST'
    });

    if (!response.ok) {
        throw new Error(`Failed to ${modeText} job`);
    }

    // Refresh jobs list
    await refreshJobs();
}
```

## Usage Examples

### Python: Cancel with Mode

```python
import requests

# Graceful cancellation
response = requests.post('http://localhost:3000/api/runs/job-123/cancel')
print(response.json())
# {'success': True, 'message': 'Run job-123 cancelled successfully (graceful mode)', 'mode': 'graceful'}

# Forced cancellation
response = requests.post(
    'http://localhost:3000/api/runs/job-456/cancel',
    params={'mode': 'forced'}
)
print(response.json())
# {'success': True, 'message': 'Run job-456 cancelled successfully (forced mode)', 'mode': 'forced'}
```

### Python: Process Tree Management

```python
from codecompanion.dashboard.process_manager import get_process_manager, CancellationMode
import subprocess
import os

# Start a process that spawns children
proc = subprocess.Popen(['./script_with_children.sh'])
pid = proc.pid

# Get process tree
pm = get_process_manager()
tree = pm.get_process_tree(pid)
print(f"Process tree: {len(tree)} processes")

# Cancel gracefully
success = pm.cancel_process(pid, CancellationMode.GRACEFUL)

if success:
    print("All processes terminated")
else:
    print("Some processes survived graceful cancellation")
    # Force kill if needed
    pm.cancel_process(pid, CancellationMode.FORCED)
```

### Python: Find and Clean Orphans

```python
from codecompanion.dashboard.process_manager import get_process_manager

pm = get_process_manager()
parent_pid = 12345
expected = {12346, 12347}

# Find orphans
orphans = pm.find_orphaned_processes(parent_pid, expected)

if orphans:
    print(f"Found {len(orphans)} orphaned processes")
    killed = pm.cleanup_orphans(orphans)
    print(f"Cleaned up {killed} orphans")
```

## Implementation Details

### Process Tree Discovery

Uses `psutil.Process.children(recursive=True)` to find all descendants:

```python
def get_process_tree(self, pid: int) -> List[psutil.Process]:
    try:
        parent = psutil.Process(pid)
        tree = [parent]
        children = parent.children(recursive=True)
        tree.extend(children)
        return tree
    except psutil.NoSuchProcess:
        return []
```

### Bottom-Up Termination

Processes are terminated in reverse order (children first) to avoid zombie processes:

```python
for proc in reversed(processes):
    try:
        proc.terminate()  # or proc.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
```

### Graceful Timeout

Uses `psutil.wait_procs()` to wait for processes to exit:

```python
gone, alive = psutil.wait_procs(processes, timeout=5.0)

# Kill survivors
for proc in alive:
    proc.kill()
```

### Cross-Platform Support

`psutil` provides cross-platform process management:

- **Linux/macOS**: Uses signals (SIGTERM, SIGKILL)
- **Windows**: Uses TerminateProcess API
- **All platforms**: Consistent Python API

## Testing

### Unit Tests

```bash
# Test process manager
python -c "
from codecompanion.dashboard.process_manager import get_process_manager, CancellationMode
import os

pm = get_process_manager()

# Test process tree
tree = pm.get_process_tree(os.getpid())
assert len(tree) >= 1
print(f'✓ Process tree: {len(tree)} processes')

# Test cancellation modes
assert CancellationMode.GRACEFUL.value == 'graceful'
assert CancellationMode.FORCED.value == 'forced'
print('✓ Cancellation modes validated')
"

# Test job model
python -c "
from codecompanion.dashboard.models import Job, JobMode, JobStatus
from datetime import datetime

job = Job(
    id='test',
    mode=JobMode.CHAT,
    input='test',
    agent_name=None,
    provider='claude',
    target_root='/tmp',
    status=JobStatus.CANCELLED,
    created_at=datetime.utcnow().isoformat() + 'Z',
    process_id=12345,
    cancellation_mode='graceful'
)

assert job.process_id == 12345
assert job.cancellation_mode == 'graceful'
print('✓ Job model with new fields')
"
```

### Integration Tests

```bash
# Start dashboard
codecompanion --dashboard &
DASHBOARD_PID=$!

# Wait for startup
sleep 2

# Submit a long-running job
JOB_ID=$(curl -s -X POST http://localhost:3000/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"mode": "task", "input": "sleep 60 && echo done", "provider": "claude"}' \
  | jq -r '.id')

echo "Job submitted: $JOB_ID"

# Wait for it to start
sleep 2

# Test graceful cancellation
curl -s -X POST "http://localhost:3000/api/runs/$JOB_ID/cancel?mode=graceful" | jq .

# Check job status
curl -s "http://localhost:3000/api/runs/$JOB_ID" | jq '.status, .cancellation_mode'

# Cleanup
kill $DASHBOARD_PID
```

## Troubleshooting

### Process Not Found

**Problem:** `psutil.NoSuchProcess` when trying to kill process.

**Solution:**
- Process may have already exited
- Check if process still exists before killing
- Handle exception gracefully

```python
try:
    proc = psutil.Process(pid)
    proc.kill()
except psutil.NoSuchProcess:
    print("Process already exited")
```

### Access Denied

**Problem:** `psutil.AccessDenied` when trying to kill process.

**Solution:**
- Process owned by different user
- Insufficient permissions
- May need sudo/admin privileges

```python
try:
    proc.kill()
except psutil.AccessDenied:
    print("Insufficient permissions to kill process")
```

### Processes Surviving Forced Kill

**Problem:** Some processes remain after forced cancellation.

**Possible Causes:**
1. **Zombie processes** - Parent hasn't reaped children
2. **System processes** - Cannot be killed by user
3. **Permission issues** - Insufficient privileges

**Solution:**
- Check process status: `proc.status()` may show 'zombie'
- Reap zombies by waiting on parent process
- Check process ownership and permissions

### Graceful Timeout Too Short

**Problem:** Processes need more than 5s to shut down gracefully.

**Solution:**
Increase timeout when creating process manager:

```python
from codecompanion.dashboard.process_manager import ProcessManager

pm = ProcessManager(graceful_timeout=10.0)  # 10 seconds
```

## Future Enhancements

Phase 3b provides the foundation for enhanced cancellation. Potential improvements:

### 1. Subprocess PID Tracking

Currently tracks main executor process. Could track actual subprocess PIDs:

```python
# In executor, when spawning subprocess
proc = subprocess.Popen(...)
job.process_id = proc.pid  # Track subprocess directly
```

### 2. Progress-Aware Cancellation

Cancel at safe points in job execution:

```python
class JobExecutor:
    def cancel_at_checkpoint(self, job_id: str):
        """Wait for next checkpoint before cancelling."""
```

### 3. Cascading Cancellation

Cancel all jobs in a session:

```python
def cancel_session(session_id: str, mode: CancellationMode):
    """Cancel all jobs in session with specified mode."""
```

### 4. Cancellation Hooks

Allow jobs to register cleanup handlers:

```python
@job.on_cancel
def cleanup():
    # Save partial results
    # Close connections
    # Release resources
```

### 5. Retry After Cancel

Automatically retry failed graceful cancellations with forced mode:

```python
success = executor.cancel(job_id, CancellationMode.GRACEFUL)
if not success:
    executor.cancel(job_id, CancellationMode.FORCED)
```

## References

- [Phase 0: Security Foundation](SECURITY.md)
- [Phase 1a: Basic --init Command](../codecompanion/workspace.py)
- [Phase 1b: CLI UX Polish](../codecompanion/task_handler.py)
- [Phase 2a: Async Execution Backend](ASYNC_EXECUTION.md)
- [Phase 2b: Dashboard Frontend - Projects Tab](../codecompanion/templates/dashboard.html)
- [Phase 3a: Timeline & Sessions](TIMELINE_SESSIONS.md)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [Unix Signals](https://man7.org/linux/man-pages/man7/signal.7.html)

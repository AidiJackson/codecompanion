# Async Job Execution System

**Phase 2a Implementation - Dashboard Backend (Async Runs)**

## Overview

The async job execution system transforms CodeCompanion's dashboard from a blocking, synchronous command interface into a non-blocking, production-ready job management system.

### Key Features

- ✅ **Non-blocking execution**: Jobs run in background threads
- ✅ **Persistent storage**: SQLite-based job history survives restarts
- ✅ **Real-time updates**: Server-Sent Events (SSE) for streaming status
- ✅ **Cancellation support**: Stop long-running jobs at any time
- ✅ **Multi-repository**: Target any directory, not just cwd
- ✅ **Thread-safe**: Concurrent job execution with thread pool

## Architecture

```
┌──────────────────────────────────────────────────┐
│  Client (Web Dashboard / API)                    │
│  - Submit job via POST /api/runs                 │
│  - Poll status via GET /api/runs/{id}            │
│  - Stream output via GET /api/runs/{id}/stream   │
│  - Cancel via POST /api/runs/{id}/cancel         │
└───────────────────┬──────────────────────────────┘
                    │
                    ↓
┌──────────────────────────────────────────────────┐
│  FastAPI Dashboard (app.py)                      │
│  - Route requests to executor                    │
│  - Validate inputs                               │
│  - Return immediate responses                    │
└───────────────────┬──────────────────────────────┘
                    │
                    ↓
┌──────────────────────────────────────────────────┐
│  JobExecutor (executor.py)                       │
│  - ThreadPoolExecutor (max 4 workers)            │
│  - Output capture with streaming                 │
│  - Cancellation tokens                           │
│  - Status updates to JobStore                    │
└───────────────────┬──────────────────────────────┘
                    │
                    ↓
┌──────────────────────────────────────────────────┐
│  JobStore (models.py)                            │
│  - SQLite database (.cc/jobs.db)                 │
│  - Thread-safe operations                        │
│  - Job CRUD operations                           │
│  - Status filtering and pagination               │
└──────────────────────────────────────────────────┘
```

## Data Model

### Job Status Lifecycle

```
PENDING → RUNNING → COMPLETED
                 → FAILED
                 → CANCELLED
```

### Job Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | UUID identifier |
| `mode` | JobMode | Execution mode (chat, auto, agent, task) |
| `input` | str | User instruction |
| `agent_name` | str? | Agent name (for mode=agent) |
| `provider` | str | LLM provider (claude, gpt4, gemini) |
| `target_root` | str | Target repository path |
| `status` | JobStatus | Current status |
| `created_at` | str | ISO timestamp when created |
| `started_at` | str? | ISO timestamp when execution started |
| `finished_at` | str? | ISO timestamp when completed |
| `output` | str? | Captured stdout/stderr |
| `error` | str? | Error message if failed |
| `exit_code` | int? | Process exit code |
| `can_cancel` | bool | Whether job can be cancelled |

## API Reference

### POST /api/runs

Create a new async job.

**Request:**
```json
{
  "mode": "auto",
  "input": "Run full pipeline",
  "provider": "claude",
  "target_root": "/path/to/repo"
}
```

**Response (202 Accepted):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "mode": "auto",
  "input": "Run full pipeline",
  "provider": "claude",
  "target_root": "/path/to/repo",
  "created_at": "2025-01-19T12:00:00Z",
  "can_cancel": true
}
```

### GET /api/runs

List all jobs with optional filtering.

**Query Parameters:**
- `status`: Filter by status (optional)
- `limit`: Max results (default: 100)
- `offset`: Skip N results (default: 0)

**Response:**
```json
{
  "runs": [
    { /* job object */ },
    { /* job object */ }
  ],
  "total": 42,
  "limit": 100,
  "offset": 0
}
```

### GET /api/runs/{id}

Get specific job status and output.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "output": "[partial output so far...]\n",
  "started_at": "2025-01-19T12:00:05Z",
  ...
}
```

### POST /api/runs/{id}/cancel

Cancel a running job.

**Response:**
```json
{
  "success": true,
  "message": "Run 550e8400-... cancelled successfully"
}
```

### GET /api/runs/{id}/stream

Stream job output using Server-Sent Events.

**Response (text/event-stream):**
```
data: {"status":"running","output":"Starting...\n","finished":false}

data: {"status":"running","output":"Step 1 complete\n","finished":false}

data: {"status":"completed","output":"Done!\n","finished":true,"exit_code":0}
```

## Usage Examples

### Python Client

```python
import requests
import json

# Submit job
response = requests.post('http://localhost:3000/api/runs', json={
    "mode": "auto",
    "input": "Run full pipeline",
    "provider": "claude"
})
job = response.json()
job_id = job['id']
print(f"Job submitted: {job_id}")

# Poll for status
while True:
    response = requests.get(f'http://localhost:3000/api/runs/{job_id}')
    job = response.json()
    print(f"Status: {job['status']}")

    if job['status'] in ['completed', 'failed', 'cancelled']:
        print(f"Output:\n{job['output']}")
        break

    time.sleep(2)
```

### JavaScript (SSE Streaming)

```javascript
const response = await fetch('/api/runs', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    mode: 'auto',
    input: 'Run full pipeline',
    provider: 'claude'
  })
});

const job = await response.json();
const jobId = job.id;

// Stream output
const eventSource = new EventSource(`/api/runs/${jobId}/stream`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Status:', data.status);
  console.log('Output:', data.output);

  if (data.finished) {
    eventSource.close();
    console.log('Job completed with exit code:', data.exit_code);
  }
};
```

### cURL

```bash
# Submit job
curl -X POST http://localhost:3000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"mode":"chat","input":"Explain this project","provider":"claude"}'

# Get job status
curl http://localhost:3000/api/runs/550e8400-e29b-41d4-a716-446655440000

# Cancel job
curl -X POST http://localhost:3000/api/runs/550e8400-e29b-41d4-a716-446655440000/cancel

# List all jobs
curl http://localhost:3000/api/runs

# List running jobs
curl "http://localhost:3000/api/runs?status=running"
```

## Implementation Details

### Thread Safety

All components are thread-safe:

- **JobStore**: Uses `threading.Lock()` for database operations
- **JobExecutor**: Thread pool with concurrent.futures.ThreadPoolExecutor
- **OutputCapture**: Locks when writing/reading buffer

### Output Streaming

Output is captured in real-time using custom `OutputCapture` class:

```python
class OutputCapture:
    def __init__(self, job_id: str):
        self._buffer = io.StringIO()
        self._lock = threading.Lock()

    def write(self, text: str):
        with self._lock:
            self._buffer.write(text)

    def getvalue(self) -> str:
        with self._lock:
            return self._buffer.getvalue()
```

During execution, stdout/stderr are redirected to this capture object,
allowing incremental reads while the job runs.

### Cancellation

Cancellation uses cooperative tokens:

```python
class CancellationToken:
    def __init__(self):
        self._cancelled = threading.Event()

    def cancel(self):
        self._cancelled.set()

    def is_cancelled(self) -> bool:
        return self._cancelled.is_set()
```

The executor checks `token.is_cancelled()` before and during execution,
setting job status to CANCELLED if detected.

### Database Schema

SQLite table structure:

```sql
CREATE TABLE jobs (
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
);

CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_status ON jobs(status);
```

Database location: `.cc/jobs.db` (auto-created on first use)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 3000 | Dashboard HTTP port |
| `CC_PROVIDER` | claude | Default LLM provider |

### Executor Settings

Configured in `get_executor()`:

```python
executor = JobExecutor(
    max_workers=4,  # Max concurrent jobs
    job_store=None  # Uses global store
)
```

To change max workers, modify `codecompanion/dashboard/executor.py:get_executor()`.

## Migration from Sync API

### Old (Blocking) Behavior

```python
@app.post("/api/console")
async def console_command(request: Request):
    # ... validation ...

    # BLOCKS until completion
    result = run_console_command(mode, input, agent, provider)

    # Returns after job finishes
    return result
```

### New (Non-Blocking) Behavior

```python
@app.post("/api/runs")
async def create_run(request: Request):
    # ... validation ...

    # Submit to background executor
    job = executor.submit(mode, input, agent, provider)

    # Returns immediately
    return job.to_dict()
```

### Backward Compatibility

The old `/api/console` endpoint is maintained with modified behavior:

- Returns immediately with job ID
- Response includes `"status": "submitted"` instead of blocking
- Frontend should poll `/api/runs/{id}` for results

## Testing

### Unit Tests

```bash
# Test models
python -c "
from codecompanion.dashboard.models import Job, JobMode, JobStatus
job = Job(id='test', mode=JobMode.CHAT, ...)
assert job.to_dict()['mode'] == 'chat'
"

# Test executor imports
python -c "
from codecompanion.dashboard.executor import JobExecutor
executor = JobExecutor(max_workers=2)
"
```

### Integration Tests

```bash
# Start dashboard
codecompanion --dashboard &
DASHBOARD_PID=$!

# Submit test job
curl -X POST http://localhost:3000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"mode":"chat","input":"test","provider":"claude"}' \
  | jq .id

# Cleanup
kill $DASHBOARD_PID
```

## Troubleshooting

### Jobs Stuck in PENDING

Check executor startup:

```python
from codecompanion.dashboard.executor import get_executor
executor = get_executor()
print(f"Max workers: {executor.max_workers}")
print(f"Active jobs: {len(executor._futures)}")
```

### Database Locked

SQLite locks can occur under high concurrency. The `JobStore` uses
`threading.Lock()` to prevent this, but if issues persist:

```bash
# Check database
sqlite3 .cc/jobs.db "SELECT COUNT(*) FROM jobs WHERE status='running';"

# Reset if needed
rm .cc/jobs.db
```

### Output Not Streaming

Ensure SSE client properly handles incremental updates:

```javascript
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.output contains ONLY new output since last event
  appendToConsole(data.output);  // Append, don't replace!
};
```

## Performance Considerations

### Thread Pool Size

Default: 4 workers

- **Too low**: Jobs queue up, high latency
- **Too high**: High memory usage, CPU contention

Recommended: 1-2x CPU cores for I/O-bound jobs (LLM calls)

### Database Performance

- Jobs table is indexed on `created_at` and `status`
- Pagination recommended for large result sets
- Old jobs can be deleted: `DELETE FROM jobs WHERE created_at < ?`

### Memory Usage

Each running job maintains:
- OutputCapture buffer (grows with output)
- CancellationToken (small)
- Future object (small)

Estimate: ~10-50MB per running job (depends on output volume)

## Security Considerations

### Path Validation

The executor uses `TargetContext` for path validation:

```python
from codecompanion.target import TargetContext

target = TargetContext(job.target_root)
# All file operations are validated against target directory
```

This prevents path traversal attacks when `target_root` is user-provided.

### API Authentication

Phase 2a focuses on backend architecture. Authentication should be added
in production:

```python
from fastapi import Depends, Header, HTTPException

def verify_token(authorization: str = Header(None)):
    if authorization != f"Bearer {SECRET_TOKEN}":
        raise HTTPException(status_code=401)

@app.post("/api/runs", dependencies=[Depends(verify_token)])
async def create_run(...):
    ...
```

### Resource Limits

Consider adding:
- Max job duration (timeout)
- Max output size (prevent memory exhaustion)
- Rate limiting (prevent abuse)

## Future Enhancements

Phase 2a provides the foundation. Future phases can add:

- **Phase 2b**: Dashboard UI for Projects tab
- **Phase 3a**: Timeline visualization
- **Phase 3b**: Enhanced cancellation (kill subprocess tree)
- **Phase 4**: Cost tracking, agent library, model selection

## References

- [Phase 0: Security Foundation](SECURITY.md)
- [Phase 1a: Basic --init Command](../codecompanion/workspace.py)
- [Phase 1b: CLI UX Polish](../codecompanion/task_handler.py)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Server-Sent Events Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html)

# Timeline & Sessions System

**Phase 3a Implementation - Cost Tracking & Session Management**

## Overview

Phase 3a extends the async job execution system with comprehensive cost tracking, session management, and timeline visualization. This provides users with complete visibility into token usage, API costs, and historical activity grouped by logical sessions.

### Key Features

- ✅ **Session Management**: Group related jobs together
- ✅ **Cost Tracking**: Estimate API costs per job and session
- ✅ **Token Counting**: Track input/output/total tokens
- ✅ **Analytics Dashboard**: Comprehensive metrics and breakdowns
- ✅ **Timeline View**: Chronological job history grouped by session
- ✅ **Multi-Provider Pricing**: Support for Claude, GPT-4, Gemini

## Architecture

```
┌────────────────────────────────────────────────┐
│  Timeline Tab (Frontend)                       │
│  - Analytics cards (jobs, cost, tokens, rate)  │
│  - Timeline view with session grouping         │
│  - Real-time data refresh                      │
└───────────────────┬────────────────────────────┘
                    │
                    ↓
┌────────────────────────────────────────────────┐
│  API Endpoints                                 │
│  - GET /api/analytics (metrics summary)        │
│  - GET /api/timeline (session-grouped jobs)    │
│  - GET /api/sessions (list sessions)           │
│  - GET /api/sessions/{id} (session details)    │
│  - GET /api/sessions/{id}/jobs (session jobs)  │
└───────────────────┬────────────────────────────┘
                    │
                    ↓
┌────────────────────────────────────────────────┐
│  Session & Job Models                          │
│  - Session: id, name, metrics                  │
│  - Job: +session_id, +tokens, +cost, +model    │
│  - SessionStore: CRUD operations               │
│  - JobStore: Enhanced with new columns         │
└───────────────────┬────────────────────────────┘
                    │
                    ↓
┌────────────────────────────────────────────────┐
│  Cost Calculation Engine                       │
│  - estimate_tokens(text) → token count         │
│  - calculate_cost(in, out, provider) → cost    │
│  - update_job_metrics(job) → populated metrics │
│  - PROVIDER_PRICING: Multi-provider rates      │
└────────────────────────────────────────────────┘
```

## Data Models

### Session Model

```python
@dataclass
class Session:
    id: str                  # UUID identifier
    name: str                # Human-readable name
    created_at: str          # ISO timestamp
    updated_at: str          # ISO timestamp
    total_jobs: int          # Total jobs in session
    completed_jobs: int      # Number completed
    total_cost: float        # Total estimated cost ($)
    total_tokens: int        # Total tokens used
```

**Database Schema:**

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    total_jobs INTEGER DEFAULT 0,
    completed_jobs INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    total_tokens INTEGER DEFAULT 0
);

CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
```

### Enhanced Job Model

**New Fields Added:**

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | str? | Parent session UUID |
| `input_tokens` | int | Estimated input tokens |
| `output_tokens` | int | Estimated output tokens |
| `total_tokens` | int | Sum of input + output |
| `estimated_cost` | float | API cost in USD |
| `model_used` | str? | Specific model identifier |

**Database Migration:**

```sql
ALTER TABLE jobs ADD COLUMN session_id TEXT;
ALTER TABLE jobs ADD COLUMN input_tokens INTEGER DEFAULT 0;
ALTER TABLE jobs ADD COLUMN output_tokens INTEGER DEFAULT 0;
ALTER TABLE jobs ADD COLUMN total_tokens INTEGER DEFAULT 0;
ALTER TABLE jobs ADD COLUMN estimated_cost REAL DEFAULT 0.0;
ALTER TABLE jobs ADD COLUMN model_used TEXT;
```

Migration is automatic and backward-compatible. Existing databases will be upgraded on first access.

## Cost Calculation

### Token Estimation

Token counting uses a simple character-based heuristic:

```python
def estimate_tokens(text: str) -> int:
    """
    Estimate tokens from text using 4 chars/token heuristic.

    This is an approximation. Actual tokenization depends on the
    specific model (GPT-4 uses tiktoken, Claude uses custom tokenizer).

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return max(1, len(text) // 4)
```

**Accuracy:** ~80-90% for English text. Different languages and code may vary.

### Provider Pricing

Pricing per million tokens (as of implementation):

```python
PROVIDER_PRICING = {
    'claude': {
        'input': 3.0,   # $3/M tokens
        'output': 15.0,  # $15/M tokens
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
            'gpt-4-turbo': {'input': 10.0, 'output': 30.0},
            'gpt-4': {'input': 30.0, 'output': 60.0},
        }
    },
    'gemini': {
        'input': 0.5,
        'output': 1.5,
        'models': {
            'gemini-1.5-pro': {'input': 3.5, 'output': 10.5},
            'gemini-1.5-flash': {'input': 0.075, 'output': 0.3},
        }
    }
}
```

**Note:** Prices may change. Update this dictionary as needed.

### Cost Calculation

```python
def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    provider: str,
    model: Optional[str] = None
) -> float:
    """
    Calculate estimated cost based on token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        provider: Provider name (claude, gpt4, gemini)
        model: Specific model identifier (optional)

    Returns:
        Estimated cost in USD
    """
    if provider not in PROVIDER_PRICING:
        return 0.0

    pricing = PROVIDER_PRICING[provider]

    # Use model-specific pricing if available
    if model and 'models' in pricing and model in pricing['models']:
        model_pricing = pricing['models'][model]
        input_rate = model_pricing['input']
        output_rate = model_pricing['output']
    else:
        # Fall back to provider defaults
        input_rate = pricing.get('input', 0.0)
        output_rate = pricing.get('output', 0.0)

    # Calculate cost (rates are per million tokens)
    input_cost = (input_tokens / 1_000_000) * input_rate
    output_cost = (output_tokens / 1_000_000) * output_rate

    return input_cost + output_cost
```

### Automatic Metrics Update

Jobs automatically calculate metrics on completion:

```python
def update_job_metrics(job: Job) -> Job:
    """
    Calculate and update job token and cost metrics.

    Called automatically by executor on job completion.
    """
    # Estimate tokens if not set
    if job.input_tokens == 0:
        job.input_tokens = estimate_tokens(job.input)

    if job.output_tokens == 0 and job.output:
        job.output_tokens = estimate_tokens(job.output)

    # Calculate totals
    job.total_tokens = job.input_tokens + job.output_tokens

    # Calculate cost
    if job.estimated_cost == 0.0:
        job.estimated_cost = calculate_cost(
            job.input_tokens,
            job.output_tokens,
            job.provider,
            job.model_used
        )

    return job
```

## API Reference

### GET /api/analytics

Get comprehensive dashboard analytics.

**Response:**

```json
{
  "total_jobs": 142,
  "total_sessions": 23,
  "total_cost": 2.4567,
  "total_tokens": 125000,
  "by_status": {
    "completed": 120,
    "failed": 12,
    "running": 5,
    "cancelled": 5
  },
  "by_mode": {
    "auto": 80,
    "chat": 40,
    "task": 15,
    "agent": 7
  },
  "by_provider": {
    "claude": 100,
    "gpt4": 30,
    "gemini": 12
  },
  "avg_duration": 45.2,
  "success_rate": 84.5
}
```

### GET /api/timeline

Get timeline view with session grouping.

**Query Parameters:**
- `session_id` (optional): Filter to specific session
- `limit` (optional): Max results (default: 100)
- `offset` (optional): Skip N results (default: 0)

**Response:**

```json
{
  "timeline": [
    {
      "session": {
        "id": "session-uuid-1",
        "name": "Feature Implementation",
        "total_jobs": 5,
        "completed_jobs": 4,
        "total_cost": 0.1234,
        "total_tokens": 5000,
        "created_at": "2025-01-19T10:00:00Z",
        "updated_at": "2025-01-19T11:30:00Z"
      },
      "jobs": [
        {
          "id": "job-uuid-1",
          "mode": "auto",
          "input": "Implement user authentication",
          "status": "completed",
          "provider": "claude",
          "session_id": "session-uuid-1",
          "input_tokens": 25,
          "output_tokens": 800,
          "total_tokens": 825,
          "estimated_cost": 0.0124,
          "created_at": "2025-01-19T10:00:00Z",
          "started_at": "2025-01-19T10:00:05Z",
          "finished_at": "2025-01-19T10:02:30Z",
          "exit_code": 0
        }
        // ... more jobs
      ]
    },
    {
      "session": null,
      "jobs": [
        // Ungrouped jobs without session_id
      ]
    }
  ],
  "total_jobs": 142
}
```

### GET /api/sessions

List all sessions.

**Query Parameters:**
- `limit` (optional): Max results (default: 100)
- `offset` (optional): Skip N results (default: 0)

**Response:**

```json
{
  "sessions": [
    {
      "id": "session-uuid",
      "name": "Feature Implementation",
      "total_jobs": 5,
      "completed_jobs": 4,
      "total_cost": 0.1234,
      "total_tokens": 5000,
      "created_at": "2025-01-19T10:00:00Z",
      "updated_at": "2025-01-19T11:30:00Z"
    }
  ],
  "total": 23,
  "limit": 100,
  "offset": 0
}
```

### GET /api/sessions/{session_id}

Get specific session details.

**Response:**

```json
{
  "id": "session-uuid",
  "name": "Feature Implementation",
  "total_jobs": 5,
  "completed_jobs": 4,
  "total_cost": 0.1234,
  "total_tokens": 5000,
  "created_at": "2025-01-19T10:00:00Z",
  "updated_at": "2025-01-19T11:30:00Z"
}
```

### GET /api/sessions/{session_id}/jobs

Get all jobs in a session.

**Response:**

```json
{
  "session": {
    "id": "session-uuid",
    "name": "Feature Implementation",
    ...
  },
  "jobs": [
    {
      "id": "job-uuid-1",
      "mode": "auto",
      "session_id": "session-uuid",
      ...
    }
  ]
}
```

## Dashboard UI

### Timeline Tab

The Timeline tab provides a visual interface for viewing job history and analytics:

**Analytics Cards:**

1. **Total Jobs** - Count of all jobs across all sessions
2. **Total Cost** - Cumulative estimated API costs
3. **Success Rate** - Percentage of completed jobs
4. **Avg Duration** - Average job execution time
5. **By Status** - Breakdown by job status (completed, failed, etc.)
6. **By Mode** - Breakdown by execution mode (auto, chat, task, agent)

**Timeline View:**

- Jobs grouped by session (or "Ungrouped" for jobs without sessions)
- Session headers show aggregated metrics:
  - Total cost for session
  - Total tokens used
  - Completion ratio (X/Y completed)
- Individual job cards display:
  - Mode and agent name (if applicable)
  - Input text (truncated to 100 chars)
  - Status badge with color coding
  - Time ago and duration
  - Provider icon
  - **Cost in green** ($0.0012)
  - **Token count in gray** (1.2K tok)

**Auto-Refresh:**

Timeline and analytics refresh automatically when the tab is opened.

## Usage Examples

### Python: Create Session and Submit Jobs

```python
import requests
import json
from datetime import datetime

# Create a session
session_data = {
    "id": "my-session-123",
    "name": "Bug Fix Sprint",
    "created_at": datetime.utcnow().isoformat() + "Z",
    "updated_at": datetime.utcnow().isoformat() + "Z",
}

# Submit jobs in this session
job_data = {
    "mode": "auto",
    "input": "Fix authentication bug",
    "provider": "claude",
    "session_id": "my-session-123"
}

response = requests.post('http://localhost:3000/api/runs', json=job_data)
job = response.json()

print(f"Job submitted: {job['id']}")
print(f"Session: {job['session_id']}")

# Later, check session metrics
session = requests.get(f'http://localhost:3000/api/sessions/my-session-123').json()
print(f"Session cost: ${session['total_cost']:.4f}")
print(f"Session tokens: {session['total_tokens']}")
```

### JavaScript: Display Analytics

```javascript
// Fetch analytics
const response = await fetch('/api/analytics');
const analytics = await response.json();

// Display cost
const costElement = document.getElementById('total-cost');
costElement.textContent = `$${analytics.total_cost.toFixed(4)}`;

// Display token usage
const tokensElement = document.getElementById('total-tokens');
const tokensFormatted = analytics.total_tokens >= 1000000
  ? `${(analytics.total_tokens / 1000000).toFixed(2)}M`
  : `${(analytics.total_tokens / 1000).toFixed(1)}K`;
tokensElement.textContent = tokensFormatted;

// Display success rate
const rateElement = document.getElementById('success-rate');
rateElement.textContent = `${analytics.success_rate.toFixed(1)}%`;
```

### cURL: Timeline Query

```bash
# Get timeline for specific session
curl "http://localhost:3000/api/timeline?session_id=my-session-123"

# Get overall analytics
curl http://localhost:3000/api/analytics

# Get all sessions
curl http://localhost:3000/api/sessions
```

## Implementation Details

### Token Estimation Accuracy

The character-based estimation (1 token ≈ 4 chars) provides reasonable accuracy for cost planning:

| Text Type | Accuracy |
|-----------|----------|
| English prose | 85-95% |
| Code (Python, JS) | 75-85% |
| JSON/YAML | 70-80% |
| Chinese/Japanese | 60-70% |

For production billing, integrate actual tokenizers:
- **Claude**: Anthropic's tokenizer API
- **GPT-4**: `tiktoken` library
- **Gemini**: Google's tokenizer API

### Session Lifecycle

Sessions are currently created manually via API. Future enhancements could add:

1. **Auto-session creation**: Start new session when launching dashboard
2. **Session naming**: Auto-generate names from first job input
3. **Session merging**: Combine related sessions
4. **Session archiving**: Mark old sessions as archived

### Cost Accuracy

Cost estimates are based on public pricing and token estimation. Actual costs may differ due to:

- Token estimation variance (see above)
- Pricing changes by providers
- Caching or other discounts
- Model-specific variations

**Recommendation:** Treat estimates as planning tools, not billing data. Cross-reference with actual provider invoices.

### Database Performance

**Indexes:**

The sessions table has an index on `created_at` for efficient timeline queries:

```sql
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
```

Jobs table already has indexes on `status` and `created_at` from Phase 2a.

**Query Optimization:**

Timeline queries use:
1. `LIMIT` to cap result size
2. `OFFSET` for pagination
3. In-memory grouping by session (acceptable for <10K jobs)

For larger datasets (>100K jobs), consider:
- Server-side session grouping with SQL `GROUP BY`
- Materialized views for analytics
- Time-based partitioning

## Testing

### Unit Tests

```bash
# Test token estimation
python -c "
from codecompanion.dashboard.models import estimate_tokens
assert estimate_tokens('Hello world') == 2
assert estimate_tokens('a' * 100) == 25
print('✓ Token estimation tests passed')
"

# Test cost calculation
python -c "
from codecompanion.dashboard.models import calculate_cost
cost = calculate_cost(1000, 2000, 'claude')
assert 0.032 < cost < 0.034  # $0.033 expected
print('✓ Cost calculation tests passed')
"

# Test job metrics update
python -c "
from codecompanion.dashboard.models import Job, JobMode, JobStatus, update_job_metrics
from datetime import datetime

job = Job(
    id='test',
    mode=JobMode.CHAT,
    input='Test input',
    agent_name=None,
    provider='claude',
    target_root='/tmp',
    status=JobStatus.COMPLETED,
    created_at=datetime.utcnow().isoformat() + 'Z',
    output='Test output'
)

update_job_metrics(job)
assert job.input_tokens > 0
assert job.output_tokens > 0
assert job.total_tokens == job.input_tokens + job.output_tokens
assert job.estimated_cost > 0
print('✓ Job metrics tests passed')
"
```

### Integration Tests

```bash
# Start dashboard
codecompanion --dashboard &
DASHBOARD_PID=$!

# Wait for startup
sleep 2

# Test analytics endpoint
curl http://localhost:3000/api/analytics | jq .

# Test timeline endpoint
curl http://localhost:3000/api/timeline | jq .

# Test sessions endpoint
curl http://localhost:3000/api/sessions | jq .

# Cleanup
kill $DASHBOARD_PID
```

## Migration from Phase 2a

Phase 3a is fully backward-compatible. Existing jobs will:

1. Automatically gain new columns with default values
2. Calculate metrics on next read (lazy migration)
3. Continue working without any code changes

**Manual Migration (Optional):**

To recalculate metrics for existing jobs:

```python
from codecompanion.dashboard.models import get_job_store, update_job_metrics

store = get_job_store()
jobs = store.list(limit=10000)

for job in jobs:
    if job.total_tokens == 0:
        update_job_metrics(job)
        store.update(job)
        print(f"Updated job {job.id}: {job.total_tokens} tokens, ${job.estimated_cost:.6f}")
```

## Configuration

### Update Provider Pricing

Edit `codecompanion/dashboard/models.py`:

```python
PROVIDER_PRICING = {
    'claude': {
        'input': 3.0,   # Update these values
        'output': 15.0,
        'models': {
            'claude-3-sonnet-20240229': {'input': 3.0, 'output': 15.0},
            # Add new models here
        }
    },
    # ...
}
```

### Custom Token Estimation

Replace `estimate_tokens()` with actual tokenizer:

```python
import tiktoken  # For GPT-4

def estimate_tokens(text: str, model: str = 'gpt-4') -> int:
    """Use tiktoken for accurate GPT-4 token counting."""
    if not text:
        return 0

    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))
```

## Troubleshooting

### Cost Estimates Too High/Low

Check:
1. Token estimation accuracy for your text type
2. Provider pricing in `PROVIDER_PRICING`
3. Model-specific vs provider-default pricing

### Session Jobs Not Grouping

Ensure:
1. `session_id` is set when creating jobs
2. Session exists in database
3. Timeline query includes correct `session_id`

### Database Migration Fails

If automatic migration doesn't work:

```bash
# Check current schema
sqlite3 .cc/jobs.db "PRAGMA table_info(jobs);"

# Manual migration
sqlite3 .cc/jobs.db "
ALTER TABLE jobs ADD COLUMN session_id TEXT;
ALTER TABLE jobs ADD COLUMN input_tokens INTEGER DEFAULT 0;
ALTER TABLE jobs ADD COLUMN output_tokens INTEGER DEFAULT 0;
ALTER TABLE jobs ADD COLUMN total_tokens INTEGER DEFAULT 0;
ALTER TABLE jobs ADD COLUMN estimated_cost REAL DEFAULT 0.0;
ALTER TABLE jobs ADD COLUMN model_used TEXT;
"
```

## Future Enhancements

Phase 3a provides the foundation. Future improvements could include:

### Phase 3b: Enhanced Cancellation
- Kill entire subprocess tree (not just main process)
- Graceful vs forced cancellation
- Cleanup orphaned processes

### Phase 4: Advanced Features
1. **Cost Transparency**
   - Real-time cost tracking during execution
   - Budget alerts and limits
   - Cost per session/user/project

2. **Agent Library**
   - Pre-built agents for common tasks
   - Agent marketplace
   - Custom agent creation UI

3. **Smart Model Selection**
   - Auto-select best model for task
   - Cost/quality tradeoffs
   - Model performance tracking

## References

- [Phase 0: Security Foundation](SECURITY.md)
- [Phase 1a: Basic --init Command](../codecompanion/workspace.py)
- [Phase 1b: CLI UX Polish](../codecompanion/task_handler.py)
- [Phase 2a: Async Execution Backend](ASYNC_EXECUTION.md)
- [Phase 2b: Dashboard Frontend - Projects Tab](../codecompanion/templates/dashboard.html)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [OpenAI Pricing](https://openai.com/pricing)
- [Google AI Pricing](https://ai.google.dev/pricing)

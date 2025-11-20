# Cost Transparency & Budget Management

**Phase 4 Implementation - Budget Control & Spending Visibility**

## Overview

Phase 4 builds upon the Timeline & Sessions system (Phase 3a) by adding comprehensive budget management and spending controls. This enables users to set spending limits, track budget usage in real-time, and receive alerts when approaching or exceeding limits.

### Key Features

- ✅ **Multi-Period Budgets**: Daily, weekly, monthly, per-session, and lifetime budgets
- ✅ **Real-Time Tracking**: Automatic spending updates after job completion
- ✅ **Alert Thresholds**: Configurable warning levels (default 80%)
- ✅ **Budget Status Indicators**: Visual progress bars with color coding
- ✅ **Spending Analytics**: Breakdowns by provider, mode, status, and session
- ✅ **Budget CRUD Operations**: Full create, read, update, delete, and reset functionality
- ✅ **Overview Dashboard Integration**: At-a-glance budget status on main dashboard

## Architecture

```
┌────────────────────────────────────────────────┐
│  Budgets Tab (Frontend)                        │
│  - Budget creation form                        │
│  - Budget cards with usage bars                │
│  - Spending summary cards                      │
│  - Enable/disable, edit, delete, reset actions │
└───────────────────┬────────────────────────────┘
                    │
                    ↓
┌────────────────────────────────────────────────┐
│  API Endpoints                                 │
│  - POST /api/budgets (create)                  │
│  - GET /api/budgets (list)                     │
│  - GET /api/budgets/{id} (get one)             │
│  - PUT /api/budgets/{id} (update)              │
│  - DELETE /api/budgets/{id} (delete)           │
│  - POST /api/budgets/{id}/reset (reset period) │
│  - GET /api/spending/summary (analytics)       │
└───────────────────┬────────────────────────────┘
                    │
                    ↓
┌────────────────────────────────────────────────┐
│  Budget Model & Store                          │
│  - Budget: dataclass with computed properties  │
│  - BudgetStore: SQLite-backed CRUD             │
│  - Automatic spending updates                  │
│  - Period-based resets                         │
└───────────────────┬────────────────────────────┘
                    │
                    ↓
┌────────────────────────────────────────────────┐
│  Job Executor Integration                      │
│  - _update_budgets() called after job          │
│  - Automatic cost tracking                     │
│  - Non-session budgets only (session separate) │
└────────────────────────────────────────────────┘
```

## Data Models

### Budget Model

```python
@dataclass
class Budget:
    id: str                          # UUID identifier
    name: str                        # Human-readable name
    period: BudgetPeriod             # daily, weekly, monthly, session, total
    limit: float                     # Spending limit ($)
    current_spending: float = 0.0    # Current period spending
    alert_threshold: float = 80.0    # Alert percentage (0-100)
    enabled: bool = True             # Active/inactive status
    created_at: str | None           # ISO timestamp
    period_start: str | None         # Period start time
    period_end: str | None           # Period end time (for time-based)
    last_alert_at: str | None        # Last alert timestamp

    def usage_percentage(self) -> float:
        """Calculate usage as percentage of limit"""
        if self.limit <= 0:
            return 0.0
        return (self.current_spending / self.limit) * 100.0

    def remaining(self) -> float:
        """Calculate remaining budget"""
        return max(0.0, self.limit - self.current_spending)

    def is_exceeded(self) -> bool:
        """Check if budget is exceeded"""
        return self.current_spending >= self.limit

    def should_alert(self) -> bool:
        """Check if alert threshold reached"""
        return self.usage_percentage() >= self.alert_threshold
```

### Budget Period Types

```python
class BudgetPeriod(str, Enum):
    DAILY = "daily"       # Resets every 24 hours
    WEEKLY = "weekly"     # Resets every 7 days
    MONTHLY = "monthly"   # Resets every 30 days
    SESSION = "session"   # Per-session tracking (manual reset)
    TOTAL = "total"       # Lifetime total (manual reset)
```

**Database Schema:**

```sql
CREATE TABLE budgets (
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
);

CREATE INDEX idx_budgets_period ON budgets(period);
CREATE INDEX idx_budgets_enabled ON budgets(enabled);
```

## API Endpoints

### 1. Create Budget

**Endpoint:** `POST /api/budgets`

**Request Body:**
```json
{
    "name": "Daily Development Budget",
    "period": "daily",
    "limit": 10.0,
    "alert_threshold": 80
}
```

**Response (201):**
```json
{
    "id": "uuid-here",
    "name": "Daily Development Budget",
    "period": "daily",
    "limit": 10.0,
    "current_spending": 0.0,
    "alert_threshold": 80.0,
    "enabled": true,
    "created_at": "2025-11-20T20:00:00Z",
    "period_start": "2025-11-20T20:00:00Z",
    "period_end": "2025-11-21T20:00:00Z",
    "last_alert_at": null
}
```

**Validation:**
- `name`: Required, non-empty string
- `period`: Must be one of: daily, weekly, monthly, session, total
- `limit`: Required, must be > 0
- `alert_threshold`: Optional, must be 0-100 (default 80)

**Period Calculations:**
- **daily**: period_end = now + 1 day
- **weekly**: period_end = now + 7 days
- **monthly**: period_end = now + 30 days
- **session/total**: No period_end (manual reset)

### 2. List Budgets

**Endpoint:** `GET /api/budgets`

**Query Parameters:**
- `period` (optional): Filter by period type
- `enabled_only` (optional): Show only enabled budgets (default: false)

**Response (200):**
```json
{
    "budgets": [
        {
            "id": "uuid-1",
            "name": "Daily Budget",
            "period": "daily",
            "limit": 10.0,
            "current_spending": 2.5,
            "alert_threshold": 80.0,
            "enabled": true,
            ...
        }
    ],
    "total": 1
}
```

### 3. Get Budget Details

**Endpoint:** `GET /api/budgets/{budget_id}`

**Response (200):**
```json
{
    "id": "uuid-here",
    "name": "Daily Budget",
    "period": "daily",
    "limit": 10.0,
    "current_spending": 2.5,
    "alert_threshold": 80.0,
    "enabled": true,
    "created_at": "2025-11-20T20:00:00Z",
    "period_start": "2025-11-20T20:00:00Z",
    "period_end": "2025-11-21T20:00:00Z",
    "last_alert_at": null,
    "usage_percentage": 25.0,
    "remaining": 7.5,
    "is_exceeded": false,
    "should_alert": false
}
```

**Computed Fields:**
- `usage_percentage`: Current spending as % of limit
- `remaining`: Amount left in budget
- `is_exceeded`: True if spending >= limit
- `should_alert`: True if usage >= alert_threshold

### 4. Update Budget

**Endpoint:** `PUT /api/budgets/{budget_id}`

**Request Body (partial updates supported):**
```json
{
    "limit": 15.0,
    "alert_threshold": 85,
    "enabled": true
}
```

**Response (200):** Updated budget object

**Updatable Fields:**
- `name`: Budget name
- `limit`: Spending limit
- `alert_threshold`: Alert percentage
- `enabled`: Active status

**Non-updatable:**
- `id`, `period`, `created_at`, `current_spending`, `period_start`, `period_end`

### 5. Delete Budget

**Endpoint:** `DELETE /api/budgets/{budget_id}`

**Response (200):**
```json
{
    "success": true,
    "message": "Budget deleted successfully"
}
```

### 6. Reset Budget Period

**Endpoint:** `POST /api/budgets/{budget_id}/reset`

**Response (200):** Budget object with:
- `current_spending` reset to 0.0
- `period_start` updated to now
- `period_end` recalculated (for time-based periods)
- `last_alert_at` cleared

**Use Cases:**
- Manual reset of session/total budgets
- Force reset of time-based budgets before period expires

### 7. Spending Summary

**Endpoint:** `GET /api/spending/summary`

**Query Parameters:**
- `period` (optional): Filter by time period (today, week, month, all)
- `start_date` (optional): ISO timestamp start
- `end_date` (optional): ISO timestamp end

**Response (200):**
```json
{
    "total_spending": 5.25,
    "total_jobs": 42,
    "by_provider": {
        "claude": {"cost": 3.50, "jobs": 30},
        "gpt4": {"cost": 1.75, "jobs": 12}
    },
    "by_mode": {
        "auto": {"cost": 2.00, "jobs": 10},
        "task": {"cost": 2.50, "jobs": 20},
        "chat": {"cost": 0.75, "jobs": 12}
    },
    "by_status": {
        "completed": {"cost": 5.00, "jobs": 40},
        "failed": {"cost": 0.25, "jobs": 2}
    },
    "by_session": [
        {
            "session_id": "uuid-1",
            "name": "Session A",
            "cost": 3.00,
            "jobs": 25
        }
    ],
    "timeline": [
        {
            "date": "2025-11-20",
            "cost": 2.50,
            "jobs": 20
        }
    ]
}
```

## Budget Integration with Job Execution

### Automatic Spending Updates

When a job completes (success or failure), the executor automatically updates all active non-session budgets:

```python
def _update_budgets(self, job: Job):
    """Update budget spending after job completion"""
    if job.estimated_cost <= 0:
        return  # No cost to track

    budget_store = get_budget_store()
    budgets = budget_store.list(enabled_only=True)

    for budget in budgets:
        # Skip session budgets (handled separately)
        if budget.period.value == 'session':
            continue

        # Add spending to budget
        budget_store.add_spending(budget.id, job.estimated_cost)
```

**Called After:**
- Job completes successfully
- Job fails with error
- Job is cancelled

**Integration Points:**
1. `executor.py::_execute_job()` → `_update_budgets()` in finally block
2. After `update_job_metrics()` calculates cost
3. Updates all enabled budgets (except session type)

## UI Components

### 1. Budgets Tab

**Location:** Main dashboard navigation, 4th tab

**Components:**
- **Budget Management Section**
  - "Create Budget" button (shows/hides form)
  - Budget creation form (name, period, limit, threshold)
  - Budget cards grid with:
    - Budget name and period type
    - Enable/disable toggle
    - Usage progress bar with color coding
    - Stats: spent, remaining, limit, alert threshold
    - Actions: Reset Period, Edit, Delete

- **Spending Summary Section**
  - Total spending card
  - By provider breakdown
  - By mode breakdown
  - By status breakdown

### 2. Overview Tab Integration

**Active Budgets Card:**
- Shows all enabled budgets
- Visual progress bars with color coding:
  - Green: < 50% usage
  - Yellow: 50-80% usage
  - Red: > 80% usage or exceeded
- Status indicators:
  - ✓ Healthy (< threshold)
  - ⚠ Warning (>= threshold)
  - ⚠ EXCEEDED (>= limit)
- "Manage Budgets" button → navigates to Budgets tab

### Budget Card Color Coding

```css
/* Default: green (healthy) */
.budget-progress-bar {
    background: linear-gradient(90deg, #22c55e, #16a34a);
}

/* Warning: yellow/orange (>= alert threshold) */
.budget-progress-bar.warning {
    background: linear-gradient(90deg, #f59e0b, #d97706);
}

/* Exceeded: red (>= limit) */
.budget-progress-bar.exceeded {
    background: linear-gradient(90deg, #ef4444, #dc2626);
}
```

## JavaScript Functions

### Budget Management

```javascript
// Form management
showCreateBudgetForm()           // Show budget creation form
hideCreateBudgetForm()           // Hide and reset form

// CRUD operations
createBudget()                   // POST /api/budgets
refreshBudgets()                 // GET /api/budgets
toggleBudget(id, enabled)        // PUT /api/budgets/{id}
editBudget(id)                   // PUT /api/budgets/{id}
deleteBudget(id)                 // DELETE /api/budgets/{id}
resetBudget(id)                  // POST /api/budgets/{id}/reset

// Rendering
renderBudgets(budgets)           // Render budget cards
renderSpendingSummary(data)      // Render spending breakdown

// Overview integration
refreshOverviewBudgets()         // GET /api/budgets?enabled_only=true
renderOverviewBudgets(budgets)   // Render in overview tab
```

## Usage Examples

### 1. Create a Daily Budget

```bash
curl -X POST http://localhost:8000/api/budgets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Development",
    "period": "daily",
    "limit": 10.0,
    "alert_threshold": 80
  }'
```

### 2. List All Active Budgets

```bash
curl http://localhost:8000/api/budgets?enabled_only=true
```

### 3. Update Budget Limit

```bash
curl -X PUT http://localhost:8000/api/budgets/{budget_id} \
  -H "Content-Type: application/json" \
  -d '{"limit": 15.0}'
```

### 4. Reset Budget Period

```bash
curl -X POST http://localhost:8000/api/budgets/{budget_id}/reset
```

### 5. Get Spending Summary

```bash
curl http://localhost:8000/api/spending/summary?period=today
```

## Testing

### API Testing

All budget endpoints tested successfully:

```bash
# 1. Create budget
✓ POST /api/budgets - Returns 201 with full budget object

# 2. List budgets
✓ GET /api/budgets - Returns budgets array with total count

# 3. Get single budget
✓ GET /api/budgets/{id} - Returns budget with computed fields

# 4. Update budget
✓ PUT /api/budgets/{id} - Updates fields and returns updated object

# 5. Reset budget
✓ POST /api/budgets/{id}/reset - Resets spending and updates periods

# 6. Delete budget
✓ DELETE /api/budgets/{id} - Returns success message

# 7. Spending summary
✓ GET /api/spending/summary - Returns comprehensive breakdowns
```

### UI Testing

Dashboard elements verified:

```bash
✓ Budgets tab button in navigation
✓ Budget CSS classes in HTML
✓ Budget JavaScript functions loaded
✓ Overview budget indicators rendered
✓ Budget form validation working
✓ Budget cards rendering correctly
✓ Spending summary displaying
```

## Implementation Files

### Backend
- `codecompanion/dashboard/models.py` (+367 lines)
  - Budget dataclass with computed properties
  - BudgetPeriod enum
  - BudgetStore class with CRUD operations
  - Database schema and migrations

- `codecompanion/dashboard/app.py` (+441 lines)
  - 7 budget API endpoints
  - Spending summary endpoint with analytics
  - Request validation and error handling

- `codecompanion/dashboard/executor.py` (+24 lines)
  - _update_budgets() integration
  - Automatic cost tracking after job completion

### Frontend
- `codecompanion/templates/dashboard.html` (+695 lines)
  - Budgets tab with management UI
  - Budget creation form
  - Budget cards with progress bars
  - Spending summary visualization
  - Overview tab budget indicators
  - CSS styles for budgets
  - JavaScript functions for CRUD operations

## Migration Notes

**Database Changes:**
- New table: `budgets`
- Indexes: `idx_budgets_period`, `idx_budgets_enabled`
- No changes to existing tables

**Backward Compatibility:**
- Budget system is entirely additive
- Existing jobs/sessions unaffected
- Dashboard works without budgets configured

## Future Enhancements

### Potential Improvements
- **Email/Webhook Alerts**: Send notifications when thresholds reached
- **Budget Templates**: Pre-configured budget presets
- **Historical Tracking**: Budget usage over time charts
- **Multi-Currency**: Support for different currencies
- **Cost Forecasting**: Predict when budget will be exhausted
- **Shared Budgets**: Team budgets across multiple users
- **Budget Reports**: Exportable PDF/CSV reports
- **Rolling Windows**: 7-day or 30-day rolling averages
- **Budget Approval**: Require approval before exceeding limits
- **Cost Optimization Tips**: AI-suggested ways to reduce spending

## Related Documentation

- [Timeline & Sessions System](TIMELINE_SESSIONS.md) - Phase 3a (cost tracking foundation)
- [Async Job Execution](ASYNC_EXECUTION.md) - Phase 2a/2b (job execution system)
- [Enhanced Cancellation](ENHANCED_CANCELLATION.md) - Phase 3b (process management)
- [Security Architecture](SECURITY.md) - Phase 0 (TargetContext & safety)

## Commit History

- **5429b2d**: Phase 4 Part 1 - Budget models, store, and database
- **0c420c4**: Phase 4 Part 2 - Budget API endpoints and spending analytics
- **[pending]**: Phase 4 Part 3 - Budget UI and dashboard integration

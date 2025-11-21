"""
FastAPI dashboard application for CodeCompanion Control Tower.
Provides a web-based live status board with async job execution.

Features:
- Non-blocking agent execution via background job queue
- Real-time job status tracking
- Job cancellation support
- Persistent job history with SQLite
"""
import os
import sys
from pathlib import Path
from typing import Optional, List

# Suppress Streamlit warnings before any imports that might trigger it
os.environ['STREAMLIT_LOGGER_LEVEL'] = 'error'

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
from datetime import datetime

# Import info gathering functions
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from codecompanion.info_core import gather_all_info

# Import async job execution components
from .models import Job, JobStatus, JobMode, Session, Budget, BudgetPeriod, get_job_store, get_session_store, get_budget_store
from .executor import get_executor

# Import model catalog (MIS v1)
from codecompanion.model_catalog import get_catalog_store, sync_openrouter_models
import logging

logger = logging.getLogger(__name__)


app = FastAPI(
    title="CodeCompanion Control Tower",
    description="Live status dashboard for CodeCompanion with async job execution",
    version="0.2.0",
)


@app.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Serve the main dashboard HTML page."""
    template_path = Path(__file__).parent.parent / "templates" / "dashboard.html"

    if not template_path.exists():
        return HTMLResponse(
            content="<h1>Dashboard template not found</h1>",
            status_code=500,
        )

    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    return HTMLResponse(content=html_content)


@app.get("/api/info")
async def get_info():
    """
    API endpoint that returns current system information.
    This is the same data structure returned by `codecompanion --info --raw`.

    Returns JSON with:
    - bootstrap: Project and bootstrap status
    - agent_workflow: Agent files and completion status
    - providers: LLM provider configurations and API key status
    - pipeline: Pipeline execution history (placeholder)
    - errors: Error history and recovery status (placeholder)
    - recommendations: System recommendations based on current state
    """
    project_root = os.getcwd()
    info_data = gather_all_info(project_root)
    return JSONResponse(content=info_data)


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "codecompanion-dashboard"}


# ============================================================================
# ASYNC JOB EXECUTION API
# ============================================================================


@app.post("/api/runs")
async def create_run(request: Request):
    """
    Create a new async run/job.

    Request body (JSON):
    {
        "mode": "chat" | "auto" | "agent" | "task",
        "input": "<user instruction>",
        "agent": "<optional agent name>",  # required for mode=agent
        "provider": "<optional provider, defaults to claude>",
        "target_root": "<optional target directory, defaults to cwd>"
    }

    Response (JSON):
    {
        "id": "<job_id>",
        "status": "pending",
        "mode": "...",
        "created_at": "...",
        ...
    }
    """
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON request body: {str(e)}"
        )

    # Extract and validate parameters
    mode_str = body.get("mode", "chat")
    input_text = body.get("input", "").strip()
    agent_name = body.get("agent")
    provider = body.get("provider", "claude")
    target_root = body.get("target_root")

    # Validate input
    if not input_text:
        raise HTTPException(
            status_code=400,
            detail="Input text is required"
        )

    # Validate mode
    try:
        mode = JobMode(mode_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {mode_str}. Use 'chat', 'auto', 'agent', or 'task'"
        )

    # Validate agent name for agent mode
    if mode == JobMode.AGENT and not agent_name:
        raise HTTPException(
            status_code=400,
            detail="Agent name is required for mode='agent'"
        )

    # Submit job to executor
    executor = get_executor()
    job = executor.submit(
        mode=mode,
        input_text=input_text,
        agent_name=agent_name,
        provider=provider,
        target_root=target_root
    )

    return JSONResponse(content=job.to_dict())


@app.get("/api/runs")
async def list_runs(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List all runs with optional filtering.

    Query parameters:
    - status: Filter by status (pending, running, completed, failed, cancelled)
    - limit: Maximum number of runs to return (default: 100)
    - offset: Number of runs to skip (default: 0)

    Response (JSON):
    {
        "runs": [{...}, {...}, ...],
        "total": <total_count>,
        "limit": <limit>,
        "offset": <offset>
    }
    """
    # Validate status
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}"
            )

    # Get jobs from store
    job_store = get_job_store()
    jobs = job_store.list(status=status_filter, limit=limit, offset=offset)
    total = job_store.count(status=status_filter)

    return JSONResponse(content={
        "runs": [job.to_dict() for job in jobs],
        "total": total,
        "limit": limit,
        "offset": offset
    })


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    """
    Get a specific run by ID.

    Response (JSON):
    {
        "id": "<run_id>",
        "status": "...",
        "mode": "...",
        "output": "...",  # current output (may be incomplete if still running)
        ...
    }
    """
    executor = get_executor()
    job = executor.get_status(run_id)

    if not job:
        raise HTTPException(status_code=404, detail="Run not found")

    # Include current output if job is running
    if job.status == JobStatus.RUNNING:
        current_output = executor.get_output(run_id)
        if current_output:
            job.output = current_output

    return JSONResponse(content=job.to_dict())


@app.post("/api/runs/{run_id}/cancel")
async def cancel_run(run_id: str, mode: str = "graceful"):
    """
    Cancel a running job with specified mode.

    Query Parameters:
        mode: Cancellation mode - "graceful" (default) or "forced"
              - graceful: SIGTERM -> wait 5s -> SIGKILL
              - forced: SIGKILL immediately

    Response (JSON):
    {
        "success": true/false,
        "message": "...",
        "mode": "graceful|forced"
    }
    """
    from .process_manager import CancellationMode

    # Validate mode
    try:
        cancel_mode = CancellationMode(mode.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cancellation mode: {mode}. Use 'graceful' or 'forced'"
        )

    executor = get_executor()
    success = executor.cancel(run_id, cancel_mode)

    if success:
        return JSONResponse(content={
            "success": True,
            "message": f"Run {run_id} cancelled successfully ({mode} mode)",
            "mode": mode
        })
    else:
        return JSONResponse(
            content={
                "success": False,
                "message": f"Run {run_id} not found or already finished"
            },
            status_code=404
        )


@app.get("/api/runs/{run_id}/stream")
async def stream_run_output(run_id: str):
    """
    Stream run output and status using Server-Sent Events (SSE).

    This endpoint provides real-time updates for a running job,
    sending periodic status updates until the job finishes.

    Response: text/event-stream (Server-Sent Events)

    Event format:
    data: {"status": "...", "output": "...", "finished": true/false}
    """
    executor = get_executor()

    # Check if run exists
    job = executor.get_status(run_id)
    if not job:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_generator():
        """Generate SSE events for job status updates."""
        last_output_length = 0

        while True:
            # Get current job status
            job = executor.get_status(run_id)
            if not job:
                break

            # Get current output
            current_output = executor.get_output(run_id) or ""

            # Only send new output (incremental)
            new_output = current_output[last_output_length:]
            last_output_length = len(current_output)

            # Check if job is finished
            is_finished = job.status in [
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED
            ]

            # Send update event
            event_data = {
                "status": job.status.value,
                "output": new_output,
                "finished": is_finished,
                "exit_code": job.exit_code,
                "error": job.error
            }

            yield f"data: {json.dumps(event_data)}\n\n"

            # If finished, stop streaming
            if is_finished:
                break

            # Wait before next update (1 second)
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# ============================================================================
# SESSIONS API
# ============================================================================


@app.get("/api/sessions")
async def list_sessions(limit: int = 100, offset: int = 0):
    """
    List all sessions.

    Query parameters:
    - limit: Maximum number of sessions to return (default: 100)
    - offset: Number of sessions to skip (default: 0)

    Response (JSON):
    {
        "sessions": [{...}, {...}, ...],
        "total": <total_count>,
        "limit": <limit>,
        "offset": <offset>
    }
    """
    session_store = get_session_store()
    sessions = session_store.list(limit=limit, offset=offset)
    total = session_store.count()

    return JSONResponse(content={
        "sessions": [session.to_dict() for session in sessions],
        "total": total,
        "limit": limit,
        "offset": offset
    })


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get a specific session by ID.

    Response (JSON):
    {
        "id": "<session_id>",
        "name": "...",
        "total_jobs": ...,
        "total_cost": ...,
        ...
    }
    """
    session_store = get_session_store()
    session = session_store.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return JSONResponse(content=session.to_dict())


@app.get("/api/sessions/{session_id}/jobs")
async def get_session_jobs(session_id: str):
    """
    Get all jobs for a specific session.

    Response (JSON):
    {
        "session": {...},
        "jobs": [{...}, {...}, ...]
    }
    """
    session_store = get_session_store()
    job_store = get_job_store()

    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all jobs for this session
    all_jobs = job_store.list(limit=1000)  # Get enough jobs
    session_jobs = [job for job in all_jobs if job.session_id == session_id]

    return JSONResponse(content={
        "session": session.to_dict(),
        "jobs": [job.to_dict() for job in session_jobs]
    })


# ============================================================================
# TIMELINE & ANALYTICS API
# ============================================================================


@app.get("/api/timeline")
async def get_timeline(
    session_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get timeline view of jobs with optional session filtering.

    Timeline shows jobs chronologically grouped by session.

    Query parameters:
    - session_id: Optional session ID to filter by
    - limit: Maximum number of jobs to return (default: 100)
    - offset: Number of jobs to skip (default: 0)

    Response (JSON):
    {
        "timeline": [
            {
                "session": {...} or null,
                "jobs": [{...}, {...}, ...]
            },
            ...
        ],
        "total_jobs": <total_count>
    }
    """
    job_store = get_job_store()
    session_store = get_session_store()

    # Get jobs
    if session_id:
        all_jobs = job_store.list(limit=1000)
        jobs = [job for job in all_jobs if job.session_id == session_id]
    else:
        jobs = job_store.list(limit=limit, offset=offset)

    # Group by session
    sessions_map = {}
    for job in jobs:
        sid = job.session_id or "ungrouped"
        if sid not in sessions_map:
            sessions_map[sid] = []
        sessions_map[sid].append(job)

    # Build timeline
    timeline = []
    for sid, job_list in sessions_map.items():
        if sid == "ungrouped":
            session_data = None
        else:
            session = session_store.get(sid)
            session_data = session.to_dict() if session else None

        timeline.append({
            "session": session_data,
            "jobs": [job.to_dict() for job in job_list]
        })

    return JSONResponse(content={
        "timeline": timeline,
        "total_jobs": len(jobs)
    })


@app.get("/api/analytics")
async def get_analytics():
    """
    Get analytics dashboard data.

    Response (JSON):
    {
        "total_jobs": ...,
        "total_sessions": ...,
        "total_cost": ...,
        "total_tokens": ...,
        "by_status": {...},
        "by_mode": {...},
        "by_provider": {...},
        "avg_duration": ...,
        "success_rate": ...
    }
    """
    job_store = get_job_store()
    session_store = get_session_store()

    # Get all jobs
    all_jobs = job_store.list(limit=10000)  # Get all jobs

    # Calculate metrics
    total_jobs = len(all_jobs)
    total_sessions = session_store.count()

    total_cost = sum(job.estimated_cost for job in all_jobs)
    total_tokens = sum(job.total_tokens for job in all_jobs)

    # Group by status
    by_status = {}
    for job in all_jobs:
        status = job.status.value
        by_status[status] = by_status.get(status, 0) + 1

    # Group by mode
    by_mode = {}
    for job in all_jobs:
        mode = job.mode.value
        by_mode[mode] = by_mode.get(mode, 0) + 1

    # Group by provider
    by_provider = {}
    for job in all_jobs:
        provider = job.provider
        by_provider[provider] = by_provider.get(provider, 0) + 1

    # Calculate average duration
    finished_jobs = [j for j in all_jobs if j.finished_at and j.started_at]
    if finished_jobs:
        durations = []
        for job in finished_jobs:
            try:
                started = datetime.fromisoformat(job.started_at.replace('Z', '+00:00'))
                finished = datetime.fromisoformat(job.finished_at.replace('Z', '+00:00'))
                duration = (finished - started).total_seconds()
                durations.append(duration)
            except:
                pass
        avg_duration = sum(durations) / len(durations) if durations else 0
    else:
        avg_duration = 0

    # Calculate success rate
    completed_jobs = by_status.get('completed', 0)
    success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0

    return JSONResponse(content={
        "total_jobs": total_jobs,
        "total_sessions": total_sessions,
        "total_cost": round(total_cost, 4),
        "total_tokens": total_tokens,
        "by_status": by_status,
        "by_mode": by_mode,
        "by_provider": by_provider,
        "avg_duration": round(avg_duration, 2),
        "success_rate": round(success_rate, 2)
    })


# ============================================================================
# BUDGET API
# ============================================================================


@app.get("/api/budgets")
async def list_budgets(
    period: Optional[str] = None,
    enabled_only: bool = False
):
    """
    List all budgets with optional filters.

    Query Parameters:
        period: Filter by period (daily, weekly, monthly, session, total)
        enabled_only: Only return enabled budgets (default: false)

    Response (JSON):
    {
        "budgets": [
            {
                "id": "<budget_id>",
                "name": "Daily Budget",
                "period": "daily",
                "limit": 10.0,
                "current_spending": 3.5,
                "alert_threshold": 80.0,
                "enabled": true,
                "created_at": "...",
                "period_start": "...",
                "period_end": "...",
                "last_alert_at": null
            }
        ],
        "total": 5
    }
    """
    budget_store = get_budget_store()

    # Parse period filter
    period_filter = None
    if period:
        try:
            period_filter = BudgetPeriod(period.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period: {period}. Use 'daily', 'weekly', 'monthly', 'session', or 'total'"
            )

    budgets = budget_store.list(period=period_filter, enabled_only=enabled_only)

    return JSONResponse(content={
        "budgets": [b.to_dict() for b in budgets],
        "total": len(budgets)
    })


@app.post("/api/budgets")
async def create_budget(request: Request):
    """
    Create a new budget.

    Request Body (JSON):
    {
        "name": "Daily Development Budget",
        "period": "daily",
        "limit": 10.0,
        "alert_threshold": 80.0,  // optional, default 80
        "enabled": true           // optional, default true
    }

    Response (JSON):
    {
        "id": "<budget_id>",
        "name": "...",
        ...
    }
    """
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON request body: {str(e)}"
        )

    # Validate required fields
    name = body.get("name", "").strip()
    period_str = body.get("period", "").lower()
    limit = body.get("limit")

    if not name:
        raise HTTPException(status_code=400, detail="Budget name is required")

    if not period_str:
        raise HTTPException(status_code=400, detail="Budget period is required")

    if limit is None or limit <= 0:
        raise HTTPException(status_code=400, detail="Budget limit must be positive")

    # Validate period
    try:
        period = BudgetPeriod(period_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period_str}. Use 'daily', 'weekly', 'monthly', 'session', or 'total'"
        )

    # Create budget
    import uuid
    budget = Budget(
        id=str(uuid.uuid4()),
        name=name,
        period=period,
        limit=float(limit),
        alert_threshold=float(body.get("alert_threshold", 80.0)),
        enabled=bool(body.get("enabled", True)),
        created_at=datetime.utcnow().isoformat() + "Z"
    )

    # Set period_start for new budget
    budget.period_start = budget.created_at

    # Calculate period_end for time-based budgets
    if period == BudgetPeriod.DAILY:
        from datetime import timedelta
        end = datetime.utcnow() + timedelta(days=1)
        budget.period_end = end.isoformat() + "Z"
    elif period == BudgetPeriod.WEEKLY:
        from datetime import timedelta
        end = datetime.utcnow() + timedelta(weeks=1)
        budget.period_end = end.isoformat() + "Z"
    elif period == BudgetPeriod.MONTHLY:
        from datetime import timedelta
        end = datetime.utcnow() + timedelta(days=30)
        budget.period_end = end.isoformat() + "Z"

    budget_store = get_budget_store()
    budget_store.create(budget)

    return JSONResponse(content=budget.to_dict(), status_code=201)


@app.get("/api/budgets/{budget_id}")
async def get_budget(budget_id: str):
    """
    Get a specific budget by ID.

    Response (JSON):
    {
        "id": "<budget_id>",
        "name": "...",
        "period": "...",
        "limit": 10.0,
        "current_spending": 3.5,
        "usage_percentage": 35.0,
        "remaining": 6.5,
        "is_exceeded": false,
        "should_alert": false,
        ...
    }
    """
    budget_store = get_budget_store()
    budget = budget_store.get(budget_id)

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Add computed fields
    budget_dict = budget.to_dict()
    budget_dict['usage_percentage'] = budget.usage_percentage()
    budget_dict['remaining'] = budget.remaining()
    budget_dict['is_exceeded'] = budget.is_exceeded()
    budget_dict['should_alert'] = budget.should_alert()

    return JSONResponse(content=budget_dict)


@app.put("/api/budgets/{budget_id}")
async def update_budget(budget_id: str, request: Request):
    """
    Update an existing budget.

    Request Body (JSON) - all fields optional:
    {
        "name": "Updated Name",
        "limit": 15.0,
        "alert_threshold": 85.0,
        "enabled": false
    }

    Response (JSON):
    {
        "id": "<budget_id>",
        "name": "...",
        ...
    }
    """
    budget_store = get_budget_store()
    budget = budget_store.get(budget_id)

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON request body: {str(e)}"
        )

    # Update fields if provided
    if "name" in body:
        budget.name = body["name"].strip()
        if not budget.name:
            raise HTTPException(status_code=400, detail="Budget name cannot be empty")

    if "limit" in body:
        limit = float(body["limit"])
        if limit <= 0:
            raise HTTPException(status_code=400, detail="Budget limit must be positive")
        budget.limit = limit

    if "alert_threshold" in body:
        threshold = float(body["alert_threshold"])
        if threshold < 0 or threshold > 100:
            raise HTTPException(status_code=400, detail="Alert threshold must be between 0 and 100")
        budget.alert_threshold = threshold

    if "enabled" in body:
        budget.enabled = bool(body["enabled"])

    budget_store.update(budget)

    return JSONResponse(content=budget.to_dict())


@app.delete("/api/budgets/{budget_id}")
async def delete_budget(budget_id: str):
    """
    Delete a budget.

    Response (JSON):
    {
        "success": true,
        "message": "Budget deleted successfully"
    }
    """
    budget_store = get_budget_store()
    success = budget_store.delete(budget_id)

    if not success:
        raise HTTPException(status_code=404, detail="Budget not found")

    return JSONResponse(content={
        "success": True,
        "message": "Budget deleted successfully"
    })


@app.post("/api/budgets/{budget_id}/reset")
async def reset_budget_period(budget_id: str):
    """
    Reset a budget's period.

    Sets current_spending to 0 and recalculates period_start/period_end.

    Response (JSON):
    {
        "id": "<budget_id>",
        "current_spending": 0.0,
        "period_start": "...",
        "period_end": "...",
        ...
    }
    """
    budget_store = get_budget_store()
    budget = budget_store.reset_period(budget_id)

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    return JSONResponse(content=budget.to_dict())


@app.get("/api/spending/summary")
async def get_spending_summary(
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get spending summary with various breakdowns.

    Query Parameters:
        period: Filter by period (today, week, month, all)
        start_date: ISO timestamp start (optional)
        end_date: ISO timestamp end (optional)

    Response (JSON):
    {
        "total_spending": 123.45,
        "total_jobs": 250,
        "by_provider": {
            "claude": {"cost": 80.0, "jobs": 150},
            "gpt4": {"cost": 43.45, "jobs": 100}
        },
        "by_mode": {
            "auto": {"cost": 90.0, "jobs": 50},
            "chat": {"cost": 33.45, "jobs": 200}
        },
        "by_status": {
            "completed": {"cost": 120.0, "jobs": 230},
            "failed": {"cost": 3.45, "jobs": 20}
        },
        "by_session": [
            {"session_id": "...", "name": "...", "cost": 25.0, "jobs": 10}
        ],
        "timeline": [
            {"date": "2025-01-19", "cost": 15.0, "jobs": 20}
        ]
    }
    """
    from datetime import timedelta
    job_store = get_job_store()
    session_store = get_session_store()

    # Get all jobs (with date filtering if provided)
    all_jobs = job_store.list(limit=10000)

    # Filter by date range
    if period or start_date or end_date:
        now = datetime.utcnow()

        if period == "today":
            start_date = (now.replace(hour=0, minute=0, second=0, microsecond=0)).isoformat() + "Z"
        elif period == "week":
            start_date = (now - timedelta(days=7)).isoformat() + "Z"
        elif period == "month":
            start_date = (now - timedelta(days=30)).isoformat() + "Z"

        if start_date:
            all_jobs = [j for j in all_jobs if j.created_at >= start_date]
        if end_date:
            all_jobs = [j for j in all_jobs if j.created_at <= end_date]

    # Calculate totals
    total_spending = sum(job.estimated_cost for job in all_jobs)
    total_jobs = len(all_jobs)

    # Group by provider
    by_provider = {}
    for job in all_jobs:
        provider = job.provider
        if provider not in by_provider:
            by_provider[provider] = {"cost": 0.0, "jobs": 0}
        by_provider[provider]["cost"] += job.estimated_cost
        by_provider[provider]["jobs"] += 1

    # Group by mode
    by_mode = {}
    for job in all_jobs:
        mode = job.mode.value
        if mode not in by_mode:
            by_mode[mode] = {"cost": 0.0, "jobs": 0}
        by_mode[mode]["cost"] += job.estimated_cost
        by_mode[mode]["jobs"] += 1

    # Group by status
    by_status = {}
    for job in all_jobs:
        status = job.status.value
        if status not in by_status:
            by_status[status] = {"cost": 0.0, "jobs": 0}
        by_status[status]["cost"] += job.estimated_cost
        by_status[status]["jobs"] += 1

    # Group by session
    by_session_dict = {}
    for job in all_jobs:
        if not job.session_id:
            continue
        if job.session_id not in by_session_dict:
            by_session_dict[job.session_id] = {"cost": 0.0, "jobs": 0}
        by_session_dict[job.session_id]["cost"] += job.estimated_cost
        by_session_dict[job.session_id]["jobs"] += 1

    # Add session names
    by_session = []
    for session_id, data in by_session_dict.items():
        session = session_store.get(session_id)
        by_session.append({
            "session_id": session_id,
            "name": session.name if session else "Unknown",
            "cost": round(data["cost"], 4),
            "jobs": data["jobs"]
        })

    # Sort by cost descending
    by_session.sort(key=lambda x: x["cost"], reverse=True)

    # Create daily timeline
    timeline_dict = {}
    for job in all_jobs:
        try:
            date_str = job.created_at[:10]  # YYYY-MM-DD
            if date_str not in timeline_dict:
                timeline_dict[date_str] = {"cost": 0.0, "jobs": 0}
            timeline_dict[date_str]["cost"] += job.estimated_cost
            timeline_dict[date_str]["jobs"] += 1
        except:
            pass

    timeline = [
        {"date": date, "cost": round(data["cost"], 4), "jobs": data["jobs"]}
        for date, data in sorted(timeline_dict.items())
    ]

    # Round costs
    for provider_data in by_provider.values():
        provider_data["cost"] = round(provider_data["cost"], 4)
    for mode_data in by_mode.values():
        mode_data["cost"] = round(mode_data["cost"], 4)
    for status_data in by_status.values():
        status_data["cost"] = round(status_data["cost"], 4)

    return JSONResponse(content={
        "total_spending": round(total_spending, 4),
        "total_jobs": total_jobs,
        "by_provider": by_provider,
        "by_mode": by_mode,
        "by_status": by_status,
        "by_session": by_session,
        "timeline": timeline
    })


# ============================================================================
# LEGACY API (for backward compatibility)
# ============================================================================


@app.post("/api/console")
async def console_command_legacy(request: Request):
    """
    Legacy console command endpoint.

    This endpoint is maintained for backward compatibility.
    New code should use POST /api/runs instead.

    Behaves the same as POST /api/runs.
    """
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON request body: {str(e)}"
        )

    # Map mode
    mode_str = body.get("mode", "chat")
    if mode_str not in ["chat", "auto", "agent"]:
        # Support "task" mode
        if "task" in body.get("input", "").lower():
            mode_str = "task"

    # Submit as new run
    input_text = body.get("input", "").strip()
    agent_name = body.get("agent")
    provider = body.get("provider", "claude")

    if not input_text:
        raise HTTPException(
            status_code=400,
            detail="Input text is required"
        )

    try:
        mode = JobMode(mode_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {mode_str}"
        )

    executor = get_executor()
    job = executor.submit(
        mode=mode,
        input_text=input_text,
        agent_name=agent_name,
        provider=provider,
        target_root=None
    )

    # Return job details (not blocking)
    return JSONResponse(content={
        "status": "submitted",
        "run_id": job.id,
        "message": f"Job submitted successfully. Use GET /api/runs/{job.id} to check status",
        "job": job.to_dict()
    })


# ============================================================================
# MODEL INTELLIGENCE SYSTEM (MIS) API v1
# ============================================================================


@app.get("/api/models/catalog")
async def get_model_catalog(provider: Optional[str] = None):
    """
    Get model catalog.

    Query parameters:
    - provider: Optional provider filter (e.g., "openrouter")

    Response (JSON):
    {
        "models": [
            {
                "id": "anthropic/claude-3.5-sonnet",
                "provider": "openrouter",
                "display_name": "Claude 3.5 Sonnet",
                "family": "anthropic",
                "context_length": 200000,
                "input_price": 3.0,  # USD per 1M tokens
                "output_price": 15.0,  # USD per 1M tokens
                "capabilities": {"vision": false, "tools": true},
                "is_active": true,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T00:00:00Z"
            },
            ...
        ]
    }
    """
    try:
        store = get_catalog_store()
        models = store.list_models(provider=provider, active_only=False)

        return JSONResponse(content={
            "models": [
                {
                    "id": m.id,
                    "provider": m.provider,
                    "display_name": m.display_name,
                    "family": m.family,
                    "context_length": m.context_length,
                    "input_price": m.input_price,
                    "output_price": m.output_price,
                    "capabilities": m.capabilities,
                    "is_active": m.is_active,
                    "created_at": m.created_at,
                    "updated_at": m.updated_at,
                }
                for m in models
            ]
        })
    except Exception as e:
        logger.exception("Error fetching model catalog")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/sync")
async def sync_models():
    """
    Trigger model sync with OpenRouter.

    Returns diff of changes (new, updated, removed models).

    Response (JSON):
    {
        "provider": "openrouter",
        "new": ["model1", "model2", ...],
        "updated": ["model3", ...],
        "removed": ["model4", ...],
        "last_synced": "2024-01-15T12:00:00Z"
    }
    """
    try:
        diff = sync_openrouter_models()
        return JSONResponse(content=diff)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error syncing OpenRouter models")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/updates")
async def get_model_updates():
    """
    Get model update summary and metadata.

    Returns information about last sync and available updates.

    Response (JSON):
    {
        "openrouter": {
            "has_updates": false,
            "new_count": 0,
            "updated_count": 0,
            "removed_count": 0,
            "last_synced": "2024-01-15T12:00:00Z",
            "update_mode": "notify"
        }
    }
    """
    try:
        store = get_catalog_store()
        last_synced = store.get_last_synced("openrouter")
        update_mode = store.get_update_mode()

        # For v1, we don't track new/updated/removed counts persistently
        # They're only returned from sync_openrouter_models()
        # So has_updates is simply based on whether we've ever synced
        has_updates = last_synced is None

        return JSONResponse(content={
            "openrouter": {
                "has_updates": has_updates,
                "new_count": 0,
                "updated_count": 0,
                "removed_count": 0,
                "last_synced": last_synced,
                "update_mode": update_mode,
            }
        })
    except Exception as e:
        logger.exception("Error fetching model updates")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/settings")
async def get_model_settings():
    """
    Get model catalog settings.

    Response (JSON):
    {
        "update_mode": "auto" | "notify" | "off"
    }
    """
    try:
        store = get_catalog_store()
        update_mode = store.get_update_mode()

        return JSONResponse(content={
            "update_mode": update_mode
        })
    except Exception as e:
        logger.exception("Error fetching model settings")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/settings")
async def update_model_settings(request: Request):
    """
    Update model catalog settings.

    Request body (JSON):
    {
        "update_mode": "auto" | "notify" | "off"
    }

    Response (JSON):
    {
        "update_mode": "notify"
    }
    """
    try:
        body = await request.json()
        update_mode = body.get("update_mode")

        if not update_mode or update_mode not in ("auto", "notify", "off"):
            raise HTTPException(
                status_code=400,
                detail="Invalid update_mode. Must be 'auto', 'notify', or 'off'"
            )

        store = get_catalog_store()
        store.set_update_mode(update_mode)

        return JSONResponse(content={
            "update_mode": update_mode
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating model settings")
        raise HTTPException(status_code=500, detail=str(e))


def run_dashboard(host: str = "0.0.0.0", port: Optional[int] = None):
    """Run the dashboard server using uvicorn with graceful shutdown."""
    import uvicorn
    import signal
    import sys

    if port is None:
        port = int(os.getenv("PORT", 3000))

    print(f"[CodeCompanion] Starting Control Tower dashboard...")
    print(f"[CodeCompanion] Dashboard available at: http://{host}:{port}/")
    print(f"[CodeCompanion] Press Ctrl+C to stop")

    # Create uvicorn server instance for graceful shutdown
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
        )
    )

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\n[CodeCompanion] Shutting down dashboard...")

        # Shutdown executor
        executor = get_executor()
        executor.shutdown(wait=False)

        server.should_exit = True
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the server
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n[CodeCompanion] Dashboard stopped")
        sys.exit(0)

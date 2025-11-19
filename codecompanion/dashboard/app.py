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
from .models import Job, JobStatus, JobMode, get_job_store
from .executor import get_executor


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
async def cancel_run(run_id: str):
    """
    Cancel a running job.

    Response (JSON):
    {
        "success": true/false,
        "message": "..."
    }
    """
    executor = get_executor()
    success = executor.cancel(run_id)

    if success:
        return JSONResponse(content={
            "success": True,
            "message": f"Run {run_id} cancelled successfully"
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

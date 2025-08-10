"""
FastAPI Backend for Real-time Multi-Agent Orchestration

Provides WebSocket endpoints for real-time UI updates, REST endpoints for
artifact operations, and event streaming for workflow monitoring.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from core.event_streaming import (
    RealTimeEventOrchestrator, EventBus, StreamEvent, EventType, 
    EventStreamType, OrchestratorConsumer, MetricsConsumer
)
from schemas.artifacts import ArtifactType, ArtifactBase, SpecDoc, DesignDoc, CodePatch
from schemas.ledgers import TaskLedger, TaskStatus, Priority
from schemas.routing import ModelType, TaskType
from core.artifacts import ArtifactHandler, ArtifactValidator
from settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CodeCompanion Orchestra API", version="3.0.0")

# CORS middleware for Streamlit integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://0.0.0.0:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
orchestrator: Optional[RealTimeEventOrchestrator] = None
artifact_handler = ArtifactHandler()
artifact_validator = ArtifactValidator()
active_connections: List[WebSocket] = []
settings = Settings()


class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: str
    payload: Dict[str, Any]
    timestamp: datetime = datetime.now()


class ArtifactCreateRequest(BaseModel):
    """Request to create new artifact"""
    artifact_type: ArtifactType
    content: Dict[str, Any]
    agent_id: str
    correlation_id: str


class WorkflowStartRequest(BaseModel):
    """Request to start new workflow"""
    tasks: List[Dict[str, Any]]
    workflow_name: str = "default"


class SimulateTaskRequest(BaseModel):
    """Request to simulate task for development testing"""
    objective: str


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global orchestrator
    
    try:
        orchestrator = RealTimeEventOrchestrator("api_workflow_001")
        logger.info("FastAPI server started with real-time orchestration")
        
        # Start background event processing
        asyncio.create_task(background_event_processor())
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Continue without Redis if not available
        logger.warning("Starting without Redis - using mock event system")


async def background_event_processor():
    """Background task to process events and broadcast to WebSocket clients"""
    
    while True:
        try:
            if orchestrator and active_connections:
                # Get real-time stats and broadcast to connected clients
                stats = orchestrator.get_real_time_stats()
                
                message = WebSocketMessage(
                    type="stats_update",
                    payload=stats
                )
                
                # Broadcast to all connected clients
                disconnected = []
                for connection in active_connections:
                    try:
                        await connection.send_json(message.dict())
                    except WebSocketDisconnect:
                        disconnected.append(connection)
                
                # Remove disconnected clients
                for conn in disconnected:
                    active_connections.remove(conn)
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
        except Exception as e:
            logger.error(f"Background processor error: {e}")
            await asyncio.sleep(5)


@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming"""
    
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(active_connections)}")
    
    try:
        while True:
            # Listen for client messages
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "subscribe_workflow":
                correlation_id = data.get("correlation_id")
                if orchestrator and correlation_id:
                    # Send workflow events to client
                    events = await orchestrator.get_workflow_events(correlation_id)
                    
                    response = WebSocketMessage(
                        type="workflow_events",
                        payload={
                            "correlation_id": correlation_id,
                            "events": [event.dict() for event in events]
                        }
                    )
                    await websocket.send_json(response.dict())
            
            elif message_type == "ping":
                # Respond to ping
                pong = WebSocketMessage(type="pong", payload={})
                await websocket.send_json(pong.dict())
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(active_connections)}")


@app.post("/api/workflows/start")
async def start_workflow(request: WorkflowStartRequest, background_tasks: BackgroundTasks):
    """Start new workflow with tasks"""
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        # Convert task data to TaskLedger objects
        tasks = []
        for task_data in request.tasks:
            task = TaskLedger(
                task_id=task_data.get("task_id", f"task_{uuid4().hex[:8]}"),
                title=task_data.get("title", "Untitled Task"),
                goal=task_data.get("goal", ""),
                description=task_data.get("description", ""),
                status=TaskStatus.PENDING,
                priority=Priority.MEDIUM,
                acceptance_tests=[],
                success_criteria=["Task completion"],
                expected_artifacts=[],
                estimated_duration=60,
                actual_duration=None,
                started_at=None,
                completed_at=None
            )
            tasks.append(task)
        
        # Start workflow
        correlation_id = await orchestrator.start_workflow(tasks)
        
        # Broadcast workflow started event to WebSocket clients
        message = WebSocketMessage(
            type="workflow_started",
            payload={
                "correlation_id": correlation_id,
                "workflow_name": request.workflow_name,
                "task_count": len(tasks)
            }
        )
        
        for connection in active_connections:
            try:
                await connection.send_json(message.dict())
            except:
                pass  # Handle disconnected clients in background task
        
        return {
            "correlation_id": correlation_id,
            "status": "started",
            "task_count": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/artifacts/create")
async def create_artifact(request: ArtifactCreateRequest):
    """Create new artifact and validate"""
    
    try:
        # Create artifact based on type
        artifact_data = {
            "artifact_id": f"{request.artifact_type.value}_{uuid4().hex[:8]}",
            "artifact_type": request.artifact_type.value,
            "created_by": request.agent_id,
            "confidence": request.content.get("confidence", 0.8),
            **request.content
        }
        
        # Validate artifact
        validation_result = artifact_validator.validate_artifact(artifact_data)
        
        if validation_result.is_valid:
            # Store artifact
            artifact_handler.store_artifact(artifact_data)
            
            # Publish artifact creation event
            if orchestrator:
                event = StreamEvent(
                    correlation_id=request.correlation_id,
                    event_type=EventType.ARTIFACT_CREATED,
                    agent_id=request.agent_id,
                    task_id=f"task_{uuid4().hex[:8]}",
                    artifact_id=artifact_data["artifact_id"],
                    payload=artifact_data,
                    metadata={
                        "validation_quality": validation_result.quality_score,
                        "validation_completeness": validation_result.completeness_score
                    }
                )
                
                await orchestrator.event_bus.publish_event(EventStreamType.ARTIFACTS, event)
            
            # Broadcast to WebSocket clients
            message = WebSocketMessage(
                type="artifact_created",
                payload={
                    "artifact_id": artifact_data["artifact_id"],
                    "artifact_type": request.artifact_type.value,
                    "agent_id": request.agent_id,
                    "validation": validation_result.dict()
                }
            )
            
            for connection in active_connections:
                try:
                    await connection.send_json(message.dict())
                except:
                    pass
            
            return {
                "artifact_id": artifact_data["artifact_id"],
                "validation": validation_result.dict(),
                "status": "created"
            }
        
        else:
            return {
                "status": "validation_failed",
                "errors": validation_result.validation_errors,
                "warnings": validation_result.validation_warnings
            }
    
    except Exception as e:
        logger.error(f"Failed to create artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Get artifact by ID"""
    
    artifact = artifact_handler.retrieve_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    return artifact


@app.get("/api/artifacts")
async def list_artifacts(artifact_type: Optional[ArtifactType] = None):
    """List artifacts, optionally filtered by type"""
    
    if artifact_type:
        artifacts = artifact_handler.list_artifacts_by_type(artifact_type)
    else:
        artifacts = list(artifact_handler.artifact_store.values())
    
    return {
        "artifacts": artifacts,
        "count": len(artifacts)
    }


@app.get("/api/workflows/{correlation_id}/events")
async def get_workflow_events(correlation_id: str):
    """Get all events for a workflow"""
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        events = await orchestrator.get_workflow_events(correlation_id)
        return {
            "correlation_id": correlation_id,
            "events": [event.dict() for event in events],
            "count": len(events)
        }
    
    except Exception as e:
        logger.error(f"Failed to get workflow events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/real-time")
async def get_real_time_stats():
    """Get real-time orchestration statistics"""
    
    if not orchestrator:
        return {"error": "Orchestrator not available", "mock_mode": True}
    
    stats = orchestrator.get_real_time_stats()
    
    # Add artifact handler stats
    stats["artifact_stats"] = artifact_handler.get_artifact_stats()
    
    return stats


@app.post("/api/agents/register")
async def register_agent(agent_data: Dict[str, Any]):
    """Register new agent with the system"""
    
    agent_id = agent_data.get("agent_id", f"agent_{uuid4().hex[:8]}")
    
    # Publish agent registration event
    if orchestrator:
        event = StreamEvent(
            correlation_id="system",
            event_type=EventType.AGENT_REGISTERED,
            agent_id=agent_id,
            task_id=f"reg_{uuid4().hex[:8]}",
            artifact_id=f"agent_reg_{uuid4().hex[:8]}",
            payload=agent_data,
            metadata={"registration_time": datetime.now().isoformat()}
        )
        
        await orchestrator.event_bus.publish_event(EventStreamType.AGENT_STATUS, event)
    
    return {
        "agent_id": agent_id,
        "status": "registered",
        "capabilities": agent_data.get("capabilities", [])
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with event bus and database status"""
    
    # Check Redis connection
    redis_ok = False
    if orchestrator and hasattr(orchestrator, 'event_bus'):
        try:
            # Try to access the event bus redis connection
            redis_ok = (
                settings.EVENT_BUS == "redis" and 
                hasattr(orchestrator.event_bus, 'redis') and 
                orchestrator.event_bus.redis is not None
            )
        except:
            redis_ok = False
    
    # Check database connection
    db_ok = True  # Assume SQLite is always OK since it's file-based
    try:
        import sqlite3
        # Quick test of database connection
        with sqlite3.connect(settings.get_database_url().replace("sqlite:///", "")):
            pass
    except:
        db_ok = False
    
    return {
        "ok": True,
        "event_bus": settings.EVENT_BUS,
        "redis_ok": redis_ok,
        "db_ok": db_ok
    }


@app.post("/simulate_task")
async def simulate_task(request: SimulateTaskRequest):
    """Simulate task creation for development testing only"""
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        # Generate random task ID
        task_id = f"sim_task_{uuid4().hex[:8]}"
        
        # Create a simulated task event
        event = StreamEvent(
            correlation_id=f"sim_workflow_{uuid4().hex[:8]}",
            event_type=EventType.TASK_CREATED,
            task_id=task_id,
            payload={
                "task_id": task_id,
                "objective": request.objective,
                "status": "created",
                "priority": "medium",
                "created_at": datetime.now().isoformat()
            },
            metadata={
                "source": "simulate_task_endpoint",
                "environment": "development"
            }
        )
        
        # Publish to TASKS stream
        await orchestrator.event_bus.publish_event(EventStreamType.TASKS, event)
        
        # Also broadcast to WebSocket clients
        ws_message = WebSocketMessage(
            type="task_simulated",
            payload={
                "task_id": task_id,
                "objective": request.objective,
                "correlation_id": event.correlation_id
            }
        )
        
        for connection in active_connections:
            try:
                await connection.send_json(ws_message.dict())
            except:
                pass  # Handle disconnected clients gracefully
        
        logger.info(f"Simulated task created: {task_id} - {request.objective}")
        
        return {"task_id": task_id}
        
    except Exception as e:
        logger.error(f"Failed to simulate task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
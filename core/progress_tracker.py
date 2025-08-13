"""
Live Progress Tracking System
Real-time tracking of agent progress, artifact creation, and collaboration metrics
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
from uuid import uuid4
from enum import Enum
from dataclasses import dataclass, field

from core.event_streaming import StreamEvent, EventType, StreamConsumer

logger = logging.getLogger(__name__)


class ProgressEventType(str, Enum):
    """Types of progress events"""

    AGENT_STARTED = "agent_started"
    AGENT_PROGRESS_UPDATE = "agent_progress_update"
    AGENT_COMPLETED = "agent_completed"
    ARTIFACT_CREATED = "artifact_created"
    MILESTONE_REACHED = "milestone_reached"
    COLLABORATION_EVENT = "collaboration_event"


@dataclass
class AgentProgress:
    """Real-time agent progress tracking"""

    agent_id: str
    agent_type: str
    task_id: str
    correlation_id: str
    status: str = "pending"
    progress_percentage: float = 0.0
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    current_activity: str = ""
    subtasks_completed: int = 0
    subtasks_total: int = 0
    tokens_used: int = 0
    api_calls_made: int = 0
    error_count: int = 0
    quality_score: Optional[float] = None


@dataclass
class ArtifactCreationEvent:
    """Tracks artifact creation events"""

    artifact_id: str
    artifact_type: str
    created_by: str
    correlation_id: str
    creation_time: datetime
    size_estimate: int = 0
    quality_score: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass
class CollaborationMetrics:
    """Metrics for agent collaboration"""

    workflow_id: str
    active_agents: Set[str] = field(default_factory=set)
    completed_agents: Set[str] = field(default_factory=set)
    total_artifacts: int = 0
    handoffs_completed: int = 0
    parallel_work_sessions: int = 0
    avg_response_time: float = 0.0
    collaboration_efficiency: float = 0.0


class LiveProgressTracker(StreamConsumer):
    """
    Live progress tracking system that monitors agent activities,
    artifact creation, and collaboration metrics in real-time
    """

    def __init__(self, event_bus=None):
        from bus import bus

        super().__init__(bus, "progress_tracker")

        # Progress tracking storage
        self.agent_progress: Dict[str, AgentProgress] = {}
        self.artifact_events: List[ArtifactCreationEvent] = []
        self.collaboration_metrics: Dict[str, CollaborationMetrics] = {}

        # Live updates
        self.progress_subscribers: Set[str] = set()
        self.update_callbacks: List[callable] = []

        # Analytics
        self.session_start_time = datetime.now(timezone.utc)
        self.total_events_processed = 0

        logger.info("Live progress tracker initialized")

    async def process_event(self, event: StreamEvent):
        """Process events for progress tracking"""

        self.total_events_processed += 1

        try:
            if event.event_type == EventType.AGENT_STARTED:
                await self._handle_agent_started(event)

            elif event.event_type == EventType.AGENT_COMPLETED:
                await self._handle_agent_completed(event)

            elif event.event_type == EventType.ARTIFACT_CREATED:
                await self._handle_artifact_created(event)

            elif event.event_type == EventType.PERFORMANCE_METRIC:
                await self._handle_performance_metric(event)

            elif event.event_type == EventType.TASK_STARTED:
                await self._handle_task_started(event)

            elif event.event_type == EventType.TASK_COMPLETED:
                await self._handle_task_completed(event)

            # Publish live updates to subscribers
            await self._publish_live_update(event)

        except Exception as e:
            logger.error(f"Error processing progress event {event.event_id}: {e}")

    async def _handle_agent_started(self, event: StreamEvent):
        """Handle agent started events"""

        payload = event.payload
        agent_id = payload.get("agent_id", event.agent_id)

        progress = AgentProgress(
            agent_id=agent_id,
            agent_type=payload.get("agent_type", "unknown"),
            task_id=event.task_id or f"task_{agent_id}",
            correlation_id=event.correlation_id,
            status="running",
            start_time=event.timestamp,
            last_update=event.timestamp,
            current_activity="Initializing agent execution",
        )

        # Estimate completion time based on agent type
        estimated_duration = self._estimate_agent_duration(progress.agent_type)
        progress.estimated_completion = progress.start_time + timedelta(
            seconds=estimated_duration
        )

        self.agent_progress[agent_id] = progress

        # Update collaboration metrics
        await self._update_collaboration_metrics(
            event.correlation_id, "agent_started", agent_id
        )

        logger.info(f"Started tracking progress for agent {agent_id}")

    async def _handle_agent_completed(self, event: StreamEvent):
        """Handle agent completion events"""

        payload = event.payload
        agent_id = payload.get("agent_id", event.agent_id)

        if agent_id in self.agent_progress:
            progress = self.agent_progress[agent_id]
            progress.status = "completed"
            progress.progress_percentage = 100.0
            progress.last_update = event.timestamp
            progress.current_activity = "Agent execution completed"

            # Calculate actual execution time
            if progress.start_time:
                execution_time = (event.timestamp - progress.start_time).total_seconds()
                logger.info(
                    f"Agent {agent_id} completed in {execution_time:.1f} seconds"
                )

            # Update collaboration metrics
            await self._update_collaboration_metrics(
                event.correlation_id, "agent_completed", agent_id
            )

    async def _handle_artifact_created(self, event: StreamEvent):
        """Handle artifact creation events"""

        payload = event.payload

        artifact_event = ArtifactCreationEvent(
            artifact_id=event.artifact_id or f"artifact_{uuid4().hex[:8]}",
            artifact_type=payload.get("artifact_type", "unknown"),
            created_by=event.agent_id or "unknown",
            correlation_id=event.correlation_id,
            creation_time=event.timestamp,
            size_estimate=payload.get("size", 0),
            quality_score=payload.get("quality_score"),
            dependencies=payload.get("dependencies", []),
        )

        self.artifact_events.append(artifact_event)

        # Update collaboration metrics
        await self._update_collaboration_metrics(
            event.correlation_id, "artifact_created"
        )

        # Update agent progress if applicable
        if event.agent_id in self.agent_progress:
            progress = self.agent_progress[event.agent_id]
            progress.current_activity = f"Created {artifact_event.artifact_type}"
            progress.last_update = event.timestamp
            progress.subtasks_completed += 1

        logger.info(
            f"Artifact {artifact_event.artifact_id} created by {artifact_event.created_by}"
        )

    async def _handle_performance_metric(self, event: StreamEvent):
        """Handle performance metric events"""

        payload = event.payload
        agent_id = payload.get("agent_id", event.agent_id)

        if agent_id in self.agent_progress:
            progress = self.agent_progress[agent_id]

            # Update progress if provided
            if "progress" in payload:
                progress.progress_percentage = min(payload["progress"] * 100, 100.0)
                progress.last_update = event.timestamp

            # Update activity if provided
            if "activity" in payload:
                progress.current_activity = payload["activity"]

            # Update metrics
            if "tokens_used" in payload:
                progress.tokens_used += payload["tokens_used"]

            if "api_calls" in payload:
                progress.api_calls_made += payload["api_calls"]

            if "quality_score" in payload:
                progress.quality_score = payload["quality_score"]

    async def _handle_task_started(self, event: StreamEvent):
        """Handle task started events"""

        # Initialize collaboration metrics for new workflows
        correlation_id = event.correlation_id

        if correlation_id not in self.collaboration_metrics:
            self.collaboration_metrics[correlation_id] = CollaborationMetrics(
                workflow_id=correlation_id
            )

    async def _handle_task_completed(self, event: StreamEvent):
        """Handle task completion events"""

        correlation_id = event.correlation_id

        if correlation_id in self.collaboration_metrics:
            metrics = self.collaboration_metrics[correlation_id]

            # Calculate final collaboration efficiency
            total_time = (event.timestamp - self.session_start_time).total_seconds()
            if total_time > 0:
                metrics.collaboration_efficiency = (
                    metrics.handoffs_completed + metrics.parallel_work_sessions
                ) / total_time

    async def _update_collaboration_metrics(
        self, correlation_id: str, event_type: str, agent_id: Optional[str] = None
    ):
        """Update collaboration metrics"""

        if correlation_id not in self.collaboration_metrics:
            self.collaboration_metrics[correlation_id] = CollaborationMetrics(
                workflow_id=correlation_id
            )

        metrics = self.collaboration_metrics[correlation_id]

        if event_type == "agent_started" and agent_id:
            metrics.active_agents.add(agent_id)

        elif event_type == "agent_completed" and agent_id:
            metrics.active_agents.discard(agent_id)
            metrics.completed_agents.add(agent_id)

            # Count as handoff if multiple agents involved
            if len(metrics.completed_agents) > 1:
                metrics.handoffs_completed += 1

        elif event_type == "artifact_created":
            metrics.total_artifacts += 1

        # Calculate parallel work sessions
        if len(metrics.active_agents) > 1:
            metrics.parallel_work_sessions += 1

    def _estimate_agent_duration(self, agent_type: str) -> int:
        """Estimate agent execution duration in seconds"""

        duration_estimates = {
            "PROJECT_MANAGER": 300,  # 5 minutes
            "CODE_GENERATOR": 600,  # 10 minutes
            "UI_DESIGNER": 480,  # 8 minutes
            "TEST_WRITER": 360,  # 6 minutes
            "DEBUGGER": 240,  # 4 minutes
        }

        return duration_estimates.get(agent_type.upper(), 300)

    async def _publish_live_update(self, original_event: StreamEvent):
        """Publish live updates to subscribed systems"""

        # Create progress update event
        progress_update = StreamEvent(
            correlation_id=original_event.correlation_id,
            event_type=EventType.PERFORMANCE_METRIC,
            payload={
                "progress_summary": self.get_live_progress_summary(),
                "recent_events": [
                    {
                        "event_type": original_event.event_type.value,
                        "timestamp": original_event.timestamp.isoformat(),
                        "agent_id": original_event.agent_id,
                        "artifact_id": original_event.artifact_id,
                    }
                ],
            },
            metadata={"source": "progress_tracker", "live_update": True},
        )

        # Publish to metrics stream
        from bus import Event

        event = Event(
            topic="metrics",
            payload={
                "event_type": "progress_update",
                "correlation_id": original_event.correlation_id,
                "progress_data": progress_update.payload,
            },
        )
        await self.event_bus.publish(event)

    def get_live_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary"""

        active_agents = [
            p for p in self.agent_progress.values() if p.status == "running"
        ]
        completed_agents = [
            p for p in self.agent_progress.values() if p.status == "completed"
        ]

        # Calculate overall progress
        if self.agent_progress:
            overall_progress = sum(
                p.progress_percentage for p in self.agent_progress.values()
            ) / len(self.agent_progress)
        else:
            overall_progress = 0.0

        # Recent artifacts (last 10)
        recent_artifacts = sorted(
            self.artifact_events, key=lambda x: x.creation_time, reverse=True
        )[:10]

        return {
            "overall_progress": overall_progress,
            "active_agents": len(active_agents),
            "completed_agents": len(completed_agents),
            "total_artifacts": len(self.artifact_events),
            "recent_artifacts": [
                {
                    "id": a.artifact_id,
                    "type": a.artifact_type,
                    "created_by": a.created_by,
                    "timestamp": a.creation_time.isoformat(),
                }
                for a in recent_artifacts
            ],
            "agent_details": [
                {
                    "agent_id": p.agent_id,
                    "agent_type": p.agent_type,
                    "status": p.status,
                    "progress": p.progress_percentage,
                    "current_activity": p.current_activity,
                    "estimated_completion": p.estimated_completion.isoformat()
                    if p.estimated_completion
                    else None,
                }
                for p in self.agent_progress.values()
            ],
        }

    def get_agent_progress(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress for specific agent"""

        if agent_id not in self.agent_progress:
            return None

        progress = self.agent_progress[agent_id]

        return {
            "agent_id": progress.agent_id,
            "agent_type": progress.agent_type,
            "task_id": progress.task_id,
            "correlation_id": progress.correlation_id,
            "status": progress.status,
            "progress_percentage": progress.progress_percentage,
            "start_time": progress.start_time.isoformat()
            if progress.start_time
            else None,
            "last_update": progress.last_update.isoformat()
            if progress.last_update
            else None,
            "estimated_completion": progress.estimated_completion.isoformat()
            if progress.estimated_completion
            else None,
            "current_activity": progress.current_activity,
            "subtasks_completed": progress.subtasks_completed,
            "subtasks_total": progress.subtasks_total,
            "tokens_used": progress.tokens_used,
            "api_calls_made": progress.api_calls_made,
            "error_count": progress.error_count,
            "quality_score": progress.quality_score,
        }

    def get_collaboration_metrics(
        self, correlation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get collaboration metrics for workflow"""

        if correlation_id not in self.collaboration_metrics:
            return None

        metrics = self.collaboration_metrics[correlation_id]

        return {
            "workflow_id": metrics.workflow_id,
            "active_agents": list(metrics.active_agents),
            "completed_agents": list(metrics.completed_agents),
            "total_artifacts": metrics.total_artifacts,
            "handoffs_completed": metrics.handoffs_completed,
            "parallel_work_sessions": metrics.parallel_work_sessions,
            "avg_response_time": metrics.avg_response_time,
            "collaboration_efficiency": metrics.collaboration_efficiency,
        }

    def get_artifact_timeline(
        self, correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get timeline of artifact creation"""

        artifacts = self.artifact_events

        if correlation_id:
            artifacts = [a for a in artifacts if a.correlation_id == correlation_id]

        return [
            {
                "artifact_id": a.artifact_id,
                "artifact_type": a.artifact_type,
                "created_by": a.created_by,
                "correlation_id": a.correlation_id,
                "creation_time": a.creation_time.isoformat(),
                "size_estimate": a.size_estimate,
                "quality_score": a.quality_score,
                "dependencies": a.dependencies,
            }
            for a in sorted(artifacts, key=lambda x: x.creation_time, reverse=True)
        ]

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""

        uptime = (datetime.now(timezone.utc) - self.session_start_time).total_seconds()

        # Calculate agent health
        agent_health = {
            "total_agents": len(self.agent_progress),
            "active_agents": len(
                [p for p in self.agent_progress.values() if p.status == "running"]
            ),
            "completed_agents": len(
                [p for p in self.agent_progress.values() if p.status == "completed"]
            ),
            "failed_agents": len(
                [p for p in self.agent_progress.values() if p.status == "failed"]
            ),
        }

        success_rate = (
            agent_health["completed_agents"] / agent_health["total_agents"]
            if agent_health["total_agents"] > 0
            else 0
        )

        return {
            "uptime_seconds": uptime,
            "events_processed": self.total_events_processed,
            "processing_rate": self.total_events_processed / uptime
            if uptime > 0
            else 0,
            "agent_health": agent_health,
            "success_rate": success_rate,
            "total_artifacts_created": len(self.artifact_events),
            "active_workflows": len(self.collaboration_metrics),
            "memory_usage": {
                "agent_progress_entries": len(self.agent_progress),
                "artifact_events": len(self.artifact_events),
                "collaboration_metrics": len(self.collaboration_metrics),
            },
        }

    async def subscribe_to_updates(self, subscriber_id: str, callback: callable):
        """Subscribe to live progress updates"""

        self.progress_subscribers.add(subscriber_id)
        self.update_callbacks.append(callback)

        logger.info(f"Subscriber {subscriber_id} added to progress updates")

    def unsubscribe_from_updates(self, subscriber_id: str):
        """Unsubscribe from live progress updates"""

        self.progress_subscribers.discard(subscriber_id)
        logger.info(f"Subscriber {subscriber_id} removed from progress updates")

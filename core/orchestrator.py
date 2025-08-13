"""
Event-sourced orchestrator for multi-agent workflows.

Manages workflow state through immutable events, providing full auditability,
replay capability, and consistent state management across distributed agents.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from uuid import uuid4
from pydantic import BaseModel, Field
import logging
from collections import defaultdict

from schemas.ledgers import TaskLedger, ProgressLedger, TaskStatus
from schemas.artifacts import ArtifactBase
from schemas.routing import RoutingDecision


logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of events in the orchestration system"""

    WORKFLOW_STARTED = "workflow_started"
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    ARTIFACT_PRODUCED = "artifact_produced"
    AGENT_COMMUNICATION = "agent_communication"
    DEPENDENCY_RESOLVED = "dependency_resolved"
    BLOCKER_IDENTIFIED = "blocker_identified"
    BLOCKER_RESOLVED = "blocker_resolved"
    WORKFLOW_COMPLETED = "workflow_completed"
    ERROR_OCCURRED = "error_occurred"


class WorkflowEvent(BaseModel):
    """Immutable event in the workflow event stream"""

    event_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique event ID"
    )
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Event timestamp"
    )

    # Event context
    workflow_id: str = Field(..., description="Workflow this event belongs to")
    task_id: Optional[str] = Field(None, description="Task ID if task-specific")
    agent_id: Optional[str] = Field(None, description="Agent ID if agent-specific")

    # Event data
    data: Dict[str, Any] = Field(
        default_factory=dict, description="Event-specific data"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    # Event relationships
    correlation_id: Optional[str] = Field(None, description="ID linking related events")
    caused_by_event: Optional[str] = Field(
        None, description="ID of event that caused this one"
    )

    class Config:
        frozen = True  # Immutable events


class OrchestratorState(BaseModel):
    """Current state of orchestrator rebuilt from event stream"""

    workflow_id: str = Field(..., description="Workflow identifier")

    # Workflow status
    started_at: Optional[datetime] = Field(None, description="Workflow start time")
    completed_at: Optional[datetime] = Field(
        None, description="Workflow completion time"
    )
    status: str = Field(default="initialized", description="Current workflow status")

    # Task management
    tasks: Dict[str, TaskLedger] = Field(
        default_factory=dict, description="All tasks in workflow"
    )
    task_dependencies: Dict[str, List[str]] = Field(
        default_factory=dict, description="Task dependency graph"
    )
    completed_tasks: List[str] = Field(
        default_factory=list, description="Completed task IDs"
    )
    active_tasks: List[str] = Field(
        default_factory=list, description="Currently active task IDs"
    )
    blocked_tasks: List[str] = Field(
        default_factory=list, description="Blocked task IDs"
    )

    # Agent assignments
    agent_assignments: Dict[str, List[str]] = Field(
        default_factory=dict, description="Agent to task mapping"
    )
    agent_status: Dict[str, str] = Field(
        default_factory=dict, description="Current agent status"
    )

    # Artifacts
    produced_artifacts: Dict[str, ArtifactBase] = Field(
        default_factory=dict, description="All produced artifacts"
    )
    artifact_dependencies: Dict[str, List[str]] = Field(
        default_factory=dict, description="Artifact dependency graph"
    )

    # Communication log
    communications: List[Dict[str, Any]] = Field(
        default_factory=list, description="Agent communications"
    )

    # Progress tracking
    progress_ledger: Optional[ProgressLedger] = Field(
        None, description="Overall progress tracking"
    )

    # Error tracking
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Workflow errors"
    )
    warnings: List[Dict[str, Any]] = Field(
        default_factory=list, description="Workflow warnings"
    )


class EventSourcedOrchestrator:
    """
    Event-sourced orchestrator that manages workflow state through immutable events.

    All state changes are recorded as events, allowing for:
    - Full audit trail of decisions and changes
    - Replay capability for debugging and recovery
    - Consistent state across distributed components
    - Time-travel debugging and analysis
    """

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.events: List[WorkflowEvent] = []
        self.state = OrchestratorState(workflow_id=workflow_id)
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.snapshots: Dict[
            int, OrchestratorState
        ] = {}  # Event count -> state snapshot
        self.snapshot_frequency = 50  # Create snapshot every N events

        # Register default event handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default event handlers for state updates"""

        self.event_handlers[EventType.WORKFLOW_STARTED].append(
            self._handle_workflow_started
        )
        self.event_handlers[EventType.TASK_CREATED].append(self._handle_task_created)
        self.event_handlers[EventType.TASK_ASSIGNED].append(self._handle_task_assigned)
        self.event_handlers[EventType.TASK_STARTED].append(self._handle_task_started)
        self.event_handlers[EventType.TASK_COMPLETED].append(
            self._handle_task_completed
        )
        self.event_handlers[EventType.TASK_FAILED].append(self._handle_task_failed)
        self.event_handlers[EventType.ARTIFACT_PRODUCED].append(
            self._handle_artifact_produced
        )
        self.event_handlers[EventType.AGENT_COMMUNICATION].append(
            self._handle_agent_communication
        )
        self.event_handlers[EventType.ERROR_OCCURRED].append(
            self._handle_error_occurred
        )

    def emit_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> WorkflowEvent:
        """Emit a new event and update state"""

        event = WorkflowEvent(
            event_type=event_type,
            workflow_id=self.workflow_id,
            task_id=task_id,
            agent_id=agent_id,
            data=data,
            correlation_id=correlation_id,
        )

        self.events.append(event)

        # Process event through handlers
        for handler in self.event_handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error processing event {event.event_id}: {e}")
                self._emit_error_event(f"Event handler error: {e}", event.event_id)

        # Create snapshot if needed
        if len(self.events) % self.snapshot_frequency == 0:
            self._create_snapshot()

        logger.info(f"Event emitted: {event_type} for workflow {self.workflow_id}")
        return event

    def _emit_error_event(
        self, error_message: str, related_event: Optional[str] = None
    ):
        """Emit error event for internal errors"""
        error_data = {
            "error_message": error_message,
            "related_event": related_event,
            "timestamp": datetime.now().isoformat(),
        }

        error_event = WorkflowEvent(
            event_type=EventType.ERROR_OCCURRED,
            workflow_id=self.workflow_id,
            data=error_data,
        )
        self.events.append(error_event)

    def _create_snapshot(self):
        """Create state snapshot for faster replay"""
        self.snapshots[len(self.events)] = self.state.copy(deep=True)
        logger.debug(f"Created state snapshot at event {len(self.events)}")

    def replay_events(self, up_to_event: Optional[int] = None) -> OrchestratorState:
        """Replay events to rebuild state"""

        # Find latest snapshot before target
        target = up_to_event or len(self.events)
        snapshot_point = 0
        for event_count in sorted(self.snapshots.keys(), reverse=True):
            if event_count <= target:
                self.state = self.snapshots[event_count].copy(deep=True)
                snapshot_point = event_count
                break

        # Replay events from snapshot point
        for i in range(snapshot_point, target):
            if i < len(self.events):
                event = self.events[i]
                for handler in self.event_handlers.get(event.event_type, []):
                    handler(event)

        return self.state

    def start_workflow(self, initial_tasks: List[TaskLedger]) -> str:
        """Start workflow with initial tasks"""

        correlation_id = str(uuid4())

        # Emit workflow started event
        self.emit_event(
            EventType.WORKFLOW_STARTED,
            data={
                "initial_task_count": len(initial_tasks),
                "task_ids": [task.task_id for task in initial_tasks],
            },
            correlation_id=correlation_id,
        )

        # Create initial tasks
        for task in initial_tasks:
            self.create_task(task, correlation_id)

        return correlation_id

    def create_task(
        self, task: TaskLedger, correlation_id: Optional[str] = None
    ) -> str:
        """Create a new task in the workflow"""

        self.emit_event(
            EventType.TASK_CREATED,
            data=task.dict(),
            task_id=task.task_id,
            correlation_id=correlation_id,
        )

        return task.task_id

    def assign_task(
        self,
        task_id: str,
        agent_id: str,
        routing_decision: RoutingDecision,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Assign task to specific agent"""

        if task_id not in self.state.tasks:
            logger.error(f"Task {task_id} not found")
            return False

        self.emit_event(
            EventType.TASK_ASSIGNED,
            data={
                "agent_id": agent_id,
                "routing_decision": routing_decision.dict(),
                "assignment_timestamp": datetime.now().isoformat(),
            },
            task_id=task_id,
            agent_id=agent_id,
            correlation_id=correlation_id,
        )

        return True

    def start_task(
        self, task_id: str, agent_id: str, correlation_id: Optional[str] = None
    ) -> bool:
        """Mark task as started"""

        if task_id not in self.state.tasks:
            logger.error(f"Task {task_id} not found")
            return False

        self.emit_event(
            EventType.TASK_STARTED,
            data={"started_timestamp": datetime.now().isoformat()},
            task_id=task_id,
            agent_id=agent_id,
            correlation_id=correlation_id,
        )

        return True

    def complete_task(
        self,
        task_id: str,
        agent_id: str,
        artifacts: List[ArtifactBase],
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Mark task as completed with produced artifacts"""

        if task_id not in self.state.tasks:
            logger.error(f"Task {task_id} not found")
            return False

        # First emit task completion
        self.emit_event(
            EventType.TASK_COMPLETED,
            data={
                "completed_timestamp": datetime.now().isoformat(),
                "artifact_count": len(artifacts),
                "artifact_ids": [artifact.artifact_id for artifact in artifacts],
            },
            task_id=task_id,
            agent_id=agent_id,
            correlation_id=correlation_id,
        )

        # Then emit artifact production events
        for artifact in artifacts:
            self.emit_event(
                EventType.ARTIFACT_PRODUCED,
                data=artifact.dict(),
                task_id=task_id,
                agent_id=agent_id,
                correlation_id=correlation_id,
            )

        return True

    def fail_task(
        self,
        task_id: str,
        agent_id: str,
        error_message: str,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Mark task as failed"""

        if task_id not in self.state.tasks:
            logger.error(f"Task {task_id} not found")
            return False

        self.emit_event(
            EventType.TASK_FAILED,
            data={
                "error_message": error_message,
                "failed_timestamp": datetime.now().isoformat(),
            },
            task_id=task_id,
            agent_id=agent_id,
            correlation_id=correlation_id,
        )

        return True

    def log_communication(
        self,
        from_agent: str,
        to_agent: Optional[str],
        message: str,
        communication_type: str = "handoff",
        correlation_id: Optional[str] = None,
    ):
        """Log communication between agents"""

        self.emit_event(
            EventType.AGENT_COMMUNICATION,
            data={
                "from_agent": from_agent,
                "to_agent": to_agent,
                "message": message,
                "communication_type": communication_type,
                "timestamp": datetime.now().isoformat(),
            },
            agent_id=from_agent,
            correlation_id=correlation_id,
        )

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""

        total_tasks = len(self.state.tasks)
        completed_tasks = len(self.state.completed_tasks)
        active_tasks = len(self.state.active_tasks)
        blocked_tasks = len(self.state.blocked_tasks)

        progress_percentage = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        return {
            "workflow_id": self.workflow_id,
            "status": self.state.status,
            "started_at": self.state.started_at,
            "completed_at": self.state.completed_at,
            "progress_percentage": progress_percentage,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "active_tasks": active_tasks,
            "blocked_tasks": blocked_tasks,
            "total_events": len(self.events),
            "artifacts_produced": len(self.state.produced_artifacts),
            "active_agents": list(self.state.agent_status.keys()),
        }

    # Event handlers
    def _handle_workflow_started(self, event: WorkflowEvent):
        """Handle workflow started event"""
        self.state.started_at = event.timestamp
        self.state.status = "running"

    def _handle_task_created(self, event: WorkflowEvent):
        """Handle task created event"""
        task_data = event.data
        task = TaskLedger(**task_data)
        self.state.tasks[task.task_id] = task

        # Add to dependency graph
        if task.dependencies:
            self.state.task_dependencies[task.task_id] = task.dependencies

    def _handle_task_assigned(self, event: WorkflowEvent):
        """Handle task assigned event"""
        task_id = event.task_id
        agent_id = event.data["agent_id"]

        if task_id in self.state.tasks:
            # Add to agent assignments
            if agent_id not in self.state.agent_assignments:
                self.state.agent_assignments[agent_id] = []
            self.state.agent_assignments[agent_id].append(task_id)

            # Update agent status
            self.state.agent_status[agent_id] = "assigned"

    def _handle_task_started(self, event: WorkflowEvent):
        """Handle task started event"""
        task_id = event.task_id
        agent_id = event.agent_id

        if task_id in self.state.tasks:
            self.state.tasks[task_id].status = TaskStatus.IN_PROGRESS
            self.state.tasks[task_id].started_at = event.timestamp

            if task_id not in self.state.active_tasks:
                self.state.active_tasks.append(task_id)

            if agent_id:
                self.state.agent_status[agent_id] = "working"

    def _handle_task_completed(self, event: WorkflowEvent):
        """Handle task completed event"""
        task_id = event.task_id
        agent_id = event.agent_id

        if task_id in self.state.tasks:
            self.state.tasks[task_id].status = TaskStatus.COMPLETED
            self.state.tasks[task_id].completed_at = event.timestamp

            # Move from active to completed
            if task_id in self.state.active_tasks:
                self.state.active_tasks.remove(task_id)
            if task_id not in self.state.completed_tasks:
                self.state.completed_tasks.append(task_id)

            if agent_id:
                self.state.agent_status[agent_id] = "idle"

    def _handle_task_failed(self, event: WorkflowEvent):
        """Handle task failed event"""
        task_id = event.task_id
        agent_id = event.agent_id

        if task_id in self.state.tasks:
            self.state.tasks[task_id].status = TaskStatus.FAILED

            # Remove from active tasks
            if task_id in self.state.active_tasks:
                self.state.active_tasks.remove(task_id)

            if agent_id:
                self.state.agent_status[agent_id] = "error"

    def _handle_artifact_produced(self, event: WorkflowEvent):
        """Handle artifact produced event"""
        artifact_data = event.data
        artifact_id = artifact_data["artifact_id"]

        # Store artifact (would need factory to reconstruct proper type)
        self.state.produced_artifacts[artifact_id] = artifact_data

        # Update task with produced artifact
        if event.task_id and event.task_id in self.state.tasks:
            if artifact_id not in self.state.tasks[event.task_id].produced_artifacts:
                self.state.tasks[event.task_id].produced_artifacts.append(artifact_id)

    def _handle_agent_communication(self, event: WorkflowEvent):
        """Handle agent communication event"""
        communication = {
            "timestamp": event.timestamp,
            "from_agent": event.data["from_agent"],
            "to_agent": event.data.get("to_agent"),
            "message": event.data["message"],
            "communication_type": event.data.get("communication_type", "general"),
        }
        self.state.communications.append(communication)

    def _handle_error_occurred(self, event: WorkflowEvent):
        """Handle error occurred event"""
        error = {
            "timestamp": event.timestamp,
            "error_message": event.data["error_message"],
            "related_event": event.data.get("related_event"),
            "task_id": event.task_id,
            "agent_id": event.agent_id,
        }
        self.state.errors.append(error)

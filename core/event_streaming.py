"""
Real-time Event-Sourced Orchestration with Redis Streams

Provides production-grade event streaming for multi-agent coordination:
- Event bus with Redis Streams
- Real-time event processing
- Event replay capability
- Stream consumers for different responsibilities
"""

import asyncio
import json
import logging
import redis
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from uuid import uuid4
from pydantic import BaseModel, Field
from enum import Enum

from schemas.artifacts import ArtifactType, ArtifactBase
from schemas.ledgers import TaskLedger

logger = logging.getLogger(__name__)


class EventStreamType(str, Enum):
    """Event stream types for different categories"""
    TASKS = "tasks"
    ARTIFACTS = "artifacts" 
    REVIEWS = "reviews"
    METRICS = "metrics"
    AGENT_STATUS = "agent_status"


class EventType(str, Enum):
    """Types of events in the system"""
    # Task events
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # Artifact events
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_VALIDATED = "artifact_validated"
    ARTIFACT_APPROVED = "artifact_approved"
    ARTIFACT_REJECTED = "artifact_rejected"
    
    # Review events
    REVIEW_REQUESTED = "review_requested"
    REVIEW_SUBMITTED = "review_submitted"
    REVIEW_CONFLICT = "review_conflict"
    
    # Agent events
    AGENT_REGISTERED = "agent_registered"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    
    # Metrics events
    PERFORMANCE_METRIC = "performance_metric"
    ROUTING_DECISION = "routing_decision"


class StreamEvent(BaseModel):
    """Standardized event structure for Redis Streams"""
    
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:8]}")
    correlation_id: str = Field(..., description="Correlation ID for related events")
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Event source
    agent_id: Optional[str] = Field(None, description="ID of agent that generated event")
    task_id: Optional[str] = Field(None, description="Related task ID")
    artifact_id: Optional[str] = Field(None, description="Related artifact ID")
    
    # Event payload
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Event properties
    priority: str = Field(default="normal", description="Event priority level")
    retryable: bool = Field(default=True, description="Whether event processing can be retried")


class EventBus:
    """
    Redis Streams-based event bus for real-time event processing.
    
    Provides:
    - Event publishing to multiple streams
    - Consumer group management
    - Event replay capability
    - Stream monitoring and metrics
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        from settings import settings
        
        # Use strict configuration - no fallbacks without explicit config
        if settings.EVENT_BUS == "redis":
            redis_url = redis_url or settings.get_redis_url()
            
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                self.redis.ping()
                logger.info(f"✅ Redis connected successfully: {settings.scrub_url(redis_url)}")
                
            except redis.ConnectionError as e:
                # FAIL-FAST: No fallback to mock when Redis is explicitly configured
                raise RuntimeError(f"Redis configured but unreachable: {settings.scrub_url(redis_url)} - {e}")
        
        elif settings.EVENT_BUS == "mock":
            logger.warning("🚨 WARNING: Using MOCK event bus - simulation data may interfere with real API results")
            self.redis = None
            
        else:
            raise ValueError(f"Invalid EVENT_BUS configuration: {settings.EVENT_BUS}")
        
        # Store configuration
        self.event_bus_type = settings.EVENT_BUS
        self.redis_connected = self.redis is not None
        
        self.stream_prefix = "orchestra"
        self.consumer_groups: Dict[str, str] = {}
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        
    async def publish_event(self, stream_type: EventStreamType, event: StreamEvent) -> str:
        """Publish event to specified stream"""
        
        if not self.redis:
            # CRITICAL: DO NOT publish mock events - they interfere with real API data
            logger.info(f"Event bus disabled - skipping event: {event.event_type}")
            return "disabled"  # Return indicator that event was not published
            
        try:
            stream_name = f"{self.stream_prefix}:{stream_type.value}"
            
            # Serialize event data
            event_data = {
                "event_id": event.event_id,
                "correlation_id": event.correlation_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "agent_id": event.agent_id or "",
                "task_id": event.task_id or "",
                "artifact_id": event.artifact_id or "",
                "payload": json.dumps(event.payload),
                "metadata": json.dumps(event.metadata),
                "priority": event.priority,
                "retryable": str(event.retryable)
            }
            
            # Add to stream
            message_id = self.redis.xadd(stream_name, event_data)
            logger.info(f"Published event {event.event_id} to stream {stream_name}: {message_id}")
            
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            raise
    
    async def create_consumer_group(self, stream_type: EventStreamType, 
                                  group_name: str, consumer_id: str = "0") -> bool:
        """Create consumer group for stream"""
        
        if not self.redis:
            return True
            
        try:
            stream_name = f"{self.stream_prefix}:{stream_type.value}"
            self.redis.xgroup_create(stream_name, group_name, consumer_id, mkstream=True)
            self.consumer_groups[stream_name] = group_name
            logger.info(f"Created consumer group {group_name} for stream {stream_name}")
            return True
            
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group {group_name} already exists")
                return True
            logger.error(f"Failed to create consumer group: {e}")
            return False
    
    async def consume_stream(self, stream_type: EventStreamType, group_name: str,
                           consumer_name: str, count: int = 10) -> List[StreamEvent]:
        """Consume events from stream using consumer group"""
        
        if not self.redis:
            return []
            
        try:
            stream_name = f"{self.stream_prefix}:{stream_type.value}"
            
            # Read from stream
            messages = self.redis.xreadgroup(
                group_name, consumer_name,
                {stream_name: '>'},
                count=count,
                block=1000  # Block for 1 second
            )
            
            events = []
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    try:
                        # Deserialize event
                        event = StreamEvent(
                            event_id=fields["event_id"],
                            correlation_id=fields["correlation_id"],
                            event_type=EventType(fields["event_type"]),
                            timestamp=datetime.fromisoformat(fields["timestamp"]),
                            agent_id=fields.get("agent_id") or None,
                            task_id=fields.get("task_id") or None,
                            artifact_id=fields.get("artifact_id") or None,
                            payload=json.loads(fields.get("payload", "{}")),
                            metadata=json.loads(fields.get("metadata", "{}")),
                            priority=fields.get("priority", "normal"),
                            retryable=fields.get("retryable", "True") == "True"
                        )
                        events.append(event)
                        
                        # Acknowledge message
                        self.redis.xack(stream_name, group_name, msg_id)
                        
                    except Exception as e:
                        logger.error(f"Failed to deserialize event {msg_id}: {e}")
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to consume from stream {stream_name}: {e}")
            return []
    
    async def replay_events(self, stream_type: EventStreamType, 
                          start_time: Optional[datetime] = None,
                          correlation_id: Optional[str] = None) -> AsyncGenerator[StreamEvent, None]:
        """Replay events from stream with optional filtering"""
        
        if not self.redis:
            return
            
        try:
            stream_name = f"{self.stream_prefix}:{stream_type.value}"
            start_id = "0"
            
            if start_time:
                # Convert timestamp to Redis message ID format
                timestamp_ms = int(start_time.timestamp() * 1000)
                start_id = f"{timestamp_ms}-0"
            
            # Read all messages from start
            while True:
                messages = self.redis.xread({stream_name: start_id}, count=100, block=0)
                
                if not messages:
                    break
                
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        try:
                            event = StreamEvent(
                                event_id=fields["event_id"],
                                correlation_id=fields["correlation_id"],
                                event_type=EventType(fields["event_type"]),
                                timestamp=datetime.fromisoformat(fields["timestamp"]),
                                agent_id=fields.get("agent_id") or None,
                                task_id=fields.get("task_id") or None,
                                artifact_id=fields.get("artifact_id") or None,
                                payload=json.loads(fields.get("payload", "{}")),
                                metadata=json.loads(fields.get("metadata", "{}")),
                                priority=fields.get("priority", "normal"),
                                retryable=fields.get("retryable", "True") == "True"
                            )
                            
                            # Filter by correlation ID if specified
                            if correlation_id and event.correlation_id != correlation_id:
                                continue
                                
                            yield event
                            start_id = msg_id
                            
                        except Exception as e:
                            logger.error(f"Failed to deserialize event during replay {msg_id}: {e}")
                            continue
        
        except Exception as e:
            logger.error(f"Failed to replay events from {stream_name}: {e}")
    
    def get_stream_info(self, stream_type: EventStreamType) -> Dict[str, Any]:
        """Get information about stream"""
        
        if not self.redis:
            return {"length": 0, "groups": 0, "mock": True}
            
        try:
            stream_name = f"{self.stream_prefix}:{stream_type.value}"
            info = self.redis.xinfo_stream(stream_name)
            
            return {
                "length": info.get("length", 0),
                "radix_tree_keys": info.get("radix-tree-keys", 0),
                "radix_tree_nodes": info.get("radix-tree-nodes", 0),
                "groups": info.get("groups", 0),
                "last_generated_id": info.get("last-generated-id"),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry")
            }
            
        except redis.ResponseError:
            # Stream doesn't exist yet
            return {"length": 0, "groups": 0, "exists": False}
        except Exception as e:
            logger.error(f"Failed to get stream info: {e}")
            return {"error": str(e)}


class StreamConsumer:
    """Base class for stream consumers with specific processing logic"""
    
    def __init__(self, event_bus: EventBus, consumer_name: str):
        self.event_bus = event_bus
        self.consumer_name = consumer_name
        self.running = False
        self.processed_count = 0
        self.error_count = 0
    
    async def start(self, stream_type: EventStreamType, group_name: str):
        """Start consuming events from stream"""
        
        self.running = True
        logger.info(f"Starting consumer {self.consumer_name} for stream {stream_type}")
        
        # Ensure consumer group exists
        await self.event_bus.create_consumer_group(stream_type, group_name)
        
        while self.running:
            try:
                events = await self.event_bus.consume_stream(
                    stream_type, group_name, self.consumer_name
                )
                
                for event in events:
                    try:
                        await self.process_event(event)
                        self.processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing event {event.event_id}: {e}")
                        self.error_count += 1
                        
                        if not event.retryable:
                            logger.warning(f"Event {event.event_id} marked as non-retryable, skipping")
                
                # Brief pause to avoid busy waiting
                if not events:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Consumer {self.consumer_name} error: {e}")
                await asyncio.sleep(1)
    
    def stop(self):
        """Stop consuming events"""
        self.running = False
        logger.info(f"Stopping consumer {self.consumer_name}")
    
    async def process_event(self, event: StreamEvent):
        """Override this method to implement event processing logic"""
        raise NotImplementedError
    
    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics"""
        return {
            "consumer_name": self.consumer_name,
            "running": self.running,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "success_rate": self.processed_count / (self.processed_count + self.error_count) if (self.processed_count + self.error_count) > 0 else 0
        }


class OrchestratorConsumer(StreamConsumer):
    """Consumer for orchestrating workflow progression based on events"""
    
    def __init__(self, event_bus: EventBus, orchestrator):
        super().__init__(event_bus, "orchestrator_consumer")
        self.orchestrator = orchestrator
    
    async def process_event(self, event: StreamEvent):
        """Process events for workflow orchestration"""
        
        logger.info(f"Orchestrator processing: {event.event_type} for {event.correlation_id}")
        
        if event.event_type == EventType.TASK_CREATED:
            # Task created - assign to appropriate agent
            task_data = event.payload
            await self._assign_task(event.correlation_id, task_data)
            
        elif event.event_type == EventType.ARTIFACT_CREATED:
            # Artifact created - validate and potentially trigger next task
            await self._handle_artifact_creation(event)
            
        elif event.event_type == EventType.TASK_COMPLETED:
            # Task completed - check if workflow can progress
            await self._handle_task_completion(event)
        
        elif event.event_type == EventType.REVIEW_CONFLICT:
            # Review conflict - escalate or retry
            await self._handle_review_conflict(event)
    
    async def _assign_task(self, correlation_id: str, task_data: Dict[str, Any]):
        """Assign task to optimal agent"""
        # Implementation would integrate with routing system
        logger.info(f"Assigning task {correlation_id} based on: {list(task_data.keys())}")
    
    async def _handle_artifact_creation(self, event: StreamEvent):
        """Handle new artifact creation"""
        logger.info(f"New artifact created: {event.artifact_id} by {event.agent_id}")
    
    async def _handle_task_completion(self, event: StreamEvent):
        """Handle task completion and trigger next steps"""
        logger.info(f"Task completed: {event.task_id} by {event.agent_id}")
    
    async def _handle_review_conflict(self, event: StreamEvent):
        """Handle review conflicts"""
        logger.warning(f"Review conflict detected for {event.artifact_id}")


class MetricsConsumer(StreamConsumer):
    """Consumer for collecting performance analytics and metrics"""
    
    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus, "metrics_consumer")
        self.metrics_store: Dict[str, Any] = {}
    
    async def process_event(self, event: StreamEvent):
        """Collect and store performance metrics"""
        
        if event.event_type == EventType.PERFORMANCE_METRIC:
            metric_data = event.payload
            if event.agent_id:
                self._store_metric(event.agent_id, metric_data)
            
        elif event.event_type == EventType.ROUTING_DECISION:
            routing_data = event.payload
            self._store_routing_metric(routing_data)
            
        elif event.event_type in [EventType.TASK_COMPLETED, EventType.TASK_FAILED]:
            self._update_task_metrics(event)
    
    def _store_metric(self, agent_id: str, metric_data: Dict[str, Any]):
        """Store performance metric"""
        if agent_id not in self.metrics_store:
            self.metrics_store[agent_id] = []
        self.metrics_store[agent_id].append(metric_data)
    
    def _store_routing_metric(self, routing_data: Dict[str, Any]):
        """Store routing decision metrics"""
        if "routing" not in self.metrics_store:
            self.metrics_store["routing"] = []
        self.metrics_store["routing"].append(routing_data)
    
    def _update_task_metrics(self, event: StreamEvent):
        """Update task completion metrics"""
        task_metrics = self.metrics_store.get("tasks", [])
        task_metrics.append({
            "task_id": event.task_id or "unknown",
            "agent_id": event.agent_id or "unknown",
            "artifact_id": event.artifact_id or "unknown",
            "status": "completed" if event.event_type == EventType.TASK_COMPLETED else "failed",
            "timestamp": event.timestamp.isoformat(),
            "metadata": event.metadata
        })
        self.metrics_store["tasks"] = task_metrics
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get aggregated metrics summary"""
        return {
            "total_agents": len([k for k in self.metrics_store.keys() if k not in ["routing", "tasks"]]),
            "total_tasks": len(self.metrics_store.get("tasks", [])),
            "total_routing_decisions": len(self.metrics_store.get("routing", [])),
            "agents_with_metrics": list(k for k in self.metrics_store.keys() if k not in ["routing", "tasks"])
        }


class LiveCollaborationEngine:
    """
    Enhanced Live Collaboration Engine with Real-Time Streaming
    
    Implements the complete live collaboration system that shows agents
    working together in real-time with event-driven architecture.
    """
    
    def __init__(self):
        self.event_bus = EventBus()
        self.streams = {
            "tasks": "task_stream",
            "artifacts": "artifact_stream", 
            "reviews": "review_stream",
            "incidents": "incident_stream"
        }
        
        # Real-time collaboration state
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}
        self.live_agent_activities: Dict[str, Any] = {}
        self.artifact_creation_queue: List[Dict[str, Any]] = []
        
        # Progress tracking
        self.collaboration_metrics = {
            "total_sessions": 0,
            "active_agents": 0,
            "artifacts_created": 0,
            "handoffs_completed": 0
        }
        
        logger.info("Live collaboration engine initialized with real-time streaming")
    
    async def publish_event(self, stream: str, event_data: Dict[str, Any]):
        """
        Publish event with correlation_id and artifact_id tracking
        Updates live UI dynamically
        """
        
        # Add correlation and tracking IDs
        correlation_id = event_data.get('correlation_id', f"collab_{uuid4().hex[:8]}")
        artifact_id = event_data.get('artifact_id', f"artifact_{uuid4().hex[:8]}")
        
        # Enhanced event structure
        enhanced_event = StreamEvent(
            event_id=f"live_{uuid4().hex[:8]}",
            correlation_id=correlation_id,
            event_type=event_data.get('event_type', EventType.TASK_CREATED),
            payload={
                **event_data,
                'correlation_id': correlation_id,
                'artifact_id': artifact_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'live_collaboration': True
            },
            metadata={
                'collaboration_engine': 'live_v2',
                'real_time_updates': True,
                'stream_name': stream
            }
        )
        
        # Publish to appropriate stream
        stream_type = EventStreamType.TASKS if stream == "tasks" else EventStreamType.ARTIFACTS
        event_id = await self.event_bus.publish_event(stream_type, enhanced_event)
        
        # Update live collaboration state
        await self._update_live_state(enhanced_event)
        
        # Trigger live UI updates
        await self._update_live_ui(enhanced_event)
        
        logger.info(f"Published live collaboration event {event_id} to {stream}")
        return event_id
    
    async def consume_events(self, stream: str, callback: callable):
        """
        Real-time event consumption with live UI updates
        """
        
        stream_type = EventStreamType.TASKS if stream == "tasks" else EventStreamType.ARTIFACTS
        consumer_group = f"live_collaboration_{stream}"
        consumer_name = f"live_consumer_{uuid4().hex[:8]}"
        
        # Create consumer group
        await self.event_bus.create_consumer_group(stream_type, consumer_group)
        
        # Start consuming
        while True:
            try:
                events = await self.event_bus.consume_stream(
                    stream_type, consumer_group, consumer_name, count=5
                )
                
                for event in events:
                    # Process with callback
                    await callback(event)
                    
                    # Update live collaboration metrics
                    await self._update_collaboration_metrics(event)
                
                # Brief pause to avoid overwhelming
                if not events:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Error consuming from {stream}: {e}")
                await asyncio.sleep(1)
    
    async def _update_live_state(self, event: StreamEvent):
        """Update live collaboration state"""
        
        correlation_id = event.correlation_id
        
        if correlation_id not in self.active_collaborations:
            self.active_collaborations[correlation_id] = {
                'correlation_id': correlation_id,
                'status': 'active',
                'start_time': event.timestamp,
                'agents': set(),
                'artifacts': [],
                'events': [],
                'current_stage': 'initialization'
            }
        
        collaboration = self.active_collaborations[correlation_id]
        collaboration['events'].append({
            'event_id': event.event_id,
            'event_type': event.event_type.value,
            'timestamp': event.timestamp.isoformat(),
            'agent_id': event.agent_id,
            'payload': event.payload
        })
        
        # Track agent activities
        if event.agent_id:
            collaboration['agents'].add(event.agent_id)
            
            self.live_agent_activities[event.agent_id] = {
                'agent_id': event.agent_id,
                'current_activity': event.payload.get('activity', 'Working'),
                'status': event.payload.get('status', 'active'),
                'last_update': event.timestamp.isoformat(),
                'correlation_id': correlation_id
            }
        
        # Track artifact creation
        if event.event_type == EventType.ARTIFACT_CREATED:
            artifact_data = {
                'artifact_id': event.artifact_id or f"artifact_{uuid4().hex[:8]}",
                'type': event.payload.get('artifact_type', 'unknown'),
                'created_by': event.agent_id,
                'creation_time': event.timestamp.isoformat(),
                'correlation_id': correlation_id
            }
            collaboration['artifacts'].append(artifact_data)
            self.artifact_creation_queue.append(artifact_data)
    
    async def _update_live_ui(self, event: StreamEvent):
        """Update live UI components with real-time data"""
        
        ui_update = {
            'type': 'live_update',
            'event_type': event.event_type.value,
            'correlation_id': event.correlation_id,
            'agent_id': event.agent_id,
            'timestamp': event.timestamp.isoformat(),
            'data': event.payload,
            'ui_components': []
        }
        
        # Determine which UI components need updates
        if event.event_type == EventType.AGENT_STARTED:
            ui_update['ui_components'].append('agent_status_panel')
            ui_update['ui_components'].append('live_activity_feed')
            
        elif event.event_type == EventType.ARTIFACT_CREATED:
            ui_update['ui_components'].append('artifact_timeline')
            ui_update['ui_components'].append('progress_indicators')
            
        elif event.event_type == EventType.TASK_COMPLETED:
            ui_update['ui_components'].append('completion_metrics')
            ui_update['ui_components'].append('collaboration_summary')
        
        # Publish UI update event
        ui_event = StreamEvent(
            correlation_id=event.correlation_id,
            event_type=EventType.PERFORMANCE_METRIC,
            payload=ui_update,
            metadata={'ui_update': True, 'real_time': True}
        )
        
        await self.event_bus.publish_event(EventStreamType.METRICS, ui_event)
    
    async def _update_collaboration_metrics(self, event: StreamEvent):
        """Update collaboration metrics in real-time"""
        
        if event.event_type == EventType.AGENT_STARTED:
            self.collaboration_metrics['active_agents'] += 1
            
        elif event.event_type == EventType.AGENT_COMPLETED:
            self.collaboration_metrics['active_agents'] = max(0, self.collaboration_metrics['active_agents'] - 1)
            self.collaboration_metrics['handoffs_completed'] += 1
            
        elif event.event_type == EventType.ARTIFACT_CREATED:
            self.collaboration_metrics['artifacts_created'] += 1
        
        elif event.event_type == EventType.TASK_STARTED:
            self.collaboration_metrics['total_sessions'] += 1
    
    def get_live_collaboration_status(self) -> Dict[str, Any]:
        """Get current live collaboration status"""
        
        return {
            'active_collaborations': len(self.active_collaborations),
            'live_agent_activities': self.live_agent_activities,
            'recent_artifacts': self.artifact_creation_queue[-10:],  # Last 10
            'collaboration_metrics': self.collaboration_metrics,
            'collaboration_details': {
                corr_id: {
                    'status': collab['status'],
                    'agents_count': len(collab['agents']),
                    'artifacts_count': len(collab['artifacts']),
                    'events_count': len(collab['events']),
                    'current_stage': collab['current_stage'],
                    'duration': (datetime.now(timezone.utc) - collab['start_time']).total_seconds()
                }
                for corr_id, collab in self.active_collaborations.items()
            }
        }
    
    def get_agent_activity_feed(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get live agent activity feed"""
        
        activities = []
        for collaboration in self.active_collaborations.values():
            for event in collaboration['events'][-limit:]:
                activities.append({
                    'timestamp': event['timestamp'],
                    'agent_id': event['agent_id'],
                    'event_type': event['event_type'],
                    'activity': event['payload'].get('activity', 'Unknown activity'),
                    'correlation_id': collaboration['correlation_id']
                })
        
        # Sort by timestamp, most recent first
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]
    
    def get_artifact_creation_timeline(self) -> List[Dict[str, Any]]:
        """Get timeline of artifact creation events"""
        
        return sorted(self.artifact_creation_queue, key=lambda x: x['creation_time'], reverse=True)
    
    async def start_live_collaboration_session(self, project_description: str, 
                                            project_type: str = "web_app") -> str:
        """Start a new live collaboration session"""
        
        correlation_id = f"live_collab_{uuid4().hex[:8]}"
        
        # Initialize collaboration
        await self.publish_event("tasks", {
            'event_type': EventType.TASK_STARTED,
            'correlation_id': correlation_id,
            'project_description': project_description,
            'project_type': project_type,
            'activity': 'Starting live collaboration session',
            'live_session': True
        })
        
        logger.info(f"Started live collaboration session {correlation_id}")
        return correlation_id


class RealTimeEventOrchestrator:
    """
    Production-grade event-sourced orchestrator using Redis Streams.
    
    Coordinates multi-agent workflows through real-time event processing
    with full auditability and replay capability.
    """
    
    def __init__(self, workflow_id: str, redis_url: str = "redis://localhost:6379"):
        self.workflow_id = workflow_id
        self.event_bus = EventBus(redis_url)
        self.consumers: List[StreamConsumer] = []
        
        # Initialize consumers
        self.orchestrator_consumer = OrchestratorConsumer(self.event_bus, self)
        self.metrics_consumer = MetricsConsumer(self.event_bus)
        
        self.consumers = [self.orchestrator_consumer, self.metrics_consumer]
        
        logger.info(f"Real-time event orchestrator initialized for workflow {workflow_id}")
    
    async def start_workflow(self, tasks: List[TaskLedger]) -> str:
        """Start workflow and publish initial events"""
        
        correlation_id = f"workflow_{self.workflow_id}_{uuid4().hex[:8]}"
        
        # Start consumers
        await asyncio.gather(*[
            consumer.start(EventStreamType.TASKS, "orchestrator_group")
            for consumer in self.consumers
        ])
        
        # Publish workflow started event
        workflow_event = StreamEvent(
            correlation_id=correlation_id,
            event_type=EventType.TASK_CREATED,
            payload={"workflow_id": self.workflow_id, "tasks": [task.model_dump() for task in tasks]},
            metadata={"total_tasks": len(tasks)}
        )
        
        await self.event_bus.publish_event(EventStreamType.TASKS, workflow_event)
        
        return correlation_id
    
    async def publish_artifact_event(self, artifact: ArtifactBase, event_type: EventType,
                                   agent_id: str, correlation_id: str):
        """Publish artifact-related event"""
        
        event = StreamEvent(
            correlation_id=correlation_id,
            event_type=event_type,
            agent_id=agent_id,
            artifact_id=artifact.artifact_id,
            payload=artifact.model_dump(),
            metadata={
                "confidence": artifact.confidence,
                "version": artifact.version,
                "created_by": artifact.created_by
            }
        )
        
        await self.event_bus.publish_event(EventStreamType.ARTIFACTS, event)
    
    async def get_workflow_events(self, correlation_id: str) -> List[StreamEvent]:
        """Get all events for a workflow"""
        
        events = []
        for stream_type in EventStreamType:
            async for event in self.event_bus.replay_events(stream_type, correlation_id=correlation_id):
                events.append(event)
        
        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)
        return events
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time orchestrator statistics"""
        
        stats = {
            "workflow_id": self.workflow_id,
            "consumers": [consumer.get_stats() for consumer in self.consumers],
            "stream_info": {}
        }
        
        # Get stream information
        for stream_type in EventStreamType:
            stats["stream_info"][stream_type.value] = self.event_bus.get_stream_info(stream_type)
        
        return stats
    
    async def stop(self):
        """Stop all consumers and cleanup"""
        for consumer in self.consumers:
            consumer.stop()
        logger.info(f"Stopped real-time orchestrator for workflow {self.workflow_id}")
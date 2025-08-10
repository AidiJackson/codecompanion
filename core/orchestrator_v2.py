"""
Updated Event-Sourced Orchestrator using the new production bus system.

This replaces the old event_streaming.py orchestrator with cleaner bus integration.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

from bus import bus, Event
from schemas.artifacts import ArtifactBase
from agents.base_agent import AgentType

logger = logging.getLogger(__name__)

class EventSourcedOrchestrator:
    """
    Event-sourced orchestrator using the production bus system.
    
    Coordinates multi-agent workflows through event streams with
    full audit trail and replay capability.
    """
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: List[str] = []
        logger.info(f"🎼 Event-sourced orchestrator initialized: {workflow_id}")
    
    async def start_workflow(self, project_description: str, agents: List[AgentType]) -> str:
        """Start a new multi-agent workflow"""
        
        workflow_event = Event(
            topic="workflow.lifecycle",
            payload={
                "workflow_id": self.workflow_id,
                "event_type": "workflow_started", 
                "project_description": project_description,
                "agents": [agent.value for agent in agents],
                "timestamp": datetime.utcnow().isoformat(),
                "status": "active"
            }
        )
        
        message_id = await bus.publish(workflow_event)
        logger.info(f"✅ Workflow started: {self.workflow_id} -> {message_id}")
        
        return message_id
    
    async def assign_task(self, agent_type: AgentType, task_description: str, 
                         dependencies: List[str] = None) -> str:
        """Assign task to specific agent with dependency tracking"""
        
        task_id = str(uuid.uuid4())
        
        task_event = Event(
            topic="agent.tasks",
            payload={
                "workflow_id": self.workflow_id,
                "task_id": task_id,
                "agent_type": agent_type.value,
                "event_type": "task_assigned",
                "description": task_description,
                "dependencies": dependencies or [],
                "timestamp": datetime.utcnow().isoformat(),
                "status": "pending"
            }
        )
        
        message_id = await bus.publish(task_event)
        
        # Track in local state
        self.active_tasks[task_id] = {
            "agent_type": agent_type,
            "description": task_description,
            "dependencies": dependencies or [],
            "status": "pending",
            "assigned_at": datetime.utcnow()
        }
        
        logger.info(f"📋 Task assigned to {agent_type.value}: {task_id}")
        return task_id
    
    async def complete_task(self, task_id: str, output: Dict[str, Any], 
                          artifacts: List[ArtifactBase] = None) -> str:
        """Mark task as completed with output and artifacts"""
        
        completion_event = Event(
            topic="agent.tasks",
            payload={
                "workflow_id": self.workflow_id,
                "task_id": task_id,
                "event_type": "task_completed",
                "output": output,
                "artifacts": [artifact.dict() for artifact in artifacts or []],
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed"
            }
        )
        
        message_id = await bus.publish(completion_event)
        
        # Update local state
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["completed_at"] = datetime.utcnow()
            self.active_tasks[task_id]["output"] = output
            self.completed_tasks.append(task_id)
        
        logger.info(f"✅ Task completed: {task_id}")
        return message_id
    
    async def publish_artifact(self, artifact: ArtifactBase, 
                              created_by: str, task_id: str = None) -> str:
        """Publish artifact creation event"""
        
        artifact_event = Event(
            topic="artifacts",
            payload={
                "workflow_id": self.workflow_id,
                "artifact_id": artifact.id,
                "artifact_type": artifact.type.value,
                "event_type": "artifact_created",
                "created_by": created_by,
                "task_id": task_id,
                "content": artifact.content,
                "metadata": artifact.metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        message_id = await bus.publish(artifact_event)
        logger.info(f"🎨 Artifact published: {artifact.id} -> {message_id}")
        
        return message_id
    
    async def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status and progress"""
        
        total_tasks = len(self.active_tasks)
        completed_count = len(self.completed_tasks)
        pending_tasks = [tid for tid, task in self.active_tasks.items() 
                        if task["status"] != "completed"]
        
        return {
            "workflow_id": self.workflow_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "pending_tasks": len(pending_tasks),
            "progress_percentage": (completed_count / total_tasks * 100) if total_tasks > 0 else 0,
            "active_task_ids": pending_tasks,
            "completed_task_ids": self.completed_tasks,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def wait_for_dependencies(self, task_id: str) -> bool:
        """Check if all task dependencies are completed"""
        
        if task_id not in self.active_tasks:
            return False
            
        dependencies = self.active_tasks[task_id]["dependencies"]
        
        if not dependencies:
            return True  # No dependencies
            
        # Check if all dependencies are completed
        for dep_id in dependencies:
            if dep_id not in self.completed_tasks:
                logger.info(f"⏳ Task {task_id} waiting for dependency: {dep_id}")
                return False
        
        logger.info(f"✅ All dependencies met for task: {task_id}")
        return True


async def example_orchestration():
    """Example of using the event-sourced orchestrator"""
    
    orchestrator = EventSourcedOrchestrator(f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Start workflow
    await orchestrator.start_workflow(
        "Build a web application with user authentication",
        [AgentType.PROJECT_MANAGER, AgentType.CODE_GENERATOR, AgentType.UI_DESIGNER]
    )
    
    # Assign tasks with dependencies
    pm_task = await orchestrator.assign_task(
        AgentType.PROJECT_MANAGER, 
        "Create project architecture and requirements"
    )
    
    code_task = await orchestrator.assign_task(
        AgentType.CODE_GENERATOR,
        "Implement backend API and authentication",
        dependencies=[pm_task]
    )
    
    ui_task = await orchestrator.assign_task(
        AgentType.UI_DESIGNER,
        "Design user interface and authentication flow", 
        dependencies=[pm_task]
    )
    
    # Simulate task completion
    await orchestrator.complete_task(pm_task, {"architecture": "microservices", "database": "postgresql"})
    
    # Check workflow status
    status = await orchestrator.get_workflow_status()
    logger.info(f"Workflow status: {status}")


if __name__ == "__main__":
    asyncio.run(example_orchestration())
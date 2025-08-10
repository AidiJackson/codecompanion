"""
Parallel Agent Execution Engine
Coordinates multiple AI agents working concurrently with real-time progress tracking
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import uuid4
from enum import Enum
from dataclasses import dataclass, field
import json

from core.event_streaming import EventBus, StreamEvent, EventType, EventStreamType
from agents.base_agent import AgentInput, AgentOutput, AgentType, AgentCapability
from schemas.artifacts import ArtifactType

logger = logging.getLogger(__name__)


class ExecutionPhase(str, Enum):
    """Execution phases for parallel coordination"""
    INITIALIZATION = "initialization"
    PLANNING = "planning"
    PARALLEL_EXECUTION = "parallel_execution"
    COORDINATION = "coordination"
    FINALIZATION = "finalization"


class AgentDependency(str, Enum):
    """Agent dependency types"""
    REQUIRES_OUTPUT = "requires_output"
    BLOCKS_EXECUTION = "blocks_execution"
    PROVIDES_INPUT = "provides_input"
    REVIEWS_WORK = "reviews_work"


@dataclass
class AgentExecutionNode:
    """Represents an agent in the execution graph"""
    agent_type: AgentType
    task_id: str
    correlation_id: str
    agent_input: AgentInput
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[AgentOutput] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    progress: float = 0.0


class ParallelExecutionEngine:
    """
    Coordinates parallel execution of multiple AI agents with intelligent
    dependency management and real-time progress tracking
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.agent_graph: Dict[str, AgentExecutionNode] = {}
        self.execution_metrics = {}
        
        logger.info("Parallel execution engine initialized")
    
    async def execute_parallel_agents(self, project_config: Dict[str, Any]) -> str:
        """
        Execute multiple agents in parallel based on project configuration
        
        Returns execution_id for tracking progress
        """
        execution_id = f"parallel_exec_{uuid4().hex[:8]}"
        
        # Build execution graph
        execution_graph = await self._build_execution_graph(project_config, execution_id)
        
        # Initialize execution tracking
        execution_state = {
            "execution_id": execution_id,
            "project_config": project_config,
            "graph": execution_graph,
            "phase": ExecutionPhase.INITIALIZATION,
            "start_time": datetime.now(timezone.utc),
            "total_agents": len(execution_graph),
            "completed_agents": 0,
            "failed_agents": 0,
            "active_agents": set(),
            "results": {},
            "progress": 0.0
        }
        
        self.active_executions[execution_id] = execution_state
        
        # Publish execution started event
        await self._publish_execution_event(
            execution_id, EventType.TASK_STARTED,
            {"phase": ExecutionPhase.INITIALIZATION, "total_agents": len(execution_graph)}
        )
        
        # Start parallel coordination
        asyncio.create_task(self._coordinate_parallel_execution(execution_id))
        
        logger.info(f"Started parallel execution {execution_id} with {len(execution_graph)} agents")
        return execution_id
    
    async def _build_execution_graph(self, project_config: Dict[str, Any], 
                                   execution_id: str) -> Dict[str, AgentExecutionNode]:
        """Build the agent execution dependency graph"""
        
        graph = {}
        correlation_id = f"{execution_id}_workflow"
        
        # Project Manager - starts immediately (no dependencies)
        pm_node = AgentExecutionNode(
            agent_type=AgentType.PROJECT_MANAGER,
            task_id=f"{execution_id}_pm",
            correlation_id=correlation_id,
            agent_input=AgentInput(
                task_id=f"{execution_id}_pm",
                correlation_id=correlation_id,
                objective="Analyze project requirements and create detailed specifications",
                context=f"Project: {project_config.get('description', '')}\nType: {project_config.get('type', 'web_app')}",
                requested_artifact=ArtifactType.SPEC_DOC,
                priority="high",
                max_processing_time=600,  # 10 minutes
                submitted_by="parallel_engine"
            )
        )
        graph["project_manager"] = pm_node
        
        # Code Generator - depends on Project Manager
        code_node = AgentExecutionNode(
            agent_type=AgentType.CODE_GENERATOR,
            task_id=f"{execution_id}_code",
            correlation_id=correlation_id,
            agent_input=AgentInput(
                task_id=f"{execution_id}_code",
                correlation_id=correlation_id,
                objective="Implement core functionality based on specifications",
                context=f"Project: {project_config.get('description', '')}",
                requested_artifact=ArtifactType.CODE_PATCH,
                dependency_artifacts=[],  # Will be filled from PM output
                priority="high",
                max_processing_time=900,  # 15 minutes
                submitted_by="parallel_engine"
            ),
            dependencies=["project_manager"]
        )
        graph["code_generator"] = code_node
        
        # UI Designer - depends on Project Manager (can run parallel with Code Generator)
        ui_node = AgentExecutionNode(
            agent_type=AgentType.UI_DESIGNER,
            task_id=f"{execution_id}_ui",
            correlation_id=correlation_id,
            agent_input=AgentInput(
                task_id=f"{execution_id}_ui",
                correlation_id=correlation_id,
                objective="Design user interface and user experience",
                context=f"Project: {project_config.get('description', '')}",
                requested_artifact=ArtifactType.DESIGN_DOC,
                dependency_artifacts=[],  # Will be filled from PM output
                priority="medium",
                max_processing_time=600,  # 10 minutes
                submitted_by="parallel_engine"
            ),
            dependencies=["project_manager"]
        )
        graph["ui_designer"] = ui_node
        
        # Test Writer - depends on Code Generator and UI Designer
        test_node = AgentExecutionNode(
            agent_type=AgentType.TEST_WRITER,
            task_id=f"{execution_id}_test",
            correlation_id=correlation_id,
            agent_input=AgentInput(
                task_id=f"{execution_id}_test",
                correlation_id=correlation_id,
                objective="Create comprehensive testing strategy and test cases",
                context=f"Project: {project_config.get('description', '')}",
                requested_artifact=ArtifactType.TEST_PLAN,
                dependency_artifacts=[],  # Will be filled from dependencies
                priority="medium",
                max_processing_time=720,  # 12 minutes
                submitted_by="parallel_engine"
            ),
            dependencies=["code_generator", "ui_designer"]
        )
        graph["test_writer"] = test_node
        
        # Debugger - depends on Code Generator and Test Writer
        debug_node = AgentExecutionNode(
            agent_type=AgentType.DEBUGGER,
            task_id=f"{execution_id}_debug",
            correlation_id=correlation_id,
            agent_input=AgentInput(
                task_id=f"{execution_id}_debug",
                correlation_id=correlation_id,
                objective="Review code quality, identify issues, and optimize performance",
                context=f"Project: {project_config.get('description', '')}",
                requested_artifact=ArtifactType.EVAL_REPORT,
                dependency_artifacts=[],  # Will be filled from dependencies
                priority="medium",
                max_processing_time=600,  # 10 minutes
                submitted_by="parallel_engine"
            ),
            dependencies=["code_generator", "test_writer"]
        )
        graph["debugger"] = debug_node
        
        # Build reverse dependency relationships
        for agent_id, node in graph.items():
            for dep_id in node.dependencies:
                if dep_id in graph:
                    graph[dep_id].dependents.append(agent_id)
        
        return graph
    
    async def _coordinate_parallel_execution(self, execution_id: str):
        """Coordinate the parallel execution of agents"""
        
        execution_state = self.active_executions[execution_id]
        graph = execution_state["graph"]
        
        try:
            # Phase 1: Start agents with no dependencies
            ready_agents = [
                agent_id for agent_id, node in graph.items()
                if not node.dependencies and node.status == "pending"
            ]
            
            for agent_id in ready_agents:
                await self._start_agent_execution(execution_id, agent_id)
            
            # Monitor and coordinate execution
            while execution_state["completed_agents"] + execution_state["failed_agents"] < execution_state["total_agents"]:
                await asyncio.sleep(2)  # Check every 2 seconds
                
                # Check for newly ready agents
                await self._check_and_start_ready_agents(execution_id)
                
                # Update progress
                await self._update_execution_progress(execution_id)
                
                # Check for completion or failure
                if execution_state["failed_agents"] > 0:
                    logger.warning(f"Execution {execution_id} has {execution_state['failed_agents']} failed agents")
            
            # Finalize execution
            await self._finalize_execution(execution_id)
            
        except Exception as e:
            logger.error(f"Parallel execution {execution_id} failed: {e}")
            execution_state["status"] = "failed"
            execution_state["error"] = str(e)
            
            await self._publish_execution_event(
                execution_id, EventType.TASK_FAILED,
                {"error": str(e)}
            )
    
    async def _start_agent_execution(self, execution_id: str, agent_id: str):
        """Start execution of a specific agent"""
        
        execution_state = self.active_executions[execution_id]
        graph = execution_state["graph"]
        node = graph[agent_id]
        
        # Update dependencies in agent input
        dependency_artifacts = []
        for dep_id in node.dependencies:
            dep_node = graph[dep_id]
            if dep_node.result and hasattr(dep_node.result, 'artifact'):
                dependency_artifacts.append(json.dumps(dep_node.result.artifact))
        
        node.agent_input.dependency_artifacts = dependency_artifacts
        node.status = "running"
        node.start_time = datetime.now(timezone.utc)
        execution_state["active_agents"].add(agent_id)
        
        # Publish agent started event
        await self._publish_execution_event(
            execution_id, EventType.AGENT_STARTED,
            {
                "agent_id": agent_id, 
                "agent_type": node.agent_type.value,
                "dependencies": node.dependencies
            }
        )
        
        # Start actual agent execution (mock for now)
        asyncio.create_task(self._execute_agent_task(execution_id, agent_id))
        
        logger.info(f"Started agent {agent_id} in execution {execution_id}")
    
    async def _execute_agent_task(self, execution_id: str, agent_id: str):
        """Execute the actual agent task"""
        
        execution_state = self.active_executions[execution_id]
        graph = execution_state["graph"]
        node = graph[agent_id]
        
        try:
            # Import AI clients for real execution
            from core.ai_clients import RealAIClients, AIClientConfig
            
            ai_clients = RealAIClients(AIClientConfig())
            
            # Update progress periodically
            progress_task = asyncio.create_task(
                self._update_agent_progress(execution_id, agent_id)
            )
            
            # Execute the agent
            result = await ai_clients.execute_agent(node.agent_input, node.agent_type)
            
            # Stop progress updates
            progress_task.cancel()
            
            # Update node with result
            node.result = result
            node.status = "completed"
            node.end_time = datetime.now(timezone.utc)
            node.progress = 1.0
            
            execution_state["active_agents"].discard(agent_id)
            execution_state["completed_agents"] += 1
            execution_state["results"][agent_id] = result
            
            # Publish completion event
            await self._publish_execution_event(
                execution_id, EventType.AGENT_COMPLETED,
                {
                    "agent_id": agent_id,
                    "agent_type": node.agent_type.value,
                    "execution_time": (node.end_time - node.start_time).total_seconds(),
                    "status": result.status if result else "unknown"
                }
            )
            
            logger.info(f"Agent {agent_id} completed in execution {execution_id}")
            
        except Exception as e:
            # Handle agent failure
            node.status = "failed"
            node.error = str(e)
            node.end_time = datetime.now(timezone.utc)
            node.progress = 0.0
            
            execution_state["active_agents"].discard(agent_id)
            execution_state["failed_agents"] += 1
            
            await self._publish_execution_event(
                execution_id, EventType.AGENT_ERROR,
                {
                    "agent_id": agent_id,
                    "agent_type": node.agent_type.value,
                    "error": str(e)
                }
            )
            
            logger.error(f"Agent {agent_id} failed in execution {execution_id}: {e}")
    
    async def _update_agent_progress(self, execution_id: str, agent_id: str):
        """Update agent progress periodically"""
        
        execution_state = self.active_executions[execution_id]
        graph = execution_state["graph"]
        node = graph[agent_id]
        
        try:
            while node.status == "running":
                # Simulate progress based on elapsed time
                if node.start_time:
                    elapsed = (datetime.now(timezone.utc) - node.start_time).total_seconds()
                    max_time = node.agent_input.max_processing_time
                    node.progress = min(elapsed / max_time, 0.95)  # Cap at 95% until completion
                
                await self._publish_execution_event(
                    execution_id, EventType.PERFORMANCE_METRIC,
                    {
                        "agent_id": agent_id,
                        "progress": node.progress,
                        "status": node.status
                    }
                )
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
        except asyncio.CancelledError:
            pass  # Task was cancelled when agent completed
    
    async def _check_and_start_ready_agents(self, execution_id: str):
        """Check for agents whose dependencies are satisfied and start them"""
        
        execution_state = self.active_executions[execution_id]
        graph = execution_state["graph"]
        
        ready_agents = []
        for agent_id, node in graph.items():
            if node.status == "pending":
                # Check if all dependencies are completed
                dependencies_met = all(
                    graph[dep_id].status == "completed" 
                    for dep_id in node.dependencies
                    if dep_id in graph
                )
                
                if dependencies_met:
                    ready_agents.append(agent_id)
        
        for agent_id in ready_agents:
            await self._start_agent_execution(execution_id, agent_id)
    
    async def _update_execution_progress(self, execution_id: str):
        """Update overall execution progress"""
        
        execution_state = self.active_executions[execution_id]
        total_agents = execution_state["total_agents"]
        completed = execution_state["completed_agents"]
        failed = execution_state["failed_agents"]
        
        # Calculate weighted progress
        progress = (completed + failed) / total_agents if total_agents > 0 else 0
        execution_state["progress"] = progress
        
        # Publish progress update
        await self._publish_execution_event(
            execution_id, EventType.PERFORMANCE_METRIC,
            {
                "overall_progress": progress,
                "completed_agents": completed,
                "failed_agents": failed,
                "active_agents": len(execution_state["active_agents"])
            }
        )
    
    async def _finalize_execution(self, execution_id: str):
        """Finalize the parallel execution"""
        
        execution_state = self.active_executions[execution_id]
        execution_state["end_time"] = datetime.now(timezone.utc)
        execution_state["status"] = "completed"
        
        # Calculate execution metrics
        total_time = (execution_state["end_time"] - execution_state["start_time"]).total_seconds()
        success_rate = execution_state["completed_agents"] / execution_state["total_agents"]
        
        execution_state["metrics"] = {
            "total_execution_time": total_time,
            "success_rate": success_rate,
            "parallel_efficiency": self._calculate_parallel_efficiency(execution_state)
        }
        
        # Publish completion event
        await self._publish_execution_event(
            execution_id, EventType.TASK_COMPLETED,
            {
                "execution_time": total_time,
                "success_rate": success_rate,
                "completed_agents": execution_state["completed_agents"],
                "failed_agents": execution_state["failed_agents"]
            }
        )
        
        logger.info(f"Parallel execution {execution_id} completed with {success_rate:.1%} success rate")
    
    def _calculate_parallel_efficiency(self, execution_state: Dict[str, Any]) -> float:
        """Calculate parallel execution efficiency"""
        
        graph = execution_state["graph"]
        total_agent_time = sum(
            (node.end_time - node.start_time).total_seconds()
            for node in graph.values()
            if node.start_time and node.end_time
        )
        
        actual_execution_time = (execution_state["end_time"] - execution_state["start_time"]).total_seconds()
        
        # Efficiency = total work done / (actual time * max possible parallelism)
        max_parallelism = len([node for node in graph.values() if not node.dependencies])
        efficiency = total_agent_time / (actual_execution_time * max_parallelism) if actual_execution_time > 0 else 0
        
        return min(efficiency, 1.0)  # Cap at 100%
    
    async def _publish_execution_event(self, execution_id: str, event_type: EventType, payload: Dict[str, Any]):
        """Publish execution-related events"""
        
        event = StreamEvent(
            correlation_id=execution_id,
            event_type=event_type,
            payload=payload,
            metadata={"execution_engine": "parallel_v1"}
        )
        
        await self.event_bus.publish_event(EventStreamType.TASKS, event)
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of parallel execution"""
        
        execution_state = self.active_executions.get(execution_id)
        if not execution_state:
            return None
        
        graph = execution_state["graph"]
        
        return {
            "execution_id": execution_id,
            "status": execution_state.get("status", "running"),
            "progress": execution_state["progress"],
            "total_agents": execution_state["total_agents"],
            "completed_agents": execution_state["completed_agents"],
            "failed_agents": execution_state["failed_agents"],
            "active_agents": list(execution_state["active_agents"]),
            "agent_details": {
                agent_id: {
                    "status": node.status,
                    "progress": node.progress,
                    "agent_type": node.agent_type.value,
                    "dependencies": node.dependencies,
                    "start_time": node.start_time.isoformat() if node.start_time else None,
                    "error": node.error
                }
                for agent_id, node in graph.items()
            },
            "start_time": execution_state["start_time"].isoformat(),
            "metrics": execution_state.get("metrics", {})
        }
    
    def get_all_active_executions(self) -> List[Dict[str, Any]]:
        """Get status of all active executions"""
        
        return [
            self.get_execution_status(execution_id)
            for execution_id in self.active_executions.keys()
        ]
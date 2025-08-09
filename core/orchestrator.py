"""
Agent orchestration system for managing multi-agent workflows
"""
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json
import logging
from dataclasses import dataclass
from enum import Enum
from .communication import AgentCommunication
from .memory import ProjectMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowState(Enum):
    """Workflow execution states"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class Task:
    """Represents a task in the workflow"""
    task_id: str
    description: str
    assigned_agent: str
    dependencies: List[str]
    status: str = "pending"
    result: Any = None
    created_at: datetime = None
    completed_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class AgentOrchestrator:
    """Central orchestrator for managing multi-agent collaboration"""
    
    def __init__(self, agents: Dict[str, Any], memory: ProjectMemory):
        self.agents = agents
        self.memory = memory
        self.communication = AgentCommunication()
        self.workflow_state = WorkflowState.IDLE
        self.current_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.routing_rules = self._initialize_routing_rules()
        
    def _initialize_routing_rules(self) -> Dict[str, Dict[str, float]]:
        """Initialize agent routing rules with confidence scores"""
        return {
            # Keywords and their agent affinity scores
            "project_manager": {
                "plan": 0.9, "manage": 0.9, "coordinate": 0.8, "timeline": 0.8,
                "requirement": 0.9, "scope": 0.8, "overview": 0.7, "organize": 0.7
            },
            "code_generator": {
                "code": 0.9, "function": 0.9, "algorithm": 0.8, "implement": 0.8,
                "backend": 0.9, "api": 0.8, "database": 0.8, "server": 0.7,
                "python": 0.8, "javascript": 0.7, "sql": 0.7
            },
            "ui_designer": {
                "ui": 0.9, "interface": 0.9, "design": 0.8, "frontend": 0.9,
                "component": 0.8, "layout": 0.7, "style": 0.7, "user": 0.6,
                "react": 0.8, "vue": 0.8, "html": 0.7, "css": 0.7
            },
            "test_writer": {
                "test": 0.9, "testing": 0.9, "validate": 0.8, "quality": 0.8,
                "check": 0.7, "verify": 0.7, "assert": 0.8, "mock": 0.7,
                "unit": 0.8, "integration": 0.7
            },
            "debugger": {
                "debug": 0.9, "fix": 0.9, "error": 0.8, "bug": 0.9,
                "issue": 0.7, "problem": 0.7, "optimize": 0.8, "performance": 0.7,
                "analyze": 0.6, "review": 0.6
            }
        }
    
    def route_request(self, request: str, context: Dict[str, Any] = None) -> str:
        """Route request to the most appropriate agent"""
        request_lower = request.lower()
        agent_scores = {}
        
        # Calculate scores for each agent based on keyword matching
        for agent_name, keywords in self.routing_rules.items():
            score = 0.0
            word_count = 0
            
            for keyword, weight in keywords.items():
                if keyword in request_lower:
                    score += weight
                    word_count += 1
            
            # Normalize score by word count to prevent bias toward agents with more keywords
            if word_count > 0:
                agent_scores[agent_name] = score / len(keywords)
            else:
                agent_scores[agent_name] = 0.0
        
        # Apply context-based adjustments
        if context:
            agent_scores = self._apply_context_adjustments(agent_scores, context)
        
        # Select agent with highest score, default to project_manager
        best_agent = max(agent_scores.items(), key=lambda x: x[1])
        
        logger.info(f"Routing request to {best_agent[0]} (score: {best_agent[1]:.2f})")
        logger.debug(f"All scores: {agent_scores}")
        
        return best_agent[0] if best_agent[1] > 0.1 else "project_manager"
    
    def _apply_context_adjustments(self, scores: Dict[str, float], context: Dict[str, Any]) -> Dict[str, float]:
        """Apply context-based score adjustments"""
        adjusted_scores = scores.copy()
        
        # If there are existing files, boost relevant agents
        if context.get("project_files"):
            files = context["project_files"]
            
            # Boost code_generator for Python/JS files
            if any(f.endswith(('.py', '.js', '.ts')) for f in files.keys()):
                adjusted_scores["code_generator"] += 0.2
            
            # Boost ui_designer for frontend files
            if any(f.endswith(('.html', '.css', '.jsx', '.vue')) for f in files.keys()):
                adjusted_scores["ui_designer"] += 0.2
            
            # Boost test_writer if test files exist
            if any('test' in f.lower() for f in files.keys()):
                adjusted_scores["test_writer"] += 0.2
        
        # If there's a current project, boost project_manager for coordination
        if context.get("current_project"):
            adjusted_scores["project_manager"] += 0.1
        
        return adjusted_scores
    
    def create_task(self, description: str, agent_name: str, dependencies: List[str] = None) -> Task:
        """Create a new task"""
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        task = Task(
            task_id=task_id,
            description=description,
            assigned_agent=agent_name,
            dependencies=dependencies or []
        )
        
        self.current_tasks[task_id] = task
        logger.info(f"Created task {task_id} for {agent_name}: {description}")
        
        return task
    
    def execute_task(self, task: Task, context: Dict[str, Any] = None) -> Any:
        """Execute a single task"""
        if task.assigned_agent not in self.agents:
            raise ValueError(f"Agent {task.assigned_agent} not found")
        
        agent = self.agents[task.assigned_agent]
        task.status = "executing"
        
        try:
            logger.info(f"Executing task {task.task_id} with {task.assigned_agent}")
            
            # Execute the task using the agent
            result = agent.process_request(task.description, context or {})
            
            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now()
            
            # Store result in memory
            self.memory.add_interaction(
                task.description,
                result.get("content", ""),
                task.assigned_agent
            )
            
            # Handle handoffs
            if result.get("handoff_to"):
                handoff_task = self.create_task(
                    f"Handoff from {task.assigned_agent}: {result['content']}",
                    result["handoff_to"],
                    dependencies=[task.task_id]
                )
                return handoff_task
            
            return result
            
        except Exception as e:
            task.status = "failed"
            logger.error(f"Task {task.task_id} failed: {e}")
            raise
        finally:
            # Move completed task to history
            if task.status in ["completed", "failed"]:
                self.completed_tasks.append(task)
                del self.current_tasks[task.task_id]
    
    def execute_workflow(self, initial_request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a complete workflow starting from an initial request"""
        self.workflow_state = WorkflowState.PROCESSING
        workflow_results = []
        
        try:
            # Route initial request
            initial_agent = self.route_request(initial_request, context)
            initial_task = self.create_task(initial_request, initial_agent)
            
            # Execute task chain
            current_task = initial_task
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            while current_task and iteration < max_iterations:
                result = self.execute_task(current_task, context)
                workflow_results.append({
                    "task_id": current_task.task_id,
                    "agent": current_task.assigned_agent,
                    "result": result
                })
                
                # Check if there's a handoff task
                if isinstance(result, Task):
                    current_task = result
                else:
                    current_task = None
                
                iteration += 1
            
            self.workflow_state = WorkflowState.COMPLETED
            
            return {
                "status": "completed",
                "results": workflow_results,
                "total_tasks": len(workflow_results)
            }
            
        except Exception as e:
            self.workflow_state = WorkflowState.ERROR
            logger.error(f"Workflow execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "results": workflow_results
            }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "state": self.workflow_state.value,
            "active_tasks": len(self.current_tasks),
            "completed_tasks": len(self.completed_tasks),
            "current_tasks": [
                {
                    "id": task.task_id,
                    "agent": task.assigned_agent,
                    "status": task.status,
                    "description": task.description[:100] + "..." if len(task.description) > 100 else task.description
                }
                for task in self.current_tasks.values()
            ]
        }
    
    def get_agent_workload(self) -> Dict[str, int]:
        """Get current workload for each agent"""
        workload = {agent_name: 0 for agent_name in self.agents.keys()}
        
        for task in self.current_tasks.values():
            workload[task.assigned_agent] += 1
        
        return workload
    
    def suggest_next_actions(self, context: Dict[str, Any]) -> List[str]:
        """Suggest next possible actions based on current context"""
        suggestions = []
        
        # Analyze project state
        project_files = context.get("project_files", {})
        current_project = context.get("current_project")
        
        if not current_project:
            suggestions.append("Start a new project to begin development")
        
        if not project_files:
            suggestions.append("Generate initial project structure and files")
        else:
            # Suggest improvements based on existing files
            if any(f.endswith('.py') for f in project_files.keys()):
                if not any('test' in f.lower() for f in project_files.keys()):
                    suggestions.append("Add unit tests for the Python code")
            
            if any(f.endswith(('.html', '.js', '.jsx')) for f in project_files.keys()):
                suggestions.append("Review and optimize the user interface")
            
            suggestions.append("Analyze code for potential bugs and optimizations")
            suggestions.append("Add documentation and comments")
        
        # Add general suggestions
        suggestions.extend([
            "Review project requirements and scope",
            "Implement additional features or functionality",
            "Perform code quality and security review"
        ])
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def create_collaboration_plan(self, goal: str, agents_needed: List[str] = None) -> Dict[str, Any]:
        """Create a collaboration plan for achieving a goal"""
        if agents_needed is None:
            agents_needed = list(self.agents.keys())
        
        # Generate task breakdown
        tasks = []
        
        # Always start with project planning
        tasks.append({
            "phase": 1,
            "agent": "project_manager",
            "task": f"Analyze requirements and create project plan for: {goal}",
            "dependencies": []
        })
        
        # Add implementation tasks
        if "code_generator" in agents_needed:
            tasks.append({
                "phase": 2,
                "agent": "code_generator",
                "task": "Implement core functionality and backend logic",
                "dependencies": ["project_manager"]
            })
        
        if "ui_designer" in agents_needed:
            tasks.append({
                "phase": 2,
                "agent": "ui_designer", 
                "task": "Design and implement user interface",
                "dependencies": ["project_manager"]
            })
        
        # Add testing and debugging
        if "test_writer" in agents_needed:
            tasks.append({
                "phase": 3,
                "agent": "test_writer",
                "task": "Create comprehensive test suite",
                "dependencies": ["code_generator", "ui_designer"]
            })
        
        if "debugger" in agents_needed:
            tasks.append({
                "phase": 3,
                "agent": "debugger",
                "task": "Analyze code quality and fix issues",
                "dependencies": ["code_generator", "ui_designer"]
            })
        
        return {
            "goal": goal,
            "agents": agents_needed,
            "tasks": tasks,
            "estimated_phases": max(task["phase"] for task in tasks),
            "created_at": datetime.now().isoformat()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance metrics"""
        if not self.completed_tasks:
            return {"message": "No completed tasks yet"}
        
        # Calculate metrics
        total_tasks = len(self.completed_tasks)
        avg_execution_time = sum(
            (task.completed_at - task.created_at).total_seconds()
            for task in self.completed_tasks
            if task.completed_at
        ) / total_tasks
        
        agent_task_counts = {}
        for task in self.completed_tasks:
            agent_task_counts[task.assigned_agent] = agent_task_counts.get(task.assigned_agent, 0) + 1
        
        success_rate = len([t for t in self.completed_tasks if t.status == "completed"]) / total_tasks
        
        return {
            "total_completed_tasks": total_tasks,
            "average_execution_time_seconds": round(avg_execution_time, 2),
            "agent_task_distribution": agent_task_counts,
            "success_rate": round(success_rate * 100, 1),
            "current_workflow_state": self.workflow_state.value
        }

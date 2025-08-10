"""
Task and progress ledger schemas for tracking multi-agent workflows.

Provides structured tracking of tasks, progress, and context across agent interactions
with proper state management and dependency tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field, validator
from .artifacts import ArtifactType


class TaskStatus(str, Enum):
    """Status values for tasks in the system"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Priority levels for tasks and work items"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkItem(BaseModel):
    """Individual work item within a larger task"""
    
    item_id: str = Field(..., description="Unique work item identifier")
    title: str = Field(..., description="Brief description of work item")
    description: str = Field(..., description="Detailed description")
    assigned_agent: Optional[str] = Field(None, description="Agent assigned to this item")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")
    estimated_effort: Optional[int] = Field(None, description="Estimated hours")
    actual_effort: Optional[int] = Field(None, description="Actual hours spent")
    dependencies: List[str] = Field(default_factory=list, description="IDs of dependent work items")
    blockers: List[str] = Field(default_factory=list, description="Current blocking issues")
    artifacts_produced: List[str] = Field(default_factory=list, description="Artifact IDs produced")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="When work began")
    completed_at: Optional[datetime] = Field(None, description="When work completed")
    notes: str = Field(default="", description="Progress notes and comments")
    
    @validator('estimated_effort', 'actual_effort')
    def validate_effort(cls, v):
        """Ensure effort values are positive"""
        if v is not None and v <= 0:
            raise ValueError("Effort must be positive")
        return v


class TaskLedger(BaseModel):
    """Comprehensive task tracking with goals, tests, and risk management"""
    
    task_id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    goal: str = Field(..., description="Primary objective of this task")
    description: str = Field(..., description="Detailed task description")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task status")
    priority: Priority = Field(default=Priority.MEDIUM, description="Task priority")
    
    # Success criteria and validation
    acceptance_tests: List[Dict[str, Any]] = Field(..., description="Automated acceptance tests")
    success_criteria: List[str] = Field(..., description="Criteria for task completion")
    
    # Planning and risk management
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions")
    risks: List[Dict[str, Any]] = Field(default_factory=list, description="Identified risks")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Risk mitigation plans")
    
    # Execution tracking
    work_items: List[WorkItem] = Field(default_factory=list, description="Breakdown of work items")
    assigned_agents: List[str] = Field(default_factory=list, description="Agents working on this task")
    dependencies: List[str] = Field(default_factory=list, description="IDs of prerequisite tasks")
    blockers: List[str] = Field(default_factory=list, description="Current blocking issues")
    
    # Artifacts and outputs
    expected_artifacts: List[ArtifactType] = Field(..., description="Expected artifact types")
    produced_artifacts: List[str] = Field(default_factory=list, description="IDs of produced artifacts")
    
    # Timeline and effort
    estimated_duration: Optional[int] = Field(None, description="Estimated hours")
    actual_duration: Optional[int] = Field(None, description="Actual hours spent")
    created_at: datetime = Field(default_factory=datetime.now, description="Task creation time")
    started_at: Optional[datetime] = Field(None, description="When work began")
    completed_at: Optional[datetime] = Field(None, description="When task completed")
    
    # Progress tracking
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage")
    notes: str = Field(default="", description="Progress notes and updates")
    
    @validator('acceptance_tests')
    def validate_acceptance_tests(cls, v):
        """Ensure acceptance tests have required structure"""
        required_fields = {'test_id', 'description', 'criteria'}
        for test in v:
            if not isinstance(test, dict) or not required_fields.issubset(test.keys()):
                raise ValueError(f"Acceptance tests must have fields: {required_fields}")
        return v
    
    @validator('risks')
    def validate_risks(cls, v):
        """Ensure risks have required structure"""
        required_fields = {'risk_id', 'description', 'probability', 'impact'}
        for risk in v:
            if not isinstance(risk, dict) or not required_fields.issubset(risk.keys()):
                raise ValueError(f"Risks must have fields: {required_fields}")
        return v
    
    def calculate_progress(self) -> float:
        """Calculate progress based on completed work items"""
        if not self.work_items:
            return self.progress_percentage
        
        completed_items = sum(1 for item in self.work_items if item.status == TaskStatus.COMPLETED)
        return (completed_items / len(self.work_items)) * 100.0


class ContextHandle(BaseModel):
    """Handle for accessing stored context information"""
    
    handle_id: str = Field(..., description="Unique context identifier") 
    context_type: str = Field(..., description="Type of context (conversation, file, etc.)")
    description: str = Field(..., description="Human-readable description")
    size_bytes: int = Field(..., description="Size of stored context")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    last_accessed: Optional[datetime] = Field(None, description="Last access time")
    access_count: int = Field(default=0, description="Number of times accessed")
    tags: List[str] = Field(default_factory=list, description="Classification tags")
    compression_ratio: Optional[float] = Field(None, description="Compression ratio if applicable")


class ProgressLedger(BaseModel):
    """Tracks progress across multiple work items with agent assignments and artifacts"""
    
    ledger_id: str = Field(..., description="Unique ledger identifier")
    project_id: str = Field(..., description="Associated project ID")
    title: str = Field(..., description="Progress ledger title")
    
    # Work item tracking
    work_items: List[WorkItem] = Field(default_factory=list, description="All work items")
    assigned_agents: Dict[str, List[str]] = Field(default_factory=dict, description="Agent to work item mapping")
    
    # Blocking and dependency tracking
    blockers: List[Dict[str, Any]] = Field(default_factory=list, description="System-wide blockers")
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict, description="Work item dependencies")
    
    # Artifact management
    artifacts_registry: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Artifact metadata")
    artifact_dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Artifact dependency mapping")
    
    # Progress metrics
    total_items: int = Field(default=0, description="Total number of work items")
    completed_items: int = Field(default=0, description="Number of completed items") 
    blocked_items: int = Field(default=0, description="Number of blocked items")
    in_progress_items: int = Field(default=0, description="Number of items in progress")
    
    # Timeline tracking
    created_at: datetime = Field(default_factory=datetime.now, description="Ledger creation time")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update time")
    
    @validator('blockers')
    def validate_blockers(cls, v):
        """Ensure blockers have required structure"""
        required_fields = {'blocker_id', 'description', 'severity', 'affected_items'}
        for blocker in v:
            if not isinstance(blocker, dict) or not required_fields.issubset(blocker.keys()):
                raise ValueError(f"Blockers must have fields: {required_fields}")
        return v
    
    def update_metrics(self):
        """Update progress metrics based on current work items"""
        self.total_items = len(self.work_items)
        self.completed_items = sum(1 for item in self.work_items if item.status == TaskStatus.COMPLETED)
        self.blocked_items = sum(1 for item in self.work_items if item.status == TaskStatus.BLOCKED)
        self.in_progress_items = sum(1 for item in self.work_items if item.status == TaskStatus.IN_PROGRESS)
        self.last_updated = datetime.now()


class MemoryIndex(BaseModel):
    """Manages context handles with retrieval budgets and compression rules"""
    
    index_id: str = Field(..., description="Unique memory index identifier")
    project_id: str = Field(..., description="Associated project ID")
    
    # Context management
    context_handles: List[ContextHandle] = Field(default_factory=list, description="Available context handles")
    active_handles: Set[str] = Field(default_factory=set, description="Currently active context handles")
    
    # Budget and resource management
    retrieval_budget: Dict[str, int] = Field(default_factory=dict, description="API call budgets per service")
    storage_budget_mb: float = Field(default=100.0, description="Storage budget in MB")
    current_storage_mb: float = Field(default=0.0, description="Current storage usage in MB")
    
    # Compression and optimization
    compression_rules: Dict[str, Any] = Field(default_factory=dict, description="Context compression rules")
    auto_compress_threshold_mb: float = Field(default=50.0, description="Auto-compression threshold")
    max_handle_age_days: int = Field(default=30, description="Max age for context handles")
    
    # Access patterns
    access_patterns: Dict[str, List[datetime]] = Field(default_factory=dict, description="Handle access history")
    priority_handles: List[str] = Field(default_factory=list, description="High-priority context handles")
    
    created_at: datetime = Field(default_factory=datetime.now, description="Index creation time")
    last_cleaned: Optional[datetime] = Field(None, description="Last cleanup time")
    
    def get_storage_utilization(self) -> float:
        """Calculate storage utilization percentage"""
        return (self.current_storage_mb / self.storage_budget_mb) * 100.0
    
    def needs_cleanup(self) -> bool:
        """Determine if cleanup is needed"""
        return (self.current_storage_mb > self.auto_compress_threshold_mb or 
                self.get_storage_utilization() > 80.0)


# Example instances for testing and documentation
EXAMPLE_TASK_LEDGER = TaskLedger(
    task_id="task-001",
    title="Build Product Catalog API",
    goal="Create REST API for e-commerce product management",
    description="Build comprehensive API with CRUD operations, search, and filtering",
    acceptance_tests=[
        {
            "test_id": "test-001",
            "description": "All CRUD endpoints return proper HTTP status codes",
            "criteria": "200 for GET, 201 for POST, 204 for DELETE"
        }
    ],
    success_criteria=["API documentation complete", "All tests pass", "Performance under 200ms"],
    expected_artifacts=[ArtifactType.SPEC_DOC, ArtifactType.DESIGN_DOC, ArtifactType.CODE_PATCH],
    risks=[
        {
            "risk_id": "risk-001",
            "description": "Database performance issues with large datasets",
            "probability": 0.3,
            "impact": "high"
        }
    ]
)

EXAMPLE_PROGRESS_LEDGER = ProgressLedger(
    ledger_id="progress-001", 
    project_id="project-001",
    title="E-commerce API Development Progress",
    work_items=[
        WorkItem(
            item_id="item-001",
            title="Design database schema",
            description="Create PostgreSQL schema for products",
            assigned_agent="claude-agent",
            status=TaskStatus.COMPLETED
        ),
        WorkItem(
            item_id="item-002", 
            title="Implement API endpoints",
            description="Build FastAPI endpoints for CRUD operations",
            assigned_agent="gpt4-agent",
            status=TaskStatus.IN_PROGRESS
        )
    ]
)
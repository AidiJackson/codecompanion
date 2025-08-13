"""
Task Outcome Schema for Router Learning

Defines the structured format for task execution outcomes
used by the intelligent router learning system.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from schemas.routing import ModelType, TaskType, TaskComplexity


class TaskOutcome(BaseModel):
    """Outcome data for learning"""

    task_id: str = Field(..., description="Unique task identifier")
    model_used: ModelType = Field(..., description="Model that executed the task")
    task_type: TaskType = Field(..., description="Type of task")
    complexity: TaskComplexity = Field(..., description="Task complexity")

    # Outcome metrics
    success: bool = Field(..., description="Task completed successfully")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality of output")
    execution_time: float = Field(..., description="Time to complete in seconds")
    token_usage: int = Field(..., description="Tokens consumed")
    cost: float = Field(..., description="Actual cost incurred")

    # Context information
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )
    error_type: Optional[str] = Field(None, description="Error type if failed")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Completion timestamp"
    )

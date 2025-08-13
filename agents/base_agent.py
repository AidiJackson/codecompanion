"""
Base agent architecture with structured I/O contracts.

Defines standardized input/output interfaces, capability declarations,
and common agent behaviors for consistent multi-agent coordination.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import logging
from uuid import uuid4

from schemas.artifacts import ArtifactType
from schemas.routing import ModelType, TaskType


logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents in the system"""

    PROJECT_MANAGER = "project_manager"
    CODE_GENERATOR = "code_generator"
    UI_DESIGNER = "ui_designer"
    TEST_WRITER = "test_writer"
    DEBUGGER = "debugger"
    REVIEWER = "reviewer"


class AgentCapability(BaseModel):
    """Agent capability declaration"""

    agent_type: AgentType = Field(..., description="Type of agent")
    model_type: ModelType = Field(..., description="Underlying AI model")

    # Capability scores
    primary_tasks: List[TaskType] = Field(..., description="Primary task types")
    secondary_tasks: List[TaskType] = Field(
        default_factory=list, description="Secondary task types"
    )

    # Supported artifact types
    produces_artifacts: List[ArtifactType] = Field(
        ..., description="Artifact types this agent produces"
    )
    consumes_artifacts: List[ArtifactType] = Field(
        default_factory=list, description="Artifact types this agent consumes"
    )

    # Performance characteristics
    avg_processing_time_minutes: float = Field(
        ..., description="Average processing time"
    )
    quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Historical quality score"
    )
    reliability_score: float = Field(
        ..., ge=0.0, le=1.0, description="Reliability score"
    )

    # Constraints and preferences
    max_context_length: int = Field(..., description="Maximum context length")
    preferred_complexity_level: str = Field(
        default="medium", description="Preferred task complexity"
    )

    class Config:
        use_enum_values = True


class AgentInput(BaseModel):
    """Standardized agent input contract"""

    # Request identification
    request_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique request identifier"
    )
    task_id: str = Field(..., description="Task identifier")
    correlation_id: Optional[str] = Field(
        None, description="Correlation ID for related requests"
    )

    # Task specification
    objective: str = Field(..., description="Primary objective or goal")
    context: str = Field(..., description="Detailed context and background")

    # Context and dependencies
    context_handles: List[str] = Field(
        default_factory=list, description="Context handle IDs for retrieval"
    )
    dependency_artifacts: List[str] = Field(
        default_factory=list, description="IDs of dependent artifacts"
    )

    # Request specification
    requested_artifact: Optional[ArtifactType] = Field(
        default=ArtifactType.SPEC_DOC, description="Type of artifact to produce"
    )

    # Policies and constraints
    policies: Dict[str, Any] = Field(
        default_factory=dict, description="Processing policies and constraints"
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict, description="Processing preferences"
    )

    # Quality requirements
    quality_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Minimum quality threshold"
    )
    completeness_threshold: float = Field(
        default=0.9, ge=0.0, le=1.0, description="Minimum completeness threshold"
    )

    # Execution constraints
    max_processing_time: Optional[int] = Field(
        None, description="Maximum processing time in seconds"
    )
    priority: str = Field(default="medium", description="Request priority level")

    # Metadata
    submitted_at: datetime = Field(
        default_factory=datetime.now, description="Request submission time"
    )
    submitted_by: str = Field(
        default="system", description="ID of requesting agent or system"
    )


class AgentOutput(BaseModel):
    """Standardized agent output contract"""

    # Response identification
    request_id: str = Field(..., description="Original request ID")
    response_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique response identifier"
    )

    # Processing metadata
    processed_at: datetime = Field(
        default_factory=datetime.now, description="Processing completion time"
    )
    processing_duration: float = Field(
        ..., description="Processing duration in seconds"
    )
    agent_id: str = Field(..., description="ID of agent that produced this output")
    model_used: ModelType = Field(..., description="AI model used for processing")

    # Primary output
    artifact: Dict[str, Any] = Field(..., description="Produced artifact (typed)")

    # Quality metrics
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in the output"
    )
    quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Self-assessed quality score"
    )
    completeness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Completeness score"
    )

    # Additional outputs and context
    notes: str = Field(default="", description="Processing notes and observations")
    warnings: List[str] = Field(
        default_factory=list, description="Warnings encountered during processing"
    )
    intermediate_results: List[Dict[str, Any]] = Field(
        default_factory=list, description="Intermediate processing results"
    )

    # Follow-up requests
    tests_requested: List[str] = Field(
        default_factory=list, description="Suggested tests for the artifact"
    )
    review_points: List[str] = Field(
        default_factory=list, description="Points that need review"
    )
    dependencies_identified: List[str] = Field(
        default_factory=list, description="Additional dependencies identified"
    )

    # Resource usage
    tokens_consumed: Optional[int] = Field(
        None, description="Number of tokens consumed"
    )
    api_calls_made: int = Field(default=1, description="Number of API calls made")

    # Status and error handling
    status: str = Field(default="completed", description="Processing status")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    retry_count: int = Field(default=0, description="Number of retries attempted")


class ProcessingResult(BaseModel):
    """Internal processing result for agent implementations"""

    success: bool = Field(..., description="Whether processing was successful")
    output: Optional[AgentOutput] = Field(
        None, description="Agent output if successful"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_recommended: bool = Field(
        default=False, description="Whether retry is recommended"
    )

    # Performance metrics
    processing_time: float = Field(..., description="Processing time in seconds")
    resource_usage: Dict[str, Any] = Field(
        default_factory=dict, description="Resource usage metrics"
    )


class BaseAgent(ABC):
    """
    Abstract base class for all agents with structured I/O contracts.

    Provides:
    - Standardized input/output interfaces
    - Common validation and error handling
    - Capability declaration
    - Performance monitoring
    - Retry logic
    """

    def __init__(self, agent_id: str, capabilities: AgentCapability):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.processing_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, float] = {
            "avg_processing_time": 0.0,
            "success_rate": 1.0,
            "avg_quality_score": 0.0,
            "total_requests": 0,
        }

        logger.info(f"Initialized {self.__class__.__name__} with ID {agent_id}")

    @abstractmethod
    async def _process_request(self, agent_input: AgentInput) -> ProcessingResult:
        """
        Core processing method to be implemented by subclasses.

        This method contains the agent-specific logic for processing requests
        and producing artifacts.
        """
        pass

    @abstractmethod
    def _validate_input(self, agent_input: AgentInput) -> List[str]:
        """
        Validate input for agent-specific requirements.

        Returns list of validation errors (empty if valid).
        """
        pass

    def can_handle_task(self, task_type: TaskType, artifact_type: ArtifactType) -> bool:
        """Check if agent can handle specific task and artifact type"""

        task_compatible = (
            task_type in self.capabilities.primary_tasks
            or task_type in self.capabilities.secondary_tasks
        )

        artifact_compatible = artifact_type in self.capabilities.produces_artifacts

        return task_compatible and artifact_compatible

    def estimate_processing_time(self, agent_input: AgentInput) -> float:
        """Estimate processing time for given input"""

        base_time = self.capabilities.avg_processing_time_minutes

        # Adjust based on input complexity
        context_factor = min(
            2.0, len(agent_input.context) / 1000
        )  # Longer context = more time
        dependency_factor = 1.0 + (
            len(agent_input.dependency_artifacts) * 0.1
        )  # More deps = more time
        quality_factor = agent_input.quality_threshold  # Higher quality = more time

        estimated_time = base_time * context_factor * dependency_factor * quality_factor

        return max(1.0, estimated_time)  # Minimum 1 minute

    async def process_request(self, agent_input: AgentInput) -> AgentOutput:
        """
        Main entry point for processing requests with full error handling and validation.
        """

        start_time = datetime.now()

        try:
            # Input validation
            validation_errors = self._validate_common_input(agent_input)
            validation_errors.extend(self._validate_input(agent_input))

            if validation_errors:
                return self._create_error_output(
                    agent_input,
                    f"Input validation failed: {'; '.join(validation_errors)}",
                    start_time,
                )

            # Capability check
            if not self.can_handle_task(
                TaskType.REASONING_LONG, agent_input.requested_artifact
            ):
                # Note: This is simplified - in real implementation, we'd infer task type
                logger.warning(
                    f"Agent {self.agent_id} may not be optimal for {agent_input.requested_artifact}"
                )

            # Process request
            logger.info(
                f"Processing request {agent_input.request_id} for task {agent_input.task_id}"
            )

            processing_result = await self._process_request(agent_input)

            if not processing_result.success:
                return self._create_error_output(
                    agent_input,
                    processing_result.error_message or "Processing failed",
                    start_time,
                )

            # Update performance metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(processing_result.output, processing_time)

            # Store processing history
            self._record_processing_history(
                agent_input, processing_result.output, processing_time
            )

            return processing_result.output

        except Exception as e:
            logger.error(
                f"Unexpected error processing request {agent_input.request_id}: {e}"
            )
            return self._create_error_output(
                agent_input, f"Unexpected error: {str(e)}", start_time
            )

    def _validate_common_input(self, agent_input: AgentInput) -> List[str]:
        """Common input validation for all agents"""
        errors = []

        if not agent_input.task_id:
            errors.append("Task ID is required")

        if not agent_input.objective:
            errors.append("Objective is required")

        if len(agent_input.context) < 10:
            errors.append("Context is too brief (minimum 10 characters)")

        if agent_input.quality_threshold < 0.0 or agent_input.quality_threshold > 1.0:
            errors.append("Quality threshold must be between 0.0 and 1.0")

        if agent_input.requested_artifact not in self.capabilities.produces_artifacts:
            errors.append(
                f"Agent cannot produce {agent_input.requested_artifact.value}"
            )

        return errors

    def _create_error_output(
        self, agent_input: AgentInput, error_message: str, start_time: datetime
    ) -> AgentOutput:
        """Create error output for failed processing"""

        processing_time = (datetime.now() - start_time).total_seconds()

        return AgentOutput(
            request_id=agent_input.request_id,
            processing_duration=processing_time,
            agent_id=self.agent_id,
            model_used=self.capabilities.model_type,
            artifact={
                "artifact_id": f"error_{agent_input.request_id}",
                "artifact_type": agent_input.requested_artifact.value,
                "created_by": self.agent_id,
                "error": True,
                "error_message": error_message,
            },
            confidence=0.0,
            quality_score=0.0,
            completeness_score=0.0,
            status="failed",
            errors=[error_message],
        )

    def _update_performance_metrics(self, output: AgentOutput, processing_time: float):
        """Update agent performance metrics"""

        self.performance_metrics["total_requests"] += 1
        total_requests = self.performance_metrics["total_requests"]

        # Update averages
        self.performance_metrics["avg_processing_time"] = (
            self.performance_metrics["avg_processing_time"] * (total_requests - 1)
            + processing_time
        ) / total_requests

        success = output.status == "completed"
        self.performance_metrics["success_rate"] = (
            self.performance_metrics["success_rate"] * (total_requests - 1)
            + (1.0 if success else 0.0)
        ) / total_requests

        if success:
            self.performance_metrics["avg_quality_score"] = (
                self.performance_metrics["avg_quality_score"] * (total_requests - 1)
                + output.quality_score
            ) / total_requests

    def _record_processing_history(
        self, agent_input: AgentInput, output: AgentOutput, processing_time: float
    ):
        """Record processing history for analysis"""

        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": agent_input.request_id,
            "task_id": agent_input.task_id,
            "artifact_type": agent_input.requested_artifact.value,
            "processing_time": processing_time,
            "quality_score": output.quality_score,
            "confidence": output.confidence,
            "status": output.status,
            "tokens_consumed": output.tokens_consumed,
            "context_length": len(agent_input.context),
        }

        self.processing_history.append(history_entry)

        # Keep only recent history (last 100 requests)
        if len(self.processing_history) > 100:
            self.processing_history = self.processing_history[-100:]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get agent performance summary"""

        recent_history = self.processing_history[-20:]  # Last 20 requests

        return {
            "agent_id": self.agent_id,
            "agent_type": self.capabilities.agent_type.value,
            "model_type": self.capabilities.model_type.value,
            "total_requests": self.performance_metrics["total_requests"],
            "success_rate": self.performance_metrics["success_rate"],
            "avg_processing_time": self.performance_metrics["avg_processing_time"],
            "avg_quality_score": self.performance_metrics["avg_quality_score"],
            "recent_performance": {
                "avg_processing_time": sum(h["processing_time"] for h in recent_history)
                / max(len(recent_history), 1),
                "avg_quality_score": sum(h["quality_score"] for h in recent_history)
                / max(len(recent_history), 1),
                "success_rate": sum(
                    1 for h in recent_history if h["status"] == "completed"
                )
                / max(len(recent_history), 1),
            },
            "capabilities": {
                "primary_tasks": [
                    task.value for task in self.capabilities.primary_tasks
                ],
                "produces_artifacts": [
                    art.value for art in self.capabilities.produces_artifacts
                ],
                "max_context_length": self.capabilities.max_context_length,
            },
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id}, model={self.capabilities.model_type.value})"

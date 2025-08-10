"""
Agent Communication Protocol with strict handoff validation and routing rules.

This module enforces clean collaboration between agents by validating artifact types
and ensuring proper communication flows based on agent capabilities.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from pydantic import BaseModel, Field, ValidationError

from schemas.artifact_schemas import ArtifactType
from core.artifact_handler import TypedArtifactHandler


logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Supported agent types in the system"""
    PROJECT_MANAGER = "project_manager"
    CODE_GENERATOR = "code_generator"
    TEST_WRITER = "test_writer"
    UI_DESIGNER = "ui_designer"
    DEBUGGER = "debugger"


class HandoffStatus(str, Enum):
    """Status of agent handoff operations"""
    PENDING = "pending"
    VALIDATED = "validated"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class HandoffRule(BaseModel):
    """Rule defining valid handoffs between agents"""
    
    from_agent: AgentType = Field(..., description="Source agent type")
    to_agent: AgentType = Field(..., description="Target agent type")
    required_artifacts: List[ArtifactType] = Field(..., description="Required artifact types")
    optional_artifacts: List[ArtifactType] = Field(default_factory=list, description="Optional artifacts")
    conditions: List[str] = Field(default_factory=list, description="Additional conditions for handoff")
    priority: int = Field(default=1, description="Priority level (1=highest)")
    
    class Config:
        use_enum_values = True


class HandoffRequest(BaseModel):
    """Request for agent handoff with artifacts"""
    
    request_id: str = Field(..., description="Unique handoff request ID")
    from_agent: AgentType = Field(..., description="Source agent")
    to_agent: AgentType = Field(..., description="Target agent")
    artifacts: List[str] = Field(..., description="Artifact IDs being handed off")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    priority: int = Field(default=1, description="Request priority")
    created_at: datetime = Field(default_factory=datetime.now, description="Request timestamp")
    
    class Config:
        use_enum_values = True


class HandoffResult(BaseModel):
    """Result of handoff validation and execution"""
    
    request_id: str = Field(..., description="Original request ID")
    status: HandoffStatus = Field(..., description="Handoff status")
    validated_artifacts: List[str] = Field(default_factory=list, description="Successfully validated artifacts")
    rejected_artifacts: List[str] = Field(default_factory=list, description="Rejected artifacts")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    processing_time: float = Field(default=0.0, description="Processing time in seconds")
    
    class Config:
        use_enum_values = True


class AgentHandoff:
    """
    Agent communication protocol with strict handoff validation.
    
    Manages the flow of artifacts between agents, ensuring that only valid
    artifact types are exchanged according to agent capabilities and workflow rules.
    """
    
    def __init__(self, artifact_handler: TypedArtifactHandler):
        self.artifact_handler = artifact_handler
        
        # Define agent capability matrix
        self.agent_capabilities = {
            AgentType.PROJECT_MANAGER: {
                "produces": [ArtifactType.SPEC_DOC, ArtifactType.EVAL_REPORT],
                "consumes": [ArtifactType.EVAL_REPORT, ArtifactType.TEST_PLAN],
                "expertise": ["requirements", "planning", "coordination", "evaluation"]
            },
            AgentType.CODE_GENERATOR: {
                "produces": [ArtifactType.CODE_PATCH, ArtifactType.DESIGN_DOC],
                "consumes": [ArtifactType.SPEC_DOC, ArtifactType.DESIGN_DOC],
                "expertise": ["implementation", "architecture", "coding", "algorithms"]
            },
            AgentType.TEST_WRITER: {
                "produces": [ArtifactType.TEST_PLAN, ArtifactType.EVAL_REPORT],
                "consumes": [ArtifactType.CODE_PATCH, ArtifactType.SPEC_DOC],
                "expertise": ["testing", "quality_assurance", "validation", "automation"]
            },
            AgentType.UI_DESIGNER: {
                "produces": [ArtifactType.DESIGN_DOC, ArtifactType.CODE_PATCH],
                "consumes": [ArtifactType.SPEC_DOC, ArtifactType.DESIGN_DOC],
                "expertise": ["user_interface", "user_experience", "frontend", "design"]
            },
            AgentType.DEBUGGER: {
                "produces": [ArtifactType.EVAL_REPORT, ArtifactType.CODE_PATCH],
                "consumes": [ArtifactType.CODE_PATCH, ArtifactType.TEST_PLAN],
                "expertise": ["debugging", "optimization", "code_analysis", "performance"]
            }
        }
        
        # Define handoff rules
        self.handoff_rules = {
            # Project Manager handoffs
            (AgentType.PROJECT_MANAGER, AgentType.CODE_GENERATOR): HandoffRule(
                from_agent=AgentType.PROJECT_MANAGER,
                to_agent=AgentType.CODE_GENERATOR,
                required_artifacts=[ArtifactType.SPEC_DOC],
                optional_artifacts=[ArtifactType.DESIGN_DOC],
                conditions=["requirements_complete", "acceptance_criteria_defined"],
                priority=1
            ),
            (AgentType.PROJECT_MANAGER, AgentType.UI_DESIGNER): HandoffRule(
                from_agent=AgentType.PROJECT_MANAGER,
                to_agent=AgentType.UI_DESIGNER,
                required_artifacts=[ArtifactType.SPEC_DOC],
                conditions=["ui_requirements_specified"],
                priority=2
            ),
            
            # Code Generator handoffs
            (AgentType.CODE_GENERATOR, AgentType.TEST_WRITER): HandoffRule(
                from_agent=AgentType.CODE_GENERATOR,
                to_agent=AgentType.TEST_WRITER,
                required_artifacts=[ArtifactType.CODE_PATCH],
                optional_artifacts=[ArtifactType.DESIGN_DOC],
                conditions=["code_complete", "interfaces_defined"],
                priority=1
            ),
            (AgentType.CODE_GENERATOR, AgentType.DEBUGGER): HandoffRule(
                from_agent=AgentType.CODE_GENERATOR,
                to_agent=AgentType.DEBUGGER,
                required_artifacts=[ArtifactType.CODE_PATCH],
                conditions=["code_review_needed"],
                priority=3
            ),
            
            # Test Writer handoffs
            (AgentType.TEST_WRITER, AgentType.PROJECT_MANAGER): HandoffRule(
                from_agent=AgentType.TEST_WRITER,
                to_agent=AgentType.PROJECT_MANAGER,
                required_artifacts=[ArtifactType.TEST_PLAN],
                optional_artifacts=[ArtifactType.EVAL_REPORT],
                conditions=["testing_complete"],
                priority=1
            ),
            (AgentType.TEST_WRITER, AgentType.DEBUGGER): HandoffRule(
                from_agent=AgentType.TEST_WRITER,
                to_agent=AgentType.DEBUGGER,
                required_artifacts=[ArtifactType.TEST_PLAN],
                conditions=["test_failures_detected"],
                priority=2
            ),
            
            # UI Designer handoffs
            (AgentType.UI_DESIGNER, AgentType.CODE_GENERATOR): HandoffRule(
                from_agent=AgentType.UI_DESIGNER,
                to_agent=AgentType.CODE_GENERATOR,
                required_artifacts=[ArtifactType.DESIGN_DOC],
                optional_artifacts=[ArtifactType.CODE_PATCH],
                conditions=["design_approved"],
                priority=1
            ),
            (AgentType.UI_DESIGNER, AgentType.TEST_WRITER): HandoffRule(
                from_agent=AgentType.UI_DESIGNER,
                to_agent=AgentType.TEST_WRITER,
                required_artifacts=[ArtifactType.DESIGN_DOC],
                conditions=["ui_testing_needed"],
                priority=2
            ),
            
            # Debugger handoffs
            (AgentType.DEBUGGER, AgentType.CODE_GENERATOR): HandoffRule(
                from_agent=AgentType.DEBUGGER,
                to_agent=AgentType.CODE_GENERATOR,
                required_artifacts=[ArtifactType.EVAL_REPORT],
                optional_artifacts=[ArtifactType.CODE_PATCH],
                conditions=["fixes_required"],
                priority=1
            ),
            (AgentType.DEBUGGER, AgentType.PROJECT_MANAGER): HandoffRule(
                from_agent=AgentType.DEBUGGER,
                to_agent=AgentType.PROJECT_MANAGER,
                required_artifacts=[ArtifactType.EVAL_REPORT],
                conditions=["critical_issues_found"],
                priority=1
            )
        }
        
        # Track active handoffs
        self.active_handoffs: Dict[str, HandoffRequest] = {}
        self.handoff_history: List[HandoffResult] = []
    
    def validate_handoff(self, from_agent: str, to_agent: str, 
                        artifacts: List[str]) -> HandoffResult:
        """
        Validate a proposed handoff between agents.
        
        Args:
            from_agent: Source agent identifier
            to_agent: Target agent identifier
            artifacts: List of artifact IDs to hand off
            
        Returns:
            HandoffResult with validation status and details
        """
        
        start_time = datetime.now()
        request_id = f"handoff_{start_time.strftime('%Y%m%d_%H%M%S')}_{from_agent}_{to_agent}"
        
        try:
            # Convert agent strings to enum types
            from_agent_type = AgentType(from_agent)
            to_agent_type = AgentType(to_agent)
            
        except ValueError as e:
            return HandoffResult(
                request_id=request_id,
                status=HandoffStatus.REJECTED,
                validation_errors=[f"Invalid agent type: {e}"],
                processing_time=(datetime.now() - start_time).total_seconds()
            )
        
        # Check if handoff rule exists
        handoff_rule = self.handoff_rules.get((from_agent_type, to_agent_type))
        if not handoff_rule:
            return HandoffResult(
                request_id=request_id,
                status=HandoffStatus.REJECTED,
                validation_errors=[f"No handoff rule defined for {from_agent} -> {to_agent}"],
                recommendations=[f"Define handoff protocol for {from_agent} -> {to_agent}"],
                processing_time=(datetime.now() - start_time).total_seconds()
            )
        
        # Validate artifacts
        validated_artifacts = []
        rejected_artifacts = []
        validation_errors = []
        
        # Check artifact existence and types
        artifact_types = []
        for artifact_id in artifacts:
            artifact = self.artifact_handler.get_artifact(artifact_id)
            if not artifact:
                rejected_artifacts.append(artifact_id)
                validation_errors.append(f"Artifact {artifact_id} not found")
                continue
            
            artifact_types.append(artifact.artifact_type)
            validated_artifacts.append(artifact_id)
        
        # Validate required artifacts
        required_artifacts = set(handoff_rule.required_artifacts)
        provided_artifacts = set(artifact_types)
        
        missing_required = required_artifacts - provided_artifacts
        if missing_required:
            validation_errors.append(
                f"Missing required artifacts: {[art.value for art in missing_required]}"
            )
        
        # Check agent capabilities
        from_capabilities = self.agent_capabilities.get(from_agent_type, {})
        to_capabilities = self.agent_capabilities.get(to_agent_type, {})
        
        # Validate that from_agent can produce these artifacts
        can_produce = set(from_capabilities.get("produces", []))
        invalid_producers = provided_artifacts - can_produce
        if invalid_producers:
            validation_errors.append(
                f"Agent {from_agent} cannot produce: {[art.value for art in invalid_producers]}"
            )
        
        # Validate that to_agent can consume these artifacts
        can_consume = set(to_capabilities.get("consumes", []))
        invalid_consumers = provided_artifacts - can_consume
        if invalid_consumers:
            validation_errors.append(
                f"Agent {to_agent} cannot consume: {[art.value for art in invalid_consumers]}"
            )
        
        # Determine final status
        if validation_errors:
            status = HandoffStatus.REJECTED
        elif missing_required:
            status = HandoffStatus.PENDING
        else:
            status = HandoffStatus.VALIDATED
        
        # Generate recommendations
        recommendations = []
        if missing_required:
            recommendations.append(
                f"Provide missing artifacts: {[art.value for art in missing_required]}"
            )
        if invalid_producers:
            recommendations.append(
                f"Use appropriate agent for producing: {[art.value for art in invalid_producers]}"
            )
        if invalid_consumers:
            recommendations.append(
                f"Route artifacts to compatible agent for: {[art.value for art in invalid_consumers]}"
            )
        
        result = HandoffResult(
            request_id=request_id,
            status=status,
            validated_artifacts=validated_artifacts,
            rejected_artifacts=rejected_artifacts,
            validation_errors=validation_errors,
            recommendations=recommendations,
            processing_time=(datetime.now() - start_time).total_seconds()
        )
        
        # Store result
        self.handoff_history.append(result)
        
        logger.info(f"Handoff validation {from_agent} -> {to_agent}: {status.value}")
        
        return result
    
    def execute_handoff(self, handoff_request: HandoffRequest) -> HandoffResult:
        """
        Execute a validated handoff request.
        
        Args:
            handoff_request: Validated handoff request
            
        Returns:
            HandoffResult with execution status
        """
        
        # First validate the handoff
        validation_result = self.validate_handoff(
            handoff_request.from_agent.value,
            handoff_request.to_agent.value,
            handoff_request.artifacts
        )
        
        if validation_result.status != HandoffStatus.VALIDATED:
            validation_result.status = HandoffStatus.FAILED
            return validation_result
        
        try:
            # Mark as active
            self.active_handoffs[handoff_request.request_id] = handoff_request
            
            # Execute handoff logic (placeholder for actual implementation)
            # This would integrate with the actual agent execution system
            
            validation_result.status = HandoffStatus.COMPLETED
            
            # Remove from active handoffs
            self.active_handoffs.pop(handoff_request.request_id, None)
            
            logger.info(f"Handoff executed: {handoff_request.request_id}")
            
        except Exception as e:
            validation_result.status = HandoffStatus.FAILED
            validation_result.validation_errors.append(f"Execution failed: {str(e)}")
            
            logger.error(f"Handoff execution failed: {e}")
        
        return validation_result
    
    def get_valid_handoffs(self, from_agent: str) -> List[Dict[str, Any]]:
        """
        Get all valid handoff targets for a given agent.
        
        Args:
            from_agent: Source agent identifier
            
        Returns:
            List of valid handoff configurations
        """
        
        try:
            from_agent_type = AgentType(from_agent)
        except ValueError:
            return []
        
        valid_handoffs = []
        for (source, target), rule in self.handoff_rules.items():
            if source == from_agent_type:
                valid_handoffs.append({
                    "to_agent": target.value,
                    "required_artifacts": [art.value for art in rule.required_artifacts],
                    "optional_artifacts": [art.value for art in rule.optional_artifacts],
                    "conditions": rule.conditions,
                    "priority": rule.priority
                })
        
        # Sort by priority
        valid_handoffs.sort(key=lambda x: x["priority"])
        
        return valid_handoffs
    
    def get_agent_capabilities(self, agent_type: str) -> Dict[str, Any]:
        """
        Get capabilities for a specific agent type.
        
        Args:
            agent_type: Agent type identifier
            
        Returns:
            Dictionary of agent capabilities
        """
        
        try:
            agent_enum = AgentType(agent_type)
            capabilities = self.agent_capabilities.get(agent_enum, {})
            
            # Convert enums to strings for JSON serialization
            return {
                "produces": [art.value for art in capabilities.get("produces", [])],
                "consumes": [art.value for art in capabilities.get("consumes", [])],
                "expertise": capabilities.get("expertise", [])
            }
        except ValueError:
            return {}
    
    def suggest_workflow(self, project_artifacts: List[str]) -> List[Dict[str, Any]]:
        """
        Suggest optimal workflow based on available artifacts.
        
        Args:
            project_artifacts: List of artifact IDs in the project
            
        Returns:
            Suggested workflow sequence
        """
        
        # Analyze current artifacts
        artifact_types = []
        for artifact_id in project_artifacts:
            artifact = self.artifact_handler.get_artifact(artifact_id)
            if artifact:
                artifact_types.append(artifact.artifact_type)
        
        workflow_suggestions = []
        
        # Basic workflow patterns
        if ArtifactType.SPEC_DOC in artifact_types:
            if ArtifactType.CODE_PATCH not in artifact_types:
                workflow_suggestions.append({
                    "step": 1,
                    "action": "code_generation",
                    "from_agent": "project_manager",
                    "to_agent": "code_generator",
                    "artifacts_needed": ["SpecDoc"],
                    "expected_output": ["CodePatch", "DesignDoc"]
                })
        
        if ArtifactType.CODE_PATCH in artifact_types:
            if ArtifactType.TEST_PLAN not in artifact_types:
                workflow_suggestions.append({
                    "step": 2,
                    "action": "test_planning",
                    "from_agent": "code_generator",
                    "to_agent": "test_writer",
                    "artifacts_needed": ["CodePatch"],
                    "expected_output": ["TestPlan"]
                })
        
        if ArtifactType.TEST_PLAN in artifact_types:
            workflow_suggestions.append({
                "step": 3,
                "action": "evaluation",
                "from_agent": "test_writer",
                "to_agent": "project_manager",
                "artifacts_needed": ["TestPlan"],
                "expected_output": ["EvalReport"]
            })
        
        return workflow_suggestions
    
    def get_handoff_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about handoff performance and patterns.
        
        Returns:
            Dictionary of handoff metrics
        """
        
        if not self.handoff_history:
            return {"total_handoffs": 0}
        
        total_handoffs = len(self.handoff_history)
        successful_handoffs = sum(1 for h in self.handoff_history 
                                 if h.status == HandoffStatus.COMPLETED)
        failed_handoffs = sum(1 for h in self.handoff_history 
                             if h.status == HandoffStatus.FAILED)
        
        avg_processing_time = sum(h.processing_time for h in self.handoff_history) / total_handoffs
        
        # Most common errors
        all_errors = []
        for h in self.handoff_history:
            all_errors.extend(h.validation_errors)
        
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_handoffs": total_handoffs,
            "successful_handoffs": successful_handoffs,
            "failed_handoffs": failed_handoffs,
            "success_rate": successful_handoffs / total_handoffs if total_handoffs > 0 else 0,
            "average_processing_time": avg_processing_time,
            "active_handoffs": len(self.active_handoffs),
            "common_errors": common_errors
        }
"""
Core artifact schemas for multi-agent AI development.

Defines structured data types for all artifacts that agents produce and consume,
ensuring type safety and consistent interfaces across the system.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field, validator


class ArtifactType(str, Enum):
    """Types of artifacts that can be produced by agents"""
    SPEC_DOC = "spec_doc"
    DESIGN_DOC = "design_doc" 
    CODE_PATCH = "code_patch"
    TEST_PLAN = "test_plan"
    EVAL_REPORT = "eval_report"
    RUNBOOK = "runbook"


class ArtifactBase(BaseModel):
    """Base class for all artifacts with common metadata"""
    
    artifact_id: str = Field(..., description="Unique identifier for this artifact")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    created_by: str = Field(..., description="Agent that created this artifact")
    version: str = Field(default="1.0.0", description="Semantic version")
    dependencies: List[str] = Field(default_factory=list, description="IDs of artifacts this depends on")
    tags: List[str] = Field(default_factory=list, description="Classification tags")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score")
    
    class Config:
        use_enum_values = True


class SpecDoc(ArtifactBase):
    """Requirements and specifications document"""
    
    artifact_type: Literal[ArtifactType.SPEC_DOC] = Field(default=ArtifactType.SPEC_DOC)
    
    title: str = Field(..., description="Specification title")
    objective: str = Field(..., description="Primary objective or goal")
    requirements: List[Dict[str, Any]] = Field(..., description="Functional requirements")
    non_functional_requirements: List[Dict[str, Any]] = Field(
        default_factory=list, description="Performance, security, etc."
    )
    acceptance_criteria: List[str] = Field(..., description="Success criteria")
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions")
    constraints: List[str] = Field(default_factory=list, description="Technical/business constraints")
    risks: List[Dict[str, Any]] = Field(default_factory=list, description="Identified risks")
    stakeholders: List[str] = Field(default_factory=list, description="Key stakeholders")
    
    @validator('requirements', 'non_functional_requirements', 'risks')
    def validate_structured_items(cls, v):
        """Ensure structured items have required fields"""
        for item in v:
            if not isinstance(item, dict) or 'id' not in item or 'description' not in item:
                raise ValueError("Items must be dicts with 'id' and 'description'")
        return v


class DesignDoc(ArtifactBase):
    """Architecture and design decisions document"""
    
    artifact_type: Literal[ArtifactType.DESIGN_DOC] = Field(default=ArtifactType.DESIGN_DOC)
    
    title: str = Field(..., description="Design document title")
    overview: str = Field(..., description="High-level architecture overview")
    components: List[Dict[str, Any]] = Field(..., description="System components")
    interfaces: List[Dict[str, Any]] = Field(default_factory=list, description="API/interface definitions")
    data_models: List[Dict[str, Any]] = Field(default_factory=list, description="Data structure definitions")
    design_decisions: List[Dict[str, Any]] = Field(..., description="Key architectural decisions")
    trade_offs: List[Dict[str, Any]] = Field(default_factory=list, description="Trade-off analysis")
    diagrams: List[Dict[str, str]] = Field(default_factory=list, description="Architectural diagrams")
    technology_stack: Dict[str, str] = Field(default_factory=dict, description="Tech stack choices")
    
    @validator('components', 'design_decisions')
    def validate_design_items(cls, v):
        """Ensure design items have required structure"""
        required_fields = {'id', 'name', 'description'}
        for item in v:
            if not isinstance(item, dict) or not required_fields.issubset(item.keys()):
                raise ValueError(f"Items must have fields: {required_fields}")
        return v


class CodePatch(ArtifactBase):
    """Code changes with unified diff format"""
    
    artifact_type: Literal[ArtifactType.CODE_PATCH] = Field(default=ArtifactType.CODE_PATCH)
    
    title: str = Field(..., description="Patch title/summary")
    description: str = Field(..., description="Detailed description of changes")
    files_changed: List[Dict[str, Any]] = Field(..., description="Files modified in this patch")
    diff_unified: str = Field(..., description="Unified diff format")
    language: str = Field(..., description="Primary programming language")
    test_instructions: List[str] = Field(default_factory=list, description="How to test changes")
    rollback_plan: str = Field(default="", description="How to rollback if needed")
    breaking_changes: List[str] = Field(default_factory=list, description="Breaking changes")
    
    @validator('files_changed')
    def validate_files(cls, v):
        """Ensure file changes have required structure"""
        required_fields = {'path', 'action', 'lines_added', 'lines_removed'}
        for file_change in v:
            if not isinstance(file_change, dict) or not required_fields.issubset(file_change.keys()):
                raise ValueError(f"File changes must have fields: {required_fields}")
        return v


class TestPlan(ArtifactBase):
    """Testing strategies and test cases"""
    
    artifact_type: Literal[ArtifactType.TEST_PLAN] = Field(default=ArtifactType.TEST_PLAN)
    
    title: str = Field(..., description="Test plan title")
    scope: str = Field(..., description="What is being tested")
    test_strategy: str = Field(..., description="Overall testing approach")
    test_cases: List[Dict[str, Any]] = Field(..., description="Individual test cases")
    test_data: List[Dict[str, Any]] = Field(default_factory=list, description="Test data sets")
    automation_level: str = Field(default="manual", description="Level of test automation")
    tools_required: List[str] = Field(default_factory=list, description="Testing tools needed")
    environment_setup: str = Field(default="", description="Test environment requirements")
    success_criteria: List[str] = Field(..., description="Plan success criteria")
    
    @validator('test_cases')
    def validate_test_cases(cls, v):
        """Ensure test cases have required structure"""
        required_fields = {'id', 'name', 'description', 'steps', 'expected_result'}
        for test_case in v:
            if not isinstance(test_case, dict) or not required_fields.issubset(test_case.keys()):
                raise ValueError(f"Test cases must have fields: {required_fields}")
        return v


class EvalReport(ArtifactBase):
    """Quality assessment and metrics report"""
    
    artifact_type: Literal[ArtifactType.EVAL_REPORT] = Field(default=ArtifactType.EVAL_REPORT)
    
    title: str = Field(..., description="Evaluation report title")
    evaluated_artifact: str = Field(..., description="ID of artifact being evaluated")
    evaluation_criteria: List[Dict[str, Any]] = Field(..., description="Criteria used for evaluation")
    metrics: Dict[str, float] = Field(..., description="Quantitative metrics")
    qualitative_assessment: str = Field(..., description="Qualitative analysis")
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for improvement")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    overall_score: float = Field(..., ge=0.0, le=10.0, description="Overall quality score")
    pass_fail: bool = Field(..., description="Binary pass/fail result")


class Runbook(ArtifactBase):
    """Operational procedures and documentation"""
    
    artifact_type: Literal[ArtifactType.RUNBOOK] = Field(default=ArtifactType.RUNBOOK)
    
    title: str = Field(..., description="Runbook title")
    purpose: str = Field(..., description="What this runbook accomplishes")
    prerequisites: List[str] = Field(default_factory=list, description="Required setup/permissions")
    procedures: List[Dict[str, Any]] = Field(..., description="Step-by-step procedures")
    troubleshooting: List[Dict[str, Any]] = Field(default_factory=list, description="Common issues & fixes")
    monitoring: List[Dict[str, str]] = Field(default_factory=list, description="What to monitor")
    escalation_paths: List[str] = Field(default_factory=list, description="Who to contact for help")
    maintenance_schedule: str = Field(default="", description="Regular maintenance tasks")
    
    @validator('procedures')
    def validate_procedures(cls, v):
        """Ensure procedures have required structure"""
        required_fields = {'id', 'name', 'steps'}
        for procedure in v:
            if not isinstance(procedure, dict) or not required_fields.issubset(procedure.keys()):
                raise ValueError(f"Procedures must have fields: {required_fields}")
            if not isinstance(procedure['steps'], list):
                raise ValueError("Procedure steps must be a list")
        return v


# Example instances for testing and documentation
EXAMPLE_SPEC_DOC = SpecDoc(
    artifact_id="spec-001",
    created_by="claude-agent",
    title="E-commerce Product Catalog API",
    objective="Build REST API for managing product inventory and search",
    requirements=[
        {
            "id": "REQ-001",
            "description": "API must support CRUD operations for products",
            "priority": "high"
        },
        {
            "id": "REQ-002", 
            "description": "Search functionality with filters and sorting",
            "priority": "medium"
        }
    ],
    acceptance_criteria=[
        "All endpoints respond within 200ms",
        "API documentation is auto-generated",
        "100% test coverage for critical paths"
    ],
    assumptions=["PostgreSQL database available", "Redis for caching"]
)

EXAMPLE_DESIGN_DOC = DesignDoc(
    artifact_id="design-001",
    created_by="gpt4-agent",
    dependencies=["spec-001"],
    title="Product Catalog API Architecture",
    overview="Microservice architecture with event-driven updates",
    components=[
        {
            "id": "comp-001",
            "name": "API Gateway",
            "description": "Request routing and authentication",
            "technology": "FastAPI"
        }
    ],
    design_decisions=[
        {
            "id": "decision-001",
            "name": "Database Choice",
            "description": "PostgreSQL for ACID compliance and complex queries",
            "alternatives": ["MongoDB", "MySQL"],
            "rationale": "Strong consistency required for inventory"
        }
    ]
)
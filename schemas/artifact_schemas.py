"""
Enhanced artifact schema definitions with strict typing and validation.

This module provides complete schema definitions for all artifact types
with comprehensive validation rules and type safety.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field, validator


class ArtifactType(str, Enum):
    """Types of artifacts that can be produced by agents"""
    SPEC_DOC = "SpecDoc"
    DESIGN_DOC = "DesignDoc" 
    CODE_PATCH = "CodePatch"
    TEST_PLAN = "TestPlan"
    EVAL_REPORT = "EvalReport"
    RUNBOOK = "Runbook"


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


class SpecDocSchema(ArtifactBase):
    """Enhanced requirements and specifications document schema"""
    
    artifact_type: Literal[ArtifactType.SPEC_DOC] = ArtifactType.SPEC_DOC
    
    # Core specification elements
    title: str = Field(..., min_length=5, max_length=200, description="Specification title")
    objective: str = Field(..., min_length=20, description="Primary objective or goal")
    scope: str = Field(..., min_length=10, description="Project scope definition")
    
    # Requirements structure
    functional_requirements: List[Dict[str, Any]] = Field(
        default_factory=list, description="Functional requirements with structured format"
    )
    non_functional_requirements: List[Dict[str, Any]] = Field(
        default_factory=list, description="Performance, security, scalability requirements"
    )
    
    # Quality gates
    acceptance_criteria: List[str] = Field(
        default_factory=list, description="Measurable success criteria"
    )
    success_metrics: List[Dict[str, Any]] = Field(
        default_factory=list, description="Quantifiable success metrics"
    )
    
    # Risk and constraint analysis
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions")
    constraints: List[Dict[str, Any]] = Field(
        default_factory=list, description="Technical and business constraints"
    )
    risks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Identified risks with mitigation"
    )
    
    # Stakeholder information
    stakeholders: List[Dict[str, str]] = Field(
        default_factory=list, description="Stakeholders with roles"
    )
    
    # Impact analysis
    business_value: str = Field(default="", description="Expected business value")
    technical_complexity: str = Field(
        default="medium", description="Estimated technical complexity"
    )
    
    @validator('functional_requirements', 'non_functional_requirements')
    def validate_requirements(cls, v):
        """Validate requirement structure"""
        required_fields = {'id', 'title', 'description', 'priority'}
        for req in v:
            if not isinstance(req, dict):
                raise ValueError("Requirements must be dictionaries")
            if not required_fields.issubset(req.keys()):
                raise ValueError(f"Requirements must have fields: {required_fields}")
            if req.get('priority') not in ['low', 'medium', 'high', 'critical']:
                raise ValueError("Priority must be: low, medium, high, or critical")
        return v
    
    @validator('risks')
    def validate_risks(cls, v):
        """Validate risk structure"""
        required_fields = {'id', 'description', 'probability', 'impact', 'mitigation'}
        for risk in v:
            if not isinstance(risk, dict):
                raise ValueError("Risks must be dictionaries")
            if not required_fields.issubset(risk.keys()):
                raise ValueError(f"Risks must have fields: {required_fields}")
        return v


class DesignDocSchema(ArtifactBase):
    """Enhanced architecture and design decisions document schema"""
    
    artifact_type: Literal[ArtifactType.DESIGN_DOC] = ArtifactType.DESIGN_DOC
    
    # Design overview
    title: str = Field(..., min_length=5, max_length=200, description="Design document title")
    overview: str = Field(..., min_length=50, description="High-level architecture overview")
    design_goals: List[str] = Field(default_factory=list, description="Key design objectives")
    
    # Architecture elements
    system_architecture: Dict[str, Any] = Field(
        ..., description="Overall system architecture description"
    )
    components: List[Dict[str, Any]] = Field(
        default_factory=list, description="System components with interfaces"
    )
    data_flow: List[Dict[str, Any]] = Field(
        default_factory=list, description="Data flow between components"
    )
    
    # Technical specifications
    interfaces: List[Dict[str, Any]] = Field(
        default_factory=list, description="API and interface definitions"
    )
    data_models: List[Dict[str, Any]] = Field(
        default_factory=list, description="Data structure and schema definitions"
    )
    security_model: Dict[str, Any] = Field(
        default_factory=dict, description="Security architecture and considerations"
    )
    
    # Decision documentation
    design_decisions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Architectural decisions with rationale"
    )
    alternatives_considered: List[Dict[str, Any]] = Field(
        default_factory=list, description="Alternative approaches considered"
    )
    trade_offs: List[Dict[str, Any]] = Field(
        default_factory=list, description="Trade-off analysis and reasoning"
    )
    
    # Implementation guidance
    technology_stack: Dict[str, str] = Field(
        ..., description="Technology choices with justification"
    )
    deployment_architecture: Dict[str, Any] = Field(
        default_factory=dict, description="Deployment and infrastructure design"
    )
    scalability_considerations: List[str] = Field(
        default_factory=list, description="Scalability design considerations"
    )
    
    # Documentation assets
    diagrams: List[Dict[str, str]] = Field(
        default_factory=list, description="Architectural diagrams and visualizations"
    )
    
    @validator('components')
    def validate_components(cls, v):
        """Validate component structure"""
        required_fields = {'id', 'name', 'description', 'responsibilities', 'interfaces'}
        for component in v:
            if not isinstance(component, dict):
                raise ValueError("Components must be dictionaries")
            if not required_fields.issubset(component.keys()):
                raise ValueError(f"Components must have fields: {required_fields}")
        return v
    
    @validator('design_decisions')
    def validate_design_decisions(cls, v):
        """Validate design decision structure"""
        required_fields = {'id', 'title', 'description', 'rationale', 'alternatives', 'decision'}
        for decision in v:
            if not isinstance(decision, dict):
                raise ValueError("Design decisions must be dictionaries")
            if not required_fields.issubset(decision.keys()):
                raise ValueError(f"Design decisions must have fields: {required_fields}")
        return v


class CodePatchSchema(ArtifactBase):
    """Enhanced code changes schema with comprehensive metadata"""
    
    artifact_type: Literal[ArtifactType.CODE_PATCH] = ArtifactType.CODE_PATCH
    
    # Patch identification
    task_id: str = Field(..., description="Associated task or issue ID")
    title: str = Field(..., min_length=5, max_length=200, description="Patch title/summary")
    description: str = Field(..., min_length=20, description="Detailed description of changes")
    
    # Version control integration
    base_commit: str = Field(..., description="Base commit hash or reference")
    target_branch: str = Field(default="main", description="Target branch for merge")
    
    # Change analysis
    files_changed: List[Dict[str, Any]] = Field(
        default_factory=list, description="Files modified in this patch"
    )
    lines_added: int = Field(default=0, ge=0, description="Total lines added")
    lines_removed: int = Field(default=0, ge=0, description="Total lines removed")
    
    # Code content
    diff_unified: str = Field(..., min_length=10, description="Unified diff format")
    language: str = Field(..., description="Primary programming language")
    framework: str = Field(default="", description="Primary framework or library")
    
    # Impact assessment
    impact: List[str] = Field(
        default_factory=list, description="Areas of system impacted by changes"
    )
    breaking_changes: List[str] = Field(
        default_factory=list, description="Breaking changes introduced"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="Dependencies on other patches or artifacts"
    )
    
    # Quality assurance
    tests_requested: List[str] = Field(
        default_factory=list, description="Types of testing requested"
    )
    test_instructions: List[str] = Field(
        default_factory=list, description="How to test the changes"
    )
    rollback_plan: str = Field(default="", description="Plan for rollback if needed")
    
    # Code quality metrics
    complexity_score: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Code complexity assessment"
    )
    maintainability_score: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Code maintainability score"
    )
    
    @validator('files_changed')
    def validate_files_changed(cls, v):
        """Validate file change structure"""
        required_fields = {'path', 'action', 'lines_added', 'lines_removed', 'language'}
        valid_actions = {'added', 'modified', 'deleted', 'renamed'}
        
        for file_change in v:
            if not isinstance(file_change, dict):
                raise ValueError("File changes must be dictionaries")
            if not required_fields.issubset(file_change.keys()):
                raise ValueError(f"File changes must have fields: {required_fields}")
            if file_change.get('action') not in valid_actions:
                raise ValueError(f"Action must be one of: {valid_actions}")
        return v
    
    @validator('impact')
    def validate_impact(cls, v):
        """Validate impact areas"""
        valid_impacts = {
            'api', 'database', 'ui', 'business_logic', 'security', 
            'performance', 'configuration', 'documentation', 'tests'
        }
        for impact in v:
            if impact not in valid_impacts:
                raise ValueError(f"Impact must be one of: {valid_impacts}")
        return v


class TestPlanSchema(ArtifactBase):
    """Enhanced testing strategies and test case schema"""
    
    artifact_type: Literal[ArtifactType.TEST_PLAN] = ArtifactType.TEST_PLAN
    
    # Test plan overview
    title: str = Field(..., min_length=5, max_length=200, description="Test plan title")
    objective: str = Field(..., min_length=20, description="Testing objective")
    scope: str = Field(..., min_length=10, description="What is being tested")
    
    # Testing strategy
    test_strategy: str = Field(..., min_length=20, description="Overall testing approach")
    test_levels: List[str] = Field(
        default_factory=list, description="Levels of testing (unit, integration, system, etc.)"
    )
    test_types: List[str] = Field(
        default_factory=list, description="Types of testing (functional, performance, security, etc.)"
    )
    
    # Test cases and scenarios
    test_cases: List[Dict[str, Any]] = Field(
        default_factory=list, description="Individual test cases with detailed steps"
    )
    test_scenarios: List[Dict[str, Any]] = Field(
        default_factory=list, description="High-level test scenarios"
    )
    edge_cases: List[Dict[str, Any]] = Field(
        default_factory=list, description="Edge case testing scenarios"
    )
    
    # Test data and environment
    test_data_requirements: List[Dict[str, Any]] = Field(
        default_factory=list, description="Test data specifications"
    )
    environment_requirements: Dict[str, Any] = Field(
        default_factory=dict, description="Test environment specifications"
    )
    
    # Automation and tools
    automation_level: str = Field(
        default="manual", description="Level of test automation"
    )
    automation_framework: str = Field(
        default="", description="Testing framework for automation"
    )
    tools_required: List[str] = Field(
        default_factory=list, description="Testing tools and utilities needed"
    )
    
    # Execution planning
    execution_sequence: List[str] = Field(
        default_factory=list, description="Order of test execution"
    )
    entry_criteria: List[str] = Field(
        default_factory=list, description="Criteria for starting testing"
    )
    exit_criteria: List[str] = Field(
        default_factory=list, description="Criteria for completing testing"
    )
    
    # Quality gates
    success_criteria: List[str] = Field(
        default_factory=list, description="Plan success criteria"
    )
    acceptance_thresholds: Dict[str, float] = Field(
        default_factory=dict, description="Quality thresholds for acceptance"
    )
    
    # Risk and mitigation
    testing_risks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Risks in testing approach"
    )
    
    @validator('test_cases')
    def validate_test_cases(cls, v):
        """Validate test case structure"""
        required_fields = {
            'id', 'title', 'description', 'prerequisites', 
            'steps', 'expected_result', 'priority', 'category'
        }
        valid_priorities = {'low', 'medium', 'high', 'critical'}
        
        for test_case in v:
            if not isinstance(test_case, dict):
                raise ValueError("Test cases must be dictionaries")
            if not required_fields.issubset(test_case.keys()):
                raise ValueError(f"Test cases must have fields: {required_fields}")
            if test_case.get('priority') not in valid_priorities:
                raise ValueError(f"Priority must be one of: {valid_priorities}")
        return v
    
    @validator('test_levels', 'test_types', each_item=True)
    def validate_test_classifications(cls, v):
        """Validate test level and type classifications"""
        valid_levels = {'unit', 'integration', 'system', 'acceptance', 'regression'}
        valid_types = {
            'functional', 'performance', 'security', 'usability', 
            'compatibility', 'reliability', 'scalability'
        }
        
        if v in valid_levels or v in valid_types:
            return v
        else:
            raise ValueError(f"Invalid test classification: {v}")
        
        return v


class EvalReportSchema(ArtifactBase):
    """Enhanced quality assessment and metrics report schema"""
    
    artifact_type: Literal[ArtifactType.EVAL_REPORT] = ArtifactType.EVAL_REPORT
    
    # Report identification
    title: str = Field(..., min_length=5, max_length=200, description="Evaluation report title")
    evaluation_type: str = Field(..., description="Type of evaluation performed")
    evaluated_artifact: str = Field(..., description="ID of artifact being evaluated")
    evaluation_scope: str = Field(..., description="Scope of the evaluation")
    
    # Evaluation framework
    methodology: str = Field(..., min_length=20, description="Evaluation methodology used")
    evaluation_criteria: List[Dict[str, Any]] = Field(
        default_factory=list, description="Criteria used for evaluation"
    )
    evaluation_framework: str = Field(default="", description="Framework or standard used")
    
    # Quantitative metrics
    metrics: Dict[str, float] = Field(
        ..., description="Quantitative metrics and measurements"
    )
    benchmarks: Dict[str, float] = Field(
        default_factory=dict, description="Benchmark values for comparison"
    )
    performance_indicators: List[Dict[str, Any]] = Field(
        default_factory=list, description="Key performance indicators"
    )
    
    # Qualitative assessment
    qualitative_assessment: str = Field(
        ..., min_length=50, description="Detailed qualitative analysis"
    )
    strengths: List[str] = Field(
        default_factory=list, description="Identified strengths and positive aspects"
    )
    weaknesses: List[str] = Field(
        default_factory=list, description="Areas for improvement and weaknesses"
    )
    opportunities: List[str] = Field(
        default_factory=list, description="Improvement opportunities identified"
    )
    
    # Recommendations and actions
    recommendations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Detailed improvement recommendations"
    )
    action_items: List[Dict[str, Any]] = Field(
        default_factory=list, description="Specific action items for improvement"
    )
    
    # Overall assessment
    overall_score: float = Field(
        ..., ge=0.0, le=10.0, description="Overall quality score (0-10)"
    )
    grade: str = Field(..., description="Letter grade or classification")
    pass_fail: bool = Field(..., description="Binary pass/fail result")
    confidence_level: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence in evaluation results"
    )
    
    # Context and limitations
    evaluation_context: str = Field(
        default="", description="Context and constraints of evaluation"
    )
    limitations: List[str] = Field(
        default_factory=list, description="Limitations of the evaluation"
    )
    
    @validator('evaluation_criteria')
    def validate_evaluation_criteria(cls, v):
        """Validate evaluation criteria structure"""
        required_fields = {'id', 'name', 'description', 'weight', 'measurement_method'}
        
        total_weight = 0
        for criteria in v:
            if not isinstance(criteria, dict):
                raise ValueError("Evaluation criteria must be dictionaries")
            if not required_fields.issubset(criteria.keys()):
                raise ValueError(f"Criteria must have fields: {required_fields}")
            
            weight = criteria.get('weight', 0)
            if not isinstance(weight, (int, float)) or weight <= 0:
                raise ValueError("Weight must be a positive number")
            total_weight += weight
        
        # Allow some flexibility in total weight (should be around 1.0 or 100)
        if not (0.95 <= total_weight <= 1.05 or 95 <= total_weight <= 105):
            raise ValueError("Total weight of criteria should sum to 1.0 or 100")
        
        return v
    
    @validator('recommendations', 'action_items')
    def validate_recommendations_and_actions(cls, v):
        """Validate recommendations and action items structure"""
        required_fields = {'id', 'title', 'description', 'priority'}
        valid_priorities = {'low', 'medium', 'high', 'critical'}
        
        for item in v:
            if not isinstance(item, dict):
                raise ValueError("Items must be dictionaries")
            if not required_fields.issubset(item.keys()):
                raise ValueError(f"Items must have fields: {required_fields}")
            if item.get('priority') not in valid_priorities:
                raise ValueError(f"Priority must be one of: {valid_priorities}")
        
        return v


class RunbookSchema(ArtifactBase):
    """Enhanced operational procedures and documentation schema"""
    
    artifact_type: Literal[ArtifactType.RUNBOOK] = ArtifactType.RUNBOOK
    
    # Runbook identification
    title: str = Field(..., min_length=5, max_length=200, description="Runbook title")
    purpose: str = Field(..., min_length=20, description="What this runbook accomplishes")
    scope: str = Field(..., description="Scope and applicability of procedures")
    
    # Prerequisites and setup
    prerequisites: List[str] = Field(
        default_factory=list, description="Required setup, permissions, and dependencies"
    )
    required_tools: List[Dict[str, str]] = Field(
        default_factory=list, description="Tools and software required"
    )
    required_access: List[Dict[str, str]] = Field(
        default_factory=list, description="Required access permissions and credentials"
    )
    
    # Operational procedures
    procedures: List[Dict[str, Any]] = Field(
        default_factory=list, description="Step-by-step operational procedures"
    )
    emergency_procedures: List[Dict[str, Any]] = Field(
        default_factory=list, description="Emergency response procedures"
    )
    recovery_procedures: List[Dict[str, Any]] = Field(
        default_factory=list, description="System recovery procedures"
    )
    
    # Troubleshooting and support
    troubleshooting: List[Dict[str, Any]] = Field(
        default_factory=list, description="Common issues and resolution steps"
    )
    known_issues: List[Dict[str, Any]] = Field(
        default_factory=list, description="Known issues and workarounds"
    )
    escalation_paths: List[Dict[str, str]] = Field(
        default_factory=list, description="Escalation contacts and procedures"
    )
    
    # Monitoring and maintenance
    monitoring_guidelines: List[Dict[str, Any]] = Field(
        default_factory=list, description="What to monitor and alert thresholds"
    )
    maintenance_schedule: Dict[str, Any] = Field(
        default_factory=dict, description="Regular maintenance tasks and schedules"
    )
    health_checks: List[Dict[str, Any]] = Field(
        default_factory=list, description="System health check procedures"
    )
    
    # Documentation and references
    related_documents: List[Dict[str, str]] = Field(
        default_factory=list, description="Related documentation and references"
    )
    version_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="Change history and version information"
    )
    
    # Validation and testing
    validation_steps: List[Dict[str, Any]] = Field(
        default_factory=list, description="Steps to validate procedure execution"
    )
    testing_frequency: str = Field(
        default="quarterly", description="How often procedures should be tested"
    )
    
    @validator('procedures', 'emergency_procedures', 'recovery_procedures')
    def validate_procedures(cls, v):
        """Validate procedure structure"""
        required_fields = {'id', 'name', 'description', 'steps', 'expected_outcome'}
        
        for procedure in v:
            if not isinstance(procedure, dict):
                raise ValueError("Procedures must be dictionaries")
            if not required_fields.issubset(procedure.keys()):
                raise ValueError(f"Procedures must have fields: {required_fields}")
            
            # Validate steps structure
            steps = procedure.get('steps', [])
            if not isinstance(steps, list) or len(steps) == 0:
                raise ValueError("Procedures must have at least one step")
            
            for step in steps:
                if not isinstance(step, dict) or 'description' not in step:
                    raise ValueError("Each step must be a dict with 'description'")
        
        return v
    
    @validator('troubleshooting')
    def validate_troubleshooting(cls, v):
        """Validate troubleshooting structure"""
        required_fields = {'id', 'issue', 'symptoms', 'resolution_steps', 'prevention'}
        
        for trouble_item in v:
            if not isinstance(trouble_item, dict):
                raise ValueError("Troubleshooting items must be dictionaries")
            if not required_fields.issubset(trouble_item.keys()):
                raise ValueError(f"Troubleshooting must have fields: {required_fields}")
        
        return v
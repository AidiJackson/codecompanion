"""
Artifact validation and handling system for multi-agent workflows.

Provides comprehensive validation, serialization, and management of artifacts
produced and consumed by agents in the system.
"""

from typing import Dict, List, Optional, Any, Type, Union
from pydantic import BaseModel, Field, ValidationError
import json
import logging
from datetime import datetime

from schemas.artifacts import (
    ArtifactBase, ArtifactType, SpecDoc, DesignDoc, CodePatch,
    TestPlan, EvalReport, Runbook
)


logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Result of artifact validation"""
    
    is_valid: bool = Field(..., description="Whether artifact is valid")
    artifact_id: str = Field(..., description="ID of validated artifact")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    
    # Validation details
    validation_timestamp: datetime = Field(default_factory=datetime.now, description="Validation timestamp")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    # Quality metrics
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Completeness score")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    
    # Metadata
    validated_by: str = Field(..., description="Validator identifier")
    validation_rules_applied: List[str] = Field(default_factory=list, description="Rules applied during validation")


class ArtifactValidator:
    """
    Comprehensive artifact validator with type-specific validation rules.
    
    Provides:
    - Schema validation using Pydantic models
    - Business rule validation
    - Quality scoring
    - Cross-artifact dependency validation
    """
    
    def __init__(self):
        self.artifact_types = {
            ArtifactType.SPEC_DOC: SpecDoc,
            ArtifactType.DESIGN_DOC: DesignDoc,
            ArtifactType.CODE_PATCH: CodePatch,
            ArtifactType.TEST_PLAN: TestPlan,
            ArtifactType.EVAL_REPORT: EvalReport,
            ArtifactType.RUNBOOK: Runbook
        }
        
        # Quality rules for each artifact type
        self.quality_rules = {
            ArtifactType.SPEC_DOC: self._validate_spec_doc_quality,
            ArtifactType.DESIGN_DOC: self._validate_design_doc_quality,
            ArtifactType.CODE_PATCH: self._validate_code_patch_quality,
            ArtifactType.TEST_PLAN: self._validate_test_plan_quality,
            ArtifactType.EVAL_REPORT: self._validate_eval_report_quality,
            ArtifactType.RUNBOOK: self._validate_runbook_quality
        }
    
    def validate_artifact(self, artifact_data: Dict[str, Any], 
                         validator_id: str = "system") -> ValidationResult:
        """Validate artifact data and return comprehensive validation result"""
        
        errors = []
        warnings = []
        
        try:
            # Extract artifact type
            artifact_type = ArtifactType(artifact_data.get("artifact_type"))
            artifact_id = artifact_data.get("artifact_id", "unknown")
            
        except (ValueError, TypeError) as e:
            return ValidationResult(
                is_valid=False,
                artifact_id=artifact_data.get("artifact_id", "unknown"),
                artifact_type=ArtifactType.SPEC_DOC,  # Default
                validation_errors=[f"Invalid artifact type: {e}"],
                completeness_score=0.0,
                quality_score=0.0,
                validated_by=validator_id
            )
        
        # Schema validation
        artifact_class = self.artifact_types.get(artifact_type)
        if not artifact_class:
            errors.append(f"Unknown artifact type: {artifact_type}")
            return ValidationResult(
                is_valid=False,
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                validation_errors=errors,
                completeness_score=0.0,
                quality_score=0.0,
                validated_by=validator_id
            )
        
        try:
            # Validate against Pydantic schema
            artifact = artifact_class(**artifact_data)
            
        except ValidationError as e:
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                errors.append(f"{field_path}: {error['msg']}")
            
            return ValidationResult(
                is_valid=False,
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                validation_errors=errors,
                completeness_score=0.0,
                quality_score=0.0,
                validated_by=validator_id
            )
        
        # Quality validation
        quality_validator = self.quality_rules.get(artifact_type)
        if quality_validator:
            quality_result = quality_validator(artifact)
            errors.extend(quality_result.get("errors", []))
            warnings.extend(quality_result.get("warnings", []))
            completeness_score = quality_result.get("completeness_score", 1.0)
            quality_score = quality_result.get("quality_score", 1.0)
        else:
            completeness_score = 1.0
            quality_score = 1.0
        
        # Overall validation result
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            validation_errors=errors,
            validation_warnings=warnings,
            completeness_score=completeness_score,
            quality_score=quality_score,
            validated_by=validator_id,
            validation_rules_applied=[f"{artifact_type.value}_schema", f"{artifact_type.value}_quality"]
        )
    
    def _validate_spec_doc_quality(self, spec: SpecDoc) -> Dict[str, Any]:
        """Validate SpecDoc quality"""
        errors = []
        warnings = []
        
        # Check completeness
        completeness_factors = []
        
        # Requirements completeness
        if not spec.requirements:
            errors.append("No functional requirements specified")
            completeness_factors.append(0.0)
        else:
            req_quality = sum(1 for req in spec.requirements 
                            if len(req.get("description", "")) > 20) / len(spec.requirements)
            completeness_factors.append(req_quality)
        
        # Acceptance criteria
        if not spec.acceptance_criteria:
            errors.append("No acceptance criteria specified")
            completeness_factors.append(0.0)
        else:
            criteria_quality = sum(1 for criteria in spec.acceptance_criteria 
                                 if len(criteria) > 10) / len(spec.acceptance_criteria)
            completeness_factors.append(criteria_quality)
        
        # Risk assessment
        if not spec.risks:
            warnings.append("No risks identified - consider risk analysis")
            completeness_factors.append(0.5)  # Partial score for missing risks
        else:
            completeness_factors.append(1.0)
        
        # Quality scoring
        completeness_score = sum(completeness_factors) / len(completeness_factors)
        
        # Quality factors
        quality_factors = []
        
        # Objective clarity
        objective_quality = min(1.0, len(spec.objective) / 100)  # Good objectives are descriptive
        quality_factors.append(objective_quality)
        
        # Requirements detail
        if spec.requirements:
            avg_req_length = sum(len(req.get("description", "")) for req in spec.requirements) / len(spec.requirements)
            req_detail_quality = min(1.0, avg_req_length / 50)
            quality_factors.append(req_detail_quality)
        
        quality_score = sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
        
        return {
            "errors": errors,
            "warnings": warnings,
            "completeness_score": completeness_score,
            "quality_score": quality_score
        }
    
    def _validate_design_doc_quality(self, design: DesignDoc) -> Dict[str, Any]:
        """Validate DesignDoc quality"""
        errors = []
        warnings = []
        
        # Check completeness
        completeness_factors = []
        
        # Components completeness
        if not design.components:
            errors.append("No system components defined")
            completeness_factors.append(0.0)
        else:
            component_quality = sum(1 for comp in design.components 
                                  if all(key in comp for key in ["id", "name", "description"])) / len(design.components)
            completeness_factors.append(component_quality)
        
        # Design decisions
        if not design.design_decisions:
            errors.append("No design decisions documented")
            completeness_factors.append(0.0)
        else:
            decision_quality = sum(1 for decision in design.design_decisions
                                 if "rationale" in decision) / len(design.design_decisions)
            completeness_factors.append(decision_quality)
            
        # Technology stack
        if not design.technology_stack:
            warnings.append("Technology stack not specified")
            completeness_factors.append(0.7)
        else:
            completeness_factors.append(1.0)
        
        completeness_score = sum(completeness_factors) / len(completeness_factors)
        
        # Quality assessment
        quality_factors = []
        
        # Overview quality
        overview_quality = min(1.0, len(design.overview) / 200)
        quality_factors.append(overview_quality)
        
        # Design decision depth
        if design.design_decisions:
            decisions_with_rationale = sum(1 for decision in design.design_decisions 
                                         if decision.get("rationale", ""))
            decision_quality = decisions_with_rationale / len(design.design_decisions)
            quality_factors.append(decision_quality)
        
        quality_score = sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
        
        return {
            "errors": errors,
            "warnings": warnings,
            "completeness_score": completeness_score,
            "quality_score": quality_score
        }
    
    def _validate_code_patch_quality(self, patch: CodePatch) -> Dict[str, Any]:
        """Validate CodePatch quality"""
        errors = []
        warnings = []
        
        # Check required elements
        completeness_factors = []
        
        # Files changed
        if not patch.files_changed:
            errors.append("No files specified in patch")
            completeness_factors.append(0.0)
        else:
            completeness_factors.append(1.0)
        
        # Diff format
        if not patch.diff_unified:
            errors.append("No unified diff provided")
            completeness_factors.append(0.0)
        else:
            # Check if diff looks valid
            if not any(line.startswith(('+', '-', '@@')) for line in patch.diff_unified.split('\n')):
                warnings.append("Diff format may be invalid")
                completeness_factors.append(0.7)
            else:
                completeness_factors.append(1.0)
        
        # Test instructions
        if not patch.test_instructions:
            warnings.append("No test instructions provided")
            completeness_factors.append(0.8)
        else:
            completeness_factors.append(1.0)
        
        completeness_score = sum(completeness_factors) / len(completeness_factors)
        
        # Quality factors
        quality_factors = []
        
        # Description quality
        desc_quality = min(1.0, len(patch.description) / 100)
        quality_factors.append(desc_quality)
        
        # Breaking changes awareness
        if patch.breaking_changes:
            quality_factors.append(1.0)  # Good - documented breaking changes
        else:
            quality_factors.append(0.8)  # Neutral - no breaking changes or not documented
        
        quality_score = sum(quality_factors) / len(quality_factors)
        
        return {
            "errors": errors,
            "warnings": warnings,
            "completeness_score": completeness_score,
            "quality_score": quality_score
        }
    
    def _validate_test_plan_quality(self, test_plan: TestPlan) -> Dict[str, Any]:
        """Validate TestPlan quality"""
        errors = []
        warnings = []
        
        # Completeness checks
        completeness_factors = []
        
        # Test cases
        if not test_plan.test_cases:
            errors.append("No test cases defined")
            completeness_factors.append(0.0)
        else:
            required_fields = {"id", "name", "description", "steps", "expected_result"}
            complete_test_cases = sum(1 for tc in test_plan.test_cases 
                                    if required_fields.issubset(tc.keys()))
            case_completeness = complete_test_cases / len(test_plan.test_cases)
            completeness_factors.append(case_completeness)
        
        # Success criteria
        if not test_plan.success_criteria:
            errors.append("No success criteria defined")
            completeness_factors.append(0.0)
        else:
            completeness_factors.append(1.0)
        
        # Test strategy
        if len(test_plan.test_strategy) < 50:
            warnings.append("Test strategy description is brief")
            completeness_factors.append(0.8)
        else:
            completeness_factors.append(1.0)
        
        completeness_score = sum(completeness_factors) / len(completeness_factors)
        
        # Quality assessment
        quality_factors = []
        
        # Test case quality
        if test_plan.test_cases:
            detailed_cases = sum(1 for tc in test_plan.test_cases 
                               if isinstance(tc.get("steps"), list) and len(tc.get("steps", [])) > 1)
            case_quality = detailed_cases / len(test_plan.test_cases)
            quality_factors.append(case_quality)
        
        # Automation consideration
        automation_score = 1.0 if test_plan.automation_level != "manual" else 0.7
        quality_factors.append(automation_score)
        
        quality_score = sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
        
        return {
            "errors": errors,
            "warnings": warnings,
            "completeness_score": completeness_score,
            "quality_score": quality_score
        }
    
    def _validate_eval_report_quality(self, report: EvalReport) -> Dict[str, Any]:
        """Validate EvalReport quality"""
        errors = []
        warnings = []
        
        # Completeness checks
        completeness_factors = []
        
        # Evaluation criteria
        if not report.evaluation_criteria:
            errors.append("No evaluation criteria specified")
            completeness_factors.append(0.0)
        else:
            completeness_factors.append(1.0)
        
        # Metrics
        if not report.metrics:
            errors.append("No quantitative metrics provided")
            completeness_factors.append(0.0)
        else:
            completeness_factors.append(1.0)
        
        # Qualitative assessment
        if len(report.qualitative_assessment) < 100:
            warnings.append("Qualitative assessment is brief")
            completeness_factors.append(0.8)
        else:
            completeness_factors.append(1.0)
        
        completeness_score = sum(completeness_factors) / len(completeness_factors)
        
        # Quality factors
        quality_factors = []
        
        # Recommendations quality
        if not report.recommendations:
            warnings.append("No improvement recommendations provided")
            quality_factors.append(0.7)
        else:
            quality_factors.append(1.0)
        
        # Score consistency
        if 0 <= report.overall_score <= 10:
            quality_factors.append(1.0)
        else:
            errors.append("Overall score out of valid range (0-10)")
            quality_factors.append(0.0)
        
        quality_score = sum(quality_factors) / len(quality_factors)
        
        return {
            "errors": errors,
            "warnings": warnings,
            "completeness_score": completeness_score,
            "quality_score": quality_score
        }
    
    def _validate_runbook_quality(self, runbook: Runbook) -> Dict[str, Any]:
        """Validate Runbook quality"""
        errors = []
        warnings = []
        
        # Completeness checks
        completeness_factors = []
        
        # Procedures
        if not runbook.procedures:
            errors.append("No procedures defined")
            completeness_factors.append(0.0)
        else:
            complete_procedures = sum(1 for proc in runbook.procedures
                                    if all(key in proc for key in ["id", "name", "steps"]))
            proc_completeness = complete_procedures / len(runbook.procedures)
            completeness_factors.append(proc_completeness)
        
        # Prerequisites
        if not runbook.prerequisites:
            warnings.append("No prerequisites specified")
            completeness_factors.append(0.8)
        else:
            completeness_factors.append(1.0)
        
        # Purpose clarity
        if len(runbook.purpose) < 50:
            warnings.append("Purpose description is brief")
            completeness_factors.append(0.8)
        else:
            completeness_factors.append(1.0)
        
        completeness_score = sum(completeness_factors) / len(completeness_factors)
        
        # Quality factors
        quality_factors = []
        
        # Procedure detail
        if runbook.procedures:
            detailed_procedures = sum(1 for proc in runbook.procedures
                                    if isinstance(proc.get("steps"), list) and len(proc.get("steps", [])) > 2)
            proc_quality = detailed_procedures / len(runbook.procedures)
            quality_factors.append(proc_quality)
        
        # Troubleshooting guidance
        troubleshooting_score = 1.0 if runbook.troubleshooting else 0.6
        quality_factors.append(troubleshooting_score)
        
        quality_score = sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
        
        return {
            "errors": errors,
            "warnings": warnings,
            "completeness_score": completeness_score,
            "quality_score": quality_score
        }


class ArtifactHandler:
    """
    Artifact handler for serialization, storage, and retrieval.
    
    Provides centralized management of artifacts with:
    - Type-safe serialization/deserialization
    - Dependency tracking
    - Version management
    - Storage abstraction
    """
    
    def __init__(self):
        self.validator = ArtifactValidator()
        self.artifact_store: Dict[str, Dict[str, Any]] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        
    def store_artifact(self, artifact_data: Dict[str, Any], 
                      validate: bool = True) -> ValidationResult:
        """Store artifact with optional validation"""
        
        # Validate if requested
        if validate:
            validation_result = self.validator.validate_artifact(artifact_data)
            if not validation_result.is_valid:
                logger.error(f"Artifact validation failed: {validation_result.validation_errors}")
                return validation_result
        else:
            validation_result = ValidationResult(
                is_valid=True,
                artifact_id=artifact_data.get("artifact_id", "unknown"),
                artifact_type=ArtifactType(artifact_data.get("artifact_type")),
                completeness_score=1.0,
                quality_score=1.0,
                validated_by="handler"
            )
        
        # Store artifact
        artifact_id = artifact_data["artifact_id"]
        self.artifact_store[artifact_id] = artifact_data.copy()
        
        # Update dependency graph
        dependencies = artifact_data.get("dependencies", [])
        if dependencies:
            self.dependency_graph[artifact_id] = dependencies
        
        logger.info(f"Stored artifact {artifact_id} of type {artifact_data.get('artifact_type')}")
        return validation_result
    
    def retrieve_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve artifact by ID"""
        return self.artifact_store.get(artifact_id)
    
    def list_artifacts_by_type(self, artifact_type: ArtifactType) -> List[Dict[str, Any]]:
        """List all artifacts of specific type"""
        return [
            artifact for artifact in self.artifact_store.values()
            if artifact.get("artifact_type") == artifact_type.value
        ]
    
    def get_dependencies(self, artifact_id: str) -> List[str]:
        """Get dependencies for an artifact"""
        return self.dependency_graph.get(artifact_id, [])
    
    def get_dependents(self, artifact_id: str) -> List[str]:
        """Get artifacts that depend on this artifact"""
        dependents = []
        for dependent_id, dependencies in self.dependency_graph.items():
            if artifact_id in dependencies:
                dependents.append(dependent_id)
        return dependents
    
    def validate_dependencies(self, artifact_id: str) -> Dict[str, bool]:
        """Check if all dependencies exist"""
        dependencies = self.get_dependencies(artifact_id)
        return {
            dep_id: dep_id in self.artifact_store
            for dep_id in dependencies
        }
    
    def get_artifact_stats(self) -> Dict[str, Any]:
        """Get statistics about stored artifacts"""
        
        type_counts = {}
        for artifact in self.artifact_store.values():
            artifact_type = artifact.get("artifact_type", "unknown")
            type_counts[artifact_type] = type_counts.get(artifact_type, 0) + 1
        
        return {
            "total_artifacts": len(self.artifact_store),
            "type_distribution": type_counts,
            "dependency_edges": sum(len(deps) for deps in self.dependency_graph.values()),
            "artifacts_with_dependencies": len(self.dependency_graph),
            "orphaned_artifacts": len([
                artifact_id for artifact_id in self.artifact_store.keys()
                if artifact_id not in self.dependency_graph and not self.get_dependents(artifact_id)
            ])
        }
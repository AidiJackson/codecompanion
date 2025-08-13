"""
Enhanced Typed Artifact Handler with strict schema enforcement and lineage tracking.

This module provides comprehensive artifact management with confidence scoring,
semantic validation, and structured handoff protocols between agents.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
from pydantic import BaseModel, Field, ValidationError

from schemas.artifact_schemas import (
    ArtifactBase,
    SpecDocSchema,
    DesignDocSchema,
    CodePatchSchema,
    TestPlanSchema,
    EvalReportSchema,
    RunbookSchema,
)
from core.artifacts import ArtifactValidator, ValidationResult


logger = logging.getLogger(__name__)


class ArtifactLineage(BaseModel):
    """Tracks the lineage and evolution of artifacts"""

    artifact_id: str = Field(..., description="Artifact identifier")
    parent_artifacts: List[str] = Field(
        default_factory=list, description="Parent artifact IDs"
    )
    child_artifacts: List[str] = Field(
        default_factory=list, description="Child artifact IDs"
    )
    creation_agent: str = Field(..., description="Agent that created this artifact")
    modification_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="History of modifications"
    )
    semantic_hash: str = Field(
        ..., description="Hash of semantic content for change detection"
    )
    version_chain: List[str] = Field(
        default_factory=list, description="Version evolution chain"
    )

    def add_modification(self, agent_id: str, change_type: str, description: str):
        """Add a modification record to the history"""
        self.modification_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "change_type": change_type,
                "description": description,
                "version": len(self.modification_history) + 1,
            }
        )


class ConfidenceMetrics(BaseModel):
    """Confidence scoring for artifacts"""

    overall_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence score"
    )
    domain_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Domain-specific confidence"
    )
    completeness_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Completeness confidence"
    )
    accuracy_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Accuracy confidence"
    )
    consistency_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Consistency confidence"
    )

    # Factors affecting confidence
    agent_expertise_score: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Agent's expertise in domain"
    )
    data_quality_score: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Quality of input data"
    )
    complexity_penalty: float = Field(
        default=0.0, ge=0.0, le=0.5, description="Penalty for high complexity"
    )

    def calculate_overall_confidence(self) -> float:
        """Calculate weighted overall confidence"""
        weights = {
            "domain": 0.3,
            "completeness": 0.25,
            "accuracy": 0.25,
            "consistency": 0.2,
        }

        base_confidence = (
            weights["domain"] * self.domain_confidence
            + weights["completeness"] * self.completeness_confidence
            + weights["accuracy"] * self.accuracy_confidence
            + weights["consistency"] * self.consistency_confidence
        )

        # Apply expertise and quality factors
        adjusted_confidence = (
            base_confidence * self.agent_expertise_score * self.data_quality_score
        )

        # Apply complexity penalty
        final_confidence = max(0.0, adjusted_confidence - self.complexity_penalty)

        self.overall_confidence = min(1.0, final_confidence)
        return self.overall_confidence


class TypedArtifactHandler:
    """
    Enhanced artifact handler with strict typing, schema enforcement, and intelligent validation.

    Features:
    - Strict schema validation with confidence scoring
    - Lineage tracking and version management
    - Semantic similarity checking
    - Domain-specific quality assessment
    - Conflict detection and resolution
    """

    def __init__(self):
        self.artifact_schemas = {
            "SpecDoc": SpecDocSchema,
            "DesignDoc": DesignDocSchema,
            "CodePatch": CodePatchSchema,
            "TestPlan": TestPlanSchema,
            "EvalReport": EvalReportSchema,
            "Runbook": RunbookSchema,
        }

        # Agent domain expertise mapping
        self.agent_expertise = {
            "project_manager": {"SpecDoc": 0.9, "DesignDoc": 0.7, "EvalReport": 0.8},
            "code_generator": {"CodePatch": 0.95, "DesignDoc": 0.8, "TestPlan": 0.6},
            "test_writer": {"TestPlan": 0.95, "CodePatch": 0.7, "EvalReport": 0.8},
            "ui_designer": {"DesignDoc": 0.9, "CodePatch": 0.7, "SpecDoc": 0.6},
            "debugger": {"CodePatch": 0.9, "EvalReport": 0.85, "TestPlan": 0.7},
        }

        self.validator = ArtifactValidator()
        self.artifact_lineage: Dict[str, ArtifactLineage] = {}
        self.artifact_store: Dict[str, ArtifactBase] = {}

    def create_artifact(
        self,
        agent_output: Dict[str, Any],
        artifact_type: str,
        agent_id: str = "unknown",
    ) -> Dict[str, Any]:
        """
        Create and validate a typed artifact from agent output.

        Args:
            agent_output: Raw output from agent
            artifact_type: Type of artifact to create
            agent_id: ID of the creating agent

        Returns:
            Dict containing the validated artifact and metadata
        """

        # Validate artifact type
        if artifact_type not in self.artifact_schemas:
            raise ValueError(f"Unknown artifact type: {artifact_type}")

        artifact_class = self.artifact_schemas[artifact_type]

        # Generate artifact ID and metadata
        artifact_id = str(uuid4())
        creation_time = datetime.now()

        # Map artifact type names
        artifact_type_mapping = {
            "SpecDoc": "SPEC_DOC",
            "DesignDoc": "DESIGN_DOC",
            "CodePatch": "CODE_PATCH",
            "TestPlan": "TEST_PLAN",
            "EvalReport": "EVAL_REPORT",
            "Runbook": "RUNBOOK",
        }

        mapped_type = artifact_type_mapping.get(artifact_type, artifact_type.upper())

        # Prepare artifact data
        artifact_data = {
            **agent_output,
            "artifact_id": artifact_id,
            "artifact_type": mapped_type,
            "created_at": creation_time,
            "created_by": agent_id,
            "version": "1.0.0",
        }

        try:
            # Create and validate artifact
            artifact = artifact_class(**artifact_data)

            # Run comprehensive validation
            validation_result = self.validator.validate_artifact(
                artifact.dict(), validator_id=f"typed_handler_{agent_id}"
            )

            # Calculate confidence metrics
            confidence_metrics = self._calculate_confidence_metrics(
                artifact, artifact_type, agent_id, validation_result
            )

            # Create lineage tracking
            lineage = ArtifactLineage(
                artifact_id=artifact_id,
                creation_agent=agent_id,
                semantic_hash=self._generate_semantic_hash(artifact),
                version_chain=[artifact_id],
            )

            # Store artifact and lineage
            self.artifact_store[artifact_id] = artifact
            self.artifact_lineage[artifact_id] = lineage

            # Generate impact analysis
            impact_analysis = self._analyze_impact(artifact, artifact_type)

            logger.info(f"Created {artifact_type} artifact {artifact_id} by {agent_id}")

            return {
                "artifact": artifact.dict(),
                "validation_result": validation_result.dict(),
                "confidence_metrics": confidence_metrics.dict(),
                "lineage": lineage.dict(),
                "impact_analysis": impact_analysis,
                "creation_metadata": {
                    "artifact_id": artifact_id,
                    "artifact_type": artifact_type,
                    "created_by": agent_id,
                    "created_at": creation_time.isoformat(),
                    "schema_version": "2.0.0",
                },
            }

        except ValidationError as e:
            # Handle validation failures gracefully
            error_details = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_details.append(f"{field_path}: {error['msg']}")

            logger.error(
                f"Artifact validation failed for {artifact_type}: {error_details}"
            )

            return {
                "error": "artifact_validation_failed",
                "error_details": error_details,
                "artifact_type": artifact_type,
                "agent_id": agent_id,
                "raw_output": agent_output,
            }

    def _calculate_confidence_metrics(
        self,
        artifact: ArtifactBase,
        artifact_type: str,
        agent_id: str,
        validation_result: ValidationResult,
    ) -> ConfidenceMetrics:
        """Calculate comprehensive confidence metrics for an artifact"""

        # Get agent expertise for this artifact type
        agent_expertise = self.agent_expertise.get(agent_id, {}).get(artifact_type, 0.5)

        # Base confidence from validation
        completeness_confidence = validation_result.completeness_score
        accuracy_confidence = validation_result.quality_score

        # Domain-specific confidence based on artifact type
        domain_confidence = self._calculate_domain_confidence(artifact, artifact_type)

        # Consistency confidence based on internal coherence
        consistency_confidence = self._calculate_consistency_confidence(artifact)

        # Data quality based on input richness
        data_quality = min(
            1.0, len(str(artifact.dict())) / 1000
        )  # Penalize very short artifacts

        # Complexity penalty for overly complex artifacts
        complexity_penalty = self._calculate_complexity_penalty(artifact)

        confidence_metrics = ConfidenceMetrics(
            overall_confidence=0.0,  # Will be calculated
            domain_confidence=domain_confidence,
            completeness_confidence=completeness_confidence,
            accuracy_confidence=accuracy_confidence,
            consistency_confidence=consistency_confidence,
            agent_expertise_score=agent_expertise,
            data_quality_score=data_quality,
            complexity_penalty=complexity_penalty,
        )

        # Calculate overall confidence
        confidence_metrics.calculate_overall_confidence()

        return confidence_metrics

    def _calculate_domain_confidence(
        self, artifact: ArtifactBase, artifact_type: str
    ) -> float:
        """Calculate domain-specific confidence based on artifact content"""

        if artifact_type == "SpecDoc":
            spec = artifact
            score = 0.0
            factors = 0

            # Requirements quality
            if hasattr(spec, "requirements") and spec.requirements:
                avg_req_quality = sum(
                    1
                    for req in spec.requirements
                    if len(req.get("description", "")) > 30
                ) / len(spec.requirements)
                score += avg_req_quality
                factors += 1

            # Acceptance criteria presence
            if hasattr(spec, "acceptance_criteria") and spec.acceptance_criteria:
                score += 1.0
                factors += 1

            return score / factors if factors > 0 else 0.5

        elif artifact_type == "CodePatch":
            patch = artifact
            score = 0.0
            factors = 0

            # Diff quality
            if hasattr(patch, "diff_unified") and patch.diff_unified:
                has_diff_markers = any(
                    line.startswith(("+", "-", "@@"))
                    for line in patch.diff_unified.split("\n")
                )
                score += 1.0 if has_diff_markers else 0.3
                factors += 1

            # Test instructions
            if hasattr(patch, "test_instructions") and patch.test_instructions:
                score += 1.0
                factors += 1

            return score / factors if factors > 0 else 0.5

        # Default domain confidence
        return 0.7

    def _calculate_consistency_confidence(self, artifact: ArtifactBase) -> float:
        """Calculate internal consistency confidence"""

        # Check for internal consistency indicators
        artifact_dict = artifact.dict()

        # Title-content alignment
        title = artifact_dict.get("title", "")
        content_fields = [
            artifact_dict.get("description", ""),
            artifact_dict.get("objective", ""),
            artifact_dict.get("overview", ""),
            str(artifact_dict.get("requirements", [])),
            str(artifact_dict.get("components", [])),
        ]

        content = " ".join(filter(None, content_fields)).lower()
        title_words = set(title.lower().split())

        # Simple consistency check: title words should appear in content
        if title_words and content:
            consistency_ratio = len(title_words.intersection(content.split())) / len(
                title_words
            )
            return min(1.0, consistency_ratio + 0.3)  # Baseline boost

        return 0.7  # Default consistency

    def _calculate_complexity_penalty(self, artifact: ArtifactBase) -> float:
        """Calculate penalty for overly complex artifacts"""

        artifact_dict = artifact.dict()

        # Count nested structures
        nested_count = 0
        for value in artifact_dict.values():
            if isinstance(value, (list, dict)):
                nested_count += 1
                if isinstance(value, list):
                    nested_count += len(value) * 0.1  # Small penalty per list item

        # Penalty increases with complexity
        if nested_count > 20:
            return 0.3
        elif nested_count > 15:
            return 0.2
        elif nested_count > 10:
            return 0.1

        return 0.0

    def _generate_semantic_hash(self, artifact: ArtifactBase) -> str:
        """Generate a semantic hash for change detection"""

        # Extract semantic content (exclude metadata)
        semantic_content = artifact.dict()
        metadata_keys = {"artifact_id", "created_at", "created_by", "version"}

        semantic_dict = {
            k: v for k, v in semantic_content.items() if k not in metadata_keys
        }

        # Create deterministic hash
        content_str = json.dumps(semantic_dict, sort_keys=True)
        return str(hash(content_str))

    def _analyze_impact(
        self, artifact: ArtifactBase, artifact_type: str
    ) -> Dict[str, Any]:
        """Analyze the potential impact of this artifact"""

        impact = {
            "scope": "local",  # local, module, system, project
            "affected_areas": [],
            "required_updates": [],
            "risk_level": "low",  # low, medium, high, critical
            "dependencies": artifact.dependencies
            if hasattr(artifact, "dependencies")
            else [],
        }

        if artifact_type == "SpecDoc":
            impact.update(
                {
                    "scope": "project",
                    "affected_areas": ["requirements", "design", "testing"],
                    "required_updates": ["design_docs", "test_plans"],
                    "risk_level": "high",  # Specs affect everything
                }
            )

        elif artifact_type == "CodePatch":
            patch = artifact
            if hasattr(patch, "files_changed") and patch.files_changed:
                files_count = len(patch.files_changed)
                if files_count > 10:
                    impact["scope"] = "system"
                    impact["risk_level"] = "high"
                elif files_count > 5:
                    impact["scope"] = "module"
                    impact["risk_level"] = "medium"

                impact["affected_areas"] = ["codebase", "tests"]
                if hasattr(patch, "breaking_changes") and patch.breaking_changes:
                    impact["risk_level"] = "critical"
                    impact["required_updates"].append("api_documentation")

        elif artifact_type == "TestPlan":
            impact.update(
                {
                    "scope": "module",
                    "affected_areas": ["testing", "quality_assurance"],
                    "required_updates": ["test_execution"],
                    "risk_level": "medium",
                }
            )

        return impact

    def get_artifact(self, artifact_id: str) -> Optional[ArtifactBase]:
        """Retrieve an artifact by ID"""
        return self.artifact_store.get(artifact_id)

    def get_lineage(self, artifact_id: str) -> Optional[ArtifactLineage]:
        """Get lineage information for an artifact"""
        return self.artifact_lineage.get(artifact_id)

    def update_artifact(
        self, artifact_id: str, updates: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """Update an existing artifact with change tracking"""

        if artifact_id not in self.artifact_store:
            raise ValueError(f"Artifact {artifact_id} not found")

        current_artifact = self.artifact_store[artifact_id]
        lineage = self.artifact_lineage[artifact_id]

        # Create updated artifact
        updated_data = current_artifact.dict()
        updated_data.update(updates)

        # Update version
        version_parts = updated_data["version"].split(".")
        version_parts[2] = str(int(version_parts[2]) + 1)
        updated_data["version"] = ".".join(version_parts)

        # Create new artifact instance
        artifact_class = type(current_artifact)
        updated_artifact = artifact_class(**updated_data)

        # Update semantic hash and lineage
        new_semantic_hash = self._generate_semantic_hash(updated_artifact)

        lineage.add_modification(
            agent_id=agent_id,
            change_type="update",
            description=f"Updated by {agent_id}",
        )
        lineage.semantic_hash = new_semantic_hash
        lineage.version_chain.append(f"{artifact_id}_v{updated_data['version']}")

        # Store updated artifact
        self.artifact_store[artifact_id] = updated_artifact

        logger.info(f"Updated artifact {artifact_id} by {agent_id}")

        return {
            "artifact": updated_artifact.dict(),
            "lineage": lineage.dict(),
            "update_metadata": {
                "updated_by": agent_id,
                "updated_at": datetime.now().isoformat(),
                "version": updated_data["version"],
            },
        }

    def list_artifacts(
        self, artifact_type: Optional[str] = None, agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List artifacts with optional filtering"""

        artifacts = []
        for artifact_id, artifact in self.artifact_store.items():
            if artifact_type and artifact.artifact_type.value != artifact_type.lower():
                continue
            if agent_id and artifact.created_by != agent_id:
                continue

            lineage = self.artifact_lineage.get(artifact_id)
            artifacts.append(
                {
                    "artifact": artifact.dict(),
                    "lineage": lineage.dict() if lineage else None,
                }
            )

        return artifacts

    def detect_conflicts(self, artifact_ids: List[str]) -> List[Dict[str, Any]]:
        """Detect potential conflicts between artifacts"""

        conflicts = []

        for i, id1 in enumerate(artifact_ids):
            for id2 in artifact_ids[i + 1 :]:
                artifact1 = self.artifact_store.get(id1)
                artifact2 = self.artifact_store.get(id2)

                if not artifact1 or not artifact2:
                    continue

                # Check for semantic conflicts
                conflict = self._check_semantic_conflict(artifact1, artifact2)
                if conflict:
                    conflicts.append(
                        {
                            "artifact_1": id1,
                            "artifact_2": id2,
                            "conflict_type": conflict["type"],
                            "severity": conflict["severity"],
                            "description": conflict["description"],
                        }
                    )

        return conflicts

    def _check_semantic_conflict(
        self, artifact1: ArtifactBase, artifact2: ArtifactBase
    ) -> Optional[Dict[str, Any]]:
        """Check for semantic conflicts between two artifacts"""

        # Same type artifacts with overlapping scope
        if artifact1.artifact_type == artifact2.artifact_type:
            # Check for overlapping content
            content1 = str(artifact1.dict()).lower()
            content2 = str(artifact2.dict()).lower()

            # Simple overlap detection
            words1 = set(content1.split())
            words2 = set(content2.split())
            overlap = words1.intersection(words2)

            if len(overlap) > min(len(words1), len(words2)) * 0.7:
                return {
                    "type": "content_overlap",
                    "severity": "medium",
                    "description": f"High content overlap between {artifact1.artifact_type} artifacts",
                }

        # Check dependency conflicts
        deps1 = (
            set(artifact1.dependencies) if hasattr(artifact1, "dependencies") else set()
        )
        deps2 = (
            set(artifact2.dependencies) if hasattr(artifact2, "dependencies") else set()
        )

        if deps1.intersection(deps2):
            return {
                "type": "dependency_conflict",
                "severity": "high",
                "description": "Artifacts have conflicting dependencies",
            }

        return None

    def export_artifacts(self, format: str = "json") -> str:
        """Export all artifacts in specified format"""

        export_data = {
            "artifacts": [artifact.dict() for artifact in self.artifact_store.values()],
            "lineage": [lineage.dict() for lineage in self.artifact_lineage.values()],
            "export_metadata": {
                "export_time": datetime.now().isoformat(),
                "total_artifacts": len(self.artifact_store),
                "format_version": "2.0.0",
            },
        }

        if format.lower() == "json":
            return json.dumps(export_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")

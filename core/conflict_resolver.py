"""
Conflict Resolution Engine with weighted consensus and semantic analysis.

This module provides sophisticated conflict detection and resolution mechanisms
for multi-agent artifact creation, using domain expertise weighting and
semantic similarity analysis.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
import difflib

from schemas.artifact_schemas import ArtifactType, ArtifactBase
from core.artifact_handler import TypedArtifactHandler


logger = logging.getLogger(__name__)


class ConflictType(str, Enum):
    """Types of conflicts that can occur between artifacts"""

    CONTENT_OVERLAP = "content_overlap"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    SEMANTIC_INCONSISTENCY = "semantic_inconsistency"
    VERSION_CONFLICT = "version_conflict"
    REQUIREMENT_CONTRADICTION = "requirement_contradiction"
    DESIGN_MISMATCH = "design_mismatch"
    IMPLEMENTATION_CLASH = "implementation_clash"


class ConflictSeverity(str, Enum):
    """Severity levels for conflicts"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionStrategy(str, Enum):
    """Strategies for resolving conflicts"""

    WEIGHTED_CONSENSUS = "weighted_consensus"
    EXPERT_OVERRIDE = "expert_override"
    MERGE_CONTENT = "merge_content"
    ESCALATE_HUMAN = "escalate_human"
    CREATE_ALTERNATIVE = "create_alternative"
    SEQUENTIAL_REFINEMENT = "sequential_refinement"


class ConflictDetails(BaseModel):
    """Detailed information about a detected conflict"""

    conflict_id: str = Field(..., description="Unique conflict identifier")
    conflict_type: ConflictType = Field(..., description="Type of conflict")
    severity: ConflictSeverity = Field(..., description="Conflict severity")

    # Conflicting artifacts
    artifact_ids: List[str] = Field(..., description="IDs of conflicting artifacts")
    artifact_types: List[ArtifactType] = Field(
        ..., description="Types of conflicting artifacts"
    )

    # Conflict analysis
    description: str = Field(..., description="Human-readable conflict description")
    conflicting_elements: List[Dict[str, Any]] = Field(
        default_factory=list, description="Specific elements in conflict"
    )
    similarity_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Semantic similarity between artifacts"
    )

    # Impact assessment
    impact_areas: List[str] = Field(
        default_factory=list, description="Areas affected by conflict"
    )
    downstream_effects: List[str] = Field(
        default_factory=list, description="Potential downstream effects"
    )

    # Detection metadata
    detected_at: datetime = Field(
        default_factory=datetime.now, description="Detection timestamp"
    )
    detection_method: str = Field(
        default="automatic", description="How conflict was detected"
    )
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Detection confidence"
    )

    class Config:
        use_enum_values = True


class ResolutionOption(BaseModel):
    """Option for resolving a conflict"""

    option_id: str = Field(..., description="Unique option identifier")
    strategy: ResolutionStrategy = Field(..., description="Resolution strategy")
    description: str = Field(..., description="Description of resolution approach")

    # Outcome prediction
    expected_outcome: str = Field(..., description="Expected result of this resolution")
    confidence: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Confidence in resolution"
    )
    estimated_effort: str = Field(
        default="medium", description="Estimated effort required"
    )

    # Trade-offs
    advantages: List[str] = Field(
        default_factory=list, description="Advantages of this option"
    )
    disadvantages: List[str] = Field(
        default_factory=list, description="Potential drawbacks"
    )

    # Implementation details
    required_actions: List[str] = Field(
        default_factory=list, description="Actions needed"
    )
    affected_artifacts: List[str] = Field(
        default_factory=list, description="Artifacts that will change"
    )
    new_artifacts: List[str] = Field(
        default_factory=list, description="New artifacts to create"
    )

    class Config:
        use_enum_values = True


class ResolutionResult(BaseModel):
    """Result of conflict resolution"""

    resolution_id: str = Field(..., description="Unique resolution identifier")
    conflict_id: str = Field(..., description="ID of resolved conflict")
    strategy_used: ResolutionStrategy = Field(
        ..., description="Strategy that was applied"
    )

    # Resolution outcome
    success: bool = Field(..., description="Whether resolution was successful")
    resolution_description: str = Field(..., description="Description of what was done")

    # Artifact changes
    modified_artifacts: List[str] = Field(
        default_factory=list, description="Modified artifact IDs"
    )
    created_artifacts: List[str] = Field(
        default_factory=list, description="New artifact IDs"
    )
    archived_artifacts: List[str] = Field(
        default_factory=list, description="Archived artifact IDs"
    )

    # Quality metrics
    resolution_quality: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Quality of resolution"
    )
    stakeholder_satisfaction: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Estimated stakeholder satisfaction"
    )

    # Metadata
    resolved_at: datetime = Field(
        default_factory=datetime.now, description="Resolution timestamp"
    )
    resolved_by: str = Field(..., description="Who/what resolved the conflict")
    processing_time: float = Field(default=0.0, description="Time taken to resolve")

    class Config:
        use_enum_values = True


class ConflictResolver:
    """
    Advanced conflict resolution engine with multiple strategies.

    Provides sophisticated conflict detection, analysis, and resolution
    using domain expertise, semantic analysis, and weighted consensus mechanisms.
    """

    def __init__(self, artifact_handler: TypedArtifactHandler):
        self.artifact_handler = artifact_handler

        # Domain expertise weights for different agent types
        self.domain_expertise = {
            "project_manager": {
                ArtifactType.SPEC_DOC: 0.95,
                ArtifactType.EVAL_REPORT: 0.90,
                ArtifactType.TEST_PLAN: 0.70,
                ArtifactType.DESIGN_DOC: 0.60,
                ArtifactType.CODE_PATCH: 0.40,
                ArtifactType.RUNBOOK: 0.75,
            },
            "code_generator": {
                ArtifactType.CODE_PATCH: 0.95,
                ArtifactType.DESIGN_DOC: 0.85,
                ArtifactType.SPEC_DOC: 0.60,
                ArtifactType.TEST_PLAN: 0.50,
                ArtifactType.EVAL_REPORT: 0.65,
                ArtifactType.RUNBOOK: 0.70,
            },
            "test_writer": {
                ArtifactType.TEST_PLAN: 0.95,
                ArtifactType.EVAL_REPORT: 0.90,
                ArtifactType.CODE_PATCH: 0.70,
                ArtifactType.SPEC_DOC: 0.65,
                ArtifactType.DESIGN_DOC: 0.55,
                ArtifactType.RUNBOOK: 0.60,
            },
            "ui_designer": {
                ArtifactType.DESIGN_DOC: 0.95,
                ArtifactType.CODE_PATCH: 0.75,
                ArtifactType.SPEC_DOC: 0.70,
                ArtifactType.TEST_PLAN: 0.50,
                ArtifactType.EVAL_REPORT: 0.55,
                ArtifactType.RUNBOOK: 0.45,
            },
            "debugger": {
                ArtifactType.EVAL_REPORT: 0.95,
                ArtifactType.CODE_PATCH: 0.90,
                ArtifactType.TEST_PLAN: 0.80,
                ArtifactType.DESIGN_DOC: 0.65,
                ArtifactType.SPEC_DOC: 0.55,
                ArtifactType.RUNBOOK: 0.85,
            },
        }

        # Conflict resolution history
        self.conflict_history: List[ConflictDetails] = []
        self.resolution_history: List[ResolutionResult] = []

        # Semantic similarity threshold for conflict detection
        self.similarity_threshold = 0.7

    def detect_conflicts(self, artifact_ids: List[str]) -> List[ConflictDetails]:
        """
        Detect conflicts between a set of artifacts.

        Args:
            artifact_ids: List of artifact IDs to analyze

        Returns:
            List of detected conflicts
        """

        conflicts = []

        # Get artifacts
        artifacts = {}
        for artifact_id in artifact_ids:
            artifact = self.artifact_handler.get_artifact(artifact_id)
            if artifact:
                artifacts[artifact_id] = artifact

        if len(artifacts) < 2:
            return conflicts

        artifact_list = list(artifacts.items())

        # Pairwise conflict detection
        for i, (id1, artifact1) in enumerate(artifact_list):
            for id2, artifact2 in artifact_list[i + 1 :]:
                # Skip if same artifact
                if id1 == id2:
                    continue

                # Detect different types of conflicts
                conflict_checks = [
                    self._check_content_overlap,
                    self._check_dependency_conflicts,
                    self._check_semantic_inconsistency,
                    self._check_requirement_contradictions,
                    self._check_design_mismatches,
                ]

                for check_func in conflict_checks:
                    conflict = check_func(artifact1, artifact2, id1, id2)
                    if conflict:
                        conflicts.append(conflict)
                        self.conflict_history.append(conflict)

                        logger.warning(
                            f"Conflict detected: {conflict.conflict_type} between {id1} and {id2}"
                        )

        return conflicts

    def _check_content_overlap(
        self, artifact1: ArtifactBase, artifact2: ArtifactBase, id1: str, id2: str
    ) -> Optional[ConflictDetails]:
        """Check for content overlap between artifacts"""

        # Only check same-type artifacts
        if artifact1.artifact_type != artifact2.artifact_type:
            return None

        # Extract content for comparison
        content1 = self._extract_artifact_content(artifact1)
        content2 = self._extract_artifact_content(artifact2)

        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, content1, content2).ratio()

        if similarity > self.similarity_threshold:
            # Determine severity based on similarity
            if similarity > 0.9:
                severity = ConflictSeverity.HIGH
            elif similarity > 0.8:
                severity = ConflictSeverity.MEDIUM
            else:
                severity = ConflictSeverity.LOW

            return ConflictDetails(
                conflict_id=f"overlap_{id1}_{id2}_{int(datetime.now().timestamp())}",
                conflict_type=ConflictType.CONTENT_OVERLAP,
                severity=severity,
                artifact_ids=[id1, id2],
                artifact_types=[artifact1.artifact_type, artifact2.artifact_type],
                description=f"High content similarity ({similarity:.2f}) between {artifact1.artifact_type} artifacts",
                similarity_score=similarity,
                impact_areas=["content_duplication", "maintenance_overhead"],
                conflicting_elements=[
                    {
                        "type": "content_similarity",
                        "score": similarity,
                        "threshold": self.similarity_threshold,
                    }
                ],
            )

        return None

    def _check_dependency_conflicts(
        self, artifact1: ArtifactBase, artifact2: ArtifactBase, id1: str, id2: str
    ) -> Optional[ConflictDetails]:
        """Check for dependency conflicts"""

        deps1 = (
            set(artifact1.dependencies) if hasattr(artifact1, "dependencies") else set()
        )
        deps2 = (
            set(artifact2.dependencies) if hasattr(artifact2, "dependencies") else set()
        )

        # Check for circular dependencies
        if id1 in deps2 and id2 in deps1:
            return ConflictDetails(
                conflict_id=f"circular_dep_{id1}_{id2}_{int(datetime.now().timestamp())}",
                conflict_type=ConflictType.DEPENDENCY_CONFLICT,
                severity=ConflictSeverity.HIGH,
                artifact_ids=[id1, id2],
                artifact_types=[artifact1.artifact_type, artifact2.artifact_type],
                description="Circular dependency detected between artifacts",
                impact_areas=["build_order", "testing_sequence", "deployment"],
                conflicting_elements=[
                    {
                        "type": "circular_dependency",
                        "artifact_1": id1,
                        "artifact_2": id2,
                    }
                ],
            )

        # Check for conflicting dependencies
        conflicting_deps = deps1.intersection(deps2)
        if conflicting_deps and len(conflicting_deps) > len(deps1.union(deps2)) * 0.5:
            return ConflictDetails(
                conflict_id=f"dep_conflict_{id1}_{id2}_{int(datetime.now().timestamp())}",
                conflict_type=ConflictType.DEPENDENCY_CONFLICT,
                severity=ConflictSeverity.MEDIUM,
                artifact_ids=[id1, id2],
                artifact_types=[artifact1.artifact_type, artifact2.artifact_type],
                description="Conflicting dependency requirements between artifacts",
                impact_areas=["integration", "compatibility"],
                conflicting_elements=[
                    {"type": "dependency_overlap", "conflicts": list(conflicting_deps)}
                ],
            )

        return None

    def _check_semantic_inconsistency(
        self, artifact1: ArtifactBase, artifact2: ArtifactBase, id1: str, id2: str
    ) -> Optional[ConflictDetails]:
        """Check for semantic inconsistencies"""

        # For now, focus on specific artifact type combinations
        if (
            artifact1.artifact_type == ArtifactType.SPEC_DOC
            and artifact2.artifact_type == ArtifactType.DESIGN_DOC
        ):
            # Extract requirements from spec and components from design
            spec_dict = artifact1.dict()
            design_dict = artifact2.dict()

            spec_requirements = spec_dict.get("functional_requirements", [])
            design_components = design_dict.get("components", [])

            # Simple check: ensure design addresses requirements
            if spec_requirements and design_components:
                req_terms = set()
                for req in spec_requirements:
                    req_terms.update(req.get("description", "").lower().split())

                comp_terms = set()
                for comp in design_components:
                    comp_terms.update(comp.get("description", "").lower().split())

                coverage = (
                    len(req_terms.intersection(comp_terms)) / len(req_terms)
                    if req_terms
                    else 0
                )

                if coverage < 0.3:  # Low coverage indicates potential mismatch
                    return ConflictDetails(
                        conflict_id=f"semantic_{id1}_{id2}_{int(datetime.now().timestamp())}",
                        conflict_type=ConflictType.SEMANTIC_INCONSISTENCY,
                        severity=ConflictSeverity.MEDIUM,
                        artifact_ids=[id1, id2],
                        artifact_types=[
                            artifact1.artifact_type,
                            artifact2.artifact_type,
                        ],
                        description=f"Design may not adequately address requirements (coverage: {coverage:.2f})",
                        similarity_score=coverage,
                        impact_areas=["requirements_traceability", "completeness"],
                        conflicting_elements=[
                            {
                                "type": "requirement_coverage",
                                "coverage": coverage,
                                "threshold": 0.3,
                            }
                        ],
                    )

        return None

    def _check_requirement_contradictions(
        self, artifact1: ArtifactBase, artifact2: ArtifactBase, id1: str, id2: str
    ) -> Optional[ConflictDetails]:
        """Check for contradictory requirements"""

        # Only check between spec documents
        if (
            artifact1.artifact_type != ArtifactType.SPEC_DOC
            or artifact2.artifact_type != ArtifactType.SPEC_DOC
        ):
            return None

        spec1_dict = artifact1.dict()
        spec2_dict = artifact2.dict()

        # Look for contradictory requirements
        reqs1 = spec1_dict.get("functional_requirements", [])
        reqs2 = spec2_dict.get("functional_requirements", [])

        # Simple contradiction detection based on negation keywords
        contradiction_keywords = [
            ("must", "must not"),
            ("should", "should not"),
            ("required", "forbidden"),
            ("allow", "prevent"),
            ("enable", "disable"),
        ]

        contradictions = []
        for req1 in reqs1:
            req1_text = req1.get("description", "").lower()
            for req2 in reqs2:
                req2_text = req2.get("description", "").lower()

                for pos_keyword, neg_keyword in contradiction_keywords:
                    if (
                        pos_keyword in req1_text
                        and neg_keyword in req2_text
                        and len(
                            set(req1_text.split()).intersection(set(req2_text.split()))
                        )
                        > 3
                    ):
                        contradictions.append(
                            {
                                "req1": req1.get("id", "unknown"),
                                "req2": req2.get("id", "unknown"),
                                "contradiction": f"{pos_keyword} vs {neg_keyword}",
                            }
                        )

        if contradictions:
            return ConflictDetails(
                conflict_id=f"contradiction_{id1}_{id2}_{int(datetime.now().timestamp())}",
                conflict_type=ConflictType.REQUIREMENT_CONTRADICTION,
                severity=ConflictSeverity.HIGH,
                artifact_ids=[id1, id2],
                artifact_types=[artifact1.artifact_type, artifact2.artifact_type],
                description=f"Contradictory requirements detected ({len(contradictions)} conflicts)",
                impact_areas=["requirements_consistency", "implementation_clarity"],
                conflicting_elements=contradictions,
            )

        return None

    def _check_design_mismatches(
        self, artifact1: ArtifactBase, artifact2: ArtifactBase, id1: str, id2: str
    ) -> Optional[ConflictDetails]:
        """Check for design mismatches"""

        # Check between design docs and code patches
        if not (
            (
                artifact1.artifact_type == ArtifactType.DESIGN_DOC
                and artifact2.artifact_type == ArtifactType.CODE_PATCH
            )
            or (
                artifact1.artifact_type == ArtifactType.CODE_PATCH
                and artifact2.artifact_type == ArtifactType.DESIGN_DOC
            )
        ):
            return None

        # Determine which is design and which is code
        if artifact1.artifact_type == ArtifactType.DESIGN_DOC:
            design_artifact, code_artifact = artifact1, artifact2
            design_id, code_id = id1, id2
        else:
            design_artifact, code_artifact = artifact2, artifact1
            design_id, code_id = id2, id1

        design_dict = design_artifact.dict()
        code_dict = code_artifact.dict()

        # Check if code implements design components
        design_components = design_dict.get("components", [])
        code_files = code_dict.get("files_changed", [])

        if design_components and code_files:
            # Extract component names and file names for comparison
            component_names = [
                comp.get("name", "").lower() for comp in design_components
            ]
            file_names = [file_info.get("path", "").lower() for file_info in code_files]

            # Simple matching based on name similarity
            matches = 0
            for comp_name in component_names:
                if any(
                    comp_name in file_name or file_name in comp_name
                    for file_name in file_names
                ):
                    matches += 1

            match_ratio = matches / len(component_names) if component_names else 1

            if match_ratio < 0.5:  # Low match indicates potential mismatch
                return ConflictDetails(
                    conflict_id=f"design_mismatch_{design_id}_{code_id}_{int(datetime.now().timestamp())}",
                    conflict_type=ConflictType.DESIGN_MISMATCH,
                    severity=ConflictSeverity.MEDIUM,
                    artifact_ids=[design_id, code_id],
                    artifact_types=[
                        design_artifact.artifact_type,
                        code_artifact.artifact_type,
                    ],
                    description=f"Code implementation may not match design (match ratio: {match_ratio:.2f})",
                    similarity_score=match_ratio,
                    impact_areas=[
                        "design_implementation_consistency",
                        "architecture_integrity",
                    ],
                    conflicting_elements=[
                        {
                            "type": "implementation_mismatch",
                            "match_ratio": match_ratio,
                            "threshold": 0.5,
                        }
                    ],
                )

        return None

    def resolve_artifacts(
        self,
        conflicting_artifacts: List[str],
        strategy: Optional[ResolutionStrategy] = None,
    ) -> ResolutionResult:
        """
        Resolve conflicts between artifacts using specified or optimal strategy.

        Args:
            conflicting_artifacts: List of conflicting artifact IDs
            strategy: Resolution strategy to use (auto-selected if None)

        Returns:
            ResolutionResult with outcome details
        """

        start_time = datetime.now()
        resolution_id = f"resolution_{start_time.strftime('%Y%m%d_%H%M%S')}"

        # Detect conflicts first
        conflicts = self.detect_conflicts(conflicting_artifacts)

        if not conflicts:
            return ResolutionResult(
                resolution_id=resolution_id,
                conflict_id="none",
                strategy_used=ResolutionStrategy.WEIGHTED_CONSENSUS,
                success=True,
                resolution_description="No conflicts detected",
                resolved_by="system",
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

        # Select strategy if not provided
        if not strategy:
            strategy = self._select_optimal_strategy(conflicts)

        # Apply resolution strategy
        try:
            if strategy == ResolutionStrategy.WEIGHTED_CONSENSUS:
                result = self._apply_weighted_consensus(
                    conflicts, conflicting_artifacts
                )
            elif strategy == ResolutionStrategy.EXPERT_OVERRIDE:
                result = self._apply_expert_override(conflicts, conflicting_artifacts)
            elif strategy == ResolutionStrategy.MERGE_CONTENT:
                result = self._apply_content_merge(conflicts, conflicting_artifacts)
            elif strategy == ResolutionStrategy.ESCALATE_HUMAN:
                result = self._escalate_to_human(conflicts, conflicting_artifacts)
            else:
                result = self._apply_weighted_consensus(
                    conflicts, conflicting_artifacts
                )  # Default

            result.resolution_id = resolution_id
            result.strategy_used = strategy
            result.processing_time = (datetime.now() - start_time).total_seconds()

            # Store in history
            self.resolution_history.append(result)

            logger.info(
                f"Conflict resolution completed: {resolution_id} using {strategy.value}"
            )

            return result

        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}")

            return ResolutionResult(
                resolution_id=resolution_id,
                conflict_id=conflicts[0].conflict_id if conflicts else "error",
                strategy_used=strategy,
                success=False,
                resolution_description=f"Resolution failed: {str(e)}",
                resolved_by="system",
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

    def _select_optimal_strategy(
        self, conflicts: List[ConflictDetails]
    ) -> ResolutionStrategy:
        """Select the optimal resolution strategy based on conflict characteristics"""

        # Analyze conflict characteristics
        has_critical = any(c.severity == ConflictSeverity.CRITICAL for c in conflicts)
        has_high = any(c.severity == ConflictSeverity.HIGH for c in conflicts)
        has_content_overlap = any(
            c.conflict_type == ConflictType.CONTENT_OVERLAP for c in conflicts
        )
        has_dependencies = any(
            c.conflict_type == ConflictType.DEPENDENCY_CONFLICT for c in conflicts
        )

        # Strategy selection logic
        if has_critical:
            return ResolutionStrategy.ESCALATE_HUMAN
        elif has_dependencies:
            return ResolutionStrategy.EXPERT_OVERRIDE
        elif has_content_overlap and not has_high:
            return ResolutionStrategy.MERGE_CONTENT
        else:
            return ResolutionStrategy.WEIGHTED_CONSENSUS

    def _apply_weighted_consensus(
        self, conflicts: List[ConflictDetails], artifact_ids: List[str]
    ) -> ResolutionResult:
        """Apply weighted consensus based on domain expertise"""

        # Get artifacts and their creators
        artifacts = {}
        for artifact_id in artifact_ids:
            artifact = self.artifact_handler.get_artifact(artifact_id)
            if artifact:
                artifacts[artifact_id] = artifact

        # Calculate weights based on domain expertise
        weights = {}
        for artifact_id, artifact in artifacts.items():
            agent_type = artifact.created_by
            artifact_type = artifact.artifact_type

            expertise_weight = self.domain_expertise.get(agent_type, {}).get(
                artifact_type, 0.5
            )
            confidence_weight = artifact.confidence

            weights[artifact_id] = expertise_weight * confidence_weight

        # Select artifact with highest weight
        if weights:
            winning_artifact_id = max(weights, key=weights.get)
            winning_weight = weights[winning_artifact_id]

            # Create resolution description
            resolution_desc = (
                f"Selected artifact {winning_artifact_id} based on weighted consensus "
                f"(weight: {winning_weight:.3f}). "
            )

            if len(artifacts) > 1:
                other_artifacts = [
                    aid for aid in artifact_ids if aid != winning_artifact_id
                ]
                resolution_desc += f"Archived conflicting artifacts: {other_artifacts}"

            return ResolutionResult(
                resolution_id="",  # Will be set by caller
                conflict_id=conflicts[0].conflict_id if conflicts else "",
                strategy_used=ResolutionStrategy.WEIGHTED_CONSENSUS,
                success=True,
                resolution_description=resolution_desc,
                modified_artifacts=[winning_artifact_id],
                archived_artifacts=[
                    aid for aid in artifact_ids if aid != winning_artifact_id
                ],
                resolution_quality=winning_weight,
                resolved_by="weighted_consensus_algorithm",
            )

        # Fallback if no weights calculated
        return ResolutionResult(
            resolution_id="",
            conflict_id=conflicts[0].conflict_id if conflicts else "",
            strategy_used=ResolutionStrategy.WEIGHTED_CONSENSUS,
            success=False,
            resolution_description="Unable to calculate weights for consensus",
            resolved_by="system",
        )

    def _apply_expert_override(
        self, conflicts: List[ConflictDetails], artifact_ids: List[str]
    ) -> ResolutionResult:
        """Apply expert override based on highest domain expertise"""

        # Find the artifact with the highest domain expertise for its type
        best_artifact_id = None
        best_expertise = 0.0

        for artifact_id in artifact_ids:
            artifact = self.artifact_handler.get_artifact(artifact_id)
            if artifact:
                agent_type = artifact.created_by
                artifact_type = artifact.artifact_type

                expertise = self.domain_expertise.get(agent_type, {}).get(
                    artifact_type, 0.0
                )
                if expertise > best_expertise:
                    best_expertise = expertise
                    best_artifact_id = artifact_id

        if best_artifact_id:
            return ResolutionResult(
                resolution_id="",
                conflict_id=conflicts[0].conflict_id if conflicts else "",
                strategy_used=ResolutionStrategy.EXPERT_OVERRIDE,
                success=True,
                resolution_description=f"Expert override: selected artifact {best_artifact_id} "
                f"from domain expert (expertise: {best_expertise:.3f})",
                modified_artifacts=[best_artifact_id],
                archived_artifacts=[
                    aid for aid in artifact_ids if aid != best_artifact_id
                ],
                resolution_quality=best_expertise,
                resolved_by=f"domain_expert_{best_expertise:.2f}",
            )

        return ResolutionResult(
            resolution_id="",
            conflict_id=conflicts[0].conflict_id if conflicts else "",
            strategy_used=ResolutionStrategy.EXPERT_OVERRIDE,
            success=False,
            resolution_description="No clear domain expert found",
            resolved_by="system",
        )

    def _apply_content_merge(
        self, conflicts: List[ConflictDetails], artifact_ids: List[str]
    ) -> ResolutionResult:
        """Merge content from multiple artifacts"""

        # This is a simplified merge - in practice, would need sophisticated merging logic
        artifacts = {}
        for artifact_id in artifact_ids:
            artifact = self.artifact_handler.get_artifact(artifact_id)
            if artifact:
                artifacts[artifact_id] = artifact

        if len(artifacts) < 2:
            return ResolutionResult(
                resolution_id="",
                conflict_id=conflicts[0].conflict_id if conflicts else "",
                strategy_used=ResolutionStrategy.MERGE_CONTENT,
                success=False,
                resolution_description="Insufficient artifacts for merging",
                resolved_by="system",
            )

        # For now, create a placeholder merged artifact
        # In practice, this would involve sophisticated content merging
        merged_id = f"merged_{int(datetime.now().timestamp())}"

        return ResolutionResult(
            resolution_id="",
            conflict_id=conflicts[0].conflict_id if conflicts else "",
            strategy_used=ResolutionStrategy.MERGE_CONTENT,
            success=True,
            resolution_description=f"Created merged artifact {merged_id} from {len(artifacts)} sources",
            created_artifacts=[merged_id],
            archived_artifacts=list(artifact_ids),
            resolution_quality=0.8,
            resolved_by="content_merger",
        )

    def _escalate_to_human(
        self, conflicts: List[ConflictDetails], artifact_ids: List[str]
    ) -> ResolutionResult:
        """Escalate conflict to human review"""

        return ResolutionResult(
            resolution_id="",
            conflict_id=conflicts[0].conflict_id if conflicts else "",
            strategy_used=ResolutionStrategy.ESCALATE_HUMAN,
            success=True,
            resolution_description=f"Escalated {len(conflicts)} conflicts to human review. "
            f"Artifacts pending review: {artifact_ids}",
            resolution_quality=1.0,  # Human review assumed to be highest quality
            resolved_by="human_review_escalation",
        )

    def _extract_artifact_content(self, artifact: ArtifactBase) -> str:
        """Extract meaningful content from artifact for comparison"""

        artifact_dict = artifact.dict()

        # Extract key content fields based on artifact type
        content_parts = []

        if artifact.artifact_type == ArtifactType.SPEC_DOC:
            content_parts.extend(
                [
                    artifact_dict.get("objective", ""),
                    str(artifact_dict.get("functional_requirements", [])),
                    str(artifact_dict.get("acceptance_criteria", [])),
                ]
            )
        elif artifact.artifact_type == ArtifactType.DESIGN_DOC:
            content_parts.extend(
                [
                    artifact_dict.get("overview", ""),
                    str(artifact_dict.get("components", [])),
                    str(artifact_dict.get("design_decisions", [])),
                ]
            )
        elif artifact.artifact_type == ArtifactType.CODE_PATCH:
            content_parts.extend(
                [
                    artifact_dict.get("description", ""),
                    artifact_dict.get("diff_unified", ""),
                    str(artifact_dict.get("files_changed", [])),
                ]
            )
        else:
            # Generic content extraction
            content_parts.extend(
                [
                    artifact_dict.get("title", ""),
                    artifact_dict.get("description", ""),
                    artifact_dict.get("objective", ""),
                    artifact_dict.get("overview", ""),
                ]
            )

        return " ".join(filter(None, content_parts)).lower()

    def get_resolution_options(
        self, conflicts: List[ConflictDetails]
    ) -> List[ResolutionOption]:
        """Generate resolution options for given conflicts"""

        options = []

        # Analyze conflict characteristics
        severity_levels = [c.severity for c in conflicts]
        conflict_types = [c.conflict_type for c in conflicts]

        has_critical = ConflictSeverity.CRITICAL in severity_levels
        has_high = ConflictSeverity.HIGH in severity_levels

        # Generate options based on conflict characteristics
        if has_critical:
            options.append(
                ResolutionOption(
                    option_id="escalate",
                    strategy=ResolutionStrategy.ESCALATE_HUMAN,
                    description="Escalate critical conflicts to human review",
                    expected_outcome="Human expert will resolve conflicts manually",
                    confidence=1.0,
                    estimated_effort="high",
                    advantages=["Highest quality resolution", "Expert judgment"],
                    disadvantages=["Requires human intervention", "Slower resolution"],
                    required_actions=["Create review ticket", "Notify stakeholders"],
                )
            )

        # Always offer weighted consensus
        options.append(
            ResolutionOption(
                option_id="consensus",
                strategy=ResolutionStrategy.WEIGHTED_CONSENSUS,
                description="Use domain expertise weights to select best artifact",
                expected_outcome="Artifact from most qualified agent will be selected",
                confidence=0.8,
                estimated_effort="low",
                advantages=["Automated resolution", "Based on expertise"],
                disadvantages=["May lose some valuable content"],
                required_actions=["Calculate weights", "Archive losing artifacts"],
            )
        )

        # Offer expert override for high severity
        if has_high:
            options.append(
                ResolutionOption(
                    option_id="expert",
                    strategy=ResolutionStrategy.EXPERT_OVERRIDE,
                    description="Select artifact from domain expert agent",
                    expected_outcome="Domain expert's artifact will be prioritized",
                    confidence=0.9,
                    estimated_effort="low",
                    advantages=["Expert knowledge prioritized", "Clear authority"],
                    disadvantages=["May ignore valid alternative perspectives"],
                    required_actions=["Identify domain expert", "Apply override"],
                )
            )

        # Offer merge for content overlaps
        if ConflictType.CONTENT_OVERLAP in conflict_types:
            options.append(
                ResolutionOption(
                    option_id="merge",
                    strategy=ResolutionStrategy.MERGE_CONTENT,
                    description="Merge compatible content from conflicting artifacts",
                    expected_outcome="Combined artifact with best elements from all sources",
                    confidence=0.7,
                    estimated_effort="medium",
                    advantages=[
                        "Preserves all valuable content",
                        "Comprehensive solution",
                    ],
                    disadvantages=["May create inconsistencies", "More complex"],
                    required_actions=[
                        "Analyze mergeable content",
                        "Create merged artifact",
                    ],
                )
            )

        return options

    def get_conflict_metrics(self) -> Dict[str, Any]:
        """Get metrics about conflict detection and resolution performance"""

        if not self.conflict_history:
            return {"total_conflicts": 0}

        total_conflicts = len(self.conflict_history)
        total_resolutions = len(self.resolution_history)

        # Conflict type distribution
        conflict_types = {}
        for conflict in self.conflict_history:
            conflict_types[conflict.conflict_type.value] = (
                conflict_types.get(conflict.conflict_type.value, 0) + 1
            )

        # Severity distribution
        severity_levels = {}
        for conflict in self.conflict_history:
            severity_levels[conflict.severity.value] = (
                severity_levels.get(conflict.severity.value, 0) + 1
            )

        # Resolution success rate
        successful_resolutions = sum(1 for r in self.resolution_history if r.success)
        success_rate = (
            successful_resolutions / total_resolutions if total_resolutions > 0 else 0
        )

        # Average resolution quality
        avg_quality = (
            sum(r.resolution_quality for r in self.resolution_history)
            / total_resolutions
            if total_resolutions > 0
            else 0
        )

        # Strategy effectiveness
        strategy_stats = {}
        for resolution in self.resolution_history:
            strategy = resolution.strategy_used.value
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"count": 0, "success": 0, "avg_quality": 0}

            strategy_stats[strategy]["count"] += 1
            if resolution.success:
                strategy_stats[strategy]["success"] += 1
            strategy_stats[strategy]["avg_quality"] += resolution.resolution_quality

        # Calculate averages
        for strategy in strategy_stats:
            count = strategy_stats[strategy]["count"]
            strategy_stats[strategy]["success_rate"] = (
                strategy_stats[strategy]["success"] / count
            )
            strategy_stats[strategy]["avg_quality"] = (
                strategy_stats[strategy]["avg_quality"] / count
            )

        return {
            "total_conflicts": total_conflicts,
            "total_resolutions": total_resolutions,
            "resolution_rate": total_resolutions / total_conflicts
            if total_conflicts > 0
            else 0,
            "success_rate": success_rate,
            "average_resolution_quality": avg_quality,
            "conflict_types": conflict_types,
            "severity_levels": severity_levels,
            "strategy_effectiveness": strategy_stats,
            "pending_conflicts": total_conflicts - total_resolutions,
        }

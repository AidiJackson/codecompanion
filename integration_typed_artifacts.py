"""
Integration module for the Typed Artifact System with the main Streamlit application.

This module provides seamless integration of the enhanced artifact system
with the existing multi-agent orchestration platform.
"""

import streamlit as st
import logging
from typing import Dict, List, Any
from datetime import datetime

from core.artifact_handler import TypedArtifactHandler
from core.handoff_protocol import AgentHandoff
from core.conflict_resolver import ConflictResolver

logger = logging.getLogger(__name__)


class TypedArtifactOrchestrator:
    """
    Orchestrator that integrates typed artifacts with the main application.

    Provides a high-level interface for the Streamlit app to use the
    typed artifact system seamlessly.
    """

    def __init__(self):
        self.artifact_handler = TypedArtifactHandler()
        self.handoff_protocol = AgentHandoff(self.artifact_handler)
        self.conflict_resolver = ConflictResolver(self.artifact_handler)

        # Initialize session state if not exists
        if "typed_artifacts" not in st.session_state:
            st.session_state.typed_artifacts = {
                "artifacts": {},
                "handoff_history": [],
                "conflict_history": [],
                "active_workflow": None,
            }

    def create_artifact_from_agent_output(
        self,
        agent_id: str,
        agent_output: str,
        artifact_type: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Create a typed artifact from agent output.

        Args:
            agent_id: ID of the agent creating the artifact
            agent_output: Raw output from the agent
            artifact_type: Type of artifact to create
            context: Additional context for artifact creation

        Returns:
            Dictionary with artifact creation result and metadata
        """

        try:
            # Parse agent output into structured data
            artifact_data = self._parse_agent_output(
                agent_output, artifact_type, context
            )

            # Create the artifact
            result = self.artifact_handler.create_artifact(
                agent_output=artifact_data,
                artifact_type=artifact_type,
                agent_id=agent_id,
            )

            if "error" not in result:
                # Store in session state
                artifact_id = result["artifact"]["artifact_id"]
                st.session_state.typed_artifacts["artifacts"][artifact_id] = result

                # Log success
                logger.info(
                    f"Created {artifact_type} artifact {artifact_id} from {agent_id}"
                )

                return {
                    "success": True,
                    "artifact_id": artifact_id,
                    "artifact": result["artifact"],
                    "confidence": result["confidence_metrics"]["overall_confidence"],
                    "quality_score": result["validation_result"]["quality_score"],
                    "impact_analysis": result["impact_analysis"],
                }
            else:
                logger.error(f"Artifact creation failed: {result['error_details']}")
                return {
                    "success": False,
                    "error": result["error"],
                    "details": result["error_details"],
                }

        except Exception as e:
            logger.error(f"Exception in artifact creation: {e}")
            return {"success": False, "error": "creation_exception", "details": str(e)}

    def validate_agent_handoff(
        self, from_agent: str, to_agent: str, artifacts: List[str]
    ) -> Dict[str, Any]:
        """
        Validate a proposed handoff between agents.

        Args:
            from_agent: Source agent
            to_agent: Target agent
            artifacts: Artifact IDs to hand off

        Returns:
            Handoff validation result
        """

        result = self.handoff_protocol.validate_handoff(from_agent, to_agent, artifacts)

        # Store in session state
        st.session_state.typed_artifacts["handoff_history"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "from_agent": from_agent,
                "to_agent": to_agent,
                "artifacts": artifacts,
                "result": result.dict(),
            }
        )

        return {
            "is_valid": result.status == "validated",
            "status": result.status,
            "validated_artifacts": result.validated_artifacts,
            "rejected_artifacts": result.rejected_artifacts,
            "errors": result.validation_errors,
            "recommendations": result.recommendations,
        }

    def detect_and_resolve_conflicts(self, artifact_ids: List[str]) -> Dict[str, Any]:
        """
        Detect and resolve conflicts between artifacts.

        Args:
            artifact_ids: List of artifact IDs to check for conflicts

        Returns:
            Conflict detection and resolution results
        """

        # Detect conflicts
        conflicts = self.conflict_resolver.detect_conflicts(artifact_ids)

        resolution_results = []

        if conflicts:
            # Store conflicts in session state
            for conflict in conflicts:
                st.session_state.typed_artifacts["conflict_history"].append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "conflict": conflict.dict(),
                    }
                )

            # Attempt automatic resolution for low/medium severity conflicts
            auto_resolvable = [c for c in conflicts if c.severity in ["low", "medium"]]

            for conflict in auto_resolvable:
                resolution = self.conflict_resolver.resolve_artifacts(
                    conflict.artifact_ids
                )
                resolution_results.append(resolution.dict())

        return {
            "conflicts_found": len(conflicts),
            "conflicts": [c.dict() for c in conflicts],
            "auto_resolved": len(resolution_results),
            "resolutions": resolution_results,
            "requires_manual_review": len(
                [c for c in conflicts if c.severity in ["high", "critical"]]
            ),
        }

    def get_artifact_lineage(self, artifact_id: str) -> Dict[str, Any]:
        """Get complete lineage information for an artifact"""

        artifact = self.artifact_handler.get_artifact(artifact_id)
        lineage = self.artifact_handler.get_lineage(artifact_id)

        if not artifact or not lineage:
            return {"found": False}

        return {
            "found": True,
            "artifact": artifact.dict(),
            "lineage": lineage.dict(),
            "dependencies": artifact.dependencies,
            "created_by": artifact.created_by,
            "confidence": artifact.confidence,
        }

    def get_workflow_suggestions(self) -> List[Dict[str, Any]]:
        """Get workflow suggestions based on current artifacts"""

        all_artifacts = list(st.session_state.typed_artifacts["artifacts"].keys())

        if not all_artifacts:
            return []

        return self.handoff_protocol.suggest_workflow(all_artifacts)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics about the artifact system"""

        artifacts = st.session_state.typed_artifacts["artifacts"]
        handoff_history = st.session_state.typed_artifacts["handoff_history"]
        conflict_history = st.session_state.typed_artifacts["conflict_history"]

        # Artifact metrics
        artifact_metrics = {
            "total_artifacts": len(artifacts),
            "by_type": {},
            "by_agent": {},
            "avg_confidence": 0.0,
            "avg_quality": 0.0,
        }

        if artifacts:
            confidences = []
            qualities = []

            for artifact_data in artifacts.values():
                artifact = artifact_data["artifact"]
                artifact_type = artifact["artifact_type"]
                created_by = artifact["created_by"]

                # Count by type
                artifact_metrics["by_type"][artifact_type] = (
                    artifact_metrics["by_type"].get(artifact_type, 0) + 1
                )

                # Count by agent
                artifact_metrics["by_agent"][created_by] = (
                    artifact_metrics["by_agent"].get(created_by, 0) + 1
                )

                # Collect confidence and quality scores
                confidences.append(
                    artifact_data["confidence_metrics"]["overall_confidence"]
                )
                qualities.append(artifact_data["validation_result"]["quality_score"])

            artifact_metrics["avg_confidence"] = sum(confidences) / len(confidences)
            artifact_metrics["avg_quality"] = sum(qualities) / len(qualities)

        # Handoff metrics
        handoff_metrics = {
            "total_handoffs": len(handoff_history),
            "successful_handoffs": len(
                [h for h in handoff_history if h["result"]["status"] == "validated"]
            ),
            "most_common_handoffs": {},
        }

        if handoff_history:
            handoff_metrics["success_rate"] = (
                handoff_metrics["successful_handoffs"]
                / handoff_metrics["total_handoffs"]
            )

            # Count handoff patterns
            for handoff in handoff_history:
                pattern = f"{handoff['from_agent']} → {handoff['to_agent']}"
                handoff_metrics["most_common_handoffs"][pattern] = (
                    handoff_metrics["most_common_handoffs"].get(pattern, 0) + 1
                )

        # Conflict metrics
        conflict_metrics = {
            "total_conflicts": len(conflict_history),
            "by_type": {},
            "by_severity": {},
        }

        for conflict_record in conflict_history:
            conflict = conflict_record["conflict"]
            conflict_type = conflict["conflict_type"]
            severity = conflict["severity"]

            conflict_metrics["by_type"][conflict_type] = (
                conflict_metrics["by_type"].get(conflict_type, 0) + 1
            )
            conflict_metrics["by_severity"][severity] = (
                conflict_metrics["by_severity"].get(severity, 0) + 1
            )

        return {
            "artifacts": artifact_metrics,
            "handoffs": handoff_metrics,
            "conflicts": conflict_metrics,
            "system_health": self._calculate_system_health(
                artifact_metrics, handoff_metrics, conflict_metrics
            ),
        }

    def _parse_agent_output(
        self, agent_output: str, artifact_type: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Parse agent output into structured artifact data"""

        # Basic parsing logic - in practice, this would be more sophisticated
        artifact_data = {
            "title": f"Generated {artifact_type}",
            "description": agent_output[:500] + "..."
            if len(agent_output) > 500
            else agent_output,
            "created_at": datetime.now(),
            "tags": context.get("tags", []) if context else [],
        }

        # Type-specific parsing
        if artifact_type == "SpecDoc":
            artifact_data.update(
                {
                    "objective": f"Objective derived from agent output: {agent_output[:200]}...",
                    "scope": "Scope to be defined based on requirements",
                    "functional_requirements": [
                        {
                            "id": "REQ-001",
                            "title": "Generated Requirement",
                            "description": "Requirement extracted from agent output",
                            "priority": "medium",
                        }
                    ],
                    "acceptance_criteria": ["Acceptance criteria to be refined"],
                }
            )

        elif artifact_type == "CodePatch":
            artifact_data.update(
                {
                    "task_id": context.get("task_id", "TASK-AUTO"),
                    "base_commit": "HEAD",
                    "files_changed": [
                        {
                            "path": "src/generated.js",
                            "action": "modified",
                            "lines_added": 50,
                            "lines_removed": 10,
                            "language": "javascript",
                        }
                    ],
                    "diff_unified": f"// Generated code patch\n{agent_output}",
                    "language": context.get("language", "javascript"),
                    "impact": ["codebase"],
                }
            )

        elif artifact_type == "TestPlan":
            artifact_data.update(
                {
                    "objective": "Test plan generated from agent analysis",
                    "scope": "Comprehensive testing of generated components",
                    "test_strategy": "Automated and manual testing approach",
                    "test_cases": [
                        {
                            "id": "TC-001",
                            "title": "Generated Test Case",
                            "description": "Test case based on agent output",
                            "prerequisites": ["System setup"],
                            "steps": ["Execute test"],
                            "expected_result": "Test passes",
                            "priority": "medium",
                            "category": "functional",
                        }
                    ],
                }
            )

        return artifact_data

    def _calculate_system_health(
        self, artifact_metrics: Dict, handoff_metrics: Dict, conflict_metrics: Dict
    ) -> Dict[str, Any]:
        """Calculate overall system health score"""

        health_score = 1.0
        issues = []

        # Check artifact quality
        if artifact_metrics["avg_quality"] < 0.7:
            health_score -= 0.2
            issues.append("Low average artifact quality")

        # Check handoff success rate
        if handoff_metrics.get("success_rate", 1.0) < 0.8:
            health_score -= 0.3
            issues.append("Low handoff success rate")

        # Check conflict frequency
        if (
            conflict_metrics["total_conflicts"]
            > artifact_metrics["total_artifacts"] * 0.3
        ):
            health_score -= 0.2
            issues.append("High conflict frequency")

        # Check for critical conflicts
        critical_conflicts = conflict_metrics["by_severity"].get("critical", 0)
        if critical_conflicts > 0:
            health_score -= 0.3
            issues.append(f"{critical_conflicts} critical conflicts detected")

        health_score = max(0.0, health_score)

        return {
            "score": health_score,
            "level": "excellent"
            if health_score > 0.8
            else "good"
            if health_score > 0.6
            else "fair"
            if health_score > 0.4
            else "poor",
            "issues": issues,
            "recommendations": self._generate_health_recommendations(
                health_score, issues
            ),
        }

    def _generate_health_recommendations(
        self, health_score: float, issues: List[str]
    ) -> List[str]:
        """Generate recommendations for improving system health"""

        recommendations = []

        if health_score < 0.5:
            recommendations.append(
                "Consider reviewing agent configuration and training"
            )

        if "Low average artifact quality" in issues:
            recommendations.append(
                "Implement stricter validation rules and agent feedback"
            )

        if "Low handoff success rate" in issues:
            recommendations.append("Review handoff protocols and agent compatibility")

        if "High conflict frequency" in issues:
            recommendations.append(
                "Improve agent coordination and communication protocols"
            )

        if any("critical conflicts" in issue for issue in issues):
            recommendations.append(
                "Immediate manual review required for critical conflicts"
            )

        if not recommendations:
            recommendations.append(
                "System is operating well - maintain current practices"
            )

        return recommendations


def render_typed_artifacts_dashboard():
    """Render the typed artifacts dashboard in Streamlit"""

    st.header("🎯 Typed Artifact System")

    # Initialize orchestrator
    if "typed_orchestrator" not in st.session_state:
        st.session_state.typed_orchestrator = TypedArtifactOrchestrator()

    orchestrator = st.session_state.typed_orchestrator

    # Get current metrics
    metrics = orchestrator.get_system_metrics()

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Artifacts", metrics["artifacts"]["total_artifacts"])

    with col2:
        st.metric("Avg Quality", f"{metrics['artifacts']['avg_quality']:.2f}")

    with col3:
        st.metric(
            "Handoff Success", f"{metrics['handoffs'].get('success_rate', 1.0):.1%}"
        )

    with col4:
        st.metric("System Health", f"{metrics['system_health']['score']:.2f}")

    # System health indicator
    health = metrics["system_health"]
    health_color = {"excellent": "🟢", "good": "🟡", "fair": "🟠", "poor": "🔴"}.get(
        health["level"], "⚪"
    )

    st.markdown(
        f"**System Health:** {health_color} {health['level'].title()} ({health['score']:.2f})"
    )

    if health["issues"]:
        st.warning(
            "**Issues Detected:**\n"
            + "\n".join(f"• {issue}" for issue in health["issues"])
        )

    if health["recommendations"]:
        st.info(
            "**Recommendations:**\n"
            + "\n".join(f"• {rec}" for rec in health["recommendations"])
        )

    # Artifacts breakdown
    if metrics["artifacts"]["total_artifacts"] > 0:
        st.subheader("📊 Artifact Analytics")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**By Type:**")
            for artifact_type, count in metrics["artifacts"]["by_type"].items():
                st.write(f"• {artifact_type}: {count}")

        with col2:
            st.write("**By Agent:**")
            for agent, count in metrics["artifacts"]["by_agent"].items():
                st.write(f"• {agent}: {count}")

    # Recent activity
    st.subheader("🔄 Recent Activity")

    recent_artifacts = list(st.session_state.typed_artifacts["artifacts"].values())[-5:]
    if recent_artifacts:
        for artifact_data in recent_artifacts:
            artifact = artifact_data["artifact"]
            with st.expander(f"{artifact['artifact_type']}: {artifact['title']}"):
                st.write(f"**ID:** {artifact['artifact_id']}")
                st.write(f"**Created by:** {artifact['created_by']}")
                st.write(
                    f"**Confidence:** {artifact_data['confidence_metrics']['overall_confidence']:.2f}"
                )
                st.write(
                    f"**Quality:** {artifact_data['validation_result']['quality_score']:.2f}"
                )
    else:
        st.info("No artifacts created yet")

    # Workflow suggestions
    suggestions = orchestrator.get_workflow_suggestions()
    if suggestions:
        st.subheader("💡 Workflow Suggestions")
        for suggestion in suggestions:
            st.write(f"**Step {suggestion['step']}:** {suggestion['action']}")
            st.write(f"From {suggestion['from_agent']} → {suggestion['to_agent']}")
            st.write(f"Expected output: {', '.join(suggestion['expected_output'])}")
            st.write("---")


# Export the main integration class for use in the main app
__all__ = ["TypedArtifactOrchestrator", "render_typed_artifacts_dashboard"]

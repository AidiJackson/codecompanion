"""
Multi-Model Consensus Validation System

This module implements consensus-based validation using multiple AI models
with domain-specific expertise weighting and statistical significance testing.
"""

import logging
import numpy as np
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from uuid import uuid4
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class ValidationDomain(str, Enum):
    """Domain types for specialized validation"""

    SECURITY = "security"
    UI_DESIGN = "ui_design"
    TESTING = "testing"
    CODE_QUALITY = "code_quality"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"


class ConsensusMethod(str, Enum):
    """Methods for reaching consensus"""

    WEIGHTED_VOTING = "weighted_voting"
    MAJORITY_VOTE = "majority_vote"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    STATISTICAL_SIGNIFICANCE = "statistical_significance"
    HYBRID = "hybrid"


@dataclass
class ModelValidation:
    """Individual model validation result"""

    model_name: str
    domain: ValidationDomain
    confidence_score: float
    quality_score: float
    validation_text: str
    issues_found: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ConsensusResult:
    """Result of consensus validation"""

    artifact_id: str
    domain: ValidationDomain
    consensus_score: float
    final_quality_score: float
    validation_passed: bool
    consensus_method: ConsensusMethod
    model_validations: List[ModelValidation] = field(default_factory=list)
    consensus_issues: List[str] = field(default_factory=list)
    consensus_recommendations: List[str] = field(default_factory=list)
    statistical_metrics: Dict[str, float] = field(default_factory=dict)
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConsensusValidator:
    """
    Multi-model consensus validator with domain-specific expertise weighting
    and advanced statistical validation methods.
    """

    def __init__(self):
        # Domain-specific model expertise weights
        self.domain_weights = {
            ValidationDomain.SECURITY: {"gpt-4": 0.4, "claude": 0.4, "gemini": 0.2},
            ValidationDomain.UI_DESIGN: {"gpt-4": 0.5, "claude": 0.3, "gemini": 0.2},
            ValidationDomain.TESTING: {"gemini": 0.5, "gpt-4": 0.3, "claude": 0.2},
            ValidationDomain.CODE_QUALITY: {"claude": 0.4, "gpt-4": 0.4, "gemini": 0.2},
            ValidationDomain.DOCUMENTATION: {
                "gpt-4": 0.4,
                "claude": 0.4,
                "gemini": 0.2,
            },
            ValidationDomain.ARCHITECTURE: {"claude": 0.5, "gpt-4": 0.3, "gemini": 0.2},
            ValidationDomain.PERFORMANCE: {"gemini": 0.4, "gpt-4": 0.4, "claude": 0.2},
        }

        # Consensus thresholds by domain
        self.consensus_thresholds = {
            ValidationDomain.SECURITY: 0.9,
            ValidationDomain.UI_DESIGN: 0.8,
            ValidationDomain.TESTING: 0.85,
            ValidationDomain.CODE_QUALITY: 0.85,
            ValidationDomain.DOCUMENTATION: 0.75,
            ValidationDomain.ARCHITECTURE: 0.9,
            ValidationDomain.PERFORMANCE: 0.85,
        }

        # Statistical significance parameters
        self.min_models_required = 2
        self.significance_threshold = 0.05

        # Text similarity analyzer
        self.vectorizer = TfidfVectorizer(
            max_features=1000, stop_words="english", ngram_range=(1, 2)
        )

        # Validation history for learning
        self.validation_history: List[ConsensusResult] = []

        logger.info("Consensus Validator initialized with domain-specific weighting")

    async def validate_consensus(
        self,
        artifacts: List[Dict[str, Any]],
        domain: ValidationDomain,
        consensus_method: ConsensusMethod = ConsensusMethod.HYBRID,
    ) -> ConsensusResult:
        """
        Validate artifacts using multi-model consensus

        Args:
            artifacts: List of artifacts to validate
            domain: Domain type for specialized validation
            consensus_method: Method to use for reaching consensus

        Returns:
            ConsensusResult with validation outcome
        """

        start_time = datetime.now()

        if not artifacts:
            raise ValueError("No artifacts provided for validation")

        # For simplicity, validate the first artifact (extend for multiple)
        artifact = artifacts[0]
        artifact_id = artifact.get("id", f"artifact_{uuid4().hex[:8]}")

        logger.info(
            f"Starting consensus validation for artifact {artifact_id} in domain {domain.value}"
        )

        # Get model validations
        model_validations = await self._get_model_validations(artifact, domain)

        if len(model_validations) < self.min_models_required:
            raise ValueError(
                f"Insufficient model validations: {len(model_validations)} < {self.min_models_required}"
            )

        # Apply consensus method
        consensus_result = await self._apply_consensus_method(
            artifact_id, domain, model_validations, consensus_method
        )

        # Calculate processing time
        consensus_result.processing_time = (datetime.now() - start_time).total_seconds()

        # Store in validation history
        self.validation_history.append(consensus_result)

        logger.info(
            f"Consensus validation completed for {artifact_id}: "
            f"score={consensus_result.consensus_score:.3f}, "
            f"passed={consensus_result.validation_passed}"
        )

        return consensus_result

    async def _get_model_validations(
        self, artifact: Dict[str, Any], domain: ValidationDomain
    ) -> List[ModelValidation]:
        """Get validation results from multiple models"""

        available_models = list(self.domain_weights.get(domain, {}).keys())
        model_validations = []

        # Simulate model validations (in real implementation, would call actual models)
        for model_name in available_models:
            validation = await self._simulate_model_validation(
                artifact, model_name, domain
            )
            if validation:
                model_validations.append(validation)

        return model_validations

    async def _simulate_model_validation(
        self, artifact: Dict[str, Any], model_name: str, domain: ValidationDomain
    ) -> Optional[ModelValidation]:
        """
        Simulate model validation (replace with actual model calls)
        """

        try:
            # Simulate different model responses based on domain and model characteristics
            base_score = 0.8

            # Model-specific adjustments
            model_adjustments = {"gpt-4": 0.05, "claude": 0.03, "gemini": -0.02}

            # Domain-specific adjustments
            domain_adjustments = {
                ValidationDomain.SECURITY: -0.05,  # More conservative
                ValidationDomain.UI_DESIGN: 0.02,
                ValidationDomain.TESTING: 0.03,
                ValidationDomain.CODE_QUALITY: 0.01,
                ValidationDomain.DOCUMENTATION: 0.05,
                ValidationDomain.ARCHITECTURE: -0.03,
                ValidationDomain.PERFORMANCE: 0.0,
            }

            # Calculate scores
            confidence_score = min(
                1.0,
                max(
                    0.0,
                    base_score
                    + model_adjustments.get(model_name, 0)
                    + domain_adjustments.get(domain, 0)
                    + np.random.normal(0, 0.05),  # Add some variance
                ),
            )

            quality_score = min(
                1.0, max(0.0, confidence_score + np.random.normal(0, 0.03))
            )

            # Generate validation text
            validation_text = self._generate_validation_text(
                artifact, model_name, domain, quality_score
            )

            # Generate issues and recommendations
            issues_found = self._generate_issues(artifact, domain, quality_score)
            recommendations = self._generate_recommendations(
                artifact, domain, quality_score
            )

            return ModelValidation(
                model_name=model_name,
                domain=domain,
                confidence_score=confidence_score,
                quality_score=quality_score,
                validation_text=validation_text,
                issues_found=issues_found,
                recommendations=recommendations,
                metadata={
                    "artifact_type": artifact.get("type", "unknown"),
                    "content_length": len(str(artifact.get("content", ""))),
                },
            )

        except Exception as e:
            logger.error(f"Error simulating validation for {model_name}: {e}")
            return None

    def _generate_validation_text(
        self,
        artifact: Dict[str, Any],
        model_name: str,
        domain: ValidationDomain,
        quality_score: float,
    ) -> str:
        """Generate model-specific validation text"""

        artifact_type = artifact.get("type", "artifact")

        if quality_score >= 0.9:
            return (
                f"{model_name} validation: Excellent {artifact_type} quality in {domain.value} domain. "
                f"Well-structured with minimal issues identified."
            )
        elif quality_score >= 0.8:
            return (
                f"{model_name} validation: Good {artifact_type} quality in {domain.value} domain. "
                f"Some minor improvements recommended."
            )
        elif quality_score >= 0.7:
            return (
                f"{model_name} validation: Acceptable {artifact_type} quality in {domain.value} domain. "
                f"Several areas need attention."
            )
        else:
            return (
                f"{model_name} validation: Below standard {artifact_type} quality in {domain.value} domain. "
                f"Significant improvements required."
            )

    def _generate_issues(
        self, artifact: Dict[str, Any], domain: ValidationDomain, quality_score: float
    ) -> List[str]:
        """Generate domain-specific issues based on quality score"""

        issues = []

        if quality_score < 0.9:
            domain_issues = {
                ValidationDomain.SECURITY: [
                    "Potential security vulnerabilities detected",
                    "Input validation could be improved",
                    "Authentication mechanisms need review",
                ],
                ValidationDomain.UI_DESIGN: [
                    "Accessibility improvements needed",
                    "Inconsistent visual design elements",
                    "User experience could be enhanced",
                ],
                ValidationDomain.TESTING: [
                    "Test coverage could be improved",
                    "Edge cases not fully covered",
                    "Integration tests missing",
                ],
                ValidationDomain.CODE_QUALITY: [
                    "Code complexity could be reduced",
                    "Documentation could be more comprehensive",
                    "Some code smells detected",
                ],
                ValidationDomain.DOCUMENTATION: [
                    "Some sections lack detail",
                    "Examples could be more comprehensive",
                    "Cross-references could be improved",
                ],
                ValidationDomain.ARCHITECTURE: [
                    "Coupling between components could be reduced",
                    "Scalability concerns identified",
                    "Design patterns could be better utilized",
                ],
                ValidationDomain.PERFORMANCE: [
                    "Performance bottlenecks identified",
                    "Resource utilization could be optimized",
                    "Caching strategies could be improved",
                ],
            }

            # Select issues based on quality score
            num_issues = max(1, int((1 - quality_score) * 3))
            available_issues = domain_issues.get(
                domain, ["Generic quality issues found"]
            )
            issues = available_issues[:num_issues]

        return issues

    def _generate_recommendations(
        self, artifact: Dict[str, Any], domain: ValidationDomain, quality_score: float
    ) -> List[str]:
        """Generate domain-specific recommendations"""

        recommendations = []

        domain_recommendations = {
            ValidationDomain.SECURITY: [
                "Implement additional security headers",
                "Add input sanitization",
                "Consider using security scanning tools",
            ],
            ValidationDomain.UI_DESIGN: [
                "Improve color contrast ratios",
                "Add responsive design elements",
                "Implement user feedback mechanisms",
            ],
            ValidationDomain.TESTING: [
                "Add more unit tests",
                "Implement integration testing",
                "Consider property-based testing",
            ],
            ValidationDomain.CODE_QUALITY: [
                "Refactor complex methods",
                "Add inline documentation",
                "Consider using design patterns",
            ],
            ValidationDomain.DOCUMENTATION: [
                "Add more code examples",
                "Include architecture diagrams",
                "Improve API documentation",
            ],
            ValidationDomain.ARCHITECTURE: [
                "Apply dependency injection",
                "Consider microservices architecture",
                "Implement event-driven patterns",
            ],
            ValidationDomain.PERFORMANCE: [
                "Add performance monitoring",
                "Implement caching layers",
                "Optimize database queries",
            ],
        }

        # Select recommendations based on quality score
        if quality_score < 0.9:
            num_recommendations = max(1, int((1 - quality_score) * 2))
            available_recs = domain_recommendations.get(
                domain, ["Consider general improvements"]
            )
            recommendations = available_recs[:num_recommendations]

        return recommendations

    async def _apply_consensus_method(
        self,
        artifact_id: str,
        domain: ValidationDomain,
        model_validations: List[ModelValidation],
        consensus_method: ConsensusMethod,
    ) -> ConsensusResult:
        """Apply the specified consensus method"""

        if consensus_method == ConsensusMethod.WEIGHTED_VOTING:
            return await self._weighted_voting_consensus(
                artifact_id, domain, model_validations
            )
        elif consensus_method == ConsensusMethod.MAJORITY_VOTE:
            return await self._majority_vote_consensus(
                artifact_id, domain, model_validations
            )
        elif consensus_method == ConsensusMethod.SEMANTIC_SIMILARITY:
            return await self._semantic_similarity_consensus(
                artifact_id, domain, model_validations
            )
        elif consensus_method == ConsensusMethod.STATISTICAL_SIGNIFICANCE:
            return await self._statistical_significance_consensus(
                artifact_id, domain, model_validations
            )
        elif consensus_method == ConsensusMethod.HYBRID:
            return await self._hybrid_consensus(artifact_id, domain, model_validations)
        else:
            raise ValueError(f"Unsupported consensus method: {consensus_method}")

    async def _weighted_voting_consensus(
        self,
        artifact_id: str,
        domain: ValidationDomain,
        model_validations: List[ModelValidation],
    ) -> ConsensusResult:
        """Weighted voting by domain expertise"""

        weights = self.domain_weights.get(domain, {})

        # Calculate weighted scores
        weighted_quality_sum = 0.0
        weighted_confidence_sum = 0.0
        total_weight = 0.0

        for validation in model_validations:
            weight = weights.get(validation.model_name, 0.0)
            if weight > 0:
                weighted_quality_sum += validation.quality_score * weight
                weighted_confidence_sum += validation.confidence_score * weight
                total_weight += weight

        if total_weight == 0:
            raise ValueError("No valid model weights found for domain")

        final_quality_score = weighted_quality_sum / total_weight
        consensus_score = weighted_confidence_sum / total_weight

        # Determine if validation passed
        threshold = self.consensus_thresholds.get(domain, 0.85)
        validation_passed = final_quality_score >= threshold

        # Aggregate issues and recommendations
        all_issues = []
        all_recommendations = []
        for validation in model_validations:
            all_issues.extend(validation.issues_found)
            all_recommendations.extend(validation.recommendations)

        # Remove duplicates while preserving order
        consensus_issues = list(dict.fromkeys(all_issues))
        consensus_recommendations = list(dict.fromkeys(all_recommendations))

        return ConsensusResult(
            artifact_id=artifact_id,
            domain=domain,
            consensus_score=consensus_score,
            final_quality_score=final_quality_score,
            validation_passed=validation_passed,
            consensus_method=ConsensusMethod.WEIGHTED_VOTING,
            model_validations=model_validations,
            consensus_issues=consensus_issues,
            consensus_recommendations=consensus_recommendations,
            statistical_metrics={
                "total_weight": float(total_weight),
                "score_variance": float(
                    np.var([v.quality_score for v in model_validations])
                ),
                "confidence_variance": float(
                    np.var([v.confidence_score for v in model_validations])
                ),
            },
        )

    async def _majority_vote_consensus(
        self,
        artifact_id: str,
        domain: ValidationDomain,
        model_validations: List[ModelValidation],
    ) -> ConsensusResult:
        """Simple majority vote consensus"""

        threshold = self.consensus_thresholds.get(domain, 0.85)

        # Count votes
        pass_votes = sum(1 for v in model_validations if v.quality_score >= threshold)
        total_votes = len(model_validations)

        # Calculate average scores
        avg_quality = sum(v.quality_score for v in model_validations) / total_votes
        sum(v.confidence_score for v in model_validations) / total_votes

        # Majority decision
        validation_passed = pass_votes > (total_votes / 2)
        consensus_score = pass_votes / total_votes

        return ConsensusResult(
            artifact_id=artifact_id,
            domain=domain,
            consensus_score=consensus_score,
            final_quality_score=avg_quality,
            validation_passed=validation_passed,
            consensus_method=ConsensusMethod.MAJORITY_VOTE,
            model_validations=model_validations,
            statistical_metrics={
                "pass_votes": pass_votes,
                "total_votes": total_votes,
                "vote_ratio": pass_votes / total_votes,
            },
        )

    async def _semantic_similarity_consensus(
        self,
        artifact_id: str,
        domain: ValidationDomain,
        model_validations: List[ModelValidation],
    ) -> ConsensusResult:
        """Consensus based on semantic similarity of validation texts"""

        validation_texts = [v.validation_text for v in model_validations]

        if len(validation_texts) < 2:
            # Fall back to simple average
            avg_quality = sum(v.quality_score for v in model_validations) / len(
                model_validations
            )
            return ConsensusResult(
                artifact_id=artifact_id,
                domain=domain,
                consensus_score=avg_quality,
                final_quality_score=avg_quality,
                validation_passed=avg_quality
                >= self.consensus_thresholds.get(domain, 0.85),
                consensus_method=ConsensusMethod.SEMANTIC_SIMILARITY,
                model_validations=model_validations,
            )

        try:
            # Calculate TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform(validation_texts)

            # Calculate pairwise cosine similarities
            similarities = cosine_similarity(tfidf_matrix)

            # Calculate average similarity (excluding diagonal)
            n = similarities.shape[0]
            total_similarity = (similarities.sum() - n) / (n * (n - 1))

            # Weight quality scores by semantic agreement
            weighted_scores = []
            for i, validation in enumerate(model_validations):
                # Calculate this validation's agreement with others
                agreement_score = (similarities[i].sum() - 1) / (n - 1)
                weighted_score = validation.quality_score * agreement_score
                weighted_scores.append(weighted_score)

            final_quality_score = float(
                sum(weighted_scores)
                / sum(similarities[i].sum() - 1 for i in range(n))
                * (n - 1)
            )
            consensus_score = float(total_similarity)

        except Exception as e:
            logger.warning(
                f"Error in semantic similarity analysis: {e}, falling back to average"
            )
            # Fall back to simple average
            final_quality_score = sum(v.quality_score for v in model_validations) / len(
                model_validations
            )
            consensus_score = final_quality_score
            total_similarity = 0.0

        validation_passed = bool(
            final_quality_score >= self.consensus_thresholds.get(domain, 0.85)
        )

        return ConsensusResult(
            artifact_id=artifact_id,
            domain=domain,
            consensus_score=consensus_score,
            final_quality_score=final_quality_score,
            validation_passed=validation_passed,
            consensus_method=ConsensusMethod.SEMANTIC_SIMILARITY,
            model_validations=model_validations,
            statistical_metrics={
                "avg_semantic_similarity": float(total_similarity),
                "similarity_threshold": 0.5,
            },
        )

    async def _statistical_significance_consensus(
        self,
        artifact_id: str,
        domain: ValidationDomain,
        model_validations: List[ModelValidation],
    ) -> ConsensusResult:
        """Statistical significance-based consensus"""

        quality_scores = [v.quality_score for v in model_validations]
        confidence_scores = [v.confidence_score for v in model_validations]

        # Basic statistical metrics
        mean_quality = np.mean(quality_scores)
        std_quality = np.std(quality_scores)
        np.mean(confidence_scores)
        np.std(confidence_scores)

        # Calculate confidence interval
        n = len(quality_scores)
        standard_error = std_quality / np.sqrt(n)
        confidence_interval = 1.96 * standard_error  # 95% CI

        # Check if scores are significantly above threshold
        threshold = self.consensus_thresholds.get(domain, 0.85)
        significantly_above_threshold = (mean_quality - confidence_interval) > threshold

        # Consensus score based on statistical confidence
        consensus_score = max(
            0.0, min(1.0, (mean_quality - threshold) / (1 - threshold))
        )

        validation_passed = significantly_above_threshold and mean_quality >= threshold

        return ConsensusResult(
            artifact_id=artifact_id,
            domain=domain,
            consensus_score=consensus_score,
            final_quality_score=mean_quality,
            validation_passed=validation_passed,
            consensus_method=ConsensusMethod.STATISTICAL_SIGNIFICANCE,
            model_validations=model_validations,
            statistical_metrics={
                "mean_quality": float(mean_quality),
                "std_quality": float(std_quality),
                "confidence_interval": float(confidence_interval),
                "sample_size": float(n),
                "significantly_above_threshold": float(significantly_above_threshold),
            },
        )

    async def _hybrid_consensus(
        self,
        artifact_id: str,
        domain: ValidationDomain,
        model_validations: List[ModelValidation],
    ) -> ConsensusResult:
        """Hybrid consensus combining multiple methods"""

        # Get results from different methods
        weighted_result = await self._weighted_voting_consensus(
            artifact_id, domain, model_validations
        )
        statistical_result = await self._statistical_significance_consensus(
            artifact_id, domain, model_validations
        )

        # Combine results
        combined_quality_score = (
            weighted_result.final_quality_score * 0.6
            + statistical_result.final_quality_score * 0.4
        )

        combined_consensus_score = (
            weighted_result.consensus_score * 0.6
            + statistical_result.consensus_score * 0.4
        )

        # Validation passes if both methods agree or combined score is high
        validation_passed = (
            weighted_result.validation_passed and statistical_result.validation_passed
        ) or combined_quality_score >= self.consensus_thresholds.get(domain, 0.85)

        # Combine statistical metrics
        combined_metrics = {
            **weighted_result.statistical_metrics,
            **statistical_result.statistical_metrics,
            "hybrid_combination": {
                "weighted_score": weighted_result.final_quality_score,
                "statistical_score": statistical_result.final_quality_score,
                "combined_score": combined_quality_score,
            },
        }

        return ConsensusResult(
            artifact_id=artifact_id,
            domain=domain,
            consensus_score=combined_consensus_score,
            final_quality_score=combined_quality_score,
            validation_passed=validation_passed,
            consensus_method=ConsensusMethod.HYBRID,
            model_validations=model_validations,
            consensus_issues=weighted_result.consensus_issues,
            consensus_recommendations=weighted_result.consensus_recommendations,
            statistical_metrics=combined_metrics,
        )

    def get_domain_expertise_weights(
        self, domain: ValidationDomain
    ) -> Dict[str, float]:
        """Get expertise weights for a specific domain"""
        return self.domain_weights.get(domain, {}).copy()

    def update_domain_weights(
        self, domain: ValidationDomain, new_weights: Dict[str, float]
    ) -> None:
        """Update expertise weights for a domain"""

        # Normalize weights to sum to 1.0
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            normalized_weights = {k: v / total_weight for k, v in new_weights.items()}
            self.domain_weights[domain] = normalized_weights
            logger.info(
                f"Updated domain weights for {domain.value}: {normalized_weights}"
            )

    def get_validation_history(
        self, domain: Optional[ValidationDomain] = None, limit: int = 100
    ) -> List[ConsensusResult]:
        """Get validation history, optionally filtered by domain"""

        history = self.validation_history[-limit:]

        if domain:
            history = [r for r in history if r.domain == domain]

        return history

    def get_consensus_statistics(self) -> Dict[str, Any]:
        """Get statistics about consensus validation performance"""

        if not self.validation_history:
            return {"total_validations": 0}

        # Basic statistics
        total_validations = len(self.validation_history)
        passed_validations = sum(
            1 for r in self.validation_history if r.validation_passed
        )
        avg_consensus_score = (
            sum(r.consensus_score for r in self.validation_history) / total_validations
        )
        avg_quality_score = (
            sum(r.final_quality_score for r in self.validation_history)
            / total_validations
        )
        avg_processing_time = (
            sum(r.processing_time for r in self.validation_history) / total_validations
        )

        # Domain distribution
        domain_counts = {}
        domain_pass_rates = {}

        for result in self.validation_history:
            domain = result.domain.value
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

            if domain not in domain_pass_rates:
                domain_pass_rates[domain] = {"passed": 0, "total": 0}

            domain_pass_rates[domain]["total"] += 1
            if result.validation_passed:
                domain_pass_rates[domain]["passed"] += 1

        # Calculate pass rates
        for domain in domain_pass_rates:
            stats = domain_pass_rates[domain]
            stats["pass_rate"] = (
                stats["passed"] / stats["total"] if stats["total"] > 0 else 0.0
            )

        return {
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "overall_pass_rate": passed_validations / total_validations,
            "avg_consensus_score": avg_consensus_score,
            "avg_quality_score": avg_quality_score,
            "avg_processing_time": avg_processing_time,
            "domain_distribution": domain_counts,
            "domain_pass_rates": domain_pass_rates,
        }

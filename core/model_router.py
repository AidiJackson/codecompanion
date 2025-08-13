"""
Intelligent Model Router with Learning and Optimization

Implements Thompson Sampling Bandit algorithm for adaptive model selection
based on outcome learning and cost governance.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Tuple
from dataclasses import dataclass, field
import sqlite3
from pathlib import Path

from schemas.routing import ModelType, TaskType
from schemas.outcomes import TaskOutcome
from core.bandit_learning import ThompsonSamplingBandit
from core.cost_governor import CostGovernor

logger = logging.getLogger(__name__)


@dataclass
class CapabilityVector:
    """Enhanced capability vector with learning weights"""

    model_type: ModelType
    base_capabilities: Dict[str, float] = field(default_factory=dict)
    learned_weights: Dict[str, float] = field(default_factory=dict)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

    def get_adjusted_capability(self, task_type: str, context: Dict[str, Any]) -> float:
        """Get capability score adjusted by learned weights"""
        base_score = self.base_capabilities.get(task_type, 0.5)
        learned_adjustment = self.learned_weights.get(task_type, 1.0)

        # Apply context-specific adjustments
        context_adjustment = self._get_context_adjustment(task_type, context)

        return min(1.0, base_score * learned_adjustment * context_adjustment)

    def _get_context_adjustment(self, task_type: str, context: Dict[str, Any]) -> float:
        """Calculate context-specific capability adjustments"""
        adjustment = 1.0

        # Adjust for complexity
        complexity = context.get("complexity", 0.5)
        if task_type in ["reasoning_long", "architecture"] and complexity > 0.7:
            adjustment *= 1.1  # Boost for high complexity reasoning

        # Adjust for time sensitivity
        if context.get("time_sensitive", False) and task_type in [
            "code_gen",
            "debugging",
        ]:
            adjustment *= 0.9  # Slight penalty for time pressure

        # Adjust for cost constraints
        if context.get("cost_sensitive", False):
            cost_efficiency = self.base_capabilities.get("cost", 0.5)
            adjustment *= 0.8 + 0.4 * cost_efficiency

        return adjustment


# TaskOutcome is now imported from schemas.outcomes


class IntelligentRouter:
    """
    Intelligent router with Thompson Sampling Bandit learning
    and multi-objective optimization
    """

    def __init__(self, db_path: str = "router_learning.db"):
        self.db_path = db_path
        self.capability_vectors = self._initialize_capability_vectors()
        self.bandit = ThompsonSamplingBandit()
        self.cost_governor = CostGovernor()
        # Performance tracker will be initialized externally to avoid circular imports

        # Learning parameters
        self.learning_rate = 0.1
        self.exploration_factor = 0.1
        self.quality_weight = 0.5
        self.cost_weight = 0.3
        self.latency_weight = 0.2

        # Initialize database
        self._init_database()

        logger.info("Intelligent router initialized with learning capabilities")

    def _initialize_capability_vectors(self) -> Dict[ModelType, CapabilityVector]:
        """Initialize base capability vectors for all models"""
        return {
            ModelType.CLAUDE_SONNET: CapabilityVector(
                model_type=ModelType.CLAUDE_SONNET,
                base_capabilities={
                    "reasoning_long": 0.95,
                    "architecture": 0.9,
                    "debugging": 0.85,
                    "code_review": 0.88,
                    "cost": 0.7,
                    "latency": 0.75,
                },
            ),
            ModelType.GPT4O: CapabilityVector(
                model_type=ModelType.GPT4O,
                base_capabilities={
                    "code_gen": 0.9,
                    "creativity": 0.95,
                    "ui_design": 0.85,
                    "documentation": 0.82,
                    "cost": 0.6,
                    "latency": 0.8,
                },
            ),
            ModelType.GEMINI_FLASH: CapabilityVector(
                model_type=ModelType.GEMINI_FLASH,
                base_capabilities={
                    "testing": 0.9,
                    "validation": 0.85,
                    "long_context": 0.95,
                    "code_backend": 0.8,
                    "cost": 0.9,
                    "latency": 0.9,
                },
            ),
            ModelType.GPT4_TURBO: CapabilityVector(
                model_type=ModelType.GPT4_TURBO,
                base_capabilities={
                    "code_gen": 0.88,
                    "reasoning_long": 0.85,
                    "debugging": 0.82,
                    "cost": 0.65,
                    "latency": 0.85,
                },
            ),
            ModelType.CLAUDE_HAIKU: CapabilityVector(
                model_type=ModelType.CLAUDE_HAIKU,
                base_capabilities={
                    "simple_tasks": 0.8,
                    "cost": 0.95,
                    "latency": 0.95,
                    "code_gen": 0.7,
                },
            ),
            ModelType.GEMINI_PRO: CapabilityVector(
                model_type=ModelType.GEMINI_PRO,
                base_capabilities={
                    "reasoning_long": 0.88,
                    "long_context": 0.98,
                    "multimodal": 0.9,
                    "cost": 0.8,
                    "latency": 0.7,
                },
            ),
        }

    def _init_database(self):
        """Initialize SQLite database for learning data"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE,
                    model_used TEXT,
                    task_type TEXT,
                    complexity_score REAL,
                    success BOOLEAN,
                    quality_score REAL,
                    execution_time REAL,
                    token_usage INTEGER,
                    cost REAL,
                    context TEXT,
                    timestamp DATETIME,
                    error_type TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS routing_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    selected_model TEXT,
                    routing_score REAL,
                    alternatives TEXT,
                    decision_factors TEXT,
                    timestamp DATETIME
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    model_type TEXT,
                    task_type TEXT,
                    avg_quality REAL,
                    avg_latency REAL,
                    avg_cost REAL,
                    success_rate REAL,
                    sample_count INTEGER,
                    last_updated DATETIME,
                    PRIMARY KEY (model_type, task_type)
                )
            """)

    def extract_features(self, task: Dict[str, Any]) -> Dict[str, float]:
        """Extract feature vector from task description and context"""
        description = task.get("description", "")
        context = task.get("context", {})

        features = {}

        # Text-based features
        features["description_length"] = min(1.0, len(description) / 1000)
        features["complexity_keywords"] = (
            self._count_complexity_keywords(description) / 10
        )
        features["code_keywords"] = self._count_code_keywords(description) / 10
        features["reasoning_keywords"] = (
            self._count_reasoning_keywords(description) / 10
        )

        # Context features
        features["time_sensitive"] = float(context.get("time_sensitive", False))
        features["cost_sensitive"] = float(context.get("cost_sensitive", False))
        features["quality_priority"] = context.get("quality_priority", 0.5)
        features["estimated_tokens"] = min(
            1.0, context.get("estimated_tokens", 1000) / 10000
        )

        # Task type indicators
        task_type = context.get("task_type")
        if task_type:
            for t in TaskType:
                features[f"is_{t.value}"] = float(task_type == t)

        return features

    def _count_complexity_keywords(self, text: str) -> int:
        """Count complexity-indicating keywords"""
        keywords = [
            "complex",
            "advanced",
            "sophisticated",
            "intricate",
            "elaborate",
            "comprehensive",
            "detailed",
            "thorough",
            "extensive",
            "multi-step",
        ]
        return sum(1 for keyword in keywords if keyword.lower() in text.lower())

    def _count_code_keywords(self, text: str) -> int:
        """Count coding-related keywords"""
        keywords = [
            "code",
            "function",
            "class",
            "method",
            "api",
            "database",
            "algorithm",
            "implementation",
            "programming",
            "development",
        ]
        return sum(1 for keyword in keywords if keyword.lower() in text.lower())

    def _count_reasoning_keywords(self, text: str) -> int:
        """Count reasoning-related keywords"""
        keywords = [
            "analyze",
            "design",
            "plan",
            "strategy",
            "architecture",
            "evaluate",
            "assess",
            "consider",
            "research",
            "investigate",
            "think",
            "reason",
        ]
        return sum(1 for keyword in keywords if keyword.lower() in text.lower())

    def route_task(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route task to optimal model using learned weights and bandit optimization
        """
        features = self.extract_features(task)
        task_type = context.get("task_type", TaskType.REASONING_LONG)
        context.get("complexity", 0.5)

        # Check budget constraints
        project_complexity = context.get("project_complexity", "medium")
        current_usage = context.get("current_usage", {})

        if not self.cost_governor.check_budget(project_complexity, current_usage):
            logger.warning("Budget constraints violated, using cost-efficient model")
            return self._select_cost_efficient_model(features, context)

        # Get model scores using bandit algorithm
        model_scores = {}
        model_contexts = {}

        # Register all models with bandit if not already registered
        for model_type in self.capability_vectors.keys():
            self.bandit.register_arm(model_type.value)

        for model_type, capability_vector in self.capability_vectors.items():
            # Skip models that are over budget
            if not self.cost_governor.can_afford_model(model_type, context):
                continue

            # Get capability-based score
            capability_score = capability_vector.get_adjusted_capability(
                task_type.value, context
            )

            # Get Thompson Sampling exploration bonus
            try:
                selected_arm = self.bandit.select_arm(context=features)
                # If this model was selected by bandit, give it a bonus
                exploration_bonus = (
                    self.exploration_factor if selected_arm == model_type.value else 0.0
                )
            except Exception:
                exploration_bonus = self.exploration_factor * 0.5  # Default exploration

            # Multi-objective optimization
            quality_component = capability_score * self.quality_weight
            cost_component = (
                capability_vector.base_capabilities.get("cost", 0.5) * self.cost_weight
            )
            latency_component = (
                capability_vector.base_capabilities.get("latency", 0.5)
                * self.latency_weight
            )

            # Combine scores with exploration bonus
            final_score = (
                quality_component
                + cost_component
                + latency_component
                + exploration_bonus
            )

            model_scores[model_type] = final_score
            model_contexts[model_type] = {
                "capability_score": capability_score,
                "bandit_score": exploration_bonus,
                "quality_component": quality_component,
                "cost_component": cost_component,
                "latency_component": latency_component,
                "exploration_bonus": exploration_bonus,
            }

        # Select best model
        if not model_scores:
            raise ValueError("No models available within budget constraints")

        best_model = max(model_scores.items(), key=lambda x: x[1])[0]

        # Create routing decision
        routing_decision = {
            "selected_model": best_model,
            "routing_score": model_scores[best_model],
            "alternatives": sorted(
                [(k, v) for k, v in model_scores.items() if k != best_model],
                key=lambda x: x[1],
                reverse=True,
            )[:3],  # Top 3 alternatives
            "decision_factors": model_contexts[best_model],
            "features": features,
            "context": context,
            "timestamp": datetime.now(),
        }

        # Store routing decision
        self._store_routing_decision(routing_decision)

        logger.info(
            f"Routed task to {best_model.value} with score {model_scores[best_model]:.3f}"
        )

        return routing_decision

    def _select_cost_efficient_model(
        self, features: Dict[str, float], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select most cost-efficient model when budget is constrained"""
        cost_efficient_models = [ModelType.CLAUDE_HAIKU, ModelType.GEMINI_FLASH]

        best_model = cost_efficient_models[0]
        for model in cost_efficient_models:
            if model in self.capability_vectors:
                best_model = model
                break

        return {
            "selected_model": best_model,
            "routing_score": 0.6,  # Moderate score for cost-efficient fallback
            "alternatives": [],
            "decision_factors": {"reason": "budget_constraint"},
            "features": features,
            "context": context,
            "timestamp": datetime.now(),
        }

    def update_from_outcome(self, task_id: str, outcome: TaskOutcome):
        """Update learning from task outcome"""
        try:
            # Update bandit algorithm
            reward = self._calculate_reward(outcome)
            self.bandit.update_arm(outcome.model_used.value, reward, outcome.context)

            # Update capability vectors
            self._update_capability_vectors(outcome)

            # Store outcome for analysis
            self._store_outcome(outcome)

            # Performance tracking handled externally

            logger.info(f"Updated learning from outcome: {task_id} -> {reward:.3f}")

        except Exception as e:
            logger.error(f"Failed to update from outcome {task_id}: {e}")

    def _calculate_reward(self, outcome: TaskOutcome) -> float:
        """Calculate reward signal for learning"""
        if not outcome.success:
            return 0.1  # Small positive reward to avoid complete avoidance

        # Multi-objective reward combining quality, cost efficiency, and speed
        quality_reward = outcome.quality_score

        # Cost efficiency (inverse of cost, normalized)
        expected_cost = outcome.token_usage * 0.001  # Rough baseline
        cost_efficiency = min(1.0, expected_cost / max(outcome.cost, 0.001))

        # Speed efficiency (inverse of time, with reasonable bounds)
        max_reasonable_time = 120.0  # 2 minutes
        speed_efficiency = min(
            1.0, max_reasonable_time / max(outcome.execution_time, 1.0)
        )

        # Weighted combination
        reward = quality_reward * 0.6 + cost_efficiency * 0.2 + speed_efficiency * 0.2

        return max(0.0, min(1.0, reward))

    def _update_capability_vectors(self, outcome: TaskOutcome):
        """Update capability vectors based on outcome"""
        model_vector = self.capability_vectors.get(outcome.model_used)
        if not model_vector:
            return

        task_type = outcome.task_type.value

        # Calculate performance score
        performance_score = self._calculate_reward(outcome)

        # Update learned weights with exponential moving average
        current_weight = model_vector.learned_weights.get(task_type, 1.0)
        updated_weight = (
            (1 - self.learning_rate) * current_weight
            + self.learning_rate * performance_score * 2  # Scale to [0, 2] range
        )

        model_vector.learned_weights[task_type] = max(0.1, min(2.0, updated_weight))
        model_vector.last_updated = datetime.now()

        logger.debug(
            f"Updated {outcome.model_used.value} weight for {task_type}: "
            f"{current_weight:.3f} -> {updated_weight:.3f}"
        )

    def _store_routing_decision(self, decision: Dict[str, Any]):
        """Store routing decision in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO routing_decisions 
                    (task_id, selected_model, routing_score, alternatives, 
                     decision_factors, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        decision.get("task_id", "unknown"),
                        decision["selected_model"].value,
                        decision["routing_score"],
                        json.dumps([(k.value, v) for k, v in decision["alternatives"]]),
                        json.dumps(decision["decision_factors"]),
                        decision["timestamp"],
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to store routing decision: {e}")

    def _store_outcome(self, outcome: TaskOutcome):
        """Store task outcome in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO task_outcomes 
                    (task_id, model_used, task_type, complexity_score, success,
                     quality_score, execution_time, token_usage, cost, context,
                     timestamp, error_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        outcome.task_id,
                        outcome.model_used.value,
                        outcome.task_type.value,
                        outcome.complexity.get_complexity_score(),
                        outcome.success,
                        outcome.quality_score,
                        outcome.execution_time,
                        outcome.token_usage,
                        outcome.cost,
                        json.dumps(outcome.context),
                        outcome.timestamp,
                        outcome.error_type,
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to store outcome: {e}")

    def get_model_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all models"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT model_used, task_type,
                           AVG(quality_score) as avg_quality,
                           AVG(execution_time) as avg_time,
                           AVG(cost) as avg_cost,
                           AVG(CAST(success AS FLOAT)) as success_rate,
                           COUNT(*) as sample_count
                    FROM task_outcomes
                    WHERE timestamp > datetime('now', '-30 days')
                    GROUP BY model_used, task_type
                """)

                results = cursor.fetchall()

                summary = {}
                for row in results:
                    model = row[0]
                    if model not in summary:
                        summary[model] = {}

                    summary[model][row[1]] = {
                        "avg_quality": row[2],
                        "avg_time": row[3],
                        "avg_cost": row[4],
                        "success_rate": row[5],
                        "sample_count": row[6],
                    }

                return summary

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}

    async def optimize_selection(self, features: Dict[str, float]) -> ModelType:
        """Advanced optimization using learned performance data"""
        # This is a simplified version - in practice, this could use
        # more sophisticated ML techniques like neural networks or
        # ensemble methods

        task_context = {"features": features, "timestamp": datetime.now()}

        # Use the main routing logic
        routing_decision = self.route_task({"context": task_context}, task_context)
        return routing_decision["selected_model"]

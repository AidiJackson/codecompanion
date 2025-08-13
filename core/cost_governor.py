"""
Cost Governance System for Budget Management

Implements budget controls, cost tracking, and spending optimization
across different project complexities and model usage patterns.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from pathlib import Path

from schemas.routing import ModelType

logger = logging.getLogger(__name__)


class ProjectComplexity(str, Enum):
    """Project complexity levels for budget allocation"""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


@dataclass
class BudgetLimits:
    """Budget limits for different project types"""

    max_tokens: int
    max_agents: int
    max_cost_usd: float
    max_requests: int
    time_window_hours: int = 24

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "max_agents": self.max_agents,
            "max_cost_usd": self.max_cost_usd,
            "max_requests": self.max_requests,
            "time_window_hours": self.time_window_hours,
        }


@dataclass
class UsageMetrics:
    """Current usage metrics for tracking"""

    tokens_used: int = 0
    agents_active: int = 0
    cost_incurred: float = 0.0
    requests_made: int = 0
    period_start: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tokens_used": self.tokens_used,
            "agents_active": self.agents_active,
            "cost_incurred": self.cost_incurred,
            "requests_made": self.requests_made,
            "period_start": self.period_start.isoformat(),
        }

    def reset(self):
        """Reset usage metrics for new period"""
        self.tokens_used = 0
        self.agents_active = 0
        self.cost_incurred = 0.0
        self.requests_made = 0
        self.period_start = datetime.now()


class CostGovernor:
    """
    Cost governance system that manages budgets and prevents overspending
    """

    def __init__(self, db_path: str = "cost_governance.db"):
        self.db_path = db_path

        # Default budget configurations
        self.budgets = {
            ProjectComplexity.SIMPLE: BudgetLimits(
                max_tokens=50000, max_agents=2, max_cost_usd=5.0, max_requests=100
            ),
            ProjectComplexity.MEDIUM: BudgetLimits(
                max_tokens=200000, max_agents=3, max_cost_usd=25.0, max_requests=300
            ),
            ProjectComplexity.COMPLEX: BudgetLimits(
                max_tokens=500000, max_agents=5, max_cost_usd=75.0, max_requests=750
            ),
            ProjectComplexity.ENTERPRISE: BudgetLimits(
                max_tokens=2000000, max_agents=8, max_cost_usd=300.0, max_requests=2000
            ),
        }

        # Model cost mapping (per 1K tokens)
        self.model_costs = {
            ModelType.CLAUDE_SONNET: 0.003,
            ModelType.CLAUDE_HAIKU: 0.0005,
            ModelType.GPT4O: 0.005,
            ModelType.GPT4_TURBO: 0.003,
            ModelType.GEMINI_FLASH: 0.0002,
            ModelType.GEMINI_PRO: 0.001,
        }

        # Current usage tracking
        self.current_usage: Dict[str, UsageMetrics] = {}
        self.cost_alerts_sent: Dict[str, List[datetime]] = {}

        # Initialize database
        self._init_database()

        logger.info("Cost Governor initialized with budget controls")

    def _init_database(self):
        """Initialize SQLite database for cost tracking"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    model_type TEXT,
                    tokens_used INTEGER,
                    cost_incurred REAL,
                    complexity_level TEXT,
                    timestamp DATETIME,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS budget_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    violation_type TEXT,
                    budget_limit REAL,
                    actual_usage REAL,
                    timestamp DATETIME,
                    action_taken TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_optimizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    original_model TEXT,
                    optimized_model TEXT,
                    estimated_savings REAL,
                    timestamp DATETIME,
                    reason TEXT
                )
            """)

    def check_budget(
        self,
        project_complexity: str,
        current_usage: Dict[str, Any],
        project_id: str = "default",
    ) -> bool:
        """
        Check if current usage is within budget limits

        Args:
            project_complexity: Project complexity level
            current_usage: Current usage metrics
            project_id: Project identifier for tracking

        Returns:
            True if within budget, False otherwise
        """
        try:
            complexity = ProjectComplexity(project_complexity)
            budget = self.budgets[complexity]

            # Get or create usage metrics
            if project_id not in self.current_usage:
                self.current_usage[project_id] = UsageMetrics()

            usage = self.current_usage[project_id]

            # Update usage from current data
            usage.tokens_used = current_usage.get("tokens_used", usage.tokens_used)
            usage.cost_incurred = current_usage.get(
                "cost_incurred", usage.cost_incurred
            )
            usage.requests_made = current_usage.get(
                "requests_made", usage.requests_made
            )
            usage.agents_active = current_usage.get(
                "agents_active", usage.agents_active
            )

            # Check each budget constraint
            violations = []

            if usage.tokens_used > budget.max_tokens:
                violations.append(
                    f"Token limit exceeded: {usage.tokens_used}/{budget.max_tokens}"
                )

            if usage.cost_incurred > budget.max_cost_usd:
                violations.append(
                    f"Cost limit exceeded: ${usage.cost_incurred:.2f}/${budget.max_cost_usd}"
                )

            if usage.agents_active > budget.max_agents:
                violations.append(
                    f"Agent limit exceeded: {usage.agents_active}/{budget.max_agents}"
                )

            if usage.requests_made > budget.max_requests:
                violations.append(
                    f"Request limit exceeded: {usage.requests_made}/{budget.max_requests}"
                )

            # Log violations
            if violations:
                for violation in violations:
                    logger.warning(f"Budget violation for {project_id}: {violation}")
                    self._record_budget_violation(project_id, violation, budget, usage)

                # Send cost alert if not recently sent
                self._maybe_send_cost_alert(project_id, violations)

                return False

            return True

        except Exception as e:
            logger.error(f"Error checking budget: {e}")
            return True  # Fail open to avoid blocking legitimate usage

    def can_afford_model(
        self,
        model_type: ModelType,
        context: Dict[str, Any],
        project_id: str = "default",
    ) -> bool:
        """
        Check if a specific model can be afforded given current usage

        Args:
            model_type: Model to check affordability for
            context: Request context with estimated token usage
            project_id: Project identifier

        Returns:
            True if model is affordable, False otherwise
        """
        try:
            estimated_tokens = context.get("estimated_tokens", 1000)
            estimated_cost = self.estimate_cost(model_type, estimated_tokens)

            if project_id not in self.current_usage:
                self.current_usage[project_id] = UsageMetrics()

            usage = self.current_usage[project_id]
            projected_cost = usage.cost_incurred + estimated_cost

            # Get project complexity and budget
            complexity = ProjectComplexity(context.get("project_complexity", "medium"))
            budget = self.budgets[complexity]

            # Check if projected cost would exceed budget
            if projected_cost > budget.max_cost_usd:
                logger.info(
                    f"Model {model_type.value} not affordable: "
                    f"projected ${projected_cost:.3f} > budget ${budget.max_cost_usd}"
                )
                return False

            # Check token budget
            projected_tokens = usage.tokens_used + estimated_tokens
            if projected_tokens > budget.max_tokens:
                logger.info(
                    f"Model {model_type.value} would exceed token budget: "
                    f"projected {projected_tokens} > {budget.max_tokens}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking model affordability: {e}")
            return True  # Fail open

    def estimate_cost(self, model_type: ModelType, estimated_tokens: int) -> float:
        """Estimate cost for model and token usage"""
        cost_per_1k = self.model_costs.get(model_type, 0.003)  # Default fallback
        return (estimated_tokens / 1000.0) * cost_per_1k

    def record_usage(
        self,
        project_id: str,
        model_type: ModelType,
        tokens_used: int,
        actual_cost: float,
        complexity_level: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record actual usage for tracking and learning"""
        try:
            # Update current usage
            if project_id not in self.current_usage:
                self.current_usage[project_id] = UsageMetrics()

            usage = self.current_usage[project_id]
            usage.tokens_used += tokens_used
            usage.cost_incurred += actual_cost
            usage.requests_made += 1

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO usage_history 
                    (project_id, model_type, tokens_used, cost_incurred, 
                     complexity_level, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        project_id,
                        model_type.value,
                        tokens_used,
                        actual_cost,
                        complexity_level,
                        datetime.now().isoformat(),
                        json.dumps(metadata or {}),
                    ),
                )

            logger.debug(
                f"Recorded usage: {project_id} used {tokens_used} tokens "
                f"costing ${actual_cost:.3f} with {model_type.value}"
            )

        except Exception as e:
            logger.error(f"Failed to record usage: {e}")

    def suggest_cost_optimization(
        self, project_id: str, current_model: ModelType, context: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Suggest a more cost-effective model for the given context

        Returns:
            Suggested model or None if no better option
        """
        try:
            estimated_tokens = context.get("estimated_tokens", 1000)
            current_cost = self.estimate_cost(current_model, estimated_tokens)

            # Find cheaper alternatives
            alternatives = []
            for model, cost_per_1k in self.model_costs.items():
                if model == current_model:
                    continue

                alt_cost = self.estimate_cost(model, estimated_tokens)
                if alt_cost < current_cost * 0.8:  # Must be at least 20% cheaper
                    alternatives.append((model, alt_cost, current_cost - alt_cost))

            if not alternatives:
                return None

            # Sort by savings and pick the best
            alternatives.sort(key=lambda x: x[2], reverse=True)
            suggested_model, suggested_cost, savings = alternatives[0]

            # Record optimization suggestion
            self._record_cost_optimization(
                project_id, current_model, suggested_model, savings
            )

            logger.info(
                f"Cost optimization suggestion: {current_model.value} -> "
                f"{suggested_model.value} (saves ${savings:.3f})"
            )

            return suggested_model

        except Exception as e:
            logger.error(f"Error suggesting cost optimization: {e}")
            return None

    def get_usage_summary(self, project_id: str) -> Dict[str, Any]:
        """Get usage summary for a project"""
        try:
            if project_id not in self.current_usage:
                return {"error": "No usage data found"}

            usage = self.current_usage[project_id]

            # Get budget limits (assume medium complexity if not specified)
            budget = self.budgets[ProjectComplexity.MEDIUM]

            return {
                "current_usage": usage.to_dict(),
                "budget_limits": budget.to_dict(),
                "utilization": {
                    "tokens_percent": (usage.tokens_used / budget.max_tokens) * 100,
                    "cost_percent": (usage.cost_incurred / budget.max_cost_usd) * 100,
                    "requests_percent": (usage.requests_made / budget.max_requests)
                    * 100,
                },
                "time_remaining": self._calculate_time_remaining(usage, budget),
                "projected_overage": self._calculate_projected_overage(usage, budget),
            }

        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {"error": str(e)}

    def _record_budget_violation(
        self, project_id: str, violation: str, budget: BudgetLimits, usage: UsageMetrics
    ):
        """Record budget violation for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO budget_violations 
                    (project_id, violation_type, budget_limit, actual_usage,
                     timestamp, action_taken)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        project_id,
                        violation,
                        budget.max_cost_usd,  # Primary budget limit
                        usage.cost_incurred,
                        datetime.now().isoformat(),
                        "Request rejected",
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to record budget violation: {e}")

    def _record_cost_optimization(
        self,
        project_id: str,
        original_model: ModelType,
        optimized_model: ModelType,
        estimated_savings: float,
    ):
        """Record cost optimization suggestion"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO cost_optimizations 
                    (project_id, original_model, optimized_model, 
                     estimated_savings, timestamp, reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        project_id,
                        original_model.value,
                        optimized_model.value,
                        estimated_savings,
                        datetime.now().isoformat(),
                        "Cost optimization",
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to record cost optimization: {e}")

    def _maybe_send_cost_alert(self, project_id: str, violations: List[str]):
        """Send cost alert if not recently sent"""
        now = datetime.now()

        if project_id not in self.cost_alerts_sent:
            self.cost_alerts_sent[project_id] = []

        # Check if alert was sent in last hour
        recent_alerts = [
            alert_time
            for alert_time in self.cost_alerts_sent[project_id]
            if (now - alert_time).total_seconds() < 3600
        ]

        if not recent_alerts:
            logger.warning(f"COST ALERT for {project_id}: {violations}")
            self.cost_alerts_sent[project_id].append(now)

    def _calculate_time_remaining(
        self, usage: UsageMetrics, budget: BudgetLimits
    ) -> Dict[str, float]:
        """Calculate estimated time remaining in budget period"""
        time_elapsed = (datetime.now() - usage.period_start).total_seconds() / 3600
        time_total = budget.time_window_hours

        return {
            "hours_elapsed": time_elapsed,
            "hours_remaining": max(0, time_total - time_elapsed),
            "period_percent_elapsed": min(100, (time_elapsed / time_total) * 100),
        }

    def _calculate_projected_overage(
        self, usage: UsageMetrics, budget: BudgetLimits
    ) -> Dict[str, float]:
        """Calculate projected overage based on current burn rate"""
        time_elapsed = (datetime.now() - usage.period_start).total_seconds() / 3600

        if time_elapsed <= 0:
            return {"cost_overage": 0.0, "token_overage": 0}

        # Calculate burn rates
        cost_burn_rate = usage.cost_incurred / time_elapsed
        token_burn_rate = usage.tokens_used / time_elapsed

        # Project to end of budget period
        projected_cost = cost_burn_rate * budget.time_window_hours
        projected_tokens = int(token_burn_rate * budget.time_window_hours)

        return {
            "projected_cost": projected_cost,
            "projected_tokens": projected_tokens,
            "cost_overage": max(0, projected_cost - budget.max_cost_usd),
            "token_overage": max(0, projected_tokens - budget.max_tokens),
        }

    def reset_usage(self, project_id: str):
        """Reset usage metrics for a project"""
        if project_id in self.current_usage:
            self.current_usage[project_id].reset()
            logger.info(f"Reset usage metrics for project {project_id}")

    def set_custom_budget(
        self, complexity: ProjectComplexity, budget_limits: BudgetLimits
    ):
        """Set custom budget limits for a complexity level"""
        self.budgets[complexity] = budget_limits
        logger.info(f"Updated budget for {complexity.value}: {budget_limits.to_dict()}")

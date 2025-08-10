"""
Performance Tracking System for Model Router Learning

Tracks model performance metrics, analyzes outcomes, and provides
insights for continuous improvement of routing decisions.
"""

import logging
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import sqlite3
from pathlib import Path

from schemas.routing import ModelType, TaskType
from schemas.outcomes import TaskOutcome

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics for a model/task combination"""
    model_type: ModelType
    task_type: TaskType
    
    # Core metrics
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    
    # Quality metrics
    quality_scores: List[float] = field(default_factory=list)
    avg_quality: float = 0.0
    quality_std_dev: float = 0.0
    
    # Performance metrics
    execution_times: List[float] = field(default_factory=list)
    avg_execution_time: float = 0.0
    p95_execution_time: float = 0.0
    
    # Cost metrics
    costs: List[float] = field(default_factory=list)
    avg_cost: float = 0.0
    total_cost: float = 0.0
    
    # Token usage
    token_usage: List[int] = field(default_factory=list)
    avg_tokens: float = 0.0
    total_tokens: int = 0
    
    # Error analysis
    error_types: Dict[str, int] = field(default_factory=dict)
    
    # Temporal data
    first_task: Optional[datetime] = None
    last_task: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks
    
    @property 
    def cost_per_success(self) -> float:
        """Calculate average cost per successful task"""
        if self.successful_tasks == 0:
            return 0.0
        return self.total_cost / self.successful_tasks
    
    @property
    def tokens_per_success(self) -> float:
        """Calculate average tokens per successful task"""
        if self.successful_tasks == 0:
            return 0.0
        return self.total_tokens / self.successful_tasks
    
    def update_with_outcome(self, outcome: TaskOutcome):
        """Update metrics with new task outcome"""
        self.total_tasks += 1
        
        if outcome.success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1
            
            # Track error types
            if outcome.error_type:
                self.error_types[outcome.error_type] = (
                    self.error_types.get(outcome.error_type, 0) + 1
                )
        
        # Update quality metrics
        self.quality_scores.append(outcome.quality_score)
        self.avg_quality = statistics.mean(self.quality_scores)
        if len(self.quality_scores) > 1:
            self.quality_std_dev = statistics.stdev(self.quality_scores)
        
        # Update performance metrics
        self.execution_times.append(outcome.execution_time)
        self.avg_execution_time = statistics.mean(self.execution_times)
        if len(self.execution_times) >= 20:  # Need sufficient data for p95
            self.p95_execution_time = statistics.quantiles(
                sorted(self.execution_times), n=100
            )[94]  # 95th percentile
        
        # Update cost metrics
        self.costs.append(outcome.cost)
        self.avg_cost = statistics.mean(self.costs)
        self.total_cost += outcome.cost
        
        # Update token metrics
        self.token_usage.append(outcome.token_usage)
        self.avg_tokens = statistics.mean(self.token_usage)
        self.total_tokens += outcome.token_usage
        
        # Update temporal data
        if self.first_task is None:
            self.first_task = outcome.timestamp
        self.last_task = outcome.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization"""
        return {
            'model_type': self.model_type.value,
            'task_type': self.task_type.value,
            'total_tasks': self.total_tasks,
            'successful_tasks': self.successful_tasks,
            'failed_tasks': self.failed_tasks,
            'success_rate': self.success_rate,
            'avg_quality': self.avg_quality,
            'quality_std_dev': self.quality_std_dev,
            'avg_execution_time': self.avg_execution_time,
            'p95_execution_time': self.p95_execution_time,
            'avg_cost': self.avg_cost,
            'total_cost': self.total_cost,
            'cost_per_success': self.cost_per_success,
            'avg_tokens': self.avg_tokens,
            'total_tokens': self.total_tokens,
            'tokens_per_success': self.tokens_per_success,
            'error_types': self.error_types,
            'first_task': self.first_task.isoformat() if self.first_task else None,
            'last_task': self.last_task.isoformat() if self.last_task else None
        }


@dataclass
class TrendAnalysis:
    """Trend analysis for performance over time"""
    metric_name: str
    time_periods: List[datetime]
    values: List[float]
    trend_direction: str  # 'improving', 'declining', 'stable'
    trend_strength: float  # 0.0 to 1.0
    confidence_level: float  # Statistical confidence in trend
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'metric_name': self.metric_name,
            'trend_direction': self.trend_direction,
            'trend_strength': self.trend_strength,
            'confidence_level': self.confidence_level,
            'data_points': len(self.values),
            'time_span_days': (max(self.time_periods) - min(self.time_periods)).days if self.time_periods else 0
        }


class PerformanceTracker:
    """
    Comprehensive performance tracking for model router optimization
    """
    
    def __init__(self, db_path: str = "performance_tracking.db", 
                 max_history_days: int = 90):
        self.db_path = db_path
        self.max_history_days = max_history_days
        
        # In-memory performance metrics
        self.metrics: Dict[Tuple[ModelType, TaskType], PerformanceMetrics] = {}
        
        # Recent outcomes for trend analysis
        self.recent_outcomes: deque = deque(maxlen=1000)
        
        # Performance insights cache
        self.insights_cache: Dict[str, Any] = {}
        self.cache_expiry: Optional[datetime] = None
        
        # Initialize database
        self._init_database()
        self._load_recent_data()
        
        logger.info("Performance Tracker initialized")
    
    def _init_database(self):
        """Initialize SQLite database for performance tracking"""
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
                    error_type TEXT,
                    timestamp DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_type TEXT,
                    task_type TEXT,
                    metrics_data TEXT,
                    snapshot_date DATE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(model_type, task_type, snapshot_date)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS routing_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT,
                    model_type TEXT,
                    task_type TEXT,
                    insight_data TEXT,
                    confidence_score REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_model_task ON task_outcomes(model_used, task_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_timestamp ON task_outcomes(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_date ON performance_snapshots(snapshot_date)")
    
    def _load_recent_data(self):
        """Load recent performance data from database"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_history_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT model_used, task_type, success, quality_score,
                           execution_time, token_usage, cost, error_type, timestamp
                    FROM task_outcomes
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                """, (cutoff_date.isoformat(),))
                
                for row in cursor.fetchall():
                    try:
                        model_type = ModelType(row[0])
                        task_type = TaskType(row[1])
                        
                        # Create a simple complexity object for historical data
                        from schemas.routing import TaskComplexity
                        historical_complexity = TaskComplexity(
                            technical_complexity=0.5,
                            novelty=0.5,
                            safety_risk=0.0,
                            context_requirement=0.5,
                            interdependence=0.0,
                            estimated_tokens=1000,
                            requires_reasoning=False,
                            requires_creativity=False,
                            time_sensitive=False
                        )
                        
                        # Create outcome object
                        outcome = TaskOutcome(
                            task_id="historical",  # Historical data
                            model_used=model_type,
                            task_type=task_type,
                            complexity=historical_complexity,
                            success=bool(row[2]),
                            quality_score=row[3] or 0.0,
                            execution_time=row[4] or 0.0,
                            token_usage=row[5] or 0,
                            cost=row[6] or 0.0,
                            error_type=row[7],
                            timestamp=datetime.fromisoformat(row[8])
                        )
                        
                        # Update in-memory metrics
                        key = (model_type, task_type)
                        if key not in self.metrics:
                            self.metrics[key] = PerformanceMetrics(model_type, task_type)
                        
                        self.metrics[key].update_with_outcome(outcome)
                        self.recent_outcomes.append(outcome)
                        
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Skipping invalid historical record: {e}")
                        continue
                
                logger.info(f"Loaded {len(self.recent_outcomes)} recent outcomes from database")
                
        except Exception as e:
            logger.error(f"Failed to load recent data: {e}")
    
    def record_outcome(self, outcome: TaskOutcome):
        """Record a new task outcome"""
        try:
            # Store in database
            self._store_outcome_to_db(outcome)
            
            # Update in-memory metrics
            key = (outcome.model_used, outcome.task_type)
            if key not in self.metrics:
                self.metrics[key] = PerformanceMetrics(outcome.model_used, outcome.task_type)
            
            self.metrics[key].update_with_outcome(outcome)
            
            # Add to recent outcomes
            self.recent_outcomes.append(outcome)
            
            # Invalidate insights cache
            self.insights_cache.clear()
            self.cache_expiry = None
            
            logger.debug(f"Recorded outcome for {outcome.model_used.value} on {outcome.task_type.value}")
            
        except Exception as e:
            logger.error(f"Failed to record outcome: {e}")
    
    def _store_outcome_to_db(self, outcome: TaskOutcome):
        """Store outcome to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO task_outcomes 
                    (task_id, model_used, task_type, complexity_score, success,
                     quality_score, execution_time, token_usage, cost, 
                     context, error_type, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    outcome.task_id,
                    outcome.model_used.value,
                    outcome.task_type.value,
                    outcome.complexity.get_complexity_score() if outcome.complexity else 0.0,
                    outcome.success,
                    outcome.quality_score,
                    outcome.execution_time,
                    outcome.token_usage,
                    outcome.cost,
                    json.dumps(outcome.context),
                    outcome.error_type,
                    outcome.timestamp.isoformat()
                ))
        except Exception as e:
            logger.error(f"Failed to store outcome to database: {e}")
    
    def get_model_performance(self, model_type: Optional[ModelType] = None,
                             task_type: Optional[TaskType] = None) -> Dict[str, Any]:
        """Get performance metrics for specific model/task combinations"""
        results = {}
        
        for (m_type, t_type), metrics in self.metrics.items():
            if model_type and m_type != model_type:
                continue
            if task_type and t_type != task_type:
                continue
            
            key = f"{m_type.value}_{t_type.value}"
            results[key] = metrics.to_dict()
        
        return results
    
    def analyze_trends(self, days_back: int = 30) -> Dict[str, List[TrendAnalysis]]:
        """Analyze performance trends over time"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_outcomes = [
            outcome for outcome in self.recent_outcomes
            if outcome.timestamp >= cutoff_date
        ]
        
        if len(recent_outcomes) < 10:
            logger.warning("Insufficient data for trend analysis")
            return {}
        
        trends_by_model = defaultdict(list)
        
        # Group outcomes by model and analyze trends
        for model_type in ModelType:
            model_outcomes = [
                outcome for outcome in recent_outcomes
                if outcome.model_used == model_type
            ]
            
            if len(model_outcomes) < 5:
                continue
            
            # Sort by timestamp
            model_outcomes.sort(key=lambda x: x.timestamp)
            
            # Analyze different metrics
            metrics_to_analyze = [
                ('quality_score', [o.quality_score for o in model_outcomes]),
                ('execution_time', [o.execution_time for o in model_outcomes]),
                ('success_rate', self._calculate_rolling_success_rate(model_outcomes))
            ]
            
            for metric_name, values in metrics_to_analyze:
                if not values or len(values) < 5:
                    continue
                
                trend = self._calculate_trend(
                    metric_name,
                    [o.timestamp for o in model_outcomes],
                    values
                )
                
                if trend:
                    trends_by_model[model_type.value].append(trend)
        
        return dict(trends_by_model)
    
    def _calculate_rolling_success_rate(self, outcomes: List[TaskOutcome],
                                      window_size: int = 10) -> List[float]:
        """Calculate rolling success rate"""
        if len(outcomes) < window_size:
            return []
        
        rolling_rates = []
        for i in range(window_size - 1, len(outcomes)):
            window = outcomes[i - window_size + 1:i + 1]
            success_rate = sum(1 for o in window if o.success) / len(window)
            rolling_rates.append(success_rate)
        
        return rolling_rates
    
    def _calculate_trend(self, metric_name: str, timestamps: List[datetime],
                        values: List[float]) -> Optional[TrendAnalysis]:
        """Calculate trend analysis for a metric"""
        try:
            if len(values) < 5:
                return None
            
            # Convert timestamps to numeric values (days since first timestamp)
            time_numeric = [
                (ts - timestamps[0]).total_seconds() / 86400  # Convert to days
                for ts in timestamps
            ]
            
            # Simple linear regression to detect trend
            n = len(values)
            sum_x = sum(time_numeric)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(time_numeric, values))
            sum_x2 = sum(x * x for x in time_numeric)
            
            # Calculate slope (trend direction)
            denominator = n * sum_x2 - sum_x * sum_x
            if abs(denominator) < 1e-10:  # Avoid division by zero
                return None
            
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            
            # Calculate correlation coefficient (trend strength)
            mean_x = sum_x / n
            mean_y = sum_y / n
            
            numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(time_numeric, values))
            denom_x = sum((x - mean_x) ** 2 for x in time_numeric)
            denom_y = sum((y - mean_y) ** 2 for y in values)
            
            if denom_x <= 0 or denom_y <= 0:
                return None
            
            correlation = numerator / (denom_x * denom_y) ** 0.5
            
            # Determine trend direction
            if abs(slope) < 0.01:  # Threshold for "stable"
                direction = 'stable'
            elif slope > 0:
                direction = 'improving'
            else:
                direction = 'declining'
            
            # Calculate confidence based on correlation strength and data points
            confidence = min(1.0, abs(correlation) * (min(n, 50) / 50))
            
            return TrendAnalysis(
                metric_name=metric_name,
                time_periods=timestamps,
                values=values,
                trend_direction=direction,
                trend_strength=abs(correlation),
                confidence_level=confidence
            )
            
        except Exception as e:
            logger.error(f"Error calculating trend for {metric_name}: {e}")
            return None
    
    def generate_insights(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Generate performance insights and recommendations"""
        # Check cache
        if (not force_refresh and self.insights_cache and 
            self.cache_expiry and datetime.now() < self.cache_expiry):
            return self.insights_cache
        
        insights = {
            'summary': self._generate_summary_insights(),
            'model_recommendations': self._generate_model_recommendations(),
            'optimization_opportunities': self._generate_optimization_insights(),
            'quality_analysis': self._analyze_quality_patterns(),
            'cost_analysis': self._analyze_cost_patterns(),
            'generated_at': datetime.now().isoformat()
        }
        
        # Cache insights for 1 hour
        self.insights_cache = insights
        self.cache_expiry = datetime.now() + timedelta(hours=1)
        
        return insights
    
    def _generate_summary_insights(self) -> Dict[str, Any]:
        """Generate high-level summary insights"""
        if not self.metrics:
            return {'message': 'No performance data available'}
        
        total_tasks = sum(m.total_tasks for m in self.metrics.values())
        successful_tasks = sum(m.successful_tasks for m in self.metrics.values())
        total_cost = sum(m.total_cost for m in self.metrics.values())
        
        # Find best performing models
        best_quality = max(self.metrics.values(), key=lambda m: m.avg_quality)
        best_cost = min(self.metrics.values(), key=lambda m: m.cost_per_success or float('inf'))
        best_speed = min(self.metrics.values(), key=lambda m: m.avg_execution_time)
        
        return {
            'total_tasks_analyzed': total_tasks,
            'overall_success_rate': successful_tasks / total_tasks if total_tasks > 0 else 0,
            'total_cost': total_cost,
            'best_quality_model': f"{best_quality.model_type.value} for {best_quality.task_type.value}",
            'most_cost_efficient': f"{best_cost.model_type.value} for {best_cost.task_type.value}",
            'fastest_model': f"{best_speed.model_type.value} for {best_speed.task_type.value}",
            'data_freshness': max(m.last_task for m in self.metrics.values() if m.last_task).isoformat()
        }
    
    def _generate_model_recommendations(self) -> Dict[str, str]:
        """Generate model recommendations for different task types"""
        recommendations = {}
        
        for task_type in TaskType:
            task_metrics = [
                (m.model_type, m) for m in self.metrics.values()
                if m.task_type == task_type and m.total_tasks >= 3
            ]
            
            if not task_metrics:
                continue
            
            # Score models based on multiple factors
            scored_models = []
            for model_type, metrics in task_metrics:
                score = (
                    metrics.success_rate * 0.4 +
                    metrics.avg_quality * 0.3 +
                    (1.0 - min(1.0, metrics.cost_per_success / 10.0)) * 0.2 +
                    (1.0 - min(1.0, metrics.avg_execution_time / 120.0)) * 0.1
                )
                scored_models.append((model_type, score))
            
            if scored_models:
                best_model = max(scored_models, key=lambda x: x[1])
                recommendations[task_type.value] = best_model[0].value
        
        return recommendations
    
    def _generate_optimization_insights(self) -> List[Dict[str, Any]]:
        """Generate optimization opportunities"""
        opportunities = []
        
        for key, metrics in self.metrics.items():
            if metrics.total_tasks < 5:  # Need sufficient data
                continue
            
            # Low success rate opportunity
            if metrics.success_rate < 0.8:
                opportunities.append({
                    'type': 'success_rate_improvement',
                    'model': metrics.model_type.value,
                    'task_type': metrics.task_type.value,
                    'current_rate': metrics.success_rate,
                    'suggestion': 'Consider alternative model or adjust parameters'
                })
            
            # High cost opportunity
            if metrics.cost_per_success > 1.0:  # Threshold
                opportunities.append({
                    'type': 'cost_optimization',
                    'model': metrics.model_type.value,
                    'task_type': metrics.task_type.value,
                    'current_cost': metrics.cost_per_success,
                    'suggestion': 'Evaluate more cost-efficient alternatives'
                })
            
            # High variability in quality
            if metrics.quality_std_dev > 0.3:
                opportunities.append({
                    'type': 'consistency_improvement',
                    'model': metrics.model_type.value,
                    'task_type': metrics.task_type.value,
                    'quality_variance': metrics.quality_std_dev,
                    'suggestion': 'Quality varies significantly, investigate causes'
                })
        
        return opportunities[:10]  # Limit to top 10 opportunities
    
    def _analyze_quality_patterns(self) -> Dict[str, Any]:
        """Analyze quality score patterns"""
        all_quality_scores = []
        model_quality = defaultdict(list)
        
        for metrics in self.metrics.values():
            all_quality_scores.extend(metrics.quality_scores)
            model_quality[metrics.model_type.value].extend(metrics.quality_scores)
        
        if not all_quality_scores:
            return {'message': 'No quality data available'}
        
        return {
            'overall_avg_quality': statistics.mean(all_quality_scores),
            'overall_quality_std': statistics.stdev(all_quality_scores) if len(all_quality_scores) > 1 else 0,
            'model_quality_comparison': {
                model: {
                    'avg_quality': statistics.mean(scores),
                    'consistency': 1.0 - (statistics.stdev(scores) if len(scores) > 1 else 0)
                }
                for model, scores in model_quality.items()
                if len(scores) >= 3
            }
        }
    
    def _analyze_cost_patterns(self) -> Dict[str, Any]:
        """Analyze cost efficiency patterns"""
        model_costs = defaultdict(list)
        
        for metrics in self.metrics.values():
            if metrics.cost_per_success > 0:
                model_costs[metrics.model_type.value].append(metrics.cost_per_success)
        
        if not model_costs:
            return {'message': 'No cost data available'}
        
        return {
            'cost_efficiency_ranking': sorted(
                [(model, statistics.mean(costs)) for model, costs in model_costs.items()],
                key=lambda x: x[1]
            ),
            'cost_variability': {
                model: statistics.stdev(costs) if len(costs) > 1 else 0
                for model, costs in model_costs.items()
            }
        }
    
    def cleanup_old_data(self):
        """Clean up old performance data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_history_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM task_outcomes WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                deleted_count = cursor.rowcount
                
                conn.execute(
                    "DELETE FROM performance_snapshots WHERE snapshot_date < ?",
                    (cutoff_date.date(),)
                )
            
            logger.info(f"Cleaned up {deleted_count} old performance records")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
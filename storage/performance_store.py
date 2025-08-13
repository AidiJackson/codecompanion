"""
Performance Data Storage Layer

This module provides a comprehensive storage layer for performance data,
quality metrics, and learning outcomes with efficient querying capabilities.
"""

import logging
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Any, Optional
from uuid import uuid4
import numpy as np

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of performance metrics"""

    QUALITY_SCORE = "quality_score"
    PROCESSING_TIME = "processing_time"
    COST_EFFICIENCY = "cost_efficiency"
    USER_SATISFACTION = "user_satisfaction"
    ROUTING_ACCURACY = "routing_accuracy"
    CONSENSUS_SCORE = "consensus_score"
    CASCADE_EFFICIENCY = "cascade_efficiency"


class AggregationPeriod(str, Enum):
    """Time periods for metric aggregation"""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class PerformanceMetric:
    """Individual performance metric record"""

    metric_id: str
    metric_type: MetricType
    model_name: str
    task_type: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any]
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "metric_id": self.metric_id,
            "metric_type": self.metric_type.value,
            "model_name": self.model_name,
            "task_type": self.task_type,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": json.dumps(self.metadata),
            "correlation_id": self.correlation_id,
        }


@dataclass
class AggregatedMetrics:
    """Aggregated performance metrics"""

    model_name: str
    task_type: str
    metric_type: MetricType
    period: AggregationPeriod
    start_time: datetime
    end_time: datetime

    # Statistical measures
    mean_value: float
    median_value: float
    std_deviation: float
    min_value: float
    max_value: float
    sample_count: int

    # Percentiles
    percentile_25: float
    percentile_75: float
    percentile_95: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class PerformanceStore:
    """
    High-performance storage layer for performance metrics and analytics
    """

    def __init__(self, db_path: str = "performance_store.db"):
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Initialize SQLite database with performance-optimized schema"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Raw metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                metric_id TEXT PRIMARY KEY,
                metric_type TEXT NOT NULL,
                model_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                correlation_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Aggregated metrics table for faster queries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aggregated_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                period TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                mean_value REAL NOT NULL,
                median_value REAL NOT NULL,
                std_deviation REAL NOT NULL,
                min_value REAL NOT NULL,
                max_value REAL NOT NULL,
                sample_count INTEGER NOT NULL,
                percentile_25 REAL NOT NULL,
                percentile_75 REAL NOT NULL,
                percentile_95 REAL NOT NULL,
                computed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Model performance summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_performance_summary (
                model_name TEXT PRIMARY KEY,
                total_tasks INTEGER DEFAULT 0,
                avg_quality_score REAL DEFAULT 0.0,
                avg_processing_time REAL DEFAULT 0.0,
                success_rate REAL DEFAULT 0.0,
                total_cost REAL DEFAULT 0.0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Quality trends table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                trend_period TEXT NOT NULL,
                quality_score REAL NOT NULL,
                trend_direction TEXT, -- 'improving', 'declining', 'stable'
                trend_strength REAL, -- -1.0 to 1.0
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Learning outcomes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_outcomes (
                outcome_id TEXT PRIMARY KEY,
                routing_decision_id TEXT NOT NULL,
                expected_quality REAL NOT NULL,
                actual_quality REAL NOT NULL,
                prediction_error REAL NOT NULL,
                adaptation_applied BOOLEAN DEFAULT FALSE,
                outcome_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Performance optimization indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_metrics_model_task ON performance_metrics(model_name, task_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_metrics_type ON performance_metrics(metric_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_aggregated_period ON aggregated_metrics(period, start_time)"
        )

        conn.commit()
        conn.close()

        logger.info("Performance store database initialized")

    def store_metric(self, metric: PerformanceMetric) -> bool:
        """Store a single performance metric"""

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            metric_data = metric.to_dict()

            cursor.execute(
                """
                INSERT OR REPLACE INTO performance_metrics
                (metric_id, metric_type, model_name, task_type, value, timestamp, metadata, correlation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metric_data["metric_id"],
                    metric_data["metric_type"],
                    metric_data["model_name"],
                    metric_data["task_type"],
                    metric_data["value"],
                    metric_data["timestamp"],
                    metric_data["metadata"],
                    metric_data["correlation_id"],
                ),
            )

            conn.commit()
            conn.close()

            logger.debug(
                f"Stored metric: {metric.metric_type.value} = {metric.value} for {metric.model_name}"
            )
            return True

        except Exception as e:
            logger.error(f"Error storing metric: {e}")
            return False

    def store_metrics_batch(self, metrics: List[PerformanceMetric]) -> int:
        """Store multiple metrics in a single transaction"""

        if not metrics:
            return 0

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            metric_data = [metric.to_dict() for metric in metrics]

            cursor.executemany(
                """
                INSERT OR REPLACE INTO performance_metrics
                (metric_id, metric_type, model_name, task_type, value, timestamp, metadata, correlation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    (
                        data["metric_id"],
                        data["metric_type"],
                        data["model_name"],
                        data["task_type"],
                        data["value"],
                        data["timestamp"],
                        data["metadata"],
                        data["correlation_id"],
                    )
                    for data in metric_data
                ],
            )

            conn.commit()
            conn.close()

            logger.info(f"Stored {len(metrics)} metrics in batch")
            return len(metrics)

        except Exception as e:
            logger.error(f"Error storing metrics batch: {e}")
            return 0

    def get_metrics(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[PerformanceMetric]:
        """Retrieve metrics with optional filtering"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build dynamic query
        conditions = []
        params = []

        if model_name:
            conditions.append("model_name = ?")
            params.append(model_name)

        if task_type:
            conditions.append("task_type = ?")
            params.append(task_type)

        if metric_type:
            conditions.append("metric_type = ?")
            params.append(metric_type.value)

        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())

        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT metric_id, metric_type, model_name, task_type, value, timestamp, metadata, correlation_id
            FROM performance_metrics
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """

        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Convert to PerformanceMetric objects
        metrics = []
        for row in rows:
            metadata = json.loads(row[6]) if row[6] else {}

            metric = PerformanceMetric(
                metric_id=row[0],
                metric_type=MetricType(row[1]),
                model_name=row[2],
                task_type=row[3],
                value=row[4],
                timestamp=datetime.fromisoformat(row[5]),
                metadata=metadata,
                correlation_id=row[7],
            )
            metrics.append(metric)

        return metrics

    def compute_aggregated_metrics(
        self,
        period: AggregationPeriod,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AggregatedMetrics]:
        """Compute and store aggregated metrics for the specified period"""

        if not start_time:
            start_time = datetime.now(timezone.utc) - timedelta(days=7)
        if not end_time:
            end_time = datetime.now(timezone.utc)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get raw metrics for aggregation
        cursor.execute(
            """
            SELECT model_name, task_type, metric_type, value
            FROM performance_metrics
            WHERE timestamp >= ? AND timestamp <= ?
        """,
            (start_time.isoformat(), end_time.isoformat()),
        )

        raw_data = cursor.fetchall()

        if not raw_data:
            conn.close()
            return []

        # Group by model, task type, and metric type
        grouped_data = {}
        for row in raw_data:
            model_name, task_type, metric_type, value = row
            key = (model_name, task_type, metric_type)

            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(value)

        # Compute aggregated metrics
        aggregated_metrics = []

        for (model_name, task_type, metric_type), values in grouped_data.items():
            if len(values) < 2:  # Skip if insufficient data
                continue

            values = np.array(values)

            aggregated = AggregatedMetrics(
                model_name=model_name,
                task_type=task_type,
                metric_type=MetricType(metric_type),
                period=period,
                start_time=start_time,
                end_time=end_time,
                mean_value=float(np.mean(values)),
                median_value=float(np.median(values)),
                std_deviation=float(np.std(values)),
                min_value=float(np.min(values)),
                max_value=float(np.max(values)),
                sample_count=len(values),
                percentile_25=float(np.percentile(values, 25)),
                percentile_75=float(np.percentile(values, 75)),
                percentile_95=float(np.percentile(values, 95)),
            )

            aggregated_metrics.append(aggregated)

        # Store aggregated metrics
        for agg_metric in aggregated_metrics:
            cursor.execute(
                """
                INSERT OR REPLACE INTO aggregated_metrics
                (model_name, task_type, metric_type, period, start_time, end_time,
                 mean_value, median_value, std_deviation, min_value, max_value, sample_count,
                 percentile_25, percentile_75, percentile_95)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    agg_metric.model_name,
                    agg_metric.task_type,
                    agg_metric.metric_type.value,
                    agg_metric.period.value,
                    agg_metric.start_time.isoformat(),
                    agg_metric.end_time.isoformat(),
                    agg_metric.mean_value,
                    agg_metric.median_value,
                    agg_metric.std_deviation,
                    agg_metric.min_value,
                    agg_metric.max_value,
                    agg_metric.sample_count,
                    agg_metric.percentile_25,
                    agg_metric.percentile_75,
                    agg_metric.percentile_95,
                ),
            )

        conn.commit()
        conn.close()

        logger.info(
            f"Computed {len(aggregated_metrics)} aggregated metrics for {period.value} period"
        )
        return aggregated_metrics

    def get_model_performance_trends(
        self, model_name: Optional[str] = None, days_back: int = 30
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get performance trends for models"""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build query
        if model_name:
            query = """
                SELECT model_name, task_type, metric_type, value, timestamp
                FROM performance_metrics
                WHERE model_name = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            """
            params = [model_name, start_time.isoformat(), end_time.isoformat()]
        else:
            query = """
                SELECT model_name, task_type, metric_type, value, timestamp
                FROM performance_metrics
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY model_name, timestamp ASC
            """
            params = [start_time.isoformat(), end_time.isoformat()]

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Group trends by model
        trends = {}
        for row in rows:
            model, task_type, metric_type, value, timestamp = row

            if model not in trends:
                trends[model] = []

            trends[model].append(
                {
                    "task_type": task_type,
                    "metric_type": metric_type,
                    "value": value,
                    "timestamp": timestamp,
                }
            )

        return trends

    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get comprehensive quality statistics"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_metrics,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value
            FROM performance_metrics
            WHERE metric_type = 'quality_score'
        """)

        overall_stats = cursor.fetchone()

        # Per-model statistics
        cursor.execute("""
            SELECT 
                model_name,
                COUNT(*) as metric_count,
                AVG(value) as avg_quality,
                MIN(value) as min_quality,
                MAX(value) as max_quality
            FROM performance_metrics
            WHERE metric_type = 'quality_score'
            GROUP BY model_name
        """)

        model_stats = {}
        for row in cursor.fetchall():
            model_stats[row[0]] = {
                "metric_count": row[1],
                "avg_quality": row[2],
                "min_quality": row[3],
                "max_quality": row[4],
            }

        # Recent trends (last 7 days)
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        cursor.execute(
            """
            SELECT 
                model_name,
                COUNT(*) as recent_count,
                AVG(value) as recent_avg_quality
            FROM performance_metrics
            WHERE metric_type = 'quality_score' AND timestamp >= ?
            GROUP BY model_name
        """,
            (week_ago,),
        )

        recent_trends = {}
        for row in cursor.fetchall():
            recent_trends[row[0]] = {
                "recent_count": row[1],
                "recent_avg_quality": row[2],
            }

        conn.close()

        return {
            "overall": {
                "total_metrics": overall_stats[0] if overall_stats else 0,
                "avg_quality": overall_stats[1]
                if overall_stats and overall_stats[1]
                else 0.0,
                "min_quality": overall_stats[2]
                if overall_stats and overall_stats[2]
                else 0.0,
                "max_quality": overall_stats[3]
                if overall_stats and overall_stats[3]
                else 0.0,
            },
            "by_model": model_stats,
            "recent_trends": recent_trends,
        }

    def store_learning_outcome(
        self,
        routing_decision_id: str,
        expected_quality: float,
        actual_quality: float,
        outcome_type: str,
        adaptation_applied: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Store learning outcome for analysis"""

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            prediction_error = actual_quality - expected_quality

            cursor.execute(
                """
                INSERT INTO learning_outcomes
                (outcome_id, routing_decision_id, expected_quality, actual_quality,
                 prediction_error, adaptation_applied, outcome_type, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    f"outcome_{uuid4().hex[:8]}",
                    routing_decision_id,
                    expected_quality,
                    actual_quality,
                    prediction_error,
                    adaptation_applied,
                    outcome_type,
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(metadata) if metadata else None,
                ),
            )

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Error storing learning outcome: {e}")
            return False

    def get_learning_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get learning system analytics"""

        start_time = (
            datetime.now(timezone.utc) - timedelta(days=days_back)
        ).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Basic learning metrics
        cursor.execute(
            """
            SELECT 
                outcome_type,
                COUNT(*) as count,
                AVG(prediction_error) as avg_error,
                AVG(ABS(prediction_error)) as avg_abs_error,
                SUM(CASE WHEN adaptation_applied THEN 1 ELSE 0 END) as adaptations_applied
            FROM learning_outcomes
            WHERE timestamp >= ?
            GROUP BY outcome_type
        """,
            (start_time,),
        )

        outcome_stats = {}
        for row in cursor.fetchall():
            outcome_stats[row[0]] = {
                "count": row[1],
                "avg_prediction_error": row[2],
                "avg_abs_prediction_error": row[3],
                "adaptations_applied": row[4],
            }

        # Prediction accuracy trends
        cursor.execute(
            """
            SELECT 
                DATE(timestamp) as date,
                AVG(ABS(prediction_error)) as daily_avg_error,
                COUNT(*) as daily_count
            FROM learning_outcomes
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
        """,
            (start_time,),
        )

        accuracy_trends = []
        for row in cursor.fetchall():
            accuracy_trends.append(
                {"date": row[0], "avg_absolute_error": row[1], "sample_count": row[2]}
            )

        conn.close()

        return {
            "outcome_statistics": outcome_stats,
            "accuracy_trends": accuracy_trends,
            "analysis_period_days": days_back,
        }

    def cleanup_old_metrics(self, days_to_keep: int = 90) -> int:
        """Clean up old metric records"""

        cutoff_time = (
            datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        ).isoformat()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Delete old raw metrics
            cursor.execute(
                "DELETE FROM performance_metrics WHERE timestamp < ?", (cutoff_time,)
            )
            deleted_metrics = cursor.rowcount

            # Delete old learning outcomes
            cursor.execute(
                "DELETE FROM learning_outcomes WHERE timestamp < ?", (cutoff_time,)
            )
            deleted_outcomes = cursor.rowcount

            conn.commit()
            conn.close()

            total_deleted = deleted_metrics + deleted_outcomes
            logger.info(
                f"Cleaned up {total_deleted} old records (metrics: {deleted_metrics}, outcomes: {deleted_outcomes})"
            )

            return total_deleted

        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
            return 0

    def export_metrics(
        self,
        output_file: str,
        model_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> bool:
        """Export metrics to JSON file"""

        try:
            metrics = self.get_metrics(
                model_name=model_name,
                start_time=start_time,
                end_time=end_time,
                limit=10000,
            )

            export_data = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "filter_criteria": {
                    "model_name": model_name,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                },
                "metrics_count": len(metrics),
                "metrics": [metric.to_dict() for metric in metrics],
            }

            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported {len(metrics)} metrics to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return False

"""
Continuous Learning Engine with Meta-Learning

This module implements a continuous learning system that tracks performance,
optimizes routing decisions, and adapts based on historical outcomes using
meta-learning algorithms and performance tracking.
"""

import logging
import sqlite3
import numpy as np
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class OutcomeType(str, Enum):
    """Types of learning outcomes"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
    ESCALATED = "escalated"
    TIMEOUT = "timeout"


class LearningMode(str, Enum):
    """Learning algorithm modes"""
    PASSIVE = "passive"          # Only observe and record
    ACTIVE = "active"            # Actively adjust routing
    META_LEARNING = "meta_learning"  # Use meta-learning algorithms
    HYBRID = "hybrid"            # Combine multiple approaches


@dataclass
class TaskFeatures:
    """Feature vector for task representation"""
    task_type: str
    complexity_level: float
    content_length: int
    keyword_features: Dict[str, float] = field(default_factory=dict)
    semantic_features: List[float] = field(default_factory=list)
    temporal_features: Dict[str, float] = field(default_factory=dict)
    context_features: Dict[str, Any] = field(default_factory=dict)
    
    def to_vector(self) -> List[float]:
        """Convert features to numerical vector for ML algorithms"""
        vector = [
            self.complexity_level,
            float(self.content_length),
            len(self.keyword_features),
            sum(self.keyword_features.values()),
            len(self.semantic_features)
        ]
        
        # Add keyword feature values
        vector.extend(list(self.keyword_features.values())[:10])  # Limit to top 10
        
        # Add temporal features
        vector.extend([
            self.temporal_features.get("hour_of_day", 0.0),
            self.temporal_features.get("day_of_week", 0.0),
            self.temporal_features.get("workload_factor", 1.0)
        ])
        
        return vector


@dataclass
class RoutingDecision:
    """Record of a routing decision and its outcome"""
    decision_id: str
    task_features: TaskFeatures
    selected_model: str
    confidence_score: float
    alternative_models: List[Tuple[str, float]] = field(default_factory=list)
    routing_weights: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Outcome tracking
    outcome_type: Optional[OutcomeType] = None
    quality_score: Optional[float] = None
    processing_time: Optional[float] = None
    cost_incurred: Optional[float] = None
    user_satisfaction: Optional[float] = None
    error_details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "decision_id": self.decision_id,
            "task_features": {
                "task_type": self.task_features.task_type,
                "complexity_level": self.task_features.complexity_level,
                "content_length": self.task_features.content_length,
                "keyword_features": self.task_features.keyword_features,
                "temporal_features": self.task_features.temporal_features,
                "context_features": self.task_features.context_features
            },
            "selected_model": self.selected_model,
            "confidence_score": self.confidence_score,
            "alternative_models": self.alternative_models,
            "routing_weights": self.routing_weights,
            "timestamp": self.timestamp.isoformat(),
            "outcome_type": self.outcome_type.value if self.outcome_type else None,
            "quality_score": self.quality_score,
            "processing_time": self.processing_time,
            "cost_incurred": self.cost_incurred,
            "user_satisfaction": self.user_satisfaction,
            "error_details": self.error_details
        }


class PostgreSQLStore:
    """PostgreSQL storage adapter (mock implementation)"""
    
    def __init__(self, db_path: str = "learning_engine.db"):
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize SQLite database (mock PostgreSQL)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS routing_decisions (
                decision_id TEXT PRIMARY KEY,
                task_features TEXT,
                selected_model TEXT,
                confidence_score REAL,
                alternative_models TEXT,
                routing_weights TEXT,
                timestamp TEXT,
                outcome_type TEXT,
                quality_score REAL,
                processing_time REAL,
                cost_incurred REAL,
                user_satisfaction REAL,
                error_details TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                model_name TEXT,
                task_type TEXT,
                avg_quality_score REAL,
                avg_processing_time REAL,
                success_rate REAL,
                total_tasks INTEGER,
                last_updated TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_metrics (
                metric_name TEXT PRIMARY KEY,
                metric_value REAL,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_routing_decision(self, decision: RoutingDecision):
        """Store routing decision in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO routing_decisions VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            decision.decision_id,
            json.dumps(decision.task_features.__dict__),
            decision.selected_model,
            decision.confidence_score,
            json.dumps(decision.alternative_models),
            json.dumps(decision.routing_weights),
            decision.timestamp.isoformat(),
            decision.outcome_type.value if decision.outcome_type else None,
            decision.quality_score,
            decision.processing_time,
            decision.cost_incurred,
            decision.user_satisfaction,
            decision.error_details
        ))
        
        conn.commit()
        conn.close()
    
    def get_routing_history(self, limit: int = 1000) -> List[RoutingDecision]:
        """Retrieve routing decision history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM routing_decisions
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        decisions = []
        for row in rows:
            task_features_data = json.loads(row[1])
            task_features = TaskFeatures(
                task_type=task_features_data.get("task_type", ""),
                complexity_level=task_features_data.get("complexity_level", 0.5),
                content_length=task_features_data.get("content_length", 0),
                keyword_features=task_features_data.get("keyword_features", {}),
                temporal_features=task_features_data.get("temporal_features", {}),
                context_features=task_features_data.get("context_features", {})
            )
            
            decision = RoutingDecision(
                decision_id=row[0],
                task_features=task_features,
                selected_model=row[2],
                confidence_score=row[3],
                alternative_models=json.loads(row[4]) if row[4] else [],
                routing_weights=json.loads(row[5]) if row[5] else {},
                timestamp=datetime.fromisoformat(row[6]),
                outcome_type=OutcomeType(row[7]) if row[7] else None,
                quality_score=row[8],
                processing_time=row[9],
                cost_incurred=row[10],
                user_satisfaction=row[11],
                error_details=row[12]
            )
            decisions.append(decision)
        
        return decisions
    
    def update_model_performance(self, model_name: str, task_type: str, metrics: Dict[str, Any]):
        """Update model performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO model_performance VALUES
            (?, ?, ?, ?, ?, ?, ?)
        ''', (
            model_name,
            task_type,
            metrics.get("avg_quality_score", 0.0),
            metrics.get("avg_processing_time", 0.0),
            metrics.get("success_rate", 0.0),
            metrics.get("total_tasks", 0),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()


class MAMLLearner:
    """Model-Agnostic Meta-Learning implementation"""
    
    def __init__(self, meta_lr: float = 0.01, inner_lr: float = 0.1):
        self.meta_lr = meta_lr
        self.inner_lr = inner_lr
        self.base_model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
        logger.info("MAML learner initialized for routing optimization")
    
    def meta_train(self, task_episodes: List[List[Tuple[List[float], float]]]) -> Dict[str, Any]:
        """Meta-train on multiple task episodes"""
        
        if not task_episodes:
            return {"error": "No training episodes provided"}
        
        # Collect all data for initial model training
        all_X, all_y = [], []
        for episode in task_episodes:
            for features, target in episode:
                all_X.append(features)
                all_y.append(target)
        
        if not all_X:
            return {"error": "No training data found"}
        
        # Fit scaler and base model
        X_scaled = self.scaler.fit_transform(all_X)
        self.base_model.fit(X_scaled, all_y)
        self.is_trained = True
        
        # Calculate meta-learning metrics
        cv_scores = cross_val_score(self.base_model, X_scaled, all_y, cv=5)
        
        logger.info(f"MAML meta-training completed: CV score = {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        return {
            "meta_training_score": cv_scores.mean(),
            "meta_training_std": cv_scores.std(),
            "episodes_processed": len(task_episodes),
            "total_samples": len(all_X)
        }
    
    def fast_adapt(self, support_data: List[Tuple[List[float], float]]) -> float:
        """Fast adaptation to new task (simplified)"""
        
        if not self.is_trained or not support_data:
            return 0.0
        
        # Extract features and targets
        X_support = [x[0] for x in support_data]
        y_support = [x[1] for x in support_data]
        
        # Scale features
        X_scaled = self.scaler.transform(X_support)
        
        # Simple adaptation: retrain on support data
        adapted_model = RandomForestRegressor(n_estimators=20, random_state=42)
        adapted_model.fit(X_scaled, y_support)
        
        # Return adaptation quality score
        if len(support_data) > 1:
            score = adapted_model.score(X_scaled, y_support)
            return max(0.0, min(1.0, score))
        
        return 0.5  # Default score for single sample
    
    def predict_performance(self, task_features: List[float]) -> float:
        """Predict performance for given task features"""
        
        if not self.is_trained:
            return 0.5  # Default prediction
        
        try:
            X_scaled = self.scaler.transform([task_features])
            prediction = self.base_model.predict(X_scaled)[0]
            return float(max(0.0, min(1.0, prediction)))
        except Exception as e:
            logger.warning(f"Error in performance prediction: {e}")
            return 0.5


class ContinuousLearner:
    """
    Continuous learning system with meta-learning and adaptive routing optimization
    """
    
    def __init__(self, db_path: str = "learning_engine.db", 
                 learning_mode: LearningMode = LearningMode.HYBRID):
        self.performance_db = PostgreSQLStore(db_path)
        self.meta_learner = MAMLLearner()
        self.learning_mode = learning_mode
        
        # Model performance tracking
        self.model_performance: Dict[str, Dict[str, Any]] = {}
        self.routing_weights: Dict[str, float] = {
            "gpt-4": 0.4,
            "claude": 0.4,
            "gemini": 0.2
        }
        
        # Learning parameters
        self.learning_rate = 0.01
        self.adaptation_threshold = 0.1
        self.min_samples_for_learning = 10
        
        # Performance tracking
        self.recent_decisions: List[RoutingDecision] = []
        self.learning_metrics = {
            "total_decisions": 0,
            "successful_adaptations": 0,
            "avg_improvement": 0.0,
            "last_meta_training": None
        }
        
        # Initialize with historical data
        self._initialize_from_history()
        
        logger.info(f"Continuous Learner initialized in {learning_mode.value} mode")
    
    def _initialize_from_history(self):
        """Initialize learning system with historical data"""
        
        try:
            # Load recent routing history
            history = self.performance_db.get_routing_history(limit=500)
            
            if history:
                logger.info(f"Loaded {len(history)} historical routing decisions")
                
                # Update model performance metrics
                self._update_model_performance_from_history(history)
                
                # Prepare meta-learning data
                if len(history) >= self.min_samples_for_learning:
                    self._prepare_meta_learning_data(history)
                
        except Exception as e:
            logger.warning(f"Error initializing from history: {e}")
    
    def _update_model_performance_from_history(self, history: List[RoutingDecision]):
        """Update model performance metrics from historical data"""
        
        model_stats = {}
        
        for decision in history:
            if decision.outcome_type and decision.quality_score is not None:
                model = decision.selected_model
                task_type = decision.task_features.task_type
                
                key = (model, task_type)
                if key not in model_stats:
                    model_stats[key] = {
                        "quality_scores": [],
                        "processing_times": [],
                        "successes": 0,
                        "total": 0
                    }
                
                stats = model_stats[key]
                stats["quality_scores"].append(decision.quality_score)
                if decision.processing_time:
                    stats["processing_times"].append(decision.processing_time)
                
                if decision.outcome_type == OutcomeType.SUCCESS:
                    stats["successes"] += 1
                stats["total"] += 1
        
        # Update performance metrics
        for (model, task_type), stats in model_stats.items():
            metrics = {
                "avg_quality_score": np.mean(stats["quality_scores"]),
                "avg_processing_time": np.mean(stats["processing_times"]) if stats["processing_times"] else 0.0,
                "success_rate": stats["successes"] / stats["total"],
                "total_tasks": stats["total"]
            }
            
            if model not in self.model_performance:
                self.model_performance[model] = {}
            
            self.model_performance[model][task_type] = metrics
            
            # Store in database
            self.performance_db.update_model_performance(model, task_type, metrics)
    
    def _prepare_meta_learning_data(self, history: List[RoutingDecision]):
        """Prepare data for meta-learning"""
        
        # Group decisions by task characteristics
        task_episodes = []
        
        # Simple grouping by task type and complexity
        grouped_decisions = {}
        for decision in history:
            if decision.quality_score is not None:
                task_key = (decision.task_features.task_type, 
                           round(decision.task_features.complexity_level, 1))
                
                if task_key not in grouped_decisions:
                    grouped_decisions[task_key] = []
                
                grouped_decisions[task_key].append(decision)
        
        # Create episodes for meta-learning
        for task_key, decisions in grouped_decisions.items():
            if len(decisions) >= 5:  # Minimum episode size
                episode = []
                for decision in decisions:
                    features = decision.task_features.to_vector()
                    target = decision.quality_score
                    episode.append((features, target))
                
                task_episodes.append(episode)
        
        # Perform meta-training if we have enough episodes
        if len(task_episodes) >= 3:
            result = self.meta_learner.meta_train(task_episodes)
            self.learning_metrics["last_meta_training"] = datetime.now().isoformat()
            logger.info(f"Meta-learning completed: {result}")
    
    def track_outcome(self, routing_decision: RoutingDecision, 
                     artifacts: List[Dict[str, Any]], quality_score: float) -> None:
        """
        Track outcome of a routing decision for learning
        
        Args:
            routing_decision: The original routing decision
            artifacts: Generated artifacts
            quality_score: Final quality assessment
        """
        
        # Update decision with outcome
        routing_decision.outcome_type = OutcomeType.SUCCESS if quality_score >= 0.8 else OutcomeType.PARTIAL_SUCCESS
        routing_decision.quality_score = quality_score
        routing_decision.processing_time = (datetime.now(timezone.utc) - routing_decision.timestamp).total_seconds()
        
        # Store in database
        self.performance_db.store_routing_decision(routing_decision)
        
        # Add to recent decisions
        self.recent_decisions.append(routing_decision)
        if len(self.recent_decisions) > 100:
            self.recent_decisions.pop(0)
        
        # Update performance metrics
        self._update_model_performance(routing_decision)
        
        # Adapt routing weights if in active learning mode
        if self.learning_mode in [LearningMode.ACTIVE, LearningMode.HYBRID]:
            self._adapt_routing_weights(routing_decision)
        
        # Trigger meta-learning if enough new data
        if (len(self.recent_decisions) >= self.min_samples_for_learning and 
            len(self.recent_decisions) % 20 == 0):
            
            self._trigger_meta_learning()
        
        self.learning_metrics["total_decisions"] += 1
        
        logger.debug(f"Tracked outcome for decision {routing_decision.decision_id}: "
                    f"quality={quality_score:.3f}, outcome={routing_decision.outcome_type.value}")
    
    def _update_model_performance(self, decision: RoutingDecision):
        """Update model performance metrics"""
        
        model = decision.selected_model
        task_type = decision.task_features.task_type
        
        if model not in self.model_performance:
            self.model_performance[model] = {}
        
        if task_type not in self.model_performance[model]:
            self.model_performance[model][task_type] = {
                "quality_scores": [],
                "processing_times": [],
                "successes": 0,
                "total": 0
            }
        
        metrics = self.model_performance[model][task_type]
        
        # Update metrics
        if decision.quality_score is not None:
            metrics["quality_scores"].append(decision.quality_score)
        if decision.processing_time is not None:
            metrics["processing_times"].append(decision.processing_time)
        
        if decision.outcome_type == OutcomeType.SUCCESS:
            metrics["successes"] += 1
        metrics["total"] += 1
        
        # Calculate aggregated metrics
        aggregated = {
            "avg_quality_score": np.mean(metrics["quality_scores"]) if metrics["quality_scores"] else 0.0,
            "avg_processing_time": np.mean(metrics["processing_times"]) if metrics["processing_times"] else 0.0,
            "success_rate": metrics["successes"] / metrics["total"],
            "total_tasks": metrics["total"]
        }
        
        # Store in database
        self.performance_db.update_model_performance(model, task_type, aggregated)
    
    def _adapt_routing_weights(self, decision: RoutingDecision):
        """Adapt routing weights based on performance"""
        
        if decision.quality_score is None:
            return
        
        model = decision.selected_model
        expected_quality = decision.confidence_score
        actual_quality = decision.quality_score
        
        # Calculate prediction error
        prediction_error = actual_quality - expected_quality
        
        # Adjust weights based on performance
        if abs(prediction_error) > self.adaptation_threshold:
            adjustment = self.learning_rate * prediction_error
            
            # Update weight for this model
            current_weight = self.routing_weights.get(model, 0.33)
            new_weight = max(0.1, min(0.8, current_weight + adjustment))
            
            # Normalize weights
            other_models = [m for m in self.routing_weights.keys() if m != model]
            if other_models:
                remaining_weight = 1.0 - new_weight
                other_weight = remaining_weight / len(other_models)
                
                self.routing_weights[model] = new_weight
                for other_model in other_models:
                    self.routing_weights[other_model] = other_weight
                
                self.learning_metrics["successful_adaptations"] += 1
                
                logger.debug(f"Adapted routing weights: {self.routing_weights}")
    
    def _trigger_meta_learning(self):
        """Trigger meta-learning update"""
        
        if self.learning_mode not in [LearningMode.META_LEARNING, LearningMode.HYBRID]:
            return
        
        try:
            # Prepare recent data for meta-learning
            recent_episodes = []
            
            # Group recent decisions by similarity
            decisions_by_type = {}
            for decision in self.recent_decisions[-50:]:  # Use last 50 decisions
                if decision.quality_score is not None:
                    task_type = decision.task_features.task_type
                    if task_type not in decisions_by_type:
                        decisions_by_type[task_type] = []
                    decisions_by_type[task_type].append(decision)
            
            # Create episodes
            for task_type, decisions in decisions_by_type.items():
                if len(decisions) >= 3:
                    episode = []
                    for decision in decisions:
                        features = decision.task_features.to_vector()
                        target = decision.quality_score
                        episode.append((features, target))
                    recent_episodes.append(episode)
            
            # Update meta-learner
            if recent_episodes:
                result = self.meta_learner.meta_train(recent_episodes)
                self.learning_metrics["last_meta_training"] = datetime.now().isoformat()
                logger.info(f"Meta-learning update: {result}")
                
        except Exception as e:
            logger.warning(f"Error in meta-learning update: {e}")
    
    def optimize_routing(self, task_features: TaskFeatures) -> Dict[str, float]:
        """
        Use historical data to optimize routing for given task features
        
        Args:
            task_features: Features of the task to route
            
        Returns:
            Optimized routing weights for available models
        """
        
        if self.learning_mode == LearningMode.PASSIVE:
            return self.routing_weights.copy()
        
        try:
            # Get performance predictions from meta-learner
            feature_vector = task_features.to_vector()
            
            # Predict performance for each model
            model_predictions = {}
            for model in self.routing_weights.keys():
                # Use meta-learner prediction if available
                prediction = self.meta_learner.predict_performance(feature_vector)
                
                # Combine with historical performance
                task_type = task_features.task_type
                if (model in self.model_performance and 
                    task_type in self.model_performance[model]):
                    
                    historical_score = self.model_performance[model][task_type]["avg_quality_score"]
                    
                    # Weighted combination
                    combined_score = 0.6 * prediction + 0.4 * historical_score
                    model_predictions[model] = combined_score
                else:
                    model_predictions[model] = prediction
            
            # Convert predictions to routing weights
            total_score = sum(model_predictions.values())
            if total_score > 0:
                optimized_weights = {
                    model: score / total_score 
                    for model, score in model_predictions.items()
                }
                
                # Smooth with existing weights to avoid dramatic changes
                smoothed_weights = {}
                for model in self.routing_weights.keys():
                    current_weight = self.routing_weights[model]
                    optimized_weight = optimized_weights.get(model, 0.33)
                    smoothed_weights[model] = 0.7 * optimized_weight + 0.3 * current_weight
                
                # Normalize
                total_weight = sum(smoothed_weights.values())
                if total_weight > 0:
                    smoothed_weights = {k: v/total_weight for k, v in smoothed_weights.items()}
                
                logger.debug(f"Optimized routing weights: {smoothed_weights}")
                return smoothed_weights
            
        except Exception as e:
            logger.warning(f"Error optimizing routing: {e}")
        
        # Fallback to current weights
        return self.routing_weights.copy()
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        
        stats = {
            "learning_mode": self.learning_mode.value,
            "total_decisions": self.learning_metrics["total_decisions"],
            "successful_adaptations": self.learning_metrics["successful_adaptations"],
            "recent_decisions": len(self.recent_decisions),
            "current_routing_weights": self.routing_weights.copy(),
            "meta_learner_trained": self.meta_learner.is_trained,
            "last_meta_training": self.learning_metrics.get("last_meta_training"),
            "model_performance_summary": {}
        }
        
        # Summarize model performance
        for model, task_metrics in self.model_performance.items():
            model_summary = {
                "total_task_types": len(task_metrics),
                "avg_quality_across_tasks": np.mean([
                    metrics.get("avg_quality_score", 0.0) 
                    for metrics in task_metrics.values()
                ]),
                "avg_success_rate": np.mean([
                    metrics.get("success_rate", 0.0)
                    for metrics in task_metrics.values()
                ])
            }
            stats["model_performance_summary"][model] = model_summary
        
        return stats
    
    def reset_learning(self):
        """Reset learning system (useful for testing)"""
        
        self.model_performance.clear()
        self.recent_decisions.clear()
        self.routing_weights = {"gpt-4": 0.4, "claude": 0.4, "gemini": 0.2}
        self.learning_metrics = {
            "total_decisions": 0,
            "successful_adaptations": 0,
            "avg_improvement": 0.0,
            "last_meta_training": None
        }
        
        logger.info("Learning system reset")
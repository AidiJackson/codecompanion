"""
Thompson Sampling Bandit Algorithm for Model Selection

Implements Bayesian learning for multi-armed bandit problems
to balance exploration and exploitation in model selection.
"""

import logging
import math
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import sqlite3
from pathlib import Path

# Optional scientific computing libraries
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    stats = None

logger = logging.getLogger(__name__)


@dataclass
class BanditArm:
    """Individual bandit arm representing a model"""
    arm_id: str
    alpha: float = 1.0  # Prior successes + observed successes
    beta: float = 1.0   # Prior failures + observed failures
    total_pulls: int = 0
    total_reward: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    context_weights: Dict[str, float] = field(default_factory=dict)
    
    @property
    def estimated_mean(self) -> float:
        """Estimated mean reward using Beta distribution"""
        return self.alpha / (self.alpha + self.beta)
    
    @property
    def confidence_interval(self) -> Tuple[float, float]:
        """95% confidence interval for the arm's performance"""
        if SCIPY_AVAILABLE:
            lower = stats.beta.ppf(0.025, self.alpha, self.beta)
            upper = stats.beta.ppf(0.975, self.alpha, self.beta)
            return (lower, upper)
        else:
            # Fallback approximation using normal distribution
            mean = self.estimated_mean
            var = (self.alpha * self.beta) / ((self.alpha + self.beta)**2 * (self.alpha + self.beta + 1))
            std = var ** 0.5
            return (max(0, mean - 1.96 * std), min(1, mean + 1.96 * std))
    
    def sample_theta(self) -> float:
        """Sample from posterior Beta distribution (Thompson Sampling)"""
        if NUMPY_AVAILABLE:
            try:
                return np.random.beta(self.alpha, self.beta)
            except Exception:
                return self.estimated_mean
        else:
            # Simple fallback sampling using built-in random
            import random
            # Use method of moments approximation
            mean = self.estimated_mean
            # Add some randomness around the mean
            noise = random.gauss(0, 0.1) * (1 - mean) * mean
            return max(0.0, min(1.0, mean + noise))
    
    def update(self, reward: float, context: Optional[Dict[str, Any]] = None):
        """Update arm parameters with observed reward"""
        self.total_pulls += 1
        self.total_reward += reward
        
        # Update Beta parameters
        # Treat reward as success probability
        self.alpha += reward
        self.beta += (1.0 - reward)
        
        # Update context weights if provided
        if context:
            self._update_context_weights(reward, context)
        
        self.last_updated = datetime.now()
    
    def _update_context_weights(self, reward: float, context: Dict[str, Any]):
        """Update context-specific weights"""
        learning_rate = 0.1
        
        for feature, value in context.items():
            if isinstance(value, (int, float)):
                current_weight = self.context_weights.get(feature, 0.0)
                # Update weight based on correlation with reward
                correlation = reward * value
                updated_weight = (1 - learning_rate) * current_weight + learning_rate * correlation
                self.context_weights[feature] = max(-1.0, min(1.0, updated_weight))


class ThompsonSamplingBandit:
    """
    Thompson Sampling Multi-Armed Bandit for model selection
    
    Uses Bayesian approach to balance exploration vs exploitation
    by sampling from posterior distributions.
    """
    
    def __init__(self, db_path: str = "bandit_learning.db"):
        self.db_path = db_path
        self.arms: Dict[str, BanditArm] = {}
        self.total_interactions = 0
        self.learning_rate = 0.1
        self.context_decay = 0.95  # Decay factor for old context information
        
        # Initialize database
        self._init_database()
        self._load_arms_from_db()
        
        logger.info("Thompson Sampling Bandit initialized")
    
    def _init_database(self):
        """Initialize SQLite database for bandit state"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bandit_arms (
                    arm_id TEXT PRIMARY KEY,
                    alpha REAL,
                    beta REAL,
                    total_pulls INTEGER,
                    total_reward REAL,
                    context_weights TEXT,
                    last_updated DATETIME
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bandit_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    arm_id TEXT,
                    reward REAL,
                    context TEXT,
                    timestamp DATETIME
                )
            """)
    
    def _load_arms_from_db(self):
        """Load bandit arms from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT arm_id, alpha, beta, total_pulls, total_reward,
                           context_weights, last_updated
                    FROM bandit_arms
                """)
                
                for row in cursor.fetchall():
                    arm_id = row[0]
                    context_weights = json.loads(row[5]) if row[5] else {}
                    last_updated = datetime.fromisoformat(row[6]) if row[6] else datetime.now()
                    
                    self.arms[arm_id] = BanditArm(
                        arm_id=arm_id,
                        alpha=row[1],
                        beta=row[2],
                        total_pulls=row[3],
                        total_reward=row[4],
                        context_weights=context_weights,
                        last_updated=last_updated
                    )
                
                logger.info(f"Loaded {len(self.arms)} bandit arms from database")
                
        except Exception as e:
            logger.warning(f"Could not load bandit arms from database: {e}")
    
    def _save_arm_to_db(self, arm: BanditArm):
        """Save single bandit arm to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO bandit_arms 
                    (arm_id, alpha, beta, total_pulls, total_reward, 
                     context_weights, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    arm.arm_id,
                    arm.alpha,
                    arm.beta,
                    arm.total_pulls,
                    arm.total_reward,
                    json.dumps(arm.context_weights),
                    arm.last_updated.isoformat()
                ))
        except Exception as e:
            logger.error(f"Failed to save arm {arm.arm_id}: {e}")
    
    def _record_interaction(self, arm_id: str, reward: float, context: Dict[str, Any]):
        """Record bandit interaction for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO bandit_interactions 
                    (arm_id, reward, context, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (
                    arm_id,
                    reward,
                    json.dumps(context),
                    datetime.now().isoformat()
                ))
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
    
    def register_arm(self, arm_id: str, prior_alpha: float = 1.0, 
                    prior_beta: float = 1.0):
        """Register a new bandit arm (model)"""
        if arm_id not in self.arms:
            self.arms[arm_id] = BanditArm(
                arm_id=arm_id,
                alpha=prior_alpha,
                beta=prior_beta
            )
            self._save_arm_to_db(self.arms[arm_id])
            logger.info(f"Registered new bandit arm: {arm_id}")
    
    def select_arm(self, context: Optional[Dict[str, float]] = None,
                  exclude_arms: Optional[List[str]] = None) -> str:
        """
        Select arm using Thompson Sampling
        
        Args:
            context: Context features for contextual bandit
            exclude_arms: Arms to exclude from selection
            
        Returns:
            Selected arm ID
        """
        available_arms = [
            arm_id for arm_id in self.arms.keys()
            if not exclude_arms or arm_id not in exclude_arms
        ]
        
        if not available_arms:
            raise ValueError("No arms available for selection")
        
        # Sample from posterior for each arm
        arm_scores = {}
        
        for arm_id in available_arms:
            arm = self.arms[arm_id]
            
            # Base Thompson sampling score
            base_score = arm.sample_theta()
            
            # Apply contextual adjustment if context provided
            if context:
                context_adjustment = self._calculate_context_score(arm, context)
                final_score = base_score * (1.0 + context_adjustment)
            else:
                final_score = base_score
            
            arm_scores[arm_id] = final_score
        
        # Select arm with highest sampled score
        selected_arm = max(arm_scores.items(), key=lambda x: x[1])[0]
        
        self.total_interactions += 1
        
        logger.debug(f"Selected arm {selected_arm} with score {arm_scores[selected_arm]:.3f}")
        
        return selected_arm
    
    def _calculate_context_score(self, arm: BanditArm, context: Dict[str, float]) -> float:
        """Calculate context-based score adjustment"""
        if not arm.context_weights:
            return 0.0
        
        score = 0.0
        weight_sum = 0.0
        
        for feature, value in context.items():
            if feature in arm.context_weights:
                weight = arm.context_weights[feature]
                score += weight * value
                weight_sum += abs(weight)
        
        # Normalize by total weight magnitude
        if weight_sum > 0:
            return score / weight_sum
        else:
            return 0.0
    
    def update_arm(self, arm_id: str, reward: float, 
                  context: Optional[Dict[str, Any]] = None):
        """Update arm with observed reward"""
        if arm_id not in self.arms:
            self.register_arm(arm_id)
        
        arm = self.arms[arm_id]
        arm.update(reward, context)
        
        # Save to database
        self._save_arm_to_db(arm)
        
        # Record interaction
        if context:
            self._record_interaction(arm_id, reward, context)
        
        logger.debug(f"Updated arm {arm_id}: reward={reward:.3f}, "
                    f"alpha={arm.alpha:.3f}, beta={arm.beta:.3f}")
    
    def get_arm_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all arms"""
        stats = {}
        
        for arm_id, arm in self.arms.items():
            ci_lower, ci_upper = arm.confidence_interval
            
            stats[arm_id] = {
                'estimated_mean': arm.estimated_mean,
                'confidence_interval': (ci_lower, ci_upper),
                'total_pulls': arm.total_pulls,
                'total_reward': arm.total_reward,
                'alpha': arm.alpha,
                'beta': arm.beta,
                'last_updated': arm.last_updated.isoformat()
            }
        
        return stats
    
    def get_best_arm(self, confidence_threshold: float = 0.95) -> Tuple[str, float]:
        """
        Get the arm with highest estimated performance
        
        Args:
            confidence_threshold: Minimum confidence level required
            
        Returns:
            (arm_id, estimated_mean) of best performing arm
        """
        if not self.arms:
            raise ValueError("No arms available")
        
        best_arm = None
        best_mean = -1.0
        
        for arm_id, arm in self.arms.items():
            if arm.total_pulls < 3:  # Require minimum observations
                continue
                
            ci_lower, ci_upper = arm.confidence_interval
            confidence_width = ci_upper - ci_lower
            
            # Only consider arms with sufficient confidence
            if confidence_width <= (2.0 - 2.0 * confidence_threshold):
                if arm.estimated_mean > best_mean:
                    best_mean = arm.estimated_mean
                    best_arm = arm_id
        
        if best_arm is None:
            # Fallback to arm with most observations
            best_arm = max(self.arms.items(), key=lambda x: x[1].total_pulls)[0]
            best_mean = self.arms[best_arm].estimated_mean
        
        return best_arm, best_mean
    
    def reset_arm(self, arm_id: str):
        """Reset specific arm to initial state"""
        if arm_id in self.arms:
            self.arms[arm_id] = BanditArm(arm_id=arm_id)
            self._save_arm_to_db(self.arms[arm_id])
            logger.info(f"Reset bandit arm: {arm_id}")
    
    def decay_old_information(self, decay_days: int = 30):
        """Apply decay to old information to adapt to changing conditions"""
        cutoff_date = datetime.now() - timedelta(days=decay_days)
        
        for arm in self.arms.values():
            if arm.last_updated < cutoff_date:
                # Decay towards prior
                decay_factor = self.context_decay ** decay_days
                
                arm.alpha = 1.0 + (arm.alpha - 1.0) * decay_factor
                arm.beta = 1.0 + (arm.beta - 1.0) * decay_factor
                arm.total_pulls = int(arm.total_pulls * decay_factor)
                arm.total_reward *= decay_factor
                
                # Decay context weights
                for feature in arm.context_weights:
                    arm.context_weights[feature] *= decay_factor
                
                self._save_arm_to_db(arm)
        
        logger.info(f"Applied decay to arms older than {decay_days} days")
    
    def export_learning_data(self) -> Dict[str, Any]:
        """Export all learning data for analysis"""
        return {
            'arms': {arm_id: {
                'alpha': arm.alpha,
                'beta': arm.beta,
                'total_pulls': arm.total_pulls,
                'total_reward': arm.total_reward,
                'estimated_mean': arm.estimated_mean,
                'confidence_interval': arm.confidence_interval,
                'context_weights': arm.context_weights,
                'last_updated': arm.last_updated.isoformat()
            } for arm_id, arm in self.arms.items()},
            'total_interactions': self.total_interactions,
            'export_timestamp': datetime.now().isoformat()
        }
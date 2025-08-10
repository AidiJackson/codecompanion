"""
Data-driven model router for optimal agent selection.

Provides intelligent routing based on capability vectors, task analysis,
and multi-objective optimization considering quality, cost, and latency.
"""

from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from schemas.routing import (
    ModelRouter, ModelCapability, RoutingDecision, TaskType, TaskComplexity,
    ModelType, MODEL_CAPABILITIES
)
from schemas.ledgers import TaskLedger


logger = logging.getLogger(__name__)


class RoutingContext(BaseModel):
    """Context information for routing decisions"""
    
    # Request context
    request_id: str = Field(..., description="Unique request identifier")
    workflow_id: str = Field(..., description="Associated workflow ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Routing timestamp")
    
    # Task context
    task: TaskLedger = Field(..., description="Task to be routed")
    complexity: TaskComplexity = Field(..., description="Task complexity analysis")
    
    # System context
    available_models: List[ModelType] = Field(..., description="Currently available models")
    system_load: Dict[ModelType, float] = Field(default_factory=dict, description="Current system load per model")
    
    # Constraints and preferences
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Hard constraints")
    preferences: Dict[str, float] = Field(default_factory=dict, description="Soft preferences")
    
    # Budget and limits
    remaining_budget: Optional[float] = Field(None, description="Remaining cost budget")
    max_latency_tolerance: Optional[float] = Field(None, description="Maximum acceptable latency")
    retry_attempt: int = Field(default=0, description="Retry attempt number")


class ModelSelection(BaseModel):
    """Result of model selection with full context"""
    
    # Selection result
    routing_decision: RoutingDecision = Field(..., description="Primary routing decision")
    context: RoutingContext = Field(..., description="Routing context")
    
    # Selection metadata
    selection_timestamp: datetime = Field(default_factory=datetime.now, description="Selection timestamp")
    selection_reasoning: str = Field(..., description="Human-readable reasoning")
    confidence_factors: Dict[str, float] = Field(..., description="Factors affecting confidence")
    
    # Fallback options
    fallback_models: List[Tuple[ModelType, str]] = Field(default_factory=list, description="Fallback options with reasons")
    
    # Execution guidance
    recommended_timeout: float = Field(..., description="Recommended timeout in seconds")
    retry_policy: Dict[str, Any] = Field(..., description="Retry policy configuration")
    monitoring_points: List[str] = Field(default_factory=list, description="What to monitor during execution")


class DataDrivenRouter:
    """
    Advanced router that uses capability vectors and task analysis for optimal model selection.
    
    Features:
    - Multi-objective optimization (quality, cost, latency)
    - Dynamic load balancing
    - Constraint satisfaction
    - Adaptive learning from historical performance
    - Fallback and retry strategies
    """
    
    def __init__(self, 
                 models: Optional[List[ModelCapability]] = None,
                 quality_weight: float = 0.7,
                 cost_weight: float = 0.2,
                 latency_weight: float = 0.1):
        
        self.models = models or MODEL_CAPABILITIES
        self.model_router = ModelRouter(
            available_models=self.models,
            quality_weight=quality_weight,
            cost_weight=cost_weight,
            latency_weight=latency_weight
        )
        
        # Historical performance tracking
        self.performance_history: Dict[ModelType, List[Dict[str, Any]]] = {}
        self.routing_history: List[ModelSelection] = []
        
        # Dynamic load tracking
        self.current_loads: Dict[ModelType, float] = {}
        self.recent_failures: Dict[ModelType, List[datetime]] = {}
        
        logger.info(f"Router initialized with {len(self.models)} models")
    
    def analyze_task_complexity(self, task: TaskLedger) -> TaskComplexity:
        """Analyze task to determine complexity profile"""
        
        # Base complexity assessment
        description_length = len(task.description)
        requirements_count = len(task.acceptance_tests)
        dependency_count = len(task.dependencies)
        
        # Heuristic complexity scoring
        technical_complexity = min(1.0, (description_length / 1000) * 0.3 + 
                                 (requirements_count / 10) * 0.4 +
                                 (dependency_count / 5) * 0.3)
        
        # Assess novelty based on task type and description keywords
        novelty_keywords = ['new', 'novel', 'innovative', 'experimental', 'research', 'prototype']
        novelty_score = sum(1 for keyword in novelty_keywords 
                           if keyword.lower() in task.description.lower()) / len(novelty_keywords)
        
        # Safety risk assessment
        safety_keywords = ['security', 'authentication', 'encryption', 'financial', 'medical', 'critical']
        safety_risk = sum(1 for keyword in safety_keywords 
                         if keyword.lower() in task.description.lower()) / len(safety_keywords)
        
        # Context requirement estimation
        context_requirement = min(1.0, description_length / 5000)  # Higher for longer descriptions
        
        # Interdependence based on dependencies
        interdependence = min(1.0, dependency_count / 10)
        
        # Estimate token count
        estimated_tokens = int(description_length * 1.3)  # Rough estimate including response
        
        # Task characteristics
        requires_reasoning = any(keyword in task.description.lower() 
                               for keyword in ['analyze', 'design', 'architect', 'plan', 'strategy'])
        requires_creativity = any(keyword in task.description.lower()
                                for keyword in ['creative', 'innovative', 'design', 'ui', 'ux'])
        time_sensitive = task.priority.value in ['high', 'critical']
        
        return TaskComplexity(
            technical_complexity=technical_complexity,
            novelty=novelty_score,
            safety_risk=safety_risk,
            context_requirement=context_requirement,
            interdependence=interdependence,
            estimated_tokens=estimated_tokens,
            requires_reasoning=requires_reasoning,
            requires_creativity=requires_creativity,
            time_sensitive=time_sensitive
        )
    
    def infer_task_type(self, task: TaskLedger) -> TaskType:
        """Infer primary task type from task description and requirements"""
        
        description_lower = task.description.lower()
        
        # Keyword-based task type inference
        task_type_keywords = {
            TaskType.REASONING_LONG: ['analyze', 'research', 'investigate', 'plan', 'strategy', 'architecture'],
            TaskType.CODE_UI: ['ui', 'ux', 'frontend', 'interface', 'design', 'user experience'],
            TaskType.CODE_BACKEND: ['backend', 'api', 'database', 'server', 'service', 'endpoint'],
            TaskType.TEST_GEN: ['test', 'testing', 'qa', 'quality', 'validation', 'verification'],
            TaskType.CODE_REVIEW: ['review', 'audit', 'analysis', 'quality', 'refactor'],
            TaskType.DOCUMENTATION: ['document', 'documentation', 'readme', 'guide', 'manual'],
            TaskType.DEBUGGING: ['debug', 'fix', 'bug', 'issue', 'error', 'troubleshoot'],
            TaskType.ARCHITECTURE: ['architecture', 'design', 'system', 'structure', 'framework']
        }
        
        # Score each task type
        task_type_scores = {}
        for task_type, keywords in task_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                task_type_scores[task_type] = score
        
        # Return highest scoring task type or default to reasoning
        if task_type_scores:
            return max(task_type_scores.items(), key=lambda x: x[1])[0]
        else:
            return TaskType.REASONING_LONG  # Default fallback
    
    def apply_load_balancing(self, routing_decision: RoutingDecision, 
                           context: RoutingContext) -> RoutingDecision:
        """Apply load balancing adjustments to routing decision"""
        
        selected_model = routing_decision.selected_model
        current_load = self.current_loads.get(selected_model, 0.0)
        
        # If selected model is heavily loaded, consider alternatives
        if current_load > 0.8:  # 80% load threshold
            logger.info(f"Model {selected_model} heavily loaded ({current_load:.2f}), considering alternatives")
            
            # Look for alternatives with lower load
            for alt_model, alt_score in routing_decision.alternatives:
                alt_load = self.current_loads.get(alt_model, 0.0)
                
                # Switch if alternative has significantly lower load and reasonable score
                if alt_load < current_load - 0.3 and alt_score > routing_decision.final_score * 0.85:
                    logger.info(f"Switching to {alt_model} due to load balancing")
                    
                    # Create new routing decision with alternative
                    new_decision = routing_decision.copy()
                    new_decision.selected_model = alt_model
                    new_decision.final_score = alt_score * (1.0 - alt_load * 0.2)  # Adjust for load
                    new_decision.routing_parameters["load_balancing_applied"] = True
                    
                    return new_decision
        
        return routing_decision
    
    def check_recent_failures(self, model: ModelType, failure_threshold: int = 3,
                            time_window_minutes: int = 10) -> bool:
        """Check if model has had recent failures"""
        
        if model not in self.recent_failures:
            return False
        
        recent_failures = self.recent_failures[model]
        cutoff_time = datetime.now().timestamp() - (time_window_minutes * 60)
        
        # Count failures in time window
        recent_count = sum(1 for failure_time in recent_failures 
                          if failure_time.timestamp() > cutoff_time)
        
        return recent_count >= failure_threshold
    
    def route_task(self, task: TaskLedger, workflow_id: str, 
                  constraints: Optional[Dict[str, Any]] = None,
                  preferences: Optional[Dict[str, float]] = None) -> ModelSelection:
        """Route task to optimal model with full context and reasoning"""
        
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.routing_history)}"
        
        # Analyze task complexity
        complexity = self.analyze_task_complexity(task)
        task_type = self.infer_task_type(task)
        
        # Create routing context
        context = RoutingContext(
            request_id=request_id,
            workflow_id=workflow_id,
            task=task,
            complexity=complexity,
            available_models=[model.model_type for model in self.models],
            constraints=constraints or {},
            preferences=preferences or {}
        )
        
        # Get base routing decision
        routing_decision = self.model_router.route_task(task_type, complexity, constraints)
        
        # Apply load balancing
        routing_decision = self.apply_load_balancing(routing_decision, context)
        
        # Check for recent failures and adjust if needed
        if self.check_recent_failures(routing_decision.selected_model):
            logger.warning(f"Model {routing_decision.selected_model} has recent failures, selecting alternative")
            
            # Find alternative without recent failures
            for alt_model, alt_score in routing_decision.alternatives:
                if not self.check_recent_failures(alt_model):
                    routing_decision.selected_model = alt_model
                    routing_decision.final_score = alt_score
                    routing_decision.routing_parameters["failure_avoidance_applied"] = True
                    break
        
        # Build confidence factors
        confidence_factors = {
            "base_capability": routing_decision.quality_score,
            "load_factor": 1.0 - self.current_loads.get(routing_decision.selected_model, 0.0),
            "reliability_factor": 1.0 - (len(self.recent_failures.get(routing_decision.selected_model, [])) / 10.0),
            "task_match": 1.0 if task_type in [model.best_task_types for model in self.models 
                                             if model.model_type == routing_decision.selected_model][0] else 0.7
        }
        
        # Generate selection reasoning
        selected_model_name = next(model.display_name for model in self.models 
                                 if model.model_type == routing_decision.selected_model)
        
        reasoning = f"""Selected {selected_model_name} for {task_type.value} task.
        
Reasoning:
- Task complexity: {complexity.get_complexity_score():.2f}/1.0
- Quality score: {routing_decision.quality_score:.2f}
- Cost efficiency: {routing_decision.cost_score:.2f}
- Latency score: {routing_decision.latency_score:.2f}
- Current load: {self.current_loads.get(routing_decision.selected_model, 0.0):.2f}

Key factors: {"High complexity task requiring strong reasoning" if complexity.requires_reasoning else "Standard complexity task"}.
{"Time-sensitive execution preferred" if complexity.time_sensitive else "Quality over speed preferred"}.
"""
        
        # Create fallback options
        fallback_models = [
            (alt_model, f"Fallback option with score {alt_score:.2f}")
            for alt_model, alt_score in routing_decision.alternatives[:2]
        ]
        
        # Configure retry policy
        retry_policy = {
            "max_retries": 3 if not complexity.time_sensitive else 1,
            "backoff_strategy": "exponential",
            "backoff_base": 2.0,
            "max_backoff": 60.0,
            "retry_on_timeout": True,
            "retry_on_rate_limit": True
        }
        
        # Set monitoring points
        monitoring_points = [
            "response_time",
            "token_usage", 
            "error_rate",
            "quality_metrics"
        ]
        
        if complexity.safety_risk > 0.5:
            monitoring_points.append("safety_compliance")
        
        if complexity.time_sensitive:
            monitoring_points.append("latency_p95")
        
        # Create model selection
        selection = ModelSelection(
            routing_decision=routing_decision,
            context=context,
            selection_reasoning=reasoning,
            confidence_factors=confidence_factors,
            fallback_models=fallback_models,
            recommended_timeout=routing_decision.suggested_timeout or 120.0,
            retry_policy=retry_policy,
            monitoring_points=monitoring_points
        )
        
        # Store in history
        self.routing_history.append(selection)
        
        logger.info(f"Routed task {task.task_id} to {routing_decision.selected_model} "
                   f"(score: {routing_decision.final_score:.2f})")
        
        return selection
    
    def update_model_load(self, model: ModelType, load: float):
        """Update current load for a model"""
        self.current_loads[model] = max(0.0, min(1.0, load))
    
    def record_failure(self, model: ModelType, error_message: str):
        """Record a model failure for load balancing"""
        if model not in self.recent_failures:
            self.recent_failures[model] = []
        
        self.recent_failures[model].append(datetime.now())
        
        # Keep only recent failures (last 30 minutes)
        cutoff_time = datetime.now().timestamp() - (30 * 60)
        self.recent_failures[model] = [
            failure_time for failure_time in self.recent_failures[model]
            if failure_time.timestamp() > cutoff_time
        ]
        
        logger.warning(f"Recorded failure for {model}: {error_message}")
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics and performance metrics"""
        
        model_usage = {}
        for selection in self.routing_history:
            model = selection.routing_decision.selected_model
            model_usage[model] = model_usage.get(model, 0) + 1
        
        total_selections = len(self.routing_history)
        
        return {
            "total_routings": total_selections,
            "model_usage_distribution": {
                model: count / total_selections 
                for model, count in model_usage.items()
            },
            "current_loads": self.current_loads.copy(),
            "recent_failures": {
                model: len(failures) 
                for model, failures in self.recent_failures.items()
            },
            "avg_confidence": sum(
                sum(selection.confidence_factors.values()) / len(selection.confidence_factors)
                for selection in self.routing_history
            ) / max(total_selections, 1)
        }
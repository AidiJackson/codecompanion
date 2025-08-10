"""
Intelligent Task Router with Real-Time Performance Tracking

Implements capability vector routing algorithm with multi-objective optimization
and adaptive routing based on real agent performance metrics.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

from schemas.routing import ModelType, TaskType, TaskComplexity
from core.event_streaming import EventBus, StreamEvent, EventType, EventStreamType
from agents.live_agent_workers import LiveAgentMetrics

logger = logging.getLogger(__name__)


@dataclass
class AgentPerformance:
    """Real-time agent performance tracking"""
    agent_id: str
    model_type: ModelType
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    average_quality: float = 0.0
    average_cost: float = 0.0
    average_time: float = 0.0
    current_load: int = 0
    last_success: Optional[datetime] = None
    specialization_scores: Dict[TaskType, float] = None
    
    def __post_init__(self):
        if self.specialization_scores is None:
            self.specialization_scores = {}
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks
    
    @property
    def reliability_score(self) -> float:
        """Calculate reliability score based on recent performance"""
        base_reliability = self.success_rate
        
        # Penalty for high failure rate
        if self.failed_tasks > 5:
            base_reliability *= 0.8
        
        # Bonus for recent success
        if self.last_success and (datetime.now() - self.last_success).days < 1:
            base_reliability *= 1.1
        
        return min(base_reliability, 1.0)


class IntelligentTaskRouter:
    """
    Intelligent router that uses capability vectors and real-time performance
    metrics to make optimal task assignments with multi-objective optimization.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.agent_performance: Dict[str, AgentPerformance] = {}
        self.task_history: List[Dict[str, Any]] = []
        
        # Routing weights for multi-objective optimization
        self.quality_weight = 0.6      # λ - weight for quality
        self.cost_weight = 0.2         # μ - weight for cost 
        self.latency_weight = 0.2      # ν - weight for latency
        
        # Performance tracking
        self.routing_decisions = []
        self.total_routing_requests = 0
        
        logger.info("Intelligent task router initialized with real-time tracking")
    
    async def route_task(self, task_data: Dict[str, Any], correlation_id: str,
                        available_agents: List[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Route task to optimal agent using capability vectors and performance metrics
        
        Returns: (selected_agent_id, routing_decision_metadata)
        """
        
        self.total_routing_requests += 1
        start_time = datetime.now()
        
        try:
            # Extract task characteristics
            task_type = self._extract_task_type(task_data)
            complexity = self._assess_task_complexity(task_data)
            
            # Evaluate each available agent
            agent_evaluations = []
            
            for agent_id in available_agents:
                evaluation = await self._evaluate_agent_for_task(
                    agent_id, task_type, complexity, task_data
                )
                if evaluation:
                    agent_evaluations.append(evaluation)
            
            if not agent_evaluations:
                raise ValueError("No suitable agents available for task")
            
            # Apply multi-objective optimization
            best_agent = self._select_optimal_agent(agent_evaluations)
            
            # Create routing decision
            routing_decision = {
                "selected_agent": best_agent["agent_id"],
                "routing_score": best_agent["final_score"],
                "quality_score": best_agent["quality_score"],
                "cost_score": best_agent["cost_score"],
                "latency_score": best_agent["latency_score"],
                "confidence": best_agent["confidence"],
                "reasoning": best_agent["reasoning"],
                "alternatives": [
                    {"agent_id": alt["agent_id"], "score": alt["final_score"]}
                    for alt in sorted(agent_evaluations, key=lambda x: x["final_score"], reverse=True)[1:4]
                ],
                "task_complexity": complexity,
                "routing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }
            
            # Store routing decision
            self.routing_decisions.append({
                "timestamp": start_time,
                "correlation_id": correlation_id,
                "decision": routing_decision,
                "task_data": task_data
            })
            
            # Publish routing decision event
            await self._publish_routing_event(correlation_id, routing_decision)
            
            logger.info(f"Routed task {correlation_id} to {best_agent['agent_id']} (score: {best_agent['final_score']:.3f})")
            
            return best_agent["agent_id"], routing_decision
            
        except Exception as e:
            logger.error(f"Task routing failed: {e}")
            # Fallback to first available agent
            if available_agents:
                return available_agents[0], {"error": str(e), "fallback": True}
            raise
    
    def _extract_task_type(self, task_data: Dict[str, Any]) -> TaskType:
        """Extract primary task type from task data"""
        
        task_type_str = task_data.get('primary_task_type', '').lower()
        objective = task_data.get('objective', '').lower()
        description = task_data.get('description', '').lower()
        
        # Analyze task content to determine type
        content = f"{task_type_str} {objective} {description}"
        
        if any(keyword in content for keyword in ['architecture', 'design', 'system']):
            return TaskType.ARCHITECTURE
        elif any(keyword in content for keyword in ['code', 'implement', 'program']):
            return TaskType.CODE_BACKEND
        elif any(keyword in content for keyword in ['test', 'validation', 'qa']):
            return TaskType.TEST_GEN
        elif any(keyword in content for keyword in ['ui', 'frontend', 'interface']):
            return TaskType.CODE_UI
        elif any(keyword in content for keyword in ['document', 'spec', 'requirements']):
            return TaskType.DOCUMENTATION
        elif any(keyword in content for keyword in ['review', 'analyze', 'debug']):
            return TaskType.CODE_REVIEW
        else:
            return TaskType.REASONING_LONG  # Default to reasoning
    
    def _assess_task_complexity(self, task_data: Dict[str, Any]) -> TaskComplexity:
        """Assess task complexity from task data"""
        
        # Extract complexity indicators
        description_length = len(task_data.get('description', ''))
        estimated_tokens = task_data.get('estimated_tokens', 0)
        
        # Calculate complexity scores
        technical_complexity = min(description_length / 1000, 1.0)
        novelty = 0.5  # Default novelty
        safety_risk = 0.3  # Default low risk
        context_requirement = min(estimated_tokens / 10000, 1.0)
        interdependence = len(task_data.get('dependencies', [])) * 0.2
        
        return TaskComplexity(
            technical_complexity=technical_complexity,
            novelty=novelty,
            safety_risk=safety_risk,
            context_requirement=context_requirement,
            interdependence=interdependence,
            estimated_tokens=estimated_tokens,
            requires_reasoning=True,
            requires_creativity='creative' in task_data.get('objective', '').lower(),
            time_sensitive=task_data.get('priority', 'medium') == 'high'
        )
    
    async def _evaluate_agent_for_task(self, agent_id: str, task_type: TaskType,
                                     complexity: TaskComplexity, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate an agent's suitability for a specific task"""
        
        # Get agent performance data
        performance = self.agent_performance.get(agent_id)
        if not performance:
            # Initialize performance for new agent
            performance = AgentPerformance(agent_id=agent_id, model_type=ModelType.CLAUDE_SONNET)
            self.agent_performance[agent_id] = performance
        
        # Calculate capability scores
        quality_score = self._calculate_quality_score(performance, task_type, complexity)
        cost_score = self._calculate_cost_score(performance, complexity)
        latency_score = self._calculate_latency_score(performance, complexity)
        
        # Apply multi-objective optimization
        final_score = (
            self.quality_weight * quality_score -
            self.cost_weight * cost_score -
            self.latency_weight * latency_score
        )
        
        # Calculate confidence based on historical performance
        confidence = self._calculate_confidence(performance, task_type)
        
        return {
            "agent_id": agent_id,
            "quality_score": quality_score,
            "cost_score": cost_score,
            "latency_score": latency_score,
            "final_score": final_score,
            "confidence": confidence,
            "current_load": performance.current_load,
            "reasoning": f"Quality: {quality_score:.2f}, Cost: {cost_score:.2f}, Latency: {latency_score:.2f}",
            "specialization_match": performance.specialization_scores.get(task_type, 0.5)
        }
    
    def _calculate_quality_score(self, performance: AgentPerformance, 
                               task_type: TaskType, complexity: TaskComplexity) -> float:
        """Calculate expected quality score for agent on this task"""
        
        base_quality = performance.average_quality if performance.average_quality > 0 else 0.75
        
        # Adjust for specialization
        specialization_bonus = performance.specialization_scores.get(task_type, 0.0) * 0.2
        
        # Adjust for reliability
        reliability_factor = performance.reliability_score
        
        # Adjust for complexity match (some agents handle complexity better)
        complexity_factor = 1.0
        if complexity.technical_complexity > 0.8:  # High complexity
            if 'claude' in performance.agent_id.lower():
                complexity_factor = 1.1  # Claude handles complexity well
            elif 'gpt4' in performance.agent_id.lower():
                complexity_factor = 1.05
        
        quality_score = (base_quality + specialization_bonus) * reliability_factor * complexity_factor
        return min(quality_score, 1.0)
    
    def _calculate_cost_score(self, performance: AgentPerformance, 
                            complexity: TaskComplexity) -> float:
        """Calculate normalized cost score (lower is better)"""
        
        base_cost = performance.average_cost if performance.average_cost > 0 else 0.01
        
        # Adjust for complexity
        complexity_multiplier = 1 + complexity.technical_complexity
        estimated_cost = base_cost * complexity_multiplier
        
        # Normalize to 0-1 scale (assuming max cost of $1)
        return min(estimated_cost, 1.0)
    
    def _calculate_latency_score(self, performance: AgentPerformance,
                               complexity: TaskComplexity) -> float:
        """Calculate normalized latency score (lower is better)"""
        
        base_time = performance.average_time if performance.average_time > 0 else 180  # 3 minutes default
        
        # Adjust for complexity
        complexity_multiplier = 1 + complexity.technical_complexity
        estimated_time = base_time * complexity_multiplier
        
        # Adjust for current load
        load_penalty = performance.current_load * 30  # 30 seconds per queued task
        total_time = estimated_time + load_penalty
        
        # Normalize to 0-1 scale (assuming max time of 30 minutes)
        return min(total_time / 1800, 1.0)
    
    def _calculate_confidence(self, performance: AgentPerformance, task_type: TaskType) -> float:
        """Calculate confidence in routing decision"""
        
        base_confidence = performance.success_rate
        
        # Adjust for task type specialization
        specialization_confidence = performance.specialization_scores.get(task_type, 0.5)
        
        # Adjust for sample size (more data = more confidence)
        sample_confidence = min(performance.total_tasks / 10, 1.0)
        
        return (base_confidence + specialization_confidence + sample_confidence) / 3
    
    def _select_optimal_agent(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select optimal agent using multi-objective optimization"""
        
        # Sort by final score
        sorted_evaluations = sorted(evaluations, key=lambda x: x["final_score"], reverse=True)
        
        # Consider load balancing - penalize heavily loaded agents
        for evaluation in sorted_evaluations:
            if evaluation["current_load"] > 3:  # More than 3 queued tasks
                evaluation["final_score"] *= 0.8
        
        # Re-sort after load balancing adjustment
        sorted_evaluations = sorted(evaluations, key=lambda x: x["final_score"], reverse=True)
        
        return sorted_evaluations[0]
    
    async def _publish_routing_event(self, correlation_id: str, decision: Dict[str, Any]):
        """Publish routing decision event"""
        
        routing_event = StreamEvent(
            correlation_id=correlation_id,
            event_type=EventType.ROUTING_DECISION,
            payload=decision,
            metadata={
                "router_version": "intelligent_v1",
                "multi_objective": True,
                "weights": {
                    "quality": self.quality_weight,
                    "cost": self.cost_weight,
                    "latency": self.latency_weight
                }
            }
        )
        
        await self.event_bus.publish_event(EventStreamType.METRICS, routing_event)
    
    async def update_agent_performance(self, agent_id: str, task_result: Dict[str, Any]):
        """Update agent performance based on task completion"""
        
        performance = self.agent_performance.get(agent_id)
        if not performance:
            return
        
        # Update task counters
        performance.total_tasks += 1
        
        if task_result.get('success', False):
            performance.successful_tasks += 1
            performance.last_success = datetime.now()
            
            # Update quality average
            quality = task_result.get('quality_score', 0.0)
            performance.average_quality = self._update_average(
                performance.average_quality, quality, performance.successful_tasks
            )
            
            # Update specialization score for this task type
            task_type = task_result.get('task_type')
            if task_type:
                current_spec = performance.specialization_scores.get(task_type, 0.5)
                performance.specialization_scores[task_type] = self._update_average(
                    current_spec, quality, 5  # Weight recent performance more
                )
        else:
            performance.failed_tasks += 1
        
        # Update cost and time averages
        if 'cost' in task_result:
            performance.average_cost = self._update_average(
                performance.average_cost, task_result['cost'], performance.total_tasks
            )
        
        if 'processing_time' in task_result:
            performance.average_time = self._update_average(
                performance.average_time, task_result['processing_time'], performance.total_tasks
            )
        
        logger.debug(f"Updated performance for {agent_id}: {performance.success_rate:.2f} success rate")
    
    def _update_average(self, current_avg: float, new_value: float, count: int) -> float:
        """Update running average with new value"""
        if count <= 1:
            return new_value
        return ((current_avg * (count - 1)) + new_value) / count
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get comprehensive routing statistics"""
        
        recent_decisions = [d for d in self.routing_decisions 
                          if (datetime.now() - d['timestamp']).days < 7]
        
        # Calculate routing accuracy (would need feedback loop to measure)
        agent_utilization = {}
        for agent_id, performance in self.agent_performance.items():
            agent_utilization[agent_id] = {
                "total_tasks": performance.total_tasks,
                "success_rate": performance.success_rate,
                "average_quality": performance.average_quality,
                "current_load": performance.current_load,
                "specializations": dict(performance.specialization_scores)
            }
        
        return {
            "total_routing_requests": self.total_routing_requests,
            "recent_decisions": len(recent_decisions),
            "agent_performance": agent_utilization,
            "routing_weights": {
                "quality": self.quality_weight,
                "cost": self.cost_weight, 
                "latency": self.latency_weight
            },
            "average_routing_time_ms": sum(
                d['decision'].get('routing_time_ms', 0) for d in recent_decisions
            ) / len(recent_decisions) if recent_decisions else 0
        }
    
    def adjust_routing_weights(self, quality_weight: float, cost_weight: float, 
                             latency_weight: float):
        """Adjust multi-objective optimization weights"""
        
        # Normalize weights to sum to 1
        total = quality_weight + cost_weight + latency_weight
        
        self.quality_weight = quality_weight / total
        self.cost_weight = cost_weight / total  
        self.latency_weight = latency_weight / total
        
        logger.info(f"Updated routing weights: Q={self.quality_weight:.2f}, "
                   f"C={self.cost_weight:.2f}, L={self.latency_weight:.2f}")
"""
Model capability definitions and routing algorithms for optimal agent selection.

Provides data-driven model selection based on capability vectors, task complexity,
and optimization criteria including quality, cost, and latency.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass
import math


class ModelType(str, Enum):
    """Available AI models in the system"""
    CLAUDE_SONNET = "claude-3-5-sonnet"
    CLAUDE_HAIKU = "claude-3-haiku"  
    GPT4_TURBO = "gpt-4-turbo"
    GPT4O = "gpt-4o"
    GEMINI_FLASH = "gemini-1.5-flash"
    GEMINI_PRO = "gemini-1.5-pro"


class TaskType(str, Enum):
    """Types of tasks that can be assigned to agents"""
    REASONING_LONG = "reasoning_long"      # Complex analysis and planning
    CODE_UI = "code_ui"                    # User interface development  
    CODE_BACKEND = "code_backend"          # Backend/API development
    TEST_GEN = "test_generation"           # Test case generation
    CODE_REVIEW = "code_review"            # Code quality analysis
    DOCUMENTATION = "documentation"        # Technical writing
    DEBUGGING = "debugging"                # Issue diagnosis and fixing
    ARCHITECTURE = "architecture"          # System design


class CapabilityVector(BaseModel):
    """Capability scores for a specific model across different dimensions"""
    
    model_type: ModelType = Field(..., description="Model identifier")
    
    # Core capability scores (0.0 to 1.0)
    reasoning_long: float = Field(..., ge=0.0, le=1.0, description="Complex reasoning and analysis")
    code_ui: float = Field(..., ge=0.0, le=1.0, description="UI/UX development capability")  
    code_backend: float = Field(..., ge=0.0, le=1.0, description="Backend development capability")
    test_gen: float = Field(..., ge=0.0, le=1.0, description="Test generation capability")
    code_review: float = Field(..., ge=0.0, le=1.0, description="Code review and analysis")
    documentation: float = Field(..., ge=0.0, le=1.0, description="Technical writing")
    debugging: float = Field(..., ge=0.0, le=1.0, description="Debugging and troubleshooting")
    architecture: float = Field(..., ge=0.0, le=1.0, description="System architecture design")
    
    # Performance characteristics  
    latency_score: float = Field(..., ge=0.0, le=1.0, description="Speed score (higher = faster)")
    cost_score: float = Field(..., ge=0.0, le=1.0, description="Cost efficiency (higher = cheaper)")
    context_length: int = Field(..., description="Maximum context length")
    
    # Model metadata
    version: str = Field(..., description="Model version")
    provider: str = Field(..., description="Model provider")
    last_updated: str = Field(..., description="Last capability assessment date")
    
    def get_capability_for_task(self, task_type: TaskType) -> float:
        """Get capability score for specific task type"""
        capability_mapping = {
            TaskType.REASONING_LONG: self.reasoning_long,
            TaskType.CODE_UI: self.code_ui,
            TaskType.CODE_BACKEND: self.code_backend,
            TaskType.TEST_GEN: self.test_gen,
            TaskType.CODE_REVIEW: self.code_review,
            TaskType.DOCUMENTATION: self.documentation,
            TaskType.DEBUGGING: self.debugging,
            TaskType.ARCHITECTURE: self.architecture,
        }
        return capability_mapping.get(task_type, 0.0)


class TaskComplexity(BaseModel):
    """Feature vectors for task complexity assessment"""
    
    # Complexity dimensions (0.0 to 1.0)
    technical_complexity: float = Field(..., ge=0.0, le=1.0, description="Technical difficulty")
    novelty: float = Field(..., ge=0.0, le=1.0, description="How new/unusual the task is")
    safety_risk: float = Field(..., ge=0.0, le=1.0, description="Safety/security risk level")
    context_requirement: float = Field(..., ge=0.0, le=1.0, description="Amount of context needed")
    interdependence: float = Field(..., ge=0.0, le=1.0, description="Dependencies on other tasks")
    
    # Task characteristics
    estimated_tokens: int = Field(..., description="Estimated token count")
    requires_reasoning: bool = Field(default=False, description="Requires complex reasoning")
    requires_creativity: bool = Field(default=False, description="Requires creative thinking") 
    time_sensitive: bool = Field(default=False, description="Time-critical task")
    
    def get_complexity_score(self) -> float:
        """Calculate overall complexity score"""
        dimensions = [
            self.technical_complexity,
            self.novelty, 
            self.safety_risk,
            self.context_requirement,
            self.interdependence
        ]
        return sum(dimensions) / len(dimensions)


class ModelCapability(BaseModel):
    """Complete model capability profile with routing metadata"""
    
    model_type: ModelType = Field(..., description="Model identifier")
    display_name: str = Field(..., description="Human-readable model name")
    capabilities: CapabilityVector = Field(..., description="Capability scores")
    
    # Operational characteristics
    max_concurrent_tasks: int = Field(default=5, description="Max parallel tasks")
    avg_response_time_ms: float = Field(..., description="Average response time")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Historical error rate")
    availability: float = Field(..., ge=0.0, le=1.0, description="Service availability")
    
    # Cost and resource usage
    cost_per_1k_tokens: float = Field(..., description="Cost per 1000 tokens")
    tokens_per_minute_limit: int = Field(..., description="Rate limit")
    
    # Specialization areas
    best_task_types: List[TaskType] = Field(..., description="Tasks this model excels at")
    avoid_task_types: List[TaskType] = Field(default_factory=list, description="Tasks to avoid")
    
    # Routing preferences
    preferred_for_safety: bool = Field(default=False, description="Preferred for safety-critical tasks")
    preferred_for_speed: bool = Field(default=False, description="Preferred for time-critical tasks")
    preferred_for_cost: bool = Field(default=False, description="Preferred for cost optimization")


class RoutingDecision(BaseModel):
    """Result of model selection algorithm with scoring details"""
    
    selected_model: ModelType = Field(..., description="Selected model")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in selection")
    
    # Scoring breakdown
    quality_score: float = Field(..., description="Quality score for this task")
    cost_score: float = Field(..., description="Cost efficiency score")
    latency_score: float = Field(..., description="Speed score")
    availability_score: float = Field(..., description="Availability score")
    final_score: float = Field(..., description="Final weighted score")
    
    # Alternative options
    alternatives: List[Tuple[ModelType, float]] = Field(default_factory=list, description="Alternative models with scores")
    
    # Decision context
    task_type: TaskType = Field(..., description="Task type being routed")
    complexity: TaskComplexity = Field(..., description="Task complexity assessment")
    routing_parameters: Dict[str, float] = Field(..., description="Routing algorithm parameters")
    
    # Execution guidance
    estimated_completion_time: Optional[float] = Field(None, description="Estimated completion time in minutes")
    suggested_timeout: Optional[float] = Field(None, description="Suggested timeout in minutes")
    retry_strategy: str = Field(default="exponential_backoff", description="Retry strategy if failed")


class ModelRouter(BaseModel):
    """Data-driven model router with optimization algorithms"""
    
    available_models: List[ModelCapability] = Field(..., description="Available models")
    
    # Routing algorithm parameters
    quality_weight: float = Field(default=0.7, description="Weight for quality in routing decision")
    cost_weight: float = Field(default=0.2, description="Weight for cost optimization") 
    latency_weight: float = Field(default=0.1, description="Weight for speed optimization")
    
    # Constraints
    max_cost_per_task: Optional[float] = Field(None, description="Maximum cost per task")
    max_latency_ms: Optional[float] = Field(None, description="Maximum acceptable latency")
    require_high_availability: bool = Field(default=True, description="Require high availability models")
    
    def calculate_routing_score(self, model: ModelCapability, task_type: TaskType, 
                              complexity: TaskComplexity) -> float:
        """
        Calculate routing score using: argmax(quality - λ·cost - μ·latency)
        """
        capability_score = model.capabilities.get_capability_for_task(task_type)
        
        # Adjust for complexity - more complex tasks need higher capability
        complexity_adjustment = 1.0 + (complexity.get_complexity_score() * 0.5)
        quality_score = capability_score * complexity_adjustment
        
        # Cost score (normalized, higher is better)
        cost_score = model.capabilities.cost_score
        
        # Latency score (normalized, higher is better) 
        latency_score = model.capabilities.latency_score
        
        # Apply routing formula: quality - λ·cost - μ·latency
        # Convert to maximization problem (higher scores are better)
        final_score = (
            quality_score * self.quality_weight +
            cost_score * self.cost_weight + 
            latency_score * self.latency_weight
        )
        
        return final_score
    
    def route_task(self, task_type: TaskType, complexity: TaskComplexity,
                   constraints: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        """
        Route task to optimal model based on capability vectors and constraints
        """
        if not self.available_models:
            raise ValueError("No models available for routing")
        
        model_scores = []
        
        for model in self.available_models:
            # Check hard constraints
            if constraints:
                if (constraints.get('max_cost') and 
                    model.cost_per_1k_tokens > constraints['max_cost']):
                    continue
                if (constraints.get('min_availability') and 
                    model.availability < constraints['min_availability']):
                    continue
            
            # Calculate routing score
            score = self.calculate_routing_score(model, task_type, complexity)
            model_scores.append((model, score))
        
        if not model_scores:
            raise ValueError("No models satisfy the given constraints")
        
        # Sort by score (highest first)
        model_scores.sort(key=lambda x: x[1], reverse=True)
        best_model, best_score = model_scores[0]
        
        # Calculate component scores for transparency
        capability_score = best_model.capabilities.get_capability_for_task(task_type)
        quality_score = capability_score * (1.0 + complexity.get_complexity_score() * 0.5)
        
        # Estimate completion time based on complexity and model speed
        base_time = complexity.estimated_tokens / 1000  # Base time per 1k tokens
        speed_factor = best_model.capabilities.latency_score
        estimated_time = base_time / max(speed_factor, 0.1)  # Prevent division by zero
        
        return RoutingDecision(
            selected_model=best_model.model_type,
            confidence=min(best_score, 1.0),
            quality_score=quality_score,
            cost_score=best_model.capabilities.cost_score,
            latency_score=best_model.capabilities.latency_score,
            availability_score=best_model.availability,
            final_score=best_score,
            alternatives=[(m.model_type, s) for m, s in model_scores[1:3]],  # Top 3 alternatives
            task_type=task_type,
            complexity=complexity,
            routing_parameters={
                'quality_weight': self.quality_weight,
                'cost_weight': self.cost_weight,
                'latency_weight': self.latency_weight
            },
            estimated_completion_time=estimated_time,
            suggested_timeout=estimated_time * 2.5  # 2.5x buffer for timeout
        )


# Pre-defined capability vectors for available models
MODEL_CAPABILITIES = [
    ModelCapability(
        model_type=ModelType.CLAUDE_SONNET,
        display_name="Claude 3.5 Sonnet",
        capabilities=CapabilityVector(
            model_type=ModelType.CLAUDE_SONNET,
            reasoning_long=0.95,
            code_ui=0.85,
            code_backend=0.90,
            test_gen=0.80,
            code_review=0.92,
            documentation=0.95,
            debugging=0.88,
            architecture=0.93,
            latency_score=0.75,
            cost_score=0.60,
            context_length=200000,
            version="20241022",
            provider="Anthropic",
            last_updated="2024-10-22"
        ),
        max_concurrent_tasks=5,
        avg_response_time_ms=2500,
        error_rate=0.02,
        availability=0.99,
        cost_per_1k_tokens=0.003,
        tokens_per_minute_limit=4000,
        best_task_types=[TaskType.REASONING_LONG, TaskType.ARCHITECTURE, TaskType.DOCUMENTATION],
        preferred_for_safety=True
    ),
    
    ModelCapability(
        model_type=ModelType.GPT4O,
        display_name="GPT-4o", 
        capabilities=CapabilityVector(
            model_type=ModelType.GPT4O,
            reasoning_long=0.88,
            code_ui=0.82,
            code_backend=0.92,
            test_gen=0.85,
            code_review=0.87,
            documentation=0.85,
            debugging=0.85,
            architecture=0.85,
            latency_score=0.85,
            cost_score=0.70,
            context_length=128000,
            version="2024-08-06",
            provider="OpenAI",
            last_updated="2024-08-06"
        ),
        max_concurrent_tasks=8,
        avg_response_time_ms=1800,
        error_rate=0.03,
        availability=0.98,
        cost_per_1k_tokens=0.005,
        tokens_per_minute_limit=10000,
        best_task_types=[TaskType.CODE_BACKEND, TaskType.TEST_GEN],
        preferred_for_speed=True
    ),
    
    ModelCapability(
        model_type=ModelType.GEMINI_FLASH,
        display_name="Gemini 1.5 Flash",
        capabilities=CapabilityVector(
            model_type=ModelType.GEMINI_FLASH,
            reasoning_long=0.78,
            code_ui=0.88,
            code_backend=0.80,
            test_gen=0.75,
            code_review=0.75,
            documentation=0.80,
            debugging=0.78,
            architecture=0.75,
            latency_score=0.95,
            cost_score=0.90,
            context_length=1000000,
            version="1.5",
            provider="Google",
            last_updated="2024-05-14"
        ),
        max_concurrent_tasks=10,
        avg_response_time_ms=1200,
        error_rate=0.04,
        availability=0.97,
        cost_per_1k_tokens=0.001,
        tokens_per_minute_limit=15000,
        best_task_types=[TaskType.CODE_UI],
        preferred_for_cost=True,
        preferred_for_speed=True
    )
]

# Example usage
EXAMPLE_ROUTER = ModelRouter(available_models=MODEL_CAPABILITIES)

EXAMPLE_TASK_COMPLEXITY = TaskComplexity(
    technical_complexity=0.8,
    novelty=0.6,
    safety_risk=0.3,
    context_requirement=0.7,
    interdependence=0.5,
    estimated_tokens=5000,
    requires_reasoning=True,
    time_sensitive=False
)
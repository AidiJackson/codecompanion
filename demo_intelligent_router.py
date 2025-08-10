#!/usr/bin/env python3
"""
Demonstration of the Intelligent Model Router with Learning System

This demo shows how the enhanced router system works with Thompson Sampling
bandit learning, cost governance, and performance tracking.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

from core.model_router import IntelligentRouter
from schemas.outcomes import TaskOutcome
from core.cost_governor import ProjectComplexity
from schemas.routing import ModelType, TaskType, TaskComplexity


def create_sample_task(task_description: str, task_type: TaskType, 
                      complexity_level: float = 0.5) -> Dict[str, Any]:
    """Create a sample task for routing demonstration"""
    return {
        'description': task_description,
        'context': {
            'task_type': task_type,
            'project_complexity': 'medium',
            'estimated_tokens': int(1000 + complexity_level * 2000),
            'time_sensitive': complexity_level > 0.7,
            'cost_sensitive': False,
            'quality_priority': 0.8
        }
    }


def simulate_task_execution(model_type: ModelType, task: Dict[str, Any]) -> TaskOutcome:
    """Simulate task execution and generate realistic outcomes"""
    import random
    
    # Simulate execution based on model capabilities
    model_performance = {
        ModelType.CLAUDE_SONNET: {'quality': 0.9, 'speed': 0.75, 'reliability': 0.95},
        ModelType.GPT4O: {'quality': 0.88, 'speed': 0.8, 'reliability': 0.92},
        ModelType.GEMINI_FLASH: {'quality': 0.82, 'speed': 0.95, 'reliability': 0.9},
        ModelType.GPT4_TURBO: {'quality': 0.85, 'speed': 0.85, 'reliability': 0.88},
        ModelType.CLAUDE_HAIKU: {'quality': 0.75, 'speed': 0.95, 'reliability': 0.85},
        ModelType.GEMINI_PRO: {'quality': 0.87, 'speed': 0.7, 'reliability': 0.93}
    }
    
    perf = model_performance.get(model_type, {'quality': 0.7, 'speed': 0.8, 'reliability': 0.8})
    
    # Add some randomness
    quality_noise = random.gauss(0, 0.1)
    speed_noise = random.gauss(0, 0.2)
    
    # Calculate outcomes
    quality_score = max(0.0, min(1.0, perf['quality'] + quality_noise))
    base_time = 30.0 + task['context']['estimated_tokens'] / 100
    execution_time = base_time / (perf['speed'] + speed_noise)
    success = random.random() < perf['reliability']
    
    # Cost calculation
    model_costs = {
        ModelType.CLAUDE_SONNET: 0.003,
        ModelType.CLAUDE_HAIKU: 0.0005,
        ModelType.GPT4O: 0.005,
        ModelType.GPT4_TURBO: 0.003,
        ModelType.GEMINI_FLASH: 0.0002,
        ModelType.GEMINI_PRO: 0.001
    }
    
    tokens_used = task['context']['estimated_tokens']
    cost = tokens_used * model_costs.get(model_type, 0.003) / 1000
    
    # Create complexity object
    complexity = TaskComplexity(
        technical_complexity=task['context'].get('complexity_level', 0.5),
        novelty=0.3,
        safety_risk=0.1,
        context_requirement=0.4,
        interdependence=0.2,
        estimated_tokens=tokens_used,
        requires_reasoning=task['context']['task_type'] == TaskType.REASONING_LONG,
        requires_creativity=task['context']['task_type'] == TaskType.CODE_UI,
        time_sensitive=task['context'].get('time_sensitive', False)
    )
    
    return TaskOutcome(
        task_id=f"demo_task_{int(time.time())}",
        model_used=model_type,
        task_type=task['context']['task_type'],
        complexity=complexity,
        success=success,
        quality_score=quality_score,
        execution_time=execution_time,
        token_usage=tokens_used,
        cost=cost,
        context=task['context'],
        error_type=None if success else "simulation_error",
        timestamp=datetime.now()
    )


async def demo_intelligent_routing():
    """Main demonstration of intelligent routing capabilities"""
    print("🤖 Intelligent Model Router with Learning - Demo")
    print("=" * 60)
    
    # Initialize the router
    print("Initializing Intelligent Router...")
    router = IntelligentRouter()
    
    # Demo tasks of different types and complexities
    demo_tasks = [
        create_sample_task(
            "Design a comprehensive system architecture for a distributed microservices platform",
            TaskType.ARCHITECTURE, 0.9
        ),
        create_sample_task(
            "Create a responsive user interface for a mobile app dashboard",
            TaskType.CODE_UI, 0.6
        ),
        create_sample_task(
            "Implement a REST API with authentication and rate limiting",
            TaskType.CODE_BACKEND, 0.7
        ),
        create_sample_task(
            "Generate comprehensive test cases for a payment processing system",
            TaskType.TEST_GEN, 0.8
        ),
        create_sample_task(
            "Debug intermittent connection issues in a database client",
            TaskType.DEBUGGING, 0.5
        ),
        create_sample_task(
            "Write technical documentation for API endpoints",
            TaskType.DOCUMENTATION, 0.4
        )
    ]
    
    print(f"\nProcessing {len(demo_tasks)} demonstration tasks...")
    print("-" * 60)
    
    # Process tasks and demonstrate learning
    for i, task in enumerate(demo_tasks, 1):
        print(f"\n🔄 Task {i}: {task['description'][:50]}...")
        print(f"   Type: {task['context']['task_type'].value}")
        print(f"   Estimated tokens: {task['context']['estimated_tokens']}")
        
        # Route the task
        try:
            routing_decision = router.route_task(task, task['context'])
            selected_model = routing_decision['selected_model']
            
            print(f"   ✅ Routed to: {selected_model.value}")
            print(f"   🎯 Routing score: {routing_decision['routing_score']:.3f}")
            
            # Show alternative models considered
            alternatives = routing_decision.get('alternatives', [])[:2]
            if alternatives:
                alt_text = ", ".join([f"{alt[0].value} ({alt[1]:.3f})" for alt in alternatives])
                print(f"   📋 Alternatives: {alt_text}")
            
            # Simulate task execution
            print("   ⚡ Executing task...")
            outcome = simulate_task_execution(selected_model, task)
            
            print(f"   📊 Results:")
            print(f"      Success: {'✅' if outcome.success else '❌'}")
            print(f"      Quality: {outcome.quality_score:.3f}")
            print(f"      Time: {outcome.execution_time:.1f}s")
            print(f"      Cost: ${outcome.cost:.4f}")
            
            # Update router learning
            router.update_from_outcome(outcome.task_id, outcome)
            
            # Small delay to simulate real processing
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("📈 Learning and Performance Analysis")
    print("=" * 60)
    
    # Show performance summary
    performance_summary = router.get_model_performance_summary()
    if performance_summary:
        print("\n🎯 Model Performance Summary:")
        for model, tasks in performance_summary.items():
            print(f"\n{model}:")
            for task_type, metrics in tasks.items():
                print(f"  {task_type}:")
                print(f"    Success Rate: {metrics['success_rate']:.3f}")
                print(f"    Avg Quality: {metrics['avg_quality']:.3f}")
                print(f"    Avg Cost: ${metrics['avg_cost']:.4f}")
                print(f"    Sample Count: {metrics['sample_count']}")
    
    # Show bandit statistics
    bandit_stats = router.bandit.get_arm_statistics()
    print(f"\n🎰 Thompson Sampling Bandit Statistics:")
    for arm_id, stats in bandit_stats.items():
        print(f"\n{arm_id}:")
        print(f"  Estimated Mean: {stats['estimated_mean']:.3f}")
        ci_lower, ci_upper = stats['confidence_interval']
        print(f"  Confidence Interval: [{ci_lower:.3f}, {ci_upper:.3f}]")
        print(f"  Total Pulls: {stats['total_pulls']}")
    
    # Show cost governance summary
    usage_summary = router.cost_governor.get_usage_summary("demo_project")
    print(f"\n💰 Cost Governance Summary:")
    if 'current_usage' in usage_summary:
        usage = usage_summary['current_usage']
        budget = usage_summary['budget_limits']
        utilization = usage_summary['utilization']
        
        print(f"  Current Usage:")
        print(f"    Tokens: {usage['tokens_used']:,} / {budget['max_tokens']:,} "
              f"({utilization['tokens_percent']:.1f}%)")
        print(f"    Cost: ${usage['cost_incurred']:.2f} / ${budget['max_cost_usd']:.2f} "
              f"({utilization['cost_percent']:.1f}%)")
        print(f"    Requests: {usage['requests_made']} / {budget['max_requests']} "
              f"({utilization['requests_percent']:.1f}%)")
    
    # Generate insights from router data
    try:
        # Generate basic insights from bandit statistics
        bandit_stats = router.bandit.get_arm_statistics()
        if bandit_stats:
            best_model = max(bandit_stats.items(), key=lambda x: x[1]['estimated_mean'])
            
            print(f"\n🔍 AI Insights:")
            print(f"  Best performing model: {best_model[0]} (score: {best_model[1]['estimated_mean']:.3f})")
            
            # Identify models that need more exploration
            underexplored = [model for model, stats in bandit_stats.items() if stats['total_pulls'] == 0]
            if underexplored:
                print(f"  Models needing exploration: {', '.join(underexplored)}")
                
    except Exception as e:
        print(f"  Error generating insights: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Demo Complete! The router has learned from task outcomes")
    print("and will continue to improve its routing decisions over time.")
    print("=" * 60)


def demo_cost_governance():
    """Demonstrate cost governance features"""
    print("\n💰 Cost Governance Demonstration")
    print("-" * 40)
    
    from core.cost_governor import CostGovernor
    cost_governor = CostGovernor()
    
    # Show budget limits for different project complexities
    print("Budget Limits by Project Complexity:")
    for complexity in ProjectComplexity:
        budget = cost_governor.budgets[complexity]
        print(f"\n{complexity.value.title()}:")
        print(f"  Max Tokens: {budget.max_tokens:,}")
        print(f"  Max Cost: ${budget.max_cost_usd}")
        print(f"  Max Agents: {budget.max_agents}")
        print(f"  Max Requests: {budget.max_requests}")
    
    # Demo cost optimization suggestions
    print(f"\n🔧 Cost Optimization Example:")
    context = {
        'estimated_tokens': 5000,
        'project_complexity': 'medium',
        'task_type': TaskType.CODE_BACKEND
    }
    
    suggested_model = cost_governor.suggest_cost_optimization(
        "demo_project", ModelType.GPT4O, context
    )
    
    if suggested_model:
        original_cost = cost_governor.estimate_cost(ModelType.GPT4O, 5000)
        optimized_cost = cost_governor.estimate_cost(suggested_model, 5000)
        savings = original_cost - optimized_cost
        
        print(f"Original Model: {ModelType.GPT4O.value} (${original_cost:.4f})")
        print(f"Suggested Model: {suggested_model.value} (${optimized_cost:.4f})")
        print(f"Potential Savings: ${savings:.4f} ({savings/original_cost*100:.1f}%)")


if __name__ == "__main__":
    print("Starting Intelligent Model Router Demo...\n")
    
    # Run the main demo
    asyncio.run(demo_intelligent_routing())
    
    # Run cost governance demo
    demo_cost_governance()
    
    print("\n🚀 Try running this demo multiple times to see how the")
    print("   router learns and adapts its decisions over time!")
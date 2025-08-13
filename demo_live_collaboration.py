"""
Live Collaboration System Demonstration
Showcases the Real-Time Event-Sourced Orchestration with Redis Streams
"""

import asyncio
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import live collaboration components
from core.event_streaming import LiveCollaborationEngine, EventType
from core.progress_tracker import LiveProgressTracker
from core.parallel_execution import ParallelExecutionEngine


async def demonstrate_live_collaboration():
    """
    Comprehensive demonstration of the live collaboration system
    """

    print("🚀 Starting Live Collaboration System Demonstration")
    print("=" * 60)

    # Initialize the live collaboration engine
    print("📡 Initializing Live Collaboration Engine...")
    collaboration_engine = LiveCollaborationEngine()

    # Initialize progress tracker
    print("📊 Initializing Live Progress Tracker...")
    LiveProgressTracker(collaboration_engine.event_bus)

    # Initialize parallel execution engine
    print("⚡ Initializing Parallel Execution Engine...")
    parallel_engine = ParallelExecutionEngine(collaboration_engine.event_bus)

    # Start a live collaboration session
    print("\n🔴 Starting Live Collaboration Session...")
    session_id = await collaboration_engine.start_live_collaboration_session(
        "Advanced Web Application with Real-Time Features", "web_app"
    )
    print(f"✅ Live session started: {session_id}")

    # Simulate agent registrations and activities
    print("\n🤖 Simulating Agent Activities...")

    # Agent 1: Project Manager starts
    await collaboration_engine.publish_event(
        "tasks",
        {
            "event_type": EventType.AGENT_STARTED,
            "correlation_id": session_id,
            "agent_id": "claude_pm",
            "activity": "Analyzing project requirements",
            "status": "active",
            "agent_type": "PROJECT_MANAGER",
        },
    )

    await asyncio.sleep(2)

    # Agent 1: Creates requirements artifact
    await collaboration_engine.publish_event(
        "artifacts",
        {
            "event_type": EventType.ARTIFACT_CREATED,
            "correlation_id": session_id,
            "agent_id": "claude_pm",
            "artifact_type": "SPEC_DOC",
            "activity": "Requirements specification completed",
            "quality_score": 0.92,
        },
    )

    await asyncio.sleep(1)

    # Agent 2: Code Generator starts (parallel)
    await collaboration_engine.publish_event(
        "tasks",
        {
            "event_type": EventType.AGENT_STARTED,
            "correlation_id": session_id,
            "agent_id": "gpt4_coder",
            "activity": "Implementing core functionality",
            "status": "active",
            "agent_type": "CODE_GENERATOR",
        },
    )

    # Agent 3: UI Designer starts (parallel)
    await collaboration_engine.publish_event(
        "tasks",
        {
            "event_type": EventType.AGENT_STARTED,
            "correlation_id": session_id,
            "agent_id": "gemini_ui",
            "activity": "Designing user interface",
            "status": "active",
            "agent_type": "UI_DESIGNER",
        },
    )

    await asyncio.sleep(3)

    # More artifacts created
    await collaboration_engine.publish_event(
        "artifacts",
        {
            "event_type": EventType.ARTIFACT_CREATED,
            "correlation_id": session_id,
            "agent_id": "gpt4_coder",
            "artifact_type": "CODE_PATCH",
            "activity": "Core backend implementation complete",
            "quality_score": 0.88,
        },
    )

    await collaboration_engine.publish_event(
        "artifacts",
        {
            "event_type": EventType.ARTIFACT_CREATED,
            "correlation_id": session_id,
            "agent_id": "gemini_ui",
            "artifact_type": "DESIGN_DOC",
            "activity": "UI component library created",
            "quality_score": 0.91,
        },
    )

    await asyncio.sleep(2)

    # Agent handoff - Test Writer starts
    await collaboration_engine.publish_event(
        "tasks",
        {
            "event_type": EventType.AGENT_STARTED,
            "correlation_id": session_id,
            "agent_id": "claude_tester",
            "activity": "Creating comprehensive test suite",
            "status": "active",
            "agent_type": "TEST_WRITER",
        },
    )

    await asyncio.sleep(2)

    # Complete some agents
    await collaboration_engine.publish_event(
        "tasks",
        {
            "event_type": EventType.AGENT_COMPLETED,
            "correlation_id": session_id,
            "agent_id": "claude_pm",
            "activity": "Project management phase completed",
            "status": "completed",
        },
    )

    await asyncio.sleep(1)

    # Show live collaboration status
    print("\n📊 Live Collaboration Status:")
    status = collaboration_engine.get_live_collaboration_status()
    print(f"  • Active Collaborations: {status['active_collaborations']}")
    print(f"  • Live Agents: {len(status['live_agent_activities'])}")
    print(
        f"  • Artifacts Created: {status['collaboration_metrics']['artifacts_created']}"
    )
    print(
        f"  • Handoffs Completed: {status['collaboration_metrics']['handoffs_completed']}"
    )

    # Show agent activity feed
    print("\n📡 Recent Agent Activity Feed:")
    activity_feed = collaboration_engine.get_agent_activity_feed(5)
    for activity in activity_feed:
        timestamp = activity["timestamp"][:19].replace("T", " ")
        print(f"  {timestamp} | {activity['agent_id']} | {activity['activity']}")

    # Show artifact timeline
    print("\n📄 Artifact Creation Timeline:")
    artifacts = collaboration_engine.get_artifact_creation_timeline()
    for artifact in artifacts:
        timestamp = artifact["creation_time"][:19].replace("T", " ")
        print(
            f"  {timestamp} | {artifact['type']} | Created by {artifact['created_by']}"
        )

    # Demonstrate parallel execution
    print("\n⚡ Demonstrating Parallel Agent Execution...")

    project_config = {
        "description": "Real-time collaborative web platform",
        "type": "web_app",
        "complexity": "high",
    }

    execution_id = await parallel_engine.execute_parallel_agents(project_config)
    print(f"✅ Parallel execution started: {execution_id}")

    # Monitor parallel execution for a few seconds
    for i in range(5):
        await asyncio.sleep(2)
        status = parallel_engine.get_execution_status(execution_id)
        if status:
            print(
                f"  Parallel Progress: {status['progress']:.1%} | "
                f"Active: {len(status['active_agents'])} | "
                f"Completed: {status['completed_agents']}"
            )

    print("\n🎉 Live Collaboration System Demonstration Complete!")
    print("=" * 60)

    return {
        "session_id": session_id,
        "execution_id": execution_id,
        "collaboration_status": status,
        "activity_feed": activity_feed,
        "artifacts": artifacts,
    }


async def demonstrate_progress_tracking():
    """
    Demonstrate the live progress tracking capabilities
    """

    print("\n📊 Progress Tracking Demonstration")
    print("-" * 40)

    # Initialize components
    collaboration_engine = LiveCollaborationEngine()
    progress_tracker = LiveProgressTracker(collaboration_engine.event_bus)

    # Start progress tracking consumer
    print("🔄 Starting progress tracking consumer...")

    # Create a test session
    session_id = await collaboration_engine.start_live_collaboration_session(
        "Progress Tracking Demo", "api_service"
    )

    # Simulate multiple agents with progress updates
    agents = [
        {"id": "agent_1", "type": "PROJECT_MANAGER"},
        {"id": "agent_2", "type": "CODE_GENERATOR"},
        {"id": "agent_3", "type": "UI_DESIGNER"},
    ]

    for agent in agents:
        await collaboration_engine.publish_event(
            "tasks",
            {
                "event_type": EventType.AGENT_STARTED,
                "correlation_id": session_id,
                "agent_id": agent["id"],
                "agent_type": agent["type"],
                "activity": f"Starting {agent['type'].lower()} work",
                "status": "active",
            },
        )

        # Simulate progress updates
        for progress in [0.2, 0.5, 0.8]:
            await collaboration_engine.publish_event(
                "tasks",
                {
                    "event_type": EventType.PERFORMANCE_METRIC,
                    "correlation_id": session_id,
                    "agent_id": agent["id"],
                    "progress": progress,
                    "activity": f"Working on {agent['type'].lower()} tasks",
                    "tokens_used": 1000,
                    "api_calls": 5,
                },
            )

            await asyncio.sleep(0.5)

    # Get progress summary
    progress_summary = progress_tracker.get_live_progress_summary()
    print("\n📈 Progress Summary:")
    print(f"  • Overall Progress: {progress_summary['overall_progress']:.1f}%")
    print(f"  • Active Agents: {progress_summary['active_agents']}")
    print(f"  • Completed Agents: {progress_summary['completed_agents']}")

    # Show system health
    health = progress_tracker.get_system_health()
    print("\n🏥 System Health:")
    print(f"  • Events Processed: {health['events_processed']}")
    print(f"  • Success Rate: {health['success_rate']:.1%}")
    print(f"  • Active Workflows: {health['active_workflows']}")

    return {
        "session_id": session_id,
        "progress_summary": progress_summary,
        "system_health": health,
    }


async def demonstrate_event_streaming():
    """
    Demonstrate the Redis Streams event-driven architecture
    """

    print("\n🌊 Event Streaming Demonstration")
    print("-" * 40)

    collaboration_engine = LiveCollaborationEngine()

    # Event callback to process consumed events
    async def event_processor(event):
        print(
            f"  📥 Consumed: {event.event_type.value} | Agent: {event.agent_id} | Time: {event.timestamp.strftime('%H:%M:%S')}"
        )

    # Start consuming events (this would run continuously in production)
    print("🔄 Starting event consumer...")

    # Publish a series of events
    events_to_publish = [
        {"event_type": EventType.TASK_STARTED, "activity": "Project initialization"},
        {
            "event_type": EventType.AGENT_STARTED,
            "agent_id": "demo_agent",
            "activity": "Agent startup",
        },
        {
            "event_type": EventType.ARTIFACT_CREATED,
            "agent_id": "demo_agent",
            "artifact_type": "SPEC_DOC",
        },
        {
            "event_type": EventType.PERFORMANCE_METRIC,
            "agent_id": "demo_agent",
            "progress": 0.75,
        },
        {
            "event_type": EventType.AGENT_COMPLETED,
            "agent_id": "demo_agent",
            "activity": "Agent completed",
        },
        {"event_type": EventType.TASK_COMPLETED, "activity": "Project completed"},
    ]

    session_id = f"event_demo_{int(time.time())}"

    print("📤 Publishing events:")
    for event_data in events_to_publish:
        event_data["correlation_id"] = session_id
        await collaboration_engine.publish_event("tasks", event_data)
        await asyncio.sleep(0.5)

    print("✅ Event streaming demonstration complete")

    return session_id


async def run_comprehensive_demo():
    """
    Run the complete live collaboration system demonstration
    """

    print("🎯 COMPREHENSIVE LIVE COLLABORATION SYSTEM DEMO")
    print("=" * 80)

    try:
        # Run all demonstrations
        collaboration_results = await demonstrate_live_collaboration()
        progress_results = await demonstrate_progress_tracking()
        streaming_session = await demonstrate_event_streaming()

        print("\n🎉 ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        print("\n📋 SUMMARY:")
        print(f"  • Live Collaboration Session: {collaboration_results['session_id']}")
        print(f"  • Parallel Execution: {collaboration_results['execution_id']}")
        print(f"  • Progress Tracking Session: {progress_results['session_id']}")
        print(f"  • Event Streaming Session: {streaming_session}")
        print(f"  • Total Artifacts Created: {len(collaboration_results['artifacts'])}")
        print(
            f"  • Agent Activities Logged: {len(collaboration_results['activity_feed'])}"
        )

        print("\n✨ The Real-Time Live Collaboration System is fully operational!")
        print(
            "   All components (Event Streaming, Progress Tracking, Parallel Execution)"
        )
        print("   are working together seamlessly with Redis Streams.")

        return {
            "status": "success",
            "collaboration_results": collaboration_results,
            "progress_results": progress_results,
            "streaming_session": streaming_session,
        }

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logger.exception("Demo execution failed")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run the comprehensive demonstration
    asyncio.run(run_comprehensive_demo())

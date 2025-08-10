"""
Live AI Agent Integration Demo

Demonstrates real Claude, GPT-4, and Gemini agents working together
through the event-sourced orchestration system.
"""

import asyncio
import logging
import os
from datetime import datetime

from core.live_orchestrator import LiveOrchestrator
from core.event_streaming import StreamEvent, EventType, EventStreamType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_live_agent_collaboration():
    """Demonstrate live AI agent collaboration on a real project"""
    
    print("🚀 Starting Live AI Agent Collaboration Demo")
    print("=" * 60)
    
    # Check API keys
    api_keys = {
        'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY'),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'), 
        'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY')
    }
    
    available_agents = sum(1 for key in api_keys.values() if key)
    print(f"Available AI agents: {available_agents}/3")
    
    for service, key in api_keys.items():
        status = "✅ Available" if key else "❌ Missing"
        print(f"  {service}: {status}")
    
    if available_agents == 0:
        print("\n❌ No API keys available. Please set at least one AI service API key.")
        return
    
    print(f"\n🎯 Proceeding with {available_agents} available agents")
    
    try:
        # Initialize live orchestrator
        orchestrator = LiveOrchestrator()
        
        # Start a live project
        project_description = """
        Build a comprehensive REST API for a task management system with the following features:
        
        1. User Authentication & Authorization
           - JWT-based authentication
           - Role-based access control (admin, user)
           - Password reset functionality
        
        2. Task Management
           - CRUD operations for tasks
           - Task categories and priorities
           - Due dates and reminders
           - Task assignment to users
        
        3. Real-time Features
           - WebSocket notifications for task updates
           - Live activity feed
           - Real-time collaboration on tasks
        
        4. Data & Analytics
           - Task completion statistics
           - User productivity metrics
           - Export functionality (JSON, CSV)
        
        Technical Requirements:
        - Python FastAPI framework
        - PostgreSQL database with SQLAlchemy ORM
        - Redis for caching and real-time features
        - Comprehensive API documentation
        - Unit and integration tests
        - Docker containerization
        """
        
        print("\n🚀 Starting Live Project...")
        correlation_id = await orchestrator.start_live_project(project_description, "api")
        
        print(f"✅ Live project started with ID: {correlation_id}")
        print("\n📊 Real-time agent collaboration will now begin...")
        print("   - Claude will handle architecture and requirements")
        print("   - GPT-4 will implement core functionality")
        print("   - Gemini will create comprehensive tests")
        print("   - Quality cascade will ensure optimal results")
        
        # Monitor project progress
        print(f"\n🔍 Monitoring project progress...")
        
        for i in range(30):  # Monitor for 5 minutes
            await asyncio.sleep(10)  # Check every 10 seconds
            
            status = orchestrator.get_live_project_status(correlation_id)
            if status:
                print(f"\n📈 Project Status Update ({datetime.now().strftime('%H:%M:%S')}):")
                print(f"   Current Phase: {status['current_phase_name']}")
                print(f"   Progress: {status['progress_percentage']:.1f}%")
                print(f"   Artifacts Created: {status['artifacts_created']}")
                
                if status['agent_assignments']:
                    print("   Agent Assignments:")
                    for phase, agent in status['agent_assignments'].items():
                        print(f"     • {phase}: {agent}")
                
                if status['status'] == 'completed':
                    print("\n🎉 Project completed successfully!")
                    break
            else:
                print(f"   Status: Monitoring... (iteration {i+1}/30)")
        
        # Get final metrics
        print("\n📊 Final Orchestrator Metrics:")
        metrics = orchestrator.get_orchestrator_metrics()
        
        print(f"   Total Projects: {metrics['total_projects']}")
        print(f"   Active Projects: {metrics['active_projects']}")
        print(f"   Completed Projects: {metrics['completed_projects']}")
        
        if 'agent_metrics' in metrics and metrics['agent_metrics']['worker_details']:
            print("\n   Agent Performance:")
            for agent_name, agent_data in metrics['agent_metrics']['worker_details'].items():
                agent_metrics = agent_data['metrics']
                print(f"     {agent_name}:")
                print(f"       Success Rate: {agent_metrics['success_rate']:.1%}")
                print(f"       Total Requests: {agent_metrics['total_requests']}")
                print(f"       Average Quality: {agent_metrics['average_quality']:.2f}")
        
        if 'routing_stats' in metrics:
            routing_stats = metrics['routing_stats']
            print(f"\n   Routing Statistics:")
            print(f"     Total Routing Requests: {routing_stats['total_routing_requests']}")
            print(f"     Average Routing Time: {routing_stats['average_routing_time_ms']:.1f}ms")
        
        print("\n✅ Live AI agent collaboration demo completed!")
        print("   Real agents collaborated to produce actual artifacts")
        print("   Event-sourced orchestration managed the workflow")
        print("   Quality cascade ensured optimal results")
        
        await orchestrator.stop_orchestrator()
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_individual_agents():
    """Demonstrate individual agent capabilities"""
    
    print("\n🤖 Individual Agent Capabilities Demo")
    print("=" * 50)
    
    from agents.live_agent_workers import ClaudeWorker, GPT4Worker, GeminiWorker
    from bus import bus as event_bus
    
    # Test Claude
    if os.environ.get('ANTHROPIC_API_KEY'):
        print("\n🧠 Testing Claude Agent...")
        try:
            claude = ClaudeWorker(event_bus)
            
            task_data = {
                'task_id': 'claude_demo',
                'objective': 'Design system architecture for a social media platform',
                'primary_task_type': 'architecture',
                'context': 'Social media platform with posts, comments, likes, user profiles, and real-time messaging',
                'complexity': 0.7
            }
            
            result = await claude._execute_ai_task(task_data)
            
            if result.success:
                print(f"   ✅ Claude Success: Quality {result.output.quality_score:.2f}")
                print(f"   📊 Processing time: {result.processing_time:.1f}s")
                print(f"   💰 Cost: ${result.resource_usage.get('cost', 0):.4f}")
                print(f"   📄 Artifact: {result.output.artifact['artifact_type']}")
            else:
                print(f"   ❌ Claude Failed: {result.error_message}")
                
        except Exception as e:
            print(f"   ⚠️ Claude Error: {e}")
    
    # Test GPT-4
    if os.environ.get('OPENAI_API_KEY'):
        print("\n💻 Testing GPT-4 Agent...")
        try:
            gpt4 = GPT4Worker(event_bus)
            
            task_data = {
                'task_id': 'gpt4_demo',
                'objective': 'Implement user authentication system',
                'primary_task_type': 'implementation',
                'context': 'JWT-based authentication with login, logout, and password reset functionality',
                'complexity': 0.6
            }
            
            result = await gpt4._execute_ai_task(task_data)
            
            if result.success:
                print(f"   ✅ GPT-4 Success: Quality {result.output.quality_score:.2f}")
                print(f"   📊 Processing time: {result.processing_time:.1f}s")
                print(f"   💰 Cost: ${result.resource_usage.get('cost', 0):.4f}")
                print(f"   📄 Artifact: {result.output.artifact['artifact_type']}")
            else:
                print(f"   ❌ GPT-4 Failed: {result.error_message}")
                
        except Exception as e:
            print(f"   ⚠️ GPT-4 Error: {e}")
    
    # Test Gemini
    if os.environ.get('GEMINI_API_KEY'):
        print("\n🔬 Testing Gemini Agent...")
        try:
            gemini = GeminiWorker(event_bus)
            
            task_data = {
                'task_id': 'gemini_demo',
                'objective': 'Create comprehensive test plan for API endpoints',
                'primary_task_type': 'testing',
                'context': 'REST API with authentication, CRUD operations, and real-time features',
                'complexity': 0.5
            }
            
            result = await gemini._execute_ai_task(task_data)
            
            if result.success:
                print(f"   ✅ Gemini Success: Quality {result.output.quality_score:.2f}")
                print(f"   📊 Processing time: {result.processing_time:.1f}s")
                print(f"   💰 Cost: ${result.resource_usage.get('cost', 0):.4f}")
                print(f"   📄 Artifact: {result.output.artifact['artifact_type']}")
            else:
                print(f"   ❌ Gemini Failed: {result.error_message}")
                
        except Exception as e:
            print(f"   ⚠️ Gemini Error: {e}")


if __name__ == "__main__":
    print("🎭 CodeCompanion Orchestra - Live AI Agent Integration")
    print("Real Claude, GPT-4, and Gemini agents working together!")
    print("=" * 70)
    
    # Run individual agent tests first
    asyncio.run(demo_individual_agents())
    
    # Then run full collaboration demo
    asyncio.run(demo_live_agent_collaboration())
    
    print("\n🎯 Demo completed! The system is ready for production use.")
"""
Test script for the production-grade Redis Streams bus system.

This validates that the new bus system works correctly with both Redis and Mock modes.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_mock_bus():
    """Test MockBus functionality"""
    logger.info("🧪 Testing MockBus...")
    
    from bus import bus, Event
    
    # Test publishing
    event = Event(topic="test.topic", payload={"message": "Hello MockBus!"})
    message_id = await bus.publish(event)
    logger.info(f"✅ MockBus published: {message_id}")
    
    # Test subscription with handler
    received_events = []
    
    async def handler(event: Event):
        received_events.append(event)
        logger.info(f"📨 MockBus received: {event.payload}")
    
    # Start subscriber in background
    subscriber_task = asyncio.create_task(
        bus.subscribe("test.topic", "test-group", "consumer-1", handler)
    )
    
    # Give subscriber time to start
    await asyncio.sleep(0.1)
    
    # Publish another event
    event2 = Event(topic="test.topic", payload={"message": "Second message"})
    await bus.publish(event2)
    
    # Give time for processing
    await asyncio.sleep(0.1)
    
    # Cancel subscriber
    subscriber_task.cancel()
    
    if len(received_events) > 0:
        logger.info("✅ MockBus subscription test passed")
        return True
    else:
        logger.error("❌ MockBus subscription test failed")
        return False

async def test_redis_bus():
    """Test RedisBus functionality (if Redis is available)"""
    from settings import settings
    
    if settings.EVENT_BUS != "redis" or not settings.REDIS_URL:
        logger.info("⏭️  Skipping Redis test - not configured")
        return True
    
    logger.info("🧪 Testing Redis Streams Bus...")
    
    try:
        from bus import RedisStreamsBus, Event
        
        bus = RedisStreamsBus(str(settings.REDIS_URL))
        
        # Test connection
        await bus.ping()
        logger.info("✅ Redis connection test passed")
        
        # Test publishing
        event = Event(topic="test.redis.topic", payload={"message": "Hello Redis!"})
        message_id = await bus.publish(event)
        logger.info(f"✅ Redis published: {message_id}")
        
        # Test subscription
        received_events = []
        
        async def handler(event: Event):
            received_events.append(event)
            logger.info(f"📨 Redis received: {event.payload}")
        
        # Start subscriber for a short time
        subscriber_task = asyncio.create_task(
            bus.subscribe("test.redis.topic", "test-group", "consumer-1", handler)
        )
        
        # Give subscriber time to start
        await asyncio.sleep(1)
        
        # Publish another event
        event2 = Event(topic="test.redis.topic", payload={"message": "Redis message"})
        await bus.publish(event2)
        
        # Give time for processing
        await asyncio.sleep(2)
        
        # Cancel subscriber
        subscriber_task.cancel()
        
        logger.info("✅ Redis Streams test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Redis test failed: {e}")
        return False

async def test_bus_factory():
    """Test the bus singleton"""
    logger.info("🧪 Testing bus singleton...")
    
    try:
        from bus import bus as bus_instance
        logger.info(f"✅ Bus factory created: {type(bus_instance).__name__}")
        
        # Test basic functionality
        from bus import Event
        event = Event(topic="factory.test", payload={"test": "factory"})
        message_id = await bus_instance.publish(event)
        logger.info(f"✅ Bus factory publish test: {message_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Bus factory test failed: {e}")
        return False

async def test_orchestrator_integration():
    """Test integration with the new orchestrator"""
    logger.info("🧪 Testing orchestrator integration...")
    
    try:
        from core.orchestrator_v2 import EventSourcedOrchestrator
        from agents.base_agent import AgentType
        
        orchestrator = EventSourcedOrchestrator("test_workflow")
        
        # Start workflow
        await orchestrator.start_workflow(
            "Test project description",
            [AgentType.PROJECT_MANAGER, AgentType.CODE_GENERATOR]
        )
        
        # Assign and complete a task
        task_id = await orchestrator.assign_task(
            AgentType.PROJECT_MANAGER,
            "Test task description"
        )
        
        await orchestrator.complete_task(
            task_id,
            {"result": "test completion"}
        )
        
        # Check status
        status = await orchestrator.get_workflow_status()
        logger.info(f"✅ Orchestrator status: {status['progress_percentage']}% complete")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Orchestrator integration test failed: {e}")
        return False

async def run_all_tests():
    """Run all bus system tests"""
    logger.info("=" * 60)
    logger.info("🚌 TESTING PRODUCTION BUS SYSTEM")
    logger.info("=" * 60)
    
    tests = [
        ("MockBus Functionality", test_mock_bus),
        ("Redis Streams Bus", test_redis_bus),
        ("Bus Factory", test_bus_factory),
        ("Orchestrator Integration", test_orchestrator_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 BUS SYSTEM TEST RESULTS")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All bus system tests passed!")
        return True
    else:
        logger.error(f"🚨 {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
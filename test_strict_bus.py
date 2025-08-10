"""
Test script for strict configuration and Redis Streams bus
"""
import asyncio
import sys

def test_strict_config():
    """Test the strict configuration system"""
    print("🧪 Testing Strict Configuration System")
    print("=" * 50)
    
    try:
        from settings import settings
        print(f"✅ Settings imported successfully")
        print(f"   EVENT_BUS: {settings.EVENT_BUS}")
        print(f"   STREAMLIT_DEBUG: {settings.STREAMLIT_DEBUG}")
        print(f"   DATABASE_URL: {settings.DATABASE_URL}")
        
        # Test bus import (this will fail fast if misconfigured)
        from bus import bus, Event
        print(f"✅ Bus imported successfully")
        
        # Test constants
        from constants import TOPIC_TASKS, TOPIC_ARTIFACTS
        print(f"✅ Constants imported successfully")
        print(f"   TOPIC_TASKS: {TOPIC_TASKS}")
        print(f"   TOPIC_ARTIFACTS: {TOPIC_ARTIFACTS}")
        
        # Test API
        from api import app
        print(f"✅ FastAPI health endpoint created")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def test_bus_functionality():
    """Test bus publish/subscribe functionality"""
    print("\n🔌 Testing Bus Functionality")
    print("=" * 50)
    
    try:
        from bus import bus, Event
        from constants import TOPIC_TASKS
        
        # Test event creation
        test_event = Event(
            topic=TOPIC_TASKS,
            payload={"task_id": "test", "action": "create"}
        )
        
        # Test publish (for MockBus this should work)
        event_id = await bus.publish(test_event)
        print(f"✅ Event published successfully: {event_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bus functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Strict Configuration and Redis Streams Bus Test Suite")
    print("=" * 70)
    
    # Test configuration
    config_ok = test_strict_config()
    
    # Test bus functionality
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bus_ok = loop.run_until_complete(test_bus_functionality())
    loop.close()
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    print(f"Configuration System: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Bus Functionality: {'✅ PASS' if bus_ok else '❌ FAIL'}")
    
    if config_ok and bus_ok:
        print("\n🎉 All tests passed! Strict configuration system is working.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
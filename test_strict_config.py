"""
Test script for strict configuration system.

This script validates that the new configuration system works correctly
with fail-fast behavior and proper settings management.
"""

import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_settings_import():
    """Test that settings import works correctly"""
    try:
        from settings import settings
        logger.info("✅ Settings import successful")
        
        # Test configuration access
        logger.info(f"EVENT_BUS: {settings.EVENT_BUS}")
        logger.info(f"Database URL: {settings.scrub_url(settings.get_database_url())}")
        
        # Test API key detection
        models = settings.get_available_models()
        logger.info(f"Available models: {models}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Settings import failed: {e}")
        return False

def test_event_bus_configuration():
    """Test event bus configuration with different settings"""
    try:
        from settings import settings
        from core.event_streaming import EventBus
        
        logger.info(f"Testing event bus with EVENT_BUS={settings.EVENT_BUS}")
        
        if settings.EVENT_BUS == "redis":
            try:
                event_bus = EventBus()
                logger.info(f"✅ Event bus initialized: redis_connected={event_bus.redis_connected}")
                
            except RuntimeError as e:
                logger.warning(f"⚠️  Redis configured but unreachable: {e}")
                
        elif settings.EVENT_BUS == "mock":
            event_bus = EventBus()
            logger.info("✅ Mock event bus initialized (with warning)")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Event bus test failed: {e}")
        return False

def test_startup_logging():
    """Test comprehensive startup logging"""
    try:
        from startup_logs import log_system_startup, validate_critical_config
        
        logger.info("Testing startup validation...")
        validate_critical_config()
        logger.info("✅ Configuration validation passed")
        
        logger.info("Testing startup logging...")
        log_system_startup()
        logger.info("✅ Startup logging completed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Startup logging test failed: {e}")
        return False

def test_ai_client_configuration():
    """Test AI client configuration with strict settings"""
    try:
        from core.ai_clients import AIClientConfig
        from settings import settings
        
        config = AIClientConfig()
        logger.info("✅ AI client config created")
        
        # Test API key availability
        logger.info(f"Claude available: {settings.has_api_key('claude')}")
        logger.info(f"GPT-4 available: {settings.has_api_key('gpt-4')}")
        logger.info(f"Gemini available: {settings.has_api_key('gemini')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI client configuration test failed: {e}")
        return False

def run_all_tests():
    """Run all configuration tests"""
    logger.info("=" * 60)
    logger.info("🧪 TESTING STRICT CONFIGURATION SYSTEM")
    logger.info("=" * 60)
    
    tests = [
        ("Settings Import", test_settings_import),
        ("Event Bus Configuration", test_event_bus_configuration),
        ("Startup Logging", test_startup_logging),
        ("AI Client Configuration", test_ai_client_configuration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Strict configuration system is working correctly.")
        return True
    else:
        logger.error(f"🚨 {total - passed} tests failed. Please check configuration.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
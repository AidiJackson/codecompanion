"""
Smoke tests for the production bus system.

Tests MockBus functionality with event publishing and consumption.
Validates that EVENT_BUS=mock works correctly for development.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bus import Event, bus


class TestMockBus:
    """Test MockBus functionality"""

    def test_mock_bus_creation(self):
        """Test that bus singleton is available"""
        assert bus is not None
        assert hasattr(bus, "publish")
        assert hasattr(bus, "subscribe")

    @pytest.mark.asyncio
    async def test_mock_bus_publish(self):
        """Test that bus singleton can publish events"""

        event = Event(
            topic="test.topic", payload={"message": "test message", "data": 123}
        )

        message_id = await bus.publish(event)
        assert message_id is not None
        assert isinstance(message_id, str)

    @pytest.mark.asyncio
    async def test_mock_bus_publish_consume_flow(self):
        """Test complete publish/consume flow with handler validation"""

        # Track handler calls
        handler_calls = []

        async def test_handler(event: Event):
            handler_calls.append(
                {
                    "topic": event.topic,
                    "payload": event.payload,
                    "timestamp": event.timestamp,
                }
            )

        # Create test event
        test_event = Event(
            topic="test.smoke.topic", payload={"test": "smoke_test", "value": 42}
        )

        # Start subscriber (in background task)
        subscriber_task = asyncio.create_task(
            bus.subscribe("test.smoke.topic", "test-group", "consumer-1", test_handler)
        )

        # Give subscriber time to start
        await asyncio.sleep(0.1)

        # Publish event
        message_id = await bus.publish(test_event)
        assert message_id is not None

        # Give time for processing
        await asyncio.sleep(0.2)

        # Cancel subscriber
        subscriber_task.cancel()

        # Verify handler was called
        assert len(handler_calls) > 0, "Handler should have been called"

        # Verify handler received correct data
        call = handler_calls[0]
        assert call["topic"] == "test.smoke.topic"
        assert call["payload"]["test"] == "smoke_test"
        assert call["payload"]["value"] == 42


class TestBusSingleton:
    """Test bus singleton functionality"""

    def test_bus_singleton_available(self):
        """Test that bus singleton is available and configured"""
        assert bus is not None
        # Bus configuration is handled by settings and bus.py

    @pytest.mark.asyncio
    async def test_bus_singleton_publish_functionality(self):
        """Test that singleton bus can publish events"""
        event = Event(topic="factory.test", payload={"factory_test": True})

        message_id = await bus.publish(event)
        assert message_id is not None
        assert isinstance(message_id, str)


class TestEventStructure:
    """Test Event data structure"""

    def test_event_creation(self):
        """Test that Event objects can be created with valid data"""
        event = Event(topic="test.event", payload={"key": "value", "number": 123})

        assert event.topic == "test.event"
        assert event.payload["key"] == "value"
        assert event.payload["number"] == 123
        assert hasattr(event, "timestamp")
        assert event.timestamp is not None

    def test_event_serialization(self):
        """Test that Event objects can be converted to dict"""
        event = Event(topic="serialize.test", payload={"data": "test"})

        # Events should be serializable for bus transmission
        event_dict = {
            "topic": event.topic,
            "payload": event.payload,
            "timestamp": event.timestamp,
        }

        assert event_dict["topic"] == "serialize.test"
        assert event_dict["payload"]["data"] == "test"


@pytest.mark.asyncio
async def test_integration_smoke():
    """Integration smoke test for the entire bus system"""

    # Track integration test results
    integration_results = []

    async def integration_handler(event: Event):
        integration_results.append(
            {
                "received_at": event.timestamp,
                "topic": event.topic,
                "payload": event.payload,
            }
        )

    # Start subscriber
    subscriber_task = asyncio.create_task(
        bus.subscribe(
            "integration.test", "integration-group", "consumer-1", integration_handler
        )
    )

    # Allow subscriber to start
    await asyncio.sleep(0.1)

    # Publish multiple events
    events = [
        Event("integration.test", {"test_id": 1, "message": "first"}),
        Event("integration.test", {"test_id": 2, "message": "second"}),
        Event("integration.test", {"test_id": 3, "message": "third"}),
    ]

    for event in events:
        await bus.publish(event)
        await asyncio.sleep(0.05)  # Small delay between publishes

    # Allow processing time
    await asyncio.sleep(0.3)

    # Clean up subscriber
    subscriber_task.cancel()

    # Verify results
    assert len(integration_results) >= 3, (
        f"Expected at least 3 events, got {len(integration_results)}"
    )

    # Verify event ordering and content
    for i, result in enumerate(integration_results[:3]):
        assert result["topic"] == "integration.test"
        assert result["payload"]["test_id"] == i + 1
        assert result["payload"]["message"] in ["first", "second", "third"]


if __name__ == "__main__":
    # Run basic smoke test if called directly
    pytest.main([__file__, "-v"])

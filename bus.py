"""
Production-grade Redis Streams Event Bus with Mock for Testing

Provides a clean event bus abstraction with fail-fast Redis configuration
and a simple mock implementation for development/testing environments.
"""

from __future__ import annotations
import asyncio
import json
import time
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass
import logging

from settings import settings

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Event structure for the bus system"""
    topic: str
    payload: Dict[str, Any]
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            from datetime import datetime
            self.timestamp = datetime.utcnow().isoformat()

class BaseBus:
    """Abstract base class for event bus implementations"""
    
    async def publish(self, event: Event) -> str:
        """Publish an event to a topic, returns message ID"""
        raise NotImplementedError
        
    async def subscribe(self, topic: str, group: str, consumer: str, handler: Callable[[Event], asyncio.Future]):
        """Subscribe to a topic with a handler function"""
        raise NotImplementedError
        
    async def ensure_topic(self, topic: str):
        """Ensure topic exists and is properly configured"""
        raise NotImplementedError

class RedisStreamsBus(BaseBus):
    """Production Redis Streams implementation with consumer groups"""
    
    def __init__(self, url: str):
        import redis.asyncio as redis
        self.r = redis.from_url(url, decode_responses=True)
        logger.info(f"✅ Redis Streams bus initialized: {settings.scrub_url(url)}")
    
    async def ping(self):
        """Health check for Redis connection"""
        await self.r.ping()
        logger.info("✅ Redis connection verified")

    async def ensure_topic(self, topic: str):
        """Create consumer group for topic if it doesn't exist"""
        try:
            await self.r.xgroup_create(
                name=topic, 
                groupname="orchestrator", 
                id="0-0", 
                mkstream=True
            )
            logger.info(f"✅ Created Redis stream: {topic}")
        except Exception as e:
            # Consumer group already exists - this is expected
            if "BUSYGROUP" not in str(e):
                logger.error(f"❌ Failed to create Redis stream {topic}: {e}")
                raise

    async def publish(self, event: Event) -> str:
        """Publish event to Redis stream"""
        data = {"payload": json.dumps(event.payload)}
        message_id = await self.r.xadd(event.topic, data)
        logger.debug(f"📤 Published to {event.topic}: {message_id}")
        return message_id

    async def subscribe(self, topic: str, group: str, consumer: str, handler: Callable[[Event], asyncio.Future]):
        """Subscribe to Redis stream with consumer group"""
        await self.ensure_topic(topic)
        logger.info(f"🔄 Starting consumer {consumer} for {topic} in group {group}")
        
        while True:
            try:
                msgs = await self.r.xreadgroup(
                    groupname=group, 
                    consumername=consumer, 
                    streams={topic: ">"}, 
                    count=10, 
                    block=5000
                )
                
                for _, entries in msgs or []:
                    for msg_id, fields in entries:
                        try:
                            payload = json.loads(fields["payload"])
                            await handler(Event(topic=topic, payload=payload))
                            await self.r.xack(topic, group, msg_id)
                            logger.debug(f"✅ Processed message {msg_id} from {topic}")
                        except Exception as e:
                            logger.error(f"❌ Error processing message {msg_id}: {e}")
                            # Acknowledge to prevent reprocessing of poison messages
                            await self.r.xack(topic, group, msg_id)
                            
            except Exception as e:
                logger.error(f"❌ Error in Redis consumer loop: {e}")
                await asyncio.sleep(1)  # Brief pause before retry

class MockBus(BaseBus):
    """Mock implementation for development and testing"""
    
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        logger.warning("🚨 MockBus initialized - only for development/testing!")
    
    async def ensure_topic(self, topic: str):
        """Create in-memory queue for topic"""
        self.queues.setdefault(topic, asyncio.Queue())
        logger.debug(f"📝 Mock topic ensured: {topic}")
    
    async def publish(self, event: Event) -> str:
        """Publish to in-memory queue"""
        await self.ensure_topic(event.topic)
        await self.queues[event.topic].put(event)
        message_id = str(time.time())
        logger.debug(f"📤 Mock published to {event.topic}: {message_id}")
        return message_id
    
    async def subscribe(self, topic: str, group: str, consumer: str, handler: Callable[[Event], asyncio.Future]):
        """Subscribe to in-memory queue"""
        await self.ensure_topic(topic)
        q = self.queues[topic]
        logger.info(f"🔄 Mock consumer {consumer} started for {topic}")
        
        while True:
            try:
                ev: Event = await q.get()
                await handler(ev)
                logger.debug(f"✅ Mock processed event from {topic}")
            except Exception as e:
                logger.error(f"❌ Error in mock consumer: {e}")

def get_bus() -> BaseBus:
    """
    Bus factory with fail-fast configuration.
    
    Returns:
        BaseBus: Production Redis bus or mock bus based on configuration
        
    Raises:
        RuntimeError: If Redis is configured but unavailable
    """
    if settings.EVENT_BUS == "redis":
        if not settings.REDIS_URL:
            raise RuntimeError("EVENT_BUS=redis but REDIS_URL not configured")
        
        bus_instance = RedisStreamsBus(str(settings.REDIS_URL))
        
        # Fail-fast connection test
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(bus_instance.ping())
            logger.info("✅ Redis Streams bus ready for production")
            return bus_instance
        except Exception as e:
            raise RuntimeError(f"Redis configured but unreachable: {e}")
    
    elif settings.EVENT_BUS == "mock":
        logger.warning("⚠️  Using MockBus - suitable only for development/testing")
        return MockBus()
    
    else:
        raise RuntimeError(f"Invalid EVENT_BUS configuration: {settings.EVENT_BUS}")

# Singleton bus instance
bus = get_bus()
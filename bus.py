from __future__ import annotations
import asyncio, json, time
from typing import Any, Dict, Callable, Optional
from dataclasses import dataclass
from settings import settings

@dataclass
class Event:
    topic: str
    payload: Dict[str, Any]

class BaseBus:
    async def publish(self, event: Event) -> str: ...
    async def subscribe(self, topic: str, group: str, consumer: str, handler: Callable[[Event], asyncio.Future]): ...
    async def ensure_topic(self, topic: str): ...

class RedisStreamsBus(BaseBus):
    def __init__(self, url: str):
        import redis.asyncio as redis
        self.r = redis.from_url(url, decode_responses=True)
    async def ping(self):
        await self.r.ping()
    async def ensure_topic(self, topic: str):
        try:
            await self.r.xgroup_create(name=topic, groupname="orchestrator", id="0-0", mkstream=True)
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise
    async def publish(self, event: Event) -> str:
        data = {"payload": json.dumps(event.payload)}
        return await self.r.xadd(event.topic, data)
    async def subscribe(self, topic: str, group: str, consumer: str, handler: Callable[[Event], asyncio.Future]):
        await self.ensure_topic(topic)
        while True:
            msgs = await self.r.xreadgroup(groupname=group, consumername=consumer, streams={topic: ">"}, count=10, block=5000)
            for _, entries in msgs or []:
                for msg_id, fields in entries:
                    try:
                        payload = json.loads(fields["payload"])
                        await handler(Event(topic=topic, payload=payload))
                        await self.r.xack(topic, group, msg_id)
                    except Exception:
                        await self.r.xack(topic, group, msg_id)

class MockBus(BaseBus):
    def __init__(self):
        self.queues = {}
    async def ensure_topic(self, topic: str):
        self.queues.setdefault(topic, asyncio.Queue())
    async def publish(self, event: Event) -> str:
        await self.ensure_topic(event.topic)
        await self.queues[event.topic].put(event)
        return str(time.time())
    async def subscribe(self, topic: str, group: str, consumer: str, handler: Callable[[Event], asyncio.Future]):
        await self.ensure_topic(topic)
        q = self.queues[topic]
        while True:
            ev: Event = await q.get()
            await handler(ev)

def get_bus() -> BaseBus:
    print(f"DEBUG: EVENT_BUS={settings.EVENT_BUS}, STREAMLIT_DEBUG={settings.STREAMLIT_DEBUG}, REDIS_URL={settings.REDIS_URL}")
    
    if settings.EVENT_BUS == "redis":
        if not settings.REDIS_URL:
            print("⚠️  EVENT_BUS=redis but REDIS_URL not set, falling back to MockBus")
            if not settings.STREAMLIT_DEBUG:
                print("⚠️  Enabling STREAMLIT_DEBUG for MockBus fallback")
            return MockBus()
        try:
            b = RedisStreamsBus(settings.REDIS_URL)
            asyncio.get_event_loop().run_until_complete(b.ping())
            return b
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}, falling back to MockBus")
            return MockBus()
    
    if settings.EVENT_BUS == "mock":
        if not settings.STREAMLIT_DEBUG:
            print("⚠️  MockBus selected but STREAMLIT_DEBUG is False, enabling it for development")
        return MockBus()
    
    raise RuntimeError(f"Unknown EVENT_BUS: {settings.EVENT_BUS}")

# export singleton
bus = get_bus()
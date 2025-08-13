from __future__ import annotations
import asyncio
import json
import time
from typing import Any, Dict, Callable
from dataclasses import dataclass
from settings import settings


@dataclass
class Event:
    topic: str
    payload: Dict[str, Any]
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class BaseBus:
    async def publish(self, event: Event) -> str: ...
    async def subscribe(
        self,
        topic: str,
        group: str,
        consumer: str,
        handler: Callable[[Event], asyncio.Future],
    ): ...
    async def ensure_topic(self, topic: str): ...


class RedisStreamsBus(BaseBus):
    def __init__(self, url: str):
        import redis.asyncio as redis

        self.r = redis.from_url(url, decode_responses=True)

    async def ping(self):
        await self.r.ping()

    async def ensure_topic(self, topic: str):
        try:
            await self.r.xgroup_create(
                name=topic, groupname="orchestrator", id="0-0", mkstream=True
            )
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def publish(self, event: Event) -> str:
        data = {"payload": json.dumps(event.payload)}
        return await self.r.xadd(event.topic, data)

    async def subscribe(
        self,
        topic: str,
        group: str,
        consumer: str,
        handler: Callable[[Event], asyncio.Future],
    ):
        await self.ensure_topic(topic)
        while True:
            msgs = await self.r.xreadgroup(
                groupname=group,
                consumername=consumer,
                streams={topic: ">"},
                count=10,
                block=5000,
            )
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

    async def subscribe(
        self,
        topic: str,
        group: str,
        consumer: str,
        handler: Callable[[Event], asyncio.Future],
    ):
        await self.ensure_topic(topic)
        q = self.queues[topic]
        while True:
            ev: Event = await q.get()
            await handler(ev)


def get_bus() -> BaseBus:
    if settings.EVENT_BUS == "redis":
        if not settings.REDIS_URL:
            raise RuntimeError("EVENT_BUS=redis but REDIS_URL not set")

        b = RedisStreamsBus(settings.REDIS_URL)

        # Test connection but don't fail startup if Redis is unreachable
        import asyncio

        try:
            try:
                loop = asyncio.get_running_loop()
                # Inside a running loop – schedule ping but do not block
                loop.create_task(b.ping())
            except RuntimeError:
                # No running loop – run synchronously
                asyncio.run(b.ping())
        except Exception as e:
            # Redis connection failed - log warning but continue with MockBus
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Redis connection failed ({e}), falling back to MockBus")
            return MockBus()

        return b

    if settings.EVENT_BUS == "mock":
        # Only allow MockBus explicitly in debug mode
        if not settings.STREAMLIT_DEBUG:
            raise RuntimeError("MockBus selected but STREAMLIT_DEBUG is False")
        return MockBus()

    raise RuntimeError(f"Unknown EVENT_BUS: {settings.EVENT_BUS}")


# export singleton
bus = get_bus()

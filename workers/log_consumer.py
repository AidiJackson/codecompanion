import asyncio, logging
from bus import bus, Event
TOPIC_TASKS = "cc.tasks"
log = logging.getLogger("log_consumer")

async def handler(ev: Event) -> asyncio.Future:
    log.info("📥 Received on %s: %s", ev.topic, ev.payload)
    future = asyncio.Future()
    future.set_result(None)
    return future

async def run():
    await bus.subscribe(topic=TOPIC_TASKS, group="orchestrator", consumer="logger", handler=handler)
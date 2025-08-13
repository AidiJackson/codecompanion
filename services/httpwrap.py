import httpx
import asyncio
import time
from typing import Any, Dict


async def post_json(
    url: str,
    headers: Dict[str, str] | None,
    json_body: Dict[str, Any],
    timeout_s=60,
    retries=2,
):
    last = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                t0 = time.time()
                r = await client.post(url, headers=headers, json=json_body)
                t1 = time.time()
                r.raise_for_status()
                usage = {"status": r.status_code, "latency_ms": int((t1 - t0) * 1000)}
                # Try to extract usage fields if present
                try:
                    data = r.json()
                    if isinstance(data, dict):
                        if "usage" in data:
                            usage["usage"] = data["usage"]
                        if "x-ratelimit-remaining" in r.headers:
                            usage["rate_remaining"] = r.headers.get(
                                "x-ratelimit-remaining"
                            )
                    return data, usage
                except Exception:
                    return r.text, usage
        except Exception as e:
            last = e
            await asyncio.sleep(0.5 * (attempt + 1))
    raise last

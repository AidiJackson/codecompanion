import os, time, httpx

DEFAULT_MODEL = "openrouter/auto"

class LLMError(Exception): ...

def complete(system: str, messages: list, model: str = None, **kwargs):
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise LLMError("OPENROUTER_API_KEY not set")
    model = model or DEFAULT_MODEL
    headers = {
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": "https://replit.com",
        "X-Title": "CodeCompanion",
    }
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        **{"temperature": kwargs.get("temperature", 0.2)},
    }
    backoff = 1.0
    for _ in range(5):
        try:
            with httpx.Client(timeout=60) as c:
                r = c.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if r.status_code >= 500 or r.status_code == 429:
                time.sleep(backoff); backoff = min(backoff*2, 10)
                continue
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]
        except Exception as e:
            last = e
            time.sleep(backoff); backoff = min(backoff*2, 10)
    raise LLMError(str(last))
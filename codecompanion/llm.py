import os
import time
import httpx


class LLMError(Exception): ...


# Provider configurations
PROVIDERS = {
    "claude": {
        "api_key_env": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1/messages",
        "model": "claude-3-5-sonnet-20241022",
        "headers": {"anthropic-version": "2023-06-01"},
    },
    "gpt4": {
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o",
        "headers": {},
    },
    "gemini": {
        "api_key_env": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
        "model": "gemini-1.5-pro",
        "headers": {},
    },
}


def complete(system: str, messages: list, provider: str = "claude", **kwargs):
    """Complete using specified provider (claude, gpt4, gemini)"""
    if provider not in PROVIDERS:
        raise LLMError(f"Unknown provider: {provider}. Use: {list(PROVIDERS.keys())}")

    config = PROVIDERS[provider]
    key = os.getenv(config["api_key_env"])
    if not key:
        raise LLMError(f"{config['api_key_env']} not set for {provider}")

    if provider == "claude":
        return _call_claude(system, messages, key, config, **kwargs)
    elif provider == "gpt4":
        return _call_openai(system, messages, key, config, **kwargs)
    elif provider == "gemini":
        return _call_gemini(system, messages, key, config, **kwargs)


def _call_claude(system: str, messages: list, key: str, config: dict, **kwargs):
    headers = {
        "x-api-key": key,
        "content-type": "application/json",
        **config["headers"],
    }
    payload = {
        "model": config["model"],
        "max_tokens": kwargs.get("max_tokens", 4096),
        "temperature": kwargs.get("temperature", 0.2),
        "system": system,
        "messages": messages,
    }
    return _retry_request(config["base_url"], headers, payload, extract_claude_content)


def _call_openai(system: str, messages: list, key: str, config: dict, **kwargs):
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["model"],
        "temperature": kwargs.get("temperature", 0.2),
        "messages": [{"role": "system", "content": system}] + messages,
    }
    return _retry_request(config["base_url"], headers, payload, extract_openai_content)


def _call_gemini(system: str, messages: list, key: str, config: dict, **kwargs):
    url = f"{config['base_url']}?key={key}"
    headers = {"Content-Type": "application/json"}

    # Convert to Gemini format
    parts = [{"text": f"System: {system}"}]
    for msg in messages:
        parts.append({"text": f"{msg['role'].title()}: {msg['content']}"})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": kwargs.get("temperature", 0.2)},
    }
    return _retry_request(url, headers, payload, extract_gemini_content)


def _retry_request(url: str, headers: dict, payload: dict, extract_fn):
    backoff = 1.0
    for attempt in range(5):
        try:
            with httpx.Client(timeout=60) as client:
                r = client.post(url, headers=headers, json=payload)
            if r.status_code >= 500 or r.status_code == 429:
                time.sleep(backoff)
                backoff = min(backoff * 2, 10)
                continue
            r.raise_for_status()
            return extract_fn(r.json())
        except Exception as e:
            last_error = e
            time.sleep(backoff)
            backoff = min(backoff * 2, 10)
    raise LLMError(f"All retries failed: {last_error}")


def extract_claude_content(data):
    return {"content": data["content"][0]["text"]}


def extract_openai_content(data):
    return data["choices"][0]["message"]


def extract_gemini_content(data):
    return {"content": data["candidates"][0]["content"]["parts"][0]["text"]}

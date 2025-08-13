import os
import httpx


class LLMError(Exception): ...


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


def complete(system, messages, provider="claude", **kwargs):
    if provider not in PROVIDERS:
        raise LLMError(f"Unknown provider: {provider}")

    config = PROVIDERS[provider]
    key = os.getenv(config["api_key_env"])
    if not key:
        raise LLMError(f"{config['api_key_env']} not set")

    try:
        if provider == "claude":
            return call_claude(system, messages, key, config, **kwargs)
        elif provider == "gpt4":
            return call_openai(system, messages, key, config, **kwargs)
        elif provider == "gemini":
            return call_gemini(system, messages, key, config, **kwargs)
    except Exception as e:
        raise LLMError(str(e))


def call_claude(system, messages, key, config, **kwargs):
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

    with httpx.Client(timeout=30) as client:
        r = client.post(config["base_url"], headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return {"content": data["content"][0]["text"]}


def call_openai(system, messages, key, config, **kwargs):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": config["model"],
        "temperature": kwargs.get("temperature", 0.2),
        "messages": [{"role": "system", "content": system}] + messages,
    }

    with httpx.Client(timeout=30) as client:
        r = client.post(config["base_url"], headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]


def call_gemini(system, messages, key, config, **kwargs):
    url = f"{config['base_url']}?key={key}"
    headers = {"Content-Type": "application/json"}

    parts = [{"text": f"System: {system}"}]
    for msg in messages:
        parts.append({"text": f"{msg['role'].title()}: {msg['content']}"})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": kwargs.get("temperature", 0.2)},
    }

    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return {"content": data["candidates"][0]["content"]["parts"][0]["text"]}

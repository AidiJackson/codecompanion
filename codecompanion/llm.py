import os
import time
import httpx
import logging

logger = logging.getLogger(__name__)


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
    "openrouter": {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "anthropic/claude-3.5-sonnet",  # Default model
        "headers": {
            "HTTP-Referer": "https://github.com/AidiJackson/codecompanion",
            "X-Title": "CodeCompanion",
        },
    },
}


def complete(system: str, messages: list, provider: str = "claude", **kwargs):
    """Complete using specified provider (claude, gpt4, gemini, openrouter)"""
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
    elif provider == "openrouter":
        return _call_openrouter(system, messages, key, config, **kwargs)


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


def _call_openrouter(system: str, messages: list, key: str, config: dict, **kwargs):
    """
    Call OpenRouter API (OpenAI-compatible).

    OpenRouter supports multiple models via the 'model' parameter.
    Returns actual cost in usage.total_cost field.
    """
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        **config["headers"],  # Includes HTTP-Referer and X-Title
    }

    # Use model from kwargs if provided, otherwise use default
    model = kwargs.get("model", config["model"])

    payload = {
        "model": model,
        "temperature": kwargs.get("temperature", 0.2),
        "messages": [{"role": "system", "content": system}] + messages,
    }

    return _retry_request(config["base_url"], headers, payload, extract_openrouter_content)


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


def extract_openrouter_content(data):
    """
    Extract content and cost from OpenRouter response.

    OpenRouter returns actual cost in usage.total_cost (USD).
    We include this in the response for accurate cost tracking.
    """
    result = data["choices"][0]["message"].copy()

    # Add usage information including actual cost
    if "usage" in data:
        result["usage"] = {
            "prompt_tokens": data["usage"].get("prompt_tokens", 0),
            "completion_tokens": data["usage"].get("completion_tokens", 0),
            "total_tokens": data["usage"].get("total_tokens", 0),
            "total_cost": data["usage"].get("total_cost", 0.0),  # Actual cost in USD
        }

    # Add model information
    if "model" in data:
        result["model"] = data["model"]

    return result


# ==============================================================================
# Fallback Logic (Phase 3)
# ==============================================================================


def _is_retryable_error(exc: Exception) -> bool:
    """
    Determine if an error is retryable for fallback purposes.

    Retryable errors include:
    - Network/timeout errors (httpx.RequestError)
    - HTTP 429, 500, 502, 503, 504 status codes
    - Model-not-found / malformed response errors

    Args:
        exc: Exception to check

    Returns:
        True if error is retryable, False otherwise
    """
    # Network / timeout errors
    if isinstance(exc, httpx.RequestError):
        return True

    # HTTP status errors
    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response is not None:
            return exc.response.status_code in {429, 500, 502, 503, 504}

    # Model-not-found / malformed response – treat as retryable for v1
    if isinstance(exc, (KeyError, ValueError)):
        return True

    # LLMError from _retry_request exhausting retries
    if isinstance(exc, LLMError):
        return True

    return False


def complete_with_fallback(
    system: str,
    messages: list,
    provider: str,
    model: str = None,
    *,
    fallback_enabled: bool = True,
    fallback_chain: list = None,
    **kwargs,
) -> dict:
    """
    Call llm.complete() with the given provider/model, with smart fallback.

    If the primary provider is 'openrouter' and fallback_enabled is True,
    we try an ordered fallback chain, catching retryable errors.

    For non-openrouter providers, this simply wraps complete() with meta info.

    Args:
        system: System prompt
        messages: List of message dicts with 'role' and 'content'
        provider: Primary provider name (claude, gpt4, gemini, openrouter)
        model: Optional model name (especially for OpenRouter)
        fallback_enabled: Enable fallback chain (default: True)
        fallback_chain: Optional custom fallback chain as list of (provider, model) tuples
        **kwargs: Additional arguments passed to complete()

    Returns:
        Dict with completion result plus 'meta' field:
        {
            "content": "...",
            "usage": {...},  # if available
            "meta": {
                "primary_provider": str,
                "primary_model": str or None,
                "used_fallback": bool,
                "fallback_provider": str or None,  # if used
                "fallback_model": str or None,     # if used
                "fallback_attempts": int,
                "primary_error_type": str or None,
                "primary_error_message": str or None,
            }
        }
    """
    primary_provider = provider
    primary_model = model

    # Build meta dict (will be populated and returned)
    meta = {
        "primary_provider": primary_provider,
        "primary_model": primary_model,
        "used_fallback": False,
        "fallback_provider": None,
        "fallback_model": None,
        "fallback_attempts": 0,
        "primary_error_type": None,
        "primary_error_message": None,
    }

    # If provider is not openrouter, just call complete() normally
    if provider != "openrouter":
        try:
            result = complete(system, messages, provider=provider, model=model, **kwargs)
            result["meta"] = meta
            return result
        except Exception as e:
            # Non-openrouter providers don't get fallback
            raise

    # For openrouter: build fallback chain if not provided
    if fallback_chain is None:
        chain = []

        # Primary: OpenRouter with specified model
        if os.getenv("OPENROUTER_API_KEY"):
            chain.append(("openrouter", model))

        # Fallback 1: Claude
        if os.getenv("ANTHROPIC_API_KEY"):
            chain.append(("claude", None))  # Use default Claude model

        # Fallback 2: GPT-4
        if os.getenv("OPENAI_API_KEY"):
            chain.append(("gpt4", None))  # Use default GPT-4 model

        fallback_chain = chain

    # If fallback is disabled or no chain, just try primary
    if not fallback_enabled or not fallback_chain:
        try:
            result = complete(system, messages, provider=provider, model=model, **kwargs)
            result["meta"] = meta
            return result
        except Exception as e:
            raise

    # Try each provider/model in the fallback chain
    primary_error = None

    for idx, (fallback_provider, fallback_model) in enumerate(fallback_chain):
        is_primary = (idx == 0)
        is_last = (idx == len(fallback_chain) - 1)

        try:
            # Attempt completion with this provider/model
            if fallback_model:
                result = complete(system, messages, provider=fallback_provider, model=fallback_model, **kwargs)
            else:
                result = complete(system, messages, provider=fallback_provider, **kwargs)

            # Success! Update meta and return
            if not is_primary:
                meta["used_fallback"] = True
                meta["fallback_provider"] = fallback_provider
                meta["fallback_model"] = fallback_model
                meta["fallback_attempts"] = idx

            result["meta"] = meta
            return result

        except Exception as e:
            # Save primary error for meta
            if is_primary:
                primary_error = e
                meta["primary_error_type"] = type(e).__name__
                meta["primary_error_message"] = str(e)[:200]  # Truncate

            # Check if we should fallback
            if not is_last and _is_retryable_error(e):
                # Log fallback attempt
                next_provider, next_model = fallback_chain[idx + 1]
                logger.warning(
                    "LLM fallback: %s/%s failed with %s, falling back to %s/%s",
                    fallback_provider,
                    fallback_model or "(default)",
                    type(e).__name__,
                    next_provider,
                    next_model or "(default)",
                )
                continue  # Try next in chain
            else:
                # Either last in chain or non-retryable error
                raise

    # Should not reach here, but just in case
    if primary_error:
        raise primary_error
    raise LLMError("Fallback chain exhausted with no result")

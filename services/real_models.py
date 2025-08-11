import os, json, uuid
from typing import Optional
from .httpwrap import post_json

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

async def call_claude(prompt: str) -> Optional[str]:
    if not ANTHROPIC_KEY: return None
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 1200,
        "messages": [{"role":"user","content":prompt}],
    }
    import httpx
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
            content = "".join([blk.get("text","") for blk in data.get("content",[])])
            return content
    except Exception as e:
        return f"[ERROR Anthropic: {e}]"

async def call_gpt4(prompt: str) -> Optional[str]:
    if not OPENAI_KEY: return None
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "gpt-4o-mini",      # or "gpt-4o"
        "messages": [{"role":"user","content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1200
    }
    import httpx
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERROR OpenAI: {e}]"

async def call_gemini(prompt: str) -> Optional[str]:
    if not GEMINI_KEY: return None
    # Generative Language API v1beta (text-only)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    body = {"contents":[{"parts":[{"text": prompt}]}]}
    import httpx
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=None, json=body)
            r.raise_for_status()
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"[ERROR Gemini: {e}]"

async def real_e2e(objective: str) -> dict:
    """
    Minimal real pipeline:
      - SpecDoc via Claude (if key), fallback GPT-4 if not
      - CodePatch via GPT-4 (if key), fallback Claude
      - DesignDoc via Gemini (if key), fallback GPT-4
      - TestPlan via GPT-4
      - EvalReport via Claude
    """
    run_id = f"R-{uuid.uuid4().hex[:8]}"
    out = []
    usage_stats = {}

    def add(kind, agent, content, conf=0.75):
        out.append({"type": kind, "agent": agent, "confidence": conf, "content": content})

    # SpecDoc via Claude or GPT-4
    spec = await call_claude(f"Write a crisp SpecDoc for: {objective}")
    if spec and not spec.startswith("[ERROR"):
        add("SpecDoc", "Claude", spec)
    else:
        spec = await call_gpt4(f"Write a crisp SpecDoc for: {objective}")
        add("SpecDoc", "GPT-4", spec or "[no key configured]")

    # CodePatch via GPT-4 or Claude
    code = await call_gpt4(f"Return ONLY a unified diff CodePatch that implements: {objective}. Keep it minimal.")
    if code and not code.startswith("[ERROR"):
        add("CodePatch", "GPT-4", code)
    else:
        code = await call_claude(f"Return ONLY a unified diff CodePatch that implements: {objective}. Keep it minimal.")
        add("CodePatch", "Claude", code or "[no key configured]")

    # DesignDoc via Gemini or GPT-4
    design = await call_gemini(f"Draft a brief DesignDoc (UI/UX) for: {objective}")
    if design and not design.startswith("[ERROR"):
        add("DesignDoc", "Gemini", design)
    else:
        design = await call_gpt4(f"Draft a brief DesignDoc (UI/UX) for: {objective}")
        add("DesignDoc", "GPT-4", design or "[no key configured]")

    # TestPlan via GPT-4 or Claude
    tests = await call_gpt4(f"Write a minimal TestPlan for: {objective}")
    if tests and not tests.startswith("[ERROR"):
        add("TestPlan", "GPT-4", tests)
    else:
        tests = await call_claude(f"Write a minimal TestPlan for: {objective}")
        add("TestPlan", "Claude", tests or "[no key configured]")

    # EvalReport via Claude or GPT-4
    review = await call_claude(f"Review the CodePatch and TestPlan for: {objective}. Return an EvalReport with risks and next steps.")
    if review and not review.startswith("[ERROR"):
        add("EvalReport", "Claude", review)
    else:
        review = await call_gpt4(f"Review the CodePatch and TestPlan for: {objective}. Return an EvalReport.")
        add("EvalReport", "GPT-4", review or "[no key configured]")

    return {"run_id": run_id, "artifacts": out, "usage": usage_stats, "models": {"claude": bool(ANTHROPIC_KEY), "gpt4": bool(OPENAI_KEY), "gemini": bool(GEMINI_KEY)}}
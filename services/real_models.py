import os, json, httpx, uuid
from typing import Optional

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")  # Direct OpenAI API
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
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        return "".join([blk.get("text","") for blk in data.get("content",[])])

async def call_gpt4(prompt: str) -> Optional[str]:
    if not OPENAI_KEY: return None
    # Direct OpenAI API endpoint
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "gpt-4o-mini",   # cheap-fast GPT-4 class
        "messages": [{"role":"user","content":prompt}],
        "temperature": 0.2,
        "max_tokens": 800,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]

async def call_gemini(prompt: str) -> Optional[str]:
    if not GEMINI_KEY: return None
    # Generative Language API v1beta (text-only)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    body = {"contents":[{"parts":[{"text": prompt}]}]}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=body)
        r.raise_for_status()
        data = r.json()
        # extract text
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return json.dumps(data)[:2000]

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

    def add(kind, agent, content, conf=0.75):
        out.append({"type": kind, "agent": agent, "confidence": conf, "content": content})

    spec = await (call_claude(f"Write a crisp SpecDoc for: {objective}") or call_gpt4(f"Write a crisp SpecDoc for: {objective}"))
    add("SpecDoc", "Claude/GPT-4", spec or "[no key configured]")

    code = await (call_gpt4(f"Return ONLY a unified diff CodePatch that implements: {objective}. Keep it minimal.") or call_claude(f"Return ONLY a unified diff CodePatch that implements: {objective}. Keep it minimal."))
    add("CodePatch", "GPT-4/Claude", code or "[no key configured]")

    design = await (call_gemini(f"Draft a brief DesignDoc (UI/UX) for: {objective}") or call_gpt4(f"Draft a brief DesignDoc (UI/UX) for: {objective}"))
    add("DesignDoc", "Gemini/GPT-4", design or "[no key configured]")

    tests = await (call_gpt4(f"Write a minimal TestPlan for: {objective}") or call_claude(f"Write a minimal TestPlan for: {objective}"))
    add("TestPlan", "GPT-4/Claude", tests or "[no key configured]")

    review = await (call_claude(f"Review the CodePatch and TestPlan for: {objective}. Return an EvalReport with risks and next steps.") or call_gpt4(f"Review the CodePatch and TestPlan for: {objective}. Return an EvalReport."))
    add("EvalReport", "Claude/GPT-4", review or "[no key configured]")

    return {"run_id": run_id, "artifacts": out}
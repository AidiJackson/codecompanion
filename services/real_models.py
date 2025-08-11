import os, json, uuid
from typing import Optional, Tuple
from .httpwrap import post_json

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")  # Direct OpenAI API
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

async def call_claude(prompt: str) -> Tuple[Optional[str], dict]:
    if not ANTHROPIC_KEY: return None, {}
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
    try:
        data, usage = await post_json(url, headers, body)
        if isinstance(data, dict):
            content = "".join([blk.get("text","") for blk in data.get("content",[])])
            return content, usage
        return str(data), usage
    except Exception:
        return None, {}

async def call_gpt4(prompt: str) -> Tuple[Optional[str], dict]:
    if not OPENAI_KEY: return None, {}
    # Direct OpenAI API endpoint
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "gpt-4o-mini",   # cheap-fast GPT-4 class
        "messages": [{"role":"user","content":prompt}],
        "temperature": 0.2,
        "max_tokens": 800,
    }
    try:
        data, usage = await post_json(url, headers, body)
        if isinstance(data, dict) and "choices" in data:
            content = data["choices"][0]["message"]["content"]
            return content, usage
        return str(data), usage
    except Exception:
        return None, {}

async def call_gemini(prompt: str) -> Tuple[Optional[str], dict]:
    if not GEMINI_KEY: return None, {}
    # Generative Language API v1beta (text-only)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    body = {"contents":[{"parts":[{"text": prompt}]}]}
    try:
        data, usage = await post_json(url, None, body)
        # extract text
        if isinstance(data, dict) and "candidates" in data:
            try:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return content, usage
            except Exception:
                return json.dumps(data)[:2000], usage
        return str(data), usage
    except Exception:
        return None, {}

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
    spec, claude_usage = await call_claude(f"Write a crisp SpecDoc for: {objective}")
    if spec:
        add("SpecDoc", "Claude", spec)
        usage_stats["claude_spec"] = claude_usage
    else:
        spec, gpt_usage = await call_gpt4(f"Write a crisp SpecDoc for: {objective}")
        add("SpecDoc", "GPT-4", spec or "[no key configured]")
        if gpt_usage:
            usage_stats["gpt4_spec"] = gpt_usage

    # CodePatch via GPT-4 or Claude
    code, gpt_usage = await call_gpt4(f"Return ONLY a unified diff CodePatch that implements: {objective}. Keep it minimal.")
    if code:
        add("CodePatch", "GPT-4", code)
        usage_stats["gpt4_code"] = gpt_usage
    else:
        code, claude_usage = await call_claude(f"Return ONLY a unified diff CodePatch that implements: {objective}. Keep it minimal.")
        add("CodePatch", "Claude", code or "[no key configured]")
        if claude_usage:
            usage_stats["claude_code"] = claude_usage

    # DesignDoc via Gemini or GPT-4
    design, gemini_usage = await call_gemini(f"Draft a brief DesignDoc (UI/UX) for: {objective}")
    if design:
        add("DesignDoc", "Gemini", design)
        usage_stats["gemini"] = gemini_usage
    else:
        design, gpt_usage = await call_gpt4(f"Draft a brief DesignDoc (UI/UX) for: {objective}")
        add("DesignDoc", "GPT-4", design or "[no key configured]")
        if gpt_usage:
            usage_stats["gpt4_design"] = gpt_usage

    # TestPlan via GPT-4 or Claude
    tests, gpt_usage = await call_gpt4(f"Write a minimal TestPlan for: {objective}")
    if tests:
        add("TestPlan", "GPT-4", tests)
        usage_stats["gpt4_tests"] = gpt_usage
    else:
        tests, claude_usage = await call_claude(f"Write a minimal TestPlan for: {objective}")
        add("TestPlan", "Claude", tests or "[no key configured]")
        if claude_usage:
            usage_stats["claude_tests"] = claude_usage

    # EvalReport via Claude or GPT-4
    review, claude_usage = await call_claude(f"Review the CodePatch and TestPlan for: {objective}. Return an EvalReport with risks and next steps.")
    if review:
        add("EvalReport", "Claude", review)
        usage_stats["claude_review"] = claude_usage
    else:
        review, gpt_usage = await call_gpt4(f"Review the CodePatch and TestPlan for: {objective}. Return an EvalReport.")
        add("EvalReport", "GPT-4", review or "[no key configured]")
        if gpt_usage:
            usage_stats["gpt4_review"] = gpt_usage

    return {"run_id": run_id, "artifacts": out, "usage": usage_stats}
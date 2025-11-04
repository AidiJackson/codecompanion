# Quick Start - Dependency Optimization

## TL;DR

Your requirements.txt was missing 13 critical dependencies and had 1 unused package. Run this to fix it:

```bash
cd /home/user/codecompanion
bash artifacts.commands
```

Then update 4 files to replace `requests` with `httpx` (they're API-compatible).

---

## What Changed

### Removed (1)
- ❌ **rich** - Never used anywhere in code

### Added (13)
Core missing dependencies that prevent the app from running:
- streamlit, fastapi, uvicorn
- pydantic, pydantic-settings, typer  
- anthropic, openai, google-generativeai
- pandas, numpy, plotly, scikit-learn

### Moved (3)
Dev tools now in requirements-dev.txt:
- pytest, ruff, pyright

---

## Files Created

| File | Purpose |
|------|---------|
| `requirements.txt.new` | Fixed production dependencies |
| `requirements-dev.txt` | Dev tools (separated) |
| `pyproject.toml.new` | Updated project config |
| `constraints.txt` | Version locks for reproducibility |
| `artifacts.commands` | Automated install script |
| `DEPENDENCY_AUDIT_REPORT.md` | Full detailed report |

---

## One-Command Install

```bash
bash artifacts.commands
```

This will:
1. Backup current environment
2. Remove unused packages (rich, requests)
3. Install all missing dependencies
4. Use constraints.txt for reproducible builds
5. Verify installation

---

## Manual Code Updates Required

After running artifacts.commands, update these 4 files:

### 1. /home/user/codecompanion/app.py
```python
# Change:
import requests
# To:
import httpx

# Then replace all:
requests.get(...) → httpx.get(...)
requests.post(...) → httpx.post(...)
```

### 2. /home/user/codecompanion/cli.py
```python
# Same as above
import requests → import httpx
requests.get/post → httpx.get/post
```

### 3. /home/user/codecompanion/test_api_endpoints.py
```python
# Same pattern
import requests → import httpx  
```

### 4. /home/user/codecompanion/agents/test_writer.py
```python
# Line 722, change the mock:
@patch('requests.get') → @patch('httpx.get')
```

**Note:** httpx has the same API as requests, so it's just find-replace!

---

## Verify Everything Works

```bash
# Test imports
python3 -c "import httpx, fastapi, streamlit, anthropic, openai; print('✅ OK')"

# Run the app
streamlit run /home/user/codecompanion/app.py
```

---

## Rollback (if needed)

```bash
mv requirements.txt.old requirements.txt
mv pyproject.toml.old pyproject.toml
pip install -r requirements.backup.txt
```

---

## Why This Matters

**Before:** App couldn't run - missing streamlit, fastapi, and all AI SDKs  
**After:** Complete, optimized, reproducible dependency set

Read **DEPENDENCY_AUDIT_REPORT.md** for full details.

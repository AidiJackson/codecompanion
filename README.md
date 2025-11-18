# CodeCompanion - Standalone Dev OS

🤖 **A standalone multi-agent Dev OS with live Control Tower dashboard for personal use**

## 📦 Local Installation

This is a personal development tool. Clone the repo and install in editable mode:

```bash
git clone https://github.com/AidiJackson/codecompanion.git
cd codecompanion
pip install -e .
```

## 🚀 Quick Start

### Check Bootstrap & Environment

Verify installation and bootstrap status:

```bash
codecompanion --check
```

### View System Status

Show human-readable system status:

```bash
codecompanion --info
```

Show raw JSON status (same structure as `/api/info` endpoint):

```bash
codecompanion --info --raw
```

### Launch Control Tower Dashboard

Start the live status dashboard:

```bash
codecompanion --dashboard
```

Then open your browser to:
- **Dashboard**: http://127.0.0.1:8008/
- **API Info**: http://127.0.0.1:8008/api/info

The dashboard auto-refreshes every 3 seconds and shows:
- ✅ Project & bootstrap status
- 🤖 Agent workflow completion
- 🔑 LLM provider configuration
- 📊 Pipeline execution history
- ⚠️ Error tracking & recovery
- 💡 System recommendations

### Run Agent Workflows

```bash
# Verify installation
codecompanion --check

# Run full agent pipeline (auto-detects your project)
codecompanion --auto

# Run specific agent
codecompanion --run Analyzer

# Use quick launcher (if available)
./cc auto           # Full pipeline
./cc run Fixer      # Single agent
./cc detect         # Show project info
```

## 🤖 Available Agents

| Agent | Purpose | LLM Provider |
|-------|---------|--------------|
| **Installer** | Environment setup, dependencies | None (tooling) |
| **EnvDoctor** | Diagnose import/runtime issues | Claude |
| **Analyzer** | Code analysis, pattern detection | GPT-4 |
| **DepAuditor** | Dependency optimization | Gemini |
| **BugTriage** | Bug reproduction, debugging | Claude |
| **Fixer** | Code generation, patches | GPT-4 |
| **TestRunner** | Test execution, coverage | None (tooling) |
| **WebDoctor** | Web app configuration | Gemini |
| **PRPreparer** | Documentation, commits | Claude |

## 🎯 Smart Project Detection

CodeCompanion automatically detects your project type and configures optimal agent workflows:

- **Python Web** (Django/Flask/FastAPI): Focus on web setup, dependencies, testing
- **Python Data** (ML/Data Science): Environment optimization, package management
- **Node Frontend** (React/Vue/Next): NPM dependencies, build optimization
- **Node Backend** (Express/API): Server setup, API testing
- **Full-Stack**: Complete development workflow
- **Generic**: Basic setup and analysis

## 🔧 Configuration

CodeCompanion uses these API keys (set in Replit Secrets):
- `ANTHROPIC_API_KEY` - For Claude (diagnostic reasoning)
- `OPENAI_API_KEY` - For GPT-4 (code analysis/generation)  
- `GEMINI_API_KEY` - For Gemini (optimization tasks)

## 📋 Agent Workflows

### Development Workflow
```bash
codecompanion --auto
# Runs: Installer → EnvDoctor → Analyzer → DepAuditor → TestRunner → PRPreparer
```

### Debug Workflow  
```bash
codecompanion --run BugTriage
codecompanion --run Fixer
codecompanion --run TestRunner
```

### Optimization Workflow
```bash
codecompanion --run DepAuditor
codecompanion --run Analyzer
codecompanion --run WebDoctor
```

## 💬 Interactive Chat

```bash
codecompanion --chat                    # Default (Claude)
codecompanion --chat --provider gpt4    # Use GPT-4
codecompanion --chat --provider gemini  # Use Gemini
```

## 🔍 Project Analysis

```bash
./cc detect
```

Shows:
- Project type detection
- Framework identification  
- Recommended agent preset
- Confidence score

## 📁 Files Created

- `.codecompanion.json` - Project configuration
- `.cc/` - Agent workspace and artifacts
- `cc` - Quick launcher script

## 🛠 Advanced Usage

### Custom Agent Sequence
```bash
codecompanion --run Installer
codecompanion --run Analyzer --provider gpt4
codecompanion --run Fixer --provider claude
```

### Environment Override
```bash
CC_PROVIDER=gemini codecompanion --auto
```

### Makefile Integration
```bash
make codecompanion-setup   # Install CodeCompanion
make cc-auto              # Run pipeline
make cc-analyze           # Analysis only
```

## 🏗 Architecture

CodeCompanion provides:
- **Multi-LLM Support**: Claude, GPT-4, Gemini with optimal task assignment
- **Project-Aware**: Auto-detects frameworks and adjusts workflows
- **Patch-Safe**: Uses `git apply` for all code changes
- **Replit-Optimized**: Designed for Replit's environment and constraints
- **Zero-Config**: Works out of the box with sensible defaults

## 🤝 Integration Examples

### Replit Template Integration
```toml
# .replit
[deployment]
run = ["codecompanion", "--auto"]

[nix]
channel = "stable-22_11"
```

### GitHub Actions
```yaml
- name: Setup CodeCompanion
  run: |
    curl -sSL https://raw.githubusercontent.com/your-repo/codecompanion/main/scripts/install.sh | bash
    codecompanion --auto
```

---

**CodeCompanion transforms any Replit project into an AI-powered development environment with specialized agents for every task.**
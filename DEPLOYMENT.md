# CodeCompanion Deployment Guide

## 🚀 Easy Installation for Any Replit Project

CodeCompanion provides three installation methods for maximum flexibility:

### Method 1: One-Line Install (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/your-repo/codecompanion/main/scripts/quick-install.sh | bash
```

### Method 2: Python One-Liner  
```bash
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/your-repo/codecompanion/main/scripts/setup.py').read())"
```

### Method 3: Manual Setup
```bash
pip install git+https://github.com/your-repo/codecompanion.git
codecompanion --check
```

## ✅ What Gets Installed

After installation, users get:

### Command-Line Tools
- `codecompanion` - Main CLI with full agent system
- `./cc` - Quick launcher for common tasks
- `python -m codecompanion.project_detector` - Project analysis

### Project Files Created
- `.codecompanion.json` - Project configuration and agent presets
- `.cc/` - Agent workspace and bootstrap files
- `.cc/agents/` - Agent stub files for customization

### Capabilities
- **9 AI Agents** with optimal LLM provider assignments
- **Auto-Detection** of project type (Python, Node, Full-stack, etc.)
- **Smart Workflows** tailored to detected framework
- **Multi-LLM Support** (Claude, GPT-4, Gemini)

## 🎯 Usage After Installation

### Immediate Commands
```bash
# Verify everything works
codecompanion --check

# Run project analysis  
./cc detect

# Execute full agent pipeline
codecompanion --auto

# Run specific agent
codecompanion --run Analyzer
```

### Project-Specific Workflows

**Python Projects:**
```bash
codecompanion --auto  # Installer → EnvDoctor → Analyzer → DepAuditor → TestRunner
```

**Node.js Projects:**
```bash
codecompanion --auto  # Installer → DepAuditor → WebDoctor → TestRunner
```

**Full-Stack Projects:**
```bash
codecompanion --auto  # Complete 9-agent pipeline
```

## 🔧 API Key Setup

For full functionality, users should set these in Replit Secrets:

- `ANTHROPIC_API_KEY` - For Claude (diagnostic reasoning, debugging)
- `OPENAI_API_KEY` - For GPT-4 (code analysis, generation)
- `GEMINI_API_KEY` - For Gemini (optimization, configuration)

**Without API keys:** Tooling agents still work (Installer, TestRunner)  
**With API keys:** Full AI-powered analysis and code generation

## 🏗 Integration Examples

### Replit Template Integration
```toml
# .replit
[deployment]
run = ["codecompanion", "--auto"]

[nix]
channel = "stable-22_11"
```

### Startup Script
```bash
# Add to project's startup script
if ! command -v codecompanion &> /dev/null; then
    echo "Installing CodeCompanion..."
    curl -sSL https://raw.githubusercontent.com/your-repo/codecompanion/main/scripts/quick-install.sh | bash
fi
```

### Makefile Integration
```makefile
setup-codecompanion:
	curl -sSL https://raw.githubusercontent.com/your-repo/codecompanion/main/scripts/quick-install.sh | bash

cc-auto:
	codecompanion --auto

cc-analyze:
	codecompanion --run Analyzer
```

## 📊 What Users Experience

### First-Time Setup (30 seconds)
1. Run one-line installer
2. Auto-detects project type
3. Configures optimal agent workflow
4. Creates quick launcher (`./cc`)

### Daily Usage
```bash
./cc                    # Check status
./cc auto              # Full pipeline  
./cc run Fixer         # Single agent
```

### Smart Workflows
- **Auto-Detection**: Recognizes React, Django, FastAPI, etc.
- **Optimal Agents**: Different AI models for different tasks
- **Context-Aware**: Adapts to project structure and needs

## 🛡 Safety Features

- **Patch-Only**: Never overwrites full files, only applies patches
- **Git-Safe**: Uses `git apply` for all code changes
- **API-Safe**: Keys are never logged or exposed
- **Rollback**: Users can undo any agent changes

## 📈 Scalability

CodeCompanion works for:
- ✅ Individual Replit projects
- ✅ Team projects (shared configuration)
- ✅ Template-based projects
- ✅ Educational environments
- ✅ Production applications

## 🔄 Updates

Users can update CodeCompanion anytime:
```bash
pip install --upgrade git+https://github.com/your-repo/codecompanion.git
```

Or reinstall:
```bash
curl -sSL https://raw.githubusercontent.com/your-repo/codecompanion/main/scripts/quick-install.sh | bash
```

---

**Result: Any Replit user can add AI-powered development agents to their project with a single command, getting the same powerful workflow you have access to.**
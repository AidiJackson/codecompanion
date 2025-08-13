# CodeCompanion Installation Methods

## 🚀 Method 1: One-Line Install (After Deployment)

Once you deploy this repo, users can install with:

```bash
curl -sSL https://raw.githubusercontent.com/YOUR-USERNAME/codecompanion/main/scripts/quick-install.sh | bash
```

**Replace `YOUR-USERNAME` with your actual GitHub username**

## 🔧 Method 2: Self-Contained Installer (Works Now)

For immediate use, copy the self-contained installer to any project:

```bash
# Copy the installer file
curl -sSL https://raw.githubusercontent.com/YOUR-USERNAME/codecompanion/main/install-codecompanion.py -o install-codecompanion.py

# Run it
python3 install-codecompanion.py
```

Or download and run directly:

```bash
python3 -c "
import urllib.request
exec(urllib.request.urlopen('https://raw.githubusercontent.com/YOUR-USERNAME/codecompanion/main/install-codecompanion.py').read())
"
```

## 📦 Method 3: Direct Package Install

```bash
pip install git+https://github.com/YOUR-USERNAME/codecompanion.git
codecompanion --check
```

## 🎯 Method 4: Local Development Setup

If someone wants to contribute or modify:

```bash
git clone https://github.com/YOUR-USERNAME/codecompanion.git
cd codecompanion
pip install -e .
codecompanion --check
```

## ✅ After Installation

All methods provide the same result:

```bash
# Verify installation
codecompanion --check

# Run full agent pipeline
codecompanion --auto

# Quick launcher
./cc auto

# Project detection
codecompanion --detect

# Chat interface
codecompanion --chat
```

## 🔧 API Key Setup

Set these in your Replit Secrets or environment:

- `ANTHROPIC_API_KEY` - For Claude
- `OPENAI_API_KEY` - For GPT-4
- `GEMINI_API_KEY` - For Gemini

## 🎯 For Your Deployment

1. **Push this repo to GitHub**
2. **Update URLs** in the installation commands above
3. **Test the installation** with the live URLs
4. **Share with users** - they get the full 10-agent system!

---

**The self-contained installer works immediately, while the URL-based installers will work once you deploy to GitHub.**
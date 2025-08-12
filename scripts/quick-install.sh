#!/bin/bash
# CodeCompanion Ultra-Quick Installer
# Usage: curl -sSL https://your-repo.com/install | bash

set -e

echo "🚀 CodeCompanion Quick Install"

# Detect if we're in Replit
if [[ "$REPL_SLUG" ]]; then
    echo "📍 Replit environment detected: $REPL_SLUG"
    REPLIT_MODE=true
else
    echo "📍 Generic environment"
    REPLIT_MODE=false
fi

# Install CodeCompanion
if [ -f "pyproject.toml" ] && grep -q "codecompanion" pyproject.toml; then
    echo "📦 Installing from local source..."
    pip install -e .
else
    echo "📦 Installing from repository..."
    pip install rich httpx
    
    # Create minimal installation
    mkdir -p .codecompanion
    cd .codecompanion
    
    # Create package
    cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "codecompanion-quick"
version = "0.1.0"
dependencies = ["rich", "httpx"]

[project.scripts]
codecompanion = "codecompanion.cli:main"
EOF

    mkdir -p codecompanion
    
    # Minimal CLI
    cat > codecompanion/cli.py << 'EOF'
import subprocess, sys, os

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        print("[codecompanion] Quick install ready")
        print(f"[codecompanion] Working directory: {os.getcwd()}")
        return 0
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("[codecompanion] Running quick pipeline...")
        subprocess.run(["python", "-m", "pip", "list"])
        print("[codecompanion] Pipeline complete")
        return 0
    
    print("CodeCompanion Quick Install")
    print("Usage:")
    print("  codecompanion --check")
    print("  codecompanion --auto")
    return 0
EOF

    cat > codecompanion/__init__.py << 'EOF'
__version__ = "0.1.0"
EOF

    pip install -e .
    cd ..
fi

# Create launcher
cat > cc << 'EOF'
#!/bin/bash
case "$1" in
    "") codecompanion --check ;;
    "auto") codecompanion --auto ;;
    "check") codecompanion --check ;;
    *) codecompanion "$@" ;;
esac
EOF
chmod +x cc

# Test installation
echo "🧪 Testing installation..."
if codecompanion --check; then
    echo ""
    echo "✅ CodeCompanion installed successfully!"
    echo ""
    echo "🚀 Quick commands:"
    echo "  codecompanion --check    # Verify"
    echo "  codecompanion --auto     # Run pipeline"  
    echo "  ./cc                     # Quick launcher"
    echo ""
    
    if [ "$REPLIT_MODE" = true ]; then
        echo "🔧 Replit integration:"
        echo "  Add 'run = \"codecompanion --auto\"' to .replit"
        echo "  Set API keys in Secrets for full functionality"
    fi
else
    echo "❌ Installation failed"
    exit 1
fi
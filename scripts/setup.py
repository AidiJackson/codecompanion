#!/usr/bin/env python3
"""
CodeCompanion Setup Utility
One-command setup for any Replit project
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def run_cmd(cmd, check=True):
    """Run shell command and return result"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def install_codecompanion():
    """Install CodeCompanion package"""
    print("📦 Installing CodeCompanion...")

    # Install via pip from this repo
    install_cmd = "pip install git+https://github.com/your-repo/codecompanion.git"

    # Fallback: install locally if we're in the repo
    if Path("pyproject.toml").exists():
        install_cmd = "pip install -e ."

    try:
        run_cmd(install_cmd)
        print("✅ CodeCompanion installed successfully")
    except:
        print("⚠️  Using local installation method...")
        run_cmd("pip install -e .", check=False)


def setup_project():
    """Set up CodeCompanion for current project"""
    print("🔧 Setting up project configuration...")

    # Import after installation
    try:
        from codecompanion.project_detector import ProjectDetector
    except ImportError:
        print("❌ CodeCompanion not properly installed")
        return False

    # Detect project and create config
    detector = ProjectDetector()
    project_info = detector.detect_project_type()
    preset = detector.get_recommended_preset(project_info)

    print(
        f"🎯 Detected: {project_info['type']} ({project_info.get('framework', 'generic')})"
    )
    print(f"🤖 Using preset: {preset['description']}")

    # Create .codecompanion.json
    config = {
        "project": project_info,
        "preset": preset,
        "agents": preset["agents"],
        "setup_complete": True,
    }

    with open(".codecompanion.json", "w") as f:
        json.dump(config, f, indent=2)

    # Create quick launcher
    launcher_content = """#!/bin/bash
# CodeCompanion Quick Launcher
case "$1" in
    ""|"help")
        echo "🤖 CodeCompanion Commands:"
        echo "  ./cc check          - Verify setup"
        echo "  ./cc auto           - Run full pipeline"
        echo "  ./cc run <agent>    - Run specific agent"
        echo "  ./cc detect         - Show project info"
        ;;
    "check") codecompanion --check ;;
    "auto") codecompanion --auto ;;
    "run") codecompanion --run "$2" ;;
    "detect") python -m codecompanion.project_detector ;;
    *) codecompanion "$@" ;;
esac
"""

    with open("cc", "w") as f:
        f.write(launcher_content)

    os.chmod("cc", 0o755)

    return True


def verify_installation():
    """Verify CodeCompanion is working"""
    print("🧪 Verifying installation...")

    try:
        result = run_cmd("codecompanion --version", check=False)
        if result.returncode == 0:
            print(f"✅ CodeCompanion version: {result.stdout.strip()}")
        else:
            print("❌ codecompanion command not working")
            return False

        # Test agent execution
        result = run_cmd("codecompanion --check", check=False)
        if result.returncode == 0:
            print("✅ Agent system working")
        else:
            print("⚠️  Agent system needs configuration")

        return True
    except:
        print("❌ Installation verification failed")
        return False


def main():
    """Main setup process"""
    print("🚀 CodeCompanion Universal Setup")
    print("=" * 40)

    # Check Python
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        sys.exit(1)

    print(f"✅ Python {sys.version.split()[0]}")

    # Install CodeCompanion
    install_codecompanion()

    # Setup project
    if setup_project():
        print("✅ Project configured")

    # Verify
    if verify_installation():
        print("\n🎉 Setup Complete!")
        print("\n🚀 Quick Start:")
        print("  ./cc check          # Verify everything works")
        print("  ./cc auto           # Run full agent pipeline")
        print("  ./cc detect         # Show project analysis")
        print("\n📚 Available Agents:")

        # Show configured agents
        try:
            with open(".codecompanion.json") as f:
                config = json.load(f)
                agents = config.get("agents", [])
                print(f"  {', '.join(agents)}")
        except:
            print("  Installer, EnvDoctor, Analyzer, TestRunner, PRPreparer")
    else:
        print("❌ Setup completed with issues. Try running again.")
        sys.exit(1)


if __name__ == "__main__":
    main()

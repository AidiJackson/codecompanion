#!/usr/bin/env python3
"""
CodeCompanion CLI wrapper script.
This allows running 'cc' command directly from the workspace.
"""
import sys
import os

# Add current directory to Python path so we can import cc_cli
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cc_cli.main import app

if __name__ == "__main__":
    app()
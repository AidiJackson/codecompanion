#!/usr/bin/env python3
"""
Simple test runner script for the CodeCompanion Orchestra project.

Runs pytest with appropriate configuration for smoke tests.
Equivalent to 'make test' functionality.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run pytest with optimal configuration"""

    # Ensure we're in the project root
    project_root = Path(__file__).parent

    # Basic pytest command with quiet output and failure info
    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",  # Quiet output
        "--tb=short",  # Short traceback format
        "-v",  # Verbose test names
        "tests/",  # Test directory
    ]

    print("🧪 Running CodeCompanion Orchestra smoke tests...")
    print(f"📁 Project root: {project_root}")
    print(f"🔧 Command: {' '.join(pytest_cmd)}")
    print("-" * 60)

    try:
        # Run pytest
        result = subprocess.run(
            pytest_cmd,
            cwd=project_root,
            capture_output=False,  # Show output in real-time
            text=True,
        )

        print("-" * 60)

        if result.returncode == 0:
            print("✅ All tests passed!")
            return 0
        else:
            print(f"❌ Tests failed with exit code: {result.returncode}")
            return result.returncode

    except FileNotFoundError:
        print("❌ Error: pytest not found. Please install with:")
        print("   pip install pytest pytest-asyncio")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

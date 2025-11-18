"""
Entry point for running codecompanion as a module.

Allows running: python -m codecompanion.cli
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())

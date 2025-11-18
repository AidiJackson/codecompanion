"""Allow codecompanion to be run as a module: python -m codecompanion"""
from .cli import main

if __name__ == "__main__":
    exit(main())

"""Allow codecompanion to be run as a module with python -m codecompanion"""

from .cli import main

if __name__ == "__main__":
    import sys
    sys.exit(main())

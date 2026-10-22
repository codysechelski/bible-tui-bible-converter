"""Allow running the tool with ``python3 -m bibles``."""

import sys

from bibles.cli import main

if __name__ == "__main__":
    sys.exit(main())

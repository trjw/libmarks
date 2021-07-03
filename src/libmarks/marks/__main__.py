"""Main entry point for MARKS"""

import sys

if sys.argv[0].endswith("__main__.py"):
    sys.argv[0] = "python -m marks"

from . import main

main.main(module=None)

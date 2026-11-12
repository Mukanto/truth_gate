"""``python -m kapi`` entry point: runs the Truth_Gate command line (spec 0.6, sections 2.1 and 9)."""

import sys

from truth_gate.cli import main

if __name__ == "__main__":
    sys.exit(main())

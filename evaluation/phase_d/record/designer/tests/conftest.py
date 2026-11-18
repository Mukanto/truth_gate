"""pytest configuration for the designer tests: keep every scratch file under designer\\tests\\work\\ (never in a
system temp folder) and do not write bytecode next to the tool."""
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")


def pytest_configure(config):
    if config.option.basetemp is None:
        config.option.basetemp = Path(__file__).resolve().parent / "work" / "pytest_tmp"

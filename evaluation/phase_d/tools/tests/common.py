"""Shared helpers of the Phase D tool tests: paths, the gate package root, and a subprocess runner for the CLIs."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
TOOLS = os.path.join(WORK, "tools")
def _default_package_root():
    """The repository that holds this folder (evaluation/phase_d/tools/tests -> four levels up) when it contains the
    gate; otherwise the designer's local repository."""
    up = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
    if os.path.isdir(os.path.join(up, "truth_gate")) and os.path.isdir(os.path.join(up, "evaluation", "phase_c")):
        return up
    return r"E:\Claude Projects\kapi-oss"


PKG = os.environ.get("KAPI_PACKAGE_ROOT") or _default_package_root()  # the gate at 0.5.1 (read-only)
PC = os.path.join(PKG, "evaluation", "phase_c")

if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)


def run_tool(script, *args, timeout=600):
    """Run ``tools/<script>`` in a fresh isolated interpreter; returns the CompletedProcess (text mode)."""
    cmd = [sys.executable, "-I", "-B", os.path.join(TOOLS, script), *map(str, args)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8")

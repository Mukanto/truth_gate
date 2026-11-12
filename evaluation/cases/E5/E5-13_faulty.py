"""E5-13 (deterministic): buffer-tank mass balance. Claim: inflow and outflow balance within 1e-3 kg/s at every step."""
import numpy as np

from kapi import Control, Criterion, Study, World

STEPS = np.arange(24, dtype=float)
INFLOW = 10.0 + np.sin(2.0 * np.pi * STEPS / 24.0)


def _tank(leak):
    q_out = INFLOW - 1.0e-5
    if leak:
        q_leak = q_out * (1.0 - leak)
    return {"inflow": INFLOW.copy(), "outflow": q_out}


def _balanced(d):
    return bool(np.max(np.abs(d["inflow"] - d["outflow"])) < 1.0e-3)


STUDY = Study(
    name="E5-13 buffer-tank mass balance",
    criteria=[Criterion("balance_closes", _balanced, tolerances={"balance_tol": (1.0e-3, 10.0)})],
    worlds={
        "plus": World(lambda rng: _tank(0.0)),
        "minus": World(lambda rng: _tank(0.05), derived_from="plus", change="5% leak in the outflow line"),
    },
    controls=[Control("outflow_lagged", ["balance_closes"], transform=lambda d, rng: {"inflow": d["inflow"], "outflow": np.roll(d["outflow"], 1)})],
    deterministic=True,
)

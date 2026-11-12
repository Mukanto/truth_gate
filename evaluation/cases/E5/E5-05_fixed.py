"""E5-05 (stochastic): spectral line. Claim: the periodogram at bin 16 exceeds ten times the median periodogram level."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

N_T = 128
F_BIN = 16
TT = np.arange(N_T)


def _record(rng, world):
    amp = 1.0
    if world == "minus":
        amp = 0.0
    return {"x": amp * np.sin(2.0 * np.pi * F_BIN * TT / N_T) + rng.normal(0.0, 1.0, N_T)}


def _line_ok(d):
    p = np.abs(np.fft.rfft(d["x"])) ** 2
    ref = float(np.median(p[1:]))
    if not ref > 0.0:
        return False
    return bool(p[F_BIN] / ref > 10.0)


STUDY = Study(
    name="E5-05 spectral line at bin 16",
    criteria=[Criterion("line_at_16", _line_ok)],
    worlds={
        "plus": World(lambda rng: _record(rng, "plus")),
        "minus": World(lambda rng: _record(rng, "minus"), derived_from="plus", change="line amplitude 1 -> 0"),
        "null": World(lambda rng: {"x": rng.normal(0.0, 1.0, N_T)}),
    },
    premises=[Premise("phase_coherence", lambda d, rng: {"x": rng.permutation(d["x"])}, "tested", ["line_at_16"])],
    controls=[
        Control(
            "line_at_23",
            ["line_at_16"],
            world=World(lambda rng: {"x": np.sin(2.0 * np.pi * 23 * TT / N_T) + rng.normal(0.0, 1.0, N_T)}),
        )
    ],
)

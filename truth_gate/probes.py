"""Generic vacuity probes (spec sections 5.5 and 6)."""

from __future__ import annotations

import numpy as np

PROBE_NOISE = "noise"
PROBE_ZEROS = "zeros"


def shuffle_name(a: str, b: str) -> str:
    """Probe name of the optional shuffle probe (spec section 5.5)."""
    return f"shuffle:{a},{b}"


def is_boolean(array: np.ndarray) -> bool:
    return array.dtype == np.bool_


def is_numeric(array: np.ndarray) -> bool:
    """``numpy.issubdtype(dtype, numpy.number)`` (spec section 6); booleans are separate."""
    return bool(np.issubdtype(array.dtype, np.number))


def noise_probe(data: dict, rng: np.random.Generator) -> dict:
    """Numeric arrays -> i.i.d. N(0, 1) float64; bool -> Bernoulli(0.5); others unchanged."""
    out = {}
    for key in data:  # insertion order of the user's dict is deterministic
        array = data[key]
        if is_boolean(array):
            out[key] = np.asarray(rng.random(array.shape) < 0.5)
        elif is_numeric(array):
            out[key] = np.asarray(rng.standard_normal(array.shape), dtype=np.float64)
        else:
            out[key] = array.copy()
    return out


def zeros_probe(data: dict, rng: np.random.Generator | None = None) -> dict:
    """Numeric arrays -> float64 zeros; bool -> False; others unchanged (rng unused)."""
    out = {}
    for key, array in data.items():
        if is_boolean(array):
            out[key] = np.zeros(array.shape, dtype=np.bool_)
        elif is_numeric(array):
            out[key] = np.zeros(array.shape, dtype=np.float64)
        else:
            out[key] = array.copy()
    return out


def shuffle_probe(data: dict, rng: np.random.Generator, a: str, b: str) -> dict:
    """Permute the first axis of ``data[b]`` relative to ``data[a]`` (spec section 5.5).

    Raises ``KeyError`` for missing keys and ``ValueError`` when ``b`` has no
    first axis of length >= 2; the evaluator turns those into UNDEFINED.
    """
    if a not in data or b not in data:
        raise KeyError("shuffle keys missing from the sample")
    target = data[b]
    if target.ndim < 1 or target.shape[0] < 2:
        raise ValueError("cannot shuffle an axis shorter than 2")
    length = target.shape[0]
    perm = rng.permutation(length)
    for _ in range(10):  # avoid the identity permutation
        if not np.array_equal(perm, np.arange(length)):
            break
        perm = rng.permutation(length)
    else:
        perm = np.roll(np.arange(length), 1)
    out = {key: value.copy() for key, value in data.items()}
    out[b] = target[perm].copy()
    return out


def unchanged_keys(data: dict, probe: str) -> list:
    """Keys a probe leaves unchanged because of their dtype (spec section 5.5)."""
    if probe not in (PROBE_NOISE, PROBE_ZEROS):
        return []
    return sorted(k for k, v in data.items() if not (is_boolean(v) or is_numeric(v)))

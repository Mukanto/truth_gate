"""Seeding and sample bookkeeping (spec section 4)."""

from __future__ import annotations

import zlib
from typing import Any

import numpy as np

# Indices evaluated to verify determinism (spec section 4.3).
DETERMINISM_INDICES = (0, 1, 2)


def stream_rng(base_seed: int, stream: str, i: int) -> np.random.Generator:
    """Generator for sample ``i`` of stream ``stream`` (spec section 4, Seeds)."""
    seq = np.random.SeedSequence([base_seed, zlib.crc32(stream.encode()), i])
    return np.random.default_rng(seq)


def sample_count(deterministic: bool, samples: int, quick_samples: int, quick: bool) -> int:
    """Number of counted samples: 1 if deterministic, else full or quick budget (spec section 4)."""
    if deterministic:
        return 1
    return quick_samples if quick else samples


def copy_data(data: dict) -> dict:
    """Shallow dict with copied arrays, so user code cannot leak state between calls."""
    return {key: np.array(value, copy=True) for key, value in data.items()}


def validate_data(data: Any) -> dict:
    """Check that a generated sample is ``dict[str, ndarray]`` (spec section 3)."""
    if not isinstance(data, dict):
        raise TypeError("data must be a dict")
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, np.ndarray):
            raise TypeError("data must map str to numpy.ndarray")
    return data

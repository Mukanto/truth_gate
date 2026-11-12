"""Statistical primitive: Wilson bounds, Bonferroni level, SL (spec section 4)."""

from __future__ import annotations

import math
from statistics import NormalDist

HOLDS = "HOLDS"


def z_value(a: float) -> float:
    """One-sided critical value ``z = inv_cdf(1 - a)`` (spec section 4.1)."""
    if not (0.0 < a < 1.0):
        raise ValueError("a must be in (0, 1)")
    return NormalDist().inv_cdf(1.0 - a)


def wilson_bounds(k: int, n: int, a: float) -> tuple:
    """One-sided Wilson score bounds ``(lower, upper)`` at level ``a`` (spec section 4.1).

    Each bound is one-sided with the same ``z``. ``k == 0`` gives lower exactly
    0 and ``k == n`` gives upper exactly 1; ``n == 0`` gives ``(0, 1)``.
    """
    if n < 0 or k < 0 or k > n:
        raise ValueError("require 0 <= k <= n")
    if n == 0:
        return 0.0, 1.0
    z = z_value(a)
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    lower = 0.0 if k == 0 else max(0.0, centre - half)
    upper = 1.0 if k == n else min(1.0, centre + half)
    return lower, upper


def wilson_lower(k: int, n: int, a: float) -> float:
    """Lower one-sided Wilson bound (spec section 4.1)."""
    return wilson_bounds(k, n, a)[0]


def wilson_upper(k: int, n: int, a: float) -> float:
    """Upper one-sided Wilson bound (spec section 4.1)."""
    return wilson_bounds(k, n, a)[1]


def bonferroni_a(alpha_family: float, m: int) -> float:
    """Per-bound level ``a = alpha_family / (2 m)`` (spec section 4.2)."""
    if m < 1:
        raise ValueError("m must be >= 1")
    return alpha_family / (2.0 * m)


def sl_stochastic(k_low: int, n_low: int, k_high: int, n_high: int, a: float) -> bool:
    """``SL(A, B)``: ``wilson_upper(A, a) < wilson_lower(B, a)`` (spec section 4.2)."""
    return wilson_bounds(k_low, n_low, a)[1] < wilson_bounds(k_high, n_high, a)[0]


def sl_deterministic(outcome_low: str, outcome_high: str) -> bool:
    """Deterministic ``SL``: A in {FAILS, UNDEFINED} and B is HOLDS (spec section 4.3)."""
    return outcome_low != HOLDS and outcome_high == HOLDS

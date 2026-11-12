"""Separate passes that run after the two evaluations (spec 0.6, sections 1.1 and 4).

Passes add fields and flags to the body; they never feed anything back into K1-K7.  Stage (b) holds
``pattern_stats``.  The orchestrator runs it under the armed guard.
"""

from __future__ import annotations

import warnings

import numpy as np

from .checks import _call, build_plan, component_verdict, make_sample
from .patterns import UNDEFINED
from .sampling import copy_data, sample_count, stream_rng
from .study import Study

SUGGESTED_UNREVIEWED = "SUGGESTED_UNREVIEWED"
QUANTILES = (0.05, 0.5, 0.95)
STREAM_LABELS = {"world:plus": "plus", "world:minus": "minus", "world:null": "null"}


def add_component_flags(result: dict, flags) -> dict:
    """Add flags to every component of an evaluation result and recompute its verdict (spec section 1.1, item 3).

    The flags are added after the 0.3 cascade and the identical-minus suppression and are never suppressed.  The
    component's stored flag list is the one its verdict was computed from, so the new verdict is the 0.3 verdict
    function applied to that list plus the new flags.
    """
    extra = set(flags)
    if not extra:
        return result
    for comp in result["components"]:
        merged = set(comp["flags"]) | extra
        comp["flags"] = sorted(merged)
        comp["verdict"] = component_verdict(merged)
    return result


def add_flags_by_component(result: dict, flags_by_component: dict) -> dict:
    """Like :func:`add_component_flags`, with a different flag set per component id (the K8 flags)."""
    for comp in result["components"]:
        extra = set(flags_by_component.get(comp["id"], ()))
        if not extra:
            continue
        merged = set(comp["flags"]) | extra
        comp["flags"] = sorted(merged)
        comp["verdict"] = component_verdict(merged)
    return result


def _summary(values: list) -> dict:
    if not values:
        return {"n_finite": 0, "q05": None, "q50": None, "q95": None}
    q05, q50, q95 = (float(v) for v in np.quantile(np.asarray(values, dtype=np.float64), QUANTILES))
    return {"n_finite": len(values), "q05": q05, "q50": q50, "q95": q95}


def pattern_stats(study: Study, quick: bool, patterns: dict) -> dict:
    """The ``pattern_stats`` pass (spec section 4, last paragraph).

    Regenerates the counted samples of the ``plus``, ``minus`` and ``null`` streams with the engine's own seeds and
    sample function (``stream_rng``, ``make_sample``; the samples K1-K7 saw): indices below ``sample_count`` of the
    mode, or index 0 in a deterministic study.  For every pattern criterion and stream it records the 5%, 50% and 95%
    quantiles (numpy's linear method, float64, unrounded) of each statistic the pattern computes, its thresholds and
    the number of finite values.  Parts of ``all_of`` / ``any_of`` are keyed by position path.  UNDEFINED samples are
    excluded.  ``patterns`` maps criterion id to a compiled pattern.
    """
    if not patterns:
        return {}
    seed = study.budget.base_seed
    n = sample_count(study.deterministic, study.budget.samples, study.budget.quick_samples, quick)
    indices = range(1) if study.deterministic else range(n)
    streams = [sd for sd in build_plan(study) if sd.kind == "world"]
    # acc[criterion][path][stream label][statistic] -> list of finite values
    acc: dict = {cid: {path: {} for path, _ in pattern.leaves()} for cid, pattern in patterns.items()}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for i in indices:
            plus = _call(study.worlds["plus"].generate, stream_rng(seed, "world:plus", i))
            for sd in streams:
                sample = make_sample(study, sd, i, plus)
                if sample.data is None:
                    continue
                label = STREAM_LABELS[sd.name]
                for cid, pattern in patterns.items():
                    record: dict = {}
                    try:
                        pattern.evaluate(copy_data(sample.data), record)
                    except Exception:
                        continue  # the criterion raised: UNDEFINED, excluded
                    for path, (outcome, stats) in record.items():
                        if outcome == UNDEFINED:
                            continue
                        per_stream = acc[cid][path].setdefault(label, {})
                        for name, value in stats.items():
                            per_stream.setdefault(name, [])
                            if np.isfinite(value):
                                per_stream[name].append(float(value))
    out: dict = {}
    for cid, pattern in patterns.items():
        parts = {}
        for path, leaf in pattern.leaves():
            streams_out = {}
            for sd in streams:
                label = STREAM_LABELS[sd.name]
                streams_out[label] = {
                    name: _summary(vals) for name, vals in sorted(acc[cid][path].get(label, {}).items())
                }
            parts[path] = {"pattern": leaf.name, "thresholds": leaf.thresholds(), "streams": streams_out}
        out[cid] = {"parts": parts}
    return out


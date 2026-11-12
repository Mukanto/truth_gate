"""K8: invariance, a separate pass (spec 0.6, section 7).

An invariance declares a transformation that, by the study's own logic, must not change any criterion outcome.  The
pass runs after the two evaluations and their comparison, under the armed guard.  It never feeds samples or outcomes
back into K1-K7, and its draws are the gate's own streams, so they are not part of the 0.3 determinism check.

* **Pairs.** For each invariance, each listed criterion component and each of the worlds ``plus`` and ``minus``.
  Stochastic study: the counted samples of the world in the current mode are regenerated with the engine's seeds
  (``stream_rng``, ``make_sample``); each is evaluated before and after one transformation drawn from the stream
  ``k8:<invariance>:<world>`` at the sample's index.  Deterministic study: the one sample is evaluated once
  untransformed and after ``budget.samples`` transformations (``quick_samples`` in quick mode), the ``j``-th drawn from
  the stream at index ``j``.  Pairs with an UNDEFINED side are counted apart.
* **Family.** ``m_k8`` = 2 x the number of (invariance, component) pairs; every (invariance, component, world) rate is
  tested with the one-sided Wilson lower bound at level ``alpha_family / m_k8``.
* **Flags** (per component): ``K8_NOT_INVARIANT`` (mandatory), ``K8_SOME_CHANGES`` (info), ``K8_INCONCLUSIVE``
  (capping).  The orchestrator adds them after the 0.3 suppression rules; nothing suppresses them.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np

from .checks import UNDEFINED, Sample, _call, build_plan, evaluate_criterion, make_sample
from .mutations import apply_mutations
from .sampling import sample_count, stream_rng
from .stats import wilson_lower
from .study import Study, StudyError, criterion_component_ids

BUILTIN_ID = "builtin:permute_rows"
STATEMENT = "study-wide family-wise error rate at most 2 · alpha_family"
WORLDS = ("plus", "minus")
FLAG_NOT_INVARIANT = "K8_NOT_INVARIANT"
FLAG_SOME_CHANGES = "K8_SOME_CHANGES"
FLAG_INCONCLUSIVE = "K8_INCONCLUSIVE"
K8_FLAGS = (FLAG_NOT_INVARIANT, FLAG_SOME_CHANGES, FLAG_INCONCLUSIVE)


@dataclass(frozen=True)
class Invariance:
    """A compiled invariance: validated mutations, the criteria it covers and the row-aligned keys of each world."""

    id: str
    criteria: tuple
    mutations: list
    row_keys: dict = field(default_factory=dict)  # world name ("plus", "minus") -> tuple of row-aligned keys
    builtin: bool = False


@dataclass
class K8Result:
    """Outcome of the pass: certificate fields and the flags of every component."""

    k8: dict  # invariance id -> component id -> world -> record
    m_k8: int
    flags: dict  # component id -> set of K8 flags
    ran: bool

    def body_fields(self) -> dict:
        """Fields added to the manifest body (spec section 11).  Without K8 the statement is absent."""
        out = {"k8": self.k8, "m_k8": self.m_k8}
        if self.ran:
            out["k8_statement"] = STATEMENT
        return out


def validate_invariances(study: Study, invariances: list) -> None:
    """Study-level checks of the invariances (a ``StudyError``, like the same checks of controls and premises)."""
    ids = {c.id for c in study.criteria}
    seen: set = set()
    for inv in invariances:
        if inv.id in seen:
            raise StudyError(f"duplicate invariance id {inv.id!r}")
        seen.add(inv.id)
        if not inv.criteria:
            raise StudyError(f"invariance {inv.id!r} lists no criterion")
        if len(set(inv.criteria)) != len(inv.criteria):
            raise StudyError(f"invariance {inv.id!r} lists a criterion twice")
        for cid in inv.criteria:
            if cid not in ids:
                raise StudyError(f"invariance {inv.id!r} lists unknown criterion {cid!r}")


def k8_rng(base_seed: int, invariance_id: str, world: str, index: int) -> np.random.Generator:
    """Generator of the gate's own stream ``k8:<invariance>:<world>`` at ``index`` (the engine's seed rule)."""
    return stream_rng(base_seed, f"k8:{invariance_id}:{world}", index)


def _all_undefined(criterion) -> dict:
    return {cid: UNDEFINED for cid in criterion_component_ids(criterion)}


def _tally(counts: dict, key: tuple, before: str, after: str) -> None:
    rec = counts[key]
    rec["pairs"] += 1
    if before == UNDEFINED or after == UNDEFINED:
        rec["undefined"] += 1
    elif before != after:
        rec["changes"] += 1


def _transformed(inv: Invariance, world: str, sample: Sample, rng) -> Sample:
    if sample.data is None:
        return Sample(None, sample.error)
    return _call(apply_mutations, sample.data, inv.mutations, rng, tuple(inv.row_keys.get(world, ())))


def k8_pass(study: Study, quick: bool, invariances: list) -> K8Result:
    """Run K8 (spec section 7).  ``invariances`` are validated (:func:`validate_invariances`)."""
    if not invariances:
        return K8Result({}, 0, {}, False)
    seed = study.budget.base_seed
    det = study.deterministic
    # stochastic: the counted samples of the mode; deterministic: one sample and ``samples`` (``quick_samples``) draws
    n = (study.budget.quick_samples if quick else study.budget.samples) if det else sample_count(
        det, study.budget.samples, study.budget.quick_samples, quick)
    crit_by_id = {c.id: c for c in study.criteria}
    # tally[(invariance id, component id, world)] -> counts
    counts: dict = {}
    n_pairs = 0  # (invariance, component) pairs
    for inv in invariances:
        for crit_id in inv.criteria:
            for cid in criterion_component_ids(crit_by_id[crit_id]):
                n_pairs += 1
                for world in WORLDS:
                    counts[(inv.id, cid, world)] = {"pairs": 0, "undefined": 0, "changes": 0}
    m_k8 = 2 * n_pairs
    level = study.targets.alpha_family / m_k8

    minus_stream = next(sd for sd in build_plan(study) if sd.kind == "world" and sd.ref == "minus")
    plus_def = study.worlds["plus"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for i in range(1 if det else n):
            plus = _call(plus_def.generate, stream_rng(seed, "world:plus", i))
            samples = {"plus": plus, "minus": make_sample(study, minus_stream, i, plus)}
            for world, sample in samples.items():
                before_cache: dict = {}
                for inv in invariances:
                    draws = range(n) if det else (i,)
                    for j in draws:
                        after_sample = _transformed(inv, world, sample, k8_rng(seed, inv.id, world, j))
                        for crit_id in inv.criteria:
                            crit = crit_by_id[crit_id]
                            if crit_id not in before_cache:
                                before_cache[crit_id] = evaluate_criterion(crit, sample)[0]
                            after = evaluate_criterion(crit, after_sample)[0]
                            for cid, before_outcome in before_cache[crit_id].items():
                                _tally(counts, (inv.id, cid, world), before_outcome, after[cid])
    return _finish(study, invariances, counts, m_k8, level)


def _finish(study: Study, invariances: list, counts: dict, m_k8: int, level: float) -> K8Result:
    size = study.targets.size
    flags: dict = {}
    k8: dict = {}
    for (inv_id, cid, world), rec in sorted(counts.items()):
        defined = rec["pairs"] - rec["undefined"]
        lower = wilson_lower(rec["changes"], defined, level)
        record = {
            "pairs": rec["pairs"], "defined": defined, "changes": rec["changes"], "undefined": rec["undefined"],
            "wilson_lower": round(float(lower), 12), "level": level,
        }
        k8.setdefault(inv_id, {}).setdefault(cid, {})[world] = record
        found = flags.setdefault(cid, set())
        if lower > size:
            found.add(FLAG_NOT_INVARIANT)
        elif rec["changes"] > 0:
            found.add(FLAG_SOME_CHANGES)
        if 2 * rec["undefined"] > rec["pairs"]:
            found.add(FLAG_INCONCLUSIVE)
    return K8Result(k8, m_k8, {cid: f for cid, f in flags.items() if f}, True)


__all__ = [
    "BUILTIN_ID", "K8_FLAGS", "STATEMENT", "Invariance", "K8Result", "k8_pass", "k8_rng", "validate_invariances",
]

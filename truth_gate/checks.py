"""Checks K1-K7, evaluation driver and verdict mapping (spec sections 2, 5, 6)."""

from __future__ import annotations

import warnings
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Mapping, NamedTuple, Optional

import numpy as np

from . import minus as minus_check
from . import probes
from .sampling import DETERMINISM_INDICES, copy_data, sample_count, stream_rng, validate_data
from .stats import bonferroni_a, sl_deterministic, sl_stochastic, wilson_bounds, wilson_lower, wilson_upper
from .study import Criterion, Study, criterion_component_ids

HOLDS = "HOLDS"
FAILS = "FAILS"
UNDEFINED = "UNDEFINED"

VERDICTS = ("FALSIFIABLE", "WEAK", "UNTESTED", "NOT_FALSIFIABLE", "UNDEFINED")  # severity order (spec 0.5 delta 2)

MANDATORY_FLAGS = frozenset(
    {
        "K2_HOLDS_UNREACHABLE",
        "K2_FAILS_UNREACHABLE",
        "K2_NO_SEPARATION",
        "K2_UNRESOLVABLE",
        "K3_PREMISE_NOT_TESTED",
        "K4_NO_CONTROL",
        "K4_CONTROL_ALSO_HOLDS",
        "K5_HOLDS_ON_NOISE",
        "K5_HOLDS_ON_DEGENERATE",
        "K5_HOLDS_ON_NULL",
        "K5_HOLDS_ON_SHUFFLE",
        "K2_HIGH_SIZE",  # v0.2 delta 1: the declared alpha is mandatory
    }
)
MANDATORY_PREFIXES = ("HIGH_RATE:",)  # v0.2 delta 1
CAPPING_FLAGS = frozenset({"K2_LOW_POWER", "K3_INCONCLUSIVE", "K4_WAIVED", "K4_INCONCLUSIVE"})
CAPPING_PREFIXES = ("K5_INCONCLUSIVE:", "K1_ABSTAINED_MAJORITY:")  # spec 0.7, section 2.5
# Flags of schema 2 (spec 0.6, section 11).  Kept apart from MANDATORY_FLAGS and CAPPING_FLAGS, the 0.3 sets that its
# tests pin.  The K8 flags are added by the K8 pass after the 0.3 suppression rules and are never suppressed.
MANDATORY_FLAGS_SCHEMA2 = frozenset({"K8_NOT_INVARIANT"})
CAPPING_FLAGS_SCHEMA2 = frozenset({"SUGGESTED_UNREVIEWED", "K8_INCONCLUSIVE"})
INFORMATIONAL_FLAGS_SCHEMA2 = frozenset({"K8_SOME_CHANGES"})
# v0.2 delta 2: SL-derived flags that carry no information when plus never holds.
SUPPRESSIBLE_FLAGS = frozenset(
    {
        "K2_NO_SEPARATION",
        "K2_LOW_POWER",
        "K3_PREMISE_NOT_TESTED",
        "K4_CONTROL_ALSO_HOLDS",
        "K5_HOLDS_ON_NOISE",
        "K5_HOLDS_ON_DEGENERATE",
        "K5_HOLDS_ON_NULL",
        "K5_HOLDS_ON_SHUFFLE",
    }
)
SUPPRESSED_BY = "K2_HOLDS_UNREACHABLE"
UNTESTED_FLAGS = frozenset({minus_check.FLAG_IDENTICAL})  # spec 0.5 delta 1.4: verdict UNTESTED
INFORMATIONAL_FLAGS = frozenset({"BAD_RETURN", minus_check.FLAG_UNREAD})
INFORMATIONAL_PREFIXES = ("K1_ABSTAINED:",)  # spec 0.7, section 2.5: K1_ABSTAINED:<stream>; never enters a verdict
STUDY_LEVEL_FLAGS = frozenset(
    {"K6_LEAK_ATTEMPT", "K6_NONREPRODUCIBLE", "K7_REGIME_UNCOVERED", "K7_COMPONENT_MISMATCH", "NONDETERMINISTIC"}
)


# --------------------------------------------------------------------------
# Verdict mapping (spec section 5.8)
# --------------------------------------------------------------------------

def is_mandatory(flag: str) -> bool:
    return flag in MANDATORY_FLAGS or flag in MANDATORY_FLAGS_SCHEMA2 or flag.startswith(MANDATORY_PREFIXES)


def is_capping(flag: str) -> bool:
    return flag in CAPPING_FLAGS or flag in CAPPING_FLAGS_SCHEMA2 or flag.startswith(CAPPING_PREFIXES)


def component_verdict(flags) -> str:
    """Verdict of one criterion component from its flags (spec section 5.8 as changed by 0.5 delta 2)."""
    flags = set(flags)
    if "K1_UNDEFINED" in flags:
        return "UNDEFINED"
    if any(is_mandatory(f) for f in flags):
        return "NOT_FALSIFIABLE"
    if flags & UNTESTED_FLAGS:
        return "UNTESTED"
    if any(is_capping(f) for f in flags):
        return "WEAK"
    return "FALSIFIABLE"


def study_verdict(component_verdicts, study_flags) -> str:
    """Most severe component verdict, raised by any study-level flag (spec section 5.8)."""
    worst = max((VERDICTS.index(v) for v in component_verdicts), default=VERDICTS.index("UNDEFINED"))
    if study_flags:
        worst = max(worst, VERDICTS.index("NOT_FALSIFIABLE"))
    return VERDICTS[worst]


# --------------------------------------------------------------------------
# Per-stream statistics and the check functions (pure)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class StreamStats:
    """Outcome counts of one component on one stream."""

    holds: int
    undefined: int
    n: int
    hard_undefined: int = 0  # spec 0.7, section 1: the part of ``undefined`` that is a failure (``e_s``), not an abstention

    @property
    def abstained(self) -> int:
        """Soft UNDEFINED outcomes: the criterion itself returned UNDEFINED (``a_s``, spec 0.7 section 1)."""
        return self.undefined - self.hard_undefined

    @property
    def fails(self) -> int:
        return self.n - self.holds - self.undefined

    @property
    def outcome(self) -> str:
        """Single outcome; defined only for ``n == 1`` (deterministic mode)."""
        if self.n != 1:
            raise ValueError("outcome is defined only for n == 1")
        if self.holds:
            return HOLDS
        return UNDEFINED if self.undefined else FAILS

    @property
    def rate(self) -> float:
        return self.holds / self.n if self.n else 0.0

    @property
    def inconclusive(self) -> bool:
        """More than 50% UNDEFINED (spec sections 5.3-5.5)."""
        return 2 * self.undefined > self.n


@dataclass(frozen=True)
class Context:
    """Constants of one evaluation: mode, per-bound level ``a`` and targets."""

    deterministic: bool
    a: float
    power: float
    size: float


def sl(low: StreamStats, high: StreamStats, ctx: Context) -> bool:
    """``SL(low, high)`` in stochastic or deterministic mode (spec sections 4.2, 4.3)."""
    if ctx.deterministic:
        return sl_deterministic(low.outcome, high.outcome)
    return sl_stochastic(low.holds, low.n, high.holds, high.n, ctx.a)


def is_resolvable(value: Any, scale: Any) -> bool:
    """Resolution test for a ``(value, scale)`` declaration (spec section 5.2).

    Unresolvable if ``value == 0``, if either is not finite, or if
    ``float64(scale) + float64(value) == float64(scale)``.  Anything that cannot
    be converted to float64 fails closed (unresolvable).
    """
    try:
        v = np.float64(value)
        s = np.float64(scale)
    except (TypeError, ValueError):
        return False
    if not (np.isfinite(v) and np.isfinite(s)):
        return False
    if v == 0:
        return False
    return bool(s + v != s)


K1_STREAMS = ("world:plus", "world:minus", "world:null")
K1_MAJORITY_STREAMS = ("world:minus", "world:null")  # abstention on most of these streams caps the verdict (spec 0.7, 2.1)


def check_k1(stats: Mapping[str, StreamStats]) -> list:
    """K1 as a failure rule, abstention counted as no claim (spec 0.7, section 2.1).

    ``K1_UNDEFINED`` if a K1 stream has a hard UNDEFINED outcome (a failure, exactly as 0.4 treated every UNDEFINED) or
    if the criterion abstains on more than half of the ``plus`` samples.  Otherwise: the information flag
    ``K1_ABSTAINED:<stream>`` for every K1 stream with an abstention, and the capping flag
    ``K1_ABSTAINED_MAJORITY:<stream>`` for ``world:minus`` / ``world:null`` with more than half abstentions.
    """
    present = [s for s in K1_STREAMS if s in stats]
    if any(stats[s].hard_undefined > 0 for s in present):
        return ["K1_UNDEFINED"]
    plus = stats.get("world:plus")
    if plus is not None and 2 * plus.abstained > plus.n:
        return ["K1_UNDEFINED"]
    flags = []
    for s in present:
        if stats[s].abstained > 0:
            flags.append(f"K1_ABSTAINED:{s}")
            if s in K1_MAJORITY_STREAMS and 2 * stats[s].abstained > stats[s].n:
                flags.append(f"K1_ABSTAINED_MAJORITY:{s}")
    return flags


def check_k2(plus: StreamStats, minus: StreamStats, ctx: Context, unresolvable: bool) -> list:
    """K2: reachability, separation, resolution and targets (spec section 5.2)."""
    flags = []
    if plus.holds == 0:
        flags.append("K2_HOLDS_UNREACHABLE")
    if minus.holds == minus.n:
        flags.append("K2_FAILS_UNREACHABLE")
    if not sl(minus, plus, ctx):
        flags.append("K2_NO_SEPARATION")
    if unresolvable:
        flags.append("K2_UNRESOLVABLE")
    if not ctx.deterministic:
        if wilson_upper(plus.holds, plus.n, ctx.a) < ctx.power:
            flags.append("K2_LOW_POWER")
        if wilson_lower(minus.holds, minus.n, ctx.a) > ctx.size:
            flags.append("K2_HIGH_SIZE")
    return flags


def check_high_rate(streams: Mapping[str, StreamStats], ctx: Context) -> list:
    """High-rate rule for streams that must satisfy SL against plus (spec section 5.2)."""
    if ctx.deterministic:
        return []
    return [
        f"HIGH_RATE:{name}"
        for name, st in streams.items()
        if wilson_lower(st.holds, st.n, ctx.a) > ctx.size
    ]


def check_k3(plus: StreamStats, premise: StreamStats, role: str, unresolvable: bool, ctx: Context) -> list:
    """K3 for one premise and one component (spec section 5.3).

    More than 50% UNDEFINED -> ``K3_INCONCLUSIVE`` which replaces the
    NOT_TESTED decision.  An unresolvable magnitude on a tested premise always
    fails K3 (spec section 5.2).
    """
    flags = []
    if premise.inconclusive:
        flags.append("K3_INCONCLUSIVE")
    if role == "tested":
        if unresolvable:
            flags.append("K3_PREMISE_NOT_TESTED")
        elif not premise.inconclusive and not sl(premise, plus, ctx):
            flags.append("K3_PREMISE_NOT_TESTED")
    return flags


def check_k4(plus: StreamStats, controls: Mapping[str, StreamStats], waived: bool, ctx: Context) -> list:
    """K4: control presence, waiver and specificity (spec section 5.4)."""
    flags = []
    if waived:
        flags.append("K4_WAIVED")
    elif not controls:
        flags.append("K4_NO_CONTROL")
    for st in controls.values():
        if not sl(st, plus, ctx):
            flags.append("K4_CONTROL_ALSO_HOLDS")
        if st.inconclusive:
            flags.append("K4_INCONCLUSIVE")
    return flags


def check_k5(
    plus: StreamStats,
    noise: StreamStats,
    zeros: StreamStats,
    null: Optional[StreamStats],
    shuffles: Mapping[str, StreamStats],
    ctx: Context,
) -> list:
    """K5: vacuity probes, null world and optional shuffle probes (spec section 5.5)."""
    flags = []
    if not sl(noise, plus, ctx):
        flags.append("K5_HOLDS_ON_NOISE")
    if not sl(zeros, plus, ctx):
        flags.append("K5_HOLDS_ON_DEGENERATE")
    if null is not None and not sl(null, plus, ctx):
        flags.append("K5_HOLDS_ON_NULL")
    for st in shuffles.values():
        if not sl(st, plus, ctx):
            flags.append("K5_HOLDS_ON_SHUFFLE")
    probe_stats = {probes.PROBE_NOISE: noise, probes.PROBE_ZEROS: zeros, **shuffles}
    for name, st in probe_stats.items():
        if st.inconclusive:
            flags.append(f"K5_INCONCLUSIVE:{name}")
    return flags


# --------------------------------------------------------------------------
# Criterion return values (spec section 3)
# --------------------------------------------------------------------------

def _classify(value: Any) -> Optional[str]:
    """HOLDS / FAILS / UNDEFINED for a scalar return, or ``None`` for a bad type."""
    if value is None:
        return UNDEFINED
    if isinstance(value, (bool, np.bool_)):
        return HOLDS if bool(value) else FAILS
    return None


SOFT = "soft"  # spec 0.7, section 1: UNDEFINED because the criterion returned it (an abstention)
HARD = "hard"  # spec 0.7, section 1: every other UNDEFINED outcome (a failure)
CAUSE_BAD_RETURN = "BAD_RETURN"  # recorded in ``errors`` next to the exception names (spec 0.7, section 2.4)
CAUSE_MISSING_COMPONENT = "MISSING_COMPONENT"


def classify_return(criterion: Criterion, value: Any) -> tuple:
    """``(outcomes, bad_return_ids, mismatch, kinds, causes)`` of a ``fn`` return value (spec sections 3; 0.7 section 1).

    ``kinds`` maps the component ids whose outcome is UNDEFINED to ``SOFT`` (``None`` as the whole return or as the value
    of a declared component) or ``HARD`` (a bad type, a non-dict return of a criterion with components, a declared
    component missing from the returned dict); ``causes`` maps the hard ones to ``BAD_RETURN`` or ``MISSING_COMPONENT``.
    """
    ids = criterion_component_ids(criterion)
    if criterion.components is None:
        outcome = _classify(value)
        if outcome is None:
            return {ids[0]: UNDEFINED}, {ids[0]}, False, {ids[0]: HARD}, {ids[0]: CAUSE_BAD_RETURN}
        kinds = {ids[0]: SOFT} if outcome == UNDEFINED else {}
        return {ids[0]: outcome}, set(), False, kinds, {}
    if value is None:
        return {cid: UNDEFINED for cid in ids}, set(), False, {cid: SOFT for cid in ids}, {}
    if not isinstance(value, dict):
        return ({cid: UNDEFINED for cid in ids}, set(ids), True, {cid: HARD for cid in ids},
                {cid: CAUSE_BAD_RETURN for cid in ids})
    outcomes, bad, kinds, causes = {}, set(), {}, {}
    for name, cid in zip(criterion.components, ids):
        if name not in value:
            outcomes[cid] = UNDEFINED
            kinds[cid], causes[cid] = HARD, CAUSE_MISSING_COMPONENT
            continue
        outcome = _classify(value[name])
        if outcome is None:
            outcomes[cid] = UNDEFINED
            bad.add(cid)
            kinds[cid], causes[cid] = HARD, CAUSE_BAD_RETURN
        else:
            outcomes[cid] = outcome
            if outcome == UNDEFINED:
                kinds[cid] = SOFT
    mismatch = set(value.keys()) != set(criterion.components)
    return outcomes, bad, mismatch, kinds, causes


def normalize_return(criterion: Criterion, value: Any) -> tuple:
    """Map a ``fn`` return value to ``(outcomes, bad_return_ids, mismatch)`` (spec section 3).

    ``outcomes`` maps component id to an outcome.  A bad type is UNDEFINED with
    ``BAD_RETURN``.  With declared components a non-dict (other than ``None``)
    is a bad return and a mismatch; missing or extra keys are a mismatch and a
    missing component is UNDEFINED.  :func:`classify_return` adds the kind of every UNDEFINED outcome.
    """
    return classify_return(criterion, value)[:3]


# --------------------------------------------------------------------------
# Sample collection
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Sample:
    """A generated data sample, or the name of the exception that prevented it."""

    data: Optional[dict]
    error: Optional[str]


@dataclass(frozen=True)
class StreamDef:
    """One comparison stream and the criteria evaluated on it."""

    name: str
    kind: str  # "world" | "premise" | "control" | "probe"
    ref: Any
    criteria: tuple


def build_plan(study: Study) -> list:
    """All streams of a study in a fixed order (spec section 4, stream names)."""
    every = tuple(study.criteria)

    def listed(ids) -> tuple:
        return tuple(c for c in study.criteria if c.id in ids)

    plan = [StreamDef("world:plus", "world", "plus", every), StreamDef("world:minus", "world", "minus", every)]
    if "null" in study.worlds:
        plan.append(StreamDef("world:null", "world", "null", every))
    for p in study.premises:
        plan.append(StreamDef(f"premise:{p.id}", "premise", p, listed(p.criteria)))
    for c in study.controls:
        plan.append(StreamDef(f"control:{c.id}", "control", c, listed(c.criteria)))
    plan.append(StreamDef(f"probe:{probes.PROBE_NOISE}", "probe", probes.PROBE_NOISE, every))
    plan.append(StreamDef(f"probe:{probes.PROBE_ZEROS}", "probe", probes.PROBE_ZEROS, every))
    for a, b in study.relational:
        plan.append(StreamDef(f"probe:{probes.shuffle_name(a, b)}", "probe", (a, b), every))
    return plan


def count_comparisons(study: Study) -> int:
    """Total number of SL comparisons ``m`` (spec section 4.2), fixed by the declaration."""
    total = 0
    for crit in study.criteria:
        per_component = 1  # K2 separation
        per_component += sum(1 for p in study.premises if p.role == "tested" and crit.id in p.criteria)
        per_component += sum(1 for c in study.controls if crit.id in c.criteria)
        per_component += 2  # noise and zeros
        per_component += 1 if "null" in study.worlds else 0
        per_component += len(study.relational)
        total += per_component * len(criterion_component_ids(crit))
    return total


def _call(fn, *args) -> Sample:
    """Call user code that yields data; exceptions become an error name (spec section 3)."""
    try:
        return Sample(validate_data(fn(*args)), None)
    except Exception as exc:
        return Sample(None, type(exc).__name__)


def make_sample(study: Study, sd: StreamDef, i: int, plus: Sample) -> Sample:
    """Data of stream ``sd`` for sample ``i``, derived from the shared plus sample (spec section 4)."""
    seed = study.budget.base_seed

    def rng(stream: str):
        return stream_rng(seed, stream, i)

    if sd.kind == "world":
        if sd.ref == "plus":
            return plus
        return _call(study.worlds[sd.ref].generate, rng(sd.name))
    if sd.kind == "control" and sd.ref.world is not None:
        return _call(sd.ref.world.generate, rng(sd.name))
    if plus.data is None:
        return Sample(None, plus.error)
    if sd.kind == "premise":
        return _call(sd.ref.mutate, copy_data(plus.data), rng(f"premise-rng:{sd.ref.id}"))
    if sd.kind == "control":
        return _call(sd.ref.transform, copy_data(plus.data), rng(sd.name))
    name = sd.name
    if sd.ref == probes.PROBE_NOISE:
        return _call(probes.noise_probe, copy_data(plus.data), rng(name))
    if sd.ref == probes.PROBE_ZEROS:
        return _call(probes.zeros_probe, copy_data(plus.data), rng(name))
    a, b = sd.ref
    return _call(probes.shuffle_probe, copy_data(plus.data), rng(name), a, b)


class Evaluation(NamedTuple):
    """One criterion on one sample, with the kind of every UNDEFINED outcome (spec 0.7, sections 1 and 2.4)."""

    outcomes: dict  # component id -> HOLDS / FAILS / UNDEFINED
    bad: set  # component ids with a BAD_RETURN
    mismatch: bool
    error: Optional[str]  # name of the exception, or of the failed generation, that made every component UNDEFINED
    kinds: dict  # component id -> SOFT / HARD, for the UNDEFINED outcomes only
    causes: dict  # component id -> BAD_RETURN / MISSING_COMPONENT, for the hard outcomes that are not an ``error``


def evaluate_detailed(criterion: Criterion, sample: Sample) -> Evaluation:
    """Evaluate one criterion on one sample and classify its UNDEFINED outcomes (spec section 3; 0.7 section 1)."""
    ids = criterion_component_ids(criterion)
    if sample.data is None:  # failed or invalid generation: the sample has no data
        return Evaluation({cid: UNDEFINED for cid in ids}, set(), False, sample.error, {cid: HARD for cid in ids}, {})
    try:
        value = criterion.fn(copy_data(sample.data))
    except Exception as exc:  # an exception the criterion did not handle (also the leak guard's PermissionError)
        return Evaluation({cid: UNDEFINED for cid in ids}, set(), False, type(exc).__name__,
                          {cid: HARD for cid in ids}, {})
    outcomes, bad, mismatch, kinds, causes = classify_return(criterion, value)
    return Evaluation(outcomes, bad, mismatch, None, kinds, causes)


def evaluate_criterion(criterion: Criterion, sample: Sample) -> tuple:
    """Evaluate one criterion on one sample: ``(outcomes, bad, mismatch, error)`` (spec section 3)."""
    return tuple(evaluate_detailed(criterion, sample))[:4]


@dataclass
class Collected:
    """Raw outcomes of one evaluation pass."""

    outcomes: dict  # stream -> component id -> [outcome per index]
    errors: dict  # stream -> component id -> Counter(exception name, BAD_RETURN, MISSING_COMPONENT) over counted samples
    bad_return: set
    mismatch: set  # criterion ids
    first_plus: Optional[dict]  # plus sample at index 0, for the probe notes
    first_minus: Optional[dict] = None  # minus sample at index 0 (spec 0.5 delta 1.1, deterministic mode)
    # stream -> component id -> [SOFT / HARD for an UNDEFINED outcome, None otherwise, per index] (spec 0.7, section 2.4)
    kinds: dict = field(default_factory=dict)
    # stream -> component id -> [cause of a hard UNDEFINED (exception name, BAD_RETURN, MISSING_COMPONENT), None otherwise]
    causes: dict = field(default_factory=dict)


def collect(study: Study, plan: list, indices, n_counted: int) -> Collected:
    """Run every stream for the given sample indices (spec section 4).

    Records with every UNDEFINED outcome its kind (soft or hard) per stream, component and index (spec 0.7, 2.4).  Every
    hard UNDEFINED over the counted indices also enters ``errors`` under its cause, so that the error counts of a stream
    add up to its ``hard_undefined``.
    """
    outcomes: dict = {sd.name: {} for sd in plan}
    errors: dict = {sd.name: {} for sd in plan}
    kinds: dict = {sd.name: {} for sd in plan}
    causes: dict = {sd.name: {} for sd in plan}
    bad_return: set = set()
    mismatch: set = set()
    first_plus = None
    first_minus = None
    seed = study.budget.base_seed
    for i in indices:
        plus = _call(study.worlds["plus"].generate, stream_rng(seed, "world:plus", i))
        if i == 0:
            first_plus = plus.data
        for sd in plan:
            sample = make_sample(study, sd, i, plus)
            if i == 0 and sd.kind == "world" and sd.ref == "minus":
                first_minus = sample.data
            for crit in sd.criteria:
                ev = evaluate_detailed(crit, sample)
                bad_return |= ev.bad
                if ev.mismatch:
                    mismatch.add(crit.id)
                for cid, outcome in ev.outcomes.items():
                    outcomes[sd.name].setdefault(cid, []).append(outcome)
                    kind = ev.kinds.get(cid) if outcome == UNDEFINED else None
                    kinds[sd.name].setdefault(cid, []).append(kind)
                    cause = (ev.error or ev.causes.get(cid, CAUSE_BAD_RETURN)) if kind == HARD else None
                    causes[sd.name].setdefault(cid, []).append(cause)
                    if kind == HARD and i < n_counted:
                        errors[sd.name].setdefault(cid, Counter())[cause] += 1
    return Collected(outcomes, errors, bad_return, mismatch, first_plus, first_minus, kinds, causes)


def _stats(outcomes: list, n: int, kinds: Optional[list] = None) -> StreamStats:
    counted = outcomes[:n]
    hard = (kinds[:n] if kinds is not None else []).count(HARD)
    return StreamStats(counted.count(HOLDS), counted.count(UNDEFINED), n, hard)


def is_random_probe(stream: str) -> bool:
    """Kapi's own random probes: ``probe:noise`` and ``probe:shuffle:*`` (spec section 4.3)."""
    return stream == f"probe:{probes.PROBE_NOISE}" or stream.startswith("probe:shuffle:")


def combine_probe_draws(draws) -> str:
    """Single outcome of the deterministic-mode draws of a random probe (spec section 4.3).

    HOLDS if any draw HOLDS; otherwise UNDEFINED if at least two draws are
    UNDEFINED; otherwise FAILS.
    """
    draws = list(draws)
    if HOLDS in draws:
        return HOLDS
    if draws.count(UNDEFINED) >= 2:
        return UNDEFINED
    return FAILS


def stream_stats(stream: str, outcomes: list, n: int, deterministic: bool, kinds: Optional[list] = None) -> StreamStats:
    """Counts of a stream; in deterministic mode random probes use the combined outcome (n stays 1).

    ``kinds`` is the recorded kind of every outcome (``collect``); without it no UNDEFINED outcome counts as hard.  A
    combined random-probe outcome that is UNDEFINED is hard if any of its UNDEFINED draws is (spec 0.7, 2.4 does not
    say; it keeps ``hard_undefined <= undefined``; post-freeze R-3).
    """
    if deterministic and is_random_probe(stream):
        combined = combine_probe_draws(outcomes)
        hard = 0
        if combined == UNDEFINED and kinds is not None:
            hard = int(any(k == HARD for o, k in zip(outcomes, kinds) if o == UNDEFINED))
        return StreamStats(int(combined == HOLDS), int(combined == UNDEFINED), 1, hard)
    return _stats(outcomes, n, kinds)


def combined_probe_errors(outcomes: list, kinds: list, causes: list) -> dict:
    """``errors`` of a random probe in deterministic mode, from the same combined rule as ``hard_undefined`` (R-3).

    Exactly one entry, the cause of the first hard UNDEFINED draw, when the combined outcome is UNDEFINED and at least
    one UNDEFINED draw is hard; nothing otherwise (also not when draw 0 failed but the combined outcome is HOLDS or FAILS).
    """
    if combine_probe_draws(outcomes) != UNDEFINED:
        return {}
    for outcome, kind, cause in zip(outcomes, kinds, causes):
        if outcome == UNDEFINED and kind == HARD:
            return {cause: 1}
    return {}


def _round(x: float) -> float:
    return round(float(x), 12)


# --------------------------------------------------------------------------
# Evaluation driver
# --------------------------------------------------------------------------

def tolerance_problems(criterion: Criterion) -> list:
    """Names of unresolvable declared tolerances of a criterion (spec section 5.2)."""
    problems = []
    for name in sorted(criterion.tolerances, key=str):
        decl = criterion.tolerances[name]
        try:
            value, scale = decl
        except (TypeError, ValueError):
            problems.append(f"tolerance:{name}")
            continue
        if not is_resolvable(value, scale):
            problems.append(f"tolerance:{name}")
    return problems


def premise_unresolvable(premise) -> bool:
    """True if the premise declares a magnitude that is unresolvable (spec section 5.2)."""
    if premise.magnitude is None:
        return False
    try:
        value, scale = premise.magnitude
    except (TypeError, ValueError):
        return True
    return not is_resolvable(value, scale)


def apply_cascade_suppression(flags, plus: StreamStats, keep_not_tested: bool) -> tuple:
    """Cascade suppression when plus never holds (v0.2 delta 2). Returns ``(kept_flags, suppressed)``.

    If ``plus`` has zero HOLDS (deterministic mode: its outcome is not HOLDS), the SL-derived flags in
    ``SUPPRESSIBLE_FLAGS`` are removed and returned as a sorted list.  ``K3_PREMISE_NOT_TESTED`` is kept when
    ``keep_not_tested`` (an unresolvable tested-premise magnitude caused it).  Non-SL flags are never touched.
    """
    flags = set(flags)
    if plus.holds != 0:
        return flags, []
    dropped = {f for f in flags if f in SUPPRESSIBLE_FLAGS and not (f == "K3_PREMISE_NOT_TESTED" and keep_not_tested)}
    return flags - dropped, sorted(dropped)


def evaluate(study: Study, quick: bool, suppress_cascade: bool = True) -> dict:
    """Run the complete evaluation once (all streams, all checks).  Pure given the study.

    Returns a JSON-ready dict with components, premise map, study flags (without
    the K6 flags, which the orchestrator adds) and bookkeeping.  ``suppress_cascade=False``
    disables v0.2 delta 2 (used only to prove that suppression never changes a verdict).
    """
    det = study.deterministic
    n = sample_count(det, study.budget.samples, study.budget.quick_samples, quick)
    m = count_comparisons(study)
    a = bonferroni_a(study.targets.alpha_family, m)
    ctx = Context(det, a, study.targets.power, study.targets.size)
    plan = build_plan(study)
    indices = DETERMINISM_INDICES if det else range(n)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        col = collect(study, plan, indices, n)
        minus_info = _minus_analysis(study, col)  # spec 0.5 delta 1; after collect, so counted samples are unaffected

    components, premise_map = [], {}
    for crit in study.criteria:
        tol_problems = tolerance_problems(crit)
        for cid in criterion_component_ids(crit):
            components.append(
                _component_record(study, crit, cid, plan, col, ctx, n, tol_problems, premise_map, suppress_cascade,
                                  minus_info[crit.id])
            )

    study_flags, details = _study_level_flags(study, col, plan, n)
    notes = {}
    if col.first_plus is not None:
        notes = {p: probes.unchanged_keys(col.first_plus, p) for p in (probes.PROBE_NOISE, probes.PROBE_ZEROS)}
    return {
        "n": n,
        "m_comparisons": m,
        "alpha_per_bound": a,
        "components": components,
        "premise_map": premise_map,
        "study_flags": study_flags,
        "study_flag_details": details,
        "probe_unchanged_keys": notes,
    }


def _minus_analysis(study: Study, col: Collected) -> dict:
    """Identical-minus check for every criterion (spec 0.5 delta 1.1).

    Deterministic mode compares the plus and minus samples at ``i = 0`` that were already generated.  Stochastic mode
    generates one extra paired minus sample with the generator of stream ``world:plus``, ``i = 0``; it is used here
    only and never counted.  A sample that could not be generated leaves the check without data (not identical).
    """
    det = study.deterministic
    if det:
        minus = col.first_minus
    else:
        minus = _call(study.worlds["minus"].generate, stream_rng(study.budget.base_seed, "world:plus", 0)).data
    return minus_check.analyse(study.criteria, col.first_plus, minus, paired=not det)


def _component_record(study, crit, cid, plan, col, ctx, n, tol_problems, premise_map, suppress_cascade=True,
                      minus_info=None) -> dict:
    """All checks for one component; fills ``premise_map`` (spec sections 5.1-5.5, 0.5 delta 1)."""
    if minus_info is None:  # direct callers without an analysis: nothing known, nothing raised
        minus_info = {"minus_check": {"identical": False, "read_keys": [], "changed_keys": [],
                                      "paired": not study.deterministic}, "flags": set()}
    stats = {
        sd.name: stream_stats(sd.name, col.outcomes[sd.name][cid], n, ctx.deterministic, col.kinds[sd.name][cid])
        for sd in plan
        if cid in col.outcomes[sd.name]
    }
    plus, minus = stats["world:plus"], stats["world:minus"]
    unresolvable = list(tol_problems)
    flags = set(check_k1(stats))

    comparison = {}  # streams that must satisfy SL against plus (HIGH_RATE rule)
    for p in study.premises:
        if crit.id in p.criteria and premise_unresolvable(p):
            unresolvable.append(f"premise:{p.id}")
    flags.update(check_k2(plus, minus, ctx, bool(unresolvable)))

    for p in study.premises:
        if crit.id not in p.criteria:
            continue
        st = stats[f"premise:{p.id}"]
        flags.update(check_k3(plus, st, p.role, premise_unresolvable(p), ctx))
        premise_map.setdefault(p.id, {})[cid] = _round(plus.rate - st.rate)
        if p.role == "tested":
            comparison[f"premise:{p.id}"] = st

    controls = {f"control:{c.id}": stats[f"control:{c.id}"] for c in study.controls if crit.id in c.criteria}
    comparison.update(controls)
    waived = bool(crit.control_waiver and crit.control_waiver.strip())
    flags.update(check_k4(plus, controls, waived, ctx))

    shuffles = {probes.shuffle_name(x, y): stats[f"probe:{probes.shuffle_name(x, y)}"] for x, y in study.relational}
    null = stats.get("world:null")
    noise, zeros = stats[f"probe:{probes.PROBE_NOISE}"], stats[f"probe:{probes.PROBE_ZEROS}"]
    flags.update(check_k5(plus, noise, zeros, null, shuffles, ctx))
    if null is not None:
        comparison["world:null"] = null
    comparison[f"probe:{probes.PROBE_NOISE}"] = noise
    comparison[f"probe:{probes.PROBE_ZEROS}"] = zeros
    comparison.update({f"probe:{k}": v for k, v in shuffles.items()})
    flags.update(check_high_rate(comparison, ctx))
    if cid in col.bad_return:
        flags.add("BAD_RETURN")

    keep_not_tested = any(
        p.role == "tested" and crit.id in p.criteria and premise_unresolvable(p) for p in study.premises
    )
    flags |= minus_info["flags"]
    # 0.5 delta 1.5: an identical minus carries no information about these flags.  This is meant to change the verdict
    # (NOT_FALSIFIABLE -> UNTESTED), so the verdict is taken after it.  0.4 delta 2 is computed from the same flag
    # set, independently, so a flag may appear in both lists.
    identical = minus_info["minus_check"]["identical"]
    suppressed_minus = sorted(flags & minus_check.SUPPRESSIBLE_WHEN_IDENTICAL) if identical else []
    flags_minus = flags - set(suppressed_minus)
    kept, suppressed = apply_cascade_suppression(flags, plus, keep_not_tested)
    kept = kept - set(suppressed_minus)
    verdict = component_verdict(flags_minus)
    if component_verdict(kept) != verdict:  # 0.4 delta 2: the mandatory K2_HOLDS_UNREACHABLE makes this impossible
        raise AssertionError("cascade suppression changed a verdict")
    if suppress_cascade:
        flags = kept
    else:
        flags = flags_minus
        suppressed = []

    record = {
        "id": cid,
        "regime": crit.regime,
        "verdict": verdict,
        "flags": sorted(flags),
        "counts": {
            s: {"holds": st.holds, "undefined": st.undefined, "hard_undefined": st.hard_undefined, "n": st.n}
            for s, st in stats.items()
        },
        "bounds": {} if ctx.deterministic else {
            s: dict(zip(("lower", "upper"), map(_round, wilson_bounds(st.holds, st.n, ctx.a))))
            for s, st in stats.items()
        },
        "errors": _errors_record(col, cid, stats, ctx.deterministic),
        "unresolvable": sorted(unresolvable),
    }
    record["minus_check"] = dict(minus_info["minus_check"])
    if suppressed:
        record["suppressed_by"] = SUPPRESSED_BY
        record["suppressed"] = suppressed
    if suppressed_minus:
        record["suppressed_minus"] = suppressed_minus
    if ctx.deterministic:  # raw draws of Kapi's random probes, so the combination is auditable
        record["probe_draws"] = {s: list(col.outcomes[s][cid]) for s in stats if is_random_probe(s)}
    return record


def _errors_record(col: Collected, cid: str, stats: dict, deterministic: bool) -> dict:
    """``errors[stream][component]`` counts: the counted indices, except the random probes of a deterministic study,
    whose entry follows the combined outcome (``combined_probe_errors``)."""
    out = {}
    for s in stats:
        if deterministic and is_random_probe(s):
            found = combined_probe_errors(col.outcomes[s][cid], col.kinds[s][cid], col.causes[s][cid])
        elif cid in col.errors[s]:
            found = dict(sorted(col.errors[s][cid].items()))
        else:
            continue
        if found:
            out[s] = found
    return out


def _study_level_flags(study: Study, col: Collected, plan: list, n: int) -> tuple:
    """K7 flags and the determinism check (spec sections 4.3, 5.7)."""
    flags, details = set(), {}
    covered = {c.regime for c in study.criteria}
    uncovered = sorted(r for r in study.regimes if r not in covered)
    if uncovered:
        flags.add("K7_REGIME_UNCOVERED")
        details["K7_REGIME_UNCOVERED"] = uncovered
    if col.mismatch:
        flags.add("K7_COMPONENT_MISMATCH")
        details["K7_COMPONENT_MISMATCH"] = sorted(col.mismatch)
    if study.deterministic:
        differing = sorted(
            f"{cid}@{stream}"
            for stream, per_comp in col.outcomes.items()
            if not is_random_probe(stream)  # Kapi's randomness, not the user's (spec section 4.3)
            for cid, outs in per_comp.items()
            if len(set(outs)) > 1
        )
        if differing:
            flags.add("NONDETERMINISTIC")
            details["NONDETERMINISTIC"] = differing
    return sorted(flags), details

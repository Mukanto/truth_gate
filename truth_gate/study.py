"""Study definition API (spec section 3).

A study is a Python file that defines a module-level ``STUDY`` of type
:class:`Study`.  This module holds the declarative dataclasses, the
construction-time validation (``StudyError``) and the loader that executes a
study file.
"""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


class StudyError(Exception):
    """Construction-time validation failure (spec section 3). Verdict: UNDEFINED."""


@dataclass(frozen=True, eq=False)
class Budget:
    """Sample budget (spec sections 3 and 4)."""

    samples: int = 200
    quick_samples: int = 20
    base_seed: int = 20261105


@dataclass(frozen=True, eq=False)
class Targets:
    """Power / size targets and the family-wise alpha (spec section 3)."""

    power: float = 0.8
    size: float = 0.05
    alpha_family: float = 0.05


@dataclass(frozen=True, eq=False)
class World:
    """A synthetic data generator; ``change`` documents how minus differs from plus."""

    generate: Callable[[Any], dict]
    derived_from: Optional[str] = None
    change: str = ""


@dataclass(frozen=True, eq=False)
class Criterion:
    """An acceptance criterion; ``fn`` maps a data dict to bool / None / dict of those."""

    id: str
    fn: Callable[[dict], Any]
    regime: str = "all"
    components: Optional[list] = None
    tolerances: dict = field(default_factory=dict)
    control_waiver: Optional[str] = None


@dataclass(frozen=True, eq=False)
class Premise:
    """A premise mutator; ``role`` is ``"tested"`` or ``"assumed"``."""

    id: str
    mutate: Callable[[dict, Any], dict]
    role: str
    criteria: list
    magnitude: Optional[tuple] = None


@dataclass(frozen=True, eq=False)
class Control:
    """A negative control: exactly one of ``transform`` / ``world``."""

    id: str
    criteria: list
    transform: Optional[Callable[[dict, Any], dict]] = None
    world: Optional[World] = None


@dataclass(frozen=True, eq=False)
class Study:
    """A complete pre-registered study declaration (spec section 3)."""

    name: str
    criteria: list
    worlds: dict
    premises: list = field(default_factory=list)
    controls: list = field(default_factory=list)
    regimes: list = field(default_factory=lambda: ["all"])
    deterministic: bool = False
    budget: Budget = field(default_factory=Budget)
    targets: Targets = field(default_factory=Targets)
    allow_paths: list = field(default_factory=list)
    relational: list = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate(self)


def criterion_component_ids(criterion: Criterion) -> list:
    """Component ids of a criterion: ``[id]`` or ``["id:name", ...]`` (spec section 3)."""
    if criterion.components is None:
        return [criterion.id]
    return [f"{criterion.id}:{name}" for name in criterion.components]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StudyError(message)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_real(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate(study: Study) -> None:
    """Construction-time validation (spec section 3, plus conservative extras)."""
    _require(isinstance(study.name, str) and study.name != "", "study name must be a non-empty string")
    _require(isinstance(study.criteria, list) and len(study.criteria) > 0, "a study needs at least one criterion")
    _require(isinstance(study.worlds, dict), "worlds must be a dict")
    _require(isinstance(study.regimes, list) and len(study.regimes) > 0, "regimes must be a non-empty list")
    _require(all(isinstance(r, str) for r in study.regimes), "regime names must be strings")
    _require(isinstance(study.deterministic, bool), "deterministic must be a bool")
    _validate_settings(study)
    _validate_worlds(study)
    criterion_ids = _validate_criteria(study)
    _validate_premises(study, criterion_ids)
    _validate_controls(study, criterion_ids)
    _validate_paths(study)


def _validate_settings(study: Study) -> None:
    b, t = study.budget, study.targets
    _require(isinstance(b, Budget) and isinstance(t, Targets), "budget / targets have the wrong type")
    _require(_is_int(b.samples) and b.samples >= 1, "budget.samples must be an int >= 1")
    _require(_is_int(b.quick_samples) and b.quick_samples >= 1, "budget.quick_samples must be an int >= 1")
    _require(_is_int(b.base_seed) and b.base_seed >= 0, "budget.base_seed must be an int >= 0")
    _require(_is_real(t.power) and 0.0 < t.power <= 1.0, "targets.power must be in (0, 1]")
    _require(_is_real(t.size) and 0.0 <= t.size < 1.0, "targets.size must be in [0, 1)")
    _require(_is_real(t.alpha_family) and 0.0 < t.alpha_family < 1.0, "targets.alpha_family must be in (0, 1)")


def _validate_worlds(study: Study) -> None:
    for name, world in study.worlds.items():
        _require(isinstance(name, str), "world names must be strings")
        _require(isinstance(world, World) and callable(world.generate), f"world {name!r} is not a valid World")
    _require("plus" in study.worlds, "missing 'plus' world")
    _require("minus" in study.worlds, "missing 'minus' world")


def _validate_criteria(study: Study) -> set:
    ids: set = set()
    component_ids: set = set()
    for c in study.criteria:
        _require(isinstance(c, Criterion), "criteria must be Criterion objects")
        _require(isinstance(c.id, str) and c.id != "", "criterion id must be a non-empty string")
        _require(callable(c.fn), f"criterion {c.id!r}: fn is not callable")
        _require(c.id not in ids, f"duplicate criterion id {c.id!r}")
        ids.add(c.id)
        _require(c.regime in study.regimes, f"criterion {c.id!r}: regime {c.regime!r} is not declared")
        _require(isinstance(c.tolerances, dict), f"criterion {c.id!r}: tolerances must be a dict")
        _require(
            c.control_waiver is None or isinstance(c.control_waiver, str),
            f"criterion {c.id!r}: control_waiver must be a string or None",
        )
        if c.components is not None:
            _require(
                isinstance(c.components, list) and len(c.components) > 0
                and all(isinstance(x, str) and x != "" for x in c.components),
                f"criterion {c.id!r}: components must be a non-empty list of strings",
            )
            _require(len(set(c.components)) == len(c.components), f"criterion {c.id!r}: duplicate component names")
        for cid in criterion_component_ids(c):
            _require(cid not in component_ids, f"duplicate component id {cid!r}")
            component_ids.add(cid)
    return ids


def _validate_premises(study: Study, criterion_ids: set) -> None:
    seen: set = set()
    for p in study.premises:
        _require(isinstance(p, Premise), "premises must be Premise objects")
        _require(isinstance(p.id, str) and p.id != "", "premise id must be a non-empty string")
        _require(p.id not in seen, f"duplicate premise id {p.id!r}")
        seen.add(p.id)
        _require(callable(p.mutate), f"premise {p.id!r}: mutate is not callable")
        _require(p.role in ("tested", "assumed"), f"premise {p.id!r}: role must be 'tested' or 'assumed'")
        _require(isinstance(p.criteria, list), f"premise {p.id!r}: criteria must be a list")
        for cid in p.criteria:
            _require(cid in criterion_ids, f"premise {p.id!r} lists unknown criterion {cid!r}")


def _validate_controls(study: Study, criterion_ids: set) -> None:
    seen: set = set()
    for c in study.controls:
        _require(isinstance(c, Control), "controls must be Control objects")
        _require(isinstance(c.id, str) and c.id != "", "control id must be a non-empty string")
        _require(c.id not in seen, f"duplicate control id {c.id!r}")
        seen.add(c.id)
        _require(
            (c.transform is None) != (c.world is None),
            f"control {c.id!r}: exactly one of transform / world is required",
        )
        _require(c.transform is None or callable(c.transform), f"control {c.id!r}: transform is not callable")
        _require(
            c.world is None or (isinstance(c.world, World) and callable(c.world.generate)),
            f"control {c.id!r}: world is not a valid World",
        )
        _require(isinstance(c.criteria, list), f"control {c.id!r}: criteria must be a list")
        for cid in c.criteria:
            _require(cid in criterion_ids, f"control {c.id!r} lists unknown criterion {cid!r}")


def _validate_paths(study: Study) -> None:
    _require(
        isinstance(study.allow_paths, list) and all(isinstance(p, str) for p in study.allow_paths),
        "allow_paths must be a list of strings",
    )
    _require(len(set(study.allow_paths)) == len(study.allow_paths), "duplicate allow_paths entry")
    _require(isinstance(study.relational, list), "relational must be a list")
    pairs = []
    for pair in study.relational:
        _require(
            isinstance(pair, (tuple, list)) and len(pair) == 2 and all(isinstance(x, str) for x in pair),
            "relational entries must be (str, str) pairs",
        )
        pairs.append(tuple(pair))
    _require(len(set(pairs)) == len(pairs), "duplicate relational pair")


def load_study(path: str, source: bytes) -> Study:
    """Execute a study file and return its ``STUDY`` (spec sections 3 and 5.6).

    The source is compiled from the bytes given by the caller (no import
    machinery, so no ``__pycache__`` access).  The caller is responsible for
    arming the leak guard first.  Exceptions raised by the study module
    propagate; a missing or mistyped ``STUDY`` raises ``StudyError``.
    """
    name = "kapi_study_module"
    module = types.ModuleType(name)
    module.__file__ = path
    code = compile(source, path, "exec")
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        exec(code, module.__dict__)  # noqa: S102 - executing the study file is the purpose
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    study = module.__dict__.get("STUDY")
    if study is None:
        raise StudyError("the study file does not define STUDY")
    if not isinstance(study, Study):
        raise StudyError("STUDY is not a kapi.Study")
    return study

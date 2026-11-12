"""The manifest (spec 0.6, section 3): parse, validate and compile to the 0.3 ``Study`` objects.

Two phases, as in spec section 1.2:

* :func:`parse_manifest` runs **before** the leak guard is armed.  It reads the manifest text, validates every key,
  reads and hashes every data file and every ``python`` reference file.  Any problem is a
  :class:`~truth_gate.common.ManifestError` (exit code 4, no certificate).
* :func:`build_study` runs **under the armed guard**.  It executes the ``python`` reference files and builds the
  ``Study``; every problem there (including 0.3's own validation) is a ``StudyError`` or another exception, which the
  orchestrator records in the certificate (exit code 3).
"""

from __future__ import annotations

import datetime
import json
import math
import os
import sys
import tomllib
import types
from dataclasses import dataclass, field
from typing import Any, Optional

from .common import (
    ManifestError, check_keys, fail, get_bool, get_int, get_number, get_str, get_str_list, is_number, join,
)
from .data_io import Table, load_table, read_bytes, sample_table, sha256_hex
from .k8 import BUILTIN_ID, Invariance, validate_invariances
from .mutations import MutationSet, needs_row_keys, op_names, validate_mutations
from .patterns import CRITERION_KEYS, Pattern
from .study import Budget, Control, Criterion, Premise, Study, StudyError, Targets, World

TOP_KEYS = ("study", "data", "worlds", "criteria", "controls", "premises", "invariances", "budget", "targets", "external")
COLUMN_TYPES = ("float", "int", "bool", "str")
COLUMN_ROLES = ("outcome", "effect", "group", "label", "calibration", "grid", "id", "covariate")
RESAMPLE_MODES = ("bootstrap", "subsample", "none")
ORIGIN_SUGGESTED = "suggested"
WORLD_KEYS = ("file", "provenance", "resample", "fraction", "delimiter", "python", "derive", "mutations", "change",
              "origin")


# --------------------------------------------------------------------------
# Parsed form
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class PyRef:
    """A ``"file.py:function"`` reference."""

    declared: str
    path: str  # real path of the file
    function: str


@dataclass
class WorldSpec:
    name: str
    source: str  # "file" | "python" | "derive"
    change: str = ""
    origin: Optional[str] = None
    table: Optional[Table] = None
    file: Optional[str] = None
    provenance: Optional[str] = None
    resample: Optional[str] = None
    fraction: Optional[float] = None
    ref: Optional[PyRef] = None
    parent: Optional[str] = None
    mutations: list = field(default_factory=list)
    row_keys: tuple = ()


@dataclass
class CriterionSpec:
    id: str
    kind: str  # "pattern" | "command" | "python"
    regime: str = "all"
    control_waiver: Optional[str] = None
    tolerances: dict = field(default_factory=dict)
    components: Optional[list] = None
    origin: Optional[str] = None
    pattern: Optional[Pattern] = None
    argv: Optional[list] = None
    ref: Optional[PyRef] = None


@dataclass
class ControlSpec:
    id: str
    criteria: list
    mutations: Optional[list] = None
    world: Optional[str] = None
    ref: Optional[PyRef] = None
    origin: Optional[str] = None


@dataclass
class PremiseSpec:
    id: str
    role: Any
    criteria: list
    mutations: Optional[list] = None
    ref: Optional[PyRef] = None
    magnitude: Optional[tuple] = None
    origin: Optional[str] = None


@dataclass
class InvarianceSpec:
    id: str
    criteria: list
    mutations: list
    reason: str
    origin: Optional[str] = None


@dataclass
class Manifest:
    path: str
    directory: str
    sha256: str
    parsed: dict
    name: str
    regimes: list
    deterministic: bool
    allow_paths: list
    relational: list
    rows_exchangeable: bool
    rows: list
    columns: dict
    worlds: dict
    criteria: list
    controls: list
    premises: list
    invariances: list
    budget: dict
    targets: dict
    external: dict
    data_files: dict  # real path -> {"path": declared, "sha256": ...}
    python_files: dict  # real path -> {"path": declared, "sha256": ..., "source": bytes}
    plus_rows: tuple = ()
    uses_files: list = field(default_factory=list)  # set by the external session: [{"path", "sha256"}]
    commands: list = field(default_factory=list)  # set by the external session: [{"argv", "sha256"}]

    # -- certificate material -------------------------------------------------

    @property
    def suggested_count(self) -> int:
        """Number of declarations that carry ``origin`` (spec section 8)."""
        entries = list(self.worlds.values()) + self.criteria + self.controls + self.premises + self.invariances
        return sum(1 for e in entries if e.origin is not None)

    def mutation_ops(self) -> dict:
        """The ops of every world, control, premise and invariance (spec section 11, ``mutations``)."""
        return {
            "worlds": [{"id": w.name, "ops": op_names(w.mutations)} for w in self.worlds.values() if w.source == "derive"],
            "controls": [{"id": c.id, "ops": op_names(c.mutations)} for c in self.controls if c.mutations is not None],
            "premises": [{"id": p.id, "ops": op_names(p.mutations)} for p in self.premises if p.mutations is not None],
            "invariances": [{"id": i.id, "ops": op_names(i.mutations)} for i in self.invariances]
            + ([{"id": BUILTIN_ID, "ops": ["permute_rows"]}] if self.rows_exchangeable else []),
        }

    def record(self) -> dict:
        """The ``manifest`` field of the certificate (spec section 11)."""
        def listing(files: dict) -> list:
            return sorted(({"path": f["path"], "sha256": f["sha256"]} for f in files.values()), key=lambda f: f["path"])

        return {
            "sha256": self.sha256,
            "parsed": self.parsed,
            "data_files": listing(self.data_files),
            "python_files": listing(self.python_files),
            "uses_files": list(self.uses_files),
            "provenance": {w.name: w.provenance for w in self.worlds.values() if w.provenance is not None},
            "commands": list(self.commands),
        }


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def _scan(value: Any, where: str) -> None:
    """Datetimes and non-finite numbers are validation errors anywhere (spec section 3)."""
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        fail(where, "datetime values are not allowed")
    if isinstance(value, float) and not math.isfinite(value):
        fail(where, "non-finite numbers are not allowed")
    if isinstance(value, dict):
        for key, item in value.items():
            _scan(item, join(where, key))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _scan(item, f"{where}[{i}]")


def _load_text(path: str, source: bytes) -> dict:
    ext = os.path.splitext(path)[1].lower()
    try:
        text = source.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ManifestError("the manifest is not valid UTF-8") from None
    if ext == ".toml":
        try:
            parsed = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            raise ManifestError(f"TOML syntax error: {exc}") from None
    else:
        try:
            parsed = json.loads(text)
        except ValueError as exc:
            raise ManifestError(f"JSON syntax error: {exc}") from None
    if not isinstance(parsed, dict):
        raise ManifestError("the manifest must be a table (object) at the top level")
    return parsed


class _Parser:
    def __init__(self, path: str, source: bytes) -> None:
        self.path = os.path.realpath(path)
        self.dir = os.path.dirname(self.path)
        self.source = source
        self.data_files: dict = {}
        self.python_files: dict = {}

    # -- helpers -----------------------------------------------------------

    def resolve(self, declared: str) -> str:
        return declared if os.path.isabs(declared) else os.path.join(self.dir, declared)

    def python_ref(self, value: Any, where: str) -> PyRef:
        if not isinstance(value, str):
            fail(where, "must be a string \"file.py:function\"")
        file_part, sep, function = value.rpartition(":")
        if not sep or not file_part or not function.isidentifier():
            fail(where, "must have the form \"file.py:function\"")
        real = os.path.realpath(self.resolve(file_part))
        if not os.path.isfile(real):
            fail(where, f"python file not found: {file_part}")
        if real not in self.python_files:
            raw = read_bytes(real, where)
            self.python_files[real] = {"path": file_part, "sha256": sha256_hex(raw), "source": raw}
        return PyRef(declared=value, path=real, function=function)

    @staticmethod
    def origin(table: dict, where: str) -> Optional[str]:
        if "origin" not in table:
            return None
        value = get_str(table, "origin", where)
        if value != ORIGIN_SUGGESTED:  # post-freeze revision R-9: a typo must not skip the review cap
            fail(join(where, "origin"), f"must be \"{ORIGIN_SUGGESTED}\" (delete the key once the declaration is reviewed)")
        return value

    # -- tables ------------------------------------------------------------

    def parse(self, parsed: dict) -> Manifest:
        for key in parsed:
            if key not in TOP_KEYS:
                fail(key, "unknown table")
        if "study" not in parsed:
            fail("study", "missing required table")
        study = self.study(parsed["study"])
        data = self.data(parsed.get("data", {}))
        budget = self.budget(parsed.get("budget", {}))
        targets = self.targets(parsed.get("targets", {}))
        external = self.external(parsed.get("external", {}))
        worlds = self.worlds(parsed.get("worlds", {}), study["deterministic"], data)
        plus_rows = worlds["plus"].row_keys if "plus" in worlds else ()
        criteria = self.criteria(parsed.get("criteria", []))
        controls = self.controls(parsed.get("controls", []), worlds, plus_rows)
        premises = self.premises(parsed.get("premises", []), plus_rows)
        minus_rows = worlds["minus"].row_keys if "minus" in worlds else ()
        invariances = self.invariances(parsed.get("invariances", []), plus_rows, minus_rows)
        if data["rows_exchangeable"] and "plus" in worlds and "minus" in worlds:
            # the built-in permute_rows invariance (spec section 7) is a row operation on both worlds
            self.check_row_ops([{"op": "permute_rows"}], plus_rows, "data.rows_exchangeable (plus world)")
            self.check_row_ops([{"op": "permute_rows"}], minus_rows, "data.rows_exchangeable (minus world)")
        manifest = Manifest(
            path=self.path, directory=self.dir, sha256=sha256_hex(self.source), parsed=parsed, name=study["name"],
            regimes=study["regimes"], deterministic=study["deterministic"], allow_paths=study["allow_paths"],
            relational=study["relational"], rows_exchangeable=data["rows_exchangeable"], rows=data["rows"],
            columns=data["columns"], worlds=worlds, criteria=criteria, controls=controls, premises=premises,
            invariances=invariances, budget=budget, targets=targets, external=external,
            data_files=self.data_files, python_files=self.python_files, plus_rows=plus_rows,
        )
        return manifest

    def study(self, t: Any) -> dict:
        check_keys(t, "study", ["name"], ["regimes", "deterministic", "allow_paths", "relational"])
        name = get_str(t, "name", "study")
        regimes = get_str_list(t, "regimes", "study") if "regimes" in t else ["all"]
        allow_paths = get_str_list(t, "allow_paths", "study")
        for i, declared in enumerate(allow_paths):
            if not os.path.isfile(self.resolve(declared)):
                fail(f"study.allow_paths[{i}]", f"file not found: {declared}")
        raw_relational = t.get("relational", [])
        if not isinstance(raw_relational, list):
            fail("study.relational", "must be a list of pairs")
        relational = []
        for i, pair in enumerate(raw_relational):
            if not (isinstance(pair, list) and len(pair) == 2 and all(isinstance(p, str) for p in pair)):
                fail(f"study.relational[{i}]", "must be a pair of strings")
            relational.append((pair[0], pair[1]))
        return {"name": name, "regimes": regimes, "deterministic": get_bool(t, "deterministic", "study", False),
                "allow_paths": allow_paths, "relational": relational}

    def data(self, t: Any) -> dict:
        check_keys(t, "data", [], ["rows_exchangeable", "rows", "columns"])
        columns: dict = {}
        raw_columns = t.get("columns", {})
        if not isinstance(raw_columns, dict):
            fail("data.columns", "must be a table")
        for name, decl in raw_columns.items():
            where = join("data.columns", name)
            check_keys(decl, where, ["type"], ["role"])
            ctype = get_str(decl, "type", where)
            if ctype not in COLUMN_TYPES:
                fail(join(where, "type"), f"must be one of {', '.join(COLUMN_TYPES)}")
            role = get_str(decl, "role", where, required=False)
            if role is not None and role not in COLUMN_ROLES:
                fail(join(where, "role"), f"must be one of {', '.join(COLUMN_ROLES)}")
            columns[name] = {"type": ctype, "role": role}
        return {
            "rows_exchangeable": get_bool(t, "rows_exchangeable", "data", False),
            "rows": get_str_list(t, "rows", "data", unique=True),
            "columns": columns,
        }

    def budget(self, t: Any) -> dict:
        check_keys(t, "budget", [], ["samples", "quick_samples", "base_seed"])
        return {k: get_int(t, k, "budget") for k in ("samples", "quick_samples", "base_seed") if k in t}

    def targets(self, t: Any) -> dict:
        check_keys(t, "targets", [], ["power", "size", "alpha_family"])
        return {k: get_number(t, k, "targets") for k in ("power", "size", "alpha_family") if k in t}

    def external(self, t: Any) -> dict:
        check_keys(t, "external", [], ["uses", "env", "startup_timeout_s", "request_timeout_s"])
        uses = get_str_list(t, "uses", "external")
        env = get_str_list(t, "env", "external")
        for i, name in enumerate(env):
            if not name or "=" in name or "\0" in name:
                fail(f"external.env[{i}]", "must be a variable name (not empty, no \"=\")")
        for i, declared in enumerate(uses):
            if not os.path.isfile(self.resolve(declared)):
                fail(f"external.uses[{i}]", f"file not found: {declared}")
        return {
            "uses": uses,
            "env": env,
            "startup_timeout_s": get_number(t, "startup_timeout_s", "external", required=False, default=120, lo=0,
                                            lo_open=True),
            "request_timeout_s": get_number(t, "request_timeout_s", "external", required=False, default=60, lo=0,
                                            lo_open=True),
        }

    # -- worlds ------------------------------------------------------------

    def worlds(self, t: Any, deterministic: bool, data: dict) -> dict:
        if not isinstance(t, dict):
            fail("worlds", "must be a table of worlds")
        worlds: dict = {}
        for name, wt in t.items():
            worlds[name] = self.world(name, wt, deterministic, data)
        for name, world in worlds.items():  # parents must exist, and derivation must not cycle
            if world.source == "derive":
                chain, current = [name], world
                while current.source == "derive":
                    if current.parent not in worlds:
                        fail(f"worlds.{current.name}.derive", f"unknown world {current.parent!r}")
                    if current.parent in chain:
                        fail(f"worlds.{name}.derive", "derivation cycle: " + " -> ".join(chain + [current.parent]))
                    chain.append(current.parent)
                    current = worlds[current.parent]
        for name, world in worlds.items():
            if world.source == "derive":
                world.row_keys = _row_keys_of(world, worlds)
                self.check_row_ops(world.mutations, world.row_keys, f"worlds.{name}.mutations")
            if world.source == "file" and not deterministic and world.resample in ("bootstrap", "subsample") \
                    and not world.row_keys:
                fail(f"worlds.{name}", "a file world needs row-aligned keys to be resampled (list them in `[data] rows`)")
        return worlds

    def world(self, name: str, wt: Any, deterministic: bool, data: dict) -> WorldSpec:
        where = f"worlds.{name}"
        check_keys(wt, where, [], WORLD_KEYS)
        sources = [k for k in ("file", "python", "derive") if k in wt]
        if len(sources) != 1:
            fail(where, "needs exactly one of `file`, `python` and `derive`")
        change = get_str(wt, "change", where, required=(name == "minus"), default="")
        spec = WorldSpec(name=name, source=sources[0], change=change, origin=self.origin(wt, where))
        source = sources[0]
        file_only = ("provenance", "resample", "fraction", "delimiter")
        if source != "file":
            for key in file_only:
                if key in wt:
                    fail(join(where, key), "only valid for `file` worlds")
        if source != "derive" and "mutations" in wt:
            fail(join(where, "mutations"), "only valid for `derive` worlds")
        if source == "python":
            spec.ref = self.python_ref(wt["python"], join(where, "python"))
            spec.row_keys = tuple(data["rows"])
        elif source == "derive":
            spec.parent = get_str(wt, "derive", where)
            if "mutations" not in wt:
                fail(join(where, "mutations"), "missing required key (a `derive` world needs mutations)")
            spec.mutations = validate_mutations(wt["mutations"], join(where, "mutations"))
        else:
            self.file_world(spec, wt, where, deterministic, data)
        return spec

    def file_world(self, spec: WorldSpec, wt: dict, where: str, deterministic: bool, data: dict) -> None:
        spec.file = get_str(wt, "file", where)
        spec.provenance = get_str(wt, "provenance", where)
        if not spec.provenance.strip() or spec.provenance.strip() == "TODO":
            fail(join(where, "provenance"), "must say where the file comes from (it is empty or still \"TODO\")")
        delimiter = get_str(wt, "delimiter", where, required=False)
        real = os.path.realpath(self.resolve(spec.file))
        if not os.path.isfile(real):
            fail(join(where, "file"), f"data file not found: {spec.file}")
        table, digest = load_table(real, where, data["columns"], data["rows"], delimiter)
        self.data_files[real] = {"path": spec.file, "sha256": digest}
        spec.table = table
        spec.row_keys = table.row_keys
        resample = get_str(wt, "resample", where, required=False)
        if resample is not None and resample not in RESAMPLE_MODES:
            fail(join(where, "resample"), f"must be one of {', '.join(RESAMPLE_MODES)}")
        if deterministic:
            if resample not in (None, "none"):
                fail(join(where, "resample"), "in a deterministic study `resample` must be \"none\"")
            if "fraction" in wt:
                fail(join(where, "fraction"), "not valid in a deterministic study")
            spec.resample = "none"
        else:
            spec.resample = resample or "bootstrap"
            if spec.resample == "none":
                fail(join(where, "resample"), "\"none\" is only valid in a deterministic study")
            if spec.resample == "subsample":
                spec.fraction = get_number(wt, "fraction", where, lo=0, hi=1, lo_open=True, hi_open=True)
            elif "fraction" in wt:
                fail(join(where, "fraction"), "only valid with resample = \"subsample\"")

    @staticmethod
    def check_row_ops(mutations: list, row_keys: tuple, where: str) -> None:
        ops = needs_row_keys(mutations)
        if ops and not row_keys:
            fail(where, f"row operation(s) {', '.join(sorted(set(ops)))} need row-aligned keys: every CSV column, or the "
                        "keys listed in `[data] rows`")

    # -- criteria, controls, premises, invariances ---------------------------

    def tolerances(self, value: Any, where: str) -> dict:
        if not isinstance(value, dict):
            fail(where, "must be a table of name = [value, scale]")
        out = {}
        for name, decl in value.items():
            w = join(where, name)
            if not (isinstance(decl, list) and len(decl) == 2 and all(is_number(v) for v in decl)):
                fail(w, "must be [value, scale] (two numbers)")
            out[name] = (decl[0], decl[1])
        return out

    def criteria(self, items: Any) -> list:
        if not isinstance(items, list):
            fail("criteria", "must be an array of tables ([[criteria]])")
        out = []
        for i, ct in enumerate(items):
            where = f"criteria[{i}]"
            if not isinstance(ct, dict):
                fail(where, "must be a table")
            kinds = [k for k in ("pattern", "command", "python") if k in ct]
            if len(kinds) != 1:
                fail(where, "needs exactly one of `pattern`, `command` and `python`")
            kind = kinds[0]
            spec = CriterionSpec(id=get_str(ct, "id", where), kind=kind, origin=self.origin(ct, where))
            if "regime" in ct:
                spec.regime = get_str(ct, "regime", where)
            if "control_waiver" in ct:
                spec.control_waiver = get_str(ct, "control_waiver", where)
            if "tolerances" in ct:
                spec.tolerances = self.tolerances(ct["tolerances"], join(where, "tolerances"))
            if "components" in ct:
                if kind == "pattern":
                    fail(join(where, "components"), "only valid for `command` and `python` criteria")
                spec.components = get_str_list(ct, "components", where, non_empty=True)
            if kind == "pattern":
                table = {k: v for k, v in ct.items() if k not in CRITERION_KEYS}
                spec.pattern = Pattern(table, where)
            elif kind == "python":
                check_keys(ct, where, ["id", "python"], CRITERION_KEYS - {"id"})
                spec.ref = self.python_ref(ct["python"], join(where, "python"))
            else:
                check_keys(ct, where, ["id", "command"], CRITERION_KEYS - {"id"})
                argv = get_str_list(ct, "command", where, required=True, non_empty=True)
                if not argv[0]:
                    fail(join(where, "command"), "the first element (the executable) must not be empty")
                spec.argv = argv
            out.append(spec)
        return out

    def controls(self, items: Any, worlds: dict, plus_rows: tuple) -> list:
        if not isinstance(items, list):
            fail("controls", "must be an array of tables ([[controls]])")
        out = []
        for i, ct in enumerate(items):
            where = f"controls[{i}]"
            check_keys(ct, where, ["id", "criteria"], ["mutations", "world", "python", "origin"])
            kinds = [k for k in ("mutations", "world", "python") if k in ct]
            if len(kinds) != 1:
                fail(where, "needs exactly one of `mutations`, `world` and `python`")
            spec = ControlSpec(id=get_str(ct, "id", where), criteria=get_str_list(ct, "criteria", where, required=True),
                               origin=self.origin(ct, where))
            if kinds[0] == "mutations":
                spec.mutations = validate_mutations(ct["mutations"], join(where, "mutations"))
                self.check_row_ops(spec.mutations, plus_rows, join(where, "mutations"))
            elif kinds[0] == "world":
                spec.world = get_str(ct, "world", where)
                if spec.world not in worlds:
                    fail(join(where, "world"), f"unknown world {spec.world!r}")
            else:
                spec.ref = self.python_ref(ct["python"], join(where, "python"))
            out.append(spec)
        return out

    def premises(self, items: Any, plus_rows: tuple) -> list:
        if not isinstance(items, list):
            fail("premises", "must be an array of tables ([[premises]])")
        out = []
        for i, pt in enumerate(items):
            where = f"premises[{i}]"
            check_keys(pt, where, ["id", "role", "criteria"], ["mutations", "python", "magnitude", "origin"])
            if ("mutations" in pt) == ("python" in pt):
                fail(where, "needs exactly one of `mutations` and `python`")
            spec = PremiseSpec(id=get_str(pt, "id", where), role=get_str(pt, "role", where),
                               criteria=get_str_list(pt, "criteria", where, required=True), origin=self.origin(pt, where))
            if "magnitude" in pt:
                mag = pt["magnitude"]
                if not (isinstance(mag, list) and len(mag) == 2 and all(is_number(v) for v in mag)):
                    fail(join(where, "magnitude"), "must be [value, scale] (two numbers)")
                spec.magnitude = (mag[0], mag[1])
            if "mutations" in pt:
                spec.mutations = validate_mutations(pt["mutations"], join(where, "mutations"))
                self.check_row_ops(spec.mutations, plus_rows, join(where, "mutations"))
            else:
                spec.ref = self.python_ref(pt["python"], join(where, "python"))
            out.append(spec)
        return out

    def invariances(self, items: Any, plus_rows: tuple, minus_rows: tuple) -> list:
        if not isinstance(items, list):
            fail("invariances", "must be an array of tables ([[invariances]])")
        out = []
        for i, it in enumerate(items):
            where = f"invariances[{i}]"
            check_keys(it, where, ["id", "criteria", "mutations", "reason"], ["origin"])
            reason = get_str(it, "reason", where)
            if not reason.strip():
                fail(join(where, "reason"), "must be a non-empty text")
            spec = InvarianceSpec(
                id=get_str(it, "id", where), criteria=get_str_list(it, "criteria", where, required=True),
                mutations=validate_mutations(it["mutations"], join(where, "mutations")), reason=reason,
                origin=self.origin(it, where),
            )
            # K8 transforms samples of the plus and the minus world, so both must have the row-aligned keys
            self.check_row_ops(spec.mutations, plus_rows, join(where, "mutations") + " (plus world)")
            self.check_row_ops(spec.mutations, minus_rows, join(where, "mutations") + " (minus world)")
            out.append(spec)
        return out


def _row_keys_of(world: WorldSpec, worlds: dict) -> tuple:
    """Row-aligned keys: every CSV column; otherwise the keys of ``[data] rows``; a derived world inherits."""
    while world.source == "derive":
        world = worlds[world.parent]
    return world.row_keys


def parse_manifest(path: str, source: bytes) -> Manifest:
    """Parse and validate a manifest, read and hash its data files (before the guard is armed)."""
    parsed = _load_text(path, source)
    _scan(parsed, "")
    return _Parser(path, source).parse(parsed)


# --------------------------------------------------------------------------
# Compilation to 0.3 objects (under the armed guard)
# --------------------------------------------------------------------------

class _Loader:
    """Executes ``python`` reference files from their hashed bytes (like :func:`truth_gate.study.load_study`)."""

    def __init__(self, files: dict) -> None:
        self.files = files
        self.modules: dict = {}

    def module(self, path: str) -> types.ModuleType:
        if path not in self.modules:
            name = f"truth_gate_manifest_module_{len(self.modules)}"
            module = types.ModuleType(name)
            module.__file__ = path
            code = compile(self.files[path]["source"], path, "exec")
            previous = sys.modules.get(name)
            sys.modules[name] = module
            try:
                exec(code, module.__dict__)  # noqa: S102 - executing the referenced file is the purpose
            finally:
                if previous is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = previous
            self.modules[path] = module
        return self.modules[path]

    def function(self, ref: PyRef):
        fn = self.module(ref.path).__dict__.get(ref.function)
        if not callable(fn):
            raise StudyError(f"python reference {ref.declared!r}: no callable {ref.function!r} in the file")
        return fn


def build_study(manifest: Manifest, session: Any = None) -> Study:
    """Compile a validated manifest into a ``Study``.  Call under the armed guard (spec section 1.2, step 2).

    ``session`` is the :class:`~truth_gate.external.ExternalSession` of the run (started before the guard); it supplies
    the functions of ``command`` criteria."""
    loader = _Loader(manifest.python_files)
    budget = Budget(**manifest.budget)
    targets = Targets(**manifest.targets)
    det, seed = manifest.deterministic, budget.base_seed
    worlds: dict = {}

    def world(name: str) -> World:
        if name in worlds:
            return worlds[name]
        spec = manifest.worlds[name]
        if spec.source == "file":
            table, resample, fraction = spec.table, spec.resample, spec.fraction

            def generate(rng, table=table, resample=resample, fraction=fraction):
                return sample_table(table, rng, resample, fraction)

            built = World(generate, None, spec.change)
        elif spec.source == "python":
            built = World(loader.function(spec.ref), None, spec.change)
        else:
            parent = world(spec.parent)
            mutate = MutationSet(f"world:{name}", spec.mutations, spec.row_keys, det, seed)

            def generate(rng, parent=parent, mutate=mutate):
                return mutate(parent.generate(rng), rng)

            built = World(generate, spec.parent, spec.change)
        worlds[name] = built
        return built

    for name in manifest.worlds:
        world(name)
    criteria = []
    for c in manifest.criteria:
        if c.kind == "pattern":
            fn = c.pattern.fn
        elif c.kind == "command":
            if session is None:
                raise StudyError(f"criterion {c.id!r} is a command criterion, but no external session was started")
            fn = session.criterion(c.id, c.argv)
        else:
            fn = loader.function(c.ref)
        criteria.append(Criterion(c.id, fn, c.regime, c.components, dict(c.tolerances), c.control_waiver))
    controls = []
    for c in manifest.controls:
        if c.mutations is not None:
            transform = MutationSet(f"control:{c.id}", c.mutations, manifest.plus_rows, det, seed)
            controls.append(Control(c.id, c.criteria, transform=transform))
        elif c.world is not None:
            controls.append(Control(c.id, c.criteria, world=world(c.world)))
        else:
            controls.append(Control(c.id, c.criteria, transform=loader.function(c.ref)))
    premises = []
    for p in manifest.premises:
        if p.mutations is not None:
            mutate = MutationSet(f"premise:{p.id}", p.mutations, manifest.plus_rows, det, seed)
        else:
            mutate = loader.function(p.ref)
        premises.append(Premise(p.id, mutate, p.role, p.criteria, p.magnitude))
    return Study(
        name=manifest.name, criteria=criteria, worlds=worlds, premises=premises, controls=controls,
        regimes=manifest.regimes, deterministic=det, budget=budget, targets=targets,
        allow_paths=manifest.allow_paths, relational=manifest.relational,
    )


def compiled_invariances(manifest: Manifest, study: Study) -> list:
    """The invariances of the K8 pass: the declared ones, then the built-in ``permute_rows`` (spec section 7).

    ``rows_exchangeable = true`` adds the built-in invariance for every criterion; it cannot be removed.  Call under
    the armed guard, after :func:`build_study`: a problem (unknown or repeated criterion id, repeated invariance id) is
    a ``StudyError``, like the same problems of controls and premises.
    """
    row_keys = {"plus": manifest.worlds["plus"].row_keys, "minus": manifest.worlds["minus"].row_keys}
    out = [Invariance(i.id, tuple(i.criteria), i.mutations, row_keys) for i in manifest.invariances]
    if manifest.rows_exchangeable:
        out.append(Invariance(BUILTIN_ID, tuple(c.id for c in study.criteria), [{"op": "permute_rows"}], row_keys,
                              builtin=True))
    validate_invariances(study, out)
    return out


def compiled_patterns(manifest: Manifest) -> dict:
    """Criterion id -> compiled pattern, for the ``pattern_stats`` pass."""
    return {c.id: c.pattern for c in manifest.criteria if c.kind == "pattern"}

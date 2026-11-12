"""``truth-gate suggest DATA.csv``: a starter manifest from one dataset (spec 0.6, section 8).

The output is text.  Nothing here runs a study.  What it writes:

* the warning that DATA must be a realistic synthetic or pilot dataset, **not the real study data** (printed by the
  CLI and written as a comment at the top of the manifest);
* ``[data]`` with the inferred types and the given roles;
* ``plus`` as a bootstrap of DATA with ``provenance = "TODO"`` (a validation error until it is replaced);
* a ``minus`` world: ``null_effect`` with ``--group``, ``--outcome`` and ``--reference``, otherwise one joint
  ``shuffle`` with ``columns = [...]`` of all ``--effect`` columns (revision R-22); the other candidates as comments;
* controls: ``shuffle`` of the group (else the outcome) column, ``sign_flip`` of the effect columns;
* ``rows_exchangeable = true`` only with ``--exchangeable``;
* **no active criterion**: every pattern as a commented template with the column names filled in.

Every generated declaration carries ``origin = "suggested"``, which caps every component at WEAK
(``SUGGESTED_UNREVIEWED``) until the key is deleted.
"""

from __future__ import annotations

import json
import re
from typing import Optional

import numpy as np

from .common import ManifestError
from .data_io import parse_csv

WARNING_LINES = (
    "WARNING: the data file must be a realistic synthetic or pilot dataset, NOT the real study data.",
    "The gate never sees the real data or the real result, and a plus world built from the real data makes the",
    "plus and minus checks circular. You must say where the file comes from (provenance) before the gate will run.",
)
_BARE_KEY = re.compile(r"^[A-Za-z0-9_-]+$")


class SuggestError(ManifestError):
    """A problem with the arguments or the data file (CLI exit code 4)."""


def _q(text: str) -> str:
    """A TOML basic string."""
    return json.dumps(text, ensure_ascii=False)


def _key(name: str) -> str:
    return name if _BARE_KEY.match(name) else _q(name)


def _toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return _q(str(value))


def infer_types(data: dict, group: Optional[str]) -> dict:
    """Column name -> ``float`` / ``bool`` / ``str`` as the CSV reader detects them; the group column becomes ``int``
    when it holds integers only (a float group could not be matched against a reference value)."""
    types = {}
    for name, arr in data.items():
        kind = arr.dtype.kind
        types[name] = {"f": "float", "b": "bool", "U": "str"}[kind]
    if group is not None and types[group] == "float":
        col = data[group]
        if np.all(np.isfinite(col)) and np.all(col == np.round(col)):
            types[group] = "int"
        else:
            raise SuggestError(f"the group column {group!r} must hold strings, bools or integers")
    return types


def _reference_value(text: str, ctype: str, column: np.ndarray, group: str):
    """The ``--reference`` text as a value of the group column's type; it must occur in the column."""
    if ctype == "str":
        value = text
        present = bool(np.any(column == value))
    elif ctype == "bool":
        if text.lower() not in ("true", "false"):
            raise SuggestError(f"--reference must be true or false for the bool column {group!r}")
        value = text.lower() == "true"
        present = bool(np.any(column == value))
    else:
        try:
            value = int(text)
        except ValueError:
            raise SuggestError(f"--reference must be an integer for the integer column {group!r}") from None
        present = bool(np.any(column == value))
    if not present:
        raise SuggestError(f"the reference value {text!r} does not occur in the group column {group!r}")
    return value


def _other_value(column: np.ndarray, ctype: str, reference):
    """A group value other than the reference (the first one in the data), or ``None``."""
    for value in column:
        item = value.item() if hasattr(value, "item") else value
        if item != reference:
            return item
    return None


def suggest_manifest(csv_bytes: bytes, data_ref: str, *, outcome: Optional[str] = None, group: Optional[str] = None,
                     reference: Optional[str] = None, effects: Optional[list] = None,
                     exchangeable: bool = False) -> str:
    """The text of the starter manifest.  ``data_ref`` is the path of DATA as written into the manifest.

    Raises :class:`SuggestError` for a problem with the arguments or the file (exit 4, nothing is written).
    """
    effects = list(effects or [])
    if (group is None) != (reference is None):
        raise SuggestError("--group and --reference go together (null_effect needs both)")
    if group is not None and outcome is None:
        raise SuggestError("--group needs --outcome (null_effect replaces the outcomes of the non-reference rows)")
    if len(set(effects)) != len(effects):
        raise SuggestError("--effect lists a column twice")
    if group is None and not effects:
        raise SuggestError("a minus world needs a candidate: give --group, --outcome and --reference, or --effect COL ...")
    table = parse_csv(csv_bytes, "DATA", {}, ",")  # a ManifestError (exit 4) for a bad file
    data = table.data
    given = {"--outcome": outcome, "--group": group}
    for flag, column in list(given.items()) + [("--effect", c) for c in effects]:
        if column is not None and column not in data:
            raise SuggestError(f"{flag} {column!r} is not a column of the data file")
    roles: dict = {}
    for role, columns in (("outcome", [outcome] if outcome else []), ("group", [group] if group else []),
                          ("effect", effects)):
        for column in columns:
            if column in roles:
                raise SuggestError(f"the column {column!r} is given two roles ({roles[column]} and {role})")
            roles[column] = role
    types = infer_types(data, group)
    for column in effects:
        if types[column] not in ("float", "int"):
            raise SuggestError(f"the effect column {column!r} must be numeric (sign_flip multiplies by -1)")
    ref_value = _reference_value(reference, types[group], data[group], group) if group is not None else None

    lines: list = []
    add = lines.append
    for text in ("truth-gate suggest: a STARTING POINT, not a pre-registration.",) + WARNING_LINES:
        add("# " + text)
    add("#")
    add('# Every declaration below carries origin = "suggested". While any declaration carries it, every component is')
    add("# capped at WEAK (SUGGESTED_UNREVIEWED) and the GitHub Action fails. Review each one against your theory, then")
    add("# delete its origin key. There is no active criterion: write one (templates at the end), then run")
    add("# `truth-gate check`.")
    add("")
    add("[study]")
    add('name = "TODO: state the claim this study tests"')
    add("")
    add("[data]")
    if exchangeable:
        add("rows_exchangeable = true       # rows are i.i.d. units, so their order must not matter (adds a K8 check)")
    else:
        add("# rows_exchangeable = true     # uncomment if the rows are i.i.d. units (adds a K8 check); default false")
    add("[data.columns]")
    for name, ctype in types.items():
        role = roles.get(name)
        add(f"{_key(name)} = {{ type = {_q(ctype)}" + (f", role = {_q(role)}" if role else "") + " }")
    add("")
    add("[worlds.plus]")
    add(f"file = {_q(data_ref)}")
    add('provenance = "TODO"             # where this file comes from; the gate refuses to run while this says TODO')
    add('resample = "bootstrap"')
    add('origin = "suggested"')
    add("")

    add("[worlds.minus]")
    add('derive = "plus"')
    # R-22: one joint shuffle of all effect columns (protocol rule 8: one change at a time); it breaks their relation
    # to the other columns and keeps their relation to each other.
    joint_shuffle = '{ op = "shuffle", columns = [' + ", ".join(_q(c) for c in effects) + "] }" if effects else ""
    candidates: list = []
    if group is not None:
        null_effect = (f'{{ op = "null_effect", outcome = {_q(outcome)}, group = {_q(group)}, '
                       f"reference = {_toml_value(ref_value)} }}")
        add(f"change = {_q('no effect: the ' + outcome + ' of the rows outside ' + group + ' = ' + str(ref_value) + ' are drawn from the reference rows (suggested)')}")
        add(f"mutations = [ {null_effect} ]")
        if effects:
            candidates.append(f"joint shuffle of the effect columns: mutations = [ {joint_shuffle} ]")
    else:
        add(f"change = {_q('no effect: the effect column(s) are shuffled relative to every other column (suggested)')}")
        add(f"mutations = [ {joint_shuffle} ]")
        for c in effects:
            candidates.append(f'constant effect: {{ op = "constant", column = {_q(c)}, stat = "mean" }}')
        if outcome:
            candidates.append(f'shuffled outcome: {{ op = "shuffle", column = {_q(outcome)} }}')
    add('origin = "suggested"')
    for text in candidates:
        add("# alternative minus (replace `mutations`): " + text)
    add("")

    add("# Controls: the theory is broken, so the criterion must not hold. `criteria` is empty: list the criterion ids.")
    if group is not None or outcome is not None:
        target = group if group is not None else outcome
        label = "labels_shuffled" if group is not None else "outcome_shuffled"
        add("[[controls]]")
        add(f"id = {_q(label)}")
        add("criteria = []                  # TODO: the criterion ids this control applies to")
        add(f'mutations = [ {{ op = "shuffle", column = {_q(target)} }} ]')
        add('origin = "suggested"')
        add("")
        if group is not None and outcome is not None:
            add(f'# other candidate: {{ op = "shuffle", column = {_q(outcome)} }}')
            add("")
    if effects:
        add("[[controls]]")
        add('id = "effects_negated"')
        add("criteria = []                  # TODO: the criterion ids this control applies to")
        add("mutations = [ " + ", ".join(f'{{ op = "sign_flip", column = {_q(c)} }}' for c in effects) + " ]")
        add('origin = "suggested"')
        add("")

    add("# " + "-" * 76)
    add("# Criterion templates. None is active. Uncomment ONE, fill in the TODO values, and keep or delete the origin")
    add("# line (while it stays, the verdict is capped). Each template is a complete [[criteria]] table.")
    add("# " + "-" * 76)
    lines.extend(criterion_templates(data, types, outcome, group, ref_value, effects))
    return "\n".join(lines) + "\n"


def _first(types: dict, wanted: tuple, skip: tuple = ()) -> Optional[str]:
    for name, ctype in types.items():
        if ctype in wanted and name not in skip:
            return name
    return None


def criterion_templates(data: dict, types: dict, outcome: Optional[str], group: Optional[str], ref_value,
                        effects: list) -> list:
    """Every pattern of spec section 4 as a commented ``[[criteria]]`` template, column names filled in."""
    y = outcome or _first(types, ("float",)) or "TODO_column"
    x = effects[0] if effects else (_first(types, ("float", "int"), (y,)) or y)
    where_a = where_b = None
    if group is not None:
        gtype = types[group]
        other = _other_value(data[group], gtype, ref_value)
        if gtype == "int":
            where_a = f"{{ column = {_q(group)}, op = \">\", value = {ref_value} }}"
            where_b = f"{{ column = {_q(group)}, op = \"<=\", value = {ref_value} }}"
        else:
            where_a = f"{{ column = {_q(group)}, equals = {_toml_value(other if other is not None else 'TODO')} }}"
            where_b = f"{{ column = {_q(group)}, equals = {_toml_value(ref_value)} }}"
    leaf_threshold = f'{{ pattern = "threshold", x = {_q(y)}, stat = "mean", op = ">=", value = 0.0 }}'
    leaf_spread = f'{{ pattern = "threshold", x = {_q(y)}, stat = "std", op = "<=", value = 1.0 }}'

    def block(cid: str, body: list) -> list:
        out = ["#", "# [[criteria]]", f"# id = {_q(cid)}", '# origin = "suggested"']
        out.extend("# " + line for line in body)
        return out

    diff = [f"a = {_q(y)}"]
    if where_a:
        diff.append(f"a_where = {where_a}")
    diff.append(f"b = {_q(y)}")
    if where_b:
        diff.append(f"b_where = {where_b}")
    ratio = [f"a = {_q(y)}"] + ([f"a_where = {where_a}"] if where_a else []) + [f"b = {_q(y)}"] + (
        [f"b_where = {where_b}"] if where_b else [])
    within = [f"a = {_q(y)}"] + ([f"a_where = {where_a}"] if where_a else []) + [f"b = {_q(y)}"] + (
        [f"b_where = {where_b}"] if where_b else [])
    out: list = []
    out += block("C_threshold", ['pattern = "threshold"', f"x = {_q(y)}", 'stat = "mean"', 'op = ">="',
                                 "value = 0.0                  # TODO: the threshold of your claim"])
    out += block("C_difference", ['pattern = "difference"'] + diff + [
        'stat = "mean"', 'op = ">="', "value = 0.5                  # TODO: the smallest difference your claim needs"])
    out += block("C_ratio_band", ['pattern = "ratio_band"'] + ratio + [
        'stat = "mean"', "lo = 0.5                     # TODO", "hi = 2.0                     # TODO"])
    out += block("C_within", ['pattern = "within"'] + within + [
        'mode = "stat"', 'stat = "mean"', "tol = 0.1                    # TODO: the tolerance (above the noise ceiling)"])
    out += block("C_rate", ['pattern = "rate"', f'condition = {{ column = {_q(y)}, op = ">", value = 0.0 }}',
                            'op = ">="', "value = 0.5                  # TODO: the required fraction of rows"])
    out += block("C_ci_excludes", ['pattern = "ci_excludes"', f"x = {_q(y)}", 'stat = "mean"', "level = 0.95",
                                   'side = "above"', "value = 0.0                  # TODO: the value the interval must clear"])
    out += block("C_largest_true", [
        'pattern = "largest_true"', "grid = [1.0, 2.0, 3.0]    # TODO: a literal list, matched by position to y",
        f"y = {_q(y)}", 'op = ">="', "threshold = 0.5             # TODO",
        "compare_to = { value = 2.0 }   # TODO: a literal grid value, or { y = ..., op = ..., threshold = ... }",
        'cmp = "=="'])
    out += block("C_monotone", ['pattern = "monotone"', f"x = {_q(x)}", f"y = {_q(y)}", 'direction = "increasing"',
                                "strict = false", "tol = 0"])
    out += block("C_all_of", ['pattern = "all_of"', "of = [", f"  {leaf_threshold},", f"  {leaf_spread},", "]"])
    out += block("C_any_of", ['pattern = "any_of"', "of = [", f"  {leaf_threshold},", f"  {leaf_spread},", "]"])
    return out

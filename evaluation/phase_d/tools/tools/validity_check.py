"""Phase D validity check (PREREG_PHASE_D sections 2.2 to 2.4; TOOLS_SPEC_D section 3; TOOLS_SPEC_D_round2 item 2).

For one case folder it assembles ``faulty_R`` and ``fixed_R`` (``reference.py`` plus the two bodies), loads them, and
runs the mechanical checks of section 2.2, V1, V2 and the timing check.  Every sample comes from
``stream_rng(seed, "validity:<stream>", i)`` (streams ``plus``, ``minus``, ``noise``); the structure statistic uses
``structure:<world>`` (``structure_stat.py``) and the timing check ``timing:plus``.  The gate uses none of these names, and
the default seed 20261117 is not the gate's base seed.  Each sample is generated once per stream and reused for both
twins.  Nothing here runs the gate; the criteria are evaluated by the gate's own ``checks.evaluate_detailed`` on samples
(the leak guard is not armed).

Steps
-----
1. Assemble and load both twins (unique module names).
2. Mechanical checks.  (a) ``structure_stat`` on 200 ``plus`` and 200 ``minus`` samples: each mean within
   ``|mean - note_value| <= 0.2 * |note_value - null_value|`` (R2-14; no special case at 0, so a note value equal to the
   null value has a zero band), and |mean_plus - mean_minus| <= 3 sqrt(sd_p^2/200 + sd_m^2/200).  With ``set_by_brief``,
   (a) only needs the statistic to be computable.  With ``--no-structure`` (R2-7; accepted only when
   ``PRIVATE.json["structure_statistic"]`` is null) (a) is skipped: ``"structure": "not used (decoy)"``, ``mech_a`` and
   ``structure_computable`` are null, and ``valid`` does not require them.  (b) the gate's minus analysis
   (``truth_gate.minus.analyse``, called as ``truth_gate/checks.py`` ``_minus_analysis`` calls it, lines 691-703) on the
   fixed study: the paired ``plus`` and ``minus`` samples at index 0 differ in at least one key that the fixed criterion
   reads.
3. V1 on ``samples`` ``minus`` samples: passes when faulty_holds/samples >= 0.25 and the one-sided Fisher exact p
   (faulty > fixed) < 0.01.  A failure is V1a when faulty_holds/samples < kstar/200, where kstar is the smallest k of 200
   with ``wilson_lower(k, 200, bonferroni_a(alpha_family, m)) > size`` (m = ``count_comparisons`` of the faulty study,
   alpha_family and size from its targets); every other failure is V1b.  A failure caused by an error has no label.
4. V2 for the fixed criterion: holds in at most 0.065 of ``samples`` ``minus`` samples, at most 0.065 of ``samples``
   noise-probe samples, at least 0.70 of ``samples`` ``plus`` samples.  A noise-probe sample is
   ``probes.noise_probe(copy_data(plus sample i), stream_rng(seed, "validity:noise", i))`` (``checks.py`` lines 450-451).
5. ``None`` counts as not-holds (the gate's UNDEFINED).  An exception, a bad return type or a sample that cannot be
   generated is recorded and makes the check that needs it fail with the reason "error".
6. Timing (R2-19).  t is the mean time of the fixed criterion (``evaluate_detailed``, outcomes not recorded) and g the mean
   time of the ``plus`` generation, over the same 20 reference ``plus`` samples ``stream_rng(seed, "timing:plus", i)``.  S is
   the gate's stream count for the fixed reference study, ``len(build_plan(study))`` (= worlds + controls + premises +
   relational pairs + 2).  The estimate is ``2 * 200 * (S + 1) * (t + g)`` seconds; ``timing_ok`` is ``estimate <= 1800``
   and is part of ``valid``.  (The estimate depends on the machine's clock; it is the only field that is not
   reproducible.)
7. Errors (R2-11).  An exception, a bad return or a failed generation sets ``error_in`` to the first stage, in the order
   "structure", "mech", "V1", "V2", "timing", that had one, with ``error_text`` (its first message) and ``error_stages``
   (stage -> messages); ``valid`` is false.  A case that cannot be assembled or loaded has ``reasons["setup"]`` and no
   ``error_in``.

Validity runs and dev runs (R2-25).  Only ``--samples 1000 --seed 20261117`` is a validity run.  Any other value requires
``--dev``, which writes ``"dev": true`` to the result and to the log line, and is refused (exit 2) when ``--case`` points
into a folder named ``cases`` (a case folder: any component of its path is ``cases``, case-insensitive).

Output.  RESULT.json: ``samples``, ``seed``, ``dev``, ``m``, ``kstar``, ``alpha_family``, ``size``, ``counts`` (every count
and rate, the Fisher p), ``timing``, the booleans ``v1``, ``v2``, ``mech_a``, ``mech_b``, ``structure_computable``,
``timing_ok``, ``valid`` (all of them true or, for the two structure fields under ``--no-structure``, null), ``v1_label``
(V1a / V1b / null), ``structure``, ``error_in``, ``reasons`` (one string per check), ``details`` and ``errors``.  The log gets
one JSON line appended: case id, UTC time, SHA-256 of every input file and of this file (and of the tools it imports), seed,
samples, dev, result.  A case that cannot be assembled or loaded is logged with ``valid`` false.

Round 4 (R3-2, R3-3, R3-8; every changed line is marked ``D-R4-3``)
------------------------------------------------------------------
* **Per-arm timing** (``--arm reference|W0|W1``, default ``reference``).  With ``--arm W0`` or ``--arm W1`` the tool assembles
  ``fixed_body.py`` into ``skeletons/W0.py`` or ``skeletons/W1.py`` of the case folder and runs only the timing measurement
  of step 6 (stream ``timing:plus``, seed 20261117, 20 samples, outcomes not recorded; S is the stream count of that arm's
  study; ``estimate_s`` and ``timing_ok``).  No V1, V2 or structure check runs.  The log line has ``"mode": "timing_arm"``,
  the arm, and the SHA-256 of the skeleton and of the fixed body.  Exit code 0 if ``timing_ok``, 1 if not.
* **V1 rate on the error-free samples.**  When V1 has an error (an exception, a bad return or a failed generation on some
  samples), ``v1`` stays false with the reason "error" and ``v1_label`` stays null; in addition the faulty and fixed counts on
  the samples that neither twin failed on are recorded as ``v1_rate_on_error_free`` (``faulty_holds``, ``fixed_holds``,
  ``n``), with the label the V1 rule gives on them in ``v1_rate_label`` (V1a, V1b, or null when the rule would pass).
* **V1 final drop** (R3B-2, D-R5-2).  When the V1 stage errs, ``v1_error_share`` is the share of the ``samples`` ``minus``
  samples on which either twin erred, and ``v1_final_drop_label`` follows the draft's rule: it is the ``v1_rate_label`` (V1a
  or V1b) when ``v1_error_share <= 0.05``, and null in every other case.  When it is set the pair is dropped with that label
  and the error-repair row does not apply.  Without a V1 error both fields are null.
* **``--no-structure``** is accepted only when ``PRIVATE.json["class"]`` is ``B-1`` or ``B-6`` (the decoy classes) and its
  ``structure_statistic`` is null; anything else is a usage error (exit 2).
* **Direction check.**  The direction vocabulary of the code (``structure_stat.structure_stat``) is ``"greater"`` and
  ``"less"``: the share counts samples ``>=`` the half-way point for "greater" and ``<=`` for "less".  A statistic whose
  direction is neither, or whose direction contradicts the sign of ``note_value - null_value`` ("greater" with a note value
  below the null, "less" with a note value above it), is a usage error (exit 2).  A note value equal to the null value has no
  sign and is not refused (its band is zero, so ``mech_a`` fails).
* **Log location** (R3B-3, D-R5-3).  The log has one fixed location, ``<parent of the case folder>/validity_log.jsonl``; the
  tool writes only there.  ``--log`` is optional and, if given, must be that path (anything else is a usage error, exit 2).
  ``check_validity_log_d.py`` reads ``<cases>/validity_log.jsonl``, which is the same file when the case folders are
  ``<cases>/<id>``.
* **Per-arm decisive marking** (R3B-4, D-R5-4).  In ``--arm`` mode the first non-dev run on a given (skeleton hash, fixed-body
  hash) is logged with ``"decisive": true`` (also in its ``result``), later non-dev runs on the same two hashes with
  ``"decisive": false``; ``--dev`` runs carry no ``decisive`` field.  ``check_validity_log_d.py --timing-arms`` reads it.
* **Decisive run.**  Before a standard run (``--samples 1000
  --seed 20261117``, not ``--dev``) the log is read: if a standard run with the same five input hashes (the five files of
  ``INPUT_FILES``) is already logged, the run still happens and is logged with ``"decisive": false``; otherwise with
  ``"decisive": true``.  ``--dev`` runs carry no ``decisive`` field (a ``timing_arm`` run has its own rule above).  Every log
  line has a ``mode`` (``"validity"`` or ``"timing_arm"``).
* **Hashes and decisive flag in the result** (D-R4-4).  A full run's ``RESULT.json`` (and the ``result`` of its log line) also
  holds ``input_sha256`` (the five input hashes) and, for a standard run, ``decisive``; ``check_validity_log_d.py`` reads them.
* **The ``--dev`` guard works by folder name**: a path with any component named ``cases`` (case-insensitive) refuses
  ``--dev``.  A case folder kept anywhere else is not protected.  ``--dev`` runs are logged to the same
  ``validity_log.jsonl``, with ``"dev": true``.

Usage:
    py validity_check.py --case DIR --package-root DIR --samples 1000 --seed 20261117 --out RESULT.json
           [--log <parent of DIR>/validity_log.jsonl] [--arm reference|W0|W1] [--no-structure] [--dev]
Exit code 0 if valid, 1 if not, 2 on a usage error (missing or malformed input, failed package root check, a flag used
where it is not allowed).
"""
import argparse
import datetime
import hashlib
import json
import math
import os
import sys
import time

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from assemble import AssembleError, assemble  # noqa: E402
from attributable import fisher_greater  # noqa: E402
from structure_stat import (PackageRootError, StatisticError, import_truth_gate, load_study_module,  # noqa: E402
                            structure_stat)

INPUT_FILES = ("brief.json", "PRIVATE.json", "faulty_body.py", "fixed_body.py", "reference.py")
V1_MIN_RATE = 0.25
V1_MAX_P = 0.01
V2_MAX_MINUS = 0.065
V2_MAX_NOISE = 0.065
V2_MIN_PLUS = 0.70
STRUCTURE_SAMPLES = 200
KSTAR_N = 200
REL_TOL = 0.20  # band: |mean - note_value| <= REL_TOL * |note_value - null_value| (R2-14)
TIMING_SAMPLES = 20
TIMING_LIMIT_S = 1800.0  # 30 minutes (R2-19)
VALIDITY_SAMPLES = 1000
VALIDITY_SEED = 20261117
STRUCTURE_NOT_USED = "not used (decoy)"
LOG_NAME = "validity_log.jsonl"  # D-R4-3
DECOY_CLASSES = ("B-1", "B-6")  # D-R4-3
DIRECTIONS = ("greater", "less")  # D-R4-3: the vocabulary of structure_stat.structure_stat
ARMS = {"reference": "reference.py", "W0": os.path.join("skeletons", "W0.py"), "W1": os.path.join("skeletons", "W1.py")}  # D-R4-3


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _generate(fn, rng):
    """``(data, error_name)`` as ``truth_gate/checks.py`` ``_call`` (lines 422-427)."""
    from truth_gate.sampling import validate_data
    try:
        return validate_data(fn(rng)), None
    except Exception as exc:
        return None, type(exc).__name__


def _gen_stream(world, stream, seed, samples):
    """``samples`` samples of ``world`` from ``stream_rng(seed, "validity:<stream>", i)``: list of (data, error)."""
    from truth_gate.sampling import stream_rng
    return [_generate(world.generate, stream_rng(seed, f"validity:{stream}", i)) for i in range(samples)]


def _evaluate(criterion, samples_list, errors, label):
    """Holds count of ``criterion`` on a list of (data, error); errors are appended to ``errors``."""
    from truth_gate.checks import HOLDS, Sample, evaluate_detailed
    holds = 0
    n_err = 0
    for i, (data, gen_err) in enumerate(samples_list):
        if data is None:
            errors.append(f"{label}[{i}]: sample not generated ({gen_err})")
            n_err += 1
            continue
        ev = evaluate_detailed(criterion, Sample(data, None))
        if ev.error is not None:
            errors.append(f"{label}[{i}]: criterion raised {ev.error}")
            n_err += 1
        elif ev.bad:
            errors.append(f"{label}[{i}]: criterion returned a value that is not bool or None")
            n_err += 1
        elif ev.outcomes[criterion.id] == HOLDS:
            holds += 1
    return holds, n_err


def kstar_of(alpha_family, m, size, n=KSTAR_N):
    """Smallest k of ``n`` with ``wilson_lower(k, n, bonferroni_a(alpha_family, m)) > size`` (None if there is none)."""
    from truth_gate.stats import bonferroni_a, wilson_lower
    a = bonferroni_a(alpha_family, m)
    for k in range(n + 1):
        if wilson_lower(k, n, a) > size:
            return k
    return None


def statistic_problem(spec):  # D-R4-3
    """Why a structure statistic is refused (a usage error), or ``None``: a direction outside ``DIRECTIONS``, or one that
    contradicts the sign of ``note_value - null_value``."""
    if spec["direction"] not in DIRECTIONS:
        return f"structure_statistic direction must be one of {list(DIRECTIONS)}, not {spec['direction']!r}"
    delta = float(spec["note_value"]) - float(spec["null_value"])
    if (spec["direction"] == "greater" and delta < 0) or (spec["direction"] == "less" and delta > 0):
        return (f"structure_statistic direction {spec['direction']!r} contradicts the sign of note_value - null_value "
                f"({spec['note_value']} - {spec['null_value']})")
    return None


def _outcomes(criterion, samples_list):  # D-R4-3
    """Per sample: True (holds), False (fails or UNDEFINED) or None (an error, a bad return or a failed generation)."""
    from truth_gate.checks import HOLDS, Sample, evaluate_detailed
    out = []
    for data, _gen_err in samples_list:
        if data is None:
            out.append(None)
            continue
        ev = evaluate_detailed(criterion, Sample(data, None))
        out.append(None if (ev.error is not None or ev.bad) else ev.outcomes[criterion.id] == HOLDS)
    return out


def v1_on_error_free(crit_f, crit_x, minus_s, kstar):  # D-R4-3
    """The V1 counts and the label the V1 rule gives on the samples that neither twin failed on (R3-3).  Returns
    ``(counts, label)``: label is "V1a", "V1b" or ``None`` (the rule would pass)."""
    of, ox = _outcomes(crit_f, minus_s), _outcomes(crit_x, minus_s)
    pairs = [(f, x) for f, x in zip(of, ox) if f is not None and x is not None]
    n, fh, xh = len(pairs), sum(f for f, _ in pairs), sum(x for _, x in pairs)
    counts = {"faulty_holds": fh, "fixed_holds": xh, "n": n}
    if n == 0:
        return counts, None
    if fh / n >= V1_MIN_RATE - 1e-12 and fisher_greater(fh, n, xh, n) < V1_MAX_P:
        return counts, None
    return counts, ("V1a" if kstar is None or fh / n < kstar / KSTAR_N else "V1b")


V1_MAX_ERROR_SHARE = 0.05  # D-R5-2


def v1_final_drop_label(rate_label, error_share):  # D-R5-2
    """The draft's final-drop rule for a V1 stage that erred: the V1a or V1b label of the rate on the error-free samples when
    at most 5% of the samples erred (``error_share <= 0.05``), otherwise ``None`` (the error-repair row applies)."""
    if rate_label in ("V1a", "V1b") and error_share is not None and error_share <= V1_MAX_ERROR_SHARE + 1e-12:
        return rate_label
    return None


def _mech_a(private, mod_plus_minus, seed, package_root):
    spec = private["structure_statistic"]
    res = {"plus": None, "minus": None}
    try:
        for w in ("plus", "minus"):
            res[w] = structure_stat(mod_plus_minus, private, w, STRUCTURE_SAMPLES, seed, package_root)
    except StatisticError as e:
        return False, False, f"structure statistic not computable: {e}", {"error": str(e)}
    if spec.get("set_by_brief"):
        return True, True, "set by the brief: the statistic is computable", res
    note, null = float(spec["note_value"]), float(spec["null_value"])
    tol = REL_TOL * abs(note - null)
    dev = {w: abs(res[w]["mean"] - note) for w in res}
    in_tol = {w: dev[w] <= tol for w in res}
    diff = abs(res["plus"]["mean"] - res["minus"]["mean"])
    se3 = 3.0 * math.sqrt(res["plus"]["sd"] ** 2 / STRUCTURE_SAMPLES + res["minus"]["sd"] ** 2 / STRUCTURE_SAMPLES)
    equal = diff <= se3
    ok = all(in_tol.values()) and equal
    details = {"plus": res["plus"], "minus": res["minus"], "note_value": note, "null_value": null, "tolerance": tol,
               "within_tolerance": in_tol, "abs_mean_difference": diff, "three_se": se3, "means_equal": equal}
    reason = "ok" if ok else (
        "mean outside tolerance in " + ",".join(w for w in in_tol if not in_tol[w]) if not all(in_tol.values())
        else "plus and minus means differ more than 3 se")
    return ok, True, reason, details


def _mech_b(fixed_study, seed):
    """The gate's minus analysis on the fixed study, mirrored from ``checks._minus_analysis`` (checks.py:691-703):
    the plus sample at i = 0, and a minus sample drawn with a generator seeded like the plus sample (paired)."""
    from truth_gate import minus as minus_check
    from truth_gate.sampling import stream_rng
    plus0, e1 = _generate(fixed_study.worlds["plus"].generate, stream_rng(seed, "validity:plus", 0))
    minus0, e2 = _generate(fixed_study.worlds["minus"].generate, stream_rng(seed, "validity:plus", 0))
    if plus0 is None or minus0 is None:
        return False, "error", {"error": f"plus: {e1}; minus: {e2}"}
    rec = minus_check.analyse(fixed_study.criteria, plus0, minus0, paired=True)[fixed_study.criteria[0].id]
    mc = rec["minus_check"]
    read, changed = mc["read_keys"], mc["changed_keys"]
    read_changed = sorted(changed) if read == minus_check.ALL_KEYS else sorted(set(read) & set(changed))
    ok = bool(read_changed) and not mc["identical"]
    reason = "ok" if ok else ("minus is identical to plus" if mc["identical"]
                              else "minus changes no key that the fixed criterion reads")
    return ok, reason, {"minus_check": mc, "changed_read_keys": read_changed, "flags": sorted(rec["flags"])}


def timing_estimate(S, t, g):
    """PB section 2's estimate in seconds: ``2 * 200 * (S + 1) * (t + g)``."""
    return 2 * 200 * (S + 1) * (t + g)


def measure_timing(study, seed, n=TIMING_SAMPLES):
    """t, g and the stream count S of the fixed reference study (R2-19).

    ``n`` reference ``plus`` samples ``stream_rng(seed, "timing:plus", i)``: g is the mean generation time, t the mean time
    of the fixed criterion (``evaluate_detailed``, which copies the data as the gate does); outcomes are not recorded.
    S is the gate's stream count ``len(build_plan(study))``.  Returns ``(timing dict, errors)``.
    """
    from truth_gate.checks import Sample, build_plan, evaluate_detailed
    from truth_gate.sampling import stream_rng, validate_data
    crit, gen = study.criteria[0], study.worlds["plus"].generate
    tg, tc, errors = [], [], []
    for i in range(n):
        t0 = time.perf_counter()
        try:
            data = validate_data(gen(stream_rng(seed, "timing:plus", i)))
        except Exception as exc:
            errors.append(f"timing sample {i}: not generated ({type(exc).__name__})")
            continue
        tg.append(time.perf_counter() - t0)
        t1 = time.perf_counter()
        ev = evaluate_detailed(crit, Sample(data, None))
        tc.append(time.perf_counter() - t1)
        if ev.error is not None:
            errors.append(f"timing sample {i}: criterion raised {ev.error}")
        elif ev.bad:
            errors.append(f"timing sample {i}: criterion returned a value that is not bool or None")
    S = len(build_plan(study))
    S_formula = len(study.worlds) + len(study.controls) + len(study.premises) + len(study.relational) + 2
    t = sum(tc) / len(tc) if tc else None
    g = sum(tg) / len(tg) if tg else None
    est = timing_estimate(S, t, g) if tc and tg else None
    return {"n": n, "t": t, "g": g, "S": S, "S_formula": S_formula, "estimate_s": est, "limit_s": TIMING_LIMIT_S}, errors


def run_checks(case_dir, package_root, samples, seed, no_structure=False, dev=False):
    """All checks of one case.  Returns ``result``; ``result["valid"]`` is the verdict.

    ``no_structure`` skips the structure statistic (only allowed when it is null in PRIVATE.json, else ``ValueError``);
    ``dev`` is recorded in the result.
    """
    tg = import_truth_gate(package_root)
    from truth_gate.checks import count_comparisons
    from truth_gate.probes import noise_probe
    from truth_gate.sampling import copy_data, stream_rng
    from truth_gate.study import Study
    del tg
    paths = {n: os.path.join(case_dir, n) for n in INPUT_FILES}
    texts = {}
    for n, p in paths.items():
        with open(p, encoding="utf-8") as f:
            texts[n] = f.read()
    brief = json.loads(texts["brief.json"])
    private = json.loads(texts["PRIVATE.json"])
    spec = private["structure_statistic"]
    if spec is None and not no_structure:
        raise ValueError("PRIVATE.json structure_statistic is null: pass --no-structure")
    if spec is not None and no_structure:
        raise ValueError("--no-structure is accepted only when PRIVATE.json structure_statistic is null")
    if no_structure and private.get("class") not in DECOY_CLASSES:  # D-R4-3
        raise ValueError(f"--no-structure is accepted only for the decoy classes {list(DECOY_CLASSES)}, "  # D-R4-3
                         f"not for class {private.get('class')!r}")  # D-R4-3
    if spec is not None:
        for k in ("code", "direction", "null_value", "note_value", "set_by_brief"):
            if k not in spec:
                raise KeyError(f"PRIVATE.json structure_statistic lacks {k!r}")
        problem = statistic_problem(spec)  # D-R4-3
        if problem:  # D-R4-3
            raise ValueError(problem)  # D-R4-3
    result = {"case": brief["id"], "samples": samples, "seed": seed, "dev": bool(dev), "valid": False, "errors": [],
              "reasons": {}, "details": {}, "counts": {}, "v1": False, "v1_label": None, "v2": False, "mech_a": False,
              "mech_b": False, "structure_computable": False, "structure": "used", "timing": None,
              "timing_ok": False, "m": None, "kstar": None, "mode": "validity",
              "v1_rate_on_error_free": None, "v1_rate_label": None, "v1_error_share": None,  # D-R5-2
              "v1_final_drop_label": None, "error_in": None, "error_text": None,
              "error_stages": {}}
    errors = result["errors"]
    stage_errors = result["error_stages"]

    def note_error(stage, text):
        stage_errors.setdefault(stage, []).append(text)

    def fail(reason, why):
        result["reasons"]["setup"] = f"{reason}: {why}"
        return result

    try:
        faulty_src = assemble(texts["reference.py"], texts["faulty_body.py"])
        fixed_src = assemble(texts["reference.py"], texts["fixed_body.py"])
    except AssembleError as e:
        return fail("assemble_error", str(e))
    try:
        mod_f = load_study_module(faulty_src, "faulty_R.py", "faulty")
        mod_x = load_study_module(fixed_src, "fixed_R.py", "fixed")
    except Exception as e:
        return fail("load_error", f"{type(e).__name__}: {e}")
    study_f, study_x = getattr(mod_f, "STUDY", None), getattr(mod_x, "STUDY", None)
    if not isinstance(study_f, Study) or not isinstance(study_x, Study):
        return fail("load_error", "an assembled file does not define a truth_gate Study as STUDY")
    crit_f, crit_x = study_f.criteria[0], study_x.criteria[0]

    # --- 2. mechanical checks
    if no_structure:
        result["structure"] = STRUCTURE_NOT_USED
        result["mech_a"], result["structure_computable"] = None, None
        result["reasons"]["mech_a"] = "skipped (--no-structure)"
    else:
        result["mech_a"], result["structure_computable"], result["reasons"]["mech_a"], result["details"]["mech_a"] = \
            _mech_a(private, mod_x, seed, package_root)
        if not result["structure_computable"]:
            note_error("structure", result["reasons"]["mech_a"])
    result["mech_b"], result["reasons"]["mech_b"], result["details"]["mech_b"] = _mech_b(study_x, seed)
    if result["reasons"]["mech_b"] == "error":
        note_error("mech", result["details"]["mech_b"]["error"])

    # --- samples, once per stream
    minus_s = _gen_stream(study_f.worlds["minus"], "minus", seed, samples)
    plus_s = _gen_stream(study_x.worlds["plus"], "plus", seed, samples)
    noise_s = []
    for i, (data, err) in enumerate(plus_s):
        if data is None:
            noise_s.append((None, err))
            continue
        noise_s.append(_generate_noise(noise_probe, copy_data, data, stream_rng(seed, "validity:noise", i)))

    # --- 3. V1
    m = count_comparisons(study_f)
    kstar = kstar_of(study_f.targets.alpha_family, m, study_f.targets.size)
    result["m"], result["kstar"] = m, kstar
    result["alpha_family"], result["size"] = study_f.targets.alpha_family, study_f.targets.size
    e_f, e_x = [], []
    fh, fe = _evaluate(crit_f, minus_s, e_f, "faulty on minus")
    xh, xe = _evaluate(crit_x, minus_s, e_x, "fixed on minus")
    errors.extend(e_f[:20] + e_x[:20])
    p1 = fisher_greater(fh, samples, xh, samples)
    rate_f, rate_x = fh / samples, xh / samples
    rate_ok, p_ok = rate_f >= V1_MIN_RATE - 1e-12, p1 < V1_MAX_P
    result["counts"]["v1"] = {"faulty_holds": fh, "fixed_holds": xh, "n": samples, "faulty_rate": rate_f,
                              "fixed_rate": rate_x, "fisher_p": p1, "errors_faulty": fe, "errors_fixed": xe}
    if fe or xe:
        result["v1"], result["reasons"]["v1"] = False, "error"
        for text in (e_f[:3] + e_x[:3]):
            note_error("V1", text)
        result["v1_rate_on_error_free"], result["v1_rate_label"] = v1_on_error_free(crit_f, crit_x, minus_s, kstar)  # D-R4-3
        result["v1_error_share"] = 1.0 - result["v1_rate_on_error_free"]["n"] / len(minus_s)  # D-R5-2: either twin erred
        result["v1_final_drop_label"] = v1_final_drop_label(result["v1_rate_label"], result["v1_error_share"])  # D-R5-2
    elif rate_ok and p_ok:
        result["v1"], result["reasons"]["v1"] = True, "ok"
    else:
        result["v1"] = False
        why = []
        if not rate_ok:
            why.append(f"faulty rate {rate_f:.4g} < {V1_MIN_RATE}")
        if not p_ok:
            why.append(f"Fisher p {p1:.3g} >= {V1_MAX_P}")
        result["reasons"]["v1"] = "; ".join(why)
        below_flag = kstar is None or rate_f < kstar / KSTAR_N
        result["v1_label"] = "V1a" if below_flag else "V1b"

    # --- 4. V2 (fixed criterion)
    e2 = []
    mh, me = xh, xe  # the fixed criterion on the same minus samples as in V1
    nh, ne = _evaluate(crit_x, noise_s, e2, "fixed on noise")
    ph, pe = _evaluate(crit_x, plus_s, e2, "fixed on plus")
    errors.extend(e2[:20])
    r_m, r_n, r_p = mh / samples, nh / samples, ph / samples
    ok_m, ok_n, ok_p = r_m <= V2_MAX_MINUS + 1e-12, r_n <= V2_MAX_NOISE + 1e-12, r_p >= V2_MIN_PLUS - 1e-12
    result["counts"]["v2"] = {
        "minus": {"holds": mh, "n": samples, "rate": r_m, "max": V2_MAX_MINUS, "ok": ok_m, "errors": me},
        "noise": {"holds": nh, "n": samples, "rate": r_n, "max": V2_MAX_NOISE, "ok": ok_n, "errors": ne},
        "plus": {"holds": ph, "n": samples, "rate": r_p, "min": V2_MIN_PLUS, "ok": ok_p, "errors": pe}}
    if me or ne or pe:
        result["v2"], result["reasons"]["v2"] = False, "error"
        for text in (e_x[:3] + e2[:3]):
            note_error("V2", text)
    else:
        result["v2"] = ok_m and ok_n and ok_p
        bad = [n for n, ok in (("minus", ok_m), ("noise", ok_n), ("plus", ok_p)) if not ok]
        result["reasons"]["v2"] = "ok" if not bad else "fixed criterion outside its bound on " + ",".join(bad)

    # --- 6. timing (R2-19)
    timing, t_errors = measure_timing(study_x, seed)
    result["timing"] = timing
    if t_errors or timing["estimate_s"] is None:
        result["timing_ok"] = False
        result["reasons"]["timing"] = "error"
        for text in t_errors[:3] or ["no timing sample could be measured"]:
            note_error("timing", text)
    else:
        result["timing_ok"] = timing["estimate_s"] <= TIMING_LIMIT_S
        result["reasons"]["timing"] = ("ok" if result["timing_ok"] else
                                       f"estimate {timing['estimate_s']:.0f} s > {TIMING_LIMIT_S:.0f} s")

    for stage in ("structure", "mech", "V1", "V2", "timing"):
        if stage in stage_errors:
            result["error_in"], result["error_text"] = stage, stage_errors[stage][0]
            break
    result["valid"] = bool(result["mech_b"] and result["v1"] and result["v2"] and result["timing_ok"]
                           and (no_structure or (result["mech_a"] and result["structure_computable"])))
    return result


def _generate_noise(noise_probe, copy_data, data, rng):
    try:
        return noise_probe(copy_data(data), rng), None
    except Exception as exc:
        return None, type(exc).__name__


def log_path_for(case_dir):  # D-R5-3
    """The one location of the validity log: ``<parent of the case folder>/validity_log.jsonl``."""
    return os.path.join(os.path.dirname(os.path.abspath(case_dir)), LOG_NAME)


def same_path(a, b):  # D-R5-3
    norm = lambda p: os.path.normcase(os.path.realpath(os.path.abspath(p)))  # noqa: E731
    return norm(a) == norm(b)


def timing_arm_logged(path, skeleton_sha, body_sha):  # D-R5-4
    """True if the log already holds a non-dev ``timing_arm`` run on this (skeleton hash, fixed-body hash)."""
    for e in read_log(path):
        h = e.get("sha256") or {}
        if (e.get("mode") == "timing_arm" and not e.get("dev") and h.get("skeleton") == skeleton_sha
                and h.get("fixed_body.py") == body_sha):
            return True
    return False


def is_standard_entry(entry):  # D-R4-3
    """A logged standard validity run: mode "validity" (or none), 1000 samples, seed 20261117, not ``--dev``."""
    return (entry.get("mode", "validity") == "validity" and entry.get("samples") == VALIDITY_SAMPLES
            and entry.get("seed") == VALIDITY_SEED and not entry.get("dev"))


def read_log(path):  # D-R4-3
    """The entries of a validity log (``[]`` if it does not exist).  A line that is not a JSON object is a ``ValueError``."""
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except ValueError as e:
                raise ValueError(f"{path} line {n} is not JSON: {e}") from e
            if not isinstance(entry, dict):
                raise ValueError(f"{path} line {n} is not a JSON object")
            out.append(entry)
    return out


def standard_run_logged(path, hashes5):  # D-R4-3
    """True if the log already holds a standard run whose five input hashes equal ``hashes5``."""
    return any(is_standard_entry(e) and {n: (e.get("sha256") or {}).get(n) for n in INPUT_FILES} == hashes5
               for e in read_log(path))


def run_timing_arm(case_dir, package_root, seed, arm, dev=False):  # D-R4-3
    """The timing measurement of the fixed body assembled into the case's W0 or W1 skeleton (and nothing else).

    Returns the result dict (``mode`` "timing_arm"); ``timing_ok`` is its verdict.  A skeleton that does not assemble or load
    gives ``timing_ok`` false and ``reasons["setup"]``.  The skeleton file must exist (``OSError`` otherwise).
    """
    import_truth_gate(package_root)
    from truth_gate.study import Study
    with open(os.path.join(case_dir, "brief.json"), encoding="utf-8") as f:
        case_id = json.load(f)["id"]
    with open(os.path.join(case_dir, ARMS[arm]), encoding="utf-8") as f:
        skeleton = f.read()
    with open(os.path.join(case_dir, "fixed_body.py"), encoding="utf-8") as f:
        body = f.read()
    result = {"case": case_id, "mode": "timing_arm", "arm": arm, "seed": seed, "dev": bool(dev), "timing": None,
              "estimate_s": None, "timing_ok": False, "reasons": {}, "errors": [], "error_in": None, "error_text": None,
              "error_stages": {}}
    try:
        src = assemble(skeleton, body)
        module = load_study_module(src, f"fixed_{arm}.py", "fixed")
    except AssembleError as e:
        result["reasons"]["setup"] = f"assemble_error: {e}"
        return result
    except Exception as e:
        result["reasons"]["setup"] = f"load_error: {type(e).__name__}: {e}"
        return result
    study = getattr(module, "STUDY", None)
    if not isinstance(study, Study):
        result["reasons"]["setup"] = "load_error: the assembled file does not define a truth_gate Study as STUDY"
        return result
    timing, t_errors = measure_timing(study, seed)
    result["timing"], result["estimate_s"] = timing, timing["estimate_s"]
    if t_errors or timing["estimate_s"] is None:
        result["reasons"]["timing"] = "error"
        result["error_in"], result["error_text"] = "timing", (t_errors or ["no timing sample could be measured"])[0]
        result["error_stages"]["timing"] = t_errors[:3] or [result["error_text"]]
    else:
        result["timing_ok"] = timing["estimate_s"] <= TIMING_LIMIT_S
        result["reasons"]["timing"] = ("ok" if result["timing_ok"] else
                                       f"estimate {timing['estimate_s']:.0f} s > {TIMING_LIMIT_S:.0f} s")
    return result


def main_timing_arm(a):  # D-R4-3
    """``--arm W0`` / ``--arm W1``: run the timing only, log it, print one line.  Returns the exit code."""
    rel = ARMS[a.arm]
    needed = [os.path.join(a.case, n) for n in ("brief.json", "fixed_body.py", rel)]
    missing = [p for p in needed if not os.path.isfile(p)]
    if missing:
        print(f"missing input file(s): {missing}", file=sys.stderr)
        return 2
    try:
        import_truth_gate(a.package_root)
    except PackageRootError as e:
        print(f"package root check failed: {e}", file=sys.stderr)
        return 2
    hashes = {"skeleton": sha256_file(os.path.join(a.case, rel)), "fixed_body.py": sha256_file(needed[1]),
              "tools/validity_check.py": sha256_file(os.path.abspath(__file__))}
    for sib in ("assemble.py", "structure_stat.py", "mech_check_bodies.py"):
        hashes[f"tools/{sib}"] = sha256_file(os.path.join(TOOLS_DIR, sib))
    decisive = None  # D-R5-4
    try:
        if not a.dev:  # D-R5-4: the first non-dev run on these two hashes decides
            decisive = not timing_arm_logged(a.log, hashes["skeleton"], hashes["fixed_body.py"])  # D-R5-4
        result = run_timing_arm(a.case, a.package_root, a.seed, a.arm, a.dev)
    except (KeyError, ValueError, TypeError) as e:
        print(f"malformed case input: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if decisive is not None:  # D-R5-4
        result["decisive"] = decisive  # D-R5-4
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, default=str)
    line = {"case": result["case"], "time_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": "timing_arm", "arm": a.arm, "sha256": hashes, "seed": a.seed, "samples": TIMING_SAMPLES,
            "dev": bool(a.dev), "result": result}
    if decisive is not None:  # D-R5-4
        line["decisive"] = decisive  # D-R5-4
    with open(a.log, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(line, sort_keys=True, default=str) + "\n")
    est = result["estimate_s"]
    print(f"{result['case']}/{a.arm}: timing {'OK' if result['timing_ok'] else 'NOT OK'}"
          + ("" if est is None else f" estimate {est:.1f} s") + (" [dev]" if a.dev else "")
          + ("" if decisive is None else (" [decisive]" if decisive else " [not decisive: logged before]")))  # D-R5-4
    return 0 if result["timing_ok"] else 1


def _log_line(case_dir, result, hashes, samples, seed, dev=False, no_structure=False, decisive=None):  # D-R4-3
    line = {
        "case": result.get("case"),
        "time_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": hashes,
        "seed": seed,
        "samples": samples,
        "dev": bool(dev),
        "no_structure": bool(no_structure),
        "mode": result.get("mode", "validity"),  # D-R4-3
        "result": result,
    }
    if decisive is not None:  # D-R4-3: only a standard run carries the field
        line["decisive"] = decisive
    return line


def in_cases_folder(path):
    """True if any component of the absolute ``path`` is a folder named ``cases`` (case-insensitive)."""
    parts = os.path.normcase(os.path.abspath(path)).replace("\\", "/").split("/")
    return "cases" in parts


def run_flag_problem(samples, seed, dev, case_dir):
    """The reason a combination of ``--samples``, ``--seed``, ``--dev`` and ``--case`` is refused, or ``None`` (R2-25)."""
    standard = samples == VALIDITY_SAMPLES and seed == VALIDITY_SEED
    if dev and in_cases_folder(case_dir):
        return "--dev is refused when --case points into a folder named 'cases' (a case folder)"
    if not standard and not dev:
        return (f"only --samples {VALIDITY_SAMPLES} --seed {VALIDITY_SEED} is a validity run; "
                "other values need --dev (a development run, never accepted on case folders)")
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validity checks V1 and V2 and the mechanical checks of one Phase D case.")
    ap.add_argument("--case", required=True)
    ap.add_argument("--package-root", required=True, metavar="DIR")
    ap.add_argument("--samples", type=int, default=VALIDITY_SAMPLES)
    ap.add_argument("--seed", type=int, default=VALIDITY_SEED)
    ap.add_argument("--log", help="optional; must be <parent of --case>/validity_log.jsonl, the only place the log is written")  # D-R5-3
    ap.add_argument("--out", required=True)
    ap.add_argument("--arm", choices=sorted(ARMS), default="reference",  # D-R4-3
                    help="reference (default): the full validity run; W0 or W1: only the timing of that arm's study")
    ap.add_argument("--no-structure", action="store_true",
                    help="skip the structure statistic; accepted only when PRIVATE.json structure_statistic is null")
    ap.add_argument("--dev", action="store_true",
                    help="development run: allows other --samples/--seed, is recorded, never accepted on case folders")
    a = ap.parse_args(argv)
    sys.dont_write_bytecode = True
    if a.samples < 1:
        print("--samples must be >= 1", file=sys.stderr)
        return 2
    problem = run_flag_problem(a.samples, a.seed, a.dev, a.case)
    if problem:
        print(problem, file=sys.stderr)
        return 2
    fixed_log = log_path_for(a.case)  # D-R5-3
    if a.log is not None and not same_path(a.log, fixed_log):  # D-R5-3
        print(f"the log has one location, {fixed_log}; --log {a.log} is not it", file=sys.stderr)  # D-R5-3
        return 2  # D-R5-3
    a.log = fixed_log  # D-R5-3
    if a.arm != "reference":  # D-R4-3
        if a.no_structure:  # D-R4-3
            print("--no-structure has no meaning with --arm W0 or W1 (no structure check runs)", file=sys.stderr)  # D-R4-3
            return 2  # D-R4-3
        return main_timing_arm(a)  # D-R4-3
    try:
        import_truth_gate(a.package_root)
    except PackageRootError as e:
        print(f"package root check failed: {e}", file=sys.stderr)
        return 2
    missing = [n for n in INPUT_FILES if not os.path.isfile(os.path.join(a.case, n))]
    if missing:
        print(f"missing input file(s) in {a.case}: {missing}", file=sys.stderr)
        return 2
    hashes = {n: sha256_file(os.path.join(a.case, n)) for n in INPUT_FILES}
    hashes["tools/validity_check.py"] = sha256_file(os.path.abspath(__file__))
    for sib in ("assemble.py", "structure_stat.py", "attributable.py", "mech_check_bodies.py", "check_skeletons_d.py"):  # D-R5-5
        hashes[f"tools/{sib}"] = sha256_file(os.path.join(TOOLS_DIR, sib))
    decisive = None  # D-R4-3
    try:
        if a.samples == VALIDITY_SAMPLES and a.seed == VALIDITY_SEED and not a.dev:  # D-R4-3: a standard run
            decisive = not standard_run_logged(a.log, {n: hashes[n] for n in INPUT_FILES})  # D-R4-3
        result = run_checks(a.case, a.package_root, a.samples, a.seed, no_structure=a.no_structure, dev=a.dev)
    except (KeyError, ValueError, TypeError) as e:
        print(f"malformed case input: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    result["input_sha256"] = {n: hashes[n] for n in INPUT_FILES}  # D-R4-4: check_validity_log_d.py compares these
    if decisive is not None:  # D-R4-4
        result["decisive"] = decisive  # D-R4-4
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, default=str)
    with open(a.log, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(_log_line(a.case, result, hashes, a.samples, a.seed, a.dev, a.no_structure, decisive),
                           sort_keys=True, default=str) + "\n")
    print(f"{result['case']}: {'VALID' if result['valid'] else 'NOT VALID'}  v1={result['v1']} ({result['v1_label']}) "
          f"v2={result['v2']} mech_a={result['mech_a']} mech_b={result['mech_b']} timing_ok={result['timing_ok']}"
          + (f" error_in={result['error_in']}" if result["error_in"] else "") + (" [dev]" if a.dev else "")
          + ("" if decisive is None else (" [decisive]" if decisive else " [not decisive: a standard run is already logged]")))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())

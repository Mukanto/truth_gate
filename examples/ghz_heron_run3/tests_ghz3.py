"""tests_ghz3.py -- offline unit tests of the GHZ run-3 study code (PREREG.md run 3, v3).

Run:  <venv python> tests_ghz3.py        (FakeKingston, toy targets and run 1/2 files read-only; no network, no account)
Nothing is written to this folder: temporary folders are used (the real manifest FREEZE_GHZ3.json is not needed or created).
"""
import contextlib
import copy
import datetime
import io
import json
import math
import os
import shutil
import tempfile
import time
import unittest

import numpy as np
from qiskit import qpy
from qiskit_ibm_runtime.fake_provider import FakeKingston

import ghz2_core as core
import ghz2_study
import ghz3_analyze
import ghz3_run
import ghz3_study_h4

HERE = os.path.dirname(os.path.abspath(__file__))
RUN2 = ghz3_run.RUN2_DIR


# ------------------------------------------------------------------------------------------------------------ helpers
def ideal_counts(n, family, shots=2000, loss=0.0):
    """Analytic noiseless counts of GHZ_n (family 'GHZ') or of its classical mixture twin ('MIX'), keys = data bitstrings."""
    out = {}
    other = int(round(shots * loss))
    pop = {"0" * n: (shots - other) // 2, "1" * n: shots - other - (shots - other) // 2}
    if other:
        pop["0" * (n - 1) + "1"] = other
    out[core.circuit_name(family, n, "POP")] = {"meas": pop}
    for j in range(2 * n + 2):
        phi = j * math.pi / (n + 1)
        p_even = 0.5 * (1 + (math.cos(n * phi) if family == "GHZ" else 0.0))
        ev = int(round(shots * p_even))
        counts = {}
        if ev:
            counts["0" * n] = ev
        if shots - ev:
            counts["0" * (n - 1) + "1"] = shots - ev
        out[core.circuit_name(family, n, "PAR", j)] = {"meas": counts}
    return out


def all_ideal_counts():
    out = {}
    for n in core.GRID:
        out.update(ideal_counts(n, "GHZ"))
    for n in core.MIX_NS:
        out.update(ideal_counts(n, "MIX"))
    return out


_KING = {}


def kingston():
    """Cached FakeKingston: backend, snapshot, hash, entries (368 transpiled circuits), model (M2, int keys), comps (str keys)."""
    if not _KING:
        b = FakeKingston()
        snap, h = core.snapshot_from_backend(b, utc="TEST")
        entries = core.build_all(snap, b.target)
        model = core.model_all(entries, b.target)
        _KING.update(backend=b, snap=snap, hash=h, entries=entries, model=model,
                     comps={str(n): model[n] for n in core.GRID})
    return _KING


_REAL_POWER = ghz3_run.compute_power
_POWER_CACHE = {}


def _cached_power(pred_new, *a, **kw):
    """ghz3_run.compute_power with a cache (the runner tests would otherwise repeat the same 4-second simulation)."""
    key = (tuple(float(x) for k in ("F_pred", "P_pred", "C_pred") for x in pred_new[k]), repr(a), repr(sorted(kw.items())))
    if key not in _POWER_CACHE:
        _POWER_CACHE[key] = _REAL_POWER(pred_new, *a, **kw)
    return copy.deepcopy(_POWER_CACHE[key])


def write_run2_dir(d, snap, comps, hash_=None):
    """A fake run-2 folder with run/<snapshot> and run/model.json (the files C-1 reads)."""
    os.makedirs(os.path.join(d, "run"))
    h = hash_ or core.snapshot_hash(snap)
    with open(os.path.join(d, ghz3_run.RUN2_SNAPSHOT_FILE), "w") as fh:
        json.dump({"sha256": h, "snapshot": snap}, fh)
    with open(os.path.join(d, ghz3_run.RUN2_MODEL_FILE), "w") as fh:
        json.dump({"snapshot_sha256": h, "components": comps}, fh)
    return d


class _FakeStatus:
    def __init__(self, pending, operational=True):
        self.pending_jobs, self.operational = pending, operational


class _FakeBackend:
    def __init__(self, name, nq, pending, ptype=None):
        self.name, self.num_qubits, self._p = name, nq, pending
        if ptype is not None:
            self.processor_type = ptype

    def status(self):
        return _FakeStatus(self._p)


class _RecoverJob:
    """What --recover reads from the service: status(), backend(), creation_date (a datetime) and inputs["pubs"]."""
    def __init__(self, backend="fake_kingston", created="now", n_pubs=368, status="DONE", error=None):
        self.backend_name, self.created, self.n_pubs, self._status, self.error = backend, created, n_pubs, status, error

    def status(self):
        if self.error:
            raise self.error
        return self._status

    def backend(self):
        class _B:
            pass
        b = _B()
        b.name = self.backend_name
        return b

    @property
    def creation_date(self):
        if self.created == "now":
            return datetime.datetime.now(datetime.timezone.utc)
        return self.created

    @property
    def inputs(self):
        return {"pubs": [None] * self.n_pubs}


class _FakeService:
    def __init__(self, backends, usage=None, job=None):
        self._b, self._usage, self._job = backends, usage, job

    def job(self, job_id):
        if self._job is None:
            raise RuntimeError("no job")
        return self._job

    def backends(self, **kw):
        return list(self._b)

    def usage(self):
        if isinstance(self._usage, Exception):
            raise self._usage
        return self._usage


class _Patch:
    """Context manager patching module attributes."""
    def __init__(self, obj, **kw):
        self.obj, self.kw, self.orig = obj, kw, {}

    def __enter__(self):
        for k, v in self.kw.items():
            self.orig[k] = getattr(self.obj, k)
            setattr(self.obj, k, v)

    def __exit__(self, *a):
        for k, v in self.orig.items():
            setattr(self.obj, k, v)


def _quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*a, **k)


def _captured(fn, *a, **k):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = fn(*a, **k)
        except SystemExit as exc:
            code = exc
    return code, out.getvalue(), err.getvalue()


def _rewrite_hash_power(run_dir, mutate):
    """Rewrite run/power_run3.json after ``mutate(dict)`` and put its new SHA-256 in job.json."""
    p = os.path.join(run_dir, "power_run3.json")
    with open(p) as fh:
        pw = json.load(fh)
    mutate(pw)
    with open(p, "w") as fh:
        json.dump(pw, fh)
    jp = os.path.join(run_dir, "job.json")
    with open(jp) as fh:
        job = json.load(fh)
    job["power_run3_sha256"] = core.sha256_file(p)
    with open(jp, "w") as fh:
        json.dump(job, fh)


# ------------------------------------------------------------------------------------------------------- code identity
class TestCodeIdentity(unittest.TestCase):
    def test_core_and_study_equal_run2_frozen_values(self):
        with open(os.path.join(RUN2, "FREEZE_GHZ2.json"), "r", encoding="utf-8") as fh:
            files = json.load(fh)["files"]
        for name in ("ghz2_core.py", "ghz2_study.py"):
            mine = os.path.join(HERE, name)
            self.assertEqual(core.sha256_file(mine), files[name], name)
            with open(mine, "rb") as a, open(os.path.join(RUN2, name), "rb") as b:
                self.assertEqual(a.read(), b.read(), name)                       # byte for byte
        self.assertEqual(set(ghz3_run.code_identity(HERE)), {"ghz2_core.py", "ghz2_study.py"})

    def test_mismatch_and_missing(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as r2:
            for name in ghz3_run.CODE_IDENTITY_FILES:
                with open(os.path.join(d, name), "w") as fh:
                    fh.write("x " + name)
            files = {n: core.sha256_file(os.path.join(d, n)) for n in ghz3_run.CODE_IDENTITY_FILES}
            with self.assertRaises(core.FreezeError):                              # run 2's manifest absent
                ghz3_run.code_identity(d, r2)
            with open(os.path.join(r2, "FREEZE_GHZ2.json"), "w") as fh:
                json.dump({"files": files}, fh)
            self.assertEqual(ghz3_run.code_identity(d, r2), files)
            with open(os.path.join(d, "ghz2_core.py"), "a") as fh:
                fh.write("changed")
            with self.assertRaises(core.FreezeError):
                ghz3_run.code_identity(d, r2)
            os.remove(os.path.join(d, "ghz2_study.py"))
            with self.assertRaises(core.FreezeError):
                ghz3_run.code_identity(d, r2)


# ---------------------------------------------------------------------------------------------------------- freeze (temp)
class TestFreezeRun3(unittest.TestCase):
    def _make(self, d, r2, tamper=False, drop=None, identity_ok=True):
        files = {}
        for name in ghz3_run.REQUIRED_FROZEN_3:
            path = os.path.join(d, *name.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write("content of " + name)
            files[name] = core.sha256_file(path)
        run2_files = {n: core.sha256_file(os.path.join(d, n)) if identity_ok else "0" * 64 for n in ghz3_run.CODE_IDENTITY_FILES}
        with open(os.path.join(r2, "FREEZE_GHZ2.json"), "w") as fh:
            json.dump({"files": run2_files}, fh)
        if drop:
            files.pop(drop)
        with open(os.path.join(d, "FREEZE_GHZ3.json"), "w") as fh:
            json.dump({"files": files}, fh)
        if tamper:
            with open(os.path.join(d, "ghz3_run.py"), "a") as fh:
                fh.write("x")

    def test_required_list_is_every_file_of_the_folder(self):
        expected = (
            "PREREG.md", "README.md", "REVISIONS.md", "ghz2_core.py", "ghz2_study.py", "ghz3_study_h4.py", "ghz3_run.py",
            "ghz3_analyze.py", "ghz3_d4.py", "tests_ghz3.py", "certs/cert_h4_v1.json", "certs/cert_h123_v1.json",
            "certs/k2_sim.json", "certs/power.json")
        self.assertEqual(ghz3_run.REQUIRED_FROZEN_3, expected)
        self.assertEqual(ghz3_run.MANIFEST_NAME, "FREEZE_GHZ3.json")
        found = set()
        for dirpath, dirnames, filenames in os.walk(HERE):                         # every file of the folder
            dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "run", "scratch")]
            for f in filenames:
                found.add(os.path.relpath(os.path.join(dirpath, f), HERE).replace(os.sep, "/"))
        not_frozen = {"FREEZE_GHZ3.json", "RESULTS_GHZ3.json", "RESULTS_GHZ3.md", "RESULTS_GHZ3_boot.npz"}
        self.assertEqual(found - not_frozen, set(ghz3_run.REQUIRED_FROZEN_3))
        self.assertTrue(all(isinstance(n, str) for n in ghz3_run.REQUIRED_FROZEN_3))

    def test_refusal_and_acceptance(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as r2:
            with self.assertRaises(core.FreezeError):                              # absent
                ghz3_run.verify_run3_freeze(d, r2)
            self._make(d, r2)
            self.assertTrue(ghz3_run.verify_run3_freeze(d, r2))
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as r2:
            self._make(d, r2, tamper=True)
            with self.assertRaises(core.FreezeError):                              # hash mismatch
                ghz3_run.verify_run3_freeze(d, r2)
        for dropped in ("ghz3_study_h4.py", "certs/power.json", "ghz3_d4.py", "tests_ghz3.py", "README.md"):
            with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as r2:
                self._make(d, r2, drop=dropped)
                with self.assertRaises(core.FreezeError, msg=dropped):             # a file of the folder not covered
                    ghz3_run.verify_run3_freeze(d, r2)
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as r2:
            self._make(d, r2, identity_ok=False)
            with self.assertRaises(core.FreezeError):                              # code differs from run 2's frozen values
                ghz3_run.verify_run3_freeze(d, r2)

    def test_runner_and_analysis_refuse_before_touching_the_account(self):
        def boom():
            raise AssertionError("QiskitRuntimeService must not be created before the freeze is verified")
        with _Patch(ghz3_run, _service=boom):
            with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as r2:
                for mode in (["--dry-run"], ["--submit", "--quota-seconds", "1000"], ["--fetch"]):
                    self.assertEqual(_quiet(ghz3_run.main, mode, root=d, run2_dir=r2), 3)
                self.assertEqual(_quiet(ghz3_analyze.main, root=d), 3)
                self._make(d, r2, identity_ok=False)                               # manifest fine, code identity broken
                self.assertEqual(_quiet(ghz3_run.main, ["--dry-run"], root=d, run2_dir=r2), 3)
                self.assertFalse(os.path.exists(os.path.join(d, "run")))           # nothing written before the freeze check


# ------------------------------------------------------------------------------------------------------------------ C-1 v2
class TestC1(unittest.TestCase):
    def setUp(self):
        self.k = kingston()
        self.comps = copy.deepcopy(self.k["comps"])

    def _c1(self, new, dev_old="d", dev_new="d"):
        return ghz3_run.c1_check(self.comps, new, dev_old, dev_new)

    def test_the_inputs_are_the_n48_components(self):
        self.assertEqual(ghz3_run.C1_FIELDS, ("S", "cz_err", "g1_pop_err", "g1_par_err", "ro_err", "t1", "t2", "idle"))
        self.assertEqual(set(ghz3_run.m2_inputs(self.comps)), set(ghz3_run.C1_FIELDS))
        self.assertEqual(len(ghz3_run.m2_inputs(self.comps)["S"]), 48)

    def test_identical_is_refused(self):
        c1 = self._c1(copy.deepcopy(self.comps))
        self.assertFalse(c1["c1_satisfied"])
        self.assertFalse(c1["condition_a"])
        self.assertFalse(c1["condition_b"])
        self.assertEqual(c1["max_abs_delta_F_pred"], 0.0)
        self.assertEqual(c1["n_inputs_changed"], 0)

    def test_inputs_changed_but_small_delta_f_is_refused(self):
        new = copy.deepcopy(self.comps)
        new["48"]["t1"][3] *= 1.001
        new["16"]["F_pred"] -= 0.019
        c1 = self._c1(new)
        self.assertTrue(c1["condition_a"])
        self.assertFalse(c1["condition_b"])
        self.assertFalse(c1["c1_satisfied"])
        self.assertEqual(c1["n_inputs_changed"], 1)
        self.assertTrue(c1["inputs_changed"]["t1"]["changed"])
        self.assertEqual(c1["inputs_changed"]["t1"]["n_differing"], 1)

    def test_device_differs_but_small_delta_f_is_refused_by_the_and_rule(self):
        c1 = self._c1(copy.deepcopy(self.comps), "ibm_kingston", "ibm_other")
        self.assertTrue(c1["condition_a"])
        self.assertFalse(c1["condition_b"])
        self.assertFalse(c1["c1_satisfied"])

    def test_large_delta_f_without_any_input_change_or_device_change_is_refused(self):
        new = copy.deepcopy(self.comps)
        new["8"]["F_pred"] += 0.05
        c1 = self._c1(new)
        self.assertTrue(c1["condition_b"])
        self.assertFalse(c1["condition_a"])
        self.assertFalse(c1["c1_satisfied"])

    def test_both_conditions_pass(self):
        new = copy.deepcopy(self.comps)
        new["48"]["cz_err"][0] += 1e-3
        new["24"]["F_pred"] -= 0.03
        c1 = self._c1(new)
        self.assertTrue(c1["c1_satisfied"])
        new2 = copy.deepcopy(self.comps)
        new2["4"]["F_pred"] += 0.03
        self.assertTrue(self._c1(new2, "ibm_kingston", "ibm_other")["c1_satisfied"])          # device change + 0.03
        self.assertAlmostEqual(c1["delta_pred"]["24"]["F_pred"]["diff"], -0.03, places=12)

    def test_threshold_is_at_least_0_02(self):
        self.assertEqual(ghz3_run.C1_THRESHOLD, 0.02)
        for dF, expect in ((0.0200001, True), (-0.0200001, True), (0.0199, False)):
            new = copy.deepcopy(self.comps)
            new["48"]["t2"][0] *= 1.5
            new["32"]["F_pred"] += dF
            self.assertEqual(self._c1(new)["c1_satisfied"], expect, dF)

    def test_chip_wide_change_outside_s48_is_refused(self):
        """Every calibration value of qubits and edges outside S_48 changes; the M2 inputs and predictions do not."""
        k = self.k
        snap = copy.deepcopy(k["snap"])
        in_s = set(self.comps["48"]["S"])
        for q, rec in enumerate(snap["qubits"]):
            if q not in in_s:
                rec["t1"] = (rec["t1"] or 1e-4) * 0.5
                rec["t2"] = (rec["t2"] or 1e-4) * 0.5
                if rec["measure"]:
                    rec["measure"]["error"] = (rec["measure"]["error"] or 0.0) + 0.01
        for e in snap["edges"]:
            if e[0] not in in_s or e[1] not in in_s:
                e[2] = (e[2] or 0.0) + 0.01
        model = core.model_all(k["entries"], core.target_from_snapshot(snap))
        new = {str(n): model[n] for n in core.GRID}
        c1 = self._c1(new)
        self.assertEqual(c1["n_inputs_changed"], 0)
        self.assertEqual(c1["max_abs_delta_F_pred"], 0.0)
        self.assertFalse(c1["c1_satisfied"])

    def test_change_inside_s48_that_moves_the_predictions_passes(self):
        k = self.k
        snap = copy.deepcopy(k["snap"])
        for q in self.comps["48"]["S"]:
            snap["qubits"][q]["measure"]["error"] *= 2.0
        model = core.model_all(k["entries"], core.target_from_snapshot(snap))
        new = {str(n): model[n] for n in core.GRID}
        c1 = self._c1(new)
        self.assertTrue(c1["inputs_changed"]["ro_err"]["changed"])
        self.assertGreaterEqual(c1["max_abs_delta_F_pred"], 0.02)
        self.assertTrue(c1["c1_satisfied"])

    def test_json_serialisable(self):
        json.dumps(self._c1(copy.deepcopy(self.comps)))

    def test_run2_snapshot_itself_is_refused(self):
        """C-1 on run 2's own snapshot: the model recomputed from it equals run 2's model.json -> refused."""
        ref = ghz3_run.load_run2_reference()
        snap2 = ref["snap"]
        tgt = core.target_from_snapshot(snap2)
        model = core.model_all(core.build_all(snap2, tgt), tgt)
        c1 = ghz3_run.c1_check(ref["comps"], model, snap2["backend"], snap2["backend"])
        self.assertEqual(c1["n_inputs_changed"], 0)
        self.assertLess(c1["max_abs_delta_F_pred"], 1e-12)
        self.assertFalse(c1["c1_satisfied"])
        # also with the time stamp changed
        later = copy.deepcopy(snap2)
        later["utc"] = "later"
        tgt2 = core.target_from_snapshot(later)
        model2 = core.model_all(core.build_all(later, tgt2), tgt2)
        self.assertFalse(ghz3_run.c1_check(ref["comps"], model2, snap2["backend"], later["backend"])["c1_satisfied"])

    def test_fakekingston_against_run2(self):
        ref = ghz3_run.load_run2_reference()
        c1 = ghz3_run.c1_check(ref["comps"], self.k["model"], ref["snap"]["backend"], "fake_kingston")
        self.assertTrue(c1["device_differs"])
        self.assertTrue(c1["n_inputs_changed"] > 0)
        self.assertGreater(c1["max_abs_delta_F_pred"], 0.02)
        self.assertTrue(c1["c1_satisfied"])

    def test_reference_files_and_known_hashes(self):
        ref = ghz3_run.load_run2_reference()
        self.assertEqual(ref["snapshot_file"], "snapshot_ibm_kingston_20261111T235843Z.json")
        self.assertEqual(ref["snapshot_file_sha256"], ghz3_run.RUN2_KNOWN["snapshot_file_sha256"])
        self.assertEqual(ref["model_file_sha256"], ghz3_run.RUN2_KNOWN["model_file_sha256"])
        self.assertEqual(ref["snapshot_sha256"], ghz3_run.RUN2_KNOWN["snapshot_content_sha256"])
        self.assertEqual(set(ref["comps"]), {str(n) for n in core.GRID})

    def test_reference_integrity_is_checked(self):
        k = self.k
        with tempfile.TemporaryDirectory() as d:
            write_run2_dir(d, k["snap"], k["comps"])
            with self.assertRaises(ghz3_run.CalibrationError):                    # file hash differs from the known value
                ghz3_run.load_run2_reference(d)
            with _Patch(ghz3_run, RUN2_KNOWN=None):
                self.assertEqual(ghz3_run.load_run2_reference(d)["snapshot_sha256"], core.snapshot_hash(k["snap"]))
        with tempfile.TemporaryDirectory() as d, _Patch(ghz3_run, RUN2_KNOWN=None):
            write_run2_dir(d, k["snap"], k["comps"], hash_="0" * 64)
            with self.assertRaises(ghz3_run.CalibrationError):                    # content hash wrong
                ghz3_run.load_run2_reference(d)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ghz3_run.CalibrationError):
                ghz3_run.load_run2_reference(d)                                   # files missing

    def test_rule14(self):
        r = ghz3_run.rule14_check(self.comps)
        self.assertTrue(r["ok"])
        bad = copy.deepcopy(self.comps)
        bad["4"]["F_pred"] = 0.951
        self.assertFalse(ghz3_run.rule14_check(bad)["ok"])
        bad = copy.deepcopy(self.comps)
        bad["8"]["F_pred"] = 0.95                                               # exactly 1.00: not < 1
        self.assertFalse(ghz3_run.rule14_check(bad)["ok"])
        ok = copy.deepcopy(self.comps)
        ok["8"]["F_pred"] = 0.949
        self.assertTrue(ghz3_run.rule14_check(ok)["ok"])


# ------------------------------------------------------------------------------------------------------------------ C-2
class TestC2(unittest.TestCase):
    def test_boundary_at_115_percent(self):
        self.assertEqual(ghz3_run.C2_MARGIN, 1.15)
        self.assertTrue(ghz3_run.c2_check(100.0, 115.0)["c2_satisfied"])           # exactly 1.15 x estimate: allowed
        self.assertTrue(ghz3_run.c2_check(100.0, 115.0001)["c2_satisfied"])
        self.assertFalse(ghz3_run.c2_check(100.0, 114.99)["c2_satisfied"])
        self.assertFalse(ghz3_run.c2_check(100.0, 0.0)["c2_satisfied"])
        r = ghz3_run.c2_check(187.0, 187 * 1.15 + 1e-9)
        self.assertTrue(r["quota_ok"] and r["cap_ok"])
        self.assertAlmostEqual(r["required_seconds"], 187 * 1.15)

    def test_above_300_seconds_refused_whatever_the_quota(self):
        r = ghz3_run.c2_check(300.1, 1e9)
        self.assertTrue(r["quota_ok"])
        self.assertFalse(r["cap_ok"])
        self.assertFalse(r["c2_satisfied"])
        self.assertTrue(ghz3_run.c2_check(300.0, 345.0)["c2_satisfied"])           # the cap itself is allowed
        self.assertFalse(ghz3_run.c2_check(300.0, 344.9)["c2_satisfied"])

    def test_parse_quota(self):
        self.assertEqual(ghz3_run.parse_quota("250.5"), 250.5)
        for bad in (None, "", "abc", "0", "-5", "nan", "inf"):
            self.assertIsNone(ghz3_run.parse_quota(bad), bad)


# ------------------------------------------------------------------------------------------------------------------ H4
F_PRED = np.array([0.936, 0.889, 0.70, 0.58, 0.455, 0.29])


def _d4data(ratio=0.9, B=1000, noise=0.0, seed=3):
    rng = np.random.default_rng(seed)
    ratio = np.broadcast_to(np.asarray(ratio, float), (6,))
    f_hat = F_PRED * ratio
    boot = f_hat[None, :] + (rng.normal(0.0, noise, (B, 6)) if noise else 0.0)
    boot = np.broadcast_to(boot, (B, 6)).copy()
    return {"F_pred": F_PRED.copy(), "P_pred": F_PRED + 0.02, "C_pred": F_PRED - 0.02, "F_hat": f_hat,
            "P_hat": f_hat + 0.02, "C_hat": f_hat - 0.02, "F_boot": boot, "P_boot": boot + 0.02, "C_boot": boot - 0.02}


class TestH4(unittest.TestCase):
    fn = staticmethod(ghz3_study_h4.H4_overprediction_every_n)

    def test_all_ratios_below_one_holds(self):
        self.assertIs(self.fn(_d4data(0.9)), True)
        self.assertIs(self.fn(_d4data([0.95, 0.94, 0.88, 0.86, 0.85, 0.84], noise=0.01)), True)

    def test_one_n_with_upper_quantile_at_or_above_one_fails(self):
        for i in range(6):
            r = np.full(6, 0.9)
            r[i] = 1.02
            self.assertIs(self.fn(_d4data(r)), False, i)
        self.assertIs(self.fn(_d4data(1.0)), False)                                 # equal to the prediction: not < 1
        r = np.full(6, 0.9)
        r[2] = 1.0
        self.assertIs(self.fn(_d4data(r)), False)                                    # exactly 1 at one n

    def test_97_5th_percentile_not_the_point_estimate(self):
        d = _d4data(0.9, B=1000)
        d["F_boot"][:24, 3] = 1.5 * F_PRED[3]             # 2.4% of the replicates above 1: the 97.5th percentile is below 1
        self.assertIs(self.fn(d), True)
        d = _d4data(0.9, B=1000)
        d["F_boot"][:30, 3] = 1.5 * F_PRED[3]             # 3% above 1
        self.assertIs(self.fn(d), False)

    def test_undefined_cases(self):
        for bad in (1.0, 1.2, 0.0, -0.1, float("nan")):
            d = _d4data(0.9)
            d["F_pred"][1] = bad
            self.assertIsNone(self.fn(d), bad)
        for bad in (0.0, -0.01, float("nan")):
            d = _d4data(0.9)
            d["F_boot"][5, 2] = bad
            self.assertIsNone(self.fn(d), bad)
        d = _d4data(0.9)
        d["F_pred"] = d["F_pred"][:5]
        self.assertIsNone(self.fn(d))
        d = _d4data(0.9)
        d["F_boot"] = d["F_boot"][:, :5]
        self.assertIsNone(self.fn(d))
        d = _d4data(0.9)
        d["F_boot"] = d["F_boot"][:0]
        self.assertIsNone(self.fn(d))

    def test_study_objects_and_imports(self):
        s = ghz3_study_h4.STUDY
        self.assertEqual([c.id for c in s.criteria], ["H4_overprediction_every_n"])
        self.assertEqual({k for k in s.worlds}, {"plus", "minus"})
        ctrl = s.controls[0]
        self.assertEqual(ctrl.criteria, ["H4_overprediction_every_n"])
        for i in range(30):
            rng = np.random.default_rng([5, i])
            plus, minus = ghz3_study_h4.plus_world(rng), ghz3_study_h4.minus_world(rng)
            self.assertEqual(set(plus), {"F_pred", "P_pred", "C_pred", "F_hat", "P_hat", "C_hat", "F_boot", "P_boot", "C_boot"})
            self.assertIs(self.fn(plus), True)
            self.assertIs(self.fn(minus), False)
            out = ctrl.transform(plus, rng)
            self.assertIs(self.fn(out), False)
        with open(os.path.join(HERE, "ghz3_study_h4.py"), encoding="utf-8") as fh:
            src = fh.read()
        imports = {line.split()[1].split(".")[0] for line in src.splitlines() if line.startswith(("import ", "from "))}
        self.assertEqual(imports, {"numpy", "truth_gate"})

    def test_criteria_applied_by_the_analysis_are_the_study_functions(self):
        self.assertIs(ghz3_analyze.CRITERIA["H4_overprediction_every_n"], ghz3_study_h4.H4_overprediction_every_n)
        self.assertIs(ghz3_analyze.CRITERIA["H1_small_n_accuracy"], ghz2_study.H1_small_n_accuracy)
        self.assertIs(ghz3_analyze.CRITERIA["H2_gme_reach_matches"], ghz2_study.H2_gme_reach_matches)
        self.assertIs(ghz3_analyze.CRITERIA["H3_population_specific"], ghz2_study.H3_population_specific)
        self.assertEqual(list(ghz3_study_h4.GRID), list(core.GRID))
        self.assertEqual(ghz3_analyze.ROLES["H1_small_n_accuracy"], "confirmatory")
        self.assertEqual(ghz3_analyze.ROLES["H4_overprediction_every_n"], "confirmatory")
        self.assertTrue(ghz3_analyze.ROLES["H2_gme_reach_matches"].startswith("reported"))
        self.assertIn("exploratory", ghz3_analyze.ROLES["H3_population_specific"])


# ----------------------------------------------------------------------------------------------------------------- power
class TestPower(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inp = ghz3_run.power_inputs()
        cls.sig = ghz3_run.drift_sigmas(cls.inp)
        cls.pred2 = {k: cls.inp["pred2"][k] for k in ("F_pred", "P_pred", "C_pred")}
        cls.pw = ghz3_run.compute_power(cls.pred2, n_datasets=300, label="test", snapshot_sha256="x")

    def test_sigma_rel_follows_the_stated_formula(self):
        inp, grid = self.inp, list(core.GRID)
        for X, hat, boot in (("P", inp["P2"], inp["P_boot"]), ("C", inp["C2"], inp["C_boot"])):
            terms = []
            for n in (4, 8, 16, 32, 48):
                i = grid.index(n)
                v = np.var(boot[:, i], ddof=1) / hat[i] ** 2
                terms.append(math.log(inp["t1"][n][X] / hat[i]) ** 2 / 2 - v)
            self.assertAlmostEqual(self.sig[X], math.sqrt(max(0.0, float(np.mean(terms)))), places=12, msg=X)
        self.assertGreaterEqual(self.sig["P"], 0.0)
        self.assertGreater(self.sig["C"], 0.0)

    def test_negative_pooled_value_counts_as_zero(self):
        inp = dict(self.inp)
        inp["t1"] = {n: {"P": inp["P2"][list(core.GRID).index(n)], "C": inp["C2"][list(core.GRID).index(n)]} for n in (4, 8, 16, 32, 48)}
        s = ghz3_run.drift_sigmas(inp)                                          # run 1 == run 2: ln ratio 0, minus shot variance
        self.assertEqual((s["P"], s["C"]), (0.0, 0.0))

    def test_structure_and_probabilities(self):
        pw = self.pw
        self.assertEqual(pw["n_datasets"], 300)
        self.assertEqual(pw["seed"], 20261116)
        self.assertEqual(set(pw["power"]), {"H1", "H4"})
        self.assertEqual(set(pw["sensitivity"]), {"correlated", "drift_x2"})
        self.assertEqual(set(pw["expected_outcome"]), set(ghz3_analyze.CRITERIA))
        for v in pw["expected_outcome"].values():
            self.assertAlmostEqual(v["P_HOLDS"] + v["P_FAILS"] + v["P_UNDEFINED"], 1.0, places=12)
        for m in pw["sensitivity"].values():
            self.assertEqual(set(m), {"power_H1", "power_H4", "expected_outcome"})
        self.assertEqual(pw["power"]["H4"], pw["expected_outcome"]["H4_overprediction_every_n"]["P_HOLDS"])
        self.assertTrue(0.0 <= pw["power"]["H1"] <= 1.0)
        self.assertIn("exp(sigma_rel,X * z)", pw["method"])

    def test_deterministic(self):
        again = ghz3_run.compute_power(self.pred2, n_datasets=300, label="test", snapshot_sha256="x")
        self.assertEqual(json.dumps(again, sort_keys=True), json.dumps(self.pw, sort_keys=True))

    def test_inputs_and_hashes_recorded(self):
        names = [i["file"] for i in self.pw["inputs"]]
        self.assertEqual(len(names), 6)
        for item in self.pw["inputs"]:
            self.assertEqual(item["sha256"], core.sha256_file(os.path.normpath(os.path.join(HERE, item["file"]))))
        self.assertIn("ghz3_study_h4.py", names)
        self.assertIn("ghz2_study.py", names)
        self.assertTrue(any(n.endswith("RESULTS_GHZ2_boot.npz") for n in names))
        self.assertTrue(any(n.endswith("RESULTS_GHZ.json") for n in names))

    def test_h1_scenario_has_power_when_effect_is_inside_the_band(self):
        self.assertGreater(self.pw["power"]["H1"], 0.8)                            # truth within 0.03 of the prediction
        self.assertGreater(self.pw["power"]["H4"], 0.8)                            # run-2 ratios are well below 1
        # the expected outcome for H1 under run-2 ratios is mostly FAILS (run 2's deviations 0.045 and 0.055 straddle the band)
        self.assertLess(self.pw["expected_outcome"]["H1_small_n_accuracy"]["P_HOLDS"], 0.5)

    def test_unphysical_predictions_give_zero_power_and_undefined(self):
        pred = {k: v.copy() for k, v in self.pred2.items()}
        pred["F_pred"][0] = 1.02                                                    # F_pred outside (0, 1): H1 and H4 UNDEFINED
        pw = ghz3_run.compute_power(pred, n_datasets=50)
        self.assertEqual(pw["power"]["H1"], 0.0)
        self.assertEqual(pw["power"]["H4"], 0.0)
        self.assertEqual(pw["expected_outcome"]["H1_small_n_accuracy"]["P_UNDEFINED"], 1.0)

    def test_device_change_label(self):
        pw = ghz3_run.compute_power(self.pred2, n_datasets=20, label="device change (I-6)", device_change=True)
        self.assertTrue(pw["device_change"])
        self.assertIn("device change", pw["label"])

    def test_design_time_power_uses_run2_predictions(self):
        pw = ghz3_run.design_time_power(n_datasets=50)
        self.assertIn("design-time stand-in", pw["label"])
        self.assertEqual(pw["snapshot_sha256"], ghz3_run.RUN2_KNOWN["snapshot_content_sha256"])
        for i, n in enumerate(core.GRID):
            self.assertAlmostEqual(pw["predictions"]["F_pred"][str(n)], self.pred2["F_pred"][i], places=12)

    def test_power_file_recorded_in_certs(self):
        path = os.path.join(HERE, "certs", "power.json")
        with open(path, encoding="utf-8") as fh:
            pw = json.load(fh)
        self.assertEqual(pw["n_datasets"], 2000)
        self.assertEqual(pw["seed"], 20261116)
        self.assertIn("design-time stand-in", pw["label"])
        for item in pw["inputs"]:
            self.assertEqual(item["sha256"], core.sha256_file(os.path.normpath(os.path.join(HERE, item["file"]))), item["file"])
        self.assertEqual(set(pw["power"]), {"H1", "H4"})


# -------------------------------------------------------------------------------------------- verdict mapping and readings
class TestVerdictMapping(unittest.TestCase):
    asm = staticmethod(ghz3_analyze.assemble_answer)

    # the pre-written sentences of PREREG section 4 (v3), copied literally
    Q1 = {("HOLDS", None): "Q1: on this run's calibration M2 is accurate within 0.05 for 4 and 8 qubits.",
          ("FAILS", "fails"): "Q1: on this run's calibration M2 is not accurate within 0.05 for 4 or 8 qubits.",
          ("FAILS", "not demonstrated"): "Q1: M2's accuracy within 0.05 for 4 and 8 qubits is not demonstrated (H1 failed with power below 0.8).",
          ("UNDEFINED", None): "Q1 is not answered."}
    Q2 = {("HOLDS", None): "Q2: on a new calibration M2 still overpredicts the fidelity at every n.",
          ("FAILS", "fails"): "Q2: on a new calibration M2 does not overpredict at every n; the run-1/2 overprediction did not persist everywhere.",
          ("FAILS", "not demonstrated"): "Q2: persistence of the overprediction at every n is not demonstrated (H4 failed with power below 0.8).",
          ("UNDEFINED", None): "Q2 is not answered."}
    JOINT = {(("HOLDS", None), ("HOLDS", None)): "Together: a small systematic bias.",
             (("HOLDS", None), ("FAILS", "fails")): "Together: M2 is accurate at small n and does not overpredict everywhere.",
             (("FAILS", "fails"), ("HOLDS", None)): "Together: the bias persists and exceeds 0.05 at small n.",
             (("FAILS", "fails"), ("FAILS", "fails")): "Together: M2 misses the small-n band and does not overpredict at every n."}
    OUTCOMES = [("HOLDS", None), ("FAILS", "fails"), ("FAILS", "not demonstrated"), ("UNDEFINED", None)]

    def test_all_sixteen_combinations(self):
        seen_joint = 0
        for o1 in self.OUTCOMES:
            for o4 in self.OUTCOMES:
                out = self.asm(o1[0], o1[1], o4[0], o4[1], True, [])
                self.assertEqual(out["q1"], self.Q1[o1], (o1, o4))
                self.assertEqual(out["q2"], self.Q2[o4], (o1, o4))
                joint = self.JOINT.get((o1, o4))
                self.assertEqual(out["joint"], joint, (o1, o4))              # only the four listed combinations have one
                seen_joint += joint is not None
                self.assertEqual(out["answer"], " ".join(x for x in (out["q1"], out["q2"], joint) if x), (o1, o4))
        self.assertEqual(seen_joint, 4)

    def test_readings_of_both_criteria_are_passed(self):
        out = self.asm("FAILS", "not demonstrated", "FAILS", "fails", True)
        self.assertIn("not demonstrated", out["q1"])
        self.assertIn("does not overpredict at every n", out["q2"])
        self.assertIsNone(out["joint"])
        out = self.asm("HOLDS", None, "FAILS", "not demonstrated", True)
        self.assertIn("is not demonstrated (H4 failed with power below 0.8)", out["q2"])
        self.assertIsNone(out["joint"])
        out = self.asm("FAILS", None, "HOLDS", None, True)                      # a missing reading is read as "not demonstrated"
        self.assertIn("not demonstrated", out["q1"])
        self.assertIsNone(out["joint"])

    def test_control_failure_is_yorumlanamaz_whatever_the_criteria_say(self):
        for o1 in self.OUTCOMES:
            for o4 in self.OUTCOMES:
                out = self.asm(o1[0], o1[1], o4[0], o4[1], False, [{"label": "x", "applies_to": "y"}])
                self.assertEqual(out["answer"], "yorumlanamaz")
                self.assertIsNone(out["q1"])
                self.assertIsNone(out["q2"])
                self.assertIsNone(out["joint"])

    def test_labels_are_attached_and_never_change_the_sentences(self):
        labels = ghz3_analyze.build_labels({"within_drift": True}, {"label": "holds within drift"}, False, True,
                                           ghz3_analyze.LABEL_CHANGED, q1_replicate=True)
        self.assertEqual([x["label"] for x in labels],
                         ["within drift", "holds within drift", "H1 one-sided", ghz3_run.Q1_LABEL, "device change",
                          "calibration changed before execution"])
        self.assertEqual(ghz3_run.Q1_LABEL, "small-n predictions within 0.02 of run 2's: for Q1 this run is not a model test "
                                            "of new predictions")
        self.assertEqual(ghz3_analyze.Q1_LABEL, ghz3_run.Q1_LABEL)
        out = self.asm("HOLDS", None, "HOLDS", None, True, labels)
        self.assertEqual(out["answer"], " ".join((self.Q1[("HOLDS", None)], self.Q2[("HOLDS", None)],
                                                  "Together: a small systematic bias.")))
        self.assertEqual(len(out["labels"]), 6)
        none = ghz3_analyze.build_labels({"within_drift": False}, {"label": None}, True, False, None)
        self.assertEqual(none, [])
        nv = ghz3_analyze.build_labels(None, None, True, False, ghz3_analyze.LABEL_NOT_VERIFIED)
        self.assertEqual([x["label"] for x in nv], ["execution-time calibration not verified"])
        self.assertEqual([x["label"] for x in ghz3_analyze.build_labels(None, None, True, False, None, q1_replicate=True)],
                         [ghz3_run.Q1_LABEL])

    def test_power_reading(self):
        pr = ghz3_analyze.power_reading
        self.assertEqual(pr("FAILS", 0.8), "fails")
        self.assertEqual(pr("FAILS", 0.95), "fails")
        self.assertEqual(pr("FAILS", 0.79), "not demonstrated")
        self.assertIsNone(pr("FAILS", None))                 # no verified power file: K3 failure (yorumlanamaz), no reading at all
        self.assertIsNone(pr("HOLDS", 0.1))
        self.assertIsNone(pr("UNDEFINED", 0.9))
        self.assertNotIn("power_ok", ghz3_analyze.power_reading.__code__.co_varnames)

    def test_drift_quantities(self):
        p, c, f = np.array([0.9, 0.8]), np.array([0.8, 0.7]), np.array([0.85, 0.75])
        sf, sr = ghz3_analyze.drift_quantities(p, c, f, {"P": 0.01, "C": 0.02})
        np.testing.assert_allclose(sf, 0.5 * np.sqrt((p * 0.01) ** 2 + (c * 0.02) ** 2))
        np.testing.assert_allclose(sr, sf / f)

    def test_h1_within_drift_label(self):
        f_pred = np.array(F_PRED)
        sdF = np.full(6, 0.01)
        f_hat = f_pred + np.array([0.049, -0.052, 0, 0, 0, 0])       # decisive n = 8 (larger deviation 0.052), 0.002 from the band
        lab = ghz3_analyze.h1_drift_label(f_hat, f_pred, sdF, "FAILS")
        self.assertEqual(lab["n_decisive"], 8)
        self.assertTrue(lab["within_drift"])
        f_hat = f_pred + np.array([0.049, -0.10, 0, 0, 0, 0])        # far from the band
        self.assertFalse(ghz3_analyze.h1_drift_label(f_hat, f_pred, sdF, "FAILS")["within_drift"])
        f_hat = f_pred + np.array([-0.07, 0.01, 0, 0, 0, 0])         # decisive n = 4
        self.assertEqual(ghz3_analyze.h1_drift_label(f_hat, f_pred, sdF, "FAILS")["n_decisive"], 4)
        f_hat = f_pred + np.array([0.0, 0.029, 0, 0, 0, 0])          # HOLDS case: 0.021 inside the band, 2 sigma = 0.02
        self.assertFalse(ghz3_analyze.h1_drift_label(f_hat, f_pred, sdF, "HOLDS")["within_drift"])
        f_hat = f_pred + np.array([0.0, 0.035, 0, 0, 0, 0])
        self.assertTrue(ghz3_analyze.h1_drift_label(f_hat, f_pred, sdF, "HOLDS")["within_drift"])

    def test_h4_margins_and_labels(self):
        d = _d4data(0.97)
        sdR = np.full(6, 0.02)
        m = ghz3_analyze.h4_margins(d["F_boot"], d["F_pred"], sdR, "HOLDS")
        np.testing.assert_allclose(m["margin"], np.full(6, 0.03))
        self.assertEqual(m["label"], "holds within drift")                    # 0.03 < 2 * 0.02 at every n
        self.assertEqual(m["n_concerned"], list(core.GRID))
        m = ghz3_analyze.h4_margins(_d4data(0.9)["F_boot"], d["F_pred"], sdR, "HOLDS")
        self.assertIsNone(m["label"])                                         # margin 0.1 >= 0.04 everywhere
        self.assertEqual(m["n_concerned"], [])
        # HOLDS: "at some n", each n with its own sigma
        r = np.full(6, 0.9)
        r[3] = 0.97                                                           # only n = 24 has a small margin
        dd = _d4data(r)
        m = ghz3_analyze.h4_margins(dd["F_boot"], dd["F_pred"], sdR, "HOLDS")
        self.assertEqual((m["label"], m["n_concerned"]), ("holds within drift", [24]))
        sd2 = np.full(6, 0.001)
        sd2[3] = 0.02                                                         # a large sigma only at n = 24
        r = np.full(6, 0.95)
        r[3] = 0.97
        dd = _d4data(r)
        m = ghz3_analyze.h4_margins(dd["F_boot"], dd["F_pred"], sd2, "HOLDS")
        self.assertEqual(m["n_concerned"], [24])                              # margin 0.03 < 0.04 only there (0.05 >= 0.002 elsewhere)
        # FAILS: "at every n where q97.5 >= 1"
        r = np.full(6, 0.9)
        r[3] = 1.03
        d = _d4data(r)
        m = ghz3_analyze.h4_margins(d["F_boot"], d["F_pred"], sdR, "FAILS")
        self.assertEqual(m["n_concerned"], [24])
        self.assertEqual(m["label"], "fails within drift")                    # excess 0.03 < 0.04
        r[1] = 1.01                                                           # two n with q97.5 >= 1, both within drift
        m = ghz3_analyze.h4_margins(_d4data(r)["F_boot"], d["F_pred"], sdR, "FAILS")
        self.assertEqual(m["n_concerned"], [8, 24])
        self.assertEqual(m["label"], "fails within drift")
        r[5] = 1.2                                                            # one n clearly outside drift: no label
        m = ghz3_analyze.h4_margins(_d4data(r)["F_boot"], d["F_pred"], sdR, "FAILS")
        self.assertEqual(m["n_concerned"], [8, 24, 48])
        self.assertIsNone(m["label"])
        r = np.full(6, 0.9)
        r[3] = 1.2
        self.assertIsNone(ghz3_analyze.h4_margins(_d4data(r)["F_boot"], d["F_pred"], sdR, "FAILS")["label"])
        self.assertIsNone(ghz3_analyze.h4_margins(d["F_boot"], d["F_pred"], sdR, "UNDEFINED")["label"])
        # each n is compared with its own sigma (FAILS): a small sigma at the failing n removes the label
        r = np.full(6, 0.9)
        r[3] = 1.03
        sd3 = np.full(6, 0.02)
        sd3[3] = 0.005
        self.assertIsNone(ghz3_analyze.h4_margins(_d4data(r)["F_boot"], d["F_pred"], sd3, "FAILS")["label"])

    def test_crossing(self):
        f = [0.9, 0.8, 0.6, 0.45, 0.3, 0.2]
        self.assertAlmostEqual(ghz3_analyze.interp_crossing(f), 16 + (0.6 - 0.5) / (0.6 - 0.45) * 8)
        self.assertIsNone(ghz3_analyze.interp_crossing([0.9] * 6))
        self.assertIsNone(ghz3_analyze.interp_crossing([0.4] * 6))
        h = ghz3_analyze.h2_report(np.array(f), np.tile(f, (50, 1)), np.array(f))
        self.assertEqual(h["n_meas_point"], 16)
        self.assertEqual(h["crossing_ci"][0], h["crossing_ci"][1])
        self.assertEqual(h["crossing_replicates_without_crossing"], 0)


# ------------------------------------------------------------------------------------------------ stopping-rule log helpers
def _L(mode, utc, exit_code=0, attempt=True, snap=None, inv=None, d7=True, k2=True, c1=True, c2=True, quota=None):
    """A log line with the fields the report reads (as ghz3_run.log_line writes them); snap = snapshot time (default = utc)."""
    snap = snap or utc
    line = {"mode": mode, "utc": utc, "snapshot_utc": snap, "invocation": inv or snap, "exit_code": exit_code,
            "attempt": None if mode == "dry-run" else attempt}
    if mode in ("dry-run", "submit-refused", "submit-checks-passed", "submit-failed", "submit-accepted"):
        line.update(d7={"ok": d7}, k2={"ok": k2}, c1={"satisfied": c1}, quota_seconds=quota,
                    c2=None if c2 is None else {"c2_satisfied": c2, "estimate_seconds": 187.0, "required_seconds": 215.05})
    return line


class TestLogReport(unittest.TestCase):
    def dev(self, lines):
        return ghz3_analyze.stopping_rule_report(lines)["deviations_from_the_rule"]

    def test_counts(self):
        lines = [_L("dry-run", "20261120T080000Z"), _L("submit-not-attempt", "20261120T080500Z", 7, False),
                 _L("submit-refused", "20261120T081000Z", 5, c1=False), _L("submit-failed", "20261120T090000Z", 8),
                 _L("submit-accepted", "20261120T093000Z")]
        r = ghz3_analyze.stopping_rule_report(lines)
        self.assertEqual((r["n_lines"], r["n_dry_run"], r["n_attempts"], r["n_submit_refused"], r["n_submit_failed"],
                          r["n_submit_accepted"], r["n_not_attempts"]), (5, 1, 3, 1, 1, 1, 1))

    def test_the_lines_of_one_invocation_are_one_attempt(self):
        lines = [_L("submit-checks-passed", "20261120T080005Z", snap="20261120T080000Z"),
                 _L("submit-accepted", "20261120T080300Z", snap="20261120T080000Z")]
        r = ghz3_analyze.stopping_rule_report(lines)
        self.assertEqual((r["n_attempts"], r["n_submit_accepted"], r["n_submit_refused"], r["n_submit_failed"]), (1, 1, 0, 0))
        lines = [_L("submit-checks-passed", "20261120T080005Z", snap="20261120T080000Z"),
                 _L("submit-failed", "20261120T080300Z", 8, snap="20261120T080000Z")]
        r = ghz3_analyze.stopping_rule_report(lines)
        self.assertEqual((r["n_attempts"], r["n_submit_failed"], r["n_submit_refused"]), (1, 1, 0))
        self.assertEqual(r["deviations_from_the_rule"], [])

    def test_skipped_passing_dry_run_then_a_later_dry_run_and_submit_the_same_day(self):
        lines = [_L("dry-run", "20261120T080000Z"), _L("dry-run", "20261120T110000Z"), _L("submit-accepted", "20261120T113000Z")]
        d = self.dev(lines)                                                    # the 08:00 dry-run has no submit within 2 h
        self.assertEqual(len(d), 1)
        self.assertIn("20261120T080000Z", d[0])
        self.assertIn("without a passing --submit within 2 hours", d[0])

    def test_quota_typo_and_existing_job_json_are_not_attempts(self):
        lines = [_L("submit-not-attempt", "20261120T080000Z", 7, False), _L("submit-not-attempt", "20261120T080100Z", 1, False),
                 _L("submit-accepted", "20261120T080500Z")]
        self.assertEqual(self.dev(lines), [])
        lines = [_L("submit-not-attempt", "20261120T080000Z", 7, False), _L("submit-refused", "20261120T080500Z", 5, c1=False),
                 _L("submit-not-attempt", "20261120T080700Z", 7, False)]
        self.assertEqual(self.dev(lines), [])                                    # one refused attempt, not-attempts do not count

    def test_one_refused_attempt_then_a_passing_one_the_next_day_is_no_deviation(self):
        lines = [_L("submit-refused", "20261120T230000Z", 5, c1=False), _L("submit-accepted", "20261121T000500Z")]
        self.assertEqual(self.dev(lines), [])

    def test_two_refused_attempts_on_one_day_are_a_deviation(self):
        lines = [_L("submit-refused", "20261120T080000Z", 5, c1=False), _L("submit-refused", "20261120T120000Z", 6, c2=False)]
        d = self.dev(lines)
        self.assertEqual(len(d), 1)
        self.assertIn("20261120T120000Z", d[0])
        lines = [_L("submit-refused", "20261120T080000Z", 5, c1=False), _L("submit-accepted", "20261120T120000Z")]    # a passing one too
        self.assertEqual(len(self.dev(lines)), 1)
        lines = [_L("submit-accepted", "20261120T080000Z"), _L("submit-refused", "20261120T120000Z", 5, c1=False)]    # refused AFTER: fine
        self.assertEqual(self.dev(lines), [])

    def test_the_utc_day_is_the_day_of_the_snapshot(self):
        lines = [_L("submit-refused", "20261121T000010Z", 5, snap="20261120T235950Z", c1=False),     # written after midnight
                 _L("submit-accepted", "20261121T001500Z", snap="20261121T001000Z")]
        self.assertEqual(self.dev(lines), [])                                                      # another day by snapshot time
        lines = [_L("submit-refused", "20261121T000010Z", 5, snap="20261120T235950Z", c1=False),
                 _L("submit-accepted", "20261121T000100Z", snap="20261120T235959Z")]
        self.assertEqual(len(self.dev(lines)), 1)                                                  # the same day by snapshot time

    def test_passing_dry_run_then_a_submit_after_three_hours_is_a_deviation(self):
        lines = [_L("dry-run", "20261120T080000Z"), _L("submit-accepted", "20261120T110000Z")]
        d = self.dev(lines)
        self.assertEqual(len(d), 1)
        self.assertIn("passing --dry-run (snapshot 20261120T080000Z)", d[0])
        lines = [_L("dry-run", "20261120T080000Z"), _L("submit-accepted", "20261120T100000Z")]          # exactly 2 h: allowed
        self.assertEqual(self.dev(lines), [])
        lines = [_L("dry-run", "20261120T080000Z"), _L("submit-accepted", "20261120T095959Z")]
        self.assertEqual(self.dev(lines), [])

    def test_the_two_hour_window_is_measured_between_snapshot_times(self):
        # the dry run took long to finish (written 08:10, snapshot 08:00); the submit's snapshot is 2 h 5 min later
        lines = [_L("dry-run", "20261120T081000Z", snap="20261120T080000Z"),
                 _L("submit-accepted", "20261120T100600Z", snap="20261120T100500Z")]
        self.assertEqual(len(self.dev(lines)), 1)                                      # written 1 h 56 min apart, snapshots 2 h 5 min
        # the opposite: written 2 h 1 min apart, snapshots 1 h 59 min 50 s apart
        lines = [_L("dry-run", "20261120T080020Z", snap="20261120T080000Z"),
                 _L("submit-accepted", "20261120T100130Z", snap="20261120T095950Z")]
        self.assertEqual(self.dev(lines), [])
        # a passing --submit BEFORE the dry run does not count
        lines = [_L("submit-accepted", "20261120T070000Z"), _L("dry-run", "20261120T080000Z")]
        self.assertEqual(len(self.dev(lines)), 1)

    def test_dry_run_binding_cases(self):
        self.assertEqual(len(self.dev([_L("dry-run", "20261120T080000Z")])), 1)                         # never followed
        lines = [_L("dry-run", "20261120T080000Z"), _L("submit-refused", "20261120T081000Z", 5, c1=False)]    # refused is not passing
        self.assertEqual(len(self.dev(lines)), 1)
        self.assertEqual(self.dev([_L("dry-run", "20261120T080000Z", 5, c1=False)]), [])                # C-1 failed: not binding
        self.assertEqual(self.dev([_L("dry-run", "20261120T080000Z", 10, k2=False)]), [])               # K2 failed: not binding
        self.assertEqual(self.dev([_L("dry-run", "20261120T080000Z", 4, d7=False)]), [])                # D-7 failed: not binding
        lines = [_L("dry-run", "20261120T080000Z"), _L("submit-failed", "20261120T081000Z", 8)]         # passed the checks
        self.assertEqual(self.dev(lines), [])
        lines = [_L("dry-run", "20261120T080000Z"), _L("submit-checks-passed", "20261120T081000Z")]     # an interrupted attempt
        self.assertEqual(self.dev(lines), [])
        lines = [_L("submit-accepted", "20261120T080000Z"), _L("dry-run", "20261120T090000Z")]          # a passing dry-run afterwards
        self.assertEqual(len(self.dev(lines)), 1)

    def test_a_dry_run_is_binding_whatever_c2_says_and_the_logged_results_decide_not_the_exit_code(self):
        # D-7, K2 and C-1 pass, C-2 fails (exit 6): binding, no passing submit follows -> a deviation
        self.assertEqual(len(self.dev([_L("dry-run", "20261120T080000Z", 6, c2=False, quota=100.0)])), 1)
        # no quota given (C-2 not evaluated): binding too
        self.assertEqual(len(self.dev([_L("dry-run", "20261120T080000Z", 0, c2=None)])), 1)
        # an exit code that disagrees with the logged results changes nothing
        self.assertEqual(len(self.dev([_L("dry-run", "20261120T080000Z", 5)])), 1)               # results say C-1 passed
        self.assertEqual(self.dev([_L("dry-run", "20261120T080000Z", 0, c1=False)]), [])          # results say C-1 failed
        # a line without the new fields (never written by this code) is not binding
        self.assertEqual(self.dev([{"mode": "dry-run", "utc": "20261120T080000Z", "exit_code": 0, "attempt": None}]), [])

    def test_lines_with_c1_passed_and_c2_failed_are_reported_with_their_quota(self):
        lines = [_L("dry-run", "20261120T080000Z", 6, c2=False, quota=100.0),
                 _L("submit-refused", "20261120T090000Z", 6, c2=False, quota=150.0),
                 _L("dry-run", "20261120T091000Z", 5, c1=False, c2=False, quota=50.0),          # C-1 failed: not listed
                 _L("dry-run", "20261120T092000Z", 0, c2=True, quota=400.0),                    # C-2 passed: not listed
                 _L("dry-run", "20261120T093000Z", 0, c2=None)]                                 # C-2 not evaluated: not listed
        rep_ = ghz3_analyze.stopping_rule_report(lines)["c1_pass_c2_fail"]
        self.assertEqual([(x["mode"], x["quota_seconds"], x["snapshot_utc"]) for x in rep_],
                         [("dry-run", 100.0, "20261120T080000Z"), ("submit-refused", 150.0, "20261120T090000Z")])
        self.assertEqual(rep_[0]["estimate_seconds"], 187.0)
        self.assertEqual(ghz3_analyze.stopping_rule_report([])["c1_pass_c2_fail"], [])

    def test_read_log_tolerates_bad_lines(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "dryrun_log.jsonl"), "w") as fh:
                fh.write('{"mode": "dry-run", "utc": "20261120T080000Z"}\nnot json\n\n')
            lines, bad = ghz3_analyze.read_log(d)
            self.assertEqual((len(lines), bad), (1, 1))
            self.assertEqual(ghz3_analyze.read_log(os.path.join(d, "none")), ([], 0))

    def test_log_lines_carry_a_hash_of_the_predictions_never_the_predictions(self):
        k = kingston()
        line = ghz3_run.log_line("dry-run", "b", "h" * 64, k["model"], None, None, None, 0)
        self.assertNotIn("predictions", line)
        self.assertEqual(line["predictions_sha256"], ghz3_run.predictions_sha256(k["model"]))
        blob = json.dumps(line)
        for n in core.GRID:
            for key in ("F_pred", "P_pred", "C_pred"):
                self.assertNotIn(repr(k["model"][n][key]), blob)
        changed = copy.deepcopy(k["comps"])
        changed["16"]["F_pred"] += 1e-9
        self.assertNotEqual(ghz3_run.predictions_sha256(changed), line["predictions_sha256"])
        self.assertEqual(ghz3_run.predictions_sha256(k["comps"]), line["predictions_sha256"])      # int or str keys: same hash
        self.assertIsNone(ghz3_run.log_line("submit-not-attempt", reason="x", attempt=False)["predictions_sha256"])

    def test_log_lines_carry_snapshot_time_invocation_and_the_k2_result(self):
        k = kingston()
        ck = {"c1": {"c1_satisfied": True, "condition_a": True, "condition_b": True, "max_abs_delta_F_pred": 0.03,
                     "n_inputs_changed": 1, "device_differs": False, "q1_model_test": True},
              "budget_ok": True, "estimate": 187.0, "k2": {"pass": False, "error": "RuntimeError"}, "c2": None}
        line = ghz3_run.log_line("dry-run", "b", "h" * 64, k["model"], ck, None, "x", 10, snapshot_utc="20261120T080000Z",
                                 invocation="20261120T080000Z")
        self.assertEqual((line["snapshot_utc"], line["invocation"]), ("20261120T080000Z", "20261120T080000Z"))
        self.assertEqual(line["k2"], {"ok": False, "error": "RuntimeError"})
        self.assertEqual(line["d7"], {"ok": True, "estimate_seconds": 187.0})
        self.assertEqual(ghz3_run.log_line("fetch")["k2"], None)

    def test_log_prefix_anchor(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "run"))
            path = os.path.join(root, "run", "dryrun_log.jsonl")
            self.assertEqual(ghz3_run.log_anchor(root), {"dryrun_log_lines": 0, "dryrun_log_sha256": ghz3_run.log_prefix_sha(path, 0)})
            for i in range(3):
                ghz3_run.append_log(root, {"utc": f"2026112{i}T080000Z", "mode": "dry-run", "i": i})
            anchor = ghz3_run.log_anchor(root)
            self.assertEqual(anchor["dryrun_log_lines"], 3)
            run = os.path.join(root, "run")
            self.assertTrue(ghz3_analyze.log_prefix_status(run, anchor)["ok"])
            ghz3_run.append_log(root, {"utc": "20261125T080000Z", "mode": "submit-accepted"})        # lines after the anchor are fine
            st = ghz3_analyze.log_prefix_status(run, anchor)
            self.assertTrue(st["ok"])
            self.assertEqual(st["lines_after_anchor"], 1)
            with open(path) as fh:
                text = fh.read()
            with open(path, "w") as fh:
                fh.write(text.replace('"i": 1', '"i": 7'))                                            # tamper with the prefix
            self.assertFalse(ghz3_analyze.log_prefix_status(run, anchor)["ok"])
            with open(path, "w") as fh:
                fh.write("\n".join(text.splitlines()[:2]) + "\n")                                    # truncated
            self.assertFalse(ghz3_analyze.log_prefix_status(run, anchor)["ok"])
            self.assertFalse(ghz3_analyze.log_prefix_status(run, {})["ok"])                          # no anchor in job.json
            self.assertEqual(ghz3_analyze.log_prefix_status(run, {"dryrun_log_lines": 0, "dryrun_log_sha256": ghz3_run.log_prefix_sha(path, 0)})["ok"], True)

    def test_post_anchor_lines_must_not_be_dated_before_the_submission(self):
        with tempfile.TemporaryDirectory() as root:
            run = os.path.join(root, "run")
            for u in ("20261120T070000Z", "20261120T071000Z"):
                ghz3_run.append_log(root, {"utc": u, "mode": "dry-run"})
            job = dict(ghz3_run.log_anchor(root), submitted_utc="20261120T080000Z")
            self.assertTrue(ghz3_analyze.log_prefix_status(run, job)["post_anchor_ok"])              # no lines after the anchor
            ghz3_run.append_log(root, {"utc": "20261120T080000Z", "mode": "submit-accepted"})        # exactly at the submission: fine
            ghz3_run.append_log(root, {"utc": "20261120T083000Z", "mode": "fetch"})
            st = ghz3_analyze.log_prefix_status(run, job)
            self.assertTrue(st["ok"] and st["post_anchor_ok"])
            ghz3_run.append_log(root, {"utc": "20261120T075959Z", "mode": "dry-run"})                # one second earlier
            st = ghz3_analyze.log_prefix_status(run, job)
            self.assertTrue(st["ok"])                                                                # the prefix itself is unchanged
            self.assertFalse(st["post_anchor_ok"])
            self.assertIn("20261120T075959Z", st["post_anchor_reason"])
            ghz3_run.append_log(root, {"mode": "fetch"})                                             # a line without a time
            self.assertFalse(ghz3_analyze.log_prefix_status(run, job)["post_anchor_ok"])

    def test_first_logged_fetch_status(self):
        with tempfile.TemporaryDirectory() as run:
            f = ghz3_analyze.first_logged_fetch_status
            self.assertEqual((f(run, [])["ok"], f(run, [])["n_logged_fetches"]), (False, 0))
            with open(os.path.join(run, "execution_calibration_A.json"), "w") as fh:
                fh.write("{}")
            sha = core.sha256_file(os.path.join(run, "execution_calibration_A.json"))
            good = {"mode": "fetch", "file": "execution_calibration_A.json", "file_sha256": sha}
            self.assertTrue(f(run, [{"mode": "dry-run"}, good])["ok"])
            self.assertFalse(f(run, [dict(good, file_sha256="0" * 64)])["ok"])
            self.assertFalse(f(run, [dict(good, file="execution_calibration_B.json")])["ok"])        # missing file
            self.assertFalse(f(run, [{"mode": "fetch"}])["ok"])                                       # no file recorded
            second = dict(good, file="execution_calibration_B.json")                                  # only the FIRST logged fetch counts
            self.assertTrue(f(run, [good, second])["ok"])
            self.assertEqual(f(run, [good, second])["file"], "execution_calibration_A.json")
            self.assertFalse(f(run, [second, good])["ok"])


# ------------------------------------------------------------------------------------------------- runner flows (offline)
class TestRunnerFlows(unittest.TestCase):
    """cmd_submit / cmd_dry_run / cmd_recover with FakeKingston as the 'least busy Heron r2'. The real build_and_report runs; only
    the core build / estimate / model internals are patched (cached FakeKingston circuits), the service and the job submission."""

    def setUp(self):
        self.k = kingston()                                   # before any patch: the real build
        self.d = tempfile.TemporaryDirectory()
        self.root = self.d.name
        self.r2 = os.path.join(self.root, "run2")
        os.makedirs(self.r2)
        self.new_root = os.path.join(self.root, "run3")
        os.makedirs(self.new_root)
        self.est = 187.0
        self.submitted = []
        self.submit_error = None
        k = self.k

        def submit_job(backend, circuits, shots):
            if self.submit_error:
                raise self.submit_error
            self.submitted.append((backend.name, len(circuits), shots))
            return "FAKEJOB123"

        usage = {"usage_remaining_seconds": 4321.0, "usage_consumed_seconds": 100.0, "api_key": "SECRET",
                 "instance": "crn:v1:SECRETCRN", "name": "PRIVATE-NAME"}
        self.k2_calls = []
        self.k2_result = {"pass": True, "detail": {}}
        self.k2_error = None
        self.job_fake = _RecoverJob()                         # what --recover reads from the service

        def k2(entries):                                      # the real K2 (a ~30 s simulation) is tested in TestK2 / the rehearsal
            self.k2_calls.append(entries)
            if self.k2_error:
                raise self.k2_error
            return self.k2_result
        self.patches = [
            _Patch(core, build_all=lambda snap, target, *a, **kw: k["entries"],
                   estimate_time=lambda entries, target, rep_delay=None, shots=core.SHOTS: (self.est, 250e-6, 5e-6),
                   model_all=lambda entries, target, *a, **kw: k["model"]),
            _Patch(ghz3_run, _service=lambda: _FakeService([FakeKingston()], usage=usage, job=self.job_fake), _submit_job=submit_job,
                   RUN2_KNOWN=None, compute_power=_cached_power, k2_noiseless=k2)]
        for p in self.patches:
            p.__enter__()

    def tearDown(self):
        for p in reversed(self.patches):
            p.__exit__()
        self.d.cleanup()

    def _run2(self, mutate_comps=None, device=None):
        """A fake run-2 folder: the FakeKingston snapshot (time stamp changed, optional device name) and its model, mutated."""
        snap = copy.deepcopy(self.k["snap"])
        snap["utc"] = "RUN2"
        if device:
            snap["backend"] = device
        comps = copy.deepcopy(self.k["comps"])
        if mutate_comps:
            mutate_comps(comps)
        write_run2_dir(self.r2, snap, comps)

    @staticmethod
    def _passing(comps):                       # one input changed and F_pred moved by 0.03 at n = 4 (Q1 is a model test too)
        comps["48"]["t1"][0] *= 2.0
        comps["4"]["F_pred"] -= 0.03

    def _ls_run(self):
        p = os.path.join(self.new_root, "run")
        return sorted(os.listdir(p)) if os.path.exists(p) else None

    def _log(self):
        p = os.path.join(self.new_root, "run", "dryrun_log.jsonl")
        if not os.path.exists(p):
            return []
        with open(p) as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def _attempt_folders(self):
        return sorted(x for x in os.listdir(self.new_root) if x.startswith("attempt_"))

    def _no_run_artifacts(self):
        files = self._ls_run() or []
        for f in files:
            self.assertEqual(f, "dryrun_log.jsonl", f)
        self.assertEqual([x for x in os.listdir(self.new_root) if x != "run"], [])        # no leftover folder

    # ---- refusals
    def test_missing_or_invalid_quota_is_logged_as_not_an_attempt_and_does_not_touch_the_account(self):
        self._run2(self._passing)
        boom = lambda: (_ for _ in ()).throw(AssertionError("account touched"))
        with _Patch(ghz3_run, _service=boom):
            for q in (None, "abc", "-1", "0"):
                self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, q, self.r2), ghz3_run.EXIT_QUOTA, q)
        self._no_run_artifacts()
        self.assertEqual(self.submitted, [])
        log = self._log()
        self.assertEqual([l["mode"] for l in log], ["submit-not-attempt"] * 4)
        self.assertTrue(all(l["attempt"] is False and l["exit_code"] == 7 for l in log))
        self.assertTrue(all(l["quota_seconds"] is None for l in log))

    def test_submit_refused_if_c1_fails(self):
        self._run2()                                                              # same values as the new snapshot, other utc
        code, out, err = _captured(ghz3_run.cmd_submit, self.new_root, "1000", self.r2)
        self.assertEqual(code, ghz3_run.EXIT_C1)
        self._no_run_artifacts()
        self.assertEqual(self.submitted, [])
        log = self._log()
        self.assertEqual(len(log), 1)
        self.assertEqual((log[0]["mode"], log[0]["attempt"]), ("submit-refused", True))
        self.assertEqual(log[0]["refusal_reason"], "C-1 not satisfied")
        self.assertFalse(log[0]["c1"]["satisfied"])
        self.assertEqual(log[0]["predictions_sha256"], ghz3_run.predictions_sha256(self.k["model"]))
        self.assertNotIn("predictions", log[0])

    def test_submit_refused_inputs_changed_but_small_delta_f(self):
        self._run2(lambda c: c["48"]["t1"].__setitem__(0, c["48"]["t1"][0] * 2.0))
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "1000", self.r2), ghz3_run.EXIT_C1)
        self._no_run_artifacts()
        self.assertTrue(self._log()[0]["c1"]["condition_a"])
        self.assertFalse(self._log()[0]["c1"]["condition_b"])

    def test_submit_refused_device_differs_but_small_delta_f(self):
        self._run2(device="ibm_other")
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "1000", self.r2), ghz3_run.EXIT_C1)
        self._no_run_artifacts()
        self.assertTrue(self._log()[0]["c1"]["device_differs"])

    def test_submit_refused_if_c2_fails(self):
        self._run2(self._passing)
        need = 1.15 * self.est
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, str(need - 0.5), self.r2), ghz3_run.EXIT_C2)
        self._no_run_artifacts()
        self.assertEqual(self.submitted, [])
        self.assertEqual(self._log()[0]["refusal_reason"], "C-2 not satisfied")

    def test_submit_refused_above_300_s(self):
        self._run2(self._passing)
        self.est = 301.0
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "100000", self.r2), ghz3_run.EXIT_TIME)
        self._no_run_artifacts()
        self.assertEqual(self.submitted, [])
        self.assertFalse(self._log()[0]["d7"]["ok"])

    def test_submit_refused_if_run2_reference_missing(self):
        code = _quiet(ghz3_run.cmd_submit, self.new_root, "1000", self.r2)         # no run-2 files in self.r2
        self.assertEqual(code, ghz3_run.EXIT_C1)
        self._no_run_artifacts()
        self.assertIn("cannot be evaluated", self._log()[0]["refusal_reason"])
        self.assertEqual(self._log()[0]["attempt"], True)

    # ---- a passing submission
    def test_nothing_of_the_model_is_printed_by_the_real_build_and_report(self):
        import inspect
        self.assertIs(inspect.signature(ghz3_run.build_and_report).parameters["show_model"].default, False)
        self._run2(self._passing)
        code, out, err = _captured(ghz3_run.cmd_dry_run, self.new_root, 300.0, self.r2)
        self.assertEqual(code, 0)
        self.assertIn("circuits: 368", out)                                     # the real build_and_report printed its budget lines
        self.assertIn("rough quantum time", out)
        self.assertNotIn("model M2 per n", out)
        self.assertNotIn("S_48", out)
        self.assertNotIn("reference M", out)

    def test_submit_passes_records_everything_and_prints_no_prediction_or_power(self):
        self._run2(self._passing)
        self.assertEqual(_quiet(ghz3_run.cmd_dry_run, self.new_root, None, self.r2), 0)       # a passing dry run first (one log line)
        code, out, err = _captured(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.submitted, [("fake_kingston", 368, 2000)])
        self.assertEqual(len(self.k2_calls), 2)                                    # K2 ran on the circuits of the dry run and of the submit
        self.assertEqual(len(self.k2_calls[1]), 368)
        files = self._ls_run()
        for f in ("calibration_check.json", "job.json", "circuits.qpy", "model.json", "power_run3.json", "dryrun_log.jsonl"):
            self.assertIn(f, files)
        self.assertNotIn("attempt_record.json", files)
        self.assertTrue(any(f.startswith("snapshot_fake_kingston_") for f in files))
        self.assertEqual([x for x in os.listdir(self.new_root) if x != "run"], [])         # temporary folder gone
        with open(os.path.join(self.new_root, "run", "job.json")) as fh:
            job = json.load(fh)
        self.assertEqual(job["quota_seconds"], 250.0)
        self.assertEqual(job["job_id"], "FAKEJOB123")
        self.assertNotIn("recovered", job)
        self.assertTrue(job["c2"]["c2_satisfied"])
        pp = os.path.join(self.new_root, "run", "power_run3.json")
        self.assertEqual(job["power_run3_sha256"], core.sha256_file(pp))
        with open(pp) as fh:
            pw = json.load(fh)
        self.assertEqual(pw["snapshot_sha256"], job["snapshot_sha256"])
        self.assertEqual(pw["n_datasets"], 2000)
        env = ghz3_run.environment_info()                                          # T7: versions and platform in both files
        self.assertEqual(pw["environment"], env)
        self.assertEqual(job["environment"], env)
        self.assertEqual(set(env), {"python", "numpy", "scipy", "qiskit", "qiskit-aer", "qiskit-ibm-runtime", "platform"})
        self.assertTrue(all(env[k] for k in ("python", "numpy", "scipy", "qiskit", "qiskit-aer", "qiskit-ibm-runtime")))
        again = _REAL_POWER(ghz3_run.pred_arrays_from_comps(self.k["model"]), None, None, HERE)   # a real recomputation
        self.assertEqual(pw["power"], again["power"])
        self.assertEqual(pw["expected_outcome"], again["expected_outcome"])
        # the log anchor in job.json: the dry-run line, not yet the accepted line
        log = self._log()
        self.assertEqual([l["mode"] for l in log], ["dry-run", "submit-checks-passed", "submit-accepted"])
        self.assertEqual(job["dryrun_log_lines"], 2)                                # the dry run and the checks-passed line
        logpath = os.path.join(self.new_root, "run", "dryrun_log.jsonl")
        self.assertEqual(job["dryrun_log_sha256"], ghz3_run.log_prefix_sha(logpath, 2))
        st = ghz3_analyze.log_prefix_status(os.path.join(self.new_root, "run"), job)
        self.assertTrue(st["ok"] and st["post_anchor_ok"])
        self.assertEqual(st["lines_after_anchor"], 1)
        # the lines of one --submit share the snapshot time (= job.json's submitted_utc) and the invocation key
        self.assertEqual({(l["snapshot_utc"], l["invocation"]) for l in log[1:]}, {(job["submitted_utc"], job["submitted_utc"])})
        self.assertIsNotNone(log[0]["snapshot_utc"])                                # the dry run: a snapshot time, no invocation
        self.assertIsNone(log[0]["invocation"])
        self.assertEqual(log[1]["k2"], {"ok": True, "error": None})
        self.assertEqual(log[1]["exit_code"], 0)
        with open(os.path.join(self.new_root, "run", "calibration_check.json")) as fh:
            cc = json.load(fh)
        self.assertTrue(cc["c1_satisfied"])
        self.assertTrue(cc["condition_a_device_or_input_differs"] and cc["condition_b_max_abs_dF_ge_threshold"])
        self.assertEqual(cc["threshold"], 0.02)
        self.assertEqual(cc["n_inputs_changed"], 1)
        self.assertTrue(cc["q1_model_test"])
        self.assertIsNone(cc["q1_replicate_label"])
        self.assertAlmostEqual(cc["delta_pred_run3_minus_run2"]["4"]["F_pred"]["diff"], 0.03, places=12)
        self.assertEqual(cc["run2_snapshot_file_sha256"], core.sha256_file(os.path.join(self.r2, ghz3_run.RUN2_SNAPSHOT_FILE)))
        self.assertEqual(cc["run3_snapshot_sha256"], job["snapshot_sha256"])
        self.assertTrue(cc["rule14"]["ok"])
        # the calibration dates of every M2 input of S_48 at submission
        md = cc["m2_input_dates"]
        self.assertIsNone(cc["m2_input_dates_error"])
        self.assertEqual(md["missing"], [])
        S = self.k["comps"]["48"]["S"]
        self.assertEqual({int(q) for q in md["qubits"]}, set(S))
        self.assertTrue(all(set(v) == {"T1", "T2", "readout_error"} for v in md["qubits"].values()))
        tree, ones = ghz3_run.m2_date_targets(self.k["entries"])
        cz_pairs = {frozenset(g["qubits"]) for g in md["gates"] if g["gate"] == "cz"}
        self.assertEqual(cz_pairs, {frozenset(e) for e in tree})
        self.assertEqual({(g["gate"], g["qubits"][0]) for g in md["gates"] if g["gate"] != "cz"}, ones)
        self.assertEqual({g["param"] for g in md["gates"]}, {"gate_error", "gate_length"})
        self.assertFalse(any(frozenset(g["qubits"]) not in {frozenset(e) for e in tree} for g in md["gates"] if g["gate"] == "cz"))
        # nothing of the predictions or of the power is printed
        for n in core.GRID:
            for k in ("F_pred", "P_pred", "C_pred"):
                self.assertNotIn(f"{self.k['model'][n][k]:.4f}", out + err, (n, k))
        for v in (pw["power"]["H1"], pw["power"]["H4"]):
            self.assertNotIn(f"{v:.3f}", out + err)
        self.assertNotIn("F_pred", out)
        # refuses to submit twice (not an attempt) and logs it
        with self.assertRaises(SystemExit):
            _quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2)
        self.assertEqual(len(self.submitted), 1)
        log = self._log()
        self.assertEqual([l["mode"] for l in log], ["dry-run", "submit-checks-passed", "submit-accepted", "submit-not-attempt"])
        self.assertEqual(log[-1]["quota_seconds"], 250.0)                         # the parsed quota, not the raw string
        self.assertIs(log[-1]["attempt"], False)

    def test_q1_replicate_label_is_recorded_when_small_n_predictions_move_by_less_than_0_02(self):
        self._run2(lambda c: (c["48"]["t1"].__setitem__(0, c["48"]["t1"][0] * 2.0), c["16"].__setitem__("F_pred", c["16"]["F_pred"] - 0.03)))
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2), 0)       # C-1 holds (n = 16 moved)
        with open(os.path.join(self.new_root, "run", "calibration_check.json")) as fh:
            cc = json.load(fh)
        self.assertTrue(cc["c1_satisfied"])
        self.assertFalse(cc["q1_model_test"])
        self.assertEqual(cc["q1_replicate_label"], ghz3_run.Q1_LABEL)
        self.assertLess(cc["q1_max_abs_delta_F_pred_4_8"], 0.02)

    # ---- failures, kept attempt folders and --recover
    def test_failed_submission_keeps_the_attempt_folder_and_is_logged(self):
        self._run2(self._passing)
        self.submit_error = RuntimeError("network down")
        code = _quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2)
        self.assertEqual(code, ghz3_run.EXIT_SUBMIT_FAILED)
        self.assertEqual(self._ls_run(), ["dryrun_log.jsonl"])                      # only the log line in run/
        folders = self._attempt_folders()
        self.assertEqual(len(folders), 1)
        self.assertEqual([x for x in os.listdir(self.new_root) if x not in ("run", folders[0])], [])   # no .submit_tmp_ left
        kept = sorted(os.listdir(os.path.join(self.new_root, folders[0])))
        for f in ("calibration_check.json", "circuits.qpy", "model.json", "power_run3.json", "attempt_record.json"):
            self.assertIn(f, kept)
        self.assertFalse(os.path.exists(os.path.join(self.new_root, folders[0], "job.json")))
        log = self._log()
        self.assertEqual([(l["mode"], l["attempt"], l["exit_code"]) for l in log],
                         [("submit-checks-passed", True, 0), ("submit-failed", True, 8)])
        self.assertIn("RuntimeError", log[1]["refusal_reason"])
        self.assertEqual(log[1]["attempt_folder"], folders[0])
        self.assertIsNone(log[1]["job_id"])
        self.assertEqual(log[0]["invocation"], log[1]["invocation"])

    def test_keyboard_interrupt_is_logged_the_folder_kept_and_the_interrupt_re_raised(self):
        self._run2(self._passing)
        self.submit_error = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            _quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2)
        self.assertEqual(len(self._attempt_folders()), 1)
        self.assertEqual([l["mode"] for l in self._log()], ["submit-checks-passed", "submit-failed"])
        self.assertIn("KeyboardInterrupt", self._log()[1]["refusal_reason"])
        self.assertEqual(self._ls_run(), ["dryrun_log.jsonl"])

    def test_retry_after_a_failure_is_possible_and_recover_is_then_refused(self):
        self._run2(self._passing)
        self.submit_error = RuntimeError("x")
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2), 8)
        self.submit_error = None
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2), 0)
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "J"), ghz3_run.EXIT_RECOVER)      # job.json exists

    def test_recover_completes_run_from_the_kept_folder_without_submitting(self):
        self._run2(self._passing)
        self.submit_error = RuntimeError("network down after the job was created")
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2), 8)
        folder = self._attempt_folders()[0]
        n_before = len(self.submitted)
        code, out, err = _captured(ghz3_run.cmd_recover, self.new_root, "REAL-JOB-1")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.submitted), n_before)                              # no submission
        with open(os.path.join(self.new_root, "run", "job.json")) as fh:
            job = json.load(fh)
        self.assertEqual(job["job_id"], "REAL-JOB-1")
        self.assertIs(job["recovered"], True)
        self.assertEqual(job["recovered_from"], folder)
        for key in ("power_run3_sha256", "dryrun_log_lines", "dryrun_log_sha256", "quota_seconds", "manifest", "snapshot_file", "c2"):
            self.assertIn(key, job)
        run = os.path.join(self.new_root, "run")
        for f in ("calibration_check.json", "circuits.qpy", "model.json", "power_run3.json", job["snapshot_file"], "attempt_record.json"):
            self.assertTrue(os.path.isfile(os.path.join(run, f)), f)
        self.assertEqual(job["power_run3_sha256"], core.sha256_file(os.path.join(run, "power_run3.json")))
        self.assertEqual(self._attempt_folders(), [])
        self.assertEqual([l["mode"] for l in self._log()], ["submit-checks-passed", "submit-failed", "recover"])
        self.assertIs(self._log()[-1]["attempt"], False)
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "REAL-JOB-1"), ghz3_run.EXIT_RECOVER)   # job.json exists now
        # the analysis loads the recovered run's job.json and the log prefix check still holds
        self.assertTrue(ghz3_analyze.log_prefix_status(run, job)["ok"])

    def test_recover_refusals(self):
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "J"), ghz3_run.EXIT_RECOVER)         # no attempt folder
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, ""), ghz3_run.EXIT_RECOVER)          # no job id
        self._run2(self._passing)
        self.submit_error = RuntimeError("x")
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2), 8)
        first = self._attempt_folders()[0]
        os.makedirs(os.path.join(self.new_root, "attempt_29990101T000000Z"))                              # a second folder
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "J"), ghz3_run.EXIT_RECOVER)          # exactly one is required
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "J", "attempt_nope"), ghz3_run.EXIT_RECOVER)
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "J", "attempt_29990101T000000Z"), ghz3_run.EXIT_RECOVER)  # no record
        self.assertFalse(os.path.exists(os.path.join(self.new_root, "run", "job.json")))
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "J", first), 0)                      # an explicit --attempt works
        self.assertTrue(os.path.exists(os.path.join(self.new_root, "run", "job.json")))

    def test_recover_after_the_move_failed_uses_the_job_id_of_the_kept_job_json(self):
        self._run2(self._passing)
        orig = ghz3_run._move_into

        def failing_move(tmp, run_dir, names):
            raise OSError("disk full")
        with _Patch(ghz3_run, _move_into=failing_move):
            self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2), 8)
        self.assertEqual(len(self.submitted), 1)                                    # the job WAS created
        log = self._log()
        self.assertEqual(log[1]["job_id"], "FAKEJOB123")
        self.assertIn("a job id WAS returned", log[1]["refusal_reason"])
        folder = self._attempt_folders()[0]
        self.assertTrue(os.path.isfile(os.path.join(self.new_root, folder, "job.json")))
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "OTHER-ID"), ghz3_run.EXIT_RECOVER)   # a different job id
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "FAKEJOB123"), 0)
        with open(os.path.join(self.new_root, "run", "job.json")) as fh:
            self.assertEqual(json.load(fh)["job_id"], "FAKEJOB123")

    def _failed_attempt(self):
        if not os.path.isdir(os.path.join(self.r2, "run")):
            self._run2(self._passing)
        self.submit_error = RuntimeError("x")
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2), 8)
        return self._attempt_folders()[0]

    def _recover_refused(self, folder):
        code, out, err = _captured(ghz3_run.cmd_recover, self.new_root, "J1")
        self.assertEqual(code, ghz3_run.EXIT_RECOVER, err)
        self.assertFalse(os.path.exists(os.path.join(self.new_root, "run", "job.json")))
        self.assertEqual(self._attempt_folders(), [folder])                                  # nothing was moved
        return err

    def test_recover_records_what_it_read_from_the_service(self):
        self._failed_attempt()
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "J1"), 0)
        with open(os.path.join(self.new_root, "run", "job.json")) as fh:
            notes = json.load(fh)["recovered_service_read"]
        self.assertEqual((notes["status"], notes["backend"], notes["n_circuits"]), ("DONE", "fake_kingston", 368))
        self.assertTrue(notes["created_utc"].endswith("+00:00"))

    def test_recover_is_refused_unless_the_service_read_succeeds_and_confirms(self):
        folder = self._failed_attempt()
        now = datetime.datetime.now(datetime.timezone.utc)
        # the read fails: at status(), at the creation date (missing), at the service itself
        self.job_fake.error = RuntimeError("down")
        self.assertIn("service read", self._recover_refused(folder))
        self.job_fake.error = None
        self.job_fake.created = None
        self.assertIn("service read", self._recover_refused(folder))
        self.job_fake.created = "now"
        with _Patch(ghz3_run, _service=lambda: (_ for _ in ()).throw(RuntimeError("no network"))):
            self.assertIn("service read", self._recover_refused(folder))
        # another backend, a job created before the attempt's snapshot, one created more than 10 minutes after the failure
        self.job_fake.backend_name = "ibm_other"
        self.assertIn("ibm_other", self._recover_refused(folder))
        self.job_fake.backend_name = "fake_kingston"
        self.job_fake.created = now - datetime.timedelta(hours=1)
        self.assertIn("outside the window", self._recover_refused(folder))
        self.job_fake.created = now + datetime.timedelta(minutes=11)
        self.assertIn("outside the window", self._recover_refused(folder))
        # not 368 circuits
        self.job_fake.created = "now"
        for n in (367, 369, 0):
            self.job_fake.n_pubs = n
            self.assertIn("circuits", self._recover_refused(folder))
        self.job_fake.n_pubs = 368
        # no failure line in the log for the folder
        log_path = os.path.join(self.new_root, "run", "dryrun_log.jsonl")
        with open(log_path) as fh:
            text = fh.read()
        with open(log_path, "w") as fh:
            fh.write("\n".join(x for x in text.splitlines() if '"submit-failed"' not in x) + "\n")
        self.assertIn("no failure line", self._recover_refused(folder))
        with open(log_path, "w") as fh:
            fh.write(text)
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "J1"), 0)               # all confirmed: recovered

    def test_recover_window_boundaries_are_ten_minutes_either_side(self):
        sec, ten = datetime.timedelta(seconds=1), datetime.timedelta(minutes=10)
        cases = (("snapshot - 10 min - 1 s", lambda s, f: s - ten - sec, False), ("snapshot - 10 min", lambda s, f: s - ten, True),
                 ("snapshot - 10 min + 1 s", lambda s, f: s - ten + sec, True), ("failure + 10 min + 1 s", lambda s, f: f + ten + sec, False),
                 ("failure + 10 min", lambda s, f: f + ten, True), ("failure + 10 min - 1 s", lambda s, f: f + ten - sec, True))
        for i, (name, make, ok) in enumerate(cases):
            self.new_root = os.path.join(self.root, f"case{i}")                  # a fresh folder per case
            os.makedirs(self.new_root)
            folder = self._failed_attempt()
            with open(os.path.join(self.new_root, folder, "attempt_record.json")) as fh:
                snap_at = ghz3_analyze._utc(json.load(fh)["submitted_utc"])
            failed_at = ghz3_analyze._utc([l for l in self._log() if l["mode"] == "submit-failed"][-1]["utc"])
            self.job_fake.created = make(snap_at, failed_at)
            code = _quiet(ghz3_run.cmd_recover, self.new_root, "J1")
            self.assertEqual(code, 0 if ok else ghz3_run.EXIT_RECOVER, name)
            self.assertEqual(os.path.exists(os.path.join(self.new_root, "run", "job.json")), ok, name)
            self.assertEqual(self._attempt_folders(), [] if ok else [folder], name)

    def test_recover_window_accepts_a_job_created_up_to_ten_minutes_after_the_failure_and_naive_local_times(self):
        self._failed_attempt()
        self.job_fake.created = datetime.datetime.now() + datetime.timedelta(minutes=5)       # naive, local time (as the SDK returns it)
        self.assertEqual(_quiet(ghz3_run.cmd_recover, self.new_root, "J1"), 0)
        with open(os.path.join(self.new_root, "run", "job.json")) as fh:
            self.assertEqual(json.load(fh)["job_id"], "J1")

    def test_recover_through_main_needs_the_freeze(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as r2:
            self.assertEqual(_quiet(ghz3_run.main, ["--recover", "J"], root=d, run2_dir=r2), 3)

    def test_failed_power_computation_submits_nothing(self):
        self._run2(self._passing)

        def bad(*a, **k):
            raise ValueError("no data")
        with _Patch(ghz3_run, compute_power=bad):
            self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2), ghz3_run.EXIT_SUBMIT_FAILED)
        self.assertEqual(self.submitted, [])
        self._no_run_artifacts()

    def test_power_is_written_to_the_temporary_folder_before_the_job_is_submitted(self):
        self._run2(self._passing)
        seen = {}

        def spy(backend, circuits, shots):
            tmps = [x for x in os.listdir(self.new_root) if x.startswith(".submit_tmp_")]
            seen["tmp"] = tmps
            seen["files"] = sorted(os.listdir(os.path.join(self.new_root, tmps[0]))) if tmps else None
            seen["run_has_power"] = os.path.exists(os.path.join(self.new_root, "run", "power_run3.json"))
            return "X"
        with _Patch(ghz3_run, _submit_job=spy):
            self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2), 0)
        self.assertEqual(len(seen["tmp"]), 1)
        for f in ("power_run3.json", "calibration_check.json", "circuits.qpy", "model.json", "attempt_record.json"):
            self.assertIn(f, seen["files"])
        self.assertNotIn("job.json", seen["files"])
        self.assertFalse(seen["run_has_power"])                                  # moved into run/ only after the job id

    # ---- dry run
    def test_dry_run_prints_only_pass_fail_and_logs(self):
        self._run2(self._passing)
        code, out, err = _captured(ghz3_run.cmd_dry_run, self.new_root, None, self.r2)
        self.assertEqual(code, 0)
        self.assertIn("C-1 (new calibration for M2): PASS", out)
        self.assertIn("K2 (noiseless simulation of the circuits to be submitted): PASS", out)
        self.assertIn("BINDING (D-7, K2 and C-1 pass)", out)
        self.assertEqual(len(self.k2_calls), 1)
        self.assertIn("D-7", out)
        self.assertIn("C-2 (quota): not evaluated", out)
        for bad in ("F_pred", "P_pred", "C_pred", "dF", "delta", "reference M"):
            self.assertNotIn(bad, out)
        for n in core.GRID:
            for k in ("F_pred", "P_pred", "C_pred", "F_M"):
                self.assertNotIn(f"{self.k['model'][n][k]:.4f}", out)
        self.assertIn("usage_remaining_seconds = 4321", out)                      # whitelisted numeric usage fields only
        for secret in ("SECRET", "PRIVATE", "crn", "api_key", "instance"):
            self.assertNotIn(secret, out + err)
        self.assertEqual(self._ls_run(), ["dryrun_log.jsonl"])
        log = self._log()
        self.assertEqual(len(log), 1)
        self.assertEqual((log[0]["mode"], log[0]["backend"]), ("dry-run", "fake_kingston"))
        self.assertEqual(len(log[0]["snapshot_sha256"]), 64)
        self.assertNotIn("predictions", log[0])
        self.assertEqual(log[0]["predictions_sha256"], ghz3_run.predictions_sha256(self.k["model"]))
        self.assertTrue(log[0]["c1"]["satisfied"])
        self.assertTrue(log[0]["d7"]["ok"])
        self.assertEqual(log[0]["k2"], {"ok": True, "error": None})
        self.assertIsNotNone(log[0]["snapshot_utc"])
        self.assertIsNone(log[0]["c2"])
        self.assertIsNone(log[0]["refusal_reason"])
        self.assertEqual(_quiet(ghz3_run.cmd_dry_run, self.new_root, 100.0, self.r2), ghz3_run.EXIT_C2)
        self.assertEqual(_quiet(ghz3_run.cmd_dry_run, self.new_root, 1000.0, self.r2), 0)
        self.assertEqual(self._ls_run(), ["dryrun_log.jsonl"])
        log = self._log()
        self.assertEqual([l["exit_code"] for l in log], [0, 6, 0])
        self.assertEqual(log[1]["refusal_reason"], "C-2 not satisfied")
        shutil.rmtree(os.path.join(self.r2, "run"))
        self._run2()                                                              # identical values: C-1 fails
        code, out, err = _captured(ghz3_run.cmd_dry_run, self.new_root, 1000.0, self.r2)
        self.assertEqual(code, ghz3_run.EXIT_C1)
        self.assertIn("C-1 (new calibration for M2): FAIL", out)
        self.assertIn("not binding", out)
        self.assertEqual(self._log()[-1]["exit_code"], 5)

    # ---- T1: the checks-passed line and the binding dry run
    def test_the_checks_passed_line_is_written_before_the_power_computation(self):
        self._run2(self._passing)
        seen = {}

        def spy(*a, **kw):
            seen["log"] = self._log()
            raise KeyboardInterrupt()                       # an interruption right after the checks
        with _Patch(ghz3_run, compute_power=spy):
            with self.assertRaises(KeyboardInterrupt):
                _quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2)
        self.assertEqual([l["mode"] for l in seen["log"]], ["submit-checks-passed"])             # already there when power starts
        log = self._log()
        self.assertEqual([l["mode"] for l in log], ["submit-checks-passed"])                       # and it is all that is left
        l = log[0]
        self.assertTrue(l["attempt"] is True and l["d7"]["ok"] and l["k2"]["ok"] and l["c1"]["satisfied"] and l["c2"]["c2_satisfied"])
        self.assertEqual(l["snapshot_utc"], l["invocation"])
        self.assertEqual(l["quota_seconds"], 250.0)
        r = ghz3_analyze.stopping_rule_report(log)
        self.assertEqual((r["n_attempts"], r["n_submit_refused"]), (1, 0))                          # a passing attempt, no job

    def test_a_refused_submit_writes_no_checks_passed_line_and_a_c2_refusal_is_listed_with_its_quota(self):
        self._run2(self._passing)
        need = 1.15 * self.est
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, str(need - 0.5), self.r2), ghz3_run.EXIT_C2)
        self.assertEqual([l["mode"] for l in self._log()], ["submit-refused"])
        r = ghz3_analyze.stopping_rule_report(self._log())
        self.assertEqual(len(r["c1_pass_c2_fail"]), 1)
        self.assertEqual(r["c1_pass_c2_fail"][0]["quota_seconds"], need - 0.5)
        self.assertEqual(r["n_submit_refused"], 1)

    def test_a_dry_run_that_fails_only_c2_is_binding(self):
        self._run2(self._passing)
        code, out, err = _captured(ghz3_run.cmd_dry_run, self.new_root, 100.0, self.r2)
        self.assertEqual(code, ghz3_run.EXIT_C2)
        self.assertIn("BINDING", out)
        self.assertNotIn("not binding", out)
        log = self._log()
        r = ghz3_analyze.stopping_rule_report(log)
        self.assertEqual(len(r["deviations_from_the_rule"]), 1)                                      # no passing submit follows
        self.assertEqual(r["c1_pass_c2_fail"][0]["quota_seconds"], 100.0)

    # ---- T8: K2 on the circuits about to be submitted
    def test_k2_runs_on_the_circuits_to_be_submitted_and_a_failure_refuses_the_attempt_with_exit_10(self):
        self.assertEqual(ghz3_run.EXIT_K2, 10)
        self._run2(self._passing)
        self.k2_result = {"pass": False, "detail": {}}
        code, out, err = _captured(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2)
        self.assertEqual(code, 10)
        self.assertIs(self.k2_calls[0], self.k["entries"])                                           # the entries that would be submitted
        self._no_run_artifacts()
        self.assertEqual(self.submitted, [])
        self.assertIn("K2", err)
        log = self._log()
        self.assertEqual([(l["mode"], l["attempt"], l["exit_code"]) for l in log], [("submit-refused", True, 10)])
        self.assertEqual(log[0]["k2"], {"ok": False, "error": None})
        self.assertIn("K2", log[0]["refusal_reason"])
        r = ghz3_analyze.stopping_rule_report(log)
        self.assertEqual(r["n_submit_refused"], 1)                                                    # counts as a refused attempt
        lines = log + [_L("submit-refused", "99991231T000000Z", 5, snap=log[0]["snapshot_utc"], c1=False)]
        lines[1]["invocation"] = "other"
        self.assertEqual(len(ghz3_analyze.stopping_rule_report(lines)["deviations_from_the_rule"]), 1)   # a second one the same day

    def test_a_k2_exception_is_a_failure_and_the_error_type_is_logged(self):
        self._run2(self._passing)
        self.k2_error = RuntimeError("simulator crashed")
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "250.0", self.r2), 10)
        self.assertEqual(self._log()[0]["k2"], {"ok": False, "error": "RuntimeError"})
        self._no_run_artifacts()

    def test_the_refusal_order_is_d7_then_k2_then_c1_then_c2(self):
        self.k2_result = {"pass": False, "detail": {}}
        self._run2()                                                            # C-1 fails too
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "1.0", self.r2), 10)       # K2 before C-1 and C-2
        shutil.rmtree(os.path.join(self.r2, "run"))
        self._run2(self._passing)
        self.est = 301.0
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "1.0", self.r2), ghz3_run.EXIT_TIME)   # D-7 before K2
        self.est = 187.0
        self.k2_result = {"pass": True, "detail": {}}
        self.assertEqual(_quiet(ghz3_run.cmd_submit, self.new_root, "1.0", self.r2), ghz3_run.EXIT_C2)

    def test_dry_run_with_a_failing_k2_exits_10_and_is_not_binding(self):
        self._run2(self._passing)
        self.k2_result = {"pass": False, "detail": {}}
        code, out, err = _captured(ghz3_run.cmd_dry_run, self.new_root, None, self.r2)
        self.assertEqual(code, 10)
        self.assertIn("K2 (noiseless simulation of the circuits to be submitted): FAIL", out)
        self.assertIn("not binding", out)
        log = self._log()
        self.assertEqual((log[0]["mode"], log[0]["exit_code"], log[0]["k2"]["ok"]), ("dry-run", 10, False))
        self.assertEqual(ghz3_analyze.stopping_rule_report(log)["deviations_from_the_rule"], [])
        self.k2_error = RuntimeError("x")
        self.assertEqual(_quiet(ghz3_run.cmd_dry_run, self.new_root, None, self.r2), 10)
        self.assertEqual(self._log()[-1]["k2"], {"ok": False, "error": "RuntimeError"})

    def test_usage_whitelist(self):
        self.assertEqual(ghz3_run.usage_summary({"usage_remaining_seconds": 5, "x": 1, "usage_consumed_seconds": "a",
                                                 "usage_limit_seconds": True}), {"usage_remaining_seconds": 5})
        self.assertEqual(ghz3_run.usage_summary(None), {})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ghz3_run._print_usage(_FakeService([], usage=RuntimeError("no usage")))
            ghz3_run._print_usage(_FakeService([], usage={"token": "T"}))
            ghz3_run._print_usage(object())
        self.assertIn("not available", out.getvalue())
        self.assertIn("no whitelisted numeric field", out.getvalue())
        self.assertNotIn("token", out.getvalue())


# --------------------------------------------------------------------------------------------------- --fetch: execution-time calibration
class _Reg:
    def __init__(self, counts):
        self._c = counts

    def get_counts(self):
        return dict(self._c)


class _Data:
    def __init__(self, counts):
        self.meas = _Reg(counts)


class _Pub:
    def __init__(self, counts):
        self.data = _Data(counts)


class _FakeJob:
    def __init__(self, metrics=None, metrics_error=None, result=None):
        self._m, self._me, self._r = metrics, metrics_error, result

    def job_id(self):
        return "FAKEJOB123"

    def status(self):
        return "DONE"

    def result(self):
        return self._r

    def metrics(self):
        if self._me:
            raise self._me
        return self._m

    def usage(self):
        return 190.5


def _shifted_props(days):
    """FakeKingston's properties with every calibration date moved ``days`` later (a service that ignores the datetime and
    returns a later calibration)."""
    p = copy.deepcopy(FakeKingston().properties())
    delta = datetime.timedelta(days=days)
    for params in p.qubits:
        for nd in params:
            nd.date = nd.date + delta
    for g in p.gates:
        for nd in g.parameters:
            nd.date = nd.date + delta
    p.last_update_date = p.last_update_date + delta
    return p


class _FakeIBM:
    """FakeKingston with the history API of IBMBackend; records the datetimes it was asked for."""
    def __init__(self, props_error=None, history_error=None, current_error=None, history_ignores_datetime_days=None):
        self.fk = FakeKingston()
        self.calls = []
        self.props_error = props_error
        self.history_error = history_error          # raised by properties(datetime=...) and target_history(...)
        self.current_error = current_error          # raised by properties() / properties(refresh=True)
        self.later = None if history_ignores_datetime_days is None else _shifted_props(history_ignores_datetime_days)
        self.target = self.fk.target
        self.name = self.fk.name
        self.default_rep_delay = getattr(self.fk, "default_rep_delay", None)
        self.processor_type = getattr(self.fk, "processor_type", None)

    def properties(self, refresh=False, datetime=None):
        self.calls.append(("properties", datetime))
        if self.props_error:
            raise self.props_error
        if datetime is not None:
            if self.history_error:
                raise self.history_error
            if self.later is not None:                  # the datetime is ignored: the newest calibration comes back
                return self.later
        elif self.current_error:
            raise self.current_error
        return self.fk.properties()

    def target_history(self, datetime=None):
        self.calls.append(("target_history", datetime))
        if self.history_error:
            raise self.history_error
        return self.fk.target


class _FakeSvc2:
    def __init__(self, job, backend):
        self._j, self._b = job, backend

    def job(self, job_id):
        return self._j

    def backend(self, name):
        return self._b


METRICS = {"timestamps": {"created": "2026-11-20T08:00:00.000Z", "running": "2026-11-20T08:30:15.500Z",
                          "finished": "2026-11-20T08:34:00Z"}, "usage": {"quantum_seconds": 190, "seconds": 190}}
META = {"job_id": "J", "backend": "fake_kingston"}


class TestFetchExecutionCalibration(unittest.TestCase):
    def test_saves_timestamps_usage_dates_and_the_current_calibration_in_a_new_file(self):
        be = _FakeIBM()
        with tempfile.TemporaryDirectory() as d:
            info = ghz3_run.save_execution_calibration(_FakeSvc2(_FakeJob(METRICS), be), _FakeJob(METRICS), META, d)
            files = ghz3_run.exec_files(d)
            self.assertEqual(files, [info["attempt_file"]])
            self.assertTrue(files[0].startswith("execution_calibration_"))
            with open(os.path.join(d, files[0])) as fh:
                saved = json.load(fh)
        self.assertTrue(info["available"])
        self.assertEqual(saved["timestamps"]["running"], "2026-11-20T08:30:15.500Z")
        self.assertEqual(saved["usage"], {"quantum_seconds": 190, "seconds": 190})
        self.assertEqual(saved["job_usage_seconds"], 190.5)
        self.assertEqual(saved["execution_start_utc"], "20261120T083015Z")
        self.assertEqual(saved["execution_start_iso"], "2026-11-20T08:30:15.500000+00:00")
        self.assertEqual(core.snapshot_hash(saved["snapshot"]), saved["snapshot_sha256"])
        self.assertEqual(len(saved["dates"]["qubits"]), 156)                       # the calibration dates of the history result
        self.assertTrue(any(g["gate"] == "cz" for g in saved["dates"]["gates"]))
        want = datetime.datetime(2026, 11, 20, 8, 30, 15, 500000, tzinfo=datetime.timezone.utc)
        self.assertEqual([c[0] for c in be.calls], ["properties", "target_history", "properties", "properties"])
        self.assertEqual(be.calls[0][1], want)                                     # aware UTC datetime
        self.assertEqual(be.calls[1][1], want)
        self.assertIsNone(be.calls[2][1])                                          # the current calibration, always saved too
        self.assertIsNone(be.calls[3][1])
        cur = saved["current"]
        self.assertEqual(core.snapshot_hash(cur["snapshot"]), cur["snapshot_sha256"])
        self.assertEqual(len(cur["dates"]["qubits"]), 156)
        self.assertEqual(saved["snapshot"]["backend"], "fake_kingston")

    def test_every_attempt_is_kept_and_nothing_is_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            with _Patch(ghz3_run, utc_now=lambda: "20261120T090000Z"):            # even within the same second
                a = ghz3_run.save_execution_calibration(_FakeSvc2(None, _FakeIBM()), _FakeJob(METRICS), META, d)
                b = ghz3_run.save_execution_calibration(_FakeSvc2(None, _FakeIBM(history_error=NotImplementedError("c"))), _FakeJob(METRICS), META, d)
            with _Patch(ghz3_run, utc_now=lambda: "20261121T090000Z"):
                c = ghz3_run.save_execution_calibration(_FakeSvc2(None, _FakeIBM()), _FakeJob(METRICS), META, d)
            files = ghz3_run.exec_files(d)
            self.assertEqual(len(files), 3)
            self.assertEqual(files, [a["attempt_file"], b["attempt_file"], c["attempt_file"]])           # oldest first
            self.assertEqual(files[0], "execution_calibration_20261120T090000Z.json")
            self.assertEqual(files[1], "execution_calibration_20261120T090000Z_2.json")
            with open(os.path.join(d, files[0])) as fh:
                self.assertTrue(json.load(fh)["available"])                                              # the first is untouched
            with open(os.path.join(d, files[1])) as fh:
                self.assertFalse(json.load(fh)["available"])

    def test_failures_are_recorded_not_raised(self):
        with tempfile.TemporaryDirectory() as d:
            info = ghz3_run.save_execution_calibration(_FakeSvc2(None, _FakeIBM()), _FakeJob(metrics_error=RuntimeError("x")), META, d)
            self.assertFalse(info["available"])
            self.assertEqual(info["error"], "RuntimeError")
            self.assertNotIn("snapshot", info)
            self.assertIsNotNone(info["current"])                                   # the current calibration is still saved
        with tempfile.TemporaryDirectory() as d:
            m = {"timestamps": {"created": "2026-11-20T08:00:00Z"}, "usage": {}}                # no running timestamp
            info = ghz3_run.save_execution_calibration(_FakeSvc2(None, _FakeIBM()), _FakeJob(m), META, d)
            self.assertFalse(info["available"])
            self.assertEqual(info["error"], "ValueError")
        with tempfile.TemporaryDirectory() as d:
            info = ghz3_run.save_execution_calibration(_FakeSvc2(None, _FakeIBM(props_error=NotImplementedError("cloud"))),
                                                       _FakeJob(METRICS), META, d)
            self.assertFalse(info["available"])
            self.assertEqual(info["error"], "NotImplementedError")
            self.assertEqual(info["current_error"], "NotImplementedError")
            self.assertIsNone(info["current"])
            self.assertEqual(info["timestamps"]["running"], METRICS["timestamps"]["running"])    # timestamps are still saved
        with tempfile.TemporaryDirectory() as d:                                   # nothing can be retrieved
            be = _FakeIBM(history_error=NotImplementedError("c"), current_error=RuntimeError("no"))
            info = ghz3_run.save_execution_calibration(_FakeSvc2(None, be), _FakeJob(METRICS), META, d)
            self.assertIsNone(info["current"])
            self.assertEqual(info["current_error"], "RuntimeError")

    def test_history_unavailable_still_saves_the_current_calibration_with_dates(self):
        be = _FakeIBM(history_error=NotImplementedError("cloud"))
        with tempfile.TemporaryDirectory() as d:
            ghz3_run.save_execution_calibration(_FakeSvc2(None, be), _FakeJob(METRICS), META, d)
            with open(os.path.join(d, ghz3_run.exec_files(d)[0])) as fh:
                saved = json.load(fh)
        self.assertFalse(saved["available"])
        self.assertEqual(saved["error"], "NotImplementedError")
        self.assertNotIn("snapshot", saved)
        cur = saved["current"]
        self.assertEqual(len(cur["dates"]["qubits"]), 156)
        self.assertTrue(any(g["gate"] == "cz" for g in cur["dates"]["gates"]))
        k = kingston()                                                             # end to end with the analysis
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "execution_calibration_20261120T090000Z.json"), "w") as fh:
                json.dump(saved, fh)
            ex = ghz3_analyze.execution_calibration(d, k["entries"], k["model"], "20261120T080000Z")
        self.assertEqual(ex["label"], "verified: no recalibration since submission")

    def test_a_service_that_ignores_the_datetime_cannot_make_a_later_calibration_primary(self):
        """target_history / properties(datetime=...) return the newest calibration (later dates): the analysis rejects the history
        result and falls back to the saved current calibration (verified or not verified), never to 'changed'."""
        k = kingston()
        be = _FakeIBM(history_ignores_datetime_days=400)                           # later dates (and, below, other values)
        with tempfile.TemporaryDirectory() as d:
            info = ghz3_run.save_execution_calibration(_FakeSvc2(None, be), _FakeJob(METRICS), META, d)
            self.assertTrue(info["available"])                                     # the call "worked" ...
            self.assertTrue(info["dates"]["qubits"]["0"]["T1"].startswith("2027"))  # ... but returned a calibration from 2027
            snap2 = copy.deepcopy(info["snapshot"])
            for q in k["comps"]["48"]["S"]:
                snap2["qubits"][q]["t2"] *= 0.5                                     # and other values
            info["snapshot"], info["snapshot_sha256"] = snap2, core.snapshot_hash(snap2)
            with open(os.path.join(d, info["attempt_file"]), "w") as fh:
                json.dump(info, fh)
            ex = ghz3_analyze.execution_calibration(d, k["entries"], k["model"], "20261120T080000Z",
                                                    ghz3_run.select_m2_dates(ghz3_run.calibration_dates(FakeKingston().properties()),
                                                                             k["comps"]["48"]["S"], *ghz3_run.m2_date_targets(k["entries"])))
        self.assertNotEqual(ex["status"], "changed")
        self.assertIsNone(ex["comps_exec"])
        self.assertIn("history result rejected", ex["reason"])
        self.assertEqual(ex["status"], "verified_no_recalibration")                 # the saved current calibration is the snapshot's

    def test_cmd_fetch_saves_counts_and_a_new_attempt_file_each_time(self):
        manifest = [{"index": 0, "name": "A", "family": "GHZ", "n": 2, "kind": "POP", "j": None},
                    {"index": 1, "name": "B", "family": "GHZ", "n": 2, "kind": "PAR", "j": 0}]
        result = [_Pub({"00": 1000, "11": 1000}), _Pub({"00": 1500, "01": 500})]
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "run"))
            with open(os.path.join(d, "run", "job.json"), "w") as fh:
                json.dump({"job_id": "FAKEJOB123", "backend": "fake_kingston", "shots": 2000, "manifest": manifest}, fh)
            with _Patch(ghz3_run, _service=lambda: _FakeSvc2(_FakeJob(METRICS, result=result), _FakeIBM())):
                self.assertEqual(_quiet(ghz3_run.cmd_fetch, d), 0)
            with open(os.path.join(d, "run", "counts.json")) as fh:
                counts = json.load(fh)
            self.assertTrue(counts["k3_count_totals_ok"])
            self.assertEqual(counts["order"], ["A", "B"])
            first = ghz3_run.exec_files(os.path.join(d, "run"))
            self.assertEqual(len(first), 1)
            with open(os.path.join(d, "run", first[0])) as fh:
                self.assertTrue(json.load(fh)["available"])
            log = ghz3_analyze.read_log(os.path.join(d, "run"))[0]
            self.assertEqual([l["mode"] for l in log], ["fetch"])                       # every fetch attempt is logged
            self.assertEqual((log[0]["file"], log[0]["attempt"], log[0]["exit_code"]), (first[0], False, 0))
            self.assertEqual(log[0]["file_sha256"], core.sha256_file(os.path.join(d, "run", first[0])))
            self.assertEqual(log[0]["job_id"], "FAKEJOB123")
            self.assertTrue(ghz3_analyze.first_logged_fetch_status(os.path.join(d, "run"), log)["ok"])
            with _Patch(ghz3_run, _service=lambda: _FakeSvc2(_FakeJob(METRICS, result=result), _FakeIBM(props_error=RuntimeError()))):
                self.assertEqual(_quiet(ghz3_run.cmd_fetch, d), 0)                 # a failing properties call does not break the counts
            files = ghz3_run.exec_files(os.path.join(d, "run"))
            self.assertEqual(len(files), 2)
            self.assertEqual(files[0], first[0])                                    # the first is kept, the second is a new file
            log = ghz3_analyze.read_log(os.path.join(d, "run"))[0]
            self.assertEqual([l["file"] for l in log], files)                       # both are logged, in order
            self.assertEqual(ghz3_analyze.first_logged_fetch_status(os.path.join(d, "run"), log)["file"], first[0])
            result2 = [_Pub({"00": 1000, "11": 999}), _Pub({"00": 1500, "01": 500})]
            with _Patch(ghz3_run, _service=lambda: _FakeSvc2(_FakeJob(METRICS, result=result2), _FakeIBM())):
                self.assertEqual(_quiet(ghz3_run.cmd_fetch, d), 2)                  # tampered totals: exit 2
            self.assertEqual(len(ghz3_run.exec_files(os.path.join(d, "run"))), 3)
            log = ghz3_analyze.read_log(os.path.join(d, "run"))[0]
            self.assertEqual([(l["mode"], l["exit_code"]) for l in log], [("fetch", 0), ("fetch", 0), ("fetch", 2)])


# ---------------------------------------------------------------------------------- analysis: execution-time calibration paths
LATER = "2026-06-01T00:00:00+00:00"


def tree_sets_list(tree):
    """The tree edges as frozensets, in the order of the tree."""
    return [frozenset(e) for e in tree]


class TestExecutionCalibrationPaths(unittest.TestCase):
    SUBMITTED = "20261120T080000Z"
    START = "2026-11-20T08:30:15.500000+00:00"

    def setUp(self):
        self.k = kingston()
        self.d = tempfile.TemporaryDirectory()
        self.run = os.path.join(self.d.name, "run")
        os.makedirs(self.run)
        self.S = self.k["comps"]["48"]["S"]
        self.tree, self.ones = ghz3_run.m2_date_targets(self.k["entries"])
        self.keys = ghz3_run.m2_gate_keys(self.k["entries"])
        # the calibration dates at submission (April 2026, FakeKingston's) restricted to the M2 inputs
        self.sub_dates = ghz3_run.select_m2_dates(ghz3_run.calibration_dates(FakeKingston().properties()), self.S, self.tree, self.ones)
        self.n_files = 0

    def tearDown(self):
        self.d.cleanup()

    def _write(self, info, name=None):
        self.n_files += 1
        name = name or f"execution_calibration_2026112{self.n_files}T090000Z.json"
        with open(os.path.join(self.run, name), "w") as fh:
            json.dump(info, fh)

    def _dates(self):
        return ghz3_run.calibration_dates(FakeKingston().properties())

    def _hist(self, snap, dates=None, current=None, start=None):
        return {"available": True, "error": None, "snapshot": snap, "snapshot_sha256": core.snapshot_hash(snap),
                "dates": self._dates() if dates is None else dates,
                "execution_start_utc": "20261120T083015Z", "execution_start_iso": start or self.START,
                "timestamps": METRICS["timestamps"], "usage": METRICS["usage"], "job_usage_seconds": 190.5,
                "current": current, "current_error": None}

    def _current(self, snap=None, dates=None):
        snap = copy.deepcopy(self.k["snap"]) if snap is None else snap
        snap["utc"] = "20261120T090000Z"
        return {"retrieved_utc": "20261120T090000Z", "snapshot": snap, "snapshot_sha256": core.snapshot_hash(snap),
                "dates": self._dates() if dates is None else dates}

    def _fallback(self, snap=None, dates=None):
        return {"available": False, "error": "NotImplementedError", "current_error": None, "timestamps": METRICS["timestamps"],
                "current": self._current(snap, dates)}

    def _ex(self, submitted=None, sub_dates="default"):
        return ghz3_analyze.execution_calibration(self.run, self.k["entries"], self.k["model"], submitted or self.SUBMITTED,
                                                  self.sub_dates if sub_dates == "default" else sub_dates)

    def _clear(self):
        for f in ghz3_run.exec_files(self.run):
            os.remove(os.path.join(self.run, f))

    def _later(self, dates, keys):
        """Set the date of the given ("q", qubit, param) / ("g", gate, qubits, param) records to LATER."""
        for key in keys:
            if key[0] == "q":
                dates["qubits"][str(key[1])][key[2]] = LATER
            else:
                for g in dates["gates"]:
                    if g["gate"] == key[1] and frozenset(g["qubits"]) == frozenset(key[2]) and g["param"] == key[3]:
                        g["date"] = LATER

    def _t2_snap(self, factor=0.5, qubits=None):
        snap = copy.deepcopy(self.k["snap"])
        for q in (self.S if qubits is None else qubits):
            snap["qubits"][q]["t2"] *= factor
        return snap

    # ---- the four labels
    def test_the_four_labels(self):
        labels = {}
        dates = self._dates()
        self._later(dates, [("q", q, "T2") for q in self.S])
        self._write(self._hist(self._t2_snap(), dates))
        labels["history, changed"] = self._ex()["label"]
        self._clear()
        self._write(self._hist(copy.deepcopy(self.k["snap"])))
        labels["history, equal"] = self._ex()["label"]
        self._clear()
        self._write(self._fallback())
        labels["fallback, verified"] = self._ex()["label"]
        self._clear()
        self._write({"available": False, "error": "X", "current": None, "current_error": "Y"})
        labels["nothing retrieved"] = self._ex()["label"]
        self.assertEqual(labels, {"history, changed": "calibration changed before execution", "history, equal": None,
                                  "fallback, verified": "verified: no recalibration since submission",
                                  "nothing retrieved": "execution-time calibration not verified"})

    def test_no_file_means_not_verified(self):
        ex = self._ex()
        self.assertEqual((ex["status"], ex["label"]), ("unavailable", "execution-time calibration not verified"))
        self.assertIn("not fetched", ex["reason"])
        self.assertEqual(ex["attempt_files"], [])

    # ---- the history path
    def test_equal_within_the_tolerance_uses_the_snapshot_predictions(self):
        self.assertEqual(ghz3_analyze.EXEC_RTOL, 1e-6)
        for factor, status in ((1 + 1e-8, "equal"), (1 + 5e-7, "equal"), (1 + 1e-5, "unverified_difference"), (1 - 1e-4, "unverified_difference")):
            self._clear()
            snap = copy.deepcopy(self.k["snap"])
            for q in self.S:
                snap["qubits"][q]["t1"] *= factor
            self._write(self._hist(snap))                                         # values differ, dates are the old ones
            ex = self._ex()
            self.assertEqual(ex["status"], status, factor)
            self.assertEqual(ex["label"], None if status == "equal" else "execution-time calibration not verified")
            self.assertEqual(ex["path"], "history")

    def test_changed_requires_every_differing_input_to_have_a_later_date(self):
        snap = self._t2_snap()
        # all differing T2 values carry a later date -> changed, primary predictions = the execution-time model
        dates = self._dates()
        self._later(dates, [("q", q, "T2") for q in self.S])
        self._write(self._hist(snap, dates))
        ex = self._ex()
        self.assertEqual((ex["status"], ex["label"]), ("changed", "calibration changed before execution"))
        self.assertTrue(ex["inputs_differ"]["t2"])
        self.assertLess(ex["comps_exec"][48]["C_pred"], self.k["model"][48]["C_pred"])
        # one differing input without a later date -> not verified, snapshot predictions
        self._clear()
        dates = self._dates()
        self._later(dates, [("q", q, "T2") for q in self.S[1:]])
        self._write(self._hist(snap, dates))
        ex = self._ex()
        self.assertEqual((ex["status"], ex["label"]), ("unverified_difference", "execution-time calibration not verified"))
        self.assertIsNone(ex["comps_exec"])
        self.assertIn("without a later calibration date", ex["reason"])
        # a later date on another parameter of the same qubit does not count
        self._clear()
        dates = self._dates()
        self._later(dates, [("q", q, "T1") for q in self.S])
        self._write(self._hist(snap, dates))
        self.assertEqual(self._ex()["status"], "unverified_difference")
        # no dates recorded at submission -> not verified
        self._clear()
        dates = self._dates()
        self._later(dates, [("q", q, "T2") for q in self.S])
        self._write(self._hist(snap, dates))
        self.assertEqual(self._ex(sub_dates=None)["status"], "unverified_difference")

    def test_a_changed_cz_error_needs_a_later_date_on_that_edge(self):
        i = 5
        a, b = self.keys["cz"][i]
        self.assertEqual(len(self.keys["cz"]), 47)
        snap = copy.deepcopy(self.k["snap"])
        for e in snap["edges"]:
            if {e[0], e[1]} == {a, b}:
                e[2] = e[2] * 1.5
        dates = self._dates()
        self._later(dates, [("g", "cz", (a, b), "gate_error")])
        self._write(self._hist(snap, dates))
        ex = self._ex()
        self.assertTrue(ex["inputs_differ"]["cz_err"])
        self.assertEqual(ex["status"], "changed")
        self._clear()
        dates = self._dates()
        other = self.keys["cz"][i + 1]
        self._later(dates, [("g", "cz", other, "gate_error")])                    # the later date is on another edge
        self._write(self._hist(snap, dates))
        self.assertEqual(self._ex()["status"], "unverified_difference")
        self._clear()
        dates = self._dates()
        self._later(dates, [("g", "cz", (a, b), "gate_length")])                  # the right edge, the wrong parameter
        self._write(self._hist(snap, dates))
        self.assertEqual(self._ex()["status"], "unverified_difference")

    def test_a_changed_one_qubit_gate_error_needs_a_later_date_on_that_gate(self):
        name, q = self.keys["g1_pop"][7]
        snap = copy.deepcopy(self.k["snap"])
        snap["qubits"][q]["sx"]["error"] *= 3.0
        dates = self._dates()
        self._later(dates, [("g", name, (q,), "gate_error")])
        self._write(self._hist(snap, dates))
        ex = self._ex()
        self.assertTrue(ex["inputs_differ"]["g1_pop_err"] or ex["inputs_differ"]["g1_par_err"])
        self.assertEqual(ex["status"], "changed")
        self._clear()
        self._write(self._hist(snap, self._dates()))
        self.assertEqual(self._ex()["status"], "unverified_difference")

    def test_a_changed_idle_time_needs_a_later_gate_length_date(self):
        snap = copy.deepcopy(self.k["snap"])
        pairs = {frozenset(e) for e in self.tree}
        for e in snap["edges"]:
            if frozenset((e[0], e[1])) in pairs:
                e[3] = e[3] * 2.0
        dates = self._dates()
        self._later(dates, [("g", "cz", self.keys["cz"][0], "gate_length")])
        self._write(self._hist(snap, dates))
        ex = self._ex()
        self.assertTrue(ex["inputs_differ"]["idle"])
        self.assertEqual(ex["status"], "changed")
        self._clear()
        self._write(self._hist(snap, self._dates()))
        self.assertEqual(self._ex()["status"], "unverified_difference")

    def test_differing_input_dependencies_unit(self):
        comps = {"48": copy.deepcopy(self.k["comps"]["48"])}
        other = copy.deepcopy(comps)
        self.assertEqual(ghz3_analyze.differing_input_dependencies(other, comps, self.k["entries"]), [])
        other["48"]["S"] = list(reversed(other["48"]["S"]))
        deps = ghz3_analyze.differing_input_dependencies(other, comps, self.k["entries"])
        self.assertEqual(deps, [("S", None)])                                       # the qubit list cannot be dated
        ok, why = ghz3_analyze.changed_inputs_have_later_dates(other, comps, self.k["entries"], self._dates(), self.sub_dates)
        self.assertFalse(ok)
        self.assertIn("cannot be dated", why)
        other = copy.deepcopy(comps)
        other["48"]["t1"][4] *= 2
        deps = ghz3_analyze.differing_input_dependencies(other, comps, self.k["entries"])
        self.assertEqual(deps, [("t1[4]", [("q", self.S[4], "T1")])])

    def test_a_history_result_with_dates_after_the_execution_start_is_rejected(self):
        """A service that ignores the datetime returns a later calibration with later dates: it must not become primary."""
        later_dates = ghz3_run.calibration_dates(_shifted_props(400))             # every date about 13 months later
        snap = self._t2_snap()
        # without a saved current calibration: not verified, snapshot predictions
        self._write(self._hist(snap, later_dates))
        ex = self._ex()
        self.assertEqual((ex["status"], ex["label"]), ("unavailable", "execution-time calibration not verified"))
        self.assertIn("history result rejected", ex["reason"])
        self.assertIn("after the execution start", ex["reason"])
        self.assertIsNone(ex["comps_exec"])
        # with a saved current calibration equal to the snapshot's and old dates: the fallback verifies
        self._clear()
        self._write(self._hist(snap, later_dates, current=self._current()))
        ex = self._ex()
        self.assertEqual(ex["status"], "verified_no_recalibration")
        self.assertIn("history result rejected", ex["reason"])
        # a date exactly at the start is accepted (at or before), one millisecond later is not
        self._clear()
        dates = self._dates()
        self._later(dates, [("q", self.S[0], "T2")])
        dates["qubits"][str(self.S[0])]["T2"] = self.START
        self._write(self._hist(copy.deepcopy(self.k["snap"]), dates))
        self.assertEqual(self._ex()["status"], "equal")
        self._clear()
        dates["qubits"][str(self.S[0])]["T2"] = "2026-11-20T08:30:15.501000+00:00"
        self._write(self._hist(copy.deepcopy(self.k["snap"]), dates))
        self.assertEqual(self._ex()["status"], "unavailable")
        # a missing date or record rejects it too
        self._clear()
        dates = self._dates()
        del dates["qubits"][str(self.S[2])]["T1"]
        self._write(self._hist(copy.deepcopy(self.k["snap"]), dates))
        self.assertEqual(self._ex()["status"], "unavailable")
        self._clear()
        info = self._hist(copy.deepcopy(self.k["snap"]))
        info.pop("dates")
        self._write(info)
        self.assertEqual(self._ex()["status"], "unavailable")

    def test_any_failure_of_the_history_path_falls_through_to_the_saved_current_calibration(self):
        snap = self._t2_snap()
        dates = self._dates()
        self._later(dates, [("q", q, "T2") for q in self.S])

        def bad_hash():
            info = self._hist(snap, dates, current=self._current())
            info["snapshot_sha256"] = "0" * 64                                    # the execution-time snapshot was altered
            return info

        def no_dates():
            info = self._hist(snap, dates, current=self._current())
            info.pop("dates")
            return info

        def no_snapshot():
            info = self._hist(snap, dates, current=self._current())
            info.pop("snapshot")                                                  # an exception while reading it
            return info

        def bad_start():
            return self._hist(snap, dates, current=self._current(), start="not a time")

        for make in (bad_hash, no_dates, no_snapshot, bad_start):
            self._clear()
            self._write(make())
            ex = self._ex()
            self.assertEqual((ex["status"], ex["label"]), ("verified_no_recalibration", "verified: no recalibration since submission"),
                             make.__name__)
            self.assertIsNone(ex["comps_exec"], make.__name__)                    # never the history result's predictions
            self.assertIn("history result", ex["reason"], make.__name__)
            self.assertIn("current calibration", ex["path"], make.__name__)
        # the same failures without a usable current calibration: not verified
        for make in (bad_hash, no_dates):
            self._clear()
            info = make()
            info["current"] = None
            info["current_error"] = "RuntimeError"
            self._write(info)
            ex = self._ex()
            self.assertEqual((ex["status"], ex["label"]), ("unavailable", "execution-time calibration not verified"))
        # a fall-through to a current calibration that differs or is newer than the submission is not verified either
        self._clear()
        info = bad_hash()
        info["current"] = self._current(snap=self._t2_snap())
        self._write(info)
        self.assertEqual(self._ex()["status"], "unavailable")
        self._clear()
        info = bad_hash()
        late = self._dates()
        late["qubits"][str(self.S[0])]["T1"] = "2026-11-20T08:30:00+00:00"
        info["current"] = self._current(dates=late)
        self._write(info)
        self.assertEqual(self._ex()["status"], "unavailable")

    def test_use_file_selects_the_attempt_and_the_empty_string_means_none(self):
        self._write(self._fallback(), "execution_calibration_20261120T090000Z.json")
        dates = self._dates()
        self._later(dates, [("q", q, "T2") for q in self.S])
        self._write(self._hist(self._t2_snap(), dates), "execution_calibration_20261121T090000Z.json")
        args = (self.run, self.k["entries"], self.k["model"], self.SUBMITTED, self.sub_dates)
        ex = ghz3_analyze.execution_calibration(*args, use_file="execution_calibration_20261121T090000Z.json")
        self.assertEqual((ex["status"], ex["attempt_used"]), ("changed", "execution_calibration_20261121T090000Z.json"))
        ex = ghz3_analyze.execution_calibration(*args, use_file="")
        self.assertEqual(ex["status"], "unavailable")
        ex = ghz3_analyze.execution_calibration(*args, use_file="execution_calibration_nope.json")
        self.assertEqual(ex["status"], "unavailable")
        self.assertIn("missing", ex["reason"])

    def test_the_first_attempt_is_used(self):
        self._write(self._fallback(), "execution_calibration_20261120T090000Z.json")                  # verified
        dates = self._dates()
        self._later(dates, [("q", q, "T2") for q in self.S])
        self._write(self._hist(self._t2_snap(), dates), "execution_calibration_20261121T090000Z.json")  # would be "changed"
        ex = self._ex()
        self.assertEqual(ex["attempt_used"], "execution_calibration_20261120T090000Z.json")
        self.assertEqual(ex["status"], "verified_no_recalibration")
        self.assertEqual(len(ex["attempt_files"]), 2)

    # ---- the fallback (history unavailable): the current calibration with dates
    def test_fallback_verified_when_inputs_equal_and_all_m2_input_dates_precede_the_submission(self):
        self._write(self._fallback())
        ex = self._ex()
        self.assertEqual(ex["status"], "verified_no_recalibration")
        self.assertEqual(ex["label"], "verified: no recalibration since submission")
        self.assertIsNone(ex["comps_exec"])                                         # the snapshot's predictions are used
        self.assertEqual(ex["path"], "current calibration (history unavailable)")

    def test_fallback_not_verified_cases(self):
        nv = "execution-time calibration not verified"
        S, tree = self.S, self.tree
        tree_sets = {frozenset(e) for e in tree}

        def check(info, expect=nv, submitted=None):
            self._clear()
            self._write(info)
            ex = self._ex(submitted)
            self.assertEqual(ex["label"], expect)
            return ex
        # a qubit parameter dated after the submission
        d = self._dates()
        d["qubits"][str(S[5])]["T2"] = "2026-11-20T08:30:00+00:00"
        self.assertIn("not before the submission", check(self._fallback(dates=d))["reason"])
        d = self._dates()
        d["qubits"][str(S[0])]["readout_error"] = "2026-11-20T08:00:00+00:00"        # equal to the submission time: not "before"
        check(self._fallback(dates=d))
        # a tree-edge cz dated after the submission (either direction), error or length
        for pick in (0, 20, 46):
            for param in ("gate_error", "gate_length"):
                d = self._dates()
                gs = [g for g in d["gates"] if g["gate"] == "cz" and frozenset(g["qubits"]) == tree_sets_list(tree)[pick] and g["param"] == param]
                self.assertTrue(gs)
                gs[0]["date"] = "2026-12-01T00:00:00+00:00"
                check(self._fallback(dates=d))
        # the one-qubit gates of g1_pop_err / g1_par_err (sx): error and length
        self.assertEqual({name for name, _q in self.ones}, {"sx"})
        for param in ("gate_error", "gate_length"):
            d = self._dates()
            q0 = sorted(self.ones)[5][1]
            g = [g for g in d["gates"] if g["gate"] == "sx" and g["qubits"] == [q0] and g["param"] == param][0]
            g["date"] = "2026-12-01T00:00:00+00:00"
            check(self._fallback(dates=d))
        # NOT M2 inputs: a recent date on a non-tree edge inside S_48, on gates that are not in the circuits, and on the other
        # qubit parameters does not prevent "verified"
        d = self._dates()
        non_tree = [g for g in d["gates"] if g["gate"] == "cz" and all(x in S for x in g["qubits"]) and frozenset(g["qubits"]) not in tree_sets]
        self.assertTrue(non_tree, "FakeKingston has a non-tree edge inside S_48")
        for g in non_tree:
            g["date"] = "2026-12-01T00:00:00+00:00"
        for g in d["gates"]:
            if g["gate"] in ("x", "id", "rx", "rzz", "measure", "reset") and all(x in S for x in g["qubits"]):
                g["date"] = "2026-12-01T00:00:00+00:00"
        for q in S[:10]:
            for name in ("readout_length", "prob_meas0_prep1", "prob_meas1_prep0"):
                d["qubits"][str(q)][name] = "2026-12-01T00:00:00+00:00"
        outside = [q for q in range(156) if q not in S][0]
        d["qubits"][str(outside)]["T1"] = "2026-12-01T00:00:00+00:00"
        check(self._fallback(dates=d), "verified: no recalibration since submission")
        # missing records: a qubit, a T1 date, a None date, all cz, one tree edge
        d = self._dates()
        del d["qubits"][str(S[3])]
        check(self._fallback(dates=d))
        d = self._dates()
        d["qubits"][str(S[3])]["T1"] = None
        check(self._fallback(dates=d))
        d = self._dates()
        d["gates"] = [g for g in d["gates"] if g["gate"] != "cz"]
        check(self._fallback(dates=d))
        d = self._dates()
        d["gates"] = [g for g in d["gates"] if not (g["gate"] == "cz" and frozenset(g["qubits"]) == tree_sets_list(tree)[3])]
        self.assertIn("no calibration record", check(self._fallback(dates=d))["reason"])
        # M2 inputs of S_48 that differ from the snapshot's (even with old dates)
        snap = copy.deepcopy(self.k["snap"])
        snap["qubits"][S[7]]["t2"] *= 1.05
        ex = check(self._fallback(snap=snap))
        self.assertIn("differ", ex["reason"])
        # an unreadable submission time, nothing retrieved, a corrupt saved snapshot
        check(self._fallback(), submitted="T")
        check({"available": False, "error": "RuntimeError", "current": None, "current_error": "RuntimeError"})
        info = self._fallback()
        info["current"]["snapshot_sha256"] = "0" * 64
        check(info)

    def test_date_helpers(self):
        recs, missing = ghz3_run.m2_target_records(self._dates(), self.S, self.tree, self.ones)
        self.assertEqual(missing, [])
        self.assertEqual(sum(1 for r in recs if r["gate"] is None), 3 * 48)
        self.assertEqual(ghz3_run.date_of(self.sub_dates, ("q", self.S[0], "T1")).year, 2026)
        self.assertIsNone(ghz3_run.date_of(self.sub_dates, ("q", self.S[0], "nope")))
        self.assertEqual(ghz3_run.date_of(self.sub_dates, ("g", "cz", tuple(self.keys["cz"][0]), "gate_error")).year, 2026)
        d = ghz3_run.calibration_dates(FakeKingston().properties())
        self.assertEqual(len(d["qubits"]), 156)
        self.assertEqual(set(d["qubits"]["0"]), {"T1", "T2", "readout_error", "prob_meas0_prep1", "prob_meas1_prep0", "readout_length"})
        self.assertTrue(all(v.endswith("+00:00") for v in d["qubits"]["0"].values()))
        json.dumps(d)
        self.assertEqual(len(self.keys["cz"]), 47)
        self.assertEqual(len(self.keys["g1_pop"]), len(self.k["comps"]["48"]["g1_pop_err"]))
        self.assertEqual(len(self.keys["g1_par"]), len(self.k["comps"]["48"]["g1_par_err"]))
        self.assertEqual(len(self.keys["cz"]), len(self.k["comps"]["48"]["cz_err"]))


# ------------------------------------------------------------------------------------------------------------ K2 status
class TestK2(unittest.TestCase):
    def test_missing_unreadable_and_bit_order_not_in_the_pass_condition(self):
        with tempfile.TemporaryDirectory() as d:
            k = ghz3_analyze.k2_status(d)                                       # missing file
            self.assertFalse(k["pass"])
            self.assertFalse(k["readable"])
            with open(os.path.join(d, "k2_sim.json"), "w") as fh:
                fh.write("not json")
            self.assertFalse(ghz3_analyze.k2_status(d)["pass"])
            with open(os.path.join(d, "k2_sim.json"), "w") as fh:
                json.dump({"detail": {}}, fh)                                  # no "pass" key
            self.assertFalse(ghz3_analyze.k2_status(d)["pass"])
            with open(os.path.join(d, "k2_sim.json"), "w") as fh:
                json.dump({"pass": True, "bit_order_control": {"pass": False}}, fh)
            k = ghz3_analyze.k2_status(d)
            self.assertTrue(k["pass"])                                          # a failing bit-order control does not fail K2
            self.assertEqual(k["bit_order_control_reported_only"], {"pass": False})
            with open(os.path.join(d, "k2_sim.json"), "w") as fh:
                json.dump({"pass": False}, fh)
            self.assertFalse(ghz3_analyze.k2_status(d)["pass"])

    def test_certs_k2_file(self):
        k = ghz3_analyze.k2_status(os.path.join(HERE, "certs"))
        self.assertTrue(k["pass"])
        self.assertIn("note", k["bit_order_control_reported_only"])


# ------------------------------------------------------------------------------------------ end-to-end analysis rehearsal
def _k2_stub_pass(entries):
    return {"pass": True, "detail": {"stub": True}}


class TestAnalysisRehearsal(unittest.TestCase):
    POWER_N = 60

    EXEC_NAME = "execution_calibration_20261120T090000Z.json"
    DEFAULT_EXEC = {"available": False, "error": "NotImplementedError", "current": None, "current_error": "NotImplementedError",
                    "timestamps": METRICS["timestamps"], "usage": METRICS["usage"]}

    def _put_exec(self, d, run, info=None, name=None, utc="20261120T090000Z"):
        """Save an execution-calibration attempt and log it as a --fetch line (file name and SHA-256), as cmd_fetch does."""
        name = name or self.EXEC_NAME
        with open(os.path.join(run, name), "w") as fh:
            json.dump(self.DEFAULT_EXEC if info is None else info, fh)
        ghz3_run.append_log(d, {"utc": utc, "mode": "fetch", "attempt": False, "backend": "fake_kingston", "exit_code": 0,
                                "file": name, "file_sha256": core.sha256_file(os.path.join(run, name)), "job_id": "SIMULATED"})
        return name

    def _changed_info(self):
        """An execution-time calibration whose T2 values are halved and dated later than the submission: status 'changed'."""
        k = kingston()
        snap2 = copy.deepcopy(k["snap"])
        for q in k["comps"]["48"]["S"]:
            snap2["qubits"][q]["t2"] *= 0.5
        dates = ghz3_run.calibration_dates(FakeKingston().properties())
        for q in k["comps"]["48"]["S"]:
            dates["qubits"][str(q)]["T2"] = "2026-06-01T00:00:00+00:00"
        return {"available": True, "error": None, "snapshot": snap2, "snapshot_sha256": core.snapshot_hash(snap2), "dates": dates,
                "execution_start_utc": "20261120T083015Z", "execution_start_iso": "2026-11-20T08:30:15.500000+00:00",
                "timestamps": METRICS["timestamps"], "usage": METRICS["usage"], "job_usage_seconds": 190.5,
                "current": None, "current_error": None}

    def _setup(self, d, with_cc=True, with_power=True, log=None, manifest=True, exec_info=None):
        """exec_info: None = a default attempt (nothing retrieved) saved and logged as the first fetch; a dict = that attempt;
        False = no fetch at all."""
        k = kingston()
        run = os.path.join(d, "run")
        os.makedirs(run)
        snap, h = k["snap"], k["hash"]
        with open(os.path.join(run, "snapshot_x.json"), "w") as fh:
            json.dump({"sha256": h, "snapshot": snap}, fh)
        with open(os.path.join(run, "circuits.qpy"), "wb") as fh:
            qpy.dump([e["circuit"] for e in k["entries"]], fh)
        with open(os.path.join(run, "model.json"), "w") as fh:
            json.dump({"snapshot_sha256": h, "components": k["comps"]}, fh)
        counts = all_ideal_counts()
        order = [e["name"] for e in k["entries"]]
        with open(os.path.join(run, "counts.json"), "w") as fh:
            json.dump({"job_id": "SIMULATED", "order": order, "circuits": counts}, fh)
        if log:
            with open(os.path.join(run, "dryrun_log.jsonl"), "w") as fh:
                for l in log:
                    fh.write(json.dumps(l) + "\n")
        job = {"job_id": "SIMULATED", "backend": "fake_kingston", "submitted_utc": "20261120T080000Z", "snapshot_file": "snapshot_x.json",
               "snapshot_sha256": h, "shots": core.SHOTS, "quota_seconds": 300.0, "manifest": core.manifest_of(k["entries"]),
               **ghz3_run.log_anchor(d)}
        if with_cc:
            ref = ghz3_run.load_run2_reference()
            c1 = ghz3_run.c1_check(ref["comps"], k["model"], ref["snap"]["backend"], "fake_kingston")
            tree, ones = ghz3_run.m2_date_targets(k["entries"])
            m2d = ghz3_run.select_m2_dates(ghz3_run.calibration_dates(FakeKingston().properties()), k["comps"]["48"]["S"], tree, ones)
            rec = ghz3_run.calibration_record(c1, ref, "snapshot_x.json", h, ghz3_run.rule14_check(k["model"]), m2d)
            with open(os.path.join(run, "calibration_check.json"), "w") as fh:
                json.dump(rec, fh)
        if with_power:
            pw = _cached_power(ghz3_run.pred_arrays_from_comps(k["comps"]), None, None, HERE, n_datasets=self.POWER_N, label="test",
                               snapshot_sha256=h, device_change=True)
            with open(os.path.join(run, "power_run3.json"), "w") as fh:
                json.dump(pw, fh, indent=1)
            job["power_run3_sha256"] = core.sha256_file(os.path.join(run, "power_run3.json"))
        with open(os.path.join(run, "job.json"), "w") as fh:
            json.dump(job, fh)
        if exec_info is not False:
            self._put_exec(d, run, exec_info)                                    # a post-anchor line, as after a real --fetch
        if manifest:
            with open(os.path.join(d, "FREEZE_GHZ3.json"), "w") as fh:
                json.dump({"files": {n: core.sha256_file(os.path.join(HERE, n)) for n in ("ghz2_study.py", "ghz3_study_h4.py")}}, fh)
        return run, counts, order

    def _analyse(self, d, run, real_k2=False, k2_stub=_k2_stub_pass, **kw):
        kw.setdefault("certs_dir", os.path.join(HERE, "certs"))
        kw.setdefault("power_n_datasets", self.POWER_N)
        if real_k2:
            return ghz3_analyze.run_analysis(root=d, run_dir=run, out_dir=d, B=100, **kw)
        with _Patch(ghz3_analyze, k2_noiseless=k2_stub):
            return ghz3_analyze.run_analysis(root=d, run_dir=run, out_dir=d, B=100, **kw)

    def _k3(self, res):
        return res["controls"]["K3"]["detail"]

    def test_pipeline_on_ideal_counts(self):
        log = [{"utc": "20261120T070000Z", "mode": "dry-run", "exit_code": 0, "attempt": None, "backend": "fake_kingston",
                "predictions_sha256": ghz3_run.predictions_sha256(kingston()["comps"]), "c1": {"satisfied": True}, "c2": None},
               {"utc": "20261120T073000Z", "mode": "submit-not-attempt", "exit_code": 7, "attempt": False, "backend": None,
                "predictions_sha256": None, "c1": None, "c2": None}]
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d, log=log)
            ghz3_run.append_log(d, {"utc": "20261120T080000Z", "mode": "submit-accepted", "exit_code": 0, "attempt": True,
                                    "backend": "fake_kingston", "predictions_sha256": ghz3_run.predictions_sha256(kingston()["comps"]),
                                    "c1": {"satisfied": True}, "c2": {"c2_satisfied": True}})
            res = self._analyse(d, run, write=True)
            k3 = res["controls"]["K3"]
            self.assertTrue(k3["pass"], k3)
            for key in ("core_and_study_sha256_equal_run2_frozen", "c1_recomputed_holds", "run2_hashes_in_calibration_check_equal_known",
                        "power_run3_exists_and_hash_matches_job", "power_run3_input_hashes_match_frozen", "power_run3_recomputation_equal",
                        "log_prefix_recorded_in_job_unchanged", "m2_recomputed_equals_saved_model",
                        "log_post_anchor_lines_not_before_submission", "first_logged_fetch_file_exists_and_hash_matches",
                        "job_created_and_started_after_submission"):
                self.assertTrue(k3["detail"][key], key)
            self.assertTrue(res["controls"]["K1"]["pass"])
            k2 = res["controls"]["K2"]
            self.assertTrue(k2["pass"] and k2["design_check"]["pass"] and k2["binding"]["pass"])
            self.assertTrue(res["interpretable"])
            self.assertEqual(set(res["criteria"]), set(ghz3_analyze.CRITERIA))
            self.assertEqual(res["criteria"]["H4_overprediction_every_n"], "FAILS")      # ideal data: F >= F_pred
            self.assertEqual(res["criteria"]["H1_small_n_accuracy"], "FAILS")
            pw = res["power_at_submission"]["power"]
            for cid, key in (("H1_small_n_accuracy", "H1"), ("H4_overprediction_every_n", "H4")):
                self.assertEqual(res["readings"][cid], "fails" if pw[key] >= 0.8 else "not demonstrated")
            ans = res["answer"]
            o1 = ("FAILS", res["readings"]["H1_small_n_accuracy"])
            o4 = ("FAILS", res["readings"]["H4_overprediction_every_n"])
            self.assertEqual(ans["q1"], ghz3_analyze.Q1_SENTENCES[o1])
            self.assertEqual(ans["q2"], ghz3_analyze.Q2_SENTENCES[o4])
            self.assertEqual(ans["joint"], ghz3_analyze.JOINT_SENTENCES.get((o1, o4)))
            labels = [x["label"] for x in ans["labels"]]
            self.assertIn("device change", labels)
            self.assertIn("execution-time calibration not verified", labels)
            self.assertNotIn(ghz3_run.Q1_LABEL, labels)                                  # fake vs real run 2: Q1 is a model test
            q1 = res["q1_per_question"]
            self.assertTrue(q1["model_test"])
            self.assertGreaterEqual(q1["max_abs_dF_4_8_snapshot"], 0.02)
            self.assertEqual(res["predictions_in_use"]["source"], "snapshot")
            for t in res["table"]:
                self.assertIsNotNone(t["sigma_d_R"])
                self.assertAlmostEqual(t["H4_margin"], 1.0 - t["H4_ratio_q975"])
            self.assertTrue(all(abs(t["F"] - 1.0) < 0.02 for t in res["table"]))
            self.assertEqual(res["headline"]["n_meas_point"], 48)
            self.assertEqual(res["h2_reported"]["n_meas_point"], 48)
            cmp_ = res["comparison_with_earlier_runs"]
            self.assertEqual([r["n"] for r in cmp_["R_table"]], list(core.GRID))
            self.assertIsNone([r for r in cmp_["R_table"] if r["n"] == 24][0]["R_run1"])
            self.assertIn("recomputed with ghz2_core", cmp_["run1_source"])
            tr = res["tracking"]
            self.assertTrue(tr["available"])
            self.assertEqual(tr["ci_kind"], "shot noise only")
            self.assertEqual([r["n"] for r in tr["rows"]], list(core.GRID))
            self.assertTrue(all(r["sigma_d_F"] is not None and r["ci_kind"] == "shot noise only" for r in tr["rows"]))
            self.assertTrue(res["c1"]["file_exists"])
            self.assertTrue(res["c1"]["recomputed"]["c1_satisfied"])
            self.assertTrue(res["c1"]["rule14_recheck"]["ok"])
            dl = res["dryrun_log"]
            self.assertEqual(dl["stopping_rule"]["n_lines"], 3)
            self.assertEqual(dl["stopping_rule"]["n_not_attempts"], 1)
            self.assertEqual(dl["stopping_rule"]["deviations_from_the_rule"], [])
            self.assertTrue(dl["anchor"]["ok"])
            self.assertEqual(dl["anchor"]["lines_after_anchor"], 2)                       # the fetch line and the accepted line
            self.assertTrue(dl["anchor"]["post_anchor_ok"])
            self.assertEqual(dl["first_logged_fetch"]["file"], self.EXEC_NAME)
            self.assertTrue(dl["first_logged_fetch"]["ok"])
            self.assertTrue(dl["job_time"]["ok"])
            self.assertEqual(dl["stopping_rule"]["n_post_anchor_lines_not_used_for_deviations"], 1)     # the fetch line
            self.assertEqual(res["power_at_submission"]["environment"]["differs"], {})
            self.assertEqual(res["predictions_in_use"]["execution_calibration"]["attempt_used"], self.EXEC_NAME)
            self.assertTrue(dl["stopping_rule"]["accepted_line_predictions_hash_matches_snapshot"])
            for name in ("RESULTS_GHZ3.md", "RESULTS_GHZ3.json", "RESULTS_GHZ3_boot.npz"):
                self.assertTrue(os.path.isfile(os.path.join(d, name)), name)
            with open(os.path.join(d, "RESULTS_GHZ3.md"), encoding="utf-8") as fh:
                md = fh.read()
            for token in ("Answer to Q1 and Q2", "Q1: ", "Q2: ", "Tracking", "shot noise only", "sigma_d,F", "Log (run/dryrun_log.jsonl",
                          "Power at submission", "R(n)", "C-1 (v3)", "Reported (not confirmatory)", "margin 1 - q", "C-1 per question",
                          "Environment (power file / now): identical", "first logged fetch: " + self.EXEC_NAME,
                          "Post-anchor lines dated not before the submission: True"):
                self.assertIn(token, md)
            with np.load(os.path.join(d, "RESULTS_GHZ3_boot.npz")) as z:
                self.assertEqual(z["F_boot"].shape, (100, 6))

    def test_k3_additions_fail_when_they_should(self):
        with tempfile.TemporaryDirectory() as d:                                   # calibration_check.json missing
            run, counts, order = self._setup(d, with_cc=False)
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["run2_hashes_in_calibration_check_equal_known"])
            self.assertFalse(res["interpretable"])
            self.assertEqual(res["answer"]["answer"], "yorumlanamaz")
        with tempfile.TemporaryDirectory() as d:                                   # wrong run-2 hash recorded
            run, counts, order = self._setup(d)
            p = os.path.join(run, "calibration_check.json")
            with open(p) as fh:
                cc = json.load(fh)
            cc["run2_model_file_sha256"] = "0" * 64
            with open(p, "w") as fh:
                json.dump(cc, fh)
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["run2_hashes_in_calibration_check_equal_known"])
            self.assertFalse(res["interpretable"])
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as r2:   # C-1 recomputed does not hold
            run, counts, order = self._setup(d)
            write_run2_dir(r2, kingston()["snap"], kingston()["comps"])           # a "run 2" that equals the new model
            with _Patch(ghz3_run, RUN2_KNOWN=None):
                res = self._analyse(d, run, write=False, run2_dir=r2)
            self.assertFalse(self._k3(res)["c1_recomputed_holds"])
            self.assertFalse(res["interpretable"])
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as code:
            run, counts, order = self._setup(d)
            for name in ghz3_run.CODE_IDENTITY_FILES:                              # a code folder that differs from run 2's
                with open(os.path.join(code, name), "w") as fh:
                    fh.write("different")
            res = self._analyse(d, run, write=False, code_dir=code)
            self.assertFalse(self._k3(res)["core_and_study_sha256_equal_run2_frozen"])
            self.assertFalse(res["interpretable"])
        with tempfile.TemporaryDirectory() as d:                                    # a tampered count total
            run, counts, order = self._setup(d)
            counts["GHZ4_POP"]["meas"]["0000"] += 1
            with open(os.path.join(run, "counts.json"), "w") as fh:
                json.dump({"job_id": "SIMULATED", "order": order, "circuits": counts}, fh)
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["count_totals_equal_shots"])
            self.assertFalse(res["interpretable"])

    def test_log_prefix_item(self):
        log = [{"utc": "20261120T070000Z", "mode": "dry-run", "exit_code": 0, "attempt": None, "predictions_sha256": None},
               {"utc": "20261120T071000Z", "mode": "dry-run", "exit_code": 5, "attempt": None, "predictions_sha256": None}]
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d, log=log)
            ghz3_run.append_log(d, {"utc": "20261120T080000Z", "mode": "submit-accepted", "exit_code": 0, "attempt": True})
            res = self._analyse(d, run, write=False)
            self.assertTrue(self._k3(res)["log_prefix_recorded_in_job_unchanged"])        # lines after the anchor are fine
            lp = os.path.join(run, "dryrun_log.jsonl")
            with open(lp) as fh:
                text = fh.read()
            with open(lp, "w") as fh:
                fh.write(text.replace("20261120T070000Z", "20261120T060000Z", 1))        # change a line inside the anchored prefix
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["log_prefix_recorded_in_job_unchanged"])
            self.assertFalse(res["interpretable"])
            self.assertEqual(res["answer"]["answer"], "yorumlanamaz")
            with open(lp, "w") as fh:
                fh.write("")                                                              # the log removed
            self.assertFalse(self._k3(self._analyse(d, run, write=False))["log_prefix_recorded_in_job_unchanged"])

    def test_stopping_rule_deviations_are_reported_in_the_results(self):
        log = [{"utc": "20261120T070000Z", "mode": "dry-run", "exit_code": 0, "attempt": None, "predictions_sha256": None,
                "d7": {"ok": True}, "k2": {"ok": True, "error": None}, "c1": {"satisfied": True}, "c2": None},
               {"utc": "20261120T110000Z", "mode": "submit-accepted", "exit_code": 0, "attempt": True, "predictions_sha256": None}]
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d, log=log)
            res = self._analyse(d, run, write=True)
            self.assertEqual(len(res["dryrun_log"]["stopping_rule"]["deviations_from_the_rule"]), 1)
            with open(os.path.join(d, "RESULTS_GHZ3.md"), encoding="utf-8") as fh:
                md = fh.read()
            self.assertIn("20261120T110000Z", md)
            self.assertIn("without a passing --submit within 2 hours", md)

    def test_post_anchor_line_dated_before_the_submission_is_a_k3_failure(self):
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d)
            ghz3_run.append_log(d, {"utc": "20261120T080000Z", "mode": "dry-run", "attempt": None})       # at the submission: fine
            res = self._analyse(d, run, write=False)
            self.assertTrue(self._k3(res)["log_post_anchor_lines_not_before_submission"])
            self.assertTrue(res["controls"]["K3"]["pass"])
            ghz3_run.append_log(d, {"utc": "20261120T075959Z", "mode": "dry-run", "attempt": None})       # one second earlier
            res = self._analyse(d, run, write=True)
            self.assertFalse(self._k3(res)["log_post_anchor_lines_not_before_submission"])
            self.assertTrue(self._k3(res)["log_prefix_recorded_in_job_unchanged"])                        # the prefix is intact
            self.assertFalse(res["interpretable"])
            self.assertEqual(res["answer"]["answer"], "yorumlanamaz")
            with open(os.path.join(d, "RESULTS_GHZ3.md"), encoding="utf-8") as fh:
                self.assertIn("Post-anchor lines dated not before the submission: False", fh.read())

    def test_deviations_come_from_the_anchored_lines_plus_the_accepted_line_only(self):
        dry = _L("dry-run", "20261120T070000Z", d7=True, k2=True, c1=True, c2=None)
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d, log=[dry])                                                 # anchored: one binding dry run
            ghz3_run.append_log(d, _L("submit-accepted", "20261120T083000Z"))                                # within 2 h of the dry run
            ghz3_run.append_log(d, _L("dry-run", "20261120T120000Z"))                                        # later, binding, unfollowed: ignored
            ghz3_run.append_log(d, _L("submit-refused", "20261120T121000Z", 5, c1=False))                    # ignored
            ghz3_run.append_log(d, _L("submit-refused", "20261120T122000Z", 5, c1=False))                    # ignored
            res = self._analyse(d, run, write=False)
            sr = res["dryrun_log"]["stopping_rule"]
            self.assertEqual(sr["deviations_from_the_rule"], [])
            self.assertEqual(sr["n_lines"], 2)                                                              # the dry run + the accepted line
            self.assertEqual(sr["n_post_anchor_lines_not_used_for_deviations"], 4)                           # fetch + 3 later lines
            self.assertEqual(len(res["dryrun_log"]["lines"]), 6)                                             # but every line is listed
        with tempfile.TemporaryDirectory() as d:                                                            # no accepted line: the dry run is unfollowed
            run, counts, order = self._setup(d, log=[dry])
            sr = self._analyse(d, run, write=False)["dryrun_log"]["stopping_rule"]
            self.assertEqual(len(sr["deviations_from_the_rule"]), 1)

    def test_c1_pass_c2_fail_lines_are_listed_in_the_markdown(self):
        log = [_L("dry-run", "20261120T070000Z", 6, c2=False, quota=100.0), _L("dry-run", "20261120T071000Z", 0, c2=True, quota=400.0),
               _L("submit-accepted", "20261120T072000Z")]
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d, log=log)
            res = self._analyse(d, run, write=True)
            self.assertEqual([x["quota_seconds"] for x in res["dryrun_log"]["stopping_rule"]["c1_pass_c2_fail"]], [100.0])
            with open(os.path.join(d, "RESULTS_GHZ3.md"), encoding="utf-8") as fh:
                md = fh.read()
            self.assertIn("Logged lines with C-1 passed and C-2 failed: dry-run at 20261120T070000Z (quota 100.0 s, estimate 187.0 s)", md)

    # ---- the first logged fetch (K3)
    def test_the_first_logged_fetch_must_exist_with_its_hash(self):
        K = "first_logged_fetch_file_exists_and_hash_matches"
        with tempfile.TemporaryDirectory() as d:                                   # no fetch logged, no file
            run, counts, order = self._setup(d, exec_info=False)
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)[K])
            self.assertFalse(res["interpretable"])
            self.assertEqual(res["answer"]["answer"], "yorumlanamaz")
            self.assertEqual(res["predictions_in_use"]["execution_calibration"]["status"], "unavailable")
        with tempfile.TemporaryDirectory() as d:                                   # a file that was never logged does not count
            run, counts, order = self._setup(d, exec_info=False)
            with open(os.path.join(run, self.EXEC_NAME), "w") as fh:
                json.dump(self.DEFAULT_EXEC, fh)
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)[K])
            self.assertEqual(res["predictions_in_use"]["execution_calibration"]["status"], "unavailable")
        with tempfile.TemporaryDirectory() as d:                                   # the file changed after it was logged
            run, counts, order = self._setup(d)
            with open(os.path.join(run, self.EXEC_NAME), "a") as fh:
                fh.write(" ")
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)[K])
            self.assertFalse(res["dryrun_log"]["first_logged_fetch"]["ok"])
            self.assertFalse(res["interpretable"])
        with tempfile.TemporaryDirectory() as d:                                   # the logged file was removed
            run, counts, order = self._setup(d)
            os.remove(os.path.join(run, self.EXEC_NAME))
            self.assertFalse(self._k3(self._analyse(d, run, write=False))[K])

    def test_the_calibration_used_is_the_first_logged_fetch_not_the_first_file_by_name(self):
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d, exec_info=False)
            late = "execution_calibration_20261121T090000Z.json"                  # logged FIRST, sorts second
            early = "execution_calibration_20261120T090000Z.json"                 # logged second, sorts first
            self._put_exec(d, run, self._changed_info(), name=late, utc="20261121T090000Z")
            self._put_exec(d, run, None, name=early, utc="20261122T090000Z")
            res = self._analyse(d, run, write=False)
            ex = res["predictions_in_use"]["execution_calibration"]
            self.assertEqual(ex["attempt_used"], late)
            self.assertEqual(res["predictions_in_use"]["source"], "execution-time calibration")
            self.assertEqual(res["dryrun_log"]["first_logged_fetch"]["file"], late)
            self.assertTrue(res["controls"]["K3"]["pass"], res["controls"]["K3"])
        with tempfile.TemporaryDirectory() as d:                                   # the second attempt would change the result: ignored
            run, counts, order = self._setup(d)                                   # first: nothing retrieved
            self._put_exec(d, run, self._changed_info(), name="execution_calibration_20261121T090000Z.json", utc="20261121T090000Z")
            res = self._analyse(d, run, write=False)
            self.assertEqual(res["predictions_in_use"]["execution_calibration"]["attempt_used"], self.EXEC_NAME)
            self.assertEqual(res["predictions_in_use"]["source"], "snapshot")
            self.assertEqual(res["dryrun_log"]["first_logged_fetch"]["n_logged_fetches"], 2)

    # ---- the job's creation and start times (K3)
    def test_job_time_status_unit(self):
        st = ghz3_analyze.job_time_status
        sub = "20261120T080000Z"
        ok = {"created": "2026-11-20T08:00:00.000Z", "running": "2026-11-20T08:30:15.500Z"}
        self.assertTrue(st(ok, sub)["ok"])                                                       # created exactly at the submission
        self.assertTrue(st(dict(ok, created="2026-11-20T07:59:59Z"), sub)["ok"])                 # a second early: clock tolerance
        self.assertTrue(st(dict(ok, created="2026-11-20T07:50:00Z"), sub)["ok"])                 # exactly 10 minutes early: allowed
        self.assertTrue(st(dict(ok, running="2026-11-20T07:50:00Z"), sub)["ok"])
        self.assertFalse(st(dict(ok, created="2026-11-20T07:49:59Z"), sub)["ok"])                # 10 minutes and a second early
        self.assertFalse(st(dict(ok, running="2026-11-20T07:49:59Z"), sub)["ok"])
        self.assertEqual(ghz3_run.CLOCK_TOLERANCE_SECONDS, 600)
        self.assertFalse(st({}, sub)["ok"])                                                      # both missing
        self.assertFalse(st(None, sub)["ok"])
        self.assertFalse(st({"finished": "2026-11-20T09:00:00Z"}, sub)["ok"])
        one = st({"created": "2026-11-20T08:00:05Z"}, sub)                                       # one missing: the other decides
        self.assertTrue(one["ok"])
        self.assertIsNotNone(one["reason"])
        self.assertTrue(st({"running": "2026-11-20T08:30:00Z"}, sub)["ok"])
        self.assertFalse(st({"created": "2026-11-20T07:00:00Z"}, sub)["ok"])
        self.assertTrue(st({"created": "2026-11-20T07:50:00Z"}, sub)["ok"])
        self.assertFalse(st({"running": "2026-11-20T07:49:59Z"}, sub)["ok"])
        self.assertTrue(st({"created": "2026-11-20T08:00:05Z", "started": "2026-11-20T08:10:00Z"}, sub)["ok"])   # the 'started' alias
        self.assertFalse(st(ok, "garbage")["ok"])                                                # unreadable submission time
        self.assertEqual(st(ok, sub)["created"], "2026-11-20T08:00:00+00:00")

    def test_job_time_is_a_k3_item(self):
        K = "job_created_and_started_after_submission"
        ts = dict(METRICS["timestamps"])
        for stamps, expect in ((ts, True), ({}, False), (dict(ts, created="2026-11-20T07:00:00Z"), False),
                               (dict(ts, running="2026-11-20T07:00:00Z"), False),
                               ({"running": ts["running"]}, True), ({"created": ts["created"]}, True)):
            with tempfile.TemporaryDirectory() as d:
                info = dict(self.DEFAULT_EXEC, timestamps=stamps)
                run, counts, order = self._setup(d, exec_info=info)
                res = self._analyse(d, run, write=False)
                self.assertEqual(self._k3(res)[K], expect, stamps)
                self.assertEqual(res["interpretable"], expect, stamps)
        with tempfile.TemporaryDirectory() as d:                                   # no saved metrics at all (the fetch could not read them)
            info = {"available": False, "error": "RuntimeError", "current": None, "current_error": "RuntimeError"}
            run, counts, order = self._setup(d, exec_info=info)
            self.assertFalse(self._k3(self._analyse(d, run, write=False))[K])

    # ---- T7: the environment of the power file
    def test_the_power_environment_is_compared_and_a_version_mismatch_is_reported_as_the_cause(self):
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d)
            with open(os.path.join(run, "power_run3.json")) as fh:
                self.assertEqual(json.load(fh)["environment"], ghz3_run.environment_info())
            res = self._analyse(d, run, write=True)
            self.assertEqual(res["power_at_submission"]["environment"]["differs"], {})
            self.assertTrue(self._k3(res)["power_run3_recomputation_equal"])
        with tempfile.TemporaryDirectory() as d:                                   # other versions, the same numbers: reported, K3 holds
            run, counts, order = self._setup(d)
            _rewrite_hash_power(run, lambda pw: pw["environment"].update(numpy="0.0.1"))
            res = self._analyse(d, run, write=True)
            self.assertEqual(list(res["power_at_submission"]["environment"]["differs"]), ["numpy"])
            self.assertTrue(self._k3(res)["power_run3_recomputation_equal"])
            self.assertTrue(res["controls"]["K3"]["pass"])
            with open(os.path.join(d, "RESULTS_GHZ3.md"), encoding="utf-8") as fh:
                self.assertIn("DIFFERS: numpy: 0.0.1 -> ", fh.read())
        with tempfile.TemporaryDirectory() as d:                                   # other versions AND other numbers: K3 fails, the cause named
            run, counts, order = self._setup(d)
            _rewrite_hash_power(run, lambda pw: (pw["environment"].update(numpy="0.0.1", platform="elsewhere"), pw["power"].update(H1=0.5)))
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["power_run3_recomputation_equal"])
            self.assertFalse(res["interpretable"])
            reasons = " | ".join(res["power_at_submission"]["status"])
            self.assertIn("version mismatch", reasons)
            self.assertIn("numpy: 0.0.1 ->", reasons)
            self.assertIn("platform: elsewhere ->", reasons)
        with tempfile.TemporaryDirectory() as d:                                   # other numbers in the SAME environment: no version-mismatch claim
            run, counts, order = self._setup(d)
            _rewrite_hash_power(run, lambda pw: pw["power"].update(H1=0.5))
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["power_run3_recomputation_equal"])
            self.assertNotIn("version mismatch", " | ".join(res["power_at_submission"]["status"]))
        with tempfile.TemporaryDirectory() as d:                                   # a file without an environment record (older runner)
            run, counts, order = self._setup(d)
            _rewrite_hash_power(run, lambda pw: pw.pop("environment"))
            res = self._analyse(d, run, write=False)
            self.assertTrue(self._k3(res)["power_run3_recomputation_equal"])        # numbers equal: nothing else is claimed

    # ---- the power file (K3 and the readings)
    def test_power_file_k3_items(self):
        with tempfile.TemporaryDirectory() as d:                                   # missing
            run, counts, order = self._setup(d, with_power=False)
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["power_run3_exists_and_hash_matches_job"])
            self.assertIsNone(res["readings"]["H1_small_n_accuracy"])
            self.assertIsNone(res["readings"]["H4_overprediction_every_n"])
            self.assertIsNone(res["power_at_submission"]["power"])
            self.assertFalse(res["interpretable"])
            self.assertEqual(res["answer"]["answer"], "yorumlanamaz")
        with tempfile.TemporaryDirectory() as d:                                   # hash differs from job.json's
            run, counts, order = self._setup(d)
            with open(os.path.join(run, "power_run3.json"), "a") as fh:
                fh.write(" ")
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["power_run3_exists_and_hash_matches_job"])
            self.assertIsNone(res["readings"]["H1_small_n_accuracy"])
            self.assertFalse(res["interpretable"])
        with tempfile.TemporaryDirectory() as d:                                   # a data-file hash that differs from certs/power.json
            run, counts, order = self._setup(d)
            _rewrite_hash_power(run, lambda pw: pw["inputs"][0].__setitem__("sha256", "0" * 64))
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["power_run3_input_hashes_match_frozen"])
            self.assertFalse(res["interpretable"])
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as certs:       # certs/power.json says something else
            run, counts, order = self._setup(d)
            shutil.copy(os.path.join(HERE, "certs", "k2_sim.json"), certs)
            with open(os.path.join(HERE, "certs", "power.json")) as fh:
                frozen = json.load(fh)
            frozen["inputs"][0]["sha256"] = "1" * 64
            with open(os.path.join(certs, "power.json"), "w") as fh:
                json.dump(frozen, fh)
            res = self._analyse(d, run, write=False, certs_dir=certs)
            self.assertFalse(self._k3(res)["power_run3_input_hashes_match_frozen"])
        with tempfile.TemporaryDirectory() as d:                                   # a study-file hash that differs from FREEZE_GHZ3.json
            run, counts, order = self._setup(d)
            with open(os.path.join(d, "FREEZE_GHZ3.json"), "w") as fh:
                json.dump({"files": {"ghz2_study.py": "2" * 64, "ghz3_study_h4.py": core.sha256_file(os.path.join(HERE, "ghz3_study_h4.py"))}}, fh)
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["power_run3_input_hashes_match_frozen"])
        with tempfile.TemporaryDirectory() as d:                                   # no FREEZE_GHZ3.json at all
            run, counts, order = self._setup(d, manifest=False)
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["power_run3_input_hashes_match_frozen"])
        with tempfile.TemporaryDirectory() as d:                                   # a changed number: the recomputation differs
            run, counts, order = self._setup(d)
            _rewrite_hash_power(run, lambda pw: pw["power"].update({"H1": 0.5}))
            res = self._analyse(d, run, write=False)
            self.assertTrue(self._k3(res)["power_run3_exists_and_hash_matches_job"])
            self.assertTrue(self._k3(res)["power_run3_input_hashes_match_frozen"])
            self.assertFalse(self._k3(res)["power_run3_recomputation_equal"])
            self.assertIsNone(res["readings"]["H1_small_n_accuracy"])
            self.assertFalse(res["interpretable"])
        with tempfile.TemporaryDirectory() as d:                                   # predictions that are not the snapshot's
            run, counts, order = self._setup(d)
            _rewrite_hash_power(run, lambda pw: pw["predictions"]["F_pred"].update({"16": 0.1}))
            res = self._analyse(d, run, write=False)
            self.assertFalse(self._k3(res)["power_run3_input_hashes_match_frozen"])
            self.assertFalse(self._k3(res)["power_run3_recomputation_equal"])
        with tempfile.TemporaryDirectory() as d:                                   # a file computed with another n_datasets
            run, counts, order = self._setup(d)
            res = self._analyse(d, run, write=False, power_n_datasets=self.POWER_N + 1)
            self.assertFalse(self._k3(res)["power_run3_recomputation_equal"])

    def test_power_recomputation_default_is_the_registered_2000_datasets(self):
        import inspect
        self.assertIsNone(inspect.signature(ghz3_analyze.run_analysis).parameters["power_n_datasets"].default)
        self.assertEqual(ghz3_run.POWER_DATASETS, 2000)
        self.assertEqual(ghz3_run.POWER_SEED, 20261116)

    def test_readings_use_the_submission_power_at_the_threshold(self):
        with _Patch(ghz3_analyze, _close=lambda a, b, tol=1e-9: True):             # only the readings are under test here
            for h1p, h4p, e1, e4 in ((0.79, 0.8, "not demonstrated", "fails"), (0.8, 0.1, "fails", "not demonstrated")):
                with tempfile.TemporaryDirectory() as d:
                    run, counts, order = self._setup(d)
                    _rewrite_hash_power(run, lambda pw: pw["power"].update({"H1": h1p, "H4": h4p}))
                    res = self._analyse(d, run, write=False)
                    self.assertTrue(res["controls"]["K3"]["pass"], res["controls"]["K3"])
                    self.assertEqual(res["readings"]["H1_small_n_accuracy"], e1)
                    self.assertEqual(res["readings"]["H4_overprediction_every_n"], e4)
                    self.assertEqual(res["answer"]["q1"], ghz3_analyze.Q1_SENTENCES[("FAILS", e1)])
                    self.assertEqual(res["answer"]["q2"], ghz3_analyze.Q2_SENTENCES[("FAILS", e4)])

    # ---- K2
    def test_k2_design_check_missing_or_binding_failing_makes_the_result_uninterpretable(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as certs:
            run, counts, order = self._setup(d)
            shutil.copy(os.path.join(HERE, "certs", "power.json"), certs)
            res = self._analyse(d, run, write=False, certs_dir=certs)             # no certs/k2_sim.json
            self.assertFalse(res["controls"]["K2"]["design_check"]["pass"])
            self.assertTrue(res["controls"]["K2"]["binding"]["pass"])
            self.assertFalse(res["controls"]["K2"]["pass"])
            self.assertFalse(res["interpretable"])
            self.assertEqual(res["answer"]["answer"], "yorumlanamaz")
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d)
            res = self._analyse(d, run, write=False, k2_stub=lambda entries: {"pass": False, "detail": {}})
            self.assertTrue(res["controls"]["K2"]["design_check"]["pass"])
            self.assertFalse(res["controls"]["K2"]["binding"]["pass"])
            self.assertFalse(res["interpretable"])
            self.assertEqual(res["answer"]["answer"], "yorumlanamaz")
        with tempfile.TemporaryDirectory() as d:

            def boom(entries):
                raise RuntimeError("simulator failed")
            run, counts, order = self._setup(d)
            res = self._analyse(d, run, write=True, k2_stub=boom)
            self.assertFalse(res["controls"]["K2"]["binding"]["pass"])
            self.assertEqual(res["controls"]["K2"]["binding"]["error"], "RuntimeError")
            self.assertFalse(res["interpretable"])

    def test_k2_binding_runs_on_the_submitted_circuits(self):
        k = kingston()
        t0 = time.time()
        out = ghz3_analyze.k2_noiseless(k["entries"])
        self.assertTrue(out["pass"], out)
        self.assertEqual(set(out["detail"]["F_sim"]), {str(n) for n in core.GRID})
        self.assertEqual(set(out["detail"]["C_mix_sim"]), {"8", "32"})
        self.assertTrue(all(v >= 0.98 for v in out["detail"]["F_sim"].values()))
        self.assertTrue(all(v <= 0.05 for v in out["detail"]["C_mix_sim"].values()))
        self.assertLess(time.time() - t0, 300)

    # ---- C-1 per question
    def test_q1_replicate_label_when_the_small_n_predictions_moved_by_less_than_0_02(self):
        k = kingston()
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as r2:
            run, counts, order = self._setup(d)
            comps2 = copy.deepcopy(k["comps"])
            comps2["16"]["F_pred"] -= 0.03                                         # run 2's n = 4, 8 predictions equal the new ones
            write_run2_dir(r2, k["snap"], comps2)
            with _Patch(ghz3_run, RUN2_KNOWN=None):
                res = self._analyse(d, run, write=True, run2_dir=r2)
            q1 = res["q1_per_question"]
            self.assertFalse(q1["model_test"])
            self.assertEqual(q1["max_abs_dF_4_8_snapshot"], 0.0)
            self.assertTrue(q1["replicate_label_attached"])
            self.assertIn(ghz3_run.Q1_LABEL, [x["label"] for x in res["answer"]["labels"]])
            self.assertIn({"label": ghz3_run.Q1_LABEL, "applies_to": "Q1"}, res["answer"]["labels"])
            with open(os.path.join(d, "RESULTS_GHZ3.md"), encoding="utf-8") as fh:
                self.assertIn(ghz3_run.Q1_LABEL, fh.read())

    def test_q1_snapshot_and_in_use_values_are_both_reported(self):
        k = kingston()
        snap2 = copy.deepcopy(k["snap"])
        for q in k["comps"]["48"]["S"]:
            snap2["qubits"][q]["measure"]["error"] *= 2.0                           # moves F_pred at every n
        dates = ghz3_run.calibration_dates(FakeKingston().properties())
        for q in k["comps"]["48"]["S"]:
            dates["qubits"][str(q)]["readout_error"] = "2026-06-01T00:00:00+00:00"
        info = {"available": True, "error": None, "snapshot": snap2, "snapshot_sha256": core.snapshot_hash(snap2), "dates": dates,
                "execution_start_utc": "20261120T083015Z", "execution_start_iso": "2026-11-20T08:30:15.500000+00:00",
                "timestamps": METRICS["timestamps"], "usage": METRICS["usage"], "job_usage_seconds": 190.5,
                "current": None, "current_error": None}
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d, exec_info=info)
            res = self._analyse(d, run, write=False)
            q1 = res["q1_per_question"]
            self.assertTrue(q1["in_use_differs_from_snapshot"])
            self.assertNotEqual(q1["max_abs_dF_4_8_in_use"], q1["max_abs_dF_4_8_snapshot"])

    # ---- the calibration in force at execution
    def test_execution_time_calibration_changes_the_predictions_in_use(self):
        k = kingston()
        snap2 = copy.deepcopy(k["snap"])
        for q in k["comps"]["48"]["S"]:
            snap2["qubits"][q]["t2"] *= 0.5
        dates = ghz3_run.calibration_dates(FakeKingston().properties())
        for q in k["comps"]["48"]["S"]:
            dates["qubits"][str(q)]["T2"] = "2026-06-01T00:00:00+00:00"           # recalibrated after the submission snapshot
        info = {"available": True, "error": None, "snapshot": snap2, "snapshot_sha256": core.snapshot_hash(snap2), "dates": dates,
                "execution_start_utc": "20261120T083015Z", "execution_start_iso": "2026-11-20T08:30:15.500000+00:00",
                "timestamps": METRICS["timestamps"], "usage": METRICS["usage"], "job_usage_seconds": 190.5,
                "current": None, "current_error": None}
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d, exec_info=info)
            res = self._analyse(d, run, write=False)
            self.assertEqual(res["predictions_in_use"]["source"], "execution-time calibration")
            labels = [x["label"] for x in res["answer"]["labels"]]
            self.assertIn("calibration changed before execution", labels)
            self.assertNotIn("execution-time calibration not verified", labels)
            for t in res["table"]:
                self.assertIn("F_pred_snapshot_secondary", t)
            i = list(core.GRID).index(48)
            self.assertLess(res["table"][i]["F_pred"], res["table"][i]["F_pred_snapshot_secondary"])
            self.assertAlmostEqual(res["table"][i]["F_pred_snapshot_secondary"], k["model"][48]["F_pred"], places=12)
            self.assertIsNotNone(res["criteria_secondary_snapshot_predictions"])
            self.assertTrue(res["controls"]["K3"]["pass"], res["controls"]["K3"])           # K3 is about the snapshot's own model
            # the readings still use the submission power (computed on the snapshot's predictions)
            self.assertEqual(res["power_at_submission"]["checks"], {"exists_hash": True, "inputs": True, "recompute": True})
        info["dates"] = ghz3_run.calibration_dates(FakeKingston().properties())            # the same values but no later date
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d, exec_info=info)
            res = self._analyse(d, run, write=False)
            self.assertEqual(res["predictions_in_use"]["source"], "snapshot")
            self.assertIn("execution-time calibration not verified", [x["label"] for x in res["answer"]["labels"]])
            self.assertIsNone(res["criteria_secondary_snapshot_predictions"])
        info2 = {"available": False, "error": "NotImplementedError", "current_error": None, "timestamps": METRICS["timestamps"],
                 "current": {"retrieved_utc": "20261120T090000Z", "snapshot": copy.deepcopy(k["snap"]),
                             "snapshot_sha256": None, "dates": ghz3_run.calibration_dates(FakeKingston().properties())}}
        info2["current"]["snapshot"]["utc"] = "20261120T090000Z"
        info2["current"]["snapshot_sha256"] = core.snapshot_hash(info2["current"]["snapshot"])
        with tempfile.TemporaryDirectory() as d:                                          # the fallback: verified by the dates
            run, counts, order = self._setup(d, exec_info=info2)
            res = self._analyse(d, run, write=True)
            labels = [x["label"] for x in res["answer"]["labels"]]
            self.assertIn("verified: no recalibration since submission", labels)
            self.assertNotIn("execution-time calibration not verified", labels)
            self.assertEqual(res["predictions_in_use"]["source"], "snapshot")
            self.assertTrue(res["controls"]["K3"]["pass"])
            with open(os.path.join(d, "RESULTS_GHZ3.md"), encoding="utf-8") as fh:
                self.assertIn("verified", fh.read())

    def test_rule14_failure_attaches_h1_one_sided(self):
        with tempfile.TemporaryDirectory() as d:
            run, counts, order = self._setup(d)
            bad = {"F_pred": {"4": 0.97, "8": 0.9}, "band": 0.05, "ok": False}
            with _Patch(ghz3_run, rule14_check=lambda comps: bad):
                res = self._analyse(d, run, write=False)
            self.assertFalse(res["c1"]["rule14_recheck"]["ok"])
            self.assertIn("H1 one-sided", [x["label"] for x in res["answer"]["labels"]])

    def test_run1_fallback_is_labelled(self):
        table = [{"n": n, "F": 0.5, "C": 0.5, "F_pred": 0.6, "R": 0.8} for n in core.GRID]
        with tempfile.TemporaryDirectory() as empty:
            out = ghz3_analyze.comparison_with_earlier_runs(table, run1_dir=empty, run2_dir=empty)
        self.assertIn("QUOTED", out["run1_source"])
        self.assertEqual({r["n"]: r["R_run1"] for r in out["R_table"] if r["R_run1"] is not None}, ghz3_analyze.RUN1_QUOTED_R)
        self.assertTrue(all(r["R_run2"] is None for r in out["R_table"]))

    def test_tracking_table(self):
        f_hat, f_boot, f_pred = np.full(6, 0.5), np.full((100, 6), 0.5), np.full(6, 0.5)
        tr = ghz3_analyze.tracking_table(f_hat, f_boot, f_pred, sigma_dF=np.full(6, 0.01))
        z = np.load(os.path.join(RUN2, "RESULTS_GHZ2_boot.npz"))
        self.assertAlmostEqual(tr["rows"][0]["measured_change"], 0.5 - z["F_hat"][0], places=12)
        self.assertAlmostEqual(tr["rows"][0]["predicted_change"], 0.5 - z["F_pred"][0], places=12)
        self.assertEqual(tr["rows"][0]["sigma_d_F"], 0.01)
        self.assertEqual(tr["ci_kind"], "shot noise only")
        self.assertFalse(ghz3_analyze.tracking_table(f_hat, f_boot, f_pred, run2_dir=tempfile.gettempdir() + "/none")["available"])


# -------------------------------------------------------------------------------------------------------------- selftest
class TestSelftest(unittest.TestCase):
    def test_selftest_path(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = ghz3_run.main(["--selftest"])
        self.assertEqual(code, 0, buf.getvalue()[-600:])
        self.assertIn("code identity with run 2's frozen values: OK", buf.getvalue())
        self.assertIn("C-1 (v3) logic", buf.getvalue())
        self.assertIn("power function", buf.getvalue())
        self.assertIn("[selftest] OK", buf.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=1)

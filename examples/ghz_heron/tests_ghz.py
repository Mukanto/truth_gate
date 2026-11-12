"""tests_ghz.py -- offline unit tests of the GHZ-on-Heron study code (PREREG.md sections 3-8).

Run:  <venv python> tests_ghz.py        (FakeKingston and toy targets only; no network, no account)
"""
import hashlib
import io
import json
import math
import os
import tempfile
import unittest

import numpy as np
from qiskit import QuantumCircuit, qpy
from qiskit_ibm_runtime.fake_provider import FakeKingston

import ghz_analyze
import ghz_core as core
import ghz_run
import ghz_study


# ------------------------------------------------------------------------------------------------------------ helpers
def toy_snapshot(nq=5, edges=None, t2=1e-4, ro=0.01, e_cz=0.01, e_sx=0.001, faulty=(), missing_ro=(), bad_edges=()):
    """Line 0-1-...-(nq-1) toy device in the snapshot schema (dt = 1 ns; sx 40 ns, cz 100 ns, measure 1 us)."""
    if edges is None:
        edges = [(i, i + 1) for i in range(nq - 1)]
    qubits = []
    for q in range(nq):
        qubits.append({
            "t1": 2e-4, "t2": t2, "operational": q not in faulty,
            "measure": {"error": None if q in missing_ro else ro, "duration": 1e-6},
            "sx": {"error": e_sx, "duration": 40e-9},
            "x": {"error": e_sx, "duration": 40e-9},
        })
    ed = []
    for a, b in edges:
        err = 0.6 if (a, b) in bad_edges else e_cz
        ed.append([a, b, err, 100e-9])
        ed.append([b, a, err, 100e-9])
    return {
        "schema": core.SNAPSHOT_SCHEMA, "backend": "toy", "num_qubits": nq, "dt": 1e-9, "utc": "T", "processor_type": None,
        "rep_delay": None, "timing": {"granularity": 1, "min_length": 1, "pulse_alignment": 1, "acquire_alignment": 1},
        "faulty_qubits": sorted(faulty), "faulty_gates": [], "qubits": qubits, "edges": sorted(ed),
    }


def ideal_counts(n, family, shots=2000, loss=0.0):
    """Analytic noiseless counts of GHZ_n (family 'GHZ') or of its classical mixture twin ('MIX'), keys = data bitstrings.
    ``loss`` moves that fraction of the population shots to a non-GHZ outcome (a crude stand-in for device noise)."""
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


def all_ideal_counts(mix_loss=0.0):
    out = {}
    for n in core.GRID:
        out.update(ideal_counts(n, "GHZ"))
    for n in core.MIX_NS:
        out.update(ideal_counts(n, "MIX", loss=mix_loss))
    return out


_KINGSTON = {}


def kingston():
    if not _KINGSTON:
        b = FakeKingston()
        snap, h = core.snapshot_from_backend(b, utc="TEST")
        _KINGSTON.update(backend=b, snap=snap, hash=h)
    return _KINGSTON


# ---------------------------------------------------------------------------------------------------------- selection
class TestSelection(unittest.TestCase):
    def test_line_graph(self):
        snap = toy_snapshot(5)
        adj = core.operational_graph(snap)
        self.assertEqual(core.select_root(adj), 2)
        S, T, parents = core.selection(snap, 4)
        self.assertEqual(S, [2, 1, 3, 0])                    # BFS, ascending neighbours
        self.assertEqual(T, [(2, 1), (2, 3), (1, 0)])
        self.assertEqual(parents, [None, 0, 0, 1])

    def test_exclusions(self):
        # faulty qubit 2 splits the line into {0,1} and {3,4}: equal sizes -> lowest-index component; tie on closeness -> 0
        snap = toy_snapshot(5, faulty=(2,))
        adj = core.operational_graph(snap)
        self.assertNotIn(2, adj)
        self.assertEqual(core.select_root(adj), 0)
        # missing readout error excludes the qubit; an edge with error >= 0.5 is removed
        self.assertNotIn(3, core.operational_graph(toy_snapshot(5, missing_ro=(3,))))
        self.assertNotIn(2, core.operational_graph(toy_snapshot(5, bad_edges=((1, 2),)))[1])
        snap = toy_snapshot(5)
        snap["qubits"][4]["t2"] = None
        self.assertNotIn(4, core.operational_graph(snap))
        with self.assertRaises(ValueError):
            core.selection(toy_snapshot(5), 6)

    def test_determinism_on_kingston(self):
        k = kingston()
        a = core.selection(k["snap"], 48)
        b = core.selection(core.snapshot_from_backend(FakeKingston(), utc="TEST")[0], 48)
        self.assertEqual(a, b)
        S, T, _ = a
        self.assertEqual(len(set(S)), 48)
        self.assertEqual(core.selection(k["snap"], 8)[0], S[:8])       # S_n is a prefix of the BFS order
        self.assertEqual(core.snapshot_from_backend(FakeKingston(), utc="TEST")[1], k["hash"])


# ---------------------------------------------------------------------------------------------------------- integrity
class TestIntegrity(unittest.TestCase):
    def test_good_and_routed(self):
        snap = toy_snapshot(5)
        tg = core.target_from_snapshot(snap)
        S, T, parents = core.selection(snap, 3)
        qc = core.build_circuit(3, parents, "POP")
        tc = core.transpile_checked(qc, 3, S, T, tg)
        self.assertEqual(sum(1 for i in tc.data if i.operation.num_qubits == 2), 2)
        # a layout that forces routing must raise
        with self.assertRaises(core.IntegrityError):
            core.transpile_checked(qc, 3, [0, 2, 4], [(0, 2), (0, 4)], tg)
        # a circuit with an extra two-qubit gate is rejected by the assert itself
        bad = QuantumCircuit(5, name="bad")
        bad.cz(2, 1); bad.cz(2, 3); bad.cz(1, 0)
        with self.assertRaises(core.IntegrityError):
            core.check_integrity(bad, 3, S, T)

    def test_budget_on_kingston(self):
        k = kingston()
        entries = core.build_all(k["snap"], k["backend"].target)
        self.assertEqual(len(entries), core.EXPECTED_CIRCUITS)
        self.assertEqual(len(entries) * core.SHOTS, core.EXPECTED_SHOTS)
        mix = [e for e in entries if e["family"] == "MIX"]
        self.assertEqual(len(mix), 2 + 84)
        self.assertTrue(all([r.name for r in e["circuit"].cregs] == ["meas", "mid"] for e in mix))
        self.assertTrue(all(sum(1 for i in e["circuit"].data if i.operation.num_qubits == 2) == e["n"] - 1 for e in entries))


# --------------------------------------------------------------------------------------------------------- estimators
class TestEstimators(unittest.TestCase):
    def test_ideal_ghz_gives_F_one(self):
        for n in (4, 8):
            est = core.point_estimates(ideal_counts(n, "GHZ", shots=200000), n, "GHZ")
            self.assertAlmostEqual(est["P"], 1.0)
            self.assertAlmostEqual(est["C"], 1.0, places=2)
            self.assertAlmostEqual(est["F"], 1.0, places=2)

    def test_classical_mixture_has_no_coherence(self):
        est = core.point_estimates(ideal_counts(8, "MIX"), 8, "MIX")
        self.assertAlmostEqual(est["P"], 1.0)
        self.assertAlmostEqual(est["C"], 0.0, places=12)
        self.assertAlmostEqual(est["F"], 0.5, places=12)

    def test_parity_and_population_counting(self):
        self.assertEqual(core.pop_counts({"0000": 3, "1111": 5, "0101": 2}, 4), (3, 5, 2, 10))
        self.assertEqual(core.parity_counts({"0000": 3, "0001": 5, "0111": 2, "0011": 1}), (4, 7, 11))
        self.assertEqual(core.split_registers("1 0101", [("meas", 4), ("mid", 1)]), {"mid": "1", "meas": "0101"})

    def test_bootstrap_shape_and_reproducibility(self):
        counts = all_ideal_counts()
        a = core.analyze_counts(counts, B=60)
        b = core.analyze_counts(counts, B=60)
        self.assertEqual(a["F_boot"].shape, (60, 5))
        self.assertEqual(a["F_hat"].shape, (5,))
        self.assertTrue(np.array_equal(a["F_boot"], b["F_boot"]))
        for n in core.MIX_NS:
            self.assertEqual(a["mix"][n]["C_boot"].shape, (60,))
            self.assertEqual(a["mix"][n]["F_boot"].shape, (60,))
            self.assertLess(a["mix"][n]["C"], 1e-9)
        self.assertTrue(np.all(a["F_lo"] <= a["F_hi"]))


# -------------------------------------------------------------------------------------------------------------- model
class TestModel(unittest.TestCase):
    def setUp(self):
        self.snap = toy_snapshot(3, e_cz=0.02, e_sx=0.001, ro=0.03, t2=1e-6)
        self.tg = core.target_from_snapshot(self.snap)

    def hand_circuit(self):
        qc = QuantumCircuit(3, 3)
        qc.sx(0)
        qc.cz(0, 1)
        qc.cz(1, 2)
        qc.measure([0, 1, 2], [0, 1, 2])
        return qc

    def test_idle_time_hand_computed(self):
        # ALAP: sx0 [0,40], cz01 [40,140], cz12 [140,240], measure at 240 ns.  Qubit 0 idles for cz12 (100 ns); 1 and 2 never.
        idle = core.idle_times(self.hand_circuit(), self.tg, [0, 1, 2])
        np.testing.assert_allclose(idle, [100e-9, 0.0, 0.0], atol=1e-15)

    def test_model_on_toy_target(self):
        comp = core.model_components(self.hand_circuit(), self.tg, [0, 1, 2])
        expected = (1 - 0.02) ** 2 * (1 - 0.03) ** 3 * (1 - 0.001) * math.exp(-100e-9 / 1e-6)
        self.assertAlmostEqual(comp["F_pred"], expected, places=12)
        self.assertEqual(len(comp["cz_err"]), 2)
        self.assertEqual(comp["g1_err"], [0.001])

    def test_target_roundtrip_matches_backend_target(self):
        k = kingston()
        entries = core.build_all(k["snap"], k["backend"].target, grid=(4, 8), mix_ns=())
        m1 = core.model_all(entries, k["backend"].target, grid=(4, 8))
        m2 = core.model_all(entries, core.target_from_snapshot(k["snap"]), grid=(4, 8))
        for n in (4, 8):
            self.assertAlmostEqual(m1[n]["F_pred"], m2[n]["F_pred"], places=12)
            self.assertTrue(0.0 < m1[n]["F_pred"] < 1.0)
        self.assertGreater(m1[4]["F_pred"], m1[8]["F_pred"])

    def test_snapshot_hash_is_content_hash(self):
        snap, h = core.snapshot_from_target(self.tg, "toy", utc="T")
        self.assertEqual(h, hashlib.sha256(core.canonical_json(snap).encode()).hexdigest())
        snap["qubits"][0]["t2"] += 1e-9
        self.assertNotEqual(core.snapshot_hash(snap), h)


# ---------------------------------------------------------------------------------------------------------------- freeze
class TestFreeze(unittest.TestCase):
    def _make(self, d, tamper=False, drop=None):
        files = {}
        for name in core.REQUIRED_FROZEN:
            with open(os.path.join(d, name), "w") as fh:
                fh.write("content of " + name)
            files[name] = core.sha256_file(os.path.join(d, name))
        if drop:
            files.pop(drop)
        with open(os.path.join(d, "FREEZE_GHZ.json"), "w") as fh:
            json.dump({"files": files}, fh)
        if tamper:
            with open(os.path.join(d, "ghz_core.py"), "a") as fh:
                fh.write("x")

    def test_refusal_and_acceptance(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(core.FreezeError):          # absent
                core.verify_freeze(d)
            self._make(d)
            self.assertTrue(core.verify_freeze(d))
        with tempfile.TemporaryDirectory() as d:
            self._make(d, tamper=True)
            with self.assertRaises(core.FreezeError):          # mismatch
                core.verify_freeze(d)
        with tempfile.TemporaryDirectory() as d:
            self._make(d, drop="ghz_core.py")
            with self.assertRaises(core.FreezeError):          # does not cover the study code
                core.verify_freeze(d)

    def test_runner_refuses_before_touching_the_account(self):
        def boom():
            raise AssertionError("QiskitRuntimeService must not be created before the freeze is verified")
        orig = ghz_run._service
        ghz_run._service = boom
        try:
            with tempfile.TemporaryDirectory() as d:
                for mode in (["--dry-run"], ["--submit"], ["--fetch"]):
                    self.assertEqual(ghz_run.main(mode, root=d), 3)
                self.assertEqual(ghz_analyze.main(root=d), 3)
        finally:
            ghz_run._service = orig


# ------------------------------------------------------------------------------------------------------------- criteria
def _data(f_pred, f_hat, noise=0.0, B=200, seed=1):
    rng = np.random.default_rng(seed)
    f_hat = np.array(f_hat, float)
    return {"F_pred": np.array(f_pred, float), "F_hat": f_hat,
            "F_boot": f_hat[None, :] + rng.normal(0, noise, size=(B, 5))}


class TestCriteria(unittest.TestCase):
    P = [0.92, 0.85, 0.72, 0.48, 0.38]

    def test_G1(self):
        self.assertTrue(ghz_study.G1_small_n_accuracy(_data(self.P, [0.92, 0.85, 0.7, 0.4, 0.3])))
        self.assertFalse(ghz_study.G1_small_n_accuracy(_data(self.P, [0.92, 0.70, 0.7, 0.4, 0.3])))       # R(8) = 0.82
        self.assertFalse(ghz_study.G1_small_n_accuracy(_data(self.P, [0.92 * 1.12, 0.85, 0.7, 0.4, 0.3])))  # R(4) = 1.12
        self.assertIsNone(ghz_study.G1_small_n_accuracy(_data([0.0, 0.85, 0.7, 0.4, 0.3], [0.9] * 5)))
        d = _data(self.P, [0.9] * 5)
        d["F_pred"] = d["F_pred"][:4]                                   # wrong shape -> undefined
        self.assertIsNone(ghz_study.G1_small_n_accuracy(d))
        self.assertNotIn("n", _data(self.P, [0.9] * 5))                 # the grid is not data

    def test_G2(self):
        self.assertTrue(ghz_study.G2_excess_decay_grows(_data(self.P, [0.9, 0.82, 0.62, 0.38, 0.22], noise=0.01)))
        self.assertFalse(ghz_study.G2_excess_decay_grows(_data(self.P, [0.644, 0.595, 0.504, 0.336, 0.266], noise=0.01)))
        d = _data(self.P, [0.9, 0.82, 0.62, 0.38, 0.22], noise=0.01)
        d["F_boot"][3, 4] = 0.0                                         # a draw with F(48) = 0 -> undefined
        self.assertIsNone(ghz_study.G2_excess_decay_grows(d))

    def test_G3(self):
        self.assertTrue(ghz_study.G3_gme_reach_matches(_data(self.P, [0.9, 0.82, 0.62, 0.38, 0.22], noise=0.01)))  # 16 == 16
        self.assertFalse(ghz_study.G3_gme_reach_matches(_data(self.P, [0.644, 0.595, 0.504, 0.336, 0.266], noise=0.01)))
        # revision #3: n_pred = 0 (nothing predicted above 1/2) is UNDEFINED, whatever the device does
        self.assertIsNone(ghz_study.G3_gme_reach_matches(_data([0.4] * 5, [0.3] * 5, noise=0.01)))
        self.assertIsNone(ghz_study.G3_gme_reach_matches(_data([0.4] * 5, [0.9] * 5, noise=0.01)))
        # shape checks stay positional
        d = _data(self.P, [0.9, 0.82, 0.62, 0.38, 0.22], noise=0.01)
        d["F_boot"] = d["F_boot"][:, :4]
        self.assertIsNone(ghz_study.G3_gme_reach_matches(d))

    def test_study_worlds_separate_the_criteria(self):
        rng = np.random.default_rng(0)
        plus, minus = ghz_study.plus_world(rng), ghz_study.minus_world(rng)
        for c in ghz_study.STUDY.criteria:
            self.assertTrue(c.fn(plus), c.id)
            self.assertFalse(c.fn(minus), c.id)
        self.assertEqual(plus["F_boot"].shape, (400, 5))
        self.assertEqual(set(plus), {"F_pred", "F_hat", "F_boot"})

    def test_controls_break_their_criteria_on_plus(self):
        crit = {c.id: c.fn for c in ghz_study.STUDY.criteria}
        ctrl = {c.id: c for c in ghz_study.STUDY.controls}
        self.assertEqual({k: v.criteria for k, v in ctrl.items()},
                         {"stale_calibration": ["G1_small_n_accuracy"], "column_swap_16_48": ["G2_excess_decay_grows"],
                          "device_worse_than_model": ["G3_gme_reach_matches"]})
        for i in range(30):
            rng = np.random.default_rng([11, i])
            plus = ghz_study.plus_world(rng)
            for cid in ("stale_calibration", "column_swap_16_48"):
                out = ctrl[cid].transform(plus, rng)
                self.assertEqual(set(out), set(plus), cid)                       # full dict returned
                self.assertIs(crit[ctrl[cid].criteria[0]](plus), True)
                self.assertIs(crit[ctrl[cid].criteria[0]](out), False, cid)
        # column swap exchanges columns 2 and 4 in F_pred, F_hat and F_boot; the input is not modified
        plus = ghz_study.plus_world(np.random.default_rng(0))
        out = ctrl["column_swap_16_48"].transform(plus, None)
        for k in ("F_pred", "F_hat", "F_boot"):
            np.testing.assert_array_equal(out[k][..., 2], plus[k][..., 4])
            np.testing.assert_array_equal(out[k][..., 4], plus[k][..., 2])
            np.testing.assert_array_equal(out[k][..., 0], plus[k][..., 0])
        self.assertAlmostEqual(plus["F_pred"][2], 0.72)
        # stale calibration: F_pred * 1.15 only
        out = ctrl["stale_calibration"].transform(plus, None)
        np.testing.assert_allclose(out["F_pred"], plus["F_pred"] * 1.15)
        np.testing.assert_array_equal(out["F_boot"], plus["F_boot"])
        # device worse than model: F_boot and F_hat - 0.15 (revision #6; -0.10 left n = 16 at the 1/2 line).
        out = ctrl["device_worse_than_model"].transform(plus, None)
        np.testing.assert_allclose(out["F_boot"], plus["F_boot"] - 0.15)
        np.testing.assert_allclose(out["F_hat"], plus["F_hat"] - 0.15)
        np.testing.assert_array_equal(out["F_pred"], plus["F_pred"])
        verdicts = []
        for i in range(100):
            rng = np.random.default_rng([12, i])
            verdicts.append(crit["G3_gme_reach_matches"](ctrl["device_worse_than_model"].transform(ghz_study.plus_world(rng), rng)))
        self.assertEqual(verdicts, [False] * 100)                               # it breaks G3 on every draw


# ------------------------------------------------------------------------------------------------------------------ K1, D-1
class TestK1(unittest.TestCase):
    def test_ideal_mix_passes_and_coherent_state_fails(self):
        res = core.analyze_counts(all_ideal_counts(), B=200)           # MIX twins with P = 1 and C = 0
        k1, ok = ghz_analyze.k1_verdict(res["mix"])
        self.assertTrue(ok, k1)
        for v in k1.values():
            self.assertLessEqual(v["C_mix_ci_high"], 0.05)
            self.assertGreaterEqual(v["F_mix"], 0.5 - 1e-9)             # reported, not part of the rule
        # a MIX twin that actually carries coherence (ideal GHZ counts under the MIX names) must fail K1
        bad = all_ideal_counts()
        for n in core.MIX_NS:
            for name, v in ideal_counts(n, "GHZ").items():
                bad[name.replace("GHZ", "MIX")] = v
        _k1, ok_bad = ghz_analyze.k1_verdict(core.analyze_counts(bad, B=50)["mix"])
        self.assertFalse(ok_bad)


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


class _FakeService:
    def __init__(self, backends):
        self._b = backends

    def backends(self, **kw):
        return list(self._b)


class TestD1(unittest.TestCase):
    def test_processor_type_present(self):
        svc = _FakeService([
            _FakeBackend("r3", 156, 1, {"family": "Heron", "revision": "3"}),
            _FakeBackend("r2_busy", 156, 50, {"family": "Heron", "revision": "2"}),
            _FakeBackend("r2_free", 156, 7, {"family": "Heron", "revision": "2"}),
        ])
        b, basis = ghz_run.pick_backend(svc)
        self.assertEqual((b.name, basis), ("r2_free", "processor_type"))

    def test_fallback_without_processor_type(self):
        svc = _FakeService([_FakeBackend("big", 200, 0), _FakeBackend("a156", 156, 9), _FakeBackend("b156", 156, 3)])
        b, basis = ghz_run.pick_backend(svc)
        self.assertEqual((b.name, basis), ("b156", "num_qubits_fallback"))
        self.assertEqual(ghz_run.heron_r2_basis(_FakeBackend("x", 127, 0)), (False, "num_qubits_fallback"))

    def test_no_candidate_stops(self):
        with self.assertRaises(SystemExit):
            ghz_run.pick_backend(_FakeService([_FakeBackend("small", 127, 0)]))


# ------------------------------------------------------------------------------------------ end-to-end analysis rehearsal
class TestAnalysisRehearsal(unittest.TestCase):
    def test_pipeline_on_ideal_counts(self):
        k = kingston()
        entries = core.build_all(k["snap"], k["backend"].target)
        counts = all_ideal_counts()
        with tempfile.TemporaryDirectory() as d:
            run = os.path.join(d, "run")
            os.makedirs(run)
            snap, h = k["snap"], k["hash"]
            with open(os.path.join(run, "snapshot_x.json"), "w") as fh:
                json.dump({"sha256": h, "snapshot": snap}, fh)
            with open(os.path.join(run, "circuits.qpy"), "wb") as fh:
                qpy.dump([e["circuit"] for e in entries], fh)
            model = core.model_all(entries, k["backend"].target)
            with open(os.path.join(run, "model.json"), "w") as fh:
                json.dump({"snapshot_sha256": h, "components": {str(n): model[n] for n in core.GRID}}, fh)
            with open(os.path.join(run, "counts.json"), "w") as fh:
                json.dump({"job_id": "SIMULATED", "order": [e["name"] for e in entries], "circuits": counts}, fh)
            with open(os.path.join(run, "job.json"), "w") as fh:
                json.dump({"job_id": "SIMULATED", "backend": "fake_kingston", "submitted_utc": "T", "snapshot_file": "snapshot_x.json",
                           "snapshot_sha256": h, "shots": core.SHOTS, "manifest": core.manifest_of(entries)}, fh)
            res = ghz_analyze.run_analysis(root=d, run_dir=run, out_dir=d, B=100)
            self.assertTrue(res["controls"]["K3"]["pass"], res["controls"]["K3"])
            self.assertTrue(res["controls"]["K1"]["pass"])
            self.assertTrue(res["model_matches_saved_model_json"])
            self.assertEqual(set(res["criteria"]), {"G1_small_n_accuracy", "G2_excess_decay_grows", "G3_gme_reach_matches"})
            self.assertTrue(all(abs(t["F_meas"] - 1.0) < 0.02 for t in res["table"]))
            self.assertTrue(os.path.isfile(os.path.join(d, "RESULTS_GHZ.md")))
            # a tampered count total is caught by K3
            counts["GHZ4_POP"]["meas"]["0000"] += 1
            with open(os.path.join(run, "counts.json"), "w") as fh:
                json.dump({"job_id": "SIMULATED", "order": [e["name"] for e in entries], "circuits": counts}, fh)
            res = ghz_analyze.run_analysis(root=d, run_dir=run, out_dir=d, B=20, write=False)
            self.assertFalse(res["controls"]["K3"]["pass"])
            self.assertFalse(res["interpretable"])


if __name__ == "__main__":
    unittest.main(verbosity=1)

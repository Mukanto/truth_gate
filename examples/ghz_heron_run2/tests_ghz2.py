"""tests_ghz2.py -- offline unit tests of the GHZ run-2 study code (PREREG.md run 2).

Run:  <venv python> tests_ghz2.py        (FakeKingston and toy targets only; no network, no account)
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

import ghz2_analyze
import ghz2_core as core
import ghz2_run
import ghz2_study


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
        for k in ("F_boot", "P_boot", "C_boot", "C_re_boot"):
            self.assertEqual(a[k].shape, (60, 6), k)
        self.assertEqual(a["F_hat"].shape, (6,))
        self.assertEqual(a["C_re"].shape, (6,))
        self.assertTrue(np.array_equal(a["F_boot"], b["F_boot"]))
        for n in core.MIX_NS:
            self.assertEqual(a["mix"][n]["C_boot"].shape, (60,))
            self.assertEqual(a["mix"][n]["F_boot"].shape, (60,))
            self.assertLess(a["mix"][n]["C"], 1e-9)
        self.assertTrue(np.all(a["F_lo"] <= a["F_hi"]))


# -------------------------------------------------------------------------------------------------------------- model
class TestModel(unittest.TestCase):
    def setUp(self):
        self.snap = toy_snapshot(3, e_cz=0.02, e_sx=0.001, ro=0.03, t2=1e-6)    # toy t1 = 2e-4
        self.tg = core.target_from_snapshot(self.snap)

    def hand_circuit(self, extra_sx=False):
        qc = QuantumCircuit(3, 3)
        qc.sx(0)
        qc.cz(0, 1)
        qc.cz(1, 2)
        if extra_sx:                       # a stand-in for the basis-change gates of a PAR circuit
            qc.sx(0); qc.sx(1); qc.sx(2)
        qc.measure([0, 1, 2], [0, 1, 2])
        return qc

    def test_idle_time_hand_computed(self):
        # ALAP: sx0 [0,40], cz01 [40,140], cz12 [140,240], measure at 240 ns.  Qubit 0 idles for cz12 (100 ns); 1 and 2 never.
        idle = core.idle_times(self.hand_circuit(), self.tg, [0, 1, 2])
        np.testing.assert_allclose(idle, [100e-9, 0.0, 0.0], atol=1e-15)

    def test_m2_on_toy_target(self):
        comp = core.model_components(self.hand_circuit(), self.hand_circuit(extra_sx=True), self.tg, [0, 1, 2])
        tree = (1 - 0.02) ** 2
        g_pop = tree * (1 - 0.001)                  # one sx in POP
        g_par = tree * (1 - 0.001) ** 4             # four sx in the PAR stand-in
        idle, t1, t2 = 100e-9, 2e-4, 1e-6
        p_pred = g_pop * (1 - 0.03) ** 3 * 0.5 * (1 + math.exp(-idle / t1))
        c_pred = g_par * (1 - 0.06) ** 3 * math.exp(-idle / t2)
        self.assertAlmostEqual(comp["P_pred"], p_pred, places=12)
        self.assertAlmostEqual(comp["C_pred"], c_pred, places=12)
        self.assertAlmostEqual(comp["F_pred"], (p_pred + c_pred) / 2, places=12)
        # reference arm = run 1's model M on the same circuit
        self.assertAlmostEqual(comp["F_M"], g_pop * (1 - 0.03) ** 3 * math.exp(-idle / t2), places=12)
        self.assertEqual(len(comp["cz_err"]), 2)
        self.assertEqual(comp["g1_pop_err"], [0.001])
        self.assertEqual(comp["g1_par_err"], [0.001] * 4)
        self.assertEqual(core.m2_from_components(comp)["F_pred"], comp["F_pred"])

    def test_m2_limits(self):
        # no errors, no idle: all predictions are 1; readout enters C twice, P once
        clean = toy_snapshot(3, e_cz=0.0, e_sx=0.0, ro=0.1, t2=1.0)
        tg = core.target_from_snapshot(clean)
        comp = core.model_components(self.hand_circuit(), self.hand_circuit(), tg, [0, 1, 2])
        self.assertAlmostEqual(comp["P_pred"], 0.9 ** 3 * 0.5 * (1 + math.exp(-100e-9 / 2e-4)), places=12)
        self.assertAlmostEqual(comp["C_pred"], 0.8 ** 3 * math.exp(-100e-9 / 1.0), places=12)
        # T1 only damps P through the |1..1> branch: P_pred never falls below half of its gate-and-readout value
        self.assertGreaterEqual(comp["P_pred"], 0.9 ** 3 * 0.5)

    def test_target_roundtrip_matches_backend_target(self):
        k = kingston()
        entries = core.build_all(k["snap"], k["backend"].target)
        m1 = core.model_all(entries, k["backend"].target)
        m2 = core.model_all(entries, core.target_from_snapshot(k["snap"]))
        for n in core.GRID:
            for key in ("P_pred", "C_pred", "F_pred", "F_M"):
                self.assertAlmostEqual(m1[n][key], m2[n][key], places=12)
            self.assertTrue(0.0 < m1[n]["C_pred"] < m1[n]["P_pred"] < 1.0)
        self.assertTrue(all(m1[a]["F_pred"] > m1[b]["F_pred"] for a, b in zip(core.GRID[:-1], core.GRID[1:])))
        self.assertTrue(all(m1[n]["F_pred"] < m1[n]["F_M"] for n in core.GRID))       # M2 is below the reference M

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
        with open(os.path.join(d, "FREEZE_GHZ2.json"), "w") as fh:
            json.dump({"files": files}, fh)
        if tamper:
            with open(os.path.join(d, "ghz2_core.py"), "a") as fh:
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
            self._make(d, drop="ghz2_core.py")
            with self.assertRaises(core.FreezeError):          # does not cover the study code
                core.verify_freeze(d)

    def test_runner_refuses_before_touching_the_account(self):
        def boom():
            raise AssertionError("QiskitRuntimeService must not be created before the freeze is verified")
        orig = ghz2_run._service
        ghz2_run._service = boom
        try:
            with tempfile.TemporaryDirectory() as d:
                for mode in (["--dry-run"], ["--submit"], ["--fetch"]):
                    self.assertEqual(ghz2_run.main(mode, root=d), 3)
                self.assertEqual(ghz2_analyze.main(root=d), 3)
        finally:
            ghz2_run._service = orig


# ------------------------------------------------------------------------------------------------------------- criteria
F_PRED = [0.936, 0.889, 0.70, 0.58, 0.455, 0.29]


def _data(f_pred=None, p_pred=None, c_pred=None, p_hat=None, c_hat=None, noise=0.0, B=200, seed=1):
    """Synthetic data in the study's schema (positional on GRID, no n)."""
    rng = np.random.default_rng(seed)
    f_pred = np.array(F_PRED if f_pred is None else f_pred, float)
    p_pred = f_pred + 0.02 if p_pred is None else np.array(p_pred, float)
    c_pred = f_pred - 0.02 if c_pred is None else np.array(c_pred, float)
    p_hat = p_pred * 0.9 if p_hat is None else np.array(p_hat, float)
    c_hat = c_pred * 0.97 if c_hat is None else np.array(c_hat, float)
    f_hat = (p_hat + c_hat) / 2
    shape = (B, 6)
    return {"F_pred": f_pred, "P_pred": p_pred, "C_pred": c_pred, "F_hat": f_hat, "P_hat": p_hat, "C_hat": c_hat,
            "F_boot": f_hat + rng.normal(0, noise, shape), "P_boot": p_hat + rng.normal(0, noise, shape),
            "C_boot": c_hat + rng.normal(0, noise, shape)}


class TestCriteria(unittest.TestCase):
    def test_H1(self):
        d = _data()
        d["F_hat"] = np.array(F_PRED) + np.array([0.049, -0.049, 0, 0, 0, 0])
        self.assertTrue(ghz2_study.H1_small_n_accuracy(d))
        d["F_hat"] = np.array(F_PRED) + np.array([0.0, -0.051, 0, 0, 0, 0])
        self.assertFalse(ghz2_study.H1_small_n_accuracy(d))
        d["F_hat"] = np.array(F_PRED) + np.array([0.051, 0.0, 0, 0, 0, 0])               # both directions are reachable
        self.assertFalse(ghz2_study.H1_small_n_accuracy(d))
        d["F_hat"] = np.array(F_PRED)
        d["F_pred"] = np.array([1.01] + F_PRED[1:])                                       # F_pred outside (0, 1)
        self.assertIsNone(ghz2_study.H1_small_n_accuracy(d))
        d["F_pred"] = np.array([0.0] + F_PRED[1:])
        self.assertIsNone(ghz2_study.H1_small_n_accuracy(d))
        d = _data()
        d["F_pred"] = d["F_pred"][:5]                                                     # wrong shape
        self.assertIsNone(ghz2_study.H1_small_n_accuracy(d))
        self.assertNotIn("n", _data())                                                    # the grid is not data

    def test_H2(self):
        d = _data()
        d["F_hat"] = np.array([0.9, 0.85, 0.65, 0.55, 0.45, 0.2])                         # n_meas = 24 = n_pred
        self.assertTrue(ghz2_study.H2_gme_reach_matches(d))
        d["F_hat"] = np.array([0.9, 0.85, 0.55, 0.45, 0.4, 0.2])                          # n_meas = 16
        self.assertFalse(ghz2_study.H2_gme_reach_matches(d))
        d["F_hat"] = np.array([0.9, 0.85, 0.65, 0.55, 0.52, 0.2])                         # n_meas = 32 (point values)
        self.assertFalse(ghz2_study.H2_gme_reach_matches(d))
        # n_pred = 0 is UNDEFINED, whatever the device does
        self.assertIsNone(ghz2_study.H2_gme_reach_matches(_data(f_pred=[0.4] * 6, p_pred=[0.45] * 6, c_pred=[0.35] * 6)))
        d = _data(f_pred=[0.4] * 6)
        d["F_hat"] = np.array([0.9] * 6)
        self.assertIsNone(ghz2_study.H2_gme_reach_matches(d))
        d = _data()
        d["F_hat"] = d["F_hat"][:4]
        self.assertIsNone(ghz2_study.H2_gme_reach_matches(d))

    def test_H3(self):
        pred = np.array(F_PRED)
        p_pred, c_pred = pred + 0.02, pred - 0.02
        n = np.array(ghz2_study.GRID, float)
        # population-specific shortfall: P short more than C -> HOLDS
        d = _data(p_hat=p_pred * np.exp(-0.004 * n), c_hat=c_pred * np.exp(-0.001 * n), noise=0.008)
        self.assertTrue(ghz2_study.H3_population_specific(d))
        # coherence short more than P -> FAILS
        d = _data(p_hat=p_pred * 0.98, c_hat=c_pred * 0.7, noise=0.008)
        self.assertFalse(ghz2_study.H3_population_specific(d))
        # both columns (n = 32 and n = 48) are needed: break only n = 48
        d = _data(p_hat=p_pred * np.exp(-0.004 * n), c_hat=c_pred * np.exp(-0.001 * n), noise=0.008)
        d["C_boot"][:, 5] *= 0.5
        self.assertFalse(ghz2_study.H3_population_specific(d))
        # a replicate or prediction <= 0 in an involved column is UNDEFINED; other columns do not matter
        d = _data(noise=0.008)
        d["P_boot"][3, 4] = 0.0
        self.assertIsNone(ghz2_study.H3_population_specific(d))
        d = _data(noise=0.008)
        d["C_pred"] = d["C_pred"].copy(); d["C_pred"][5] = 0.0
        self.assertIsNone(ghz2_study.H3_population_specific(d))
        d = _data(noise=0.008)
        d["C_boot"][3, 0] = -1.0                                                          # column n = 4 is not involved
        self.assertIsNotNone(ghz2_study.H3_population_specific(d))
        d = _data(noise=0.008)
        d["P_boot"] = d["P_boot"][:, :5]
        self.assertIsNone(ghz2_study.H3_population_specific(d))

    def test_worlds_and_controls_separate_the_criteria(self):
        crit = {c.id: c.fn for c in ghz2_study.STUDY.criteria}
        ctrl = {c.id: c for c in ghz2_study.STUDY.controls}
        self.assertEqual({k: v.criteria for k, v in ctrl.items()},
                         {"stale_calibration": ["H1_small_n_accuracy"], "reach_off_by_one_step": ["H2_gme_reach_matches"],
                          "coherence_specific_loss": ["H3_population_specific"]})
        for i in range(30):
            rng = np.random.default_rng([21, i])
            plus, minus = ghz2_study.plus_world(rng), ghz2_study.minus_world(rng)
            self.assertEqual(set(plus), {"F_pred", "P_pred", "C_pred", "F_hat", "P_hat", "C_hat", "F_boot", "P_boot", "C_boot"})
            self.assertEqual(plus["F_boot"].shape, (400, 6))
            for cid, fn in crit.items():
                self.assertIs(fn(plus), True, cid)
                self.assertIs(fn(minus), False, cid)
            for k, c in ctrl.items():
                out = c.transform(plus, rng)
                self.assertEqual(set(out), set(plus), k)                                   # full dict returned
                self.assertIs(crit[c.criteria[0]](out), False, k)                          # each control FAILS its criterion
        plus = ghz2_study.plus_world(np.random.default_rng(0))
        out = ctrl["stale_calibration"].transform(plus, None)
        np.testing.assert_allclose(out["F_pred"], plus["F_pred"] + 0.06)
        self.assertLess(out["F_pred"][0], 1.0)                                              # still inside (0, 1): FAILS, not UNDEFINED
        out = ctrl["reach_off_by_one_step"].transform(plus, None)
        expect = np.array(plus["F_pred"], dtype=float, copy=True); expect[[4, 5]] += 0.12
        np.testing.assert_allclose(out["F_pred"], expect)
        self.assertLess(float(np.max(out["F_pred"])), 1.0)                                   # inside (0, 1): FAILS, not UNDEFINED
        out = ctrl["coherence_specific_loss"].transform(plus, None)
        np.testing.assert_allclose(out["C_hat"], plus["C_hat"] * 0.85)
        np.testing.assert_allclose(out["C_boot"], plus["C_boot"] * 0.85)
        np.testing.assert_array_equal(out["P_boot"], plus["P_boot"])
        np.testing.assert_array_equal(out["P_hat"], plus["P_hat"])


# ------------------------------------------------------------------------------------------------------------------ K1, D-1
class TestK1(unittest.TestCase):
    def test_ideal_mix_passes_and_coherent_state_fails(self):
        res = core.analyze_counts(all_ideal_counts(), B=200)           # MIX twins with P = 1 and C = 0
        k1, ok = ghz2_analyze.k1_verdict(res["mix"])
        self.assertTrue(ok, k1)
        for v in k1.values():
            self.assertLessEqual(v["C_mix_ci_high"], 0.05)
            self.assertGreaterEqual(v["F_mix"], 0.5 - 1e-9)             # reported, not part of the rule
        # a MIX twin that actually carries coherence (ideal GHZ counts under the MIX names) must fail K1
        bad = all_ideal_counts()
        for n in core.MIX_NS:
            for name, v in ideal_counts(n, "GHZ").items():
                bad[name.replace("GHZ", "MIX")] = v
        _k1, ok_bad = ghz2_analyze.k1_verdict(core.analyze_counts(bad, B=50)["mix"])
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
        b, basis = ghz2_run.pick_backend(svc)
        self.assertEqual((b.name, basis), ("r2_free", "processor_type"))

    def test_fallback_without_processor_type(self):
        svc = _FakeService([_FakeBackend("big", 200, 0), _FakeBackend("a156", 156, 9), _FakeBackend("b156", 156, 3)])
        b, basis = ghz2_run.pick_backend(svc)
        self.assertEqual((b.name, basis), ("b156", "num_qubits_fallback"))
        self.assertEqual(ghz2_run.heron_r2_basis(_FakeBackend("x", 127, 0)), (False, "num_qubits_fallback"))

    def test_no_candidate_stops(self):
        with self.assertRaises(SystemExit):
            ghz2_run.pick_backend(_FakeService([_FakeBackend("small", 127, 0)]))


class TestBitOrderBuilder(unittest.TestCase):
    def test_flip_only_for_the_control(self):
        snap = toy_snapshot(5)
        S, T, parents = core.selection(snap, 4)
        base = core.build_circuit(4, parents, "POP")
        self.assertEqual([i.operation.name for i in base.data].count("x"), 0)
        flipped = core.build_circuit(4, parents, "POP", flip=(3,))
        self.assertEqual([i.operation.name for i in flipped.data].count("x"), 1)


class TestTimeBudget(unittest.TestCase):
    def test_refusal_above_300_seconds(self):
        self.assertEqual(core.MAX_QUANTUM_SECONDS, 300.0)
        ghz2_run.enforce_time_budget(299.9)                       # fine
        ghz2_run.enforce_time_budget(300.0)                       # exactly the limit is allowed
        with self.assertRaises(SystemExit):
            ghz2_run.enforce_time_budget(300.1)

    def test_submit_and_dry_run_refuse_before_writing_anything(self):
        orig_service, orig_est = ghz2_run._service, core.estimate_time
        ghz2_run._service = lambda: _FakeService([FakeKingston()])      # FakeKingston has status() and processor_type
        core.estimate_time = lambda *a, **k: (301.0, 250e-6, 5e-6)
        try:
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(SystemExit):
                    ghz2_run.cmd_submit(d)
                self.assertFalse(os.path.exists(os.path.join(d, "run")))
                self.assertEqual(ghz2_run.cmd_dry_run(d), 4)           # dry run says it would refuse
            core.estimate_time = orig_est                              # the real estimate (~187 s) is within the limit
            with tempfile.TemporaryDirectory() as d:
                self.assertEqual(ghz2_run.cmd_dry_run(d), 0)
        finally:
            ghz2_run._service, core.estimate_time = orig_service, orig_est


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
            res = ghz2_analyze.run_analysis(root=d, run_dir=run, out_dir=d, B=100)
            self.assertTrue(res["controls"]["K3"]["pass"], res["controls"]["K3"])
            self.assertTrue(res["controls"]["K3"]["detail"]["m2_recomputed_equals_saved_model"])
            self.assertTrue(res["controls"]["K1"]["pass"])
            self.assertEqual(set(res["criteria"]), {"H1_small_n_accuracy", "H2_gme_reach_matches", "H3_population_specific"})
            self.assertEqual(len(res["table"]), 6)
            self.assertTrue(all(abs(t["F"] - 1.0) < 0.02 for t in res["table"]))
            self.assertTrue(all(abs(t["C_re"] - t["C"]) < 0.02 for t in res["table"]))    # ideal data: nominal phase = best phase
            self.assertEqual(res["headline"]["n_meas_point"], 48)
            for name in ("RESULTS_GHZ2.md", "RESULTS_GHZ2.json", "RESULTS_GHZ2_boot.npz"):
                self.assertTrue(os.path.isfile(os.path.join(d, name)), name)
            with np.load(os.path.join(d, "RESULTS_GHZ2_boot.npz")) as z:
                self.assertEqual(z["F_boot"].shape, (100, 6))
                self.assertEqual(z["P_boot"].shape, (100, 6))
                self.assertEqual(int(z["bootstrap_seed"]), 20261113)
            # a tampered count total is caught by K3
            counts["GHZ4_POP"]["meas"]["0000"] += 1
            with open(os.path.join(run, "counts.json"), "w") as fh:
                json.dump({"job_id": "SIMULATED", "order": [e["name"] for e in entries], "circuits": counts}, fh)
            res = ghz2_analyze.run_analysis(root=d, run_dir=run, out_dir=d, B=20, write=False)
            self.assertFalse(res["controls"]["K3"]["pass"])
            self.assertFalse(res["interpretable"])


if __name__ == "__main__":
    unittest.main(verbosity=1)

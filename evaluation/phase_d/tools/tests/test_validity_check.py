import hashlib
import json
import os
import tempfile
import unittest
from unittest import mock

import common
import toy_case
from assemble import assemble
from structure_stat import import_truth_gate, load_study_module
import validity_check as vc

SEED = 20261117
N = 200  # samples per stream in the tests (the real runs use 1000)


class Case:
    """A toy case folder in a temporary directory."""

    def __init__(self, phi=0.99, **kw):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = toy_case.write_case(os.path.join(self.tmp.name, "case"), phi, **kw)
        self.log = os.path.join(self.tmp.name, "validity_log.jsonl")
        self.out = os.path.join(self.tmp.name, "RESULT.json")

    def check(self, samples=N, seed=SEED, **kw):
        return vc.run_checks(self.dir, common.PKG, samples, seed, **kw)

    def cli(self, *extra, samples=N, package_root=None, dev=True, case_dir=None):
        """Run the CLI; the tests use 200 samples, which needs --dev (R2-25)."""
        args = ["--case", case_dir or self.dir, "--package-root", package_root or common.PKG, "--samples", samples,
                "--seed", SEED, "--log", self.log, "--out", self.out, *extra]
        if dev:
            args.append("--dev")
        return common.run_tool("validity_check.py", *args)

    def cleanup(self):
        self.tmp.cleanup()


def make_case(test, **kw):
    c = Case(**kw)
    test.addCleanup(c.cleanup)
    return c


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def body_returning(expr):
    return f"import numpy as np\n\n\ndef criterion(d):\n    return {expr}\n"


def make_case_dir(cleanup):
    """A phi = 0 toy case folder in a temporary directory removed by ``cleanup(fn, path)`` (for class-level setup)."""
    import shutil
    d = tempfile.mkdtemp()
    cleanup(shutil.rmtree, d, True)
    return toy_case.write_case(os.path.join(d, "case"), 0.0)


class ValidityChecksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_truth_gate(common.PKG)
        cls.strong = Case(0.99)
        cls.weak = Case(0.0)
        cls.r_strong = cls.strong.check()
        cls.r_weak = cls.weak.check()

    @classmethod
    def tearDownClass(cls):
        cls.strong.cleanup()
        cls.weak.cleanup()

    # --- the two toy cases of the spec
    def test_strong_autocorrelation_is_valid(self):
        r = self.r_strong
        self.assertTrue(r["valid"], r["reasons"])
        self.assertTrue(r["v1"] and r["v2"] and r["mech_a"] and r["mech_b"] and r["structure_computable"])
        self.assertIsNone(r["v1_label"])
        c = r["counts"]["v1"]
        self.assertGreaterEqual(c["faulty_rate"], 0.25)
        self.assertLess(c["fisher_p"], 0.01)
        self.assertGreater(c["faulty_holds"], c["fixed_holds"])

    def test_zero_autocorrelation_fails_v1a(self):
        r = self.r_weak
        self.assertFalse(r["valid"])
        self.assertFalse(r["v1"])
        self.assertEqual(r["v1_label"], "V1a")
        self.assertLess(r["counts"]["v1"]["faulty_rate"], r["kstar"] / 200)
        self.assertTrue(r["v2"] and r["mech_b"])  # only the error's effect is missing
        self.assertFalse(r["mech_a"])  # note_value 0 equals null_value 0: the R2-14 band has zero width

    def test_result_fields(self):
        r = self.r_strong
        for k in ("case", "samples", "seed", "dev", "m", "kstar", "alpha_family", "size", "counts", "v1", "v1_label", "v2",
                  "mech_a", "mech_b", "structure_computable", "structure", "timing", "timing_ok", "error_in",
                  "error_text", "valid", "reasons", "details", "errors"):
            self.assertIn(k, r)
        self.assertEqual((r["structure"], r["dev"], r["error_in"]), ("used", False, None))
        self.assertEqual((r["case"], r["samples"], r["seed"]), ("TOY-1", N, SEED))
        self.assertEqual((r["m"], r["kstar"]), (4, 18))  # one criterion, one control, noise, zeros; first flagged count of 200
        self.assertEqual((r["alpha_family"], r["size"]), (0.05, 0.05))
        self.assertEqual(set(r["counts"]["v2"]), {"minus", "noise", "plus"})
        json.dumps(r)  # serialisable

    # --- the counts are the ones of the named streams
    def test_counts_equal_an_independent_recomputation(self):
        from truth_gate.probes import noise_probe
        from truth_gate.sampling import copy_data, stream_rng
        strong = self.strong
        rd = lambda n: read(os.path.join(strong.dir, n))  # noqa: E731
        ref = rd("reference.py")
        mf = load_study_module(assemble(ref, rd("faulty_body.py")), "f.py", "t")
        mx = load_study_module(assemble(ref, rd("fixed_body.py")), "x.py", "t")
        fh = xh = mh = nh = ph = 0
        for i in range(N):
            minus = mf.STUDY.worlds["minus"].generate(stream_rng(SEED, "validity:minus", i))
            plus = mx.STUDY.worlds["plus"].generate(stream_rng(SEED, "validity:plus", i))
            noise = noise_probe(copy_data(plus), stream_rng(SEED, "validity:noise", i))
            fh += bool(mf.criterion(copy_data(minus)))
            xh += bool(mx.criterion(copy_data(minus)))
            nh += bool(mx.criterion(copy_data(noise)))
            ph += bool(mx.criterion(copy_data(plus)))
        c = self.r_strong["counts"]
        self.assertEqual((c["v1"]["faulty_holds"], c["v1"]["fixed_holds"]), (fh, xh))
        self.assertEqual((c["v2"]["minus"]["holds"], c["v2"]["noise"]["holds"], c["v2"]["plus"]["holds"]), (xh, nh, ph))

    def test_streams_are_not_the_gates(self):
        import re
        from truth_gate import Budget
        self.assertNotEqual(SEED, Budget().base_seed)
        src = read(vc.__file__)
        # every stream name the tool draws from is a validity: name; none of the gate's names (world:, probe:, control:,
        # premise-rng:) appears as a string literal
        self.assertEqual(re.findall(r"""["'](?:world|probe|control|premise-rng):""", src), [])
        self.assertEqual(sorted(set(re.findall(r'"validity:(\w+)"', src))), ["noise", "plus"])
        self.assertIn('f"validity:{stream}"', src)

    def test_deterministic(self):
        r2 = self.strong.check()
        drop = lambda r: {k: v for k, v in r.items() if k != "timing"}  # noqa: E731  (wall-clock times)
        self.assertEqual(json.dumps(drop(r2), sort_keys=True), json.dumps(drop(self.r_strong), sort_keys=True))

    # --- the thresholds
    def test_kstar_matches_the_first_flagged_counts(self):
        # REVISIONS_D.md: the first flagged count of 200 is 17 (m <= 2), 18 (m = 4), 19 (m = 6 to 12), 20 (m >= 16)
        for m, k in ((1, 17), (2, 17), (4, 18), (6, 19), (12, 19), (16, 20)):
            self.assertEqual(vc.kstar_of(0.05, m, 0.05), k, m)
        self.assertIsNone(vc.kstar_of(0.05, 4, 0.999))

    def test_v1b_below_the_bar_but_above_the_flag_threshold(self):
        c = make_case(self, faulty_body=body_returning('bool(d["y"][0] > 7.35)'), fixed_body=body_returning("False"))
        r = c.check()
        rate = r["counts"]["v1"]["faulty_rate"]
        self.assertTrue(r["kstar"] / 200 <= rate < 0.25, rate)
        self.assertFalse(r["v1"])
        self.assertEqual(r["v1_label"], "V1b")

    def test_v1b_when_the_fixed_criterion_holds_too(self):
        c = make_case(self, faulty_body=body_returning("True"), fixed_body=body_returning("True"))
        r = c.check()
        self.assertEqual((r["counts"]["v1"]["faulty_rate"], r["counts"]["v1"]["fixed_rate"]), (1.0, 1.0))
        self.assertEqual((r["v1"], r["v1_label"]), (False, "V1b"))
        self.assertFalse(r["v2"])  # the fixed criterion holds on minus and on noise
        self.assertIn("minus", r["reasons"]["v2"])
        self.assertFalse(r["counts"]["v2"]["minus"]["ok"] or r["counts"]["v2"]["noise"]["ok"])
        self.assertTrue(r["counts"]["v2"]["plus"]["ok"])

    def test_v2_needs_the_fixed_criterion_to_hold_on_plus(self):
        c = make_case(self, fixed_body=body_returning("False"))
        r = c.check()
        self.assertFalse(r["v2"])
        self.assertFalse(r["counts"]["v2"]["plus"]["ok"])
        self.assertTrue(r["counts"]["v2"]["minus"]["ok"] and r["counts"]["v2"]["noise"]["ok"])
        self.assertFalse(r["v1"] and r["valid"])

    def test_v2_bounds_are_inclusive(self):
        self.assertEqual((vc.V2_MAX_MINUS, vc.V2_MAX_NOISE, vc.V2_MIN_PLUS), (0.065, 0.065, 0.70))
        self.assertEqual((vc.V1_MIN_RATE, vc.V1_MAX_P), (0.25, 0.01))

    # --- None and errors
    def test_none_counts_as_not_holds_and_is_not_an_error(self):
        c = make_case(self, faulty_body=body_returning("None"), fixed_body=body_returning("None"))
        r = c.check()
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["counts"]["v1"]["faulty_holds"], 0)
        self.assertEqual(r["counts"]["v2"]["plus"]["holds"], 0)
        self.assertFalse(r["v2"])
        self.assertNotEqual(r["reasons"]["v2"], "error")

    def test_exception_is_recorded_and_fails_with_reason_error(self):
        c = make_case(self, faulty_body=body_returning('bool(d["missing_key"][0] > 0)'))
        r = c.check()
        self.assertEqual(r["reasons"]["v1"], "error")
        self.assertFalse(r["v1"])
        self.assertIsNone(r["v1_label"])
        self.assertFalse(r["valid"])
        self.assertTrue(any("KeyError" in e for e in r["errors"]))
        self.assertEqual(r["counts"]["v1"]["errors_faulty"], N)

    def test_fixed_exception_fails_v1_and_v2(self):
        c = make_case(self, fixed_body=body_returning("1 / 0"))
        r = c.check()
        self.assertEqual((r["reasons"]["v1"], r["reasons"]["v2"]), ("error", "error"))
        self.assertFalse(r["valid"])

    def test_bad_return_type_is_an_error(self):
        c = make_case(self, faulty_body=body_returning("3.5"))
        r = c.check()
        self.assertEqual(r["reasons"]["v1"], "error")

    # --- the mechanical checks
    def test_mech_a_fails_when_the_structure_is_not_at_the_note_value(self):
        c = make_case(self, phi=0.99)
        priv = toy_case.private(0.5)  # the note says 0.5, the worlds carry 0.99
        with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump(priv, f)
        r = c.check()
        self.assertFalse(r["mech_a"])
        self.assertTrue(r["structure_computable"])
        self.assertIn("tolerance", r["reasons"]["mech_a"])
        self.assertFalse(r["valid"])

    def test_mech_a_band_is_relative_to_the_distance_from_the_null(self):
        # R2-14: |mean - note_value| <= 0.2 * |note_value - null_value|; no special case at 0
        self.assertAlmostEqual(self.r_strong["details"]["mech_a"]["tolerance"], 0.2 * 0.99)
        self.assertEqual(self.r_weak["details"]["mech_a"]["tolerance"], 0.0)
        self.assertFalse(self.r_weak["mech_a"])

    def test_mech_a_band_with_a_null_away_from_zero(self):
        # stat = 1 + lag-1 autocorrelation, null 1.  Take the true mean mu and a note value at which the band
        # 0.2 * |note - null| (R2-14) fails while the old band 0.2 * |note| would pass: |mu - note| = 0.3 * |note - 1|.
        mu = 1.0 + self.r_strong["details"]["mech_a"]["plus"]["mean"]
        note = (mu - 0.3) / 0.7
        self.assertLess(abs(mu - note), 0.2 * abs(note))  # the old rule would accept this note value
        self.assertGreater(abs(mu - note), 0.2 * abs(note - 1.0))
        c = make_case(self, phi=0.99)
        priv = toy_case.private(note)
        priv["structure_statistic"]["code"] = priv["structure_statistic"]["code"].replace("return float(", "return 1.0 + float(")
        priv["structure_statistic"]["null_value"] = 1.0
        with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump(priv, f)
        r = c.check()
        self.assertFalse(r["mech_a"])
        self.assertAlmostEqual(r["details"]["mech_a"]["tolerance"], 0.2 * abs(note - 1.0))
        # and a note value half as far from the mean passes
        priv["structure_statistic"]["note_value"] = (mu - 0.1) / 0.9  # |mu - note| = 0.1 * |note - 1|
        with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump(priv, f)
        self.assertTrue(c.check()["mech_a"])

    def test_world_without_the_structure_fails_the_band_when_the_null_is_not_zero(self):
        # the R2-14 example: null 1, note 1.15: the old band [0.92, 1.38] contained the null; the new one is 1.15 +- 0.03
        c = make_case(self, phi=0.0)
        priv = toy_case.private(1.15)
        priv["structure_statistic"]["code"] = "def stat(d):\n    return 1.0\n"  # a world that sits at the null
        priv["structure_statistic"]["null_value"] = 1.0
        with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump(priv, f)
        self.assertFalse(c.check()["mech_a"])

    def test_mech_a_fails_when_the_two_worlds_differ(self):
        c = make_case(self, phi=0.99)
        ref = os.path.join(c.dir, "reference.py")
        src = read(ref)
        # in minus the noise of y loses its autocorrelation: the structure is only in plus
        src = src.replace("    return _gen(rng, 0.0)",
                          "    d = _gen(rng, 0.0)\n    return {'x': d['x'], 'y': rng.standard_normal(N) * 7.0}")
        with open(ref, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        r = c.check()
        self.assertFalse(r["mech_a"])
        self.assertFalse(r["valid"])

    def test_set_by_brief_only_needs_a_computable_statistic(self):
        c = make_case(self, phi=0.99, set_by_brief=True)
        priv = toy_case.private(0.2, set_by_brief=True)  # note value far from the truth: not checked
        with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump(priv, f)
        r = c.check()
        self.assertTrue(r["mech_a"] and r["structure_computable"])
        self.assertTrue(r["details"]["mech_a"]["plus"]["set_by_brief"])

    def test_uncomputable_statistic_makes_the_pair_invalid(self):
        c = make_case(self, phi=0.99)
        priv = toy_case.private(0.99)
        priv["structure_statistic"]["code"] = "def stat(d):\n    return float('nan')\n"
        with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump(priv, f)
        r = c.check()
        self.assertFalse(r["structure_computable"] or r["mech_a"] or r["valid"])
        self.assertTrue(r["v1"] and r["v2"])  # the other checks still ran

    def test_mech_b_needs_a_changed_key_that_the_fixed_criterion_reads(self):
        c = make_case(self, fixed_body=body_returning('bool(np.mean(d["x"]) > -1e9)'))  # reads x; minus changes only y
        r = c.check()
        self.assertFalse(r["mech_b"])
        self.assertEqual(r["details"]["mech_b"]["minus_check"]["read_keys"], ["x"])
        self.assertEqual(r["details"]["mech_b"]["minus_check"]["changed_keys"], ["y"])
        self.assertFalse(r["valid"])

    def test_mech_b_mirrors_the_gates_minus_analysis(self):
        from truth_gate import minus as minus_check
        from truth_gate.sampling import stream_rng
        strong = self.strong
        ref = read(os.path.join(strong.dir, "reference.py"))
        mx = load_study_module(assemble(ref, read(os.path.join(strong.dir, "fixed_body.py"))), "x.py", "t")
        plus0 = mx.STUDY.worlds["plus"].generate(stream_rng(SEED, "validity:plus", 0))
        minus0 = mx.STUDY.worlds["minus"].generate(stream_rng(SEED, "validity:plus", 0))
        rec = minus_check.analyse(mx.STUDY.criteria, plus0, minus0, paired=True)["C"]["minus_check"]
        self.assertEqual(self.r_strong["details"]["mech_b"]["minus_check"], rec)

    def test_assemble_error_is_a_failed_check_not_a_crash(self):
        c = make_case(self, faulty_body="import math\n\ndef criterion(d):\n    return True\n")
        r = c.check()
        self.assertFalse(r["valid"])
        self.assertIn("assemble_error", r["reasons"]["setup"])


class ValidityCheckCliTests(unittest.TestCase):
    def test_valid_case_exit_0_and_log(self):
        c = make_case(self, phi=0.99)
        r = c.cli()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(c.out, encoding="utf-8") as f:
            res = json.load(f)
        self.assertTrue(res["valid"])
        with open(c.log, encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual((entry["case"], entry["seed"], entry["samples"]), ("TOY-1", SEED, N))
        self.assertRegex(entry["time_utc"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        for name in vc.INPUT_FILES:
            with open(os.path.join(c.dir, name), "rb") as f:
                self.assertEqual(entry["sha256"][name], hashlib.sha256(f.read()).hexdigest())
        with open(vc.__file__, "rb") as f:
            self.assertEqual(entry["sha256"]["tools/validity_check.py"], hashlib.sha256(f.read()).hexdigest())
        self.assertEqual(entry["result"]["valid"], True)
        self.assertEqual(entry["result"], res)

    def test_full_run_hashes_the_sibling_tools_it_imports(self):  # D-R5-5 (R3B-6)
        c = make_case(self, phi=0.99)
        self.assertEqual(c.cli().returncode, 0)
        with open(c.log, encoding="utf-8") as f:
            entry = json.loads(f.read().splitlines()[0])
        for sib in ("assemble.py", "structure_stat.py", "attributable.py", "mech_check_bodies.py", "check_skeletons_d.py"):
            with open(os.path.join(common.TOOLS, sib), "rb") as g:
                self.assertEqual(entry["sha256"][f"tools/{sib}"], hashlib.sha256(g.read()).hexdigest(), sib)

    def test_log_is_appended(self):
        c = make_case(self, phi=0.99)
        c.cli()
        c.cli()
        with open(c.log, encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 2)

    def test_invalid_case_exit_1_and_still_logged(self):
        c = make_case(self, phi=0.0)
        r = c.cli()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        with open(c.out, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["v1_label"], "V1a")
        with open(c.log, encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 1)

    def test_unassemblable_case_is_logged_with_exit_1(self):
        c = make_case(self, faulty_body="import math\n\ndef criterion(d):\n    return True\n")
        self.assertEqual(c.cli().returncode, 1)
        with open(c.log, encoding="utf-8") as f:
            self.assertFalse(json.loads(f.read())["result"]["valid"])

    def test_usage_errors_exit_2_and_nothing_is_logged(self):
        c = make_case(self, phi=0.99)
        os.remove(os.path.join(c.dir, "PRIVATE.json"))
        self.assertEqual(c.cli().returncode, 2)
        c2 = make_case(self, phi=0.99)
        self.assertEqual(c2.cli(package_root=c2.tmp.name).returncode, 2)
        self.assertEqual(c2.cli(samples=0).returncode, 2)
        self.assertEqual(common.run_tool("validity_check.py", "--case", c2.dir).returncode, 2)
        for cc in (c, c2):
            self.assertFalse(os.path.exists(cc.log))
        with open(os.path.join(c2.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump({"structure_statistic": {"code": "def stat(d):\n    return 0.0\n"}}, f)  # fields missing
        self.assertEqual(c2.cli().returncode, 2)


class NoStructureTests(unittest.TestCase):
    """R2-7: a decoy has no structure statistic."""

    def decoy(self):
        c = make_case(self, phi=0.99)
        priv = toy_case.private(0.99)
        priv["structure_statistic"] = None
        priv["class"] = "B-1"  # D-R4-3: --no-structure is for the decoy classes only
        with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump(priv, f)
        return c

    def test_no_structure_skips_the_statistic_and_valid_does_not_need_it(self):
        r = self.decoy().check(no_structure=True)
        self.assertTrue(r["valid"], r["reasons"])
        self.assertEqual(r["structure"], "not used (decoy)")
        self.assertIsNone(r["mech_a"])
        self.assertIsNone(r["structure_computable"])
        self.assertNotIn("mech_a", r["details"])
        self.assertTrue(r["mech_b"] and r["v1"] and r["v2"] and r["timing_ok"])

    def test_a_decoy_without_the_flag_is_refused(self):
        with self.assertRaises(ValueError):
            self.decoy().check()

    def test_the_flag_is_refused_when_the_statistic_is_present(self):
        c = make_case(self, phi=0.99)
        with self.assertRaises(ValueError):
            c.check(no_structure=True)

    def test_no_structure_still_needs_the_other_checks(self):
        c = self.decoy()
        with open(os.path.join(c.dir, "fixed_body.py"), "w", encoding="utf-8") as f:
            f.write(body_returning("True"))  # holds on minus and on noise: V2 fails
        r = c.check(no_structure=True)
        self.assertFalse(r["valid"])
        self.assertFalse(r["v2"])

    def test_cli_exit_codes_and_the_log(self):
        c = self.decoy()
        self.assertEqual(c.cli().returncode, 2)  # statistic null, flag missing
        self.assertFalse(os.path.exists(c.log))
        r = c.cli("--no-structure")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(c.log, encoding="utf-8") as f:
            entry = json.loads(f.read())
        self.assertTrue(entry["no_structure"])
        self.assertEqual(entry["result"]["structure"], "not used (decoy)")
        normal = make_case(self, phi=0.99)
        r = normal.cli("--no-structure")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)  # statistic present, flag given
        self.assertFalse(os.path.exists(normal.log))


class TimingTests(unittest.TestCase):
    """R2-19: t, g, S and the estimate 2 * 200 * (S + 1) * (t + g), at most 1800 seconds."""

    @classmethod
    def setUpClass(cls):
        import_truth_gate(common.PKG)

    def test_estimate_formula(self):
        self.assertEqual(vc.timing_estimate(5, 0.01, 0.005), 2 * 200 * 6 * 0.015)
        self.assertEqual((vc.TIMING_SAMPLES, vc.TIMING_LIMIT_S), (20, 1800.0))

    def test_timing_fields_on_the_toy(self):
        c = make_case(self, phi=0.99)
        r = c.check()
        t = r["timing"]
        self.assertEqual((t["n"], t["S"], t["S_formula"], t["limit_s"]), (20, 5, 5, 1800.0))  # plus, minus, 1 control, 2 probes
        self.assertGreater(t["t"], 0)
        self.assertGreater(t["g"], 0)
        self.assertAlmostEqual(t["estimate_s"], 400 * (t["S"] + 1) * (t["t"] + t["g"]))
        self.assertTrue(r["timing_ok"])
        self.assertEqual(r["reasons"]["timing"], "ok")

    def test_the_clock_decides_the_threshold(self):
        # a fake clock: every call advances by `step`, so every timed interval is `step` and t = g = step;
        # estimate = 2 * 200 * (5 + 1) * 2 * step = 4800 * step
        c = make_case(self, phi=0.99)
        for step in (0.1, 0.5):
            with self.subTest(step=step):
                ticks = iter(range(10 ** 7))
                with mock.patch.object(vc.time, "perf_counter", lambda: next(ticks) * step):
                    r = c.check()
                self.assertAlmostEqual(r["timing"]["t"], step)
                self.assertAlmostEqual(r["timing"]["g"], step)
                self.assertAlmostEqual(r["timing"]["estimate_s"], 4800 * step)
                self.assertEqual(r["timing_ok"], 4800 * step <= 1800)
                self.assertEqual(r["valid"], r["timing_ok"])  # everything else passes on the strong toy
        # exactly on the limit is allowed: estimate 1800 at step 0.375
        ticks = iter(range(10 ** 7))
        with mock.patch.object(vc.time, "perf_counter", lambda: next(ticks) * 0.375):
            r = c.check()
        self.assertAlmostEqual(r["timing"]["estimate_s"], 1800.0)
        self.assertTrue(r["timing_ok"])

    def test_a_slow_check_makes_the_pair_invalid_with_a_reason(self):
        c = make_case(self, phi=0.99)
        with mock.patch.object(vc, "TIMING_LIMIT_S", 1e-6):
            r = c.check()
        self.assertFalse(r["timing_ok"] or r["valid"])
        self.assertTrue(r["v1"] and r["v2"] and r["mech_a"] and r["mech_b"])
        self.assertIn("estimate", r["reasons"]["timing"])
        self.assertIsNone(r["error_in"])  # slow is not an error

    def test_the_samples_are_the_timing_stream(self):
        from truth_gate import sampling
        c = make_case(self, phi=0.99)
        calls = []
        real = sampling.stream_rng

        def spy(seed, stream, i):
            if stream == "timing:plus":
                calls.append((seed, i))
            return real(seed, stream, i)

        with mock.patch.object(sampling, "stream_rng", spy):
            c.check()
        self.assertEqual(calls, [(SEED, i) for i in range(20)])

    def test_s_counts_worlds_controls_premises_and_pairs(self):
        c = make_case(self, phi=0.99)
        ref = os.path.join(c.dir, "reference.py")
        src = read(ref)
        src = src.replace('        "plus": World(plus),\n', '        "plus": World(plus),\n        "null": World(minus),\n')
        src = src.replace("    controls=[Control(", '    relational=[("x", "y")],\n    controls=[Control(')
        self.assertIn('"null"', src)
        self.assertIn("relational", src)
        with open(ref, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        t = c.check()["timing"]
        self.assertEqual((t["S"], t["S_formula"]), (7, 7))  # plus, minus, null, control, noise, zeros, one shuffle

    def test_a_failing_criterion_is_a_timing_error(self):
        c = make_case(self, fixed_body=body_returning('bool(d["missing_key"][0] > 0)'))
        r = c.check()
        self.assertFalse(r["timing_ok"])
        self.assertEqual(r["reasons"]["timing"], "error")
        self.assertIn("timing", r["error_stages"])


class ErrorStageTests(unittest.TestCase):
    """R2-11: error_in names the stage of the first error."""

    def test_faulty_exception_is_a_v1_error(self):
        c = make_case(self, faulty_body=body_returning('bool(d["missing_key"][0] > 0)'))
        r = c.check()
        self.assertEqual(r["error_in"], "V1")
        self.assertIn("KeyError", r["error_text"])
        self.assertFalse(r["valid"])
        self.assertEqual(set(r["error_stages"]), {"V1"})  # the fixed criterion and the timing check are fine

    def test_fixed_exception_is_a_v1_error_and_also_a_v2_and_timing_error(self):
        c = make_case(self, fixed_body=body_returning("1 / 0"))
        r = c.check()
        self.assertEqual(r["error_in"], "V1")
        self.assertEqual(set(r["error_stages"]), {"V1", "V2", "timing"})
        self.assertIn("ZeroDivisionError", r["error_text"])

    def test_uncomputable_statistic_is_a_structure_error(self):
        c = make_case(self, phi=0.99)
        priv = toy_case.private(0.99)
        priv["structure_statistic"]["code"] = "def stat(d):\n    return float('nan')\n"
        with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump(priv, f)
        r = c.check()
        self.assertEqual(r["error_in"], "structure")
        self.assertIn("not computable", r["error_text"])
        self.assertFalse(r["valid"])

    def test_failed_generation_in_the_mechanical_check_is_a_mech_error(self):
        c = make_case(self, phi=0.99)
        priv = toy_case.private(0.0)
        priv["structure_statistic"] = None
        priv["class"] = "B-1"  # D-R4-3: --no-structure is for the decoy classes only
        with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump(priv, f)
        ref = os.path.join(c.dir, "reference.py")
        src = read(ref)
        # the first minus sample ever drawn (the paired one of the minus analysis, since the structure check is skipped) fails
        old = 'def minus(rng):\n    """The claim is false: y does not depend on x; both series keep their autocorrelation."""\n'
        self.assertIn(old, src)
        src = src.replace(old, "CALLS = []\n\n\n" + old + '    CALLS.append(1)\n    if len(CALLS) == 1:\n        raise ValueError("first call")\n')
        with open(ref, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        r = c.check(no_structure=True)
        self.assertEqual(r["error_in"], "mech")
        self.assertEqual(r["reasons"]["mech_b"], "error")
        self.assertFalse(r["valid"])

    def test_a_clean_run_has_no_error_stage(self):
        r = make_case(self, phi=0.99).check()
        self.assertEqual((r["error_in"], r["error_text"], r["error_stages"]), (None, None, {}))

    def test_an_assemble_failure_is_a_setup_reason_not_an_error_stage(self):
        c = make_case(self, faulty_body="import math\n\ndef criterion(d):\n    return True\n")
        r = c.check()
        self.assertIsNone(r["error_in"])
        self.assertIn("setup", r["reasons"])


class DevRunTests(unittest.TestCase):
    """R2-25: only --samples 1000 --seed 20261117 is a validity run."""

    def test_flag_rules(self):
        problem = vc.run_flag_problem
        self.assertIsNone(problem(1000, 20261117, False, r"C:\work\case1"))
        self.assertIsNotNone(problem(200, 20261117, False, r"C:\work\case1"))
        self.assertIsNotNone(problem(1000, 1, False, r"C:\work\case1"))
        self.assertIsNone(problem(200, 1, True, r"C:\work\case1"))
        self.assertIsNone(problem(1000, 20261117, True, r"C:\work\case1"))
        for p in (r"C:\x\cases\D-001", "/x/cases/D-001", r"C:\x\Cases\D-001", r"C:\x\cases"):
            self.assertIsNotNone(problem(200, 1, True, p), p)
            self.assertIsNotNone(problem(1000, 20261117, True, p), p)  # --dev is refused there even with standard values
            self.assertIsNone(problem(1000, 20261117, False, p), p)  # a standard run is fine
        self.assertIsNone(problem(200, 1, True, r"C:\x\case\D-001"))  # "case" is not "cases"
        self.assertIsNone(problem(200, 1, True, r"C:\x\cases-old\D-001"))

    def test_other_values_need_dev(self):
        c = make_case(self, phi=0.99)
        r = c.cli(dev=False)  # 200 samples without --dev
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("--dev", r.stderr)
        self.assertFalse(os.path.exists(c.log) or os.path.exists(c.out))

    def test_dev_run_is_marked_in_result_and_log(self):
        c = make_case(self, phi=0.99)
        r = c.cli()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[dev]", r.stdout)
        with open(c.out, encoding="utf-8") as f:
            self.assertIs(json.load(f)["dev"], True)
        with open(c.log, encoding="utf-8") as f:
            entry = json.loads(f.read())
        self.assertIs(entry["dev"], True)
        self.assertIs(entry["result"]["dev"], True)

    def test_dev_is_refused_on_a_case_folder(self):
        c = make_case(self, phi=0.99)
        cases = os.path.join(c.tmp.name, "cases")
        folder = toy_case.write_case(os.path.join(cases, "D-001"), 0.99)
        r = c.cli(case_dir=folder)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertFalse(os.path.exists(c.log))

    def test_a_validity_run_with_the_standard_values_needs_no_flag(self):
        trivial = body_returning("False")
        c = make_case(self, faulty_body=trivial, fixed_body=trivial)
        r = common.run_tool("validity_check.py", "--case", c.dir, "--package-root", common.PKG, "--log", c.log,
                            "--out", c.out)  # the defaults are 1000 and 20261117
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)  # not valid (V1), but it ran
        with open(c.out, encoding="utf-8") as f:
            res = json.load(f)
        self.assertEqual((res["samples"], res["seed"], res["dev"]), (1000, 20261117, False))
        with open(c.log, encoding="utf-8") as f:
            self.assertIs(json.loads(f.read())["dev"], False)


class V1ErrorFreeTests(unittest.TestCase):
    """D-R4-3 (b), R3-3: the V1 label on the error-free samples is recorded next to the error."""

    def check(self, faulty_expr):
        body = ("import numpy as np\n\n\ndef criterion(d):\n    y0 = float(d['y'][0])\n    if y0 > 2.0:\n"
                "        raise ValueError('boom')\n    return " + faulty_expr + "\n")
        c = make_case(self, phi=0.0, faulty_body=body, fixed_body=body_returning("False"))
        return c.check()

    def test_a_low_faulty_rate_with_exceptions_is_v1a_on_the_error_free_samples(self):
        r = self.check("bool(y0 > 1.5)")  # holds on about 4.4% of the minus samples, raises on about 2.3%
        errors = r["counts"]["v1"]["errors_faulty"]
        self.assertGreater(errors, 0)
        self.assertFalse(r["v1"])
        self.assertEqual(r["reasons"]["v1"], "error")
        self.assertIsNone(r["v1_label"])
        e = r["v1_rate_on_error_free"]
        self.assertEqual(e["n"], N - errors)
        self.assertLess(e["faulty_holds"] / e["n"], r["kstar"] / 200)
        self.assertEqual(e["fixed_holds"], 0)
        self.assertEqual(r["v1_rate_label"], "V1a")
        self.assertFalse(r["valid"])

    def test_a_middle_rate_is_v1b_and_a_high_rate_would_pass(self):
        r = self.check("bool(y0 > 1.0)")  # about 13.6% on the error-free samples
        self.assertEqual((r["v1_label"], r["v1_rate_label"]), (None, "V1b"))
        r = self.check("bool(y0 > 0.0)")  # about 47.7%
        self.assertEqual((r["v1"], r["v1_label"], r["v1_rate_label"]), (False, None, None))
        self.assertGreater(r["v1_rate_on_error_free"]["faulty_holds"] / r["v1_rate_on_error_free"]["n"], 0.25)

    def test_the_counts_are_the_paired_error_free_ones(self):
        r = self.check("bool(y0 > 1.5)")
        errors = r["counts"]["v1"]["errors_faulty"]
        self.assertEqual(r["v1_rate_on_error_free"]["n"] + errors, N)
        # holds on the full sample set equal holds on the error-free ones (an exception is never a hold)
        self.assertEqual(r["counts"]["v1"]["faulty_holds"], r["v1_rate_on_error_free"]["faulty_holds"])

    def test_no_error_no_record(self):
        r = make_case(self, phi=0.99).check()
        self.assertIsNone(r["v1_rate_on_error_free"])
        self.assertIsNone(r["v1_rate_label"])

    def test_a_fixed_exception_also_gives_the_record(self):
        c = make_case(self, phi=0.0, faulty_body=body_returning('bool(d["y"][0] > 1.0)'),
                      fixed_body="import numpy as np\n\n\ndef criterion(d):\n    if d['y'][0] > 2.0:\n        raise ValueError('x')\n    return False\n")
        r = c.check()
        self.assertEqual((r["reasons"]["v1"], r["v1_label"], r["v1_rate_label"]), ("error", None, "V1b"))


class StatisticChecksTests(unittest.TestCase):
    """D-R4-3 (c) and (d), R3-8."""

    def spec(self, direction, note, null):
        return {"code": "def stat(d):\n    return 0.0\n", "direction": direction, "null_value": null, "note_value": note,
                "set_by_brief": False}

    def test_direction_problems(self):
        f = vc.statistic_problem
        self.assertEqual(vc.DIRECTIONS, ("greater", "less"))
        self.assertIsNone(f(self.spec("greater", 0.4, 0.0)))
        self.assertIsNone(f(self.spec("less", -0.4, 0.0)))
        self.assertIsNone(f(self.spec("less", 0.8, 1.0)))
        self.assertIsNone(f(self.spec("greater", 1.2, 1.0)))
        self.assertIsNone(f(self.spec("greater", 0.0, 0.0)))  # no sign: not refused
        self.assertIn("contradicts", f(self.spec("greater", -0.4, 0.0)))
        self.assertIn("contradicts", f(self.spec("less", 1.5, 1.0)))
        self.assertIn("direction must be one of", f(self.spec("up", 0.4, 0.0)))
        self.assertIn("direction must be one of", f(self.spec("Greater", 0.4, 0.0)))

    def test_a_contradicting_direction_is_a_usage_error(self):
        c = make_case(self, phi=0.99)
        priv = toy_case.private(0.99)
        priv["structure_statistic"]["direction"] = "less"  # note value above the null
        with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump(priv, f)
        with self.assertRaises(ValueError):
            c.check()
        r = c.cli()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("contradicts", r.stderr)
        self.assertFalse(os.path.exists(c.log))

    def test_an_unknown_direction_is_a_usage_error(self):
        c = make_case(self, phi=0.99)
        priv = toy_case.private(0.99)
        priv["structure_statistic"]["direction"] = "up"
        with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
            json.dump(priv, f)
        self.assertEqual(c.cli().returncode, 2)

    def test_the_directions_are_those_of_structure_stat(self):
        import inspect
        import structure_stat
        src = inspect.getsource(structure_stat.structure_stat)
        for d in vc.DIRECTIONS:
            self.assertIn(f'"{d}"', src)

    def test_no_structure_is_for_the_decoy_classes_only(self):
        for cls, ok in (("B-1", True), ("B-6", True), ("B-2", False), ("B-3", False), (None, False)):
            with self.subTest(cls):
                c = make_case(self, phi=0.99)
                priv = toy_case.private(0.99)
                priv["structure_statistic"] = None
                priv["class"] = cls
                with open(os.path.join(c.dir, "PRIVATE.json"), "w", encoding="utf-8") as f:
                    json.dump(priv, f)
                if ok:
                    self.assertTrue(c.check(no_structure=True)["valid"])
                    self.assertEqual(c.cli("--no-structure").returncode, 0)
                else:
                    with self.assertRaises(ValueError):
                        c.check(no_structure=True)
                    r = c.cli("--no-structure")
                    self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                    self.assertIn("decoy", r.stderr)
                    self.assertFalse(os.path.exists(c.log))


class DecisiveRunTests(unittest.TestCase):
    """D-R4-3 (e), R3-8: the first standard run on a set of input hashes is decisive."""

    def standard(self, c, *extra):
        return common.run_tool("validity_check.py", "--case", c.dir, "--package-root", common.PKG, "--log", c.log, "--out", c.out,
                               *extra)

    def lines(self, c):
        with open(c.log, encoding="utf-8") as f:
            return [json.loads(ln) for ln in f.read().splitlines()]

    def trivial_case(self, **kw):
        trivial = body_returning("False")
        return make_case(self, faulty_body=trivial, fixed_body=trivial, **kw)

    def test_the_log_location_is_fixed(self):
        # D-R5-3 (R3B-3): <parent of the case folder>/validity_log.jsonl, and nowhere else
        c = self.trivial_case()
        os.makedirs(os.path.join(c.tmp.name, "elsewhere"))
        for rel in ("other.jsonl", "validity_log.json", os.path.join("elsewhere", "validity_log.jsonl")):
            r = common.run_tool("validity_check.py", "--case", c.dir, "--package-root", common.PKG, "--log",
                                os.path.join(c.tmp.name, rel), "--out", c.out, "--samples", N, "--seed", SEED, "--dev")
            self.assertEqual(r.returncode, 2, (rel, r.stderr))
            self.assertIn("validity_log.jsonl", r.stderr)
            self.assertFalse(os.path.exists(os.path.join(c.tmp.name, rel)))
            self.assertFalse(os.path.exists(c.out))

    def test_the_log_option_may_be_omitted_or_equal_to_the_fixed_path(self):
        c = self.trivial_case()
        expected = os.path.join(c.tmp.name, "validity_log.jsonl")  # the case folder is <tmp>/case
        self.assertEqual(vc.log_path_for(c.dir), expected)
        self.assertEqual(vc.log_path_for(c.dir + os.sep), expected)
        r = common.run_tool("validity_check.py", "--case", c.dir, "--package-root", common.PKG, "--out", c.out,
                            "--samples", N, "--seed", SEED, "--dev")  # no --log
        self.assertIn(r.returncode, (0, 1), r.stderr)
        self.assertEqual(len(self.lines(c)), 1)
        r = common.run_tool("validity_check.py", "--case", c.dir, "--package-root", common.PKG, "--out", c.out, "--log",
                            expected, "--samples", N, "--seed", SEED, "--dev")
        self.assertIn(r.returncode, (0, 1), r.stderr)
        self.assertEqual(len(self.lines(c)), 2)

    def test_a_case_folder_in_a_cases_dir_logs_to_the_cases_dir(self):
        c = self.trivial_case()
        folder = toy_case.write_case(os.path.join(c.tmp.name, "cases_dir", "D-001"), 0.99, faulty_body=body_returning("False"),
                                     fixed_body=body_returning("False"))
        self.assertEqual(vc.log_path_for(folder), os.path.join(c.tmp.name, "cases_dir", "validity_log.jsonl"))
        self.assertTrue(vc.same_path(vc.log_path_for(folder), os.path.join(c.tmp.name, "cases_dir", "VALIDITY_LOG.JSONL"))
                        or os.name != "nt")

    def test_first_standard_run_is_decisive_and_the_next_is_not(self):
        c = self.trivial_case()
        self.assertIn(self.standard(c).returncode, (0, 1))
        self.assertIn(self.standard(c).returncode, (0, 1))
        first, second = self.lines(c)
        self.assertIs(first["decisive"], True)
        self.assertIs(second["decisive"], False)
        self.assertEqual((first["mode"], first["samples"], first["seed"], first["dev"]), ("validity", 1000, 20261117, False))

    def test_other_hashes_start_again(self):
        c = self.trivial_case()
        self.standard(c)
        with open(os.path.join(c.dir, "fixed_body.py"), "a", encoding="utf-8") as f:
            f.write("\n# a change\n")
        self.standard(c)
        self.assertEqual([e["decisive"] for e in self.lines(c)], [True, True])

    def test_a_dev_run_does_not_count_and_carries_no_decisive_field(self):
        c = self.trivial_case()
        r = common.run_tool("validity_check.py", "--case", c.dir, "--package-root", common.PKG, "--log", c.log, "--out", c.out,
                            "--samples", N, "--seed", SEED, "--dev")
        self.assertIn(r.returncode, (0, 1), r.stderr)
        self.assertNotIn("decisive", self.lines(c)[0])
        self.standard(c)
        self.assertEqual([e.get("decisive") for e in self.lines(c)], [None, True])  # the dev run did not make it non-decisive

    def test_a_dev_run_with_the_standard_values_carries_no_decisive_field(self):
        c = self.trivial_case()
        self.standard(c, "--dev")
        self.assertNotIn("decisive", self.lines(c)[0])
        self.assertIs(self.lines(c)[0]["dev"], True)

    def test_a_malformed_log_is_a_usage_error(self):
        c = self.trivial_case()
        with open(c.log, "w", encoding="utf-8") as f:
            f.write("not json\n")
        self.assertEqual(self.standard(c).returncode, 2)

    def test_standard_run_logged_function(self):
        c = self.trivial_case()
        hashes = {n: vc.sha256_file(os.path.join(c.dir, n)) for n in vc.INPUT_FILES}
        self.assertFalse(vc.standard_run_logged(c.log, hashes))  # no log yet
        entry = {"mode": "validity", "samples": 1000, "seed": 20261117, "dev": False, "sha256": dict(hashes)}
        other = {**entry, "samples": 200}
        timing = {**entry, "mode": "timing_arm"}
        dev = {**entry, "dev": True}
        with open(c.log, "w", encoding="utf-8") as f:
            for e in (other, timing, dev):
                f.write(json.dumps(e) + "\n")
        self.assertFalse(vc.standard_run_logged(c.log, hashes))
        with open(c.log, "a", encoding="utf-8") as f:
            f.write(json.dumps({**entry, "sha256": {**hashes, "reference.py": "0" * 64}}) + "\n")
        self.assertFalse(vc.standard_run_logged(c.log, hashes))  # one of the five hashes differs
        with open(c.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        self.assertTrue(vc.standard_run_logged(c.log, hashes))


class TimingArmTests(unittest.TestCase):
    """D-R4-3 (a), R3-2: the timing of the fixed body in a W-arm skeleton."""

    def make(self, arms=("W0", "W1")):
        c = make_case(self, phi=0.99)
        ref = read(os.path.join(c.dir, "reference.py"))
        os.makedirs(os.path.join(c.dir, "skeletons"), exist_ok=True)
        variants = {"W0": ref,
                    "W1": ref.replace('        "plus": World(plus),\n', '        "plus": World(plus),\n        "null": World(minus),\n')
                             .replace("    controls=[", '    relational=[("x", "y")],\n    controls=[', 1)}
        for arm in arms:
            with open(os.path.join(c.dir, "skeletons", f"{arm}.py"), "w", encoding="utf-8", newline="\n") as f:
                f.write(variants[arm])
        return c

    def lines(self, c):
        with open(c.log, encoding="utf-8") as f:
            return [json.loads(ln) for ln in f.read().splitlines()]

    def test_cli_runs_only_the_timing_and_logs_it(self):
        c = self.make()
        r = c.cli("--arm", "W1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(c.out, encoding="utf-8") as f:
            res = json.load(f)
        self.assertEqual((res["mode"], res["arm"], res["timing_ok"]), ("timing_arm", "W1", True))
        self.assertEqual(res["timing"]["S"], 7)  # plus, minus, null, control, noise, zeros, one shuffle
        self.assertEqual(res["timing"]["n"], 20)
        self.assertAlmostEqual(res["estimate_s"], 400 * 8 * (res["timing"]["t"] + res["timing"]["g"]))
        for key in ("counts", "v1", "v2", "mech_a", "mech_b", "valid", "details"):
            self.assertNotIn(key, res)  # no V1, V2 or structure check ran
        (entry,) = self.lines(c)
        self.assertEqual((entry["mode"], entry["arm"], entry["case"]), ("timing_arm", "W1", "TOY-1"))
        self.assertNotIn("decisive", entry)
        self.assertEqual(entry["sha256"]["skeleton"], vc.sha256_file(os.path.join(c.dir, "skeletons", "W1.py")))
        self.assertEqual(entry["sha256"]["fixed_body.py"], vc.sha256_file(os.path.join(c.dir, "fixed_body.py")))
        self.assertEqual(entry["result"], res)

    def test_w0_uses_its_own_skeleton(self):
        c = self.make()
        c.cli("--arm", "W0")
        c.cli("--arm", "W1")
        w0, w1 = self.lines(c)
        self.assertEqual((w0["arm"], w0["result"]["timing"]["S"], w1["arm"], w1["result"]["timing"]["S"]), ("W0", 5, "W1", 7))
        self.assertNotEqual(w0["sha256"]["skeleton"], w1["sha256"]["skeleton"])

    def test_stream_and_samples(self):
        from truth_gate import sampling
        c = self.make()
        calls = []
        real = sampling.stream_rng

        def spy(seed, stream, i):
            calls.append((seed, stream, i))
            return real(seed, stream, i)

        with mock.patch.object(sampling, "stream_rng", spy):
            res = vc.run_timing_arm(c.dir, common.PKG, SEED, "W0")
        self.assertEqual(calls, [(SEED, "timing:plus", i) for i in range(20)])
        self.assertTrue(res["timing_ok"])

    def test_the_fake_clock_decides_the_threshold(self):
        c = self.make()
        for step, ok in ((0.1, True), (0.5, False)):
            ticks = iter(range(10 ** 7))
            with mock.patch.object(vc.time, "perf_counter", lambda: next(ticks) * step):
                res = vc.run_timing_arm(c.dir, common.PKG, SEED, "W0")
            self.assertAlmostEqual(res["estimate_s"], 2 * 200 * 6 * 2 * step)  # S = 5 in W0
            self.assertEqual(res["timing_ok"], ok)

    def test_slow_arm_exits_1(self):
        c = self.make()
        with mock.patch.object(vc, "TIMING_LIMIT_S", 1e-6):
            self.assertEqual(vc.main(["--case", c.dir, "--package-root", common.PKG, "--log", c.log, "--out", c.out,
                                      "--arm", "W0"]), 1)
        with open(c.out, encoding="utf-8") as f:
            self.assertFalse(json.load(f)["timing_ok"])

    def test_a_failing_fixed_criterion_is_a_timing_error(self):
        c = self.make()
        with open(os.path.join(c.dir, "fixed_body.py"), "w", encoding="utf-8") as f:
            f.write(body_returning("1 / 0"))
        res = vc.run_timing_arm(c.dir, common.PKG, SEED, "W1")
        self.assertFalse(res["timing_ok"])
        self.assertEqual((res["error_in"], res["reasons"]["timing"]), ("timing", "error"))

    def test_a_body_that_does_not_assemble_into_the_arm(self):
        c = self.make()
        with open(os.path.join(c.dir, "fixed_body.py"), "w", encoding="utf-8") as f:
            f.write("import numpy as np\n\n\ndef criterion(d):\n    return bool(N > 1)\n")  # reads the skeleton's N
        res = vc.run_timing_arm(c.dir, common.PKG, SEED, "W0")
        self.assertFalse(res["timing_ok"])
        self.assertIn("reads module-level name N", res["reasons"]["setup"])
        self.assertEqual(c.cli("--arm", "W0").returncode, 1)

    def test_usage_errors(self):
        c = self.make(arms=("W0",))
        self.assertEqual(c.cli("--arm", "W1").returncode, 2)  # no skeletons/W1.py
        self.assertEqual(c.cli("--arm", "W0", "--no-structure").returncode, 2)
        self.assertEqual(c.cli("--arm", "W2").returncode, 2)  # not a choice
        self.assertEqual(c.cli("--arm", "W0", dev=False).returncode, 2)  # 200 samples without --dev
        self.assertFalse(os.path.exists(c.log))

    def test_arm_runs_need_neither_private_nor_reference(self):
        c = self.make()
        os.remove(os.path.join(c.dir, "PRIVATE.json"))
        os.remove(os.path.join(c.dir, "reference.py"))
        os.remove(os.path.join(c.dir, "faulty_body.py"))
        self.assertEqual(c.cli("--arm", "W0").returncode, 0)

    # --- D-R5-4 (R3B-4): which per-arm timing run decides
    def standard_arm(self, c, arm, *extra):
        return common.run_tool("validity_check.py", "--case", c.dir, "--package-root", common.PKG, "--out", c.out, "--arm", arm, *extra)

    def test_the_first_non_dev_run_on_two_hashes_is_decisive_and_later_ones_are_not(self):
        c = self.make()
        self.assertEqual(self.standard_arm(c, "W0").returncode, 0)
        with open(c.out, encoding="utf-8") as f:
            self.assertIs(json.load(f)["decisive"], True)
        self.assertEqual(self.standard_arm(c, "W0").returncode, 0)
        with open(c.out, encoding="utf-8") as f:
            self.assertIs(json.load(f)["decisive"], False)
        first, second = self.lines(c)
        self.assertEqual((first["mode"], first["decisive"], second["decisive"]), ("timing_arm", True, False))
        self.assertIs(first["result"]["decisive"], True)

    def test_another_skeleton_or_another_body_starts_again(self):
        c = self.make()
        self.standard_arm(c, "W0")
        self.standard_arm(c, "W1")  # another skeleton
        with open(os.path.join(c.dir, "fixed_body.py"), "a", encoding="utf-8") as f:
            f.write("\n# edited\n")
        self.standard_arm(c, "W0")  # another body
        self.assertEqual([e["decisive"] for e in self.lines(c)], [True, True, True])

    def test_dev_runs_carry_no_decisive_field_and_do_not_decide(self):
        c = self.make()
        c.cli("--arm", "W0")  # --dev, 200 samples
        self.standard_arm(c, "W0")
        dev, real = self.lines(c)
        self.assertNotIn("decisive", dev)
        self.assertIs(real["decisive"], True)  # the dev run did not make it a later run
        self.standard_arm(c, "W0", "--dev")
        self.assertNotIn("decisive", self.lines(c)[-1])

    def test_a_full_run_does_not_count_as_an_arm_run(self):
        c = self.make()
        self.standard_arm(c, "reference", "--dev")  # a validity run (dev) of the reference arm
        self.standard_arm(c, "W0")
        self.assertIs(self.lines(c)[-1]["decisive"], True)

    def test_timing_arm_logged_function(self):
        c = self.make()
        self.assertFalse(vc.timing_arm_logged(c.log, "s", "b"))
        with open(c.log, "w", encoding="utf-8") as f:
            f.write(json.dumps({"mode": "timing_arm", "dev": True, "sha256": {"skeleton": "s", "fixed_body.py": "b"}}) + "\n")
            f.write(json.dumps({"mode": "validity", "dev": False, "sha256": {"skeleton": "s", "fixed_body.py": "b"}}) + "\n")
            f.write(json.dumps({"mode": "timing_arm", "dev": False, "sha256": {"skeleton": "s", "fixed_body.py": "x"}}) + "\n")
        self.assertFalse(vc.timing_arm_logged(c.log, "s", "b"))
        with open(c.log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"mode": "timing_arm", "dev": False, "sha256": {"skeleton": "s", "fixed_body.py": "b"}}) + "\n")
        self.assertTrue(vc.timing_arm_logged(c.log, "s", "b"))

    def test_a_dev_arm_run_is_marked(self):
        c = self.make()
        c.cli("--arm", "W0")
        (entry,) = self.lines(c)
        self.assertIs(entry["dev"], True)
        self.assertNotIn("decisive", entry)


class DocstringTests(unittest.TestCase):
    def test_the_dev_guard_and_log_statements(self):
        doc = vc.__doc__
        self.assertIn("works by folder name", doc)
        self.assertIn("logged to the same", doc)
        self.assertIn("``validity_log.jsonl``", doc)


class V1FinalDropTests(unittest.TestCase):
    """D-R5-2 (R3B-2): ``v1_error_share`` and ``v1_final_drop_label`` on the 1000 standard samples."""

    @classmethod
    def setUpClass(cls):
        import_truth_gate(common.PKG)
        from truth_gate.sampling import stream_rng
        probe = make_case_dir(cls.addClassCleanup)
        ref = read(os.path.join(probe, "reference.py"))
        mod = load_study_module(assemble(ref, toy_case.FAULTY_BODY), "p.py", "t")
        cls.y0 = sorted((float(mod.STUDY.worlds["minus"].generate(stream_rng(SEED, "validity:minus", i))["y"][0])
                         for i in range(1000)), reverse=True)

    def run_case(self, errors, holds):
        """A faulty body that raises on the ``errors`` largest y[0] of the 1000 minus samples and holds on the next ``holds``."""
        y = self.y0
        t = (y[errors - 1] + y[errors]) / 2  # exactly ``errors`` samples have y0 > t
        c = (y[errors + holds - 1] + y[errors + holds]) / 2  # holds on t >= y0 > c: the next ``holds`` samples
        faulty = ("import numpy as np\n\n\ndef criterion(d):\n    y0 = float(d['y'][0])\n    if y0 > %r:\n"
                  "        raise ValueError('boom')\n    return bool(y0 > %r)\n" % (t, c))
        c_ = make_case(self, phi=0.0, faulty_body=faulty, fixed_body=body_returning("False"))
        return c_.check(samples=1000)

    def test_one_exception_in_1000_with_a_v1a_rate_is_a_final_drop_v1a(self):
        r = self.run_case(errors=1, holds=40)  # about 4% holds, below kstar/200 = 9%
        self.assertEqual(r["counts"]["v1"]["errors_faulty"], 1)
        self.assertAlmostEqual(r["v1_error_share"], 0.001)
        self.assertEqual(r["v1_rate_label"], "V1a")
        self.assertEqual(r["v1_final_drop_label"], "V1a")
        self.assertIsNone(r["v1_label"])  # v1_label stays null on an error
        self.assertEqual(r["reasons"]["v1"], "error")
        self.assertFalse(r["valid"])

    def test_sixty_exceptions_in_1000_give_no_final_drop_label(self):
        r = self.run_case(errors=60, holds=40)
        self.assertEqual(r["counts"]["v1"]["errors_faulty"], 60)
        self.assertAlmostEqual(r["v1_error_share"], 0.06)
        self.assertEqual(r["v1_rate_label"], "V1a")  # the rate label is still recorded
        self.assertIsNone(r["v1_final_drop_label"])  # but 6% of the samples erred: the error-repair row applies

    def test_a_v1b_rate_with_few_errors(self):
        r = self.run_case(errors=2, holds=130)  # about 13%: between kstar/200 and 25%
        self.assertEqual((r["v1_rate_label"], r["v1_final_drop_label"]), ("V1b", "V1b"))

    def test_a_rate_that_would_pass_is_not_a_drop(self):
        r = self.run_case(errors=2, holds=400)
        self.assertIsNone(r["v1_rate_label"])
        self.assertIsNone(r["v1_final_drop_label"])
        self.assertAlmostEqual(r["v1_error_share"], 0.002)

    def test_the_helper_boundary(self):
        f = vc.v1_final_drop_label
        self.assertEqual(f("V1a", 0.05), "V1a")  # at most 5%
        self.assertIsNone(f("V1a", 0.0501))
        self.assertEqual(f("V1b", 0.0), "V1b")
        self.assertIsNone(f(None, 0.01))
        self.assertIsNone(f("V1a", None))

    def test_without_a_v1_error_both_fields_are_null(self):
        r = make_case(self, phi=0.99).check()
        self.assertEqual((r["v1_error_share"], r["v1_final_drop_label"]), (None, None))

    def test_the_share_counts_either_twin(self):
        c = make_case(self, phi=0.0, faulty_body=body_returning('bool(d["y"][0] > 1.0)'),
                      fixed_body="import numpy as np\n\n\ndef criterion(d):\n    if d['y'][0] > 2.0:\n        raise ValueError('x')\n    return False\n")
        r = c.check()  # 200 samples
        self.assertEqual(r["reasons"]["v1"], "error")
        self.assertAlmostEqual(r["v1_error_share"], r["counts"]["v1"]["errors_fixed"] / 200)


if __name__ == "__main__":
    unittest.main()

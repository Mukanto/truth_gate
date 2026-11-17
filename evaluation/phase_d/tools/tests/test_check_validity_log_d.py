import hashlib
import json
import os
import tempfile
import unittest

import common
import check_validity_log_d as cv
import validity_check as vc

OUTCOME = {"valid": True, "v1": True, "v2": True, "mech_a": True, "mech_b": True, "timing_ok": True, "v1_label": None}
# what a logged result carries besides the outcome fields: the counts and timing the final-drop rule looks at
BODY = {"counts": {"v1": {"n": 1000}, "v2": {"plus": {"n": 1000}}}, "timing": {"estimate_s": 10.0}, "reasons": {},
        "error_stages": {}, "v1_final_drop_label": None}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        t = self.tmp.name
        self.cases = os.path.join(t, "cases_dir")
        os.makedirs(self.cases)
        self.log = os.path.join(self.cases, "validity_log.jsonl")  # D-R5-3: <cases>/validity_log.jsonl
        self.freeze = os.path.join(t, "FREEZE_VALIDITY.json")
        self.out = os.path.join(t, "report.json")
        self.entries = []

    def make_case(self, pid, tag=""):
        """A case folder of the five input files with small distinct contents; returns their hashes."""
        d = os.path.join(self.cases, pid)
        os.makedirs(d, exist_ok=True)
        hashes = {}
        for n in vc.INPUT_FILES:
            text = f"{pid} {n} {tag}\n"
            with open(os.path.join(d, n), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            hashes[n] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return hashes

    def entry(self, hashes, decisive=True, mode="validity", samples=1000, seed=20261117, dev=False, case="D-001", extra=None,
              **outcome):
        res = {**BODY, **OUTCOME, **(extra or {}), **outcome}
        e = {"case": case, "mode": mode, "samples": samples, "seed": seed, "dev": dev,
             "sha256": {**hashes, "tools/validity_check.py": "f" * 64}, "result": res}
        if decisive is not None:
            e["decisive"] = decisive
        self.entries.append(e)
        return e

    def result(self, hashes, decisive=True, **outcome):
        r = {"case": "D-001", "samples": 1000, "seed": 20261117, "input_sha256": dict(hashes), **OUTCOME, **outcome}
        if decisive is not None:
            r["decisive"] = decisive
        return r

    def write(self, pairs, timing_arms=None):
        with open(self.log, "w", encoding="utf-8") as f:
            for e in self.entries:
                f.write(json.dumps(e) + "\n")
        with open(self.freeze, "w", encoding="utf-8") as f:
            json.dump({"pairs": pairs, "note": "ignored"}, f)
        if timing_arms is not None:
            self.timing_path = os.path.join(self.tmp.name, "TIMING_ARMS.json")
            with open(self.timing_path, "w", encoding="utf-8") as f:
                json.dump(timing_arms, f)

    def run_tool(self, *extra):
        return common.run_tool("check_validity_log_d.py", "--freeze", self.freeze, "--cases", self.cases, "--out", self.out, *extra)

    def report(self):
        with open(self.out, encoding="utf-8") as f:
            return json.load(f)


class PassAndFailTests(Base):
    def test_a_pair_that_passes(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h)}])
        r = self.run_tool()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rep = self.report()
        self.assertTrue(rep["all_pass"])
        self.assertEqual((rep["n_pairs"], rep["n_pass"]), (1, 1))
        self.assertEqual(rep["pairs"][0]["checks"], {k: True for k in cv.CHECKS})
        self.assertEqual(rep["pairs"][0]["problems"], [])
        self.assertEqual([(x["log_line"], x["decisive"], x["same_hashes"]) for x in rep["pairs"][0]["runs"]], [(1, True, True)])

    def test_a_failed_validity_result_can_be_frozen_too_if_it_is_not_a_final_drop_in_history(self):
        # the check is of provenance: a decisive run whose outcome was "not valid" matches itself.  (It is the pair's own run,
        # not an earlier one, so the final-drop rule does not apply to it.)
        h = self.make_case("D-001")
        bad = {"valid": False, "v1": False, "v1_label": "V1a"}
        self.entry(h, **bad)
        self.write([{"id": "D-001", "result": self.result(h, **bad)}])
        self.assertEqual(self.run_tool().returncode, 0)

    def test_a_later_run_does_not_spoil_the_first_decisive_one(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.entry(h, decisive=False, valid=False)
        self.write([{"id": "D-001", "result": self.result(h)}])
        self.assertEqual(self.run_tool().returncode, 0)

    def test_dev_timing_and_other_runs_in_the_log_are_ignored(self):
        h = self.make_case("D-001")
        self.entry(h, decisive=None, dev=True, samples=200, seed=1, valid=False)
        self.entry(h, decisive=None, mode="timing_arm", valid=False)
        self.entry(h, decisive=None, dev=True, valid=False)  # standard values with --dev
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h)}])
        self.assertEqual(self.run_tool().returncode, 0)

    def test_two_pairs_one_fails(self):
        h1, h2 = self.make_case("D-001"), self.make_case("D-002")
        self.entry(h1)
        self.write([{"id": "D-001", "result": self.result(h1)}, {"id": "D-002", "result": self.result(h2)}])
        r = self.run_tool()
        self.assertEqual(r.returncode, 1)
        rep = self.report()
        self.assertEqual([p["pass"] for p in rep["pairs"]], [True, False])
        self.assertEqual((rep["n_pairs"], rep["n_pass"], rep["all_pass"]), (2, 1, False))

    def test_a_run_of_another_case_id_is_not_this_pairs_run(self):
        h = self.make_case("D-001")
        self.entry(h, case="D-002")  # same hashes, another brief id
        self.write([{"id": "D-001", "result": self.result(h)}])
        self.assertEqual(self.run_tool().returncode, 1)
        self.assertFalse(self.report()["pairs"][0]["checks"]["run_logged"])


class FailureTests(Base):
    def test_a_missing_run(self):
        h = self.make_case("D-001")
        self.entry(h, samples=200, seed=1, dev=True)  # only a dev run
        self.write([{"id": "D-001", "result": self.result(h)}])
        r = self.run_tool()
        self.assertEqual(r.returncode, 1)
        p = self.report()["pairs"][0]
        self.assertFalse(p["checks"]["run_logged"])
        self.assertIn("no standard run", p["problems"][0])

    def test_an_empty_log(self):
        h = self.make_case("D-001")
        self.write([{"id": "D-001", "result": self.result(h)}])
        self.assertEqual(self.run_tool().returncode, 1)

    def test_a_hash_mismatch_because_a_file_changed_after_the_run(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h)}])
        with open(os.path.join(self.cases, "D-001", "fixed_body.py"), "a", encoding="utf-8") as f:
            f.write("# edited after the run\n")
        r = self.run_tool()
        self.assertEqual(r.returncode, 1)
        p = self.report()["pairs"][0]
        self.assertFalse(p["checks"]["hashes"])
        self.assertIn("fixed_body.py", p["problems"][0])
        self.assertTrue(p["checks"]["run_logged"])  # the run exists, for the old file

    def test_a_hash_mismatch_in_the_freeze_itself(self):
        h = self.make_case("D-001")
        self.entry(h)
        r = self.result(h)
        r["input_sha256"]["PRIVATE.json"] = "0" * 64
        self.write([{"id": "D-001", "result": r}])
        self.assertEqual(self.run_tool().returncode, 1)
        p = self.report()["pairs"][0]
        self.assertFalse(p["checks"]["hashes"])
        self.assertFalse(p["checks"]["run_logged"])  # no logged run has the hashes the freeze claims

    def test_a_missing_case_file_or_folder(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h)}])
        os.remove(os.path.join(self.cases, "D-001", "reference.py"))
        self.assertEqual(self.run_tool().returncode, 1)
        self.assertIn("missing case file", self.report()["pairs"][0]["problems"][0])
        self.write([{"id": "D-009", "result": self.result(h)}])  # no such folder
        self.assertEqual(self.run_tool().returncode, 1)

    def test_a_non_decisive_run_cited(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.entry(h, decisive=False)
        self.write([{"id": "D-001", "result": self.result(h, decisive=False)}])
        self.assertEqual(self.run_tool().returncode, 1)
        p = self.report()["pairs"][0]
        self.assertFalse(p["checks"]["cites_decisive"])
        self.assertTrue(p["checks"]["first_is_decisive"])
        self.assertIn("not from a decisive run", " ".join(p["problems"]))

    def test_a_result_without_the_decisive_field(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h, decisive=None)}])
        self.assertEqual(self.run_tool().returncode, 1)
        self.assertFalse(self.report()["pairs"][0]["checks"]["cites_decisive"])

    def test_the_first_standard_run_must_be_the_decisive_one(self):
        h = self.make_case("D-001")
        self.entry(h, decisive=False)
        self.entry(h, decisive=True)
        self.write([{"id": "D-001", "result": self.result(h)}])
        self.assertEqual(self.run_tool().returncode, 1)
        self.assertFalse(self.report()["pairs"][0]["checks"]["first_is_decisive"])

    def test_two_runs_both_marked_decisive(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h)}])
        self.assertEqual(self.run_tool().returncode, 1)
        self.assertIn("also marked decisive", " ".join(self.report()["pairs"][0]["problems"]))

    def test_an_outcome_mismatch(self):
        for field, value in (("valid", False), ("v1", False), ("v2", False), ("mech_a", None), ("mech_b", False),
                             ("timing_ok", False), ("v1_label", "V1a")):
            with self.subTest(field):
                self.entries.clear()
                h = self.make_case("D-001")
                self.entry(h)
                self.write([{"id": "D-001", "result": self.result(h, **{field: value})}])
                self.assertEqual(self.run_tool().returncode, 1)
                p = self.report()["pairs"][0]
                self.assertFalse(p["checks"]["outcomes"])
                self.assertIn(field, p["problems"][-1])

    def test_a_duplicate_id(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h)}, {"id": "D-001", "result": self.result(h)}])
        self.assertEqual(self.run_tool().returncode, 1)
        self.assertIn("more than once", self.report()["pairs"][0]["problems"][-1])

    def test_a_pair_without_a_result(self):
        self.write([{"id": "D-001"}])
        self.assertEqual(self.run_tool().returncode, 1)


class HistoryTests(Base):
    """D-R5-3 (R3B-3): earlier decisive runs on other hashes, final drops and repairs."""

    V1B_DROP = {"valid": False, "v1": False, "v1_label": "V1b", "reasons": {"v1": "faulty rate 0.2 < 0.25"}}
    V1_ERROR = {"valid": False, "v1": False, "v1_label": None, "reasons": {"v1": "error"}, "error_stages": {"V1": ["boom"]}}

    def drop_then_pass(self, first):
        """A decisive run on H1 with outcome ``first``, an edit of reference.py, a passing decisive run on H2."""
        h1 = self.make_case("D-001", "v1")
        e = self.entry(h1)
        e["result"].update(first)
        h2 = self.make_case("D-001", "v2")  # the edit of reference.py (and, in this fake, of every file)
        self.entry(h2)
        return h1, h2

    def test_the_reviewers_probe_a_decisive_v1b_drop_then_a_passing_run_is_refused(self):
        h1, h2 = self.drop_then_pass(self.V1B_DROP)
        self.write([{"id": "D-001", "result": self.result(h2)}])
        r = self.run_tool()
        self.assertEqual(r.returncode, 1, r.stdout)
        p = self.report()["pairs"][0]
        self.assertFalse(p["checks"]["no_earlier_final_drop"])
        self.assertFalse(p["checks"]["repairs_listed"])  # one earlier decisive run, no repair listed
        self.assertTrue(p["checks"]["hashes"] and p["checks"]["run_logged"] and p["checks"]["outcomes"])
        self.assertIn("earlier final drop", " ".join(p["problems"]))
        self.assertEqual([(x["log_line"], x["same_hashes"], x["final_drop"]) for x in p["runs"]], [(1, False, True), (2, True, False)])

    def test_listing_a_repair_does_not_excuse_a_final_drop(self):
        h1, h2 = self.drop_then_pass(self.V1B_DROP)
        repairs = [{"file": "reference.py", "reason": "the world lacked the structure", "after_run_sha256": h2["reference.py"]}]
        self.write([{"id": "D-001", "result": self.result(h2), "repairs": repairs}])
        self.assertEqual(self.run_tool().returncode, 1)
        p = self.report()["pairs"][0]
        self.assertFalse(p["checks"]["no_earlier_final_drop"])
        self.assertTrue(p["checks"]["repairs_listed"])

    def test_a_legitimate_repair_passes(self):
        # an error on H1 (an exception in V1: a repair is allowed), one repair listed, a pass on H2
        h1, h2 = self.drop_then_pass(self.V1_ERROR)
        repairs = [{"file": "faulty_body.py", "reason": "KeyError in the body", "after_run_sha256": h2["faulty_body.py"]}]
        self.write([{"id": "D-001", "result": self.result(h2), "repairs": repairs}])
        r = self.run_tool()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.report()["pairs"][0]["pass"])

    def test_the_same_history_without_the_repair_listed_is_refused(self):
        h1, h2 = self.drop_then_pass(self.V1_ERROR)
        self.write([{"id": "D-001", "result": self.result(h2)}])
        self.assertEqual(self.run_tool().returncode, 1)
        p = self.report()["pairs"][0]
        self.assertTrue(p["checks"]["no_earlier_final_drop"])  # an error is not a final drop
        self.assertFalse(p["checks"]["repairs_listed"])
        self.assertIn("unlisted repair", " ".join(p["problems"]))

    def test_two_earlier_runs_need_two_repairs(self):
        h1, h2 = self.make_case("D-001", "a"), self.make_case("D-001", "b")
        h3 = self.make_case("D-001", "c")
        for h in (h1, h2):
            self.entry(h).update({"result": {**BODY, **OUTCOME, **self.V1_ERROR}})
        self.entry(h3)
        one = [{"file": "reference.py", "reason": "r", "after_run_sha256": "a" * 64}]
        self.write([{"id": "D-001", "result": self.result(h3), "repairs": one}])
        self.assertEqual(self.run_tool().returncode, 1)
        self.write([{"id": "D-001", "result": self.result(h3), "repairs": one * 2}])
        self.assertEqual(self.run_tool().returncode, 0)

    def test_final_drops_by_stage(self):
        cases = {
            "V1 computed": ({"v1": False, "reasons": {"v1": "faulty rate 0.1"}}, True),
            "V2 computed": ({"v2": False, "reasons": {"v2": "fixed criterion outside its bound on plus"}}, True),
            "timing computed": ({"timing_ok": False, "reasons": {"timing": "estimate 2000 s > 1800 s"}}, True),
            "non-null v1_final_drop_label": ({"v1": False, "v1_final_drop_label": "V1a", "reasons": {"v1": "error"},
                                              "error_stages": {"V1": ["x"]}}, True),
            "V1 error": ({"v1": False, "reasons": {"v1": "error"}, "error_stages": {"V1": ["x"]}}, False),
            "V2 error": ({"v2": False, "reasons": {"v2": "error"}, "error_stages": {"V2": ["x"]}}, False),
            "timing error": ({"timing_ok": False, "reasons": {"timing": "error"}, "error_stages": {"timing": ["x"]}}, False),
            "setup failure (nothing computed)": ({"v1": False, "v2": False, "timing_ok": False, "counts": {}, "timing": None,
                                                  "reasons": {"setup": "assemble_error: x"}}, False),
            "everything passed": ({}, False),
            "mech_a or mech_b failed": ({"mech_a": False, "mech_b": False, "valid": False}, False),
        }
        for name, (patch, drop) in cases.items():
            with self.subTest(name):
                self.assertEqual(cv.is_final_drop({**BODY, **OUTCOME, **patch}), drop, name)
        self.assertFalse(cv.is_final_drop(None))

    def test_earlier_runs_that_are_not_decisive_or_not_earlier_or_not_this_id_do_not_count(self):
        h1, h3 = self.make_case("D-001", "a"), self.make_case("D-001", "c")
        h2 = self.make_case("D-001", "b")  # the files on disk are the pair's
        h9 = self.make_case("D-009", "z")
        self.entry(h1, decisive=False).update({"result": {**BODY, **OUTCOME, **self.V1B_DROP}})  # not decisive
        self.entry(h9, case="D-009").update({"result": {**BODY, **OUTCOME, **self.V1B_DROP}})  # another id
        self.entry(h2)
        self.entry(h3).update({"result": {**BODY, **OUTCOME, **self.V1B_DROP}})  # later than the pair's run
        self.write([{"id": "D-001", "result": self.result(h2)}])
        self.assertEqual(self.run_tool().returncode, 0, self.run_tool().stdout)

    def test_dev_and_timing_runs_are_not_history(self):
        h1, h2 = self.make_case("D-001", "a"), self.make_case("D-001", "b")
        self.entry(h1, decisive=None, dev=True).update({"result": {**BODY, **OUTCOME, **self.V1B_DROP}})
        self.entry(h1, decisive=True, mode="timing_arm").update({"result": {**BODY, **OUTCOME, **self.V1B_DROP}})
        self.entry(h2)
        self.write([{"id": "D-001", "result": self.result(h2)}])
        self.assertEqual(self.run_tool().returncode, 0)

    def test_malformed_repairs(self):
        h = self.make_case("D-001")
        self.entry(h)
        for repairs in ("one", [{"file": "x"}], [{"file": "x", "reason": "y", "after_run_sha256": 5}], [None]):
            with self.subTest(repairs):
                self.write([{"id": "D-001", "result": self.result(h), "repairs": repairs}])
                self.assertEqual(self.run_tool().returncode, 1)
                self.assertIn("repairs", " ".join(self.report()["pairs"][0]["problems"]))

    def test_every_standard_run_of_the_id_is_listed_in_log_order(self):
        h1, h2 = self.make_case("D-001", "a"), self.make_case("D-001", "b")
        self.entry(h1).update({"result": {**BODY, **OUTCOME, **self.V1_ERROR}})
        self.entry(h1, decisive=False)
        self.entry(h2)
        self.entry(h2, decisive=False)
        self.entry(h2, decisive=None, dev=True)  # not standard: not listed
        repairs = [{"file": "reference.py", "reason": "r", "after_run_sha256": "a" * 64}]
        self.write([{"id": "D-001", "result": self.result(h2), "repairs": repairs}])
        self.run_tool()
        runs = self.report()["pairs"][0]["runs"]
        self.assertEqual([(x["log_line"], x["decisive"], x["same_hashes"]) for x in runs],
                         [(1, True, False), (2, False, False), (3, True, True), (4, False, True)])


class TimingArmsTests(Base):
    """D-R5-4 (R3B-4): the per-arm timing entries."""

    def arm_entry(self, case="D-001", arm="W1", skeleton="s" * 64, body="b" * 64, estimate=100.0, decisive=True, dev=False):
        e = {"case": case, "mode": "timing_arm", "arm": arm, "dev": dev, "seed": 20261117, "samples": 20,
             "sha256": {"skeleton": skeleton, "fixed_body.py": body}, "result": {"estimate_s": estimate, "timing_ok": estimate <= 1800}}
        if decisive is not None:
            e["decisive"] = decisive
        self.entries.append(e)
        return e

    def item(self, **kw):
        base = {"id": "D-001", "arm": "W1", "skeleton_sha256": "s" * 64, "body_sha256": "b" * 64, "estimate_s": 100.0, "redo": False}
        base.update(kw)
        return base

    def check(self, items):
        h = self.make_case("D-001")
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h)}], timing_arms=items)
        r = self.run_tool("--timing-arms", self.timing_path)
        return r, self.report()

    def test_matching_entries_pass(self):
        self.arm_entry(arm="W0", skeleton="a" * 64, estimate=250.5)
        self.arm_entry(arm="W1", estimate=2400.0)
        r, rep = self.check([self.item(arm="W0", skeleton_sha256="a" * 64, estimate_s=250.5, redo=False),
                             self.item(estimate_s=2400.0, redo=True)])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(rep["all_pass"])
        self.assertEqual([t["pass"] for t in rep["timing_arms"]], [True, True])
        self.assertEqual(rep["timing_arms"][0]["checks"], {"run_logged": True, "estimate_equal": True, "redo_correct": True})

    def test_no_decisive_run(self):
        self.arm_entry(decisive=False)
        self.arm_entry(skeleton="x" * 64)  # other hashes
        self.arm_entry(arm="W0")  # other arm
        self.arm_entry(case="D-002")  # other id
        self.arm_entry(decisive=None, dev=True)  # a dev run
        r, rep = self.check([self.item()])
        self.assertEqual(r.returncode, 1)
        t = rep["timing_arms"][0]
        self.assertFalse(t["checks"]["run_logged"])
        self.assertIn("no decisive timing_arm run", t["problems"][0])
        self.assertTrue(rep["pairs"][0]["pass"])  # the pairs are fine; all_pass is False because of the timing entry
        self.assertFalse(rep["all_pass"])

    def test_a_non_decisive_run_is_not_matched_even_with_the_same_estimate(self):
        self.arm_entry(decisive=False)
        r, rep = self.check([self.item()])
        self.assertEqual(r.returncode, 1)

    def test_an_estimate_mismatch(self):
        self.arm_entry(estimate=100.0)
        r, rep = self.check([self.item(estimate_s=101.0)])
        self.assertEqual(r.returncode, 1)
        t = rep["timing_arms"][0]
        self.assertTrue(t["checks"]["run_logged"])
        self.assertFalse(t["checks"]["estimate_equal"])

    def test_redo_must_be_true_exactly_above_1800(self):
        for est, redo, ok in ((1800.0, False, True), (1800.0, True, False), (1800.01, True, True), (1800.01, False, False),
                              (10.0, True, False), (10.0, False, True)):
            with self.subTest(est=est, redo=redo):
                self.entries.clear()
                self.arm_entry(estimate=est)
                r, rep = self.check([self.item(estimate_s=est, redo=redo)])
                self.assertEqual(rep["timing_arms"][0]["checks"]["redo_correct"], ok)
                self.assertEqual(r.returncode, 0 if ok else 1)

    def test_two_decisive_runs_on_the_same_hashes(self):
        self.arm_entry()
        self.arm_entry()
        r, rep = self.check([self.item()])
        self.assertEqual(r.returncode, 1)
        self.assertIn("2 decisive timing_arm runs", rep["timing_arms"][0]["problems"][0])

    def test_a_later_non_decisive_run_does_not_matter(self):
        self.arm_entry(estimate=100.0)
        self.arm_entry(estimate=999.0, decisive=False)
        r, rep = self.check([self.item()])
        self.assertEqual(r.returncode, 0, rep)

    def test_malformed_entries(self):
        for bad in ({"id": "D-001"}, self.item(redo="yes"), self.item(estimate_s="fast"), None, self.item(estimate_s=True)):
            with self.subTest(bad):
                r, rep = self.check([bad])
                self.assertEqual(r.returncode, 1)
                self.assertFalse(rep["timing_arms"][0]["pass"])

    def test_without_the_option_there_is_no_timing_section(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h)}])
        self.assertEqual(self.run_tool().returncode, 0)
        self.assertNotIn("timing_arms", self.report())

    def test_the_limit_is_the_tools(self):
        self.assertEqual(vc.TIMING_LIMIT_S, 1800.0)


class UsageErrorTests(Base):
    def test_usage_errors(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h)}])
        other = os.path.join(self.tmp.name, "validity_log.jsonl")  # right name, wrong place
        os.replace(self.log, other)
        self.assertEqual(self.run_tool("--log", other).returncode, 2)
        self.assertEqual(self.run_tool().returncode, 2)  # <cases>/validity_log.jsonl does not exist
        with open(self.log, "w", encoding="utf-8") as f:
            f.write("not json\n")
        self.assertEqual(self.run_tool().returncode, 2)  # malformed log
        self.write([{"id": "D-001", "result": self.result(h)}])
        with open(self.freeze, "w", encoding="utf-8") as f:
            f.write('{"no_pairs": []}')
        self.assertEqual(self.run_tool().returncode, 2)
        self.assertEqual(common.run_tool("check_validity_log_d.py", "--freeze", self.freeze).returncode, 2)
        self.write([{"id": "D-001", "result": self.result(h)}])
        self.assertEqual(self.run_tool("--timing-arms", os.path.join(self.tmp.name, "nope.json")).returncode, 2)

    def test_the_log_option_equal_to_the_fixed_path_is_accepted(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h)}])
        self.assertEqual(self.run_tool("--log", self.log).returncode, 0)

    def test_the_log_is_read_from_the_cases_folder(self):
        h = self.make_case("D-001")
        self.entry(h)
        self.write([{"id": "D-001", "result": self.result(h)}])
        elsewhere = os.path.join(self.tmp.name, "validity_log.jsonl")
        os.replace(self.log, elsewhere)  # a log next to the cases folder is not the log
        self.assertEqual(self.run_tool().returncode, 2)

    def test_the_outcome_fields_are_those_of_the_spec(self):
        self.assertEqual(cv.OUTCOME_FIELDS, ("valid", "v1", "v2", "mech_a", "mech_b", "timing_ok", "v1_label"))


class RoundTripWithValidityCheckTests(unittest.TestCase):
    """A real validity run (standard values, on a trivial toy case) is accepted by the checker, and a second one is not decisive."""

    def test_round_trip(self):
        import toy_case
        trivial = "import numpy as np\n\n\ndef criterion(d):\n    return False\n"
        with tempfile.TemporaryDirectory() as t:
            cases = os.path.join(t, "cases_dir")
            case = toy_case.write_case(os.path.join(cases, "TOY-1"), 0.99, faulty_body=trivial, fixed_body=trivial)
            out = os.path.join(t, "RESULT.json")
            args = ["--case", case, "--package-root", common.PKG, "--out", out]  # the log goes to <cases>/validity_log.jsonl
            common.run_tool("validity_check.py", *args)
            with open(out, encoding="utf-8") as f:
                first = json.load(f)
            common.run_tool("validity_check.py", *args)
            with open(out, encoding="utf-8") as f:
                second = json.load(f)
            self.assertTrue(os.path.isfile(os.path.join(cases, "validity_log.jsonl")))
            self.assertIs(first["decisive"], True)
            self.assertIs(second["decisive"], False)
            self.assertEqual(set(first["input_sha256"]), set(vc.INPUT_FILES))
            freeze = os.path.join(t, "FREEZE_VALIDITY.json")
            with open(freeze, "w", encoding="utf-8") as f:
                json.dump({"pairs": [{"id": "TOY-1", "result": first}]}, f)
            r = common.run_tool("check_validity_log_d.py", "--freeze", freeze, "--cases", cases)
            # the trivial bodies give V1 failures computed without error: the pair's own run is a final drop, but that is its own
            # run, not an earlier one; the history rule is about earlier runs on other hashes
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            with open(freeze, "w", encoding="utf-8") as f:
                json.dump({"pairs": [{"id": "TOY-1", "result": second}]}, f)
            r = common.run_tool("check_validity_log_d.py", "--freeze", freeze, "--cases", cases)
            self.assertEqual(r.returncode, 1)  # the second run is not decisive


if __name__ == "__main__":
    unittest.main()

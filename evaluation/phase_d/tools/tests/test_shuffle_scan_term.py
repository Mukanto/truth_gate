import difflib
import hashlib
import importlib.util
import json
import os
import random
import re
import tempfile
import unittest

import common
import shuffle_d
import scan_docs_d
import term_check_d

PC_TOOLS = os.path.join(common.PC, "tools")


def body_of(path):
    """A module's source after its docstring."""
    with open(path, encoding="utf-8") as f:
        src = f.read()
    return src[src.index('"""', 3) + 3:]


def items(n=30):
    out = []
    for k in range(n):
        out.append({"designer_id": f"X-{k:03d}", "class": ["B-2", "B-3", "B-1"][k % 3], "half": ["A", "B", None][k % 3],
                    "source": f"SRC{k % 5}", "subtype_or_tag": f"T{k % 4}", "reserve": k % 7 == 0,
                    "claim": f"Claim number {k} about a quantity.",
                    "data_keys": [{"key": "x", "shape": "(10, 3)", "dims": [10, 3], "dtype": "float64", "meaning": f"m{k}"}],
                    "sizes": f"10 units, case {k}"})
    return out


class ShuffleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        t = self.tmp.name
        self.freeze = os.path.join(t, "FREEZE_PREREG_D.json")
        with open(self.freeze, "wb") as f:
            f.write(b'{"freeze": 1}\n')
        self.items_path = os.path.join(t, "ITEMS.json")
        self.out = os.path.join(t, "out")

    def write_items(self, its):
        with open(self.items_path, "w", encoding="utf-8") as f:
            json.dump(its, f)

    def run_shuffle(self, *extra):
        return shuffle_d.main(["--items", self.items_path, "--seed-from", self.freeze, "--out", self.out, *extra])

    def read(self, name):
        with open(os.path.join(self.out, name), encoding="utf-8") as f:
            return json.load(f)

    def test_seed_formula(self):
        want = int(hashlib.sha256(b'{"freeze": 1}\n' + b"phase-d-shuffle").hexdigest(), 16)
        self.assertEqual(shuffle_d.seed_from(self.freeze), want)
        self.assertEqual(want, 81570934554082169359160531539684493479268373872724257719968181404946749950500)

    def test_fisher_yates_pinned_and_independent(self):
        seed = shuffle_d.seed_from(self.freeze)
        self.assertEqual(shuffle_d.shuffled_order(6, seed), [2, 0, 4, 5, 3, 1])
        for n in (1, 2, 5, 30, 72):
            rng = random.Random(seed)
            order = list(range(n))
            for i in reversed(range(1, n)):  # an independent writing of Fisher-Yates
                j = rng.randrange(i + 1)
                order[i], order[j] = order[j], order[i]
            self.assertEqual(shuffle_d.shuffled_order(n, seed), order)
            self.assertEqual(sorted(order), list(range(n)))

    def test_ids_batches_and_files(self):
        self.write_items(items(30))
        self.assertEqual(self.run_shuffle(), 0)
        pub = self.read("BRIEFS_SHUFFLED.json")
        self.assertEqual([p["id"] for p in pub], [f"D-{k:03d}" for k in range(1, 31)])
        self.assertEqual(sorted(os.listdir(self.out)), ["BATCH_01.json", "BATCH_02.json", "BATCH_03.json",
                                                         "BRIEFS_SHUFFLED.json", "ID_MAP_D.json"])
        sizes = [len(self.read(f"BATCH_0{b}.json")) for b in (1, 2, 3)]
        self.assertEqual(sizes, [12, 12, 6])
        flat = [b for n in (1, 2, 3) for b in self.read(f"BATCH_0{n}.json")]
        self.assertEqual(flat, pub)  # consecutive blocks of the shuffled list

    def test_seventy_two_items_make_six_batches_of_twelve(self):
        self.write_items(items(72))
        self.run_shuffle()
        self.assertEqual([len(self.read(f"BATCH_0{b}.json")) for b in range(1, 7)], [12] * 6)
        self.assertFalse(os.path.exists(os.path.join(self.out, "BATCH_07.json")))

    def test_map_has_the_private_fields_and_batches_have_none(self):
        its = items(30)
        self.write_items(its)
        self.run_shuffle()
        idmap = self.read("ID_MAP_D.json")
        by_designer = {m["designer_id"]: m for m in idmap}
        self.assertEqual(set(by_designer), {i["designer_id"] for i in its})
        for it in its:
            m = by_designer[it["designer_id"]]
            self.assertEqual({k: m[k] for k in ("class", "half", "source", "subtype_or_tag", "reserve")},
                             {k: it[k] for k in ("class", "half", "source", "subtype_or_tag", "reserve")})
            self.assertEqual(set(m), {"id", "designer_id", "class", "half", "source", "subtype_or_tag", "reserve"})
        # the public brief of neutral id D-nnn is the brief of its designer id
        pub = {p["id"]: p for p in self.read("BRIEFS_SHUFFLED.json")}
        for m in idmap:
            src = next(i for i in its if i["designer_id"] == m["designer_id"])
            self.assertEqual({k: pub[m["id"]][k] for k in ("claim", "data_keys", "sizes")},
                             {k: src[k] for k in ("claim", "data_keys", "sizes")})
        for name in os.listdir(self.out):
            if name.startswith(("BATCH_", "BRIEFS_")):
                with open(os.path.join(self.out, name), encoding="utf-8") as f:
                    text = f.read()
                for it in its:
                    self.assertNotIn(it["designer_id"], text)
                for rec in self.read(name):
                    self.assertEqual(set(rec), {"id", "claim", "data_keys", "sizes"})
                self.assertNotRegex(text, r'"(class|half|source|reserve|subtype_or_tag|designer_id)"')
                self.assertIn('"dims"', text)  # data_keys keep their dims

    def test_reserves_get_ordinary_ids(self):
        self.write_items(items(30))
        self.run_shuffle()
        for m in self.read("ID_MAP_D.json"):
            self.assertRegex(m["id"], r"^D-\d{3}$")

    def test_order_of_the_input_file_does_not_matter(self):
        its = items(30)
        self.write_items(its)
        self.run_shuffle()
        a = self.read("ID_MAP_D.json")
        random.Random(5).shuffle(its)
        self.write_items(its)
        self.run_shuffle("--force")
        self.assertEqual(self.read("ID_MAP_D.json"), a)

    def test_a_different_freeze_file_gives_another_order(self):
        self.write_items(items(30))
        self.run_shuffle()
        a = self.read("ID_MAP_D.json")
        with open(self.freeze, "wb") as f:
            f.write(b'{"freeze": 2}\n')
        self.run_shuffle("--force")
        self.assertNotEqual(self.read("ID_MAP_D.json"), a)

    def test_refuses_to_overwrite(self):
        self.write_items(items(5))
        self.run_shuffle()
        with self.assertRaises(SystemExit):
            self.run_shuffle()
        self.assertEqual(self.run_shuffle("--force"), 0)

    def test_bad_input(self):
        good = items(3)
        bad = {"duplicate": good + [dict(good[0])], "missing field": [{k: v for k, v in good[0].items() if k != "claim"}],
               "reserve not a bool": [{**good[0], "reserve": "yes"}], "empty": [], "too many": items(1000)}
        for name, its in bad.items():
            with self.subTest(name):
                self.write_items(its)
                with self.assertRaises(SystemExit):
                    self.run_shuffle("--force")
        self.write_items(good)
        with self.assertRaises(SystemExit):
            self.run_shuffle("--batch", "0")

    # --- D-R4-7 (R3-7): subset batches
    def subset(self, ids, *extra):
        path = os.path.join(self.tmp.name, "IDS.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ids, f)
        return shuffle_d.main(["--subset", path, "--out", self.out, *extra])

    def snapshot(self):
        out = {}
        for name in sorted(os.listdir(self.out)):
            if not name.startswith("batches_subset_"):
                with open(os.path.join(self.out, name), "rb") as f:
                    out[name] = hashlib.sha256(f.read()).hexdigest()
        return out

    def test_subset_batches_in_neutral_id_order_and_nothing_else_changes(self):
        self.write_items(items(72))
        self.run_shuffle()
        before = self.snapshot()
        pub = {b["id"]: b for b in self.read("BRIEFS_SHUFFLED.json")}
        ids = [f"D-{k:03d}" for k in (70, 3, 9, 5, 41, 17, 22, 8, 1, 60, 33, 50, 12, 64, 2, 7, 29, 31, 45, 11, 19, 26, 38, 55, 66)]
        self.assertEqual(self.subset(ids), 0)
        self.assertEqual(self.snapshot(), before)  # the item-2 files, the map and the neutral ids are untouched
        files = sorted(f for f in os.listdir(self.out) if f.startswith("batches_subset_"))
        self.assertEqual(files, ["batches_subset_01.json", "batches_subset_02.json", "batches_subset_03.json"])
        blocks = [self.read(f) for f in files]
        self.assertEqual([len(b) for b in blocks], [12, 12, 1])  # 25 ids: the last block is shorter
        flat = [b for blk in blocks for b in blk]
        self.assertEqual([b["id"] for b in flat], sorted(ids))
        for b in flat:
            self.assertEqual(b, pub[b["id"]])  # the same public brief under the same neutral id

    def test_exact_multiple_and_single_batch(self):
        self.write_items(items(72))
        self.run_shuffle()
        self.subset([f"D-{k:03d}" for k in range(1, 25)])
        self.assertEqual([len(self.read(f"batches_subset_0{n}.json")) for n in (1, 2)], [12, 12])
        self.assertFalse(os.path.exists(os.path.join(self.out, "batches_subset_03.json")))
        self.subset(["D-005", "D-002"], "--force")
        self.assertEqual([b["id"] for b in self.read("batches_subset_01.json")], ["D-002", "D-005"])
        self.assertFalse(os.path.exists(os.path.join(self.out, "batches_subset_02.json")))  # no stale file

    def test_batch_size_option(self):
        self.write_items(items(30))
        self.run_shuffle()
        self.subset([f"D-{k:03d}" for k in range(1, 8)], "--batch", "3")
        self.assertEqual([len(self.read(f"batches_subset_0{n}.json")) for n in (1, 2, 3)], [3, 3, 1])

    def test_no_private_field_in_the_subset_files(self):
        its = items(30)
        self.write_items(its)
        self.run_shuffle()
        self.subset([f"D-{k:03d}" for k in range(1, 15)])
        for name in ("batches_subset_01.json", "batches_subset_02.json"):
            with open(os.path.join(self.out, name), encoding="utf-8") as f:
                text = f.read()
            for it in its:
                self.assertNotIn(it["designer_id"], text)
            self.assertNotRegex(text, r'"(class|half|source|reserve|subtype_or_tag|designer_id)"')

    def test_subset_needs_neither_items_nor_seed(self):
        self.write_items(items(30))
        self.run_shuffle()
        os.remove(self.items_path)
        os.remove(self.freeze)
        self.assertEqual(self.subset(["D-001"]), 0)

    def test_subset_errors(self):
        self.write_items(items(30))
        self.run_shuffle()
        for name, ids in (("unknown id", ["D-001", "D-999"]), ("duplicate", ["D-001", "D-001"]), ("empty", []),
                          ("not strings", [1, 2]), ("not a list", {"D-001": 1})):
            with self.subTest(name), self.assertRaises(SystemExit):
                self.subset(ids)
        self.subset(["D-001"])
        with self.assertRaises(SystemExit):
            self.subset(["D-002"])  # existing subset files are not overwritten without --force
        self.assertEqual([b["id"] for b in self.read("batches_subset_01.json")], ["D-001"])
        with self.assertRaises(SystemExit):
            shuffle_d.main(["--subset", self.items_path, "--out", os.path.join(self.tmp.name, "nowhere")])  # no BRIEFS_SHUFFLED.json
        with self.assertRaises(SystemExit):
            shuffle_d.main(["--out", self.out])  # neither --items/--seed-from nor --subset

    def test_a_rerun_of_the_full_shuffle_still_gives_the_same_ids_the_subset_used(self):
        self.write_items(items(30))
        self.run_shuffle()
        first = self.read("ID_MAP_D.json")
        self.subset(["D-003", "D-004"])
        self.run_shuffle("--force")
        self.assertEqual(self.read("ID_MAP_D.json"), first)
        self.assertTrue(os.path.exists(os.path.join(self.out, "batches_subset_01.json")))  # the full run leaves it alone

    def test_the_documented_differences(self):
        doc = shuffle_d.__doc__
        self.assertIn("phase-d-shuffle", doc)
        self.assertIn("| seed |", doc)
        self.assertEqual((shuffle_d.SALT, shuffle_d.BATCH_SIZE), (b"phase-d-shuffle", 12))


class ScanDocsDTests(unittest.TestCase):
    def hits(self, text):
        with tempfile.TemporaryDirectory() as t:
            with open(os.path.join(t, "a.md"), "w", encoding="utf-8") as f:
                f.write(text + "\n")
            return scan_docs_d.scan(t)

    def tokens(self, text):
        h = self.hits(text)
        return h[0]["tokens"] if h else []

    def test_new_substring_tokens(self):
        for tok in ("validity audit", "case-world", "case-size", "case-fixed", "sub-threshold", "attributable",
                    "ratio-shared-denominator", "ratio-vs-denominator-proxy", "change-vs-baseline",
                    "shared-measured-component", "target-from-labels"):
            with self.subTest(tok):
                self.assertIn(tok, self.tokens(f"A line with {tok} in it."))
                self.assertIn(tok, self.tokens(f"A line with {tok.upper()} in it."))
        self.assertIn("attributable", self.tokens("unattributable"))

    def test_phase_d_decoy_and_checklist_tokens(self):
        # D-R4-8 (R3-13)
        for tok in ("Phase D", "decoy", "checklist"):
            with self.subTest(tok):
                self.assertIn(tok, self.tokens(f"A line with {tok} in it."))
                self.assertIn(tok, self.tokens(f"A line with {tok.upper()} in it."))
        self.assertIn("decoy", self.tokens("The decoys are written like the others."))  # substring match
        self.assertIn("checklist", self.tokens("The checklist names four kinds of dependence."))
        self.assertEqual(self.tokens("A plain sentence about the deco rating."), [])

    def test_the_difference_table_lists_the_new_tokens(self):
        doc = scan_docs_d.__doc__
        for tok in ('"Phase D"', '"decoy"', '"checklist"'):
            self.assertIn(tok, doc)

    def test_the_six_b2_subtype_names_on_word_boundaries(self):
        for tok in ("L1.1", "L1.2", "L1.3", "L1.4", "L3.1", "L3.2"):
            with self.subTest(tok):
                self.assertIn(tok, self.tokens(f"Use subtype {tok} here."))
                self.assertIn(tok, self.tokens(f"({tok})"))
        self.assertEqual(self.tokens("The value L1.10 and XL1.1 and L1x1 and L11."), [])
        self.assertEqual(self.tokens("Version 3.1 and L3 2."), [])

    def test_phase_cs_tokens_still_hit(self):
        for tok in ("Phase A", "Phase B", "Phase C", "world author", "evaluation", "REPORT", "pilot", "case study", "Tenkit",
                    "external", "detection rate", "private", "audit", "E1", "E2", "E3", "B-1", "B-6", "miss", "misses"):
            with self.subTest(tok):
                self.assertTrue(self.hits(f"text {tok} text"), tok)
        self.assertEqual(self.hits("Nothing special: missing permission and a clean sentence."), [])

    def test_token_lists_extend_phase_cs(self):
        spec = importlib.util.spec_from_file_location("scan_docs_pc", os.path.join(PC_TOOLS, "scan_docs.py"))
        pc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pc)
        self.assertEqual(scan_docs_d.SUBSTRING_TOKENS[:len(pc.SUBSTRING_TOKENS)], pc.SUBSTRING_TOKENS)
        self.assertEqual(scan_docs_d.BOUNDARY_TOKENS[:len(pc.BOUNDARY_TOKENS)], pc.BOUNDARY_TOKENS)
        self.assertEqual(len(scan_docs_d.SUBSTRING_TOKENS) - len(pc.SUBSTRING_TOKENS), 14)
        self.assertEqual(len(scan_docs_d.BOUNDARY_TOKENS) - len(pc.BOUNDARY_TOKENS), 6)

    def test_code_is_phase_cs_except_the_token_lists(self):
        pc = body_of(os.path.join(PC_TOOLS, "scan_docs.py")).splitlines()
        new = body_of(os.path.join(common.TOOLS, "scan_docs_d.py")).splitlines()
        changed = [ln for ln in difflib.unified_diff(pc, new, lineterm="", n=0)
                   if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
        for ln in changed:
            self.assertRegex(ln[1:], r'(SUBSTRING_TOKENS|"Tenkit"|BOUNDARY_TOKENS|\("miss"|Phase D additions|"validity audit"|"Phase D"|'
                                     r'"ratio-shared|"shared-measured)', ln)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as t:
            with open(os.path.join(t, "a.md"), "w", encoding="utf-8") as f:
                f.write("A clean line.\n")
            self.assertEqual(common.run_tool("scan_docs_d.py", t).returncode, 0)
            with open(os.path.join(t, "b.md"), "w", encoding="utf-8") as f:
                f.write("An attributable detection.\n")
            r = common.run_tool("scan_docs_d.py", t)
            self.assertEqual(r.returncode, 1)
            self.assertIn("b.md:1:An attributable detection.", r.stdout)
            self.assertEqual(common.run_tool("scan_docs_d.py", os.path.join(t, "nope")).returncode, 2)

    def test_allow_file_still_works(self):
        with tempfile.TemporaryDirectory() as t:
            with open(os.path.join(t, "b.md"), "w", encoding="utf-8") as f:
                f.write("Subtype L1.3 only.\n")
            allow = os.path.join(t, "allow.json")
            with open(allow, "w", encoding="utf-8") as f:
                json.dump({"listed": [{"file": "b.md", "text": "Subtype L1.3 only.", "tokens": ["L1.3"], "reason": "x"}]}, f)
            self.assertEqual(common.run_tool("scan_docs_d.py", t, "--allow", allow).returncode, 0)


class TermCheckDTests(unittest.TestCase):
    def test_banned_stems_are_phase_cs(self):
        spec = importlib.util.spec_from_file_location("term_check_pc", os.path.join(PC_TOOLS, "term_check.py"))
        pc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pc)
        self.assertEqual(term_check_d.STEMS, pc.STEMS)
        self.assertEqual([(n, rx.pattern) for n, rx in term_check_d.PATTERNS], [(n, rx.pattern) for n, rx in pc.PATTERNS])
        self.assertEqual(len(term_check_d.STEMS), 15)

    def test_code_is_identical_to_phase_cs(self):
        self.assertEqual(body_of(os.path.join(PC_TOOLS, "term_check.py")), body_of(os.path.join(common.TOOLS, "term_check_d.py")))

    def test_each_stem_is_found(self):
        words = {"circular": "circular", "double dip": "double-dip", "leak": "leakage", "pseudorepl": "pseudoreplication",
                 "coupl": "coupled", "spurious": "spurious", "non-independ": "non independent",
                 "regression to the mean": "regression to the mean", "selection bias": "selection bias",
                 "overfit": "overfitting", "inflat": "inflated", "contaminat": "contamination", "optimis": "optimistic"}
        for stem, word in words.items():
            with self.subTest(stem):
                brief = {"id": "D-001", "claim": f"A claim with {word}.", "sizes": "10 units",
                         "data_keys": [{"key": "x", "shape": "(10,)", "dims": [10], "dtype": "float64", "meaning": "plain"}]}
                self.assertTrue(term_check_d.check([brief]), word)

    def test_clean_brief_and_data_key_fields(self):
        clean = {"id": "D-001", "claim": "The mean exceeds zero.", "sizes": "10 units",
                 "data_keys": [{"key": "x", "shape": "(10,)", "dims": [10], "dtype": "float64", "meaning": "a series"}]}
        self.assertEqual(term_check_d.check([clean]), [])
        dirty = {**clean, "data_keys": [{**clean["data_keys"][0], "meaning": "leak indicator"}]}
        hits = term_check_d.check([dirty])
        self.assertEqual([(h["id"], h["field"]) for h in hits], [("D-001", "data_keys[0].meaning")])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "briefs.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump([{"id": "D-001", "claim": "Fine.", "sizes": "n", "data_keys": []}], f)
            self.assertEqual(common.run_tool("term_check_d.py", p).returncode, 0)
            with open(p, "w", encoding="utf-8") as f:
                json.dump([{"id": "D-001", "claim": "Coupling.", "sizes": "n", "data_keys": []}], f)
            self.assertEqual(common.run_tool("term_check_d.py", p).returncode, 1)
            self.assertEqual(common.run_tool("term_check_d.py", os.path.join(t, "nope.json")).returncode, 2)


if __name__ == "__main__":
    unittest.main()

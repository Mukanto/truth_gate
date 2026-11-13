"""Truth_Gate 0.4, stage (e): the documentation covers what the code can emit and offer."""

import os
import re
import unittest

import _helpers
from test_tools_stage_d import emitted_names
from truth_gate import cli, mutations, patterns

ROOT = _helpers.ROOT
DOC_FILES = ("README.md", "CHANGELOG.md", "docs/GATE.md", "docs/MANIFEST.md", "examples/README.md")


def read(path):
    with open(os.path.join(ROOT, path), "r", encoding="utf-8") as handle:
        return handle.read()


class TestFlagsAreDocumented(unittest.TestCase):
    def test_every_flag_and_note_the_code_can_emit_appears_in_gate_md(self):
        text = read("docs/GATE.md")
        names = emitted_names()
        self.assertGreaterEqual(len(names), 30)
        for required in ("K8_NOT_INVARIANT", "K8_INCONCLUSIVE", "K8_SOME_CHANGES", "SUGGESTED_UNREVIEWED",
                         "K6_EXTERNAL_UNGUARDED", "EXTERNAL_DIED"):
            self.assertIn(required, names)
        for name in sorted(names):
            with self.subTest(name=name):
                self.assertIn(f"`{name}", text)  # a backticked name (a family name may continue: `HIGH_RATE:<stream>`)

    def test_gate_md_documents_exit_code_7_schema_2_and_k8(self):
        text = read("docs/GATE.md")
        self.assertRegex(text, r"\| 7 \| `verify`")
        for field in ("tool_version", "input_kind", "manifest", "mutations", "k8", "m_k8", "pattern_stats",
                      "suggested_unreviewed", "study_notes", "non_claims", "known_limitations"):
            self.assertIn(f"`{field}`", text, field)
        self.assertIn("## K8: invariance", text)
        self.assertIn("2 · alpha_family", text)

    def test_the_flag_tables_mention_the_class_of_the_new_flags(self):
        rows = {m.group(1): m.group(2) for m in re.finditer(r"(?m)^\| `([A-Z0-9_]+)` \| ([^|]+) \|", read("docs/GATE.md"))}
        self.assertIn("mandatory", rows["K8_NOT_INVARIANT"])
        self.assertIn("capping", rows["K8_INCONCLUSIVE"])
        self.assertIn("info", rows["K8_SOME_CHANGES"])
        self.assertIn("capping", rows["SUGGESTED_UNREVIEWED"])


class TestManifestReference(unittest.TestCase):
    def test_every_pattern_and_mutation_op_appears_in_manifest_md(self):
        text = read("docs/MANIFEST.md")
        self.assertEqual(len(patterns.PATTERN_NAMES), 10)
        self.assertEqual(len(mutations.OPS), 11)
        for name in patterns.PATTERN_NAMES:
            with self.subTest(pattern=name):
                self.assertRegex(text, r"(?m)^\| `[^|]*\b" + re.escape(name) + r"\b[^|]*` \|")  # a row of the pattern table
        for op in mutations.OPS:
            with self.subTest(op=op):
                self.assertRegex(text, r"(?m)^\| `" + re.escape(op) + r"`")  # a row of the mutation table

    def test_manifest_md_names_the_tables_the_messages_and_the_revisions(self):
        text = read("docs/MANIFEST.md")
        for table in ("[study]", "[data]", "[worlds.<name>]", "[[criteria]]", "[[controls]]", "[[premises]]",
                      "[[invariances]]", "[budget]", "[targets]", "[external]"):
            self.assertIn(table, text, table)
        for message in ('"op": "hello"', '"op": "criterion"', '"op": "bye"', "tg-line/1", "ExternalTimeout",
                        "ExternalProtocolError", "ExternalDied", "ExternalError", "K6_EXTERNAL_UNGUARDED"):
            self.assertIn(message, text, message)
        for n in (3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23):
            self.assertIn(f"R-{n}", text, f"R-{n}")  # every revision that refines the manifest is cited

    def test_manifest_md_has_the_spec_example_that_is_the_test_manifest(self):
        text = read("docs/MANIFEST.md")
        manifest = read("tests/manifests/trial_example.toml")
        for line in manifest.splitlines():
            if line.strip():
                self.assertIn(line, text)


class TestReadme(unittest.TestCase):
    def test_readme_names_every_cli_command(self):
        text = read("README.md")
        commands = set(cli.build_parser()._subparsers._group_actions[0].choices)
        self.assertEqual(commands, {"check", "verify", "suggest", "init", "freeze", "badge", "explain"})
        for command in commands:
            self.assertRegex(text, r"(?m)^\| `" + command + r"\b", command)

    def test_readme_sections_of_stage_e(self):
        text = read("README.md")
        for heading in ("### Quick start without Python code", "### The command line", "### In CI", "## Roadmap"):
            self.assertIn(heading, text)
        for needle in ("tg-line/1", "examples/node_criterion/", "uses: Mukanto/truth_gate@v0.4.1", "Moved to 0.5",
                       "Phase B", "K6_EXTERNAL_UNGUARDED", "2 · alpha_family", "docs/EVALUATION.md",
                       "not covered by the leak guard", "Version 0.4.1"):
            self.assertIn(needle, text, needle)
        # The Phase A placeholder was replaced by the results after the final run (designer, 2026-11-12).
        self.assertIn("Phase A evaluation of 0.4: all four pre-registered criteria held.", text)
        self.assertIn("## 0.4 (spec 0.6, package 0.4.0): Phase A", read("docs/EVALUATION.md"))

    def test_the_readme_quick_start_manifest_is_the_test_manifest(self):
        text = read("README.md")
        for line in read("tests/manifests/trial_example.toml").splitlines():
            if line.strip():
                self.assertIn(line, text)

    def test_changelog_has_the_0_4_0_entry_with_its_deferrals(self):
        text = read("CHANGELOG.md")
        self.assertIn("## 0.4.0 (spec 0.6", text)
        for needle in ("Deferred to 0.5", "copy", "stale", "relabel", "glob", "Parquet", "Exit code 7"):
            self.assertIn(needle, text, needle)

    def test_examples_readme_lists_the_node_example(self):
        self.assertIn("node_criterion/", read("examples/README.md"))


class TestLinks(unittest.TestCase):
    def test_relative_links_of_the_documents_resolve(self):
        link = re.compile(r"\]\(([^)#\s]+)(#[^)\s]*)?\)")
        for doc in DOC_FILES:
            base = os.path.dirname(os.path.join(ROOT, doc))
            for match in link.finditer(read(doc)):
                target = match.group(1)
                if re.match(r"^[a-z]+:", target):
                    continue
                with self.subTest(doc=doc, target=target):
                    self.assertTrue(os.path.exists(os.path.normpath(os.path.join(base, target))), target)


if __name__ == "__main__":
    unittest.main()

"""Leak guard (spec section 5.6): blocking, allow-list, import-time loading, independence of tests."""

import hashlib
import importlib
import os
import shutil
import sys
import tempfile
import unittest

import _helpers
from _helpers import body, component, toy_path
import kapi
from kapi import guard


class TestLeakToys(unittest.TestCase):
    def test_open_outside_allow_list_is_blocked_and_flagged(self):
        b = body("toy_leak_open")
        self.assertIn("K6_LEAK_ATTEMPT", b["study_flags"])
        self.assertEqual(len(b["leak_log"]), 1)
        event = b["leak_log"][0]
        self.assertEqual(event["event"], "open")
        self.assertTrue(event["target"].endswith("leak_target.txt"))
        self.assertEqual(set(event), {"event", "target"})
        # blocked: the criterion could not complete, so it is UNDEFINED with a PermissionError
        self.assertEqual(component("toy_leak_open")["errors"]["world:plus"], {"PermissionError": 30})
        self.assertEqual(b["verdict"], "UNDEFINED")

    def test_listing_a_directory_is_flagged_even_if_the_error_is_swallowed(self):
        b = body("toy_leak_listdir")
        self.assertEqual([e["event"] for e in b["leak_log"]], ["os.listdir"])
        self.assertEqual(component("toy_leak_listdir")["verdict"], "FALSIFIABLE")
        self.assertEqual(b["verdict"], "NOT_FALSIFIABLE")

    def test_file_in_allow_paths_is_not_a_leak(self):
        b = body("toy_allowed_file")
        self.assertEqual(b["leak_log"], [])
        self.assertNotIn("K6_LEAK_ATTEMPT", b["study_flags"])
        self.assertEqual(b["verdict"], "FALSIFIABLE")

    def test_import_time_read_makes_the_study_unloadable(self):
        for toy in ("toy_import_leak", "toy_import_allowed_file"):
            b = body(toy)
            self.assertEqual(b["verdict"], "UNDEFINED", toy)
            self.assertEqual(b["load_error"], {"type": "PermissionError"}, toy)
            self.assertEqual(b["components"], [], toy)
            self.assertEqual(len(b["leak_log"]), 1, toy)
            self.assertEqual(b["leak_log"][0]["event"], "open", toy)
            self.assertIn("K6_LEAK_ATTEMPT", b["study_flags"], toy)

    def test_clean_study_has_empty_leak_log(self):
        self.assertEqual(body("toy_good")["leak_log"], [])


class TestAllowedFileHashing(unittest.TestCase):
    def test_changing_an_allowed_file_changes_the_certificate(self):
        tmp = tempfile.mkdtemp(prefix="kapi_test_")
        self.addCleanup(shutil.rmtree, tmp, True)
        study = os.path.join(tmp, "toy_allowed_file.py")
        data = os.path.join(tmp, "allowed_data.txt")
        shutil.copyfile(toy_path("toy_allowed_file"), study)
        shutil.copyfile(os.path.join(_helpers.TOYS, "allowed_data.txt"), data)
        first = kapi.run_gate(study)
        with open(data, "w") as handle:
            handle.write("1.0000\n")
        second = kapi.run_gate(study)
        self.assertNotEqual(first["body_sha256"], second["body_sha256"])
        with open(data, "rb") as handle:
            self.assertEqual(second["body"]["study"]["allowed_files"][0]["sha256"], hashlib.sha256(handle.read()).hexdigest())
        self.assertEqual(second["body"]["leak_log"], [])

    def test_missing_allowed_file_fails_closed(self):
        tmp = tempfile.mkdtemp(prefix="kapi_test_")
        self.addCleanup(shutil.rmtree, tmp, True)
        study = os.path.join(tmp, "toy_allowed_file.py")
        shutil.copyfile(toy_path("toy_allowed_file"), study)  # data file deliberately not copied
        b = kapi.run_gate(study)["body"]
        self.assertEqual(b["verdict"], "UNDEFINED")
        self.assertEqual(b["load_error"]["type"], "StudyError")


class TestIndependence(unittest.TestCase):
    """The hook stays installed for the process lifetime; the armed flag must not leak between runs."""

    def test_disarmed_after_runs_and_files_readable_again(self):
        body("toy_leak_open")
        self.assertFalse(guard.is_armed())
        with open(os.path.join(_helpers.TOYS, "leak_target.txt")) as handle:
            self.assertTrue(handle.read())
        self.assertEqual(len(os.listdir(_helpers.TOYS)) > 0, True)

    def test_disarmed_after_a_load_failure(self):
        body("toy_import_leak")
        self.assertFalse(guard.is_armed())
        with open(os.path.join(_helpers.TOYS, "leak_target.txt")) as handle:
            handle.read()

    def test_dont_write_bytecode_is_restored(self):
        before = sys.dont_write_bytecode
        kapi.run_gate(toy_path("toy_good_det"))
        self.assertEqual(sys.dont_write_bytecode, before)
        with guard.armed(__file__):
            self.assertTrue(sys.dont_write_bytecode)
        self.assertEqual(sys.dont_write_bytecode, before)

    def test_leaky_run_does_not_taint_the_next_run(self):
        kapi.run_gate(toy_path("toy_leak_open"))
        clean = kapi.run_gate(toy_path("toy_good"))
        self.assertEqual(clean["body"]["leak_log"], [])
        self.assertEqual(clean["body"]["verdict"], "FALSIFIABLE")

    def test_disarmed_after_an_exception_inside_the_context(self):
        with self.assertRaises(RuntimeError):
            with guard.armed(__file__):
                raise RuntimeError("boom")
        self.assertFalse(guard.is_armed())

    def test_nested_arming_is_refused(self):
        with guard.armed(__file__):
            with self.assertRaises(RuntimeError):
                with guard.armed(__file__):
                    pass
        self.assertFalse(guard.is_armed())

    def test_hook_does_nothing_while_disarmed(self):
        self.assertIsNone(guard._hook("open", (os.path.join(_helpers.TOYS, "leak_target.txt"), "r", 0)))
        self.assertIsNone(guard._hook("socket.connect", (None, ("example.invalid", 80))))


class TestHookEvents(unittest.TestCase):
    """Direct calls of the hook with synthetic event arguments; nothing real is opened, listed or spawned."""

    def blocked(self, event, args):
        with self.assertRaises(PermissionError):
            guard._hook(event, args)

    def test_each_intercepted_event_is_blocked_and_logged(self):
        leak = os.path.join(_helpers.TOYS, "leak_target.txt")
        cases = [
            ("open", (leak, "r", 0)),
            ("open", (leak.encode(), "rb", 0)),
            ("os.listdir", (_helpers.TOYS,)),
            ("os.scandir", (_helpers.TOYS,)),
            ("socket.connect", (None, ("example.invalid", 80))),
            ("socket.getaddrinfo", ("example.invalid", 80, 0, 0, 0)),
            ("subprocess.Popen", ("tool", ["tool", "--x"], None, None)),
            ("os.system", ("echo hi",)),
            ("os.exec", ("tool", ["tool"], None)),
            ("os.posix_spawn", ("tool", ["tool"], None)),
            ("os.spawn", (0, "tool", ["tool"], None)),
        ]
        with guard.armed(__file__):
            for event, args in cases:
                with self.subTest(event=event):
                    self.blocked(event, args)
            log = guard.take_log()
        self.assertEqual({e["event"] for e in log}, {e for e, _ in cases})
        self.assertTrue(all(set(e) == {"event", "target"} for e in log))

    def test_repeated_events_are_logged_once(self):
        leak = os.path.join(_helpers.TOYS, "leak_target.txt")
        with guard.armed(__file__):
            for _ in range(3):
                self.blocked("open", (leak, "r", 0))
            self.assertEqual(len(guard.take_log()), 1)

    def test_file_descriptors_are_ignored(self):
        with guard.armed(__file__):
            self.assertIsNone(guard._hook("open", (3, "r", 0)))
            self.assertIsNone(guard._hook("os.listdir", (4,)))
            self.assertEqual(guard.take_log(), [])

    def test_allow_list_entries(self):
        with guard.armed(__file__):
            # the study file itself, the kapi package, the interpreter prefixes
            self.assertIsNone(guard._hook("open", (__file__, "r", 0)))
            self.assertIsNone(guard._hook("open", (os.path.join(guard.PACKAGE_DIR, "stats.py"), "r", 0)))
            self.assertIsNone(guard._hook("open", (os.path.join(sys.prefix, "Lib", "os.py"), "r", 0)))
            self.assertIsNone(guard._hook("os.listdir", (guard.PACKAGE_DIR,)))
            # exact files only, and only after allow_file
            sibling = os.path.join(os.path.dirname(__file__), "test_stats.py")
            self.blocked("open", (sibling, "r", 0))
            guard.allow_file(sibling)
            self.assertIsNone(guard._hook("open", (sibling, "r", 0)))
            self.blocked("os.listdir", (os.path.dirname(__file__),))  # directories are never allowed by file entries
            guard.take_log()

    def test_allow_list_is_reset_between_runs(self):
        sibling = os.path.join(os.path.dirname(__file__), "test_stats.py")
        with guard.armed(__file__):
            guard.allow_file(sibling)
        with guard.armed(__file__):
            self.blocked("open", (sibling, "r", 0))
            guard.take_log()

    def test_direct_listing_of_working_directory_is_a_leak(self):
        with guard.armed(__file__):
            self.blocked("os.listdir", (os.getcwd(),))
            self.blocked("os.listdir", (None,))
            guard.take_log()

    def test_import_machinery_listings_are_not_leaks(self):
        """Lazily importing a stdlib module lists sys.path entries such as the working directory."""
        name = next((n for n in ("colorsys", "sched", "wave", "netrc", "quopri") if n not in sys.modules), None)
        if name is None:
            self.skipTest("no unloaded candidate module")
        importlib.invalidate_caches()  # force the path finders to list their directories again
        with guard.armed(__file__):
            importlib.import_module(name)
            self.assertEqual(guard.take_log(), [])
        self.assertIn(name, sys.modules)


if __name__ == "__main__":
    unittest.main()

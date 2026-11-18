"""Tests for world_run_check_v2.py (term scan with boundaries / decoded text / baseline, provenance by replay).
All transcripts are synthetic, built in tmp_path (pytest basetemp is redirected to designer\\tests\\work\\pytest_tmp by
conftest.py). The world-root constant is monkeypatched to <tmp>\\world so that replays run in tmp only. The v1 tests
(test_world_run_check.py) cover everything that v2 did not change."""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import world_run_check_v2 as w2  # noqa: E402
import test_world_run_check as t1  # noqa: E402  (Builder, Env, constants of the v1 tests)

needs_bash = pytest.mark.skipif(not os.path.isfile(w2.GIT_BASH), reason="Git bash not available")
LABEL = "w1"


class Env2(t1.Env):
    """Like the v1 Env, but the sandbox is <tmp>\\world\\w1 and run() calls world_run_check_v2.check_run."""

    def __init__(self, tmp):
        self.tmp = tmp
        self.world = tmp / "world"
        self.sb = self.world / LABEL
        self.sb.mkdir(parents=True)
        self.prompt = tmp / "prompt.md"
        self.prompt.write_bytes(t1.PROMPT_TEXT.encode("utf-8"))
        self.prompt_sha = hashlib.sha256(t1.PROMPT_TEXT.encode("utf-8")).hexdigest()
        self.expected = t1.PROMPT_TEXT.replace("<SANDBOX>", str(self.sb))
        self.meta = {"agentType": "general-purpose", "isBuiltIn": True, "spawnDepth": 1, "requestShape": "background",
                     "model": "opus", "pickedEffortModel": t1.OPUS, "finished": True, "toolUseId": "toolu_x"}
        self.base_files = {}
        self.n_replays = 0

    def base_file(self, rel, data):
        """A file that exists in the sandbox before the agent ran and is listed in the manifest."""
        data = data if isinstance(data, bytes) else data.encode("utf-8")
        self.disk(rel, data)
        self.base_files[rel.replace("/", "\\")] = hashlib.sha256(data).hexdigest()

    def write_baseline(self, strings=("nothing",)):
        p = self.tmp / "baseline.jsonl"
        with open(p, "w", encoding="utf-8") as f:
            for s in strings:
                f.write(json.dumps({"type": "user", "message": {"content": s}}, ensure_ascii=False) + "\n")
        return p, hashlib.sha256(p.read_bytes()).hexdigest()

    def run(self, b, patterns=("nothing_*",), prefix=None, terms=None, baseline=("nothing",), baseline_sha=None,
            replay=True, replay_dir=None, timeout=60, force=False, manifest_extra=None):
        t = self.tmp / "agent-agentA.jsonl"
        b.save(t)
        m = self.tmp / "agent.meta.json"
        m.write_text(json.dumps(self.meta), encoding="utf-8")
        pre = None
        if prefix is not None:
            pre = self.tmp / "agent.prefix.json"
            pre.write_text(json.dumps(prefix), encoding="utf-8")
        tf = None
        if terms is not None:
            tf = self.tmp / "terms.txt"
            tf.write_text("\n".join(terms) + "\n", encoding="utf-8")
        bpath, bsha = self.write_baseline(baseline)
        manifest = self.tmp / "MANIFEST.json"
        mdata = {f"{LABEL}\\{rel}": sha for rel, sha in self.base_files.items()}
        mdata.update(manifest_extra or {})
        manifest.write_text(json.dumps(mdata), encoding="utf-8")
        if replay_dir is None and replay:
            self.n_replays += 1
            replay_dir = self.tmp / "replays" / f"r{self.n_replays}"
        return w2.check_run(str(t), str(m), str(self.sb), list(patterns), str(pre) if pre else None, None,
                            str(tf) if tf else None, str(self.prompt), frozen_sha=self.prompt_sha,
                            baseline_path=str(bpath), baseline_sha=baseline_sha or bsha, manifest_path=str(manifest),
                            replay_dir=str(replay_dir) if replay_dir else None, replay_timeout=timeout,
                            force_replay=force)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(w2, "WORLD_ROOT", str(tmp_path / "world"))
    return Env2(tmp_path)


def prov(res, rel):
    return res["provenance"][rel]


def reasons_text(res):
    return " | ".join(res["reasons"])


# ------------------------------------------------------------------ term scan: boundaries
def hit_terms(term, text):
    return [h["term"] for h in w2.scan_terms([(term, w2.term_regex(term))], "loc", "b_attachment", [text])]


@pytest.mark.parametrize("term,text,hit", [
    ("SELECTION_", "see SELECTION_provisional.json now", True),
    ("SELECTION_", "the tool_selection_hierarchy table", False),
    ("SELECTION_", "x-selection_y", True),  # '-' before is no word character
    ("B-1", "case B-1 is open", True),
    ("B-1", "case (B-1) is open", True),
    ("B-1", "case b-1 lower", True),  # still case-insensitive
    ("B-1", "id 4ab-1f here", False),
    ("B-1", "id 4ab-1", False),  # a letter before
    ("B-1", "B-10", False),  # a digit after
    ("L1.1", "see L1.1 here", True),
    ("L1.1", "see L1.10 here", False),
    ("L1.1", "ends with L1.1", True),
    ("L1.1", "L1.1.", True),
    ("structure\\", "the DOM structure\\ marker", True),  # a real backslash
    ("structure\\", "the DOM structure here", False),
    ("structure\\", "the DOM restructure\\ marker", False),  # a letter before the alphanumeric first char
    ("_marker", "a _marker b", True),  # a '_' first char needs no boundary before it ...
    ("_marker", "a_marker b", True),
    ("_marker", "a _marker_x b", False),  # ... but the alphanumeric last char 'r' must not touch '_'
])
def test_boundary_rule(term, text, hit):
    assert (hit_terms(term, text) != []) is hit


def test_boundary_start_and_end_of_string():
    assert hit_terms("B-1", "B-1") != []
    assert hit_terms("B-1", "B-1 tail") != []
    assert hit_terms("B-1", "head B-1") != []


def test_hit_record_fields_and_counts():
    hits = w2.scan_terms([("zzterm", w2.term_regex("zzterm"))], "loc", "a_remainder",
                         ["one zzterm and ZZTerm", "none here", "third zzterm"])
    assert len(hits) == 1
    h = hits[0]
    assert h["count"] == 3 and h["count_new"] == 3 and h["count_baseline"] == 0 and h["baseline"] is False
    assert "zzterm" in h["window"].lower() and h["location"] == "loc" and h["group"] == "a_remainder"


# ------------------------------------------------------------------ term scan: decoded text
def test_json_escape_is_not_a_backslash_hit(env):
    b = env.start()
    b.attach({"type": "x", "content": "a\nb structure\nc"})  # a real newline in the decoded string
    b.text("x")
    res = env.run(b, terms=["structure\\"])
    assert res["term_hits"] == [] and res["valid"] is True


def test_real_backslash_in_decoded_text_is_a_hit(env):
    b = env.start()
    b.attach({"type": "x", "content": "path with structure\\ in it"})
    b.text("x")
    res = env.run(b, terms=["structure\\"])
    assert [h["group"] for h in res["term_hits"]] == ["b_attachment"]
    assert res["term_hits"][0]["baseline"] is False and res["valid"] is False


def test_hit_in_a_json_key_or_uuid_text_is_not_scanned(env):
    b = env.start()
    b.attach({"type": "x", "selection_key": "fine", "id": "4ab-1f"})
    b.text("x")
    res = env.run(b, terms=["B-1", "selection_key"])
    assert res["term_hits"] == [] and res["valid"] is True


def test_hit_in_nested_leaf_prefix_and_blob(env):
    b = env.start(remainder="\nplain")
    b.raw({"type": "api-request-blob", "agentId": "agentA", "sessionId": "sessionS", "hash": "h",
           "message": {"role": "user", "content": [{"type": "text", "text": "a zzterm here"}]}})
    b.text("x")
    res = env.run(b, terms=["zzterm"], prefix={"state": {"names": ["x", {"deep": "ZZTerm!"}]}})
    assert sorted(h["group"] for h in res["term_hits"]) == ["c_prefix", "e_request_blob"]
    assert res["valid"] is False  # the prefix hit is new and invalidates


# ------------------------------------------------------------------ term scan: baseline
BASE_LEAF = "intro words 12345 the zzterm appears here and trailing words 67890 outro"


def test_baseline_hit_does_not_invalidate(env):
    b = env.start()
    b.attach({"type": "skills", "content": BASE_LEAF})
    b.text("x")
    res = env.run(b, terms=["zzterm"], baseline=("unrelated", BASE_LEAF + " and a longer tail"))
    h = res["term_hits"][0]
    assert h["baseline"] is True and h["count_baseline"] == 1 and h["count_new"] == 0
    assert res["term_hits_baseline"] == 1 and res["term_hits_new"] == 0 and res["term_hits_new_invalidating"] == 0
    assert res["valid"] is True and res["baseline_ok"] is True and len(res["baseline_sha256"]) == 64


def test_new_hit_invalidates(env):
    b = env.start()
    b.attach({"type": "skills", "content": "something else entirely, a zzterm in new surroundings"})
    b.text("x")
    res = env.run(b, terms=["zzterm"], baseline=(BASE_LEAF,))
    h = res["term_hits"][0]
    assert h["baseline"] is False and h["window"].startswith("something") is True
    assert res["term_hits_new"] == 1 and res["term_hits_baseline"] == 0
    assert res["valid"] is False and "not in the baseline" in reasons_text(res)


def test_window_is_30_chars_each_side_and_case_sensitive(env):
    leaf = "A" * 40 + " zzterm " + "B" * 40
    b = env.start()
    b.attach({"type": "x", "content": "C" * 40 + " zzterm " + "B" * 40})  # differs inside the 30 chars before
    b.attach({"type": "x", "content": "A" * 31 + " zzterm " + "B" * 31 + "tail"})  # window equals a substring
    b.attach({"type": "x", "content": "a" * 31 + " zzterm " + "B" * 31})  # case differs inside the window
    b.text("x")
    res = env.run(b, terms=["zzterm"], baseline=(leaf,))
    flags = [h["baseline"] for h in res["term_hits"]]
    assert flags == [False, True, False]
    assert res["term_hits"][1]["window"] == "A" * 29 + " zzterm " + "B" * 29


def test_window_must_be_inside_a_single_baseline_leaf(env):
    b = env.start()
    b.attach({"type": "x", "content": "left side zzterm right side"})
    b.text("x")
    res = env.run(b, terms=["zzterm"], baseline=("left side zzt", "erm right side"))
    assert res["term_hits"][0]["baseline"] is False


def test_mixed_matches_in_one_location(env):
    b = env.start()
    b.attach({"type": "x", "content": [BASE_LEAF, "a different zzterm context"]})
    b.text("x")
    res = env.run(b, terms=["zzterm"], baseline=(BASE_LEAF,))
    h = res["term_hits"][0]
    assert h["count"] == 2 and h["count_baseline"] == 1 and h["count_new"] == 1 and h["baseline"] is False
    assert "different" in h["window"] and res["valid"] is False


def test_baseline_applies_to_remainder_and_prompt_groups(env):
    b = env.start(remainder="\n" + BASE_LEAF)
    b.text("x")
    res = env.run(b, terms=["zzterm"], baseline=("\n" + BASE_LEAF + " tail",))  # the window starts at the "\n"
    assert [(h["group"], h["baseline"]) for h in res["term_hits"]] == [("a_remainder", True)]
    assert res["valid"] is True


def test_wrong_baseline_hash_is_an_error(env):
    b = env.start()
    b.text("x")
    with pytest.raises(ValueError, match="sha256"):
        env.run(b, terms=["zzterm"], baseline_sha="0" * 64)


def test_no_terms_means_no_baseline_use(env):
    b = env.start()
    b.text("x")
    res = env.run(b, baseline_sha="0" * 64)  # not read without --terms
    assert res["baseline_sha256"] is None and res["baseline_ok"] is None
    assert res["term_hits"] == [] and res["term_hits_baseline"] == 0 and res["term_hits_new"] == 0


@pytest.mark.skipif(not os.path.isfile(w2.DEFAULT_BASELINE), reason="baseline transcript not on this machine")
def test_hard_coded_baseline_hash_matches_the_recorded_file():
    base, sha = w2.load_baseline(w2.DEFAULT_BASELINE, w2.BASELINE_SHA256)
    assert sha == w2.BASELINE_SHA256 and base.n_leaves > 0
    assert base.contains(next(iter(base.leaves))[:50])
    with pytest.raises(ValueError):
        w2.load_baseline(w2.DEFAULT_BASELINE, "0" * 64)


# ------------------------------------------------------------------ path rewriting (no process is started)
def test_rewriter_all_spellings(tmp_path):
    sb = r"E:\Claude Projects\Kapi\phase_d_work\world\cd14f4"
    phase = r"E:\Claude Projects\Kapi\phase_d_work"
    rep_root = str(tmp_path / "rep" / "root")
    rep_sb = os.path.join(rep_root, "world", "cd14f4")
    rw = w2.PathRewriter(sb, phase, rep_sb, rep_root)
    drive = rep_root[0]
    fwd_sb = rep_sb.replace("\\", "/")
    cases = [
        (sb + r"\skeletons\a.py", rep_sb + r"\skeletons\a.py"),
        (sb.replace("\\", "/") + "/skeletons/a.py", fwd_sb + "/skeletons/a.py"),
        ("/e/Claude Projects/Kapi/phase_d_work/world/cd14f4/a.py", "/" + drive.lower() + fwd_sb[2:] + "/a.py"),
        (sb.replace("\\", "\\\\") + "\\\\skeletons", rep_sb.replace("\\", "\\\\") + "\\\\skeletons"),
        (sb.upper() + r"\x", rep_sb + r"\x"),  # case-insensitive
        (phase + r"\transcripts\t.jsonl", rep_root + r"\transcripts\t.jsonl"),
        ("cd /e/Claude Projects/Kapi/phase_d_work && ls", "cd /" + drive.lower() + rep_root.replace("\\", "/")[2:]
         + " && ls"),
    ]
    for src, want in cases:
        assert rw.rewrite(src) == want, src
    # the sandbox boundary: cd14f4x is not the sandbox, it falls back to the phase root rewrite
    assert rw.rewrite(sb + "x\\a") == rep_root + "\\world\\cd14f4x\\a"
    for ok in (rw.rewrite(sb + r"\skeletons\a.py"), rw.rewrite(phase + r"\x")):
        assert rw.residue(ok) == []


@pytest.mark.parametrize("cmd,refused", [
    (r'type "E:\Other\secret.txt"', True),
    ("type E:/Other/secret.txt", True),
    ("cat /e/Other/secret.txt", True),
    (r'dir C:\Users\someone', True),
    (r'"C:\Users\u\AppData\Local\Python\pythoncore-3.14-64\python.exe" -c 1', False),
    (r'"C:\Users\u\AppData\Local\Microsoft\WindowsApps\python.exe" -c 1', False),
    ("echo hello; cd skeletons", False),
    ("curl https://example.com/e/x", False),
    ("sed 's/e/x/' f.txt", False),
])
def test_residue_refusal_rules(tmp_path, cmd, refused):
    rep_root = str(tmp_path / "rep" / "root")
    rw = w2.PathRewriter(r"E:\Claude Projects\Kapi\phase_d_work\world\cd14f4",
                         r"E:\Claude Projects\Kapi\phase_d_work", os.path.join(rep_root, "world", "cd14f4"), rep_root)
    assert bool(rw.residue(rw.rewrite(cmd))) is refused


def test_map_to_sandbox_rel(tmp_path):
    sb = r"E:\Claude Projects\Kapi\phase_d_work\world\cd14f4"
    f = w2.map_to_sandbox_rel
    assert f(sb + r"\skeletons\a.py", None, sb) == os.path.join("skeletons", "a.py")
    assert f("e:/claude projects/kapi/phase_d_work/world/CD14F4/x.txt", None, sb) == "x.txt"
    assert f("/e/Claude Projects/Kapi/phase_d_work/world/cd14f4/x.txt", None, sb) == "x.txt"
    assert f("x.txt", sb, sb) == "x.txt"  # relative, resolved against the call cwd
    assert f(sb + "2\\x.txt", None, sb) is None  # sibling with the same prefix
    assert f(sb + r"\..\other\x.txt", None, sb) is None
    assert f(r"E:\elsewhere\x.txt", None, sb) is None
    assert f(sb, None, sb) is None


# ------------------------------------------------------------------ provenance by replay
def py_replace(path, old, new):
    return ("py -I - <<'EOF'\n"
            f"p = r\"{path}\"\n"
            "s = open(p, 'rb').read().decode('utf-8')\n"
            f"s = s.replace({old!r}, {new!r})\n"
            "open(p, 'wb').write(s.encode('utf-8'))\n"
            "EOF\n")


@needs_bash
def test_write_then_bash_heredoc_replace_is_replayed_match(env):
    p = env.disk("skeletons/a.py", "x = 2\ny = 1\n")
    b = env.start()
    b.write(p, "x = 1\ny = 1\n")
    b.call("Bash", {"command": py_replace(p, "x = 1", "x = 2")})
    res = env.run(b, patterns=["skeletons/*.py"])
    e = prov(res, "skeletons/a.py")
    assert e["status_v1"] == "mismatch" and e["status"] == "replayed_match"
    assert e["sha256_replayed"] == e["sha256_disk"] != e["sha256_rebuilt"]
    assert res["provenance_ok"] is True and res["valid"] is True and res["reasons"] == []
    r = res["replay"]
    assert r["replay_ran"] is True and r["n_replayed_calls"] == 2 and r["n_timeouts"] == 0 and r["n_refused"] == 0
    log = json.loads(Path(r["replay_log"]).read_text(encoding="utf-8"))
    assert [c["tool"] for c in log["calls"]] == ["Write", "Bash"]
    assert log["calls"][1]["exit_code"] == 0 and log["calls"][1]["status"] == "ok"
    assert str(env.sb).lower() not in log["calls"][1]["mapped_command"].lower()  # rewritten into the replica
    assert Path(r["replay_dir"], "root", "world", LABEL, "skeletons", "a.py").read_bytes() == b"x = 2\ny = 1\n"
    assert (env.sb / "skeletons" / "a.py").read_bytes() == b"x = 2\ny = 1\n"  # the real sandbox is untouched


@needs_bash
def test_tampered_disk_after_replay_is_mismatch(env):
    p = env.disk("skeletons/a.py", "x = 3 TAMPERED\n")
    b = env.start()
    b.write(p, "x = 1\n")
    b.call("Bash", {"command": py_replace(p, "x = 1", "x = 2")})
    res = env.run(b, patterns=["skeletons/*.py"])
    e = prov(res, "skeletons/a.py")
    assert e["status"] == "mismatch" and e["status_v1"] == "mismatch"
    assert e["sha256_replayed"] is not None and e["sha256_replayed"] != e["sha256_disk"]
    assert res["provenance_ok"] is False and res["valid"] is False and "provenance" in reasons_text(res)


def test_replay_not_run_when_every_file_matches(env):
    p = env.disk("skeletons/a.py", "x = 1\n")
    b = env.start()
    b.write(p, "x = 1\n")
    res = env.run(b, patterns=["skeletons/*.py"])
    assert prov(res, "skeletons/a.py")["status"] == "match" and res["provenance_ok"] is True
    assert res["replay"]["replay_ran"] is False and res["replay"]["replay_dir"] is None
    assert not (env.tmp / "replays").exists()


def test_force_replay_keeps_match_and_reports_replica_hash(env):
    p = env.disk("skeletons/a.py", "x = 1\n")
    b = env.start()
    b.write(p, "x = 1\n")
    res = env.run(b, patterns=["skeletons/*.py"], force=True)
    e = prov(res, "skeletons/a.py")
    assert e["status"] == "match" and e["sha256_replayed"] == e["sha256_disk"]
    assert res["replay"]["replay_ran"] is True and res["replay"]["n_replayed_calls"] == 1


@needs_bash
def test_powershell_set_content_is_replayed_match(env):
    p = env.disk("skeletons/a.py", b"x = 2")
    b = env.start()
    b.write(p, "x = 1")
    b.call("PowerShell", {"command": f"Set-Content -Path '{p}' -Value 'x = 2' -NoNewline -Encoding Ascii"})
    res = env.run(b, patterns=["skeletons/*.py"])
    assert prov(res, "skeletons/a.py")["status"] == "replayed_match", res["replay"]
    assert res["valid"] is True and res["replay"]["n_replayed_calls"] == 2


@needs_bash
def test_error_result_and_missing_result_are_skipped(env):
    p = env.disk("skeletons/a.py", "x = 2\n")  # what the failed command would have produced
    b = env.start()
    b.write(p, "x = 1\n")
    b.call("Bash", {"command": py_replace(p, "x = 1", "x = 2")}, text="Exit code 1", is_error=True)
    b.tool_use("Bash", {"command": py_replace(p, "x = 1", "x = 2")})  # cut off: no result
    res = env.run(b, patterns=["skeletons/*.py"])
    assert prov(res, "skeletons/a.py")["status"] == "mismatch"
    r = res["replay"]
    assert r["n_replayed_calls"] == 1 and r["n_skipped_error"] == 1 and r["n_skipped_no_result"] == 1
    log = json.loads(Path(r["replay_log"]).read_text(encoding="utf-8"))
    assert [c["status"] for c in log["calls"]] == ["ok", "skipped_error_result", "skipped_no_result"]


@needs_bash
def test_edit_after_bash_applies_to_the_changed_content(env):
    p = env.disk("skeletons/a.py", "a = 10\nb = 1\n")
    b = env.start()
    b.write(p, "a = 1\nb = 1\n")
    b.call("Bash", {"command": py_replace(p, "a = 1", "a = 9")})
    b.edit(p, "a = 9", "a = 10")  # old_string exists only after the Bash change
    res = env.run(b, patterns=["skeletons/*.py"])
    e = prov(res, "skeletons/a.py")
    assert e["status_v1"] == "cannot_rebuild" and e["status"] == "replayed_match"
    assert res["valid"] is True


@needs_bash
def test_replay_edit_uses_v1_crlf_rules(env):
    p = env.disk("a.txt", b"alpha\r\nBETA\r\nBETA2\r\ngamma\r\n")
    b = env.start()
    b.call("Bash", {"command": "printf 'alpha\\r\\nbeta\\r\\ngamma\\r\\n' > \"" + str(p).replace("\\", "/") + "\""})
    b.edit(p, "beta", "BETA\nBETA2")  # CRLF-majority file: new LF text becomes CRLF
    res = env.run(b, patterns=["a.txt"])
    assert prov(res, "a.txt")["status"] == "replayed_match", res["replay"]


@needs_bash
def test_manifest_files_are_copied_and_usable(env):
    env.base_file("BATCH.json", '{"k": 1}\n')
    p = env.disk("skeletons/a.py", '{"k": 1}\n')
    b = env.start()
    fwd = str(env.sb).replace("\\", "/")
    b.call("Bash", {"command": f'cat "{fwd}/BATCH.json" > "{fwd}/skeletons/a.py"'})
    res = env.run(b, patterns=["skeletons/*.py"])
    assert prov(res, "skeletons/a.py")["status"] == "replayed_match"
    assert res["replay"]["n_manifest_files_copied"] == 1
    assert (Path(res["replay"]["replay_dir"]) / "root" / "world" / LABEL / "skeletons").is_dir()


@needs_bash
def test_git_bash_spelling_and_background_flag(env):
    p = env.disk("skeletons/a.py", "hi\n")
    b = env.start()
    drive = str(env.sb)[0].lower()
    gb = "/" + drive + str(env.sb).replace("\\", "/")[2:]
    b.call("Bash", {"command": f'echo hi > "{gb}/skeletons/a.py"', "run_in_background": True})
    res = env.run(b, patterns=["skeletons/*.py"])
    assert prov(res, "skeletons/a.py")["status"] == "replayed_match", res["replay"]
    assert res["replay"]["n_background_sync"] == 1
    log = json.loads(Path(res["replay"]["replay_log"]).read_text(encoding="utf-8"))
    assert log["calls"][0]["background"] is True and "synchronously" in log["calls"][0]["note"]


@needs_bash
def test_refused_command_fails_provenance_and_is_not_run(env):
    p = env.disk("skeletons/a.py", "x = 1\n")
    b = env.start()
    b.write(p, "x = 1\n")
    b.call("Bash", {"command": 'echo leak > "E:\\Other\\leak.txt"'})
    b.call("Write", {"file_path": str(env.sb / "skeletons" / "b.py"), "content": "b\n"},
           text=f"File created successfully at: {env.sb}")
    env.disk("skeletons/b.py", "BAD\n")  # makes the replay necessary (b.py is a mismatch)
    res = env.run(b, patterns=["skeletons/*.py"])
    assert res["replay"]["n_refused"] == 1 and res["provenance_ok"] is False and res["valid"] is False
    assert "refused" in reasons_text(res)
    log = json.loads(Path(res["replay"]["replay_log"]).read_text(encoding="utf-8"))
    refused = [c for c in log["calls"] if c["status"] == "refused"]
    assert len(refused) == 1 and "exit_code" not in refused[0] and "E:" in refused[0]["refused_reason"]
    assert not Path("E:\\Other\\leak.txt").exists()


@needs_bash
def test_refusal_fails_provenance_even_if_files_replay_match(env):
    p = env.disk("skeletons/a.py", "x = 2\n")
    b = env.start()
    b.write(p, "x = 1\n")
    b.call("Bash", {"command": py_replace(p, "x = 1", "x = 2")})
    b.call("Bash", {"command": "type C:\\Users\\nobody\\x.txt"})
    res = env.run(b, patterns=["skeletons/*.py"])
    assert prov(res, "skeletons/a.py")["status"] == "replayed_match"
    assert res["replay"]["n_refused"] == 1 and res["provenance_ok"] is False and res["valid"] is False


@needs_bash
def test_timeout_kills_only_that_command_and_replay_continues(env):
    p = env.disk("skeletons/a.py", "after\n")
    b = env.start()
    b.call("Bash", {"command": "sleep 30"})
    b.write(p, "after\n")
    res = env.run(b, patterns=["skeletons/*.py"], timeout=2, force=True)
    r = res["replay"]
    assert r["n_timeouts"] == 1 and r["n_replayed_calls"] == 2
    log = json.loads(Path(r["replay_log"]).read_text(encoding="utf-8"))
    assert log["calls"][0]["timed_out"] is True and log["calls"][0]["status"] == "timeout"
    assert log["calls"][0]["duration_s"] < 25
    assert prov(res, "skeletons/a.py")["status"] == "match"


def test_write_outside_sandbox_is_skipped_and_reported(env):
    p = env.disk("skeletons/a.py", "DIFFERENT\n")
    b = env.start()
    b.write(p, "x\n")  # mismatch -> replay needed
    b.write(str(env.tmp / "outside.txt"), "o\n")
    res = env.run(b, patterns=["skeletons/*.py"])
    r = res["replay"]
    assert r["n_outside_skipped"] == 1 and r["n_replayed_calls"] == 1
    assert not (env.tmp / "outside.txt").exists()
    assert res["outside_paths"] and res["valid"] is False  # the v1 outside-path check still invalidates


def test_replay_write_is_binary_exact(env):
    content = "alpha \u00e7\u015f\r\nbeta\n"  # CRLF inside the content stays as given
    p = env.disk("w.txt", content.encode("utf-8"))
    b = env.start()
    b.write(p, content)
    res = env.run(b, patterns=["w.txt"], force=True)
    e = prov(res, "w.txt")
    assert e["status"] == "match" and e["sha256_replayed"] == e["sha256_disk"]


def test_replay_missing_file_stays_mismatch_with_no_replayed_hash(env):
    env.disk("skeletons/a.py", "never written in the replay\n")
    b = env.start()
    b.write(env.sb / "skeletons" / "a.py", "x\n")
    b.call("Write", {"file_path": str(env.sb / "skeletons" / "a.py"), "content": "x"}, text="boom", is_error=True)
    res = env.run(b, patterns=["skeletons/*.py"])
    e = prov(res, "skeletons/a.py")
    assert e["status"] == "mismatch" and e["sha256_replayed"] is not None  # the first Write was replayed
    # not written at all in the transcript
    b2 = env.start()
    b2.text("nothing")
    res2 = env.run(b2, patterns=["skeletons/*.py"])
    e2 = prov(res2, "skeletons/a.py")
    assert e2["status"] == "not_written" and e2["sha256_replayed"] is None and res2["valid"] is False


def test_sandbox_not_under_world_root_never_replays(env, monkeypatch):
    monkeypatch.setattr(w2, "WORLD_ROOT", str(env.tmp / "elsewhere"))
    p = env.disk("skeletons/a.py", "DIFFERENT\n")
    b = env.start()
    b.write(p, "x\n")
    res = env.run(b, patterns=["skeletons/*.py"], force=True)
    assert res["replay"]["replay_ran"] is False and "direct child" in res["replay"]["not_run_reason"]
    assert prov(res, "skeletons/a.py")["status"] == "mismatch" and res["valid"] is False
    assert not (env.tmp / "replays").exists()


def test_manifest_sha_mismatch_is_an_error(env):
    env.base_file("BATCH.json", "{}\n")
    env.disk("BATCH.json", "{} changed after the manifest\n")
    p = env.disk("skeletons/a.py", "DIFFERENT\n")
    b = env.start()
    b.write(p, "x\n")
    with pytest.raises(ValueError, match="sha256 mismatch"):
        env.run(b, patterns=["skeletons/*.py"])


def test_manifest_without_entries_for_the_label_copies_nothing(env):
    p = env.disk("skeletons/a.py", "DIFFERENT\n")
    b = env.start()
    b.write(p, "x\n")
    res = env.run(b, patterns=["skeletons/*.py"], manifest_extra={"other\\BATCH.json": "0" * 64})
    assert res["replay"]["n_manifest_files_copied"] == 0 and res["replay"]["replay_ran"] is True
    assert prov(res, "skeletons/a.py")["status"] == "mismatch"


def test_existing_replay_dir_is_an_error_and_is_never_deleted(env):
    env.base_file("BATCH.json", "{}\n")
    rd = env.tmp / "preexisting"
    rd.mkdir()
    (rd / "keep.txt").write_text("keep", encoding="utf-8")
    p = env.disk("skeletons/a.py", "DIFFERENT\n")
    b = env.start()
    b.write(p, "x\n")
    with pytest.raises(ValueError, match="already exists"):
        env.run(b, patterns=["skeletons/*.py"], replay_dir=rd)
    assert (rd / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_default_replay_dir_name(env):
    env.base_file("BATCH.json", "{}\n")
    p = env.disk("skeletons/a.py", "x\n")
    b = env.start()
    b.write(p, "x\n")
    t = env.tmp / "agent-agentA.jsonl"
    b.save(t)
    m = env.tmp / "agent.meta.json"
    m.write_text(json.dumps(env.meta), encoding="utf-8")
    bpath, bsha = env.write_baseline()
    man = env.tmp / "MANIFEST.json"
    man.write_text(json.dumps({f"{LABEL}\\BATCH.json": env.base_files["BATCH.json"]}), encoding="utf-8")
    res = w2.check_run(str(t), str(m), str(env.sb), ["skeletons/*.py"], prompt_path=str(env.prompt),
                       frozen_sha=env.prompt_sha, baseline_path=str(bpath), baseline_sha=bsha,
                       manifest_path=str(man), force_replay=True)
    rd = Path(res["replay"]["replay_dir"])
    assert rd.parent == env.tmp / "world_replay" and re.fullmatch(rf"{LABEL}_\d{{8}}T\d{{6}}", rd.name)
    assert (rd / "replay_log.json").is_file()


# ------------------------------------------------------------------ CLI
def test_cli_main_usage_and_success(env, capsys):
    env.base_file("BATCH.json", "{}\n")
    p = env.disk("skeletons/a.py", "x\n")
    b = env.start()
    b.write(p, "x\n")
    res = env.run(b, patterns=["skeletons/*.py"])  # writes transcript / meta / manifest files
    assert res["valid"] is True
    common = ["--transcript", str(env.tmp / "agent-agentA.jsonl"), "--meta", str(env.tmp / "agent.meta.json"),
              "--sandbox", str(env.sb), "--files", "skeletons/*.py", "--prompt", str(env.prompt)]
    # the frozen prompt hash is the real one -> invalid (exit 1) but the new options parse
    rd = env.tmp / "cli_replay"
    code = w2.main(common + ["--force-replay", "--replay-dir", str(rd), "--manifest", str(env.tmp / "MANIFEST.json"),
                             "--replay-timeout", "30", "--out", str(env.tmp / "out.json")])
    printed = json.loads(capsys.readouterr().out)
    assert code == 1 and printed["prompt_is_frozen"] is False and printed["replay"]["replay_ran"] is True
    assert json.loads((env.tmp / "out.json").read_text(encoding="utf-8")) == printed
    # replay dir exists now -> usage error 2
    code2 = w2.main(common + ["--force-replay", "--replay-dir", str(rd), "--manifest", str(env.tmp / "MANIFEST.json")])
    assert code2 == 2 and "already exists" in capsys.readouterr().err


def test_cli_wrong_baseline_is_exit_2(env, capsys):
    b = env.start()
    b.text("x")
    env.run(b)
    bpath, _ = env.write_baseline()  # hashes differently from the hard-coded constant
    (env.tmp / "terms.txt").write_text("zzterm\n", encoding="utf-8")
    code = w2.main(["--transcript", str(env.tmp / "agent-agentA.jsonl"), "--meta", str(env.tmp / "agent.meta.json"),
                    "--sandbox", str(env.sb), "--files", "nothing_*", "--prompt", str(env.prompt),
                    "--terms", str(env.tmp / "terms.txt"), "--baseline", str(bpath)])
    assert code == 2 and "sha256" in capsys.readouterr().err
    code = w2.main(["--transcript", str(env.tmp / "agent-agentA.jsonl"), "--meta", str(env.tmp / "agent.meta.json"),
                    "--sandbox", str(env.sb), "--files", "nothing_*", "--prompt", str(env.prompt),
                    "--terms", str(env.tmp / "terms.txt"), "--baseline", str(env.tmp / "no-such-baseline")])
    assert code == 2

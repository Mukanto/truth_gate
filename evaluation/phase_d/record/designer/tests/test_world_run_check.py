"""Tests for world_run_check.py. All transcripts are synthetic, built in tmp_path (pytest basetemp is redirected to
designer\\tests\\work\\pytest_tmp by conftest.py)."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "world_run_check.py"
sys.path.insert(0, str(HERE.parent))
import world_run_check as wrc  # noqa: E402

OPUS = "claude-opus-5-5"
PROMPT_TEXT = "Do the world task in <SANDBOX> now.\nSecond line."
INJECTED = "\n<context_window_protection>\n  hook text\n</context_window_protection>"
REAL_PROMPT = Path(wrc.DEFAULT_PROMPT)


class Builder:
    """Builds a synthetic agent transcript (one JSON object per line)."""

    def __init__(self, agent="agentA", session="sessionS"):
        self.rows, self.n, self.prev = [], 0, None
        self.agent, self.session = agent, session

    def _row(self, typ):
        self.n += 1
        row = {"type": typ, "uuid": f"u{self.n}", "parentUuid": self.prev, "agentId": self.agent,
               "sessionId": self.session, "version": "2.1.325", "cwd": "X:/cwd",
               "timestamp": f"2026-11-18T10:{self.n // 60:02d}:{self.n % 60:02d}.000Z"}
        self.prev = row["uuid"]
        return row

    def raw(self, obj):
        self.rows.append(obj)
        return obj

    def user_prompt(self, text):
        r = self._row("user")
        r["message"] = {"role": "user", "content": text}
        return self.raw(r)

    def user_blocks(self, blocks):
        r = self._row("user")
        r["message"] = {"role": "user", "content": blocks}
        return self.raw(r)

    def attach(self, att):
        r = self._row("attachment")
        r["attachment"] = att
        return self.raw(r)

    def assistant(self, blocks, model=OPUS, mid=None):
        r = self._row("assistant")
        r["message"] = {"id": mid or f"msg{self.n}", "model": model, "role": "assistant", "content": blocks}
        return self.raw(r)

    def text(self, text="done", model=OPUS, mid=None):
        return self.assistant([{"type": "text", "text": text}], model=model, mid=mid)

    def tool_use(self, name, inp, tid=None, model=OPUS, mid=None):
        tid = tid or f"toolu_{self.n + 1}"
        self.assistant([{"type": "tool_use", "id": tid, "name": name, "input": inp}], model=model, mid=mid)
        return tid

    def result(self, tid, text="ok", is_error=False):
        b = {"type": "tool_result", "tool_use_id": tid, "content": text}
        if is_error:
            b["is_error"] = True
        return self.user_blocks([b])

    def call(self, name, inp, text="ok", is_error=False, **kw):
        tid = self.tool_use(name, inp, **kw)
        self.result(tid, text, is_error)
        return tid

    def write(self, path, content, **kw):
        return self.call("Write", {"file_path": str(path), "content": content},
                         text=f"File created successfully at: {path}", **kw)

    def edit(self, path, old, new, replace_all=False, **kw):
        inp = {"file_path": str(path), "old_string": old, "new_string": new}
        if replace_all:
            inp["replace_all"] = True
        return self.call("Edit", inp, text=f"The file {path} has been updated successfully.", **kw)

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            for r in self.rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


class Env:
    def __init__(self, tmp):
        self.tmp = tmp
        self.sb = tmp / "sb"
        self.sb.mkdir()
        self.prompt = tmp / "prompt.md"
        self.prompt.write_bytes(PROMPT_TEXT.encode("utf-8"))
        self.prompt_sha = hashlib.sha256(PROMPT_TEXT.encode("utf-8")).hexdigest()
        self.expected = PROMPT_TEXT.replace("<SANDBOX>", str(self.sb))
        self.meta = {"agentType": "general-purpose", "isBuiltIn": True, "spawnDepth": 1, "requestShape": "background",
                     "model": "opus", "pickedEffortModel": OPUS, "finished": True, "toolUseId": "toolu_x"}

    def start(self, remainder=INJECTED, **kw):
        b = Builder(**kw)
        b.user_prompt(self.expected + remainder)
        return b

    def disk(self, rel, data):
        p = self.sb / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return p

    def run(self, b, patterns=("nothing_*",), prefix=None, base=None, terms=None, meta=None, frozen=True,
            prompt=None):
        t = self.tmp / "agent-agentA.jsonl"
        b.save(t)
        m = self.tmp / "agent.meta.json"
        m.write_text(json.dumps(self.meta if meta is None else meta), encoding="utf-8")
        pre = None
        if prefix is not None:
            pre = self.tmp / "agent.prefix.json"
            pre.write_text(json.dumps(prefix), encoding="utf-8")
        tf = None
        if terms is not None:
            tf = self.tmp / "terms.txt"
            tf.write_text("\n".join(terms) + "\n", encoding="utf-8")
        return wrc.check_run(str(t), str(m), str(self.sb), list(patterns), str(pre) if pre else None,
                             str(base) if base else None, str(tf) if tf else None,
                             str(prompt or self.prompt), frozen_sha=self.prompt_sha if frozen else wrc.FROZEN_PROMPT_SHA256)


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


def reasons_text(res):
    return " | ".join(res["reasons"])


# ------------------------------------------------------------------ valid run, model, meta
def test_valid_run(env):
    b = env.start()
    b.attach({"type": "date", "date": "2026-11-18"})
    b.raw({"type": "api-request", "agentId": "agentA", "sessionId": "sessionS", "version": "2.1.325",
           "params": {"model": OPUS, "output_config": {"effort": "xhigh"}, "thinking": {"type": "adaptive"}}})
    p = env.sb / "skeletons" / "a.py"
    env.disk("skeletons/a.py", "print(1)\n")
    b.write(p, "print(1)\n")
    b.text("finished")
    res = env.run(b, patterns=["skeletons/*.py"])
    assert res["valid"] is True and res["reasons"] == []
    assert res["prompt_is_frozen"] and res["prompt_match"] and res["model_rule_ok"]
    assert res["provenance"]["skeletons/a.py"]["status"] == "match"
    assert res["injected_remainder_len"] == len(INJECTED)
    assert res["settings"]["effort"] == "xhigh"
    assert res["settings"]["harness_versions"] == ["2.1.325"]
    assert res["tools"] == {"Write": 1}
    assert res["first_last_utc"][0] <= res["first_last_utc"][1]
    assert len(res["transcript_sha256"]) == 64


def test_wrong_model(env):
    b = env.start()
    b.text("hi", model="claude-sonnet-5-5")
    res = env.run(b)
    assert res["model_rule_ok"] is False and res["valid"] is False
    assert "model rule" in reasons_text(res)


def test_only_synthetic_assistant_entries(env):
    b = env.start()
    b.text("x", model="<synthetic>")
    res = env.run(b)
    assert res["models"] == {"<synthetic>": 1}
    assert res["model_rule_ok"] is False and res["valid"] is False


def test_synthetic_plus_opus_is_ok_and_counts_message_ids_once(env):
    b = env.start()
    b.text("a", mid="m1")
    b.text("b", mid="m1")  # second block of the same API message
    b.text("c", model="<synthetic>", mid="m2")
    res = env.run(b)
    assert res["models"] == {OPUS: 1, "<synthetic>": 1}
    assert res["model_rule_ok"] is True and res["valid"] is True


def test_mixed_models_invalid(env):
    b = env.start()
    b.text("a", mid="m1")
    b.text("b", model="claude-haiku-5-5", mid="m2")
    res = env.run(b)
    assert res["model_rule_ok"] is False


@pytest.mark.parametrize("change,needle", [
    ({"agentType": "Explore"}, "agentType"),
    ({"spawnDepth": 2}, "spawnDepth"),
    ({"model": "sonnet"}, "model="),
    ({"forkContext": True}, "fork"),
    ({"resumedFrom": "x"}, "resume"),
    ({"parentToolUseId": "toolu_p"}, "parent"),
    ({"nested": {"isFork": True}}, "fork"),
])
def test_meta_invalid(env, change, needle):
    b = env.start()
    b.text("x")
    meta = dict(env.meta, **change)
    res = env.run(b, meta=meta)
    assert res["meta"]["ok"] is False and res["valid"] is False
    assert needle in reasons_text(res)


def test_meta_falsy_fork_key_is_ok_and_fields_recorded(env):
    b = env.start()
    b.text("x")
    res = env.run(b, meta=dict(env.meta, forked=False))
    assert res["meta"]["ok"] is True and res["valid"] is True
    for k in ("pickedEffortModel", "isBuiltIn", "requestShape", "finished"):
        assert k in res["meta"]
    assert res["meta"]["pickedEffortModel"] == OPUS


# ------------------------------------------------------------------ first message / later user messages
def test_prompt_mismatch(env):
    b = Builder()
    b.user_prompt(env.expected.replace("world", "WORLD", 1) + INJECTED)
    b.text("x")
    res = env.run(b)
    assert res["prompt_match"] is False and res["valid"] is False
    d = res["prompt_diff"]
    assert d["first_diff_index"] == env.expected.index("world")
    assert "WORLD" in d["actual_context"] and "world" in d["expected_context"]
    assert len(d["expected_context"]) <= 80 and len(d["actual_context"]) <= 80


def test_prompt_mismatch_sandbox_text_not_replaced(env):
    b = Builder()
    b.user_prompt(PROMPT_TEXT + INJECTED)  # literal <SANDBOX> left in place
    b.text("x")
    res = env.run(b)
    assert res["prompt_match"] is False


def test_prompt_with_injected_remainder_still_matches(env):
    b = env.start(remainder="\n<context_window_protection>lots of text</context_window_protection>")
    b.text("x")
    res = env.run(b)
    assert res["prompt_match"] is True and res["prompt_diff"] is None
    assert res["injected_remainder_len"] > 0 and res["valid"] is True


def test_first_message_as_text_blocks(env):
    b = Builder()
    b.user_blocks([{"type": "text", "text": env.expected}, {"type": "text", "text": INJECTED}])
    b.text("x")
    res = env.run(b)
    assert res["prompt_match"] is True and res["injected_remainder_len"] == len(INJECTED)


def test_non_frozen_prompt_flagged(env):
    b = env.start()
    b.text("x")
    res = env.run(b, frozen=False)
    assert res["prompt_is_frozen"] is False and res["valid"] is False
    assert res["prompt_sha256"] == env.prompt_sha
    assert "frozen" in reasons_text(res)


def test_first_user_has_parent_or_assistant_precedes(env):
    b = Builder()
    b.text("early")  # assistant before the first user entry
    b.user_prompt(env.expected)
    res = env.run(b)
    assert res["first_message"]["assistant_before_first_user"] is True and res["valid"] is False
    b2 = Builder()
    b2.prev = "some-parent"
    b2.user_prompt(env.expected)
    b2.text("x")
    res2 = env.run(b2)
    assert res2["first_message"]["parentUuid_null"] is False and res2["valid"] is False


def test_later_user_text_message(env):
    b = env.start()
    b.text("x")
    b.user_prompt("please also do Y, and then some more text " + "z" * 300)
    res = env.run(b)
    assert res["valid"] is False and len(res["later_user_messages"]) == 1
    m = res["later_user_messages"][0]
    assert m["index"] == 2 and m["timestamp"] and len(m["text"]) == 200 and m["text"].startswith("please also")


def test_later_user_image_or_mixed_block(env):
    b = env.start()
    tid = b.tool_use("Read", {"file_path": str(env.sb / "x")})
    b.user_blocks([{"type": "tool_result", "tool_use_id": tid, "content": "ok"},
                   {"type": "text", "text": "extra note"}])
    b.user_blocks([{"type": "image", "source": {}}])
    res = env.run(b)
    assert len(res["later_user_messages"]) == 2 and res["valid"] is False


def test_tool_result_only_user_entries_ok_and_blob_is_not_a_turn(env):
    b = env.start()
    b.call("Read", {"file_path": str(env.sb / "x")})
    b.raw({"type": "api-request-blob", "agentId": "agentA", "sessionId": "sessionS", "hash": "h",
           "message": {"role": "user", "content": [{"type": "text", "text": "request copy"}]}})
    res = env.run(b)
    assert res["later_user_messages"] == [] and res["valid"] is True


# ------------------------------------------------------------------ tools
@pytest.mark.parametrize("name,inp", [
    ("Agent", {"prompt": "do it"}),
    ("Task", {"prompt": "do it"}),
    ("Workflow", {}),
    ("SendMessage", {"to": "x"}),
    ("TaskStop", {}),
    ("WebFetch", {"url": "https://example.com"}),
    ("WebSearch", {"query": "q"}),
    ("mcp__plugin_context-mode_context-mode__ctx_search", {"queries": ["a"]}),
    ("mcp__x__context_mode_thing", {}),
    ("ToolSearch", {"query": "select:mcp__plugin_context-mode_context-mode__ctx_execute"}),
    ("ToolSearch", {"query": "select:Read,WebFetch"}),
    ("ToolSearch", {"query": "ctx_batch"}),
])
def test_forbidden_tools(env, name, inp):
    b = env.start()
    b.call(name, inp)
    res = env.run(b)
    assert res["valid"] is False and len(res["forbidden_calls"]) == 1
    fc = res["forbidden_calls"][0]
    assert fc["name"] == name and fc["index"] == 1


def test_harmless_tool_search_and_names_ok(env):
    b = env.start()
    b.call("ToolSearch", {"query": "select:NotebookEdit"})
    b.call("Bash", {"command": "echo Agent"})
    b.call("Skill", {"skill": "x"})
    res = env.run(b)
    assert res["forbidden_calls"] == [] and res["valid"] is True
    assert res["tools"] == {"ToolSearch": 1, "Bash": 1, "Skill": 1}


# ------------------------------------------------------------------ linked transcript
def test_other_agent_id(env):
    b = env.start()
    b.text("x")
    r = b.text("y")
    r["agentId"] = "agentB"
    res = env.run(b)
    assert res["linked"]["ok"] is False and res["linked"]["other_agentIds"] == ["agentB"] and res["valid"] is False


def test_two_session_ids_and_missing_agent_id(env):
    b = env.start()
    r = b.text("x")
    r["sessionId"] = "other-session"
    res = env.run(b)
    assert res["linked"]["ok"] is False and len(res["linked"]["sessionIds"]) == 2
    b2 = Builder()
    b2.user_prompt(env.expected)
    del b2.rows[0]["agentId"]
    b2.text("x")
    del b2.rows[1]["agentId"]
    res2 = env.run(b2)
    assert res2["linked"]["ok"] is False and "no agentId" in res2["linked"]["problems"][0]


def test_unparsable_line_is_invalid(env):
    b = env.start()
    b.text("x")
    t = env.tmp / "agent-agentA.jsonl"
    b.save(t)
    with open(t, "a", encoding="utf-8") as f:
        f.write("{not json\n")
    res = wrc.check_run(str(t), _write_meta(env), str(env.sb), ["nothing_*"],
                        prompt_path=str(env.prompt), frozen_sha=env.prompt_sha)
    assert res["unparsable_lines"] == [3] and res["valid"] is False


def _write_meta(env):
    m = env.tmp / "m2.meta.json"
    m.write_text(json.dumps(env.meta), encoding="utf-8")
    return str(m)


# ------------------------------------------------------------------ injected-context term scan
def test_term_hit_in_attachment(env):
    b = env.start()
    b.attach({"type": "instructions", "files": [{"path": "CLAUDE.md", "content": "remember the Foo-Secret plan here"}]})
    b.text("x")
    res = env.run(b, terms=["# comment", "", "foo-secret"])
    hits = [h for h in res["term_hits"] if h["group"] == "b_attachment"]
    assert len(hits) == 1 and hits[0]["term"] == "foo-secret" and "Foo-Secret" in hits[0]["context"]
    assert len(hits[0]["context"]) <= 80 + len("foo-secret")
    assert res["valid"] is False and res["terms_scanned"] == 1


def test_term_hit_in_prefix(env):
    b = env.start()
    b.text("x")
    res = env.run(b, terms=["zzterm"], prefix={"state": {"toolNames": ["ZZTerm"]}})
    assert [h["group"] for h in res["term_hits"]] == ["c_prefix"] and res["valid"] is False


def test_term_hit_in_remainder(env):
    b = env.start(remainder=INJECTED + "\nthe hidden zzterm word")
    b.text("x")
    res = env.run(b, terms=["zzterm"])
    assert [h["group"] for h in res["term_hits"]] == ["a_remainder"] and res["valid"] is False


def test_term_hit_in_prompt_only_is_valid(tmp_path):
    e = Env(tmp_path)
    text = "Do the task in <SANDBOX>; the zzterm is mentioned in the prompt."
    e.prompt.write_bytes(text.encode("utf-8"))
    e.prompt_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    e.expected = text.replace("<SANDBOX>", str(e.sb))
    b = e.start()
    b.text("x")
    res = e.run(b, terms=["zzterm"])
    assert [h["group"] for h in res["term_hits"]] == ["d_prompt"]
    assert res["valid"] is True


def test_term_hit_in_request_blob_is_informational(env):
    b = env.start()
    b.raw({"type": "api-request-blob", "agentId": "agentA", "sessionId": "sessionS", "hash": "h",
           "message": {"role": "user", "content": [{"type": "text", "text": "a zzterm here"}]}})
    b.text("x")
    res = env.run(b, terms=["zzterm"])
    assert [h["group"] for h in res["term_hits"]] == ["e_request_blob"] and res["valid"] is True


def test_no_terms_means_no_scan(env):
    b = env.start(remainder=INJECTED + " zzterm")
    b.text("x")
    res = env.run(b)
    assert res["term_hits"] == [] and res["terms_scanned"] == 0 and res["valid"] is True


# ------------------------------------------------------------------ outside paths
def test_outside_path_in_bash(env):
    b = env.start()
    b.call("Bash", {"command": 'type "C:\\Other\\secret.txt"'})
    res = env.run(b)
    assert res["valid"] is False
    assert res["outside_paths"][0]["kind"] == "drive_path" and "other" in res["outside_paths"][0]["path"].lower()


def test_inside_paths_and_python_install_are_ok(env):
    b = env.start()
    b.call("Read", {"file_path": str(env.sb / "x.txt")})
    b.call("Bash", {"command": f'"C:\\Users\\u\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" "{env.sb}\\x.py"'})
    b.call("Bash", {"command": "curl https://example.com/a"})  # 's:/' of https must not count
    res = env.run(b)
    assert res["outside_paths"] == [] and res["valid"] is True


def test_sibling_folder_with_same_prefix_is_outside(env):
    b = env.start()
    b.call("Read", {"file_path": str(env.sb) + "2\\x.txt"})
    res = env.run(b)
    assert len(res["outside_paths"]) == 1 and res["valid"] is False


def test_dotdot_component_in_bash(env):
    b = env.start()
    b.call("Bash", {"command": "cd .. && ls"})
    b.call("Bash", {"command": "echo a..b ... "})  # not a path component
    res = env.run(b)
    kinds = [o["kind"] for o in res["outside_paths"]]
    assert kinds == ["dotdot_in_command"] and res["valid"] is False


def test_gitbash_drive_path_outside_but_sed_awk_not(env):
    b = env.start()
    b.call("Bash", {"command": "sed 's/a/b/' f.txt; awk '/a/ {print}' f.txt"})
    res = env.run(b)
    assert res["outside_paths"] == []
    b.call("Bash", {"command": "cat /e/Other/secret.txt"})
    res = env.run(b)
    assert len(res["outside_paths"]) == 1 and res["outside_paths"][0]["path"].startswith("e:/Other")


# ------------------------------------------------------------------ settings
def test_effort_not_recorded(env):
    b = env.start()
    b.text("x")
    res = env.run(b)
    assert res["settings"]["effort"] == "not recorded in transcript"
    assert any("api-request" in s for s in res["settings"]["effort_searched"])


def test_effort_from_assistant_and_prefix(env):
    b = env.start()
    r = b.text("x")
    r["effort"] = "xhigh"
    res = env.run(b, prefix={"state": {"effortValue": "xhigh", "buildVersion": "9.9.9"}})
    assert res["settings"]["effort"] == "xhigh"
    assert set(res["settings"]["effort_sources"]) == {"assistant.effort", "prefix.state.effortValue"}
    assert res["settings"]["harness_versions"] == ["2.1.325", "9.9.9"]


# ------------------------------------------------------------------ provenance
def prov(res, rel):
    return res["provenance"][rel]


def test_write_only_match(env):
    p = env.disk("WORLD_LOG.md", "# log\nline\n")
    b = env.start()
    b.write(p, "# log\nline\n")
    res = env.run(b, patterns=["WORLD_LOG.md"])
    e = prov(res, "WORLD_LOG.md")
    assert e["status"] == "match" and e["disk_equals_last_write"] is True and res["valid"] is True
    assert e["last_write_sha256"] == e["sha256_disk"] == e["sha256_rebuilt"]
    assert e["touched_by_other_tool"] is False


def test_write_then_edit_match(env):
    p = env.disk("a/b.py", "x = 2\ny = 1\n")
    b = env.start()
    b.write(p, "x = 1\ny = 1\n")
    b.edit(p, "x = 1", "x = 2")
    res = env.run(b, patterns=["a/*.py"])
    e = prov(res, "a/b.py")
    assert e["status"] == "match" and e["n_writes"] == 1 and e["n_edits"] == 1
    assert e["disk_equals_last_write"] is False  # the disk file is the edited content, not the last Write


def test_failed_edit_is_ignored(env):
    p = env.disk("f.txt", "a\nb\n")
    b = env.start()
    b.write(p, "a\nb\n")
    b.call("Edit", {"file_path": str(p), "old_string": "zzz", "new_string": "q"},
           text="String to replace not found in file.", is_error=True)
    b.call("Edit", {"file_path": str(p), "old_string": "a", "new_string": "q"},
           text="<tool_use_error>File has not been read yet.</tool_use_error>")
    b.call("Write", {"file_path": str(p), "content": "bogus"}, text="boom", is_error=True)
    res = env.run(b, patterns=["f.txt"])
    e = prov(res, "f.txt")
    assert e["status"] == "match" and e["n_failed_ops"] == 3 and res["valid"] is True


def test_call_without_result_is_skipped_and_counted(env):
    p = env.disk("f.txt", "a\n")
    b = env.start()
    b.write(p, "a\n")
    b.tool_use("Edit", {"file_path": str(p), "old_string": "a", "new_string": "q"})  # cut off, no result
    res = env.run(b, patterns=["f.txt"])
    e = prov(res, "f.txt")
    assert e["status"] == "match" and e["n_ops_without_result"] == 1


def test_duplicate_tool_use_entry_applied_once(env):
    p = env.disk("f.txt", "aa")
    b = env.start()
    b.write(p, "a")
    tid = b.tool_use("Edit", {"file_path": str(p), "old_string": "a", "new_string": "aa"}, tid="toolu_dup")
    b.assistant([{"type": "tool_use", "id": "toolu_dup", "name": "Edit",
                  "input": {"file_path": str(p), "old_string": "a", "new_string": "aa"}}])
    b.result(tid, f"The file {p} has been updated successfully.")
    res = env.run(b, patterns=["f.txt"])
    assert prov(res, "f.txt")["status"] == "match" and prov(res, "f.txt")["n_edits"] == 1


def test_replace_all(env):
    p = env.disk("f.txt", "y y y")
    b = env.start()
    b.write(p, "x x x")
    b.edit(p, "x", "y", replace_all=True)
    assert prov(env.run(b, patterns=["f.txt"]), "f.txt")["status"] == "match"
    env.disk("f.txt", "y x x")
    b2 = env.start()
    b2.write(p, "x x x")
    b2.edit(p, "x", "y")  # first occurrence only
    assert prov(env.run(b2, patterns=["f.txt"]), "f.txt")["status"] == "match"


def test_edit_before_write_with_base(env):
    base = env.tmp / "base"
    (base).mkdir()
    (base / "f.txt").write_bytes(b"hello\nworld\n")
    p = env.disk("f.txt", "HI\nworld\n")
    b = env.start()
    b.edit(p, "hello", "HI")
    res = env.run(b, patterns=["f.txt"], base=base)
    assert prov(res, "f.txt")["status"] == "match" and res["valid"] is True
    res2 = env.run(b, patterns=["f.txt"])  # no --base
    assert prov(res2, "f.txt")["status"] == "cannot_rebuild" and res2["valid"] is False
    assert "base" in prov(res2, "f.txt")["detail"]


def test_edit_old_string_missing_in_rebuild_is_cannot_rebuild(env):
    p = env.disk("f.txt", "a\nb\n")
    b = env.start()
    b.write(p, "a\nb\n")
    b.edit(p, "not-there", "x")  # the harness said "success", but the rebuilt text has no such string
    res = env.run(b, patterns=["f.txt"])
    assert prov(res, "f.txt")["status"] == "cannot_rebuild" and "not found" in prov(res, "f.txt")["detail"]


def test_disk_changed_after_is_mismatch(env):
    p = env.disk("f.txt", "tampered\n")
    b = env.start()
    b.write(p, "original\n")
    res = env.run(b, patterns=["f.txt"])
    e = prov(res, "f.txt")
    assert e["status"] == "mismatch" and e["disk_equals_last_write"] is False and res["valid"] is False


def test_file_never_written_is_not_written(env):
    env.disk("pre.txt", "x")
    b = env.start()
    b.text("nothing")
    res = env.run(b, patterns=["pre.txt"])
    assert prov(res, "pre.txt")["status"] == "not_written" and res["valid"] is False


def test_bash_cp_flags_touched_by_other_tool(env):
    p = env.disk("f.txt", "a\n")
    b = env.start()
    b.write(p, "a\n")
    b.call("Bash", {"command": f'cp "{env.sb}\\g.txt" "{env.sb}\\f.txt"'})
    b.call("Bash", {"command": "cat f.txt"})  # read only: no write-like token
    res = env.run(b, patterns=["f.txt"])
    e = prov(res, "f.txt")
    assert e["touched_by_other_tool"] is True and len(e["other_tool_commands"]) == 1
    assert e["other_tool_commands"][0]["command"].startswith("cp ")
    assert e["status"] == "match"  # the flag is reported, the verdict is the content check


@pytest.mark.parametrize("cmd", ["echo x > f.txt", "Set-Content f.txt 'x'", "py -c \"open('f.txt','w')\"",
                                 "sed -i s/a/b/ f.txt", "rm f.txt", "mv f.txt g.txt", "Out-File f.txt"])
def test_other_tool_write_tokens(env, cmd):
    p = env.disk("f.txt", "a\n")
    b = env.start()
    b.write(p, "a\n")
    b.call("Bash", {"command": cmd})
    assert prov(env.run(b, patterns=["f.txt"]), "f.txt")["touched_by_other_tool"] is True


def test_unmatched_pattern_and_unchecked_written_file(env):
    p = env.disk("keep.txt", "k")
    q = env.disk("other.txt", "o")
    b = env.start()
    b.write(p, "k")
    b.write(q, "o")
    res = env.run(b, patterns=["keep.txt", "nomatch/*.py"])
    assert res["unmatched_patterns"] == ["nomatch/*.py"]
    assert res["unchecked_written_files"] == [wrc.norm_path(str(q))]
    assert res["files_checked"] == 1 and res["valid"] is True


def test_path_resolution_is_case_and_slash_insensitive(env):
    p = env.disk("Dir/F.txt", "a")
    b = env.start()
    b.write(str(p).replace("\\", "/").upper().replace("/SB/", "/sb/").replace("DIR/F.TXT", "dir/f.txt"), "a")
    assert prov(env.run(b, patterns=["Dir/*.txt"]), "Dir/F.txt")["status"] == "match"


# ------------------------------------------------------------------ line-ending behaviours (measured, see docstring)
def test_write_is_verbatim_utf8_no_bom_no_added_newline(env):
    content = "alpha \u00e7\u015f\nbeta"
    p = env.disk("w.txt", content.encode("utf-8"))
    b = env.start()
    b.write(p, content)
    assert prov(env.run(b, patterns=["w.txt"]), "w.txt")["status"] == "match"
    env.disk("w.txt", b"\xef\xbb\xbf" + content.encode("utf-8"))  # a BOM or a trailing newline would not match
    assert prov(env.run(b, patterns=["w.txt"]), "w.txt")["status"] == "mismatch"
    env.disk("w.txt", content.encode("utf-8") + b"\n")
    assert prov(env.run(b, patterns=["w.txt"]), "w.txt")["status"] == "mismatch"


def test_write_over_existing_crlf_file_gives_lf(env):
    base = env.tmp / "base"
    base.mkdir()
    (base / "c.txt").write_bytes(b"old1\r\nold2\r\n")
    p = env.disk("c.txt", b"new1\nnew2\n")
    b = env.start()
    b.write(p, "new1\nnew2\n")
    assert prov(env.run(b, patterns=["c.txt"], base=base), "c.txt")["status"] == "match"
    env.disk("c.txt", b"new1\r\nnew2\r\n")  # CRLF on disk after a Write of LF text: reported separately
    res = env.run(b, patterns=["c.txt"], base=base)
    assert prov(res, "c.txt")["status"] == "match_after_line_endings" and res["valid"] is False


EDIT_CASES = [  # (id, file before, old, new, replace_all, file after) - all measured with the real Edit tool
    ("crlf_file_keeps_crlf_and_lf_new_text_becomes_crlf", b"alpha\r\nbeta\r\ngamma\r\n", "beta", "BETA\nBETA2", False,
     b"alpha\r\nBETA\r\nBETA2\r\ngamma\r\n"),
    ("crlf_file_without_final_newline", b"alpha\r\nbeta\r\ngamma", "alpha\nbeta", "ALPHA\nBETA", False,
     b"ALPHA\r\nBETA\r\ngamma"),
    ("crlf_multiline_lf_old_string_matches", b"one\r\ntwo\r\nthree\r\nfour\r\n", "two\nthree\n", "TWO\nTHREE\n", False,
     b"one\r\nTWO\r\nTHREE\r\nfour\r\n"),
    ("crlf_replace_all", b"x\r\nx\r\nx\r\n", "x", "y\nz", True, b"y\r\nz\r\ny\r\nz\r\ny\r\nz\r\n"),
    ("bom_is_kept", b"\xef\xbb\xbfalpha\nbeta\n", "alpha", "ALPHA", False, b"\xef\xbb\xbfALPHA\nbeta\n"),
    ("lf_file_non_ascii", b"alpha \xc3\xa7\xc5\x9f\nbeta\n\ngamma\n", "beta", "BETA \u011f", False,
     b"alpha \xc3\xa7\xc5\x9f\nBETA \xc4\x9f\n\ngamma\n"),
    ("mixed_crlf_majority_becomes_crlf", b"alpha\r\nbeta\ngamma\r\n", "gamma", "GAMMA", False,
     b"alpha\r\nbeta\r\nGAMMA\r\n"),
    ("mixed_crlf_majority_3_to_1", b"a3\r\nb3\r\nc3\r\nd3\n", "c3", "C3", False, b"a3\r\nb3\r\nC3\r\nd3\r\n"),
    ("mixed_lf_majority_becomes_lf", b"a1\r\nb1\nc1\nd1\n", "c1", "C1", False, b"a1\nb1\nC1\nd1\n"),
    ("mixed_lf_majority_crlf_last", b"a2\nb2\nc2\nd2\r\n", "c2", "C2", False, b"a2\nb2\nC2\nd2\n"),
    ("mixed_tie_gives_lf", b"a4\r\nb4\nc4", "c4", "C4", False, b"a4\nb4\nC4"),
    ("mixed_tie_gives_lf_other_order", b"a5\nb5\r\nc5", "c5", "C5", False, b"a5\nb5\nC5"),
]


@pytest.mark.parametrize("before,old,new,replace_all,after", [c[1:] for c in EDIT_CASES],
                         ids=[c[0] for c in EDIT_CASES])
def test_edit_byte_behaviour(env, before, old, new, replace_all, after):
    # the emulation itself
    assert wrc.apply_edit(before.decode("utf-8"), old, new, replace_all).encode("utf-8") == after
    # and through the whole provenance pipeline: Edit on a file from --base, disk holds the measured result
    base = env.tmp / "base"
    base.mkdir()
    (base / "e.txt").write_bytes(before)
    p = env.disk("e.txt", after)
    b = env.start()
    b.edit(p, old, new, replace_all=replace_all)
    res = env.run(b, patterns=["e.txt"], base=base)
    assert prov(res, "e.txt")["status"] == "match" and res["valid"] is True


def test_edit_after_write_uses_the_write_content_line_endings(env):
    # Write stores LF; a following Edit on that LF file must stay LF
    p = env.disk("s.txt", b"one\ntwo\nTHREE\n")
    b = env.start()
    b.write(p, "one\ntwo\nthree\n")
    b.edit(p, "three", "THREE")
    assert prov(env.run(b, patterns=["s.txt"]), "s.txt")["status"] == "match"


# ------------------------------------------------------------------ CLI
def run_cli(args):
    return subprocess.run([sys.executable, "-B", str(SCRIPT)] + args, capture_output=True, text=True,
                          encoding="utf-8")


def cli_args(env, extra=()):
    return ["--transcript", str(env.tmp / "agent-agentA.jsonl"), "--meta", str(env.tmp / "agent.meta.json"),
            "--sandbox", str(env.sb), "--files", "nothing_*", "--prompt", str(env.prompt)] + list(extra)


def test_cli_non_frozen_prompt_exit_1_and_out_file(env):
    b = env.start()
    b.text("x")
    env.run(b)  # writes the transcript and meta files
    out = env.tmp / "result.json"
    r = run_cli(cli_args(env, ["--out", str(out)]))
    assert r.returncode == 1
    printed = json.loads(r.stdout)
    assert printed == json.loads(out.read_text(encoding="utf-8"))
    assert printed["prompt_is_frozen"] is False and printed["valid"] is False and printed["prompt_match"] is True


def test_cli_usage_errors_exit_2(env):
    b = env.start()
    b.text("x")
    env.run(b)
    args = cli_args(env)
    args[args.index("--meta") + 1] = str(env.tmp / "missing.json")
    assert run_cli(args).returncode == 2
    assert run_cli(["--transcript", "x"]).returncode == 2  # missing required options (argparse)
    args = cli_args(env)
    args[args.index("--sandbox") + 1] = str(env.tmp / "no-such-dir")
    assert run_cli(args).returncode == 2
    (env.tmp / "agent.meta.json").write_text("{not json", encoding="utf-8")
    assert run_cli(cli_args(env)).returncode == 2


@pytest.mark.skipif(not REAL_PROMPT.is_file(), reason="frozen prompt file not available on this machine")
def test_cli_valid_with_real_frozen_prompt_and_default_prompt_path(env):
    prompt_text = REAL_PROMPT.read_bytes().decode("utf-8")
    assert hashlib.sha256(prompt_text.encode("utf-8")).hexdigest() == wrc.FROZEN_PROMPT_SHA256
    b = Builder()
    b.user_prompt(prompt_text.replace("<SANDBOX>", str(env.sb)) + INJECTED)
    p = env.disk("WORLD_LOG.md", "log\n")
    b.write(p, "log\n")
    b.text("done")
    b.save(env.tmp / "agent-agentA.jsonl")
    (env.tmp / "agent.meta.json").write_text(json.dumps(env.meta), encoding="utf-8")
    r = run_cli(["--transcript", str(env.tmp / "agent-agentA.jsonl"), "--meta", str(env.tmp / "agent.meta.json"),
                 "--sandbox", str(env.sb), "--files", "WORLD_LOG.md"])  # default --prompt
    assert r.returncode == 0, r.stdout
    res = json.loads(r.stdout)
    assert res["prompt_is_frozen"] is True and res["valid"] is True and res["reasons"] == []

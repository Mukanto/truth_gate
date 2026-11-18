r"""Phase D designer tool (v2): decide whether a "world author" agent batch is valid.

v2 = world_run_check.py (v1) with exactly two changes; every other check, field and CLI option is identical:
  Change 1 (check 7, term scan): terms are matched in DECODED strings (every string leaf is scanned on its own, never
      json.dumps output), with word boundaries, and hits whose surrounding text already occurs in the recorded
      pre-flight baseline transcript are marked `"baseline": true` and do not invalidate (see check 7 below).
  Change 2 (check 10, provenance): a file whose Write/Edit rebuild is not `match` is still valid when a full replay
      of the agent's recorded actions (Write, Edit, Bash, PowerShell) in an isolated replica reproduces the disk bytes
      exactly: status `replayed_match` (see check 10 below).

A world author is a Claude Code general-purpose subagent run with model `opus`. After it finishes a batch in its
sandbox folder, this script checks the agent's transcript (.jsonl), its .meta.json, its .prefix.json (optional) and
the files it produced. It extends author_run_check.py (same transcript format and path logic) with a prompt check,
an injected-context term scan and a byte-level provenance check of every produced file.

CLI (quote the globs so the shell does not expand them):
    py world_run_check_v2.py --transcript T.jsonl --meta T.meta.json [--prefix T.prefix.json] --sandbox DIR
        --files GLOB [GLOB ...] [--base DIR] [--terms TERMS.txt] [--prompt PROMPT.md] [--out RESULT.json]
        [--baseline T.jsonl] [--manifest MANIFEST_world.json] [--replay-dir DIR] [--replay-timeout SECONDS]
        [--force-replay]
Exit codes: 0 valid, 1 invalid, 2 usage / unreadable-input error (also: wrong baseline hash, manifest/replica
mismatch, existing --replay-dir). The JSON result is printed and, with --out, saved.
Library use: check_run(...) returns the result dict (see the function docstring).

Checks (each a field in the result; `valid` is the AND of those marked [V]):
 1  meta [V]            agentType general-purpose, spawnDepth 1, model "opus"; no truthy key containing
                         fork/resume/parent anywhere in the meta (recursive).
 2  first message [V]   first `type == "user"` entry: parentUuid null, no assistant entry before it, text STARTS WITH
                         the expected prompt (the frozen prompt file with the literal <SANDBOX> replaced by the
                         --sandbox argument exactly as given). The remainder is the harness-injected context.
                         The prompt file must also hash to FROZEN_PROMPT_SHA256 (`prompt_is_frozen`) [V].
 3  later user entries [V]  every later `type == "user"` entry must hold only tool_result blocks.
 4  model [V]           assistant messages (deduplicated by message.id, else uuid): at least one non-<synthetic>
                         model and every non-synthetic model is exactly claude-opus-5-5.
 5  tools [V]           Agent, Task, Workflow, SendMessage, TaskStop, WebFetch, WebSearch, any name containing
                         ctx_ / context-mode / context_mode, and ToolSearch queries naming one of them or ctx_.
 6  linked [V]          one agentId (same as the first entry that has one; at least one must exist) and at most one
                         sessionId over all entries.
 7  term scan [V when --terms]  (a) remainder of the first user message, (b) every `attachment` entry, (c) the whole
                         .prefix.json: a hit that is not in the baseline invalidates. (d) the prompt itself:
                         reported, never invalidates.
                         Extra, informational only: (e) `api-request-blob` entries (request copies of what the model
                         was sent); a hit there is reported with group "e_request_blob" and does not invalidate.
                         v2 rules: * Decoded text. For attachment entries, the prefix file and the blob messages every
                         decoded string leaf is scanned separately (string_leaves); the remainder and the prompt are
                         already decoded strings. * Boundaries (case-insensitive match): if the term's first
                         character is [A-Za-z0-9], the character before the match must not be [A-Za-z0-9_]; if its
                         last character is [A-Za-z0-9], the character after must not be [A-Za-z0-9_]. Other edges
                         (`_`, `\`, `.`) need no boundary. * Baseline: the corpus is every decoded string leaf of
                         every entry of --baseline (sha256 must equal BASELINE_SHA256, else usage error; recorded
                         2026-11-17, before any case existed). For a match the window is the scanned string from
                         max(0, start-30) to min(len, end+30); if the window occurs verbatim (case-sensitive) in one
                         baseline string leaf the match is baseline. A hit record is one (term, location) pair: it is
                         `baseline: true` only if ALL its matches are baseline; `count`, `count_baseline`,
                         `count_new` give the numbers, `window` and `context` describe the first non-baseline match
                         (the first match if all are baseline). Result fields: term_hits (full list), term_hits_baseline,
                         term_hits_new (hit records over all groups), term_hits_new_invalidating, baseline_sha256,
                         baseline_ok (both None when no --terms is given, the baseline is then not read).
 8  outside paths [V]   every drive path in a tool_use input (all string leaves, also Write/Edit content) not inside
                         the sandbox (case-insensitive, slashes normalised, Python install paths ignored; the path
                         must end at a path boundary, so sandbox2 is not inside sandbox) and every `..` path
                         component in a Bash/PowerShell command. Git-bash style /e/... drive paths are recognised.
 9  settings            harness version(s), request model, effort. Not [V].
10  provenance [V]      for every file matched by --files, the content is rebuilt from the transcript's Write/Edit
                         calls and compared byte for byte with the file on disk (v1 statuses: match, ...).
                         v2: a file is valid if it is `match` OR `replayed_match`. When at least one target file is
                         not `match` (or with --force-replay) the agent's recorded actions are replayed in an
                         isolated replica under --replay-dir (see replay below); a non-match file whose replica
                         bytes equal the disk bytes becomes `replayed_match` (the v1 verdict stays in `status_v1`);
                         otherwise it keeps its v1 status and gets `sha256_replayed` (None if the replica lacks the
                         file). `provenance_ok` is true iff every file is match/replayed_match and no replay command
                         was refused. A v1 `match` file stays `match` even when the replay differs (reported only).
                         Replay: replica = <replay-dir>\root\world\<label>\ (label = last component of --sandbox) with
                         copies of every manifest entry starting with <label>\ (sha256 verified, else usage error),
                         plus an empty skeletons\ folder inside it. The transcript's tool calls are walked in order
                         (same dedup as v1); calls whose tool_result is missing or an error are skipped. Write/Edit
                         use the v1 byte rules on the mapped path, Bash runs `C:\Program Files\Git\bin\bash.exe -c`,
                         PowerShell runs `powershell.exe -NoProfile -NonInteractive -Command`, with cwd =
                         <replay-dir>\root, background calls run synchronously (noted in the log), a timeout kills
                         only that process tree. The sandbox path (4 spellings, case-insensitive) and the
                         phase_d_work path are rewritten into the replica. A command that still names E:\, E:/, /e/
                         or C:\Users (Python install paths excepted) after the rewrite is refused (not run).
                         Never runs unless --sandbox is a direct child of WORLD_ROOT. The replay dir is never
                         deleted; replay_log.json and per-command stdout/stderr files (io\) are kept there.
                         Result fields: provenance_ok, replay {replay_ran, replay_dir, replay_log, n_replayed_calls,
                         n_timeouts, n_refused, n_failed_calls, n_outside_skipped, n_background_sync, ...}.
Also invalid: transcript lines that are not valid JSON objects (they could hide a violation).

Index convention: an "index" is the 0-based position among the transcript's JSON entries (blank lines skipped); the
1-based line number is given next to it as `line`.

--- Where effort and harness version are recorded (looked at in a real Opus agent run, harness 2.1.325) ---
  version:  every transcript entry's `version` field (`api-request`, `api-request-shape`, `assistant`, `user`,
            `attachment` ...); `.prefix.json` -> state.buildVersion.
  effort:   `api-request` entries -> params.output_config.effort; `assistant` entries -> `effort` and `perTurnEffort`;
            `.prefix.json` -> state.effortValue. `api-request-shape` entries held no effort (searched too).
            If none of these exist, settings.effort is "not recorded in transcript" and settings.effort_searched
            lists the places that were looked at.

--- Byte behaviour of the Claude Code Write / Edit tools, measured on this machine (Windows 11, 2026-11-18) ---
  Write  stores `content` exactly as given, UTF-8: LF stays LF, no trailing newline is added, no BOM is added,
         non-ASCII characters are plain UTF-8. Overwriting an existing CRLF file does NOT keep CRLF: the new file
         is the given content (LF) verbatim.
  Edit   decodes the file as UTF-8 (a BOM stays untouched), matches `old_string` against the file with CRLF seen as
         LF (a multi-line LF old_string matches a CRLF file), replaces the first occurrence (every occurrence with
         replace_all), and writes the whole file back with ONE line ending: CRLF if the file had more CRLF line
         endings than LF-only ones, otherwise LF (a tie gives LF). So an Edit normalises a mixed file, converts new
         LF text into CRLF in a CRLF-majority file, and converts the CRLF lines of an LF-majority file into LF.
         A missing/absent final newline is kept as it was.
  Result messages: "File created successfully at: ...", "The file ... has been updated successfully.",
         "The file ... has been updated. All occurrences were successfully replaced."
  The rebuild emulates exactly this (apply_edit). Not emulated: the Edit tool's curly-quote matching (an Edit whose
  old_string is not found in the rebuilt text gives `cannot_rebuild`, never a silent skip) and Write content that
  itself contains CR characters (assumed stored verbatim).
"""
import argparse
import collections
import datetime
import glob as globmod
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time

FROZEN_PROMPT_SHA256 = "cc028f55f07b96447eb20b512b035443d15cbf61a5811f669facf6d361859ce2"
WORLD_ROOT = r"E:\Claude Projects\Kapi\phase_d_work\world"  # sandboxes live directly below; tests monkeypatch it
DEFAULT_BASELINE = r"E:\Claude Projects\Kapi\phase_d_work\transcripts\preflight_opus_agent-a7db422431a547b92.jsonl"
BASELINE_SHA256 = "e434e85272f35bcd5dd5db1938137b901e22c358923fceba23b0b91e1da89319"
DEFAULT_MANIFEST = r"E:\Claude Projects\Kapi\phase_d_work\MANIFEST_world.json"
GIT_BASH = r"C:\Program Files\Git\bin\bash.exe"  # NOT C:\Windows\system32\bash.exe (that is WSL)
POWERSHELL = "powershell.exe"
DEFAULT_REPLAY_TIMEOUT = 900
OUT_TRUNC = 2000
WINDOW_PAD = 30
ALNUM_RE = re.compile(r"[A-Za-z0-9]")
LEAF_SEP = "\x00\x01\x02\x00"  # separator for the joined baseline blob (a window containing it falls back)
DEFAULT_PROMPT = r"E:\Claude Projects\kapi-oss\evaluation\phase_d\WORLD_AUTHOR_PROMPT_D.md"
REQUIRED_MODEL = "claude-opus-5-5"
SYNTHETIC = "<synthetic>"
FORBIDDEN_TOOLS = ("Agent", "Task", "Workflow", "SendMessage", "TaskStop", "WebFetch", "WebSearch")
FORBIDDEN_SUBSTR = ("ctx_", "context-mode", "context_mode")
WRITE_TOKENS = (">", "out-file", "set-content", "add-content", "cp ", "copy", "mv ", "move", "write(", "open(",
                "sed -i", "rm ", "del ", "remove-item", "tee ", "write_text", "write_bytes")
READ_ONLY_TOOLS = ("Read", "Glob", "Grep")  # tools whose input cannot write a file
DRIVE_RE = re.compile(r"(?<![a-z0-9_])[a-z]:/")
GITBASH_RE = re.compile(r"(?:^|(?<=[\s\"'=(]))/([a-z])/(?=[^\s\"'/])")
DOTDOT_RE = re.compile(r"(?:^|(?<=[\s\\/\"'=(]))\.\.(?=[\\/\s\"')]|$)")
FORBIDDEN_TOOL_RE = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(FORBIDDEN_TOOLS) + r")(?![A-Za-z0-9_])")
SUCCESS_RE = re.compile(r"successfully|has been updated", re.I)


# ------------------------------------------------------------------ small helpers
def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def norm_path(p):
    """Lower-case, forward slashes, repeated slashes collapsed, git-bash /e/ -> e:/, no trailing slash."""
    p = p.replace("\\", "/")
    p = re.sub(r"/{2,}", "/", p)
    p = re.sub(r"^/([a-zA-Z])/", r"\1:/", p)
    return p.rstrip("/").lower()


def content_text(content):
    """Text of a message content: a string, or the joined `text` blocks of a block list."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content
                       if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str))
    return ""


def string_leaves(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from string_leaves(v)
    elif isinstance(o, list):
        for v in o:
            yield from string_leaves(v)


def load_entries(path):
    """Return (entries, lines, bad_lines): parsed JSON objects, their 1-based line numbers, unparsable line numbers."""
    entries, lines, bad = [], [], []
    with open(path, "rb") as f:
        for n, raw in enumerate(f, 1):
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except ValueError:
                bad.append(n)
                continue
            if not isinstance(o, dict):
                bad.append(n)
                continue
            entries.append(o)
            lines.append(n)
    return entries, lines, bad


def context_around(text, start, end, width=80):
    pad = max(0, (width - (end - start)) // 2)
    return text[max(0, start - pad):end + pad]


# ------------------------------------------------------------------ Edit / Write emulation
def apply_edit(content, old, new, replace_all=False):
    """Emulate the Claude Code Edit tool on `content` (str). Returns the new content, or None if the edit cannot
    be applied (empty or missing old_string). See the module docstring for the measured behaviour."""
    crlf = content.count("\r\n")
    lf_only = content.count("\n") - crlf
    use_crlf = crlf > lf_only
    norm = content.replace("\r\n", "\n")
    old = old.replace("\r\n", "\n")
    new = new.replace("\r\n", "\n")
    if old == "" or old not in norm:
        return None
    out = norm.replace(old, new) if replace_all else norm.replace(old, new, 1)
    return out.replace("\n", "\r\n") if use_crlf else out


def rebuild_content(ops, base_bytes):
    """Rebuild a file from its successful Write/Edit ops (list of (tool, input)) in order.
    Returns (content_or_None, problem_or_None, last_write_content_or_None)."""
    content, last_write = None, None
    for n, (tool, inp) in enumerate(ops, 1):
        if tool == "Write":
            c = inp.get("content")
            if not isinstance(c, str):
                return None, f"op {n}: Write content is not a string", last_write
            content = last_write = c
            continue
        old, new = inp.get("old_string"), inp.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str):
            return None, f"op {n}: Edit old_string/new_string missing", last_write
        if content is None:
            if old == "" and base_bytes is None:  # Edit with empty old_string creates the file
                content = new
                continue
            if base_bytes is None:
                return None, f"op {n}: Edit before any Write and no base copy of the file", last_write
            try:
                content = base_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return None, f"op {n}: base copy is not UTF-8", last_write
        out = apply_edit(content, old, new, bool(inp.get("replace_all")))
        if out is None:
            return None, f"op {n}: Edit old_string not found in the rebuilt content", last_write
        content = out
    return content, None, last_write


# ------------------------------------------------------------------ the checks
def check_meta(meta):
    flagged = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if any(s in str(k).lower() for s in ("fork", "resume", "parent")) and v:
                    flagged.append(path + str(k))
                walk(v, path + str(k) + ".")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}].")

    walk(meta, "")
    info = {k: meta.get(k) for k in ("agentType", "spawnDepth", "model", "pickedEffortModel", "isBuiltIn",
                                     "requestShape", "finished")}
    problems = []
    if meta.get("agentType") != "general-purpose":
        problems.append(f"agentType={meta.get('agentType')!r}")
    sd = meta.get("spawnDepth")
    if isinstance(sd, bool) or sd != 1:
        problems.append(f"spawnDepth={sd!r}")
    if meta.get("model") != "opus":
        problems.append(f"model={meta.get('model')!r}")
    if flagged:
        problems.append("fork/resume/parent keys: " + ", ".join(flagged))
    info["fork_like_keys"] = flagged
    info["problems"] = problems
    info["ok"] = not problems
    return info


def check_first_message(entries, lines, expected):
    """Checks 2 and 3. Returns a dict with the first-message facts and the later user messages."""
    first = next((i for i, o in enumerate(entries) if o.get("type") == "user"), None)
    res = {"first_user_index": first, "parentUuid_null": None, "assistant_before_first_user": None,
           "prompt_match": False, "prompt_diff": None, "remainder": "", "later_user_messages": []}
    if first is None:
        return res
    o = entries[first]
    res["parentUuid_null"] = o.get("parentUuid") is None
    res["assistant_before_first_user"] = any(e.get("type") == "assistant" for e in entries[:first])
    text = content_text((o.get("message") or {}).get("content"))
    if text.startswith(expected):
        res["prompt_match"] = True
        res["remainder"] = text[len(expected):]
    else:
        i = 0
        n = min(len(text), len(expected))
        while i < n and text[i] == expected[i]:
            i += 1
        res["prompt_diff"] = {"first_diff_index": i,
                              "expected_context": expected[max(0, i - 40):i + 40],
                              "actual_context": text[max(0, i - 40):i + 40]}
    for i in range(first + 1, len(entries)):
        e = entries[i]
        if e.get("type") != "user":
            continue
        content = (e.get("message") or {}).get("content")
        if isinstance(content, list) and content and all(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            continue
        if isinstance(content, str):
            desc, types = content, ["str"]
        elif isinstance(content, list):
            types = [b.get("type") if isinstance(b, dict) else type(b).__name__ for b in content]
            desc = "".join(b.get("text", "") if isinstance(b, dict) and b.get("type") == "text"
                           else f"[{b.get('type') if isinstance(b, dict) else type(b).__name__}]" for b in content)
        else:
            desc, types = repr(content), [type(content).__name__]
        res["later_user_messages"].append({"index": i, "line": lines[i], "timestamp": e.get("timestamp"),
                                           "block_types": types, "text": desc[:200]})
    return res


def check_models(entries):
    seen, models = set(), collections.Counter()
    for i, o in enumerate(entries):
        if o.get("type") != "assistant":
            continue
        m = o.get("message") if isinstance(o.get("message"), dict) else {}
        key = m.get("id") or o.get("uuid") or ("entry", i)
        if key in seen:
            continue
        seen.add(key)
        models[str(m.get("model"))] += 1
    real = [k for k in models if k != SYNTHETIC]
    ok = bool(real) and all(k == REQUIRED_MODEL for k in real)
    return dict(models), ok


def forbidden_reason(name, inp):
    low = name.lower()
    if name in FORBIDDEN_TOOLS:
        return "forbidden tool"
    if any(s in low for s in FORBIDDEN_SUBSTR):
        return "context-mode tool"
    if name == "ToolSearch":
        q = str(inp.get("query", "")) if isinstance(inp, dict) else ""
        if any(s in q.lower() for s in FORBIDDEN_SUBSTR):
            return "ToolSearch names a context-mode tool"
        if FORBIDDEN_TOOL_RE.search(q):
            return "ToolSearch names a forbidden tool"
    return None


def collect_tool_calls(entries, lines):
    """Assistant tool_use blocks in transcript order, deduplicated by tool_use id."""
    calls, seen = [], set()
    for i, o in enumerate(entries):
        if o.get("type") != "assistant":
            continue
        m = o.get("message")
        if not isinstance(m, dict) or not isinstance(m.get("content"), list):
            continue
        for b in m["content"]:
            if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                continue
            tid = b.get("id")
            if tid is not None:
                if tid in seen:
                    continue
                seen.add(tid)
            inp = b.get("input") if isinstance(b.get("input"), dict) else {}
            calls.append({"index": i, "line": lines[i], "name": str(b.get("name", "")), "input": inp, "id": tid,
                          "cwd": o.get("cwd")})
    return calls


def collect_tool_results(entries):
    res = {}
    for o in entries:
        if o.get("type") != "user":
            continue
        content = (o.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id"):
                res[b["tool_use_id"]] = {"is_error": bool(b.get("is_error")), "text": content_text(b.get("content"))}
    return res


def check_linked(entries, transcript_path):
    first_agent = next((o["agentId"] for o in entries if o.get("agentId")), None)
    agents = {o["agentId"] for o in entries if o.get("agentId")}
    sessions = {o["sessionId"] for o in entries if o.get("sessionId")}
    problems = []
    if first_agent is None:
        problems.append("no agentId in the transcript")
    other = sorted(a for a in agents if a != first_agent)
    if other:
        problems.append("other agentIds: " + ", ".join(other))
    if len(sessions) > 1:
        problems.append("several sessionIds: " + ", ".join(sorted(sessions)))
    m = re.match(r"agent-(.+?)\.jsonl$", os.path.basename(transcript_path))
    return {"ok": not problems, "agentId": first_agent, "other_agentIds": other, "sessionIds": sorted(sessions),
            "filename_agent_id": m.group(1) if m else None,
            "agentId_matches_filename": (m.group(1) == first_agent) if m else None, "problems": problems}


def term_regex(term):
    """Case-insensitive regex for a term with the v2 boundary rule: an alphanumeric first/last character of the term
    must not touch a [A-Za-z0-9_] character in the text; other edges need no boundary."""
    pre = r"(?<![A-Za-z0-9_])" if ALNUM_RE.match(term[0]) else ""
    suf = r"(?![A-Za-z0-9_])" if ALNUM_RE.match(term[-1]) else ""
    return re.compile(pre + re.escape(term) + suf, re.I)


class Baseline:
    """Decoded string leaves of the baseline transcript; `contains(window)` = verbatim, case-sensitive occurrence
    inside ONE leaf."""

    def __init__(self, leaves):
        uniq = list(dict.fromkeys(leaves))
        self.n_leaves = len(uniq)
        self.leaves = uniq
        self.blob = LEAF_SEP.join(uniq)

    def contains(self, window):
        if LEAF_SEP in window:  # cannot be checked inside the joined blob
            return any(window in s for s in self.leaves)
        return window in self.blob


def scan_terms(terms, location, group, strings, baseline=None):
    """Scan decoded strings (an iterable of str, each scanned separately) for the terms (a list of (term, regex)).
    One hit record per (term, location); see the module docstring (check 7) for the fields."""
    strings = [s for s in strings if isinstance(s, str)]
    hits = []
    for term, rx in terms:
        matches = []  # (string, start, end, is_baseline, window)
        for s in strings:
            for m in rx.finditer(s):
                window = s[max(0, m.start() - WINDOW_PAD):min(len(s), m.end() + WINDOW_PAD)]
                matches.append((s, m.start(), m.end(), bool(baseline is not None and baseline.contains(window)),
                                window))
        if not matches:
            continue
        n_base = sum(1 for x in matches if x[3])
        n_new = len(matches) - n_base
        pick = next((x for x in matches if not x[3]), matches[0])
        hits.append({"term": term, "location": location, "group": group, "count": len(matches),
                     "count_baseline": n_base, "count_new": n_new, "baseline": n_new == 0,
                     "window": pick[4], "context": context_around(pick[0], pick[1], pick[2])})
    return hits


def load_baseline(path, expected_sha):
    """Return (Baseline, sha256). Raises ValueError (usage error) when the file hash is not `expected_sha`."""
    with open(path, "rb") as f:
        data = f.read()
    sha = sha256_bytes(data)
    if sha != expected_sha:
        raise ValueError(f"baseline transcript {path} has sha256 {sha}, expected {expected_sha}")
    entries, _, _ = load_entries(path)
    leaves = []
    for o in entries:
        leaves.extend(string_leaves(o))
    return Baseline(leaves), sha


def find_outside(calls, sandbox_abs):
    sb = norm_path(sandbox_abs)

    def inside(rest):
        return rest.startswith(sb) and (len(rest) == len(sb) or not re.match(r"[a-z0-9_.\-]", rest[len(sb)]))

    out, seen = [], set()

    def add(c, kind, snippet):
        key = (c["index"], kind, snippet)
        if key not in seen:
            seen.add(key)
            out.append({"index": c["index"], "line": c["line"], "tool": c["name"], "kind": kind, "path": snippet})

    for c in calls:
        for leaf in string_leaves(c["input"]):
            s = re.sub(r"/{2,}", "/", leaf.replace("\\", "/"))
            low = s.lower()
            starts = [(m.start(), m.start()) for m in DRIVE_RE.finditer(low)]
            for m in GITBASH_RE.finditer(low):
                starts.append((m.start(), m.start()))
            for pos, _ in starts:
                if low[pos] == "/":  # git-bash style /e/... -> e:/...
                    cand_low = low[pos + 1] + ":/" + low[pos + 3:]
                    cand = s[pos + 1] + ":/" + s[pos + 3:]
                else:
                    cand_low, cand = low[pos:], s[pos:]
                token = re.split(r"[\"'`;|&<>]", cand_low[:200])[0]
                if inside(cand_low) or any(a in token for a in ("pythoncore", "windowsapps")):
                    continue
                add(c, "drive_path", cand[:160])
        if c["name"] in ("Bash", "PowerShell"):
            cmd = c["input"].get("command")
            if isinstance(cmd, str) and DOTDOT_RE.search(cmd):
                add(c, "dotdot_in_command", cmd[:200])
    return out


def find_settings(entries, prefix, meta):
    versions, entrypoints, cwds = set(), set(), set()
    eff = collections.defaultdict(set)
    thinking = set()

    def keys_named(o, name, path, found):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == name and isinstance(v, (str, int, float)):
                    found.append((path + k, v))
                keys_named(v, name, path + k + ".", found)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                keys_named(v, name, f"{path}[{i}].", found)

    for o in entries:
        t = o.get("type")
        if o.get("version"):
            versions.add(str(o["version"]))
        if o.get("entrypoint"):
            entrypoints.add(str(o["entrypoint"]))
        if o.get("cwd"):
            cwds.add(str(o["cwd"]))
        if t == "api-request":
            p = o.get("params") if isinstance(o.get("params"), dict) else {}
            e = (p.get("output_config") or {}).get("effort") if isinstance(p.get("output_config"), dict) else None
            if e is not None:
                eff["api-request.params.output_config.effort"].add(str(e))
            if p.get("thinking") is not None:
                thinking.add(json.dumps(p["thinking"], sort_keys=True))
        elif t == "assistant":
            for k in ("effort", "perTurnEffort"):
                if o.get(k) is not None:
                    eff[f"assistant.{k}"].add(str(o[k]))
        elif t == "api-request-shape":
            found = []
            keys_named(o.get("shape"), "effort", "api-request-shape.shape.", found)
            for path, v in found:
                eff[path].add(str(v))
    if isinstance(prefix, dict):
        st = prefix.get("state") if isinstance(prefix.get("state"), dict) else {}
        if st.get("effortValue") is not None:
            eff["prefix.state.effortValue"].add(str(st["effortValue"]))
        if st.get("buildVersion"):
            versions.add(str(st["buildVersion"]))
    values = sorted({v for s in eff.values() for v in s})
    if not values:
        effort = "not recorded in transcript"
    elif len(values) == 1:
        effort = values[0]
    else:
        effort = "mixed: " + ", ".join(values)
    return {"harness_versions": sorted(versions), "request_model": meta.get("model"),
            "pickedEffortModel": meta.get("pickedEffortModel"), "effort": effort,
            "effort_sources": {k: sorted(v) for k, v in sorted(eff.items())},
            "effort_searched": ["api-request entries: params.output_config.effort",
                                "assistant entries: effort, perTurnEffort",
                                "api-request-shape entries: any 'effort' key in shape",
                                "prefix.json: state.effortValue"],
            "thinking": sorted(thinking), "entrypoints": sorted(entrypoints), "cwds": sorted(cwds)}


def check_provenance(calls, results, sandbox_abs, patterns, base):
    """Check 10. Returns (per_file dict, unmatched_patterns, unchecked_written_files)."""
    rel_files, unmatched = [], []
    for pat in patterns:
        hits = sorted(h.replace("\\", "/") for h in globmod.glob(pat, root_dir=sandbox_abs, recursive=True)
                      if os.path.isfile(os.path.join(sandbox_abs, h)))
        if not hits:
            unmatched.append(pat)
        for h in hits:
            if h not in rel_files:
                rel_files.append(h)
    sb_norm = norm_path(sandbox_abs)

    # successful Write/Edit ops by resolved path
    ops, failed, unresolved = collections.defaultdict(list), collections.Counter(), collections.Counter()
    for c in calls:
        if c["name"] not in ("Write", "Edit"):
            continue
        p = c["input"].get("file_path")
        if not isinstance(p, str):
            continue
        key = norm_path(p)
        if not re.match(r"^[a-z]:/", key) and c.get("cwd"):
            key = norm_path(str(c["cwd"]) + "/" + p)
        r = results.get(c["id"])
        if r is None:
            unresolved[key] += 1
            continue
        if r["is_error"] or "<tool_use_error>" in r["text"] or not SUCCESS_RE.search(r["text"]):
            failed[key] += 1
            continue
        ops[key].append((c["name"], c["input"]))

    per_file = {}
    for rel in rel_files:
        disk_path = os.path.join(sandbox_abs, rel)
        key = norm_path(disk_path)
        with open(disk_path, "rb") as f:
            disk = f.read()
        disk_sha = sha256_bytes(disk)
        base_bytes = None
        if base:
            bp = os.path.join(base, rel)
            if os.path.isfile(bp):
                with open(bp, "rb") as f:
                    base_bytes = f.read()
        file_ops = ops.get(key, [])
        entry = {"sha256_disk": disk_sha, "n_writes": sum(1 for t, _ in file_ops if t == "Write"),
                 "n_edits": sum(1 for t, _ in file_ops if t == "Edit"), "n_failed_ops": failed.get(key, 0),
                 "n_ops_without_result": unresolved.get(key, 0), "sha256_rebuilt": None,
                 "last_write_sha256": None, "disk_equals_last_write": None, "detail": None}
        if not file_ops:
            entry["status"] = "not_written"
        else:
            content, problem, last_write = rebuild_content(file_ops, base_bytes)
            if last_write is not None:
                lw = sha256_bytes(last_write.encode("utf-8"))
                entry["last_write_sha256"] = lw
                entry["disk_equals_last_write"] = (lw == disk_sha)
            if content is None:
                entry["status"] = "cannot_rebuild"
                entry["detail"] = problem
            else:
                rebuilt = content.encode("utf-8")
                entry["sha256_rebuilt"] = sha256_bytes(rebuilt)
                if rebuilt == disk:
                    entry["status"] = "match"
                elif rebuilt.replace(b"\r\n", b"\n") == disk.replace(b"\r\n", b"\n"):
                    entry["status"] = "match_after_line_endings"
                else:
                    entry["status"] = "mismatch"
        # touched by a tool other than Write/Edit
        base_name = os.path.basename(rel).lower()
        cmds = []
        for c in calls:
            if c["name"] in ("Write", "Edit") or c["name"] in READ_ONLY_TOOLS:
                continue
            text = c["input"].get("command") if isinstance(c["input"].get("command"), str) \
                else json.dumps(c["input"], ensure_ascii=False)
            low = text.lower()
            if base_name in low and any(tok in low for tok in WRITE_TOKENS):
                cmds.append({"index": c["index"], "tool": c["name"], "command": text[:300]})
        entry["touched_by_other_tool"] = bool(cmds)
        entry["other_tool_commands"] = cmds
        per_file[rel] = entry

    checked_keys = {norm_path(os.path.join(sandbox_abs, r)) for r in rel_files}
    unchecked = sorted(k for k in ops if k not in checked_keys and (k == sb_norm or k.startswith(sb_norm + "/")))
    return per_file, unmatched, unchecked


# ------------------------------------------------------------------ replay (check 10, v2)
SEP_RX = r"(?:\\\\|\\|/)"  # doubled backslash, backslash or slash
PY_INSTALL_MARKS = ("pythoncore", "windowsapps")  # same exemption as v1's outside-path check


def is_direct_child(path, parent):
    return norm_path(os.path.dirname(os.path.abspath(path))) == norm_path(os.path.abspath(parent))


def split_drive_path(path):
    p = path.replace("\\", "/").rstrip("/")
    m = re.match(r"^([A-Za-z]):/(.*)$", p)
    if not m:
        raise ValueError(f"not a drive path: {path}")
    return m.group(1), [c for c in m.group(2).split("/") if c]


def path_regex(path, boundary):
    """Regex source matching a drive path in its spellings (E:\\a, E:/a, /e/a, E:\\\\a; separators may be mixed).
    With `boundary` the match must end at a path-component boundary (sandbox2 is not sandbox)."""
    drive, comps = split_drive_path(path)
    body = "".join(SEP_RX + re.escape(c) for c in comps)
    rx = r"(?<![A-Za-z0-9_/\\.])(?:" + re.escape(drive + ":") + "|/" + re.escape(drive) + ")" + body
    return rx + (r"(?![A-Za-z0-9_.\-])" if boundary else "")


def spell(path, style):
    drive, comps = split_drive_path(os.path.abspath(path))
    rest = "/".join(comps)
    if style == "git":
        return "/" + drive.lower() + "/" + rest
    if style == "fwd":
        return f"{drive}:/{rest}"
    if style == "double":
        return f"{drive}:\\\\" + rest.replace("/", "\\\\")
    return f"{drive}:\\" + rest.replace("/", "\\")


def spelling_style(text):
    if text.startswith("/"):
        return "git"
    m = re.search(r"\\\\|\\|/", text[2:])
    return {None: "back", "\\\\": "double", "\\": "back", "/": "fwd"}[m.group(0) if m else None]


class PathRewriter:
    """Rewrites the real sandbox path and the phase_d_work path inside a command into the replica, and finds
    anything in the rewritten command that still points at the real drive."""

    def __init__(self, sandbox_abs, phase_root, replica_sandbox, replica_root):
        self.rx = re.compile("(?P<sb>" + path_regex(sandbox_abs, True) + ")|(?P<ph>" + path_regex(phase_root, True)
                             + ")", re.I)
        self.replica_sandbox, self.replica_root = replica_sandbox, replica_root
        self.removal = re.compile(path_regex(replica_root, False), re.I)

    def rewrite(self, text):
        def sub(m):
            return spell(self.replica_sandbox if m.group("sb") else self.replica_root, spelling_style(m.group(0)))
        return self.rx.sub(sub, text)

    def residue(self, rewritten):
        """Reasons why the rewritten command must not run (empty list = safe)."""
        t = self.removal.sub("", rewritten)
        out = []
        if re.search(r"(?<![A-Za-z0-9_])e:[\\/]", t, re.I):
            out.append("names E:\\ or E:/ outside the replica")
        if re.search(r"(?<![A-Za-z0-9_.\-/\\])/e/", t, re.I):
            out.append("names /e/ outside the replica")
        for m in re.finditer(r"(?<![A-Za-z0-9_])c:[\\/]+users\b", t, re.I):
            token = re.split(r"[\"'`;|&<>]", t[m.start():m.start() + 200])[0].lower()
            if not any(a in token for a in PY_INSTALL_MARKS):
                out.append("names C:\\Users outside Python install paths")
                break
        return out


def map_to_sandbox_rel(p, cwd, sandbox_abs):
    """Relative path (os.sep style) of `p` inside the sandbox, or None when outside / the sandbox itself."""
    def norm(x):
        x = re.sub(r"/{2,}", "/", x.replace("\\", "/"))
        return re.sub(r"^/([a-zA-Z])/", r"\1:/", x)
    s = norm(p)
    if not re.match(r"^[A-Za-z]:/", s) and cwd:
        s = norm(str(cwd) + "/" + p)
    sb = norm(sandbox_abs).rstrip("/")
    if not s.lower().startswith(sb.lower() + "/"):
        return None
    rel = os.path.normpath(s[len(sb) + 1:].replace("/", os.sep))
    if rel in ("", ".") or rel == ".." or rel.startswith(".." + os.sep) or os.path.isabs(rel) or ":" in rel:
        return None
    return rel


def _write_bytes(dst, data):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        f = open(dst, "wb")
    except PermissionError:
        os.chmod(dst, stat.S_IWRITE | stat.S_IREAD)
        f = open(dst, "wb")
    with f:
        f.write(data)


def replay_edit_file(dst, inp):
    """Apply an Edit to the replica file with the v1 byte rules. Returns None on success, else a problem string."""
    old, new = inp.get("old_string"), inp.get("new_string")
    if not isinstance(old, str) or not isinstance(new, str):
        return "Edit old_string/new_string missing"
    if not os.path.isfile(dst):
        if old == "":  # as in v1: an Edit with empty old_string creates the file
            _write_bytes(dst, new.encode("utf-8"))
            return None
        return "Edit target is not in the replica"
    with open(dst, "rb") as f:
        content = f.read().decode("utf-8")
    out = apply_edit(content, old, new, bool(inp.get("replace_all")))
    if out is None:
        return "Edit old_string not found in the replica content"
    _write_bytes(dst, out.encode("utf-8"))
    return None


def run_command(tool, command, cwd, timeout, out_base):
    """Run one Bash/PowerShell command synchronously. stdout/stderr go to files (out_base.out / .err) so a leaked
    grandchild cannot block us. A timeout kills only this command's process tree."""
    if tool == "Bash":
        argv = [GIT_BASH, "-c", command]
    else:
        argv = [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", command]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    info = {"exit_code": None, "timed_out": False, "duration_s": None, "start_error": None}
    t0 = time.monotonic()
    with open(out_base + ".out", "wb") as fo, open(out_base + ".err", "wb") as fe:
        try:
            p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=fo, stderr=fe,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except OSError as e:
            info["start_error"] = str(e)
            info["duration_s"] = round(time.monotonic() - t0, 3)
            return info
        try:
            info["exit_code"] = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            info["timed_out"] = True
            subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
            try:
                info["exit_code"] = p.wait(timeout=15)
            except subprocess.TimeoutExpired:
                p.kill()
    info["duration_s"] = round(time.monotonic() - t0, 3)
    return info


def _read_trunc(path):
    with open(path, "rb") as f:
        data = f.read()
    text = data.decode("utf-8", errors="replace")
    return text[:OUT_TRUNC] + (f"...[+{len(text) - OUT_TRUNC} chars]" if len(text) > OUT_TRUNC else "")


def run_replay(calls, results, sandbox_abs, rel_files, manifest_path, replay_dir, timeout):
    """Replay the agent's recorded Write/Edit/Bash/PowerShell calls in an isolated replica (see the module
    docstring). Returns {"summary": {...}, "sha256": {rel: sha256 of the replica file or None}}. Raises
    OSError / ValueError for usage errors (existing replay dir, manifest problems). The replay dir is never deleted."""
    label = os.path.basename(sandbox_abs)
    world_dir = os.path.dirname(sandbox_abs)
    phase_root = os.path.dirname(world_dir)
    replay_dir = os.path.abspath(replay_dir)
    if os.path.exists(replay_dir):
        raise ValueError(f"replay dir already exists: {replay_dir}")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    if not isinstance(manifest, dict):
        raise ValueError("manifest is not a JSON object")
    entries = []
    for key, sha in manifest.items():
        k = str(key).replace("/", "\\")
        if k.lower().startswith(label.lower() + "\\"):
            rel = k[len(label) + 1:]
            if not rel or ":" in rel or any(x in ("", ".", "..") for x in rel.split("\\")):
                raise ValueError(f"bad manifest key: {key!r}")
            entries.append((k, rel, str(sha).lower()))

    root = os.path.join(replay_dir, "root")
    replica_sb = os.path.join(root, "world", label)
    iodir = os.path.join(replay_dir, "io")
    os.makedirs(replica_sb)
    os.makedirs(iodir)
    for key, rel, sha in entries:
        src = os.path.join(world_dir, key)
        dst = os.path.join(replica_sb, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        os.chmod(dst, stat.S_IWRITE | stat.S_IREAD)
        with open(dst, "rb") as f:
            got = sha256_bytes(f.read())
        if got != sha:
            raise ValueError(f"manifest sha256 mismatch for {key}: copy has {got}, manifest {sha}")
    os.makedirs(os.path.join(replica_sb, "skeletons"), exist_ok=True)

    rw = PathRewriter(sandbox_abs, phase_root, replica_sb, root)
    log = []
    n = collections.Counter()
    for c in calls:
        tool = c["name"]
        if tool not in ("Write", "Edit", "Bash", "PowerShell"):
            continue
        entry = {"call_index": c["index"], "line": c["line"], "tool": tool, "tool_use_id": c["id"],
                 "background": bool(tool in ("Bash", "PowerShell") and c["input"].get("run_in_background"))}
        log.append(entry)
        r = results.get(c["id"])
        if r is None:
            entry["status"] = "skipped_no_result"
            n["skipped_no_result"] += 1
            continue
        if tool in ("Write", "Edit"):
            skip = r["is_error"] or "<tool_use_error>" in r["text"] or not SUCCESS_RE.search(r["text"])
        else:
            skip = r["is_error"] or "<tool_use_error>" in r["text"]
        if skip:
            entry["status"] = "skipped_error_result"
            n["skipped_error"] += 1
            continue
        if tool in ("Write", "Edit"):
            p = c["input"].get("file_path")
            rel = map_to_sandbox_rel(p, c.get("cwd"), sandbox_abs) if isinstance(p, str) else None
            entry["path"] = p
            if rel is None:
                entry["status"] = "skipped_outside_sandbox"
                n["outside_skipped"] += 1
                continue
            dst = os.path.join(replica_sb, rel)
            entry["mapped_path"] = dst
            try:
                if tool == "Write":
                    content = c["input"].get("content")
                    problem = None if isinstance(content, str) else "Write content is not a string"
                    if problem is None:
                        _write_bytes(dst, content.encode("utf-8"))
                else:
                    problem = replay_edit_file(dst, c["input"])
            except (OSError, UnicodeError) as e:
                problem = f"{type(e).__name__}: {e}"
            n["replayed"] += 1
            if problem:
                entry["status"] = "failed"
                entry["problem"] = problem
                n["failed"] += 1
            else:
                entry["status"] = "ok"
            continue
        cmd = c["input"].get("command")
        if not isinstance(cmd, str):
            entry["status"] = "skipped_no_command"
            continue
        mapped = rw.rewrite(cmd)
        entry["mapped_command"] = mapped
        problems = rw.residue(mapped)
        if problems:
            entry["status"] = "refused"
            entry["refused_reason"] = "; ".join(problems)
            n["refused"] += 1
            continue
        if entry["background"]:
            entry["note"] = "run_in_background in the transcript; replayed synchronously"
            n["background_sync"] += 1
        info = run_command(tool, mapped, root, timeout, os.path.join(iodir, f"{len(log):04d}_{tool}"))
        entry.update(info)
        entry["stdout"] = _read_trunc(os.path.join(iodir, f"{len(log):04d}_{tool}.out"))
        entry["stderr"] = _read_trunc(os.path.join(iodir, f"{len(log):04d}_{tool}.err"))
        n["replayed"] += 1
        if info["start_error"]:
            entry["status"] = "failed_to_start"
            n["failed"] += 1
        elif info["timed_out"]:
            entry["status"] = "timeout"
            n["timeouts"] += 1
        else:
            entry["status"] = "ok" if info["exit_code"] == 0 else "nonzero_exit"
            if info["exit_code"] != 0:
                n["nonzero_exit"] += 1

    sha = {}
    for rel in rel_files:
        fp = os.path.join(replica_sb, rel.replace("/", os.sep))
        if os.path.isfile(fp):
            with open(fp, "rb") as f:
                sha[rel] = sha256_bytes(f.read())
        else:
            sha[rel] = None
    summary = {"replay_ran": True, "replay_dir": replay_dir, "replay_log": os.path.join(replay_dir, "replay_log.json"),
               "n_replayed_calls": n["replayed"], "n_timeouts": n["timeouts"], "n_refused": n["refused"],
               "n_failed_calls": n["failed"], "n_nonzero_exit": n["nonzero_exit"],
               "n_outside_skipped": n["outside_skipped"], "n_skipped_error": n["skipped_error"],
               "n_skipped_no_result": n["skipped_no_result"], "n_background_sync": n["background_sync"],
               "n_manifest_files_copied": len(entries), "not_run_reason": None}
    with open(summary["replay_log"], "w", encoding="utf-8") as f:
        json.dump({"sandbox": sandbox_abs, "label": label, "manifest": manifest_path, "timeout_s": timeout,
                   "replica_sandbox": replica_sb, "summary": summary, "replica_sha256": sha, "calls": log}, f,
                  indent=1, ensure_ascii=False)
        f.write("\n")
    return {"summary": summary, "sha256": sha}


# ------------------------------------------------------------------ main entry
def check_run(transcript, meta_path, sandbox, patterns, prefix_path=None, base=None, terms_path=None,
              prompt_path=DEFAULT_PROMPT, frozen_sha=FROZEN_PROMPT_SHA256, baseline_path=DEFAULT_BASELINE,
              baseline_sha=BASELINE_SHA256, manifest_path=DEFAULT_MANIFEST, replay_dir=None,
              replay_timeout=DEFAULT_REPLAY_TIMEOUT, force_replay=False):
    """Run all checks and return the result dict (see the module docstring). Raises OSError / ValueError for
    unreadable inputs (also a wrong baseline hash, a manifest/replica problem, an existing replay_dir).
    `frozen_sha` and `baseline_sha` are overridable for tests only."""
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    if not isinstance(meta, dict):
        raise ValueError("meta is not a JSON object")
    prefix = None
    if prefix_path:
        with open(prefix_path, encoding="utf-8") as f:
            prefix = json.load(f)
    terms = []
    if terms_path:
        with open(terms_path, encoding="utf-8-sig") as f:
            for ln in f:
                t = ln.strip()
                if t and not t.startswith("#") and t not in terms:
                    terms.append(t)
    with open(prompt_path, "rb") as f:
        prompt_bytes = f.read()
    prompt_text = prompt_bytes.decode("utf-8")
    prompt_sha = sha256_bytes(prompt_bytes)
    expected = prompt_text.replace("<SANDBOX>", sandbox)
    sandbox_abs = os.path.abspath(sandbox)

    entries, lines, bad_lines = load_entries(transcript)
    with open(transcript, "rb") as f:
        transcript_sha = sha256_bytes(f.read())
    stamps = [o["timestamp"] for o in entries if isinstance(o.get("timestamp"), str)]

    reasons = []
    res = {"transcript": transcript, "transcript_sha256": transcript_sha,
           "first_last_utc": [min(stamps), max(stamps)] if stamps else None}

    # 1 meta
    res["meta"] = check_meta(meta)
    if not res["meta"]["ok"]:
        reasons.append("meta: " + "; ".join(res["meta"]["problems"]))

    # 2/3 prompt and user messages
    res["prompt_sha256"] = prompt_sha
    res["prompt_is_frozen"] = (prompt_sha == frozen_sha)
    if not res["prompt_is_frozen"]:
        reasons.append("prompt file is not the frozen prompt (sha256 " + prompt_sha + ")")
    fm = check_first_message(entries, lines, expected)
    res["first_message"] = {k: fm[k] for k in ("first_user_index", "parentUuid_null", "assistant_before_first_user")}
    res["prompt_match"] = fm["prompt_match"]
    res["prompt_diff"] = fm["prompt_diff"]
    res["injected_remainder_len"] = len(fm["remainder"])
    res["later_user_messages"] = fm["later_user_messages"]
    if fm["first_user_index"] is None:
        reasons.append("no user entry in the transcript")
    else:
        if fm["parentUuid_null"] is False:
            reasons.append("first user entry has a non-null parentUuid")
        if fm["assistant_before_first_user"]:
            reasons.append("an assistant entry precedes the first user entry")
        if not fm["prompt_match"]:
            reasons.append("first user message does not start with the expected prompt (first difference at char "
                           + str(fm["prompt_diff"]["first_diff_index"]) + ")")
    if fm["later_user_messages"]:
        reasons.append(f"{len(fm['later_user_messages'])} later user entr(y/ies) that are not tool_result-only")

    # 4 model
    res["models"], res["model_rule_ok"] = check_models(entries)
    if not res["model_rule_ok"]:
        reasons.append(f"model rule failed: {res['models']}")

    # 5 tools
    calls = collect_tool_calls(entries, lines)
    res["tools"] = dict(collections.Counter(c["name"] for c in calls))
    res["forbidden_calls"] = []
    for c in calls:
        why = forbidden_reason(c["name"], c["input"])
        if why:
            res["forbidden_calls"].append({"index": c["index"], "line": c["line"], "name": c["name"], "reason": why,
                                           "input": json.dumps(c["input"], ensure_ascii=False)[:200]})
    if res["forbidden_calls"]:
        reasons.append(f"{len(res['forbidden_calls'])} forbidden tool call(s): "
                       + ", ".join(sorted({x['name'] for x in res['forbidden_calls']})))

    # 6 linked
    res["linked"] = check_linked(entries, transcript)
    if not res["linked"]["ok"]:
        reasons.append("transcript not linked: " + "; ".join(res["linked"]["problems"]))

    # 7 term scan (v2: decoded string leaves, word boundaries, baseline exemption)
    res["terms_scanned"] = len(terms)
    res["baseline_sha256"], res["baseline_ok"], res["baseline_leaves"] = None, None, None
    hits = []
    if terms:
        if not baseline_path:
            raise ValueError("a --baseline transcript is required when terms are scanned")
        baseline, res["baseline_sha256"] = load_baseline(baseline_path, baseline_sha)  # ValueError on wrong hash
        res["baseline_ok"], res["baseline_leaves"] = True, baseline.n_leaves
        tx = [(t, term_regex(t)) for t in terms]
        hits += scan_terms(tx, "first user message remainder", "a_remainder", [fm["remainder"]], baseline)
        for i, o in enumerate(entries):
            if o.get("type") == "attachment":
                att = o.get("attachment")
                atype = att.get("type") if isinstance(att, dict) else None
                hits += scan_terms(tx, f"attachment entry {i} (line {lines[i]}, type {atype})", "b_attachment",
                                   string_leaves(o), baseline)
        if prefix is not None:
            hits += scan_terms(tx, "prefix.json", "c_prefix", string_leaves(prefix), baseline)
        hits += scan_terms(tx, "prompt (frozen, informational)", "d_prompt", [expected], baseline)
        for i, o in enumerate(entries):
            if o.get("type") == "api-request-blob":
                hits += scan_terms(tx, f"api-request-blob entry {i} (line {lines[i]}, informational)",
                                   "e_request_blob", string_leaves(o.get("message")), baseline)
    res["term_hits"] = hits
    res["term_hits_baseline"] = sum(1 for h in hits if h["baseline"])
    res["term_hits_new"] = sum(1 for h in hits if not h["baseline"])
    invalidating = [h for h in hits if h["group"] in ("a_remainder", "b_attachment", "c_prefix") and not h["baseline"]]
    res["term_hits_new_invalidating"] = len(invalidating)
    if invalidating:
        reasons.append(f"{len(invalidating)} term hit(s) in injected context that are not in the baseline: "
                       + ", ".join(sorted({h['term'] for h in invalidating})))

    # 8 outside paths
    res["outside_paths"] = find_outside(calls, sandbox_abs)
    if res["outside_paths"]:
        reasons.append(f"{len(res['outside_paths'])} path(s) outside the sandbox")

    # 9 settings
    res["settings"] = find_settings(entries, prefix, meta)

    # 10 provenance
    results = collect_tool_results(entries)
    per_file, unmatched, unchecked = check_provenance(calls, results, sandbox_abs, patterns, base)
    for v in per_file.values():
        v["status_v1"] = v["status"]
        v["sha256_replayed"] = None
    res["provenance"] = per_file
    res["unmatched_patterns"] = unmatched
    res["unchecked_written_files"] = unchecked
    res["files_checked"] = len(per_file)
    res["replay"] = {"replay_ran": False, "replay_dir": None, "replay_log": None, "n_replayed_calls": 0,
                     "n_timeouts": 0, "n_refused": 0, "not_run_reason": None}
    need_replay = bool(per_file) and (force_replay or any(v["status"] != "match" for v in per_file.values()))
    if need_replay:
        if not is_direct_child(sandbox_abs, WORLD_ROOT):
            res["replay"]["not_run_reason"] = f"--sandbox is not a direct child of {WORLD_ROOT}"
        else:
            if replay_dir is None:
                stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
                replay_dir = os.path.join(os.path.dirname(os.path.normpath(WORLD_ROOT)), "world_replay",
                                          f"{os.path.basename(os.path.normpath(sandbox_abs))}_{stamp}")
            rep = run_replay(calls, results, sandbox_abs, list(per_file), manifest_path, replay_dir, replay_timeout)
            res["replay"].update(rep["summary"])
            for rel, v in per_file.items():
                v["sha256_replayed"] = rep["sha256"].get(rel)
                if v["status"] != "match" and v["sha256_replayed"] == v["sha256_disk"]:
                    v["status"] = "replayed_match"
    res["provenance_ok"] = (all(v["status"] in ("match", "replayed_match") for v in per_file.values())
                            and res["replay"]["n_refused"] == 0)
    not_ok = {r: v["status"] for r, v in per_file.items() if v["status"] not in ("match", "replayed_match")}
    if not_ok:
        shown = ", ".join(f"{r}={s}" for r, s in list(not_ok.items())[:5])
        reasons.append(f"provenance: {len(not_ok)} file(s) neither `match` nor `replayed_match` "
                       f"({shown}{', ...' if len(not_ok) > 5 else ''})")
    if res["replay"]["n_refused"]:
        reasons.append(f"replay: {res['replay']['n_refused']} command(s) refused (named a path outside the replica)")

    res["unparsable_lines"] = bad_lines
    if bad_lines:
        reasons.append(f"{len(bad_lines)} unparsable transcript line(s): {bad_lines[:5]}")

    res["reasons"] = reasons
    res["valid"] = not reasons
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate a world-author agent batch (see module docstring).")
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--prefix")
    ap.add_argument("--sandbox", required=True)
    ap.add_argument("--files", nargs="+", required=True, metavar="GLOB")
    ap.add_argument("--base")
    ap.add_argument("--terms")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--out")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--replay-dir")
    ap.add_argument("--replay-timeout", type=int, default=DEFAULT_REPLAY_TIMEOUT)
    ap.add_argument("--force-replay", action="store_true")
    args = ap.parse_args(argv)  # argparse exits with 2 on usage errors
    for label, p in (("transcript", args.transcript), ("meta", args.meta), ("prefix", args.prefix),
                     ("terms", args.terms), ("prompt", args.prompt), ("baseline", args.baseline if args.terms else None)):
        if p and not os.path.isfile(p):
            print(f"usage error: {label} file not found: {p}", file=sys.stderr)
            return 2
    for label, p in (("sandbox", args.sandbox), ("base", args.base)):
        if p and not os.path.isdir(p):
            print(f"usage error: {label} directory not found: {p}", file=sys.stderr)
            return 2
    try:
        res = check_run(args.transcript, args.meta, args.sandbox, args.files, args.prefix, args.base, args.terms,
                        args.prompt, baseline_path=args.baseline, manifest_path=args.manifest,
                        replay_dir=args.replay_dir, replay_timeout=args.replay_timeout,
                        force_replay=args.force_replay)
    except (OSError, ValueError) as e:  # JSONDecodeError is a ValueError
        print(f"usage error: unreadable input: {e}", file=sys.stderr)
        return 2
    text = json.dumps(res, indent=1, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    return 0 if res["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())

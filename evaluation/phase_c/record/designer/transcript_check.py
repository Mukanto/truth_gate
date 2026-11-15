"""Phase C designer tool: summarise one agent transcript for WORLD_RUN.md (PREREG_PHASE_C section 4 item 3; P-1).

Usage: py -I transcript_check.py AGENT.jsonl AGENT.meta.json SANDBOX_DIR [--out SUMMARY.json]
Reports: request model (meta), assistant-message model ids (unique message ids), tool names called, forbidden calls
(context-mode ctx tools, Agent/Task, WebFetch/WebSearch), path strings in tool inputs that lie outside the sandbox (for
the designer to read; not a verdict), first/last timestamps, SHA-256 of the transcript.
"""
import hashlib, json, re, sys
from collections import Counter

jl, meta_p, sandbox = sys.argv[1], sys.argv[2], sys.argv[3]
out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
norm = lambda p: p.replace("\\", "/").rstrip("/").lower()
sb = norm(sandbox)
FORBID_CTX = ("ctx_search", "ctx_batch_execute", "ctx_fetch_and_index", "ctx_index")
FORBID = {"Agent", "Task", "WebFetch", "WebSearch"}
PATH_RE = re.compile(r"\"((?:[A-Za-z]:[\\/]|/[a-zA-Z]/)[^\"]*)\"|'((?:[A-Za-z]:[\\/]|/[a-zA-Z]/)[^']*)'"
                     r"|((?:[A-Za-z]:[\\/]|/[a-zA-Z]/)[^\s\"'`|;&<>]*)")


def find_paths(s):
    return [a or b or c for a, b, c in PATH_RE.findall(s)]

meta = json.load(open(meta_p, encoding="utf-8"))
models, entries, msg_seen, tools, forbidden, outside, stamps = Counter(), Counter(), set(), Counter(), [], set(), []
for line in open(jl, encoding="utf-8"):
    d = json.loads(line)
    if d.get("timestamp"):
        stamps.append(d["timestamp"])
    if d.get("type") != "assistant":
        continue
    m = d.get("message") or {}
    entries[m.get("model")] += 1
    mid = m.get("id") or d.get("uuid")
    if mid not in msg_seen:
        msg_seen.add(mid)
        models[m.get("model")] += 1
    for c in m.get("content") or []:
        if not isinstance(c, dict) or c.get("type") != "tool_use":
            continue
        name = c.get("name", "")
        tools[name] += 1
        if name in FORBID or any(f in name for f in FORBID_CTX):
            forbidden.append(name)
        inp = c.get("input") or {}
        for k, v in inp.items():
            if not isinstance(v, str):
                continue
            cands = find_paths(v) if k in ("command", "pattern", "prompt") else [v] if k in ("file_path", "path", "notebook_path") else []
            for p in cands:
                q = norm(p)
                q = re.sub(r"^/([a-z])/", r"\1:/", q)
                if not (q == sb or q.startswith(sb + "/")) and not q.startswith("/dev/null"):
                    outside.add(f"{name}.{k}: {p}")
            if k == "command" and ".." in v:
                outside.add(f"{name}.command contains '..': {v[:200]}")
summary = {
    "transcript": jl, "sha256": hashlib.sha256(open(jl, "rb").read()).hexdigest(),
    "meta_model": meta.get("model"), "meta_pickedEffortModel": meta.get("pickedEffortModel"),
    "meta_finished": meta.get("finished"), "assistant_entries_by_model": dict(entries),
    "assistant_messages_by_model": dict(models), "tools": dict(tools),
    "forbidden_calls": forbidden, "paths_outside_sandbox": sorted(outside),
    "first": min(stamps) if stamps else None, "last": max(stamps) if stamps else None,
}
print(json.dumps(summary, indent=1, ensure_ascii=False))
if out:
    json.dump(summary, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

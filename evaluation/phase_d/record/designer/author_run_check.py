"""Check a brief/criterion/structure author transcript (REVISIONS-post-freeze P-1 amendment 5; PREREG_PHASE_D section 3
item 0 sandbox rules). Usage: author_run_check.py TRANSCRIPT.jsonl SANDBOX_DIR

Reports: assistant-message model ids (every one must be claude-sonnet-*, at least one), tool counts, any agent-starting
or context-mode tool call, every absolute path in a tool input that lies outside the sandbox, every URL fetched
(WebFetch input or curl/wget in Bash), the transcript SHA-256 and the time span. Exit 0 when the run is valid."""
import collections
import hashlib
import json
import re
import sys

T, SANDBOX = sys.argv[1], sys.argv[2]
sb = SANDBOX.replace("\\", "/").rstrip("/").lower()
models, tools, ts = collections.Counter(), collections.Counter(), []
outside, urls, bad_tools = [], [], []
for line in open(T, encoding="utf-8"):
    try:
        o = json.loads(line)
    except Exception:
        continue
    if o.get("timestamp"):
        ts.append(o["timestamp"])
    m = o.get("message", {})
    # only the transcript's own assistant entries; "api-request-blob" entries are request copies of earlier turns
    if o.get("type") != "assistant" or not (isinstance(m, dict) and m.get("role") == "assistant"):
        continue
    models[m.get("model")] += 1
    for c in m.get("content", []) or []:
        if not (isinstance(c, dict) and c.get("type") == "tool_use"):
            continue
        name = c["name"]
        tools[name] += 1
        if name in ("Agent", "Task", "Workflow", "SendMessage") or "ctx_" in name:
            bad_tools.append(name)
        inp = json.dumps(c["input"], ensure_ascii=False).replace("\\\\", "/")
        low = inp.lower()
        for mt in re.finditer(r"(?<![a-z])[a-z]:/", low):  # a drive path (not the "s://" of https://)
            rest = low[mt.start():]
            if not rest.startswith(sb) and not any(a in rest[:200] for a in ("pythoncore", "windowsapps")):
                outside.append((name, inp[mt.start():mt.start() + 160]))
        if name == "WebFetch":
            urls.append(c["input"].get("url"))
        for u in re.findall(r"https?://[^\s\"'<>)]+", inp) if name in ("Bash", "PowerShell") else []:
            urls.append(u)
real = {k: v for k, v in models.items() if k != "<synthetic>"}
ok_model = bool(real) and all(str(k).startswith("claude-sonnet-") for k in real)
res = {"transcript_sha256": hashlib.sha256(open(T, "rb").read()).hexdigest(),
       "first_last_utc": [min(ts), max(ts)] if ts else None,
       "assistant_message_models": dict(models), "model_rule_ok": ok_model,
       "tools": dict(tools), "forbidden_tool_calls": bad_tools,
       "outside_paths": sorted(set(outside)), "urls": sorted(set(u for u in urls if u))}
print(json.dumps(res, indent=1, ensure_ascii=False))
sys.exit(0 if ok_model and not bad_tools else 1)

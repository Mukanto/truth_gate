"""For each ctx_search call of a transcript: its source filter and the source labels named in its result (designer, P-5)."""
import json, re, sys
ents = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
calls = {}
for d in ents:
    if d.get("type") == "assistant":
        for c in d["message"].get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use" and c["name"].endswith("ctx_search"):
                calls[c["id"]] = c["input"].get("source")
    if d.get("type") == "user":
        for c in d.get("message", {}).get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("tool_use_id") in calls:
                txt = json.dumps(c.get("content"), ensure_ascii=False)
                labels = sorted(set(re.findall(r"zq7auditB2x[\w\-]*|[A-Za-z0-9]+-pc-[\w\-]+", txt)))
                srcs = sorted(set(re.findall(r'(?:Source|source)[^A-Za-z0-9]{1,6}([A-Za-z0-9_\-\.]+)', txt)))
                print("filter:", calls[c["tool_use_id"]], "| labels in result:", labels[:12], "| source fields:", srcs[:12], "| chars:", len(txt))
